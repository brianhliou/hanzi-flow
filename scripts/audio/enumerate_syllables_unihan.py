#!/usr/bin/env python3
"""
Enumerate all valid Mandarin syllables from Unihan database.

This script:
1. Extracts kMandarin readings from Unihan (authoritative Unicode source)
2. Converts tone marks to tone3 format (yī → yi1)
3. Handles multiple readings per character
4. Converts ü to v for filename compatibility
5. Validates against our sentence dataset
6. Generates enumeration JSON ready for Azure TTS
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional


def extract_unihan_syllables(unihan_path: str) -> Set[str]:
    """
    Extract all kMandarin readings from Unihan database.

    Returns set of syllables with tone marks (e.g., 'yī', 'hǎo', 'ma')
    """
    syllables = set()

    with open(unihan_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue

            # Look for kMandarin entries
            if '\tkMandarin\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    # Format: U+4E00\tkMandarin\tyī
                    reading = parts[2].strip()
                    if reading:
                        syllables.add(reading)

    return syllables


def split_multiple_readings(syllables: Set[str]) -> Set[str]:
    """
    Split entries with multiple readings separated by spaces.

    Input: {'biào biāo', 'yī'}
    Output: {'biào', 'biāo', 'yī'}
    """
    split_syllables = set()

    for syll in syllables:
        # Split by space to handle multiple readings
        parts = syll.split()
        for part in parts:
            part = part.strip()
            if part:
                split_syllables.add(part)

    return split_syllables


def convert_tone_mark_to_number(pinyin_with_mark: str) -> tuple[str, Optional[int]]:
    """
    Convert pinyin with tone marks to base + tone number.

    Input: 'yī' → ('yi', 1)
    Input: 'hǎo' → ('hao', 3)
    Input: 'ma' → ('ma', None)

    Tone marks:
    - Tone 1 (macron): ā ē ī ō ū ǖ
    - Tone 2 (acute):  á é í ó ú ǘ
    - Tone 3 (caron):  ǎ ě ǐ ǒ ǔ ǚ
    - Tone 4 (grave):  à è ì ò ù ǜ
    - Neutral: a e i o u ü (no marks)
    """
    # Mapping of tone mark characters to (base, tone)
    tone_map = {
        # Tone 1
        'ā': ('a', 1), 'ē': ('e', 1), 'ī': ('i', 1), 'ō': ('o', 1), 'ū': ('u', 1), 'ǖ': ('ü', 1),
        # Tone 2
        'á': ('a', 2), 'é': ('e', 2), 'í': ('i', 2), 'ó': ('o', 2), 'ú': ('u', 2), 'ǘ': ('ü', 2),
        # Tone 3
        'ǎ': ('a', 3), 'ě': ('e', 3), 'ǐ': ('i', 3), 'ǒ': ('o', 3), 'ǔ': ('u', 3), 'ǚ': ('ü', 3),
        # Tone 4
        'à': ('a', 4), 'è': ('e', 4), 'ì': ('i', 4), 'ò': ('o', 4), 'ù': ('u', 4), 'ǜ': ('ü', 4),
    }

    # Find tone mark in the syllable
    base_chars = []
    tone = None

    for char in pinyin_with_mark:
        if char in tone_map:
            base_char, tone = tone_map[char]
            base_chars.append(base_char)
        else:
            base_chars.append(char)

    base = ''.join(base_chars)
    return (base, tone)


def convert_to_tone3(syllables_with_marks: Set[str]) -> Set[str]:
    """
    Convert syllables with tone marks to tone3 format.

    Input: {'yī', 'hǎo', 'ma'}
    Output: {'yi1', 'hao3', 'ma0'}

    Note: Neutral tones are marked as 0 for AWS Polly compatibility.
    """
    tone3_syllables = set()

    for syll in syllables_with_marks:
        base, tone = convert_tone_mark_to_number(syll)
        if tone:
            tone3 = f"{base}{tone}"
        else:
            # Neutral tone: use 0 for AWS Polly
            tone3 = f"{base}0"
        tone3_syllables.add(tone3)

    return tone3_syllables


def create_syllable_metadata(
    tone3_syllables: Set[str],
    dataset_syllables: Set[str]
) -> List[Dict]:
    """
    Create metadata for each syllable.

    Returns list of dicts with:
    - base: base syllable without tone
    - tone: tone number (1-4) or None for neutral
    - pinyin_tone3: our format (e.g., 'lv4', 'ma')
    - filename: ASCII-safe filename (e.g., 'lv4')
    - exists_in_dataset: whether this syllable appears in our sentences
    """
    # Use dict to deduplicate by pinyin_tone3 (our canonical format with v)
    syllable_dict = {}

    for syll in tone3_syllables:
        # Extract base and tone
        # Format: 'yi1', 'hao3', 'ma' (neutral has no number)
        match = re.match(r'^([a-zü]+?)(\d?)$', syll)

        if not match:
            print(f"Warning: Could not parse syllable '{syll}', skipping")
            continue

        base = match.group(1)
        tone_str = match.group(2)
        tone = int(tone_str) if tone_str else None

        # Convert ü to v for our internal format (canonical key)
        base_v = base.replace('ü', 'v')
        pinyin_tone3 = f"{base_v}{tone_str}" if tone_str else base_v

        # Skip if we already have this syllable (prefer ü version from Unihan)
        if pinyin_tone3 in syllable_dict:
            continue

        # Keep proper pinyin with ü for display purposes
        base_proper = base_v.replace('v', 'ü')

        # Filename uses v (ASCII-safe)
        filename = pinyin_tone3

        # Check if this syllable exists in our dataset
        exists_in_dataset = pinyin_tone3 in dataset_syllables

        syllable_dict[pinyin_tone3] = {
            'base': base_v,  # Store v version as canonical
            'base_proper': base_proper,  # ü version for display
            'tone': tone,
            'pinyin_tone3': pinyin_tone3,
            'filename': filename,
            'exists_in_dataset': exists_in_dataset,
        }

    # Convert dict to sorted list
    return [syllable_dict[key] for key in sorted(syllable_dict.keys())]


def parse_sentence_dataset(csv_path: str) -> Set[str]:
    """
    Parse sentence dataset to extract all used pinyin+tone combinations.

    Returns set of pinyin_tone3 format strings (e.g., "han4", "ma0", "wo3")

    Note: Converts neutral tones from no-number format to '0' suffix format
    for AWS Polly compatibility (e.g., "ma" → "ma0").
    """
    used_syllables = set()

    if not Path(csv_path).exists():
        return used_syllables

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char_pinyin_pairs = row.get('char_pinyin_pairs', '')
            if not char_pinyin_pairs:
                continue

            # Format: 我:wo3|們:men|試:shi4|試:shi4|看:kan4|！:
            pairs = char_pinyin_pairs.split('|')
            for pair in pairs:
                if ':' not in pair:
                    continue
                char, pinyin = pair.split(':', 1)
                pinyin = pinyin.strip()
                if pinyin:  # Skip empty strings (punctuation)
                    # AWS Polly requires neutral tones to have explicit '0' suffix
                    # Convert "ma" → "ma0" for consistency
                    if not pinyin[-1].isdigit():
                        pinyin = f"{pinyin}0"
                    used_syllables.add(pinyin)

    return used_syllables


def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent
    unihan_path = project_root / 'data' / 'sources' / 'Unihan_Readings.txt'
    sentence_csv = project_root / 'data' / 'sentences' / 'cmn_sentences_with_char_pinyin.csv'
    output_json = project_root / 'data' / 'audio' / 'syllables_enumeration.json'

    # Create output directory
    output_json.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Mandarin Syllable Enumeration - Unihan Source")
    print("=" * 70)

    print("\nStep 1: Extracting syllables from Unihan database...")
    unihan_syllables = extract_unihan_syllables(str(unihan_path))
    print(f"  Found {len(unihan_syllables)} raw entries from Unihan")
    print(f"  Sample: {list(sorted(unihan_syllables))[:5]}")

    print("\nStep 2: Splitting multiple readings...")
    split_syllables = split_multiple_readings(unihan_syllables)
    print(f"  After splitting: {len(split_syllables)} unique syllables")
    print(f"  Sample: {list(sorted(split_syllables))[:5]}")

    print("\nStep 3: Converting tone marks to tone3 format...")
    tone3_syllables = convert_to_tone3(split_syllables)
    print(f"  Converted to tone3: {len(tone3_syllables)} syllables")
    print(f"  Sample: {sorted(tone3_syllables)[:10]}")

    print("\nStep 4: Parsing sentence dataset to find used syllables...")
    dataset_syllables = parse_sentence_dataset(str(sentence_csv))
    print(f"  Found {len(dataset_syllables)} unique syllables in dataset")

    # Add any dataset syllables missing from Unihan
    # (These are typically special cases or variations)
    missing_from_unihan = dataset_syllables - tone3_syllables
    if missing_from_unihan:
        # Remove empty strings and punctuation
        missing_from_unihan = {s for s in missing_from_unihan if s and s != ':'}
        if missing_from_unihan:
            print(f"\n  Adding {len(missing_from_unihan)} syllables from dataset not in Unihan:")
            print(f"  {sorted(missing_from_unihan)[:10]}")
            tone3_syllables.update(missing_from_unihan)

    print("\nStep 5: Generating syllable metadata...")
    syllable_list = create_syllable_metadata(tone3_syllables, dataset_syllables)

    # Calculate statistics
    total = len(syllable_list)
    used = sum(1 for s in syllable_list if s['exists_in_dataset'])
    coverage = (used / total * 100) if total > 0 else 0

    # Check if all dataset syllables are covered
    enumerated_set = {s['pinyin_tone3'] for s in syllable_list}
    missing_from_unihan = dataset_syllables - enumerated_set

    print("\nStep 6: Writing output JSON...")
    metadata = {
        'metadata': {
            'total_syllables': total,
            'used_in_dataset': used,
            'coverage_percent': round(coverage, 2),
            'dataset_source': 'cmn_sentences_with_char_pinyin.csv',
            'canonical_source': 'Unihan_Readings.txt (kMandarin)',
            'missing_from_unihan': len(missing_from_unihan),
        },
        'syllables': syllable_list,
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("✓ Syllable enumeration complete!")
    print("=" * 70)
    print(f"\nOutput: {output_json}")
    print(f"\nSummary:")
    print(f"  Total Unihan syllables:     {total}")
    print(f"  Used in our dataset:        {used} ({coverage:.1f}%)")
    print(f"  Unused but valid:           {total - used}")

    if missing_from_unihan:
        print(f"\n  WARNING: {len(missing_from_unihan)} syllables in dataset NOT found in Unihan:")
        for syll in sorted(missing_from_unihan)[:10]:
            print(f"    - {syll}")
        if len(missing_from_unihan) > 10:
            print(f"    ... and {len(missing_from_unihan) - 10} more")
    else:
        print(f"\n  ✓ All dataset syllables covered by Unihan!")

    # Show examples
    print(f"\n" + "=" * 70)
    print("Example syllables:")
    print("=" * 70)

    print("\nUsed in dataset (first 10):")
    used_examples = [s for s in syllable_list if s['exists_in_dataset']][:10]
    for s in used_examples:
        tone_display = f"tone {s['tone']}" if s['tone'] else "neutral"
        print(f"  {s['pinyin_tone3']:8} ({tone_display:8}) -> {s['filename']}.ogg")

    print("\nNOT used in dataset (first 10):")
    unused_examples = [s for s in syllable_list if not s['exists_in_dataset']][:10]
    for s in unused_examples:
        tone_display = f"tone {s['tone']}" if s['tone'] else "neutral"
        print(f"  {s['pinyin_tone3']:8} ({tone_display:8}) -> {s['filename']}.ogg")

    # Show lv/nv examples
    lv_syllables = [s for s in syllable_list if 'v' in s['pinyin_tone3']]
    if lv_syllables:
        print(f"\nü→v conversion examples ({len(lv_syllables)} total):")
        for s in lv_syllables[:5]:
            used = "✓" if s['exists_in_dataset'] else " "
            print(f"  [{used}] {s['pinyin_tone3']:8} (display: {s['base_proper']}, filename: {s['filename']}.ogg)")

    print("\n" + "=" * 70)
    print("Ready for TTS generation!")
    print("=" * 70)


if __name__ == '__main__':
    main()
