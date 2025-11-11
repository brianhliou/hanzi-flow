#!/usr/bin/env python3
"""
Export v1 character set to production CSV format.

This script:
1. Analyzes sentence corpus to find which characters are actually used
2. Filters v1 (97k SOT characters) to only corpus-used characters (~5k)
3. Calculates character frequencies from corpus
4. Enriches with v0 metadata (variants, examples, hsk_level) where available
5. Outputs production-ready CSV with optimized columns

Input:
- data/character_set/v1/sot_characters_v1.0.csv (97k characters)
- data/sentences/step5_pinyin_refined.csv (sentence corpus)
- data/character_set/v0/step5_hsk.csv (v0 metadata for enrichment)

Output:
- data/character_set/v1/production/chinese_characters_v1.csv

Production CSV format (5 columns - only used columns):
- id,char,pinyins,script_type,hsk_level

Filtered columns (unused by app):
- codepoint, variants, gloss_en, examples

Note:
- pinyins uses tone marks format (yī|yí|yì) without frequencies
- Only characters appearing in sentence corpus are included
- Only columns actually used by the app are exported
"""

import csv
from pathlib import Path
from typing import Dict, Set
from collections import Counter


def extract_characters_from_corpus(corpus_path: Path) -> Dict[str, int]:
    """
    Extract unique characters and their frequencies from sentence corpus.

    Returns:
        dict mapping character → frequency count
    """
    char_freq = Counter()

    with open(corpus_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            char_pinyin_pairs = row.get('char_pinyin_pairs', '')

            # Parse: 我:wo3|們:men|試:shi4|試:shi4|看:kan4|！:
            pairs = char_pinyin_pairs.split('|')
            for pair in pairs:
                if ':' in pair:
                    char = pair.split(':')[0]
                    if char:  # Skip empty
                        char_freq[char] += 1

    return dict(char_freq)


def load_v1_characters(v1_path: Path) -> Dict[str, Dict]:
    """
    Load v1 character set.

    Returns:
        dict mapping character → {id, codepoint, pinyins_display, script_type, gloss_en}
    """
    v1_chars = {}

    with open(v1_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            char = row['char']
            v1_chars[char] = {
                'id': row['id'],
                'codepoint': row['codepoint'],
                'pinyins_display': row['pinyins_display'],
                'script_type': row['script_type'],
                'gloss_en': row.get('gloss_en', ''),
            }

    return v1_chars


def load_v0_metadata(v0_path: Path) -> Dict[str, Dict]:
    """
    Load v0 metadata for enrichment (id, variants, examples, hsk_level).

    IMPORTANT: Also preserves the original character ID from v0.
    This ensures existing IndexedDB progress data continues to work.

    Returns:
        dict mapping character → {id, variants, examples, hsk_level}
    """
    v0_metadata = {}

    with open(v0_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            char = row['char']
            v0_metadata[char] = {
                'id': int(row['id']),  # Preserve original ID
                'variants': row.get('variants', ''),
                'examples': row.get('examples', ''),
                'hsk_level': row.get('hsk_level', ''),
            }

    return v0_metadata


def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    v1_path = project_root / 'data' / 'character_set' / 'v1' / 'sot_characters_v1.0.csv'
    corpus_path = project_root / 'data' / 'sentences' / 'step5_pinyin_refined.csv'
    v0_metadata_path = project_root / 'data' / 'character_set' / 'v0' / 'step5_hsk.csv'
    output_path = project_root / 'data' / 'character_set' / 'v1' / 'production' / 'chinese_characters_v1.csv'

    print("=" * 80)
    print("Export v1 Character Set to Production CSV")
    print("=" * 80)

    # Step 1: Extract characters from corpus
    print(f"\n[1/5] Analyzing sentence corpus: {corpus_path}")
    char_freq = extract_characters_from_corpus(corpus_path)
    print(f"✓ Found {len(char_freq):,} unique characters in corpus")
    print(f"  Total character occurrences: {sum(char_freq.values()):,}")

    # Show frequency stats
    freqs = sorted(char_freq.values(), reverse=True)
    print(f"\n  Frequency distribution:")
    print(f"    Most common: {freqs[0]:,} occurrences")
    print(f"    Median: {freqs[len(freqs)//2]:,}")
    print(f"    Least common: {freqs[-1]:,}")

    # Step 2: Load v1 character set
    print(f"\n[2/5] Loading v1 character set: {v1_path}")
    v1_chars = load_v1_characters(v1_path)
    print(f"✓ Loaded {len(v1_chars):,} v1 characters")

    # Step 3: Filter v1 to corpus characters
    print(f"\n[3/5] Filtering v1 to corpus-used characters...")
    filtered_chars = {}
    missing_in_v1 = []

    for char in char_freq.keys():
        if char in v1_chars:
            filtered_chars[char] = v1_chars[char]
            filtered_chars[char]['freq'] = char_freq[char]
        else:
            missing_in_v1.append(char)

    print(f"✓ Filtered to {len(filtered_chars):,} characters")
    print(f"  Reduction: {len(v1_chars):,} → {len(filtered_chars):,} ({len(filtered_chars)/len(v1_chars)*100:.1f}%)")

    if missing_in_v1:
        print(f"\n  ⚠️  {len(missing_in_v1)} corpus characters NOT in v1:")
        for char in missing_in_v1[:20]:
            print(f"     '{char}' (freq: {char_freq[char]})")
        if len(missing_in_v1) > 20:
            print(f"     ... and {len(missing_in_v1) - 20} more")

    # Step 4: Load v0 metadata for enrichment
    print(f"\n[4/5] Loading v0 metadata for enrichment: {v0_metadata_path}")
    v0_metadata = load_v0_metadata(v0_metadata_path)
    print(f"✓ Loaded metadata for {len(v0_metadata):,} v0 characters")

    # Enrich filtered characters with v0 metadata and preserve IDs
    enriched_count = 0
    new_chars = []

    # Find max v0 ID to assign new IDs after it
    max_v0_id = max((meta['id'] for meta in v0_metadata.values()), default=0)
    next_new_id = max_v0_id + 1

    for char, data in filtered_chars.items():
        if char in v0_metadata:
            # Preserve v0 ID and metadata
            data['preserved_id'] = v0_metadata[char]['id']
            data['variants'] = v0_metadata[char]['variants']
            data['examples'] = v0_metadata[char]['examples']
            data['hsk_level'] = v0_metadata[char]['hsk_level']
            enriched_count += 1
        else:
            # New character not in v0 - assign new ID
            data['preserved_id'] = next_new_id
            data['variants'] = ''
            data['examples'] = ''
            data['hsk_level'] = ''
            new_chars.append(char)
            next_new_id += 1

    print(f"  ✓ Enriched {enriched_count:,} characters with v0 metadata (IDs preserved)")
    print(f"  ✓ {len(new_chars):,} new characters (assigned IDs {max_v0_id + 1} - {next_new_id - 1})")

    if new_chars:
        print(f"\n  New v1 characters (first 20):")
        for char in new_chars[:20]:
            freq = filtered_chars[char]['freq']
            char_id = filtered_chars[char]['preserved_id']
            print(f"     '{char}' (freq: {freq:,}, new ID: {char_id})")
        if len(new_chars) > 20:
            print(f"     ... and {len(new_chars) - 20} more")

    # Step 5: Write production CSV
    print(f"\n[5/5] Writing production CSV: {output_path}")

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort by preserved ID (maintains v0 order + new characters at end)
    sorted_chars = sorted(
        filtered_chars.items(),
        key=lambda x: x[1]['preserved_id']
    )

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        # Production CSV columns (only used columns)
        # Based on app analysis: id, char, pinyins, script_type, hsk_level are used
        # Unused: codepoint, variants, gloss_en, examples
        fieldnames = [
            'id',
            'char',
            'pinyins',
            'script_type',
            'hsk_level'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Write characters using preserved IDs
        for char, data in sorted_chars:
            writer.writerow({
                'id': data['preserved_id'],  # Use preserved ID from v0 or newly assigned
                'char': char,
                'pinyins': data['pinyins_display'],  # Use tone marks format
                'script_type': data['script_type'],
                'hsk_level': data.get('hsk_level', ''),
            })

    print(f"✓ Wrote {len(sorted_chars):,} characters to production CSV")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Input v1 characters:        {len(v1_chars):,}")
    print(f"  Corpus unique characters:   {len(char_freq):,}")
    print(f"  Production characters:      {len(filtered_chars):,}")
    print(f"  Enriched from v0:           {enriched_count:,}")
    print(f"  New in v1:                  {len(new_chars):,}")
    print(f"\n  Output: {output_path}")
    print("=" * 80)

    # File size comparison
    import os
    output_size = os.path.getsize(output_path)
    print(f"\n  Production CSV size: {output_size:,} bytes ({output_size/1024:.1f} KB)")

    print("\n✓ Production CSV export complete!")


if __name__ == '__main__':
    main()
