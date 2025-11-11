#!/usr/bin/env python3
"""
Build a character-level Trie of all Chinese pinyin syllables from the SOT v1.0 dataset.

This is the v1 adaptation - differences from v0:
- Input: 97,712 characters from sot_characters_v1.0.csv (vs 20,992 from corpus)
- No frequency data in pinyins (just "yi1" not "yi1(8867)")
- Filters out CJK-as-pinyin (pypinyin fallback characters)
- Trie nodes store only character lists (no frequency metadata)
- Statistics are count-based only

Each node represents ONE letter in tone3 format (tone numbers).
Terminal nodes store a list of characters that produce that pinyin.

Input:
- ../../../data/character_set/v1/sot_characters_v1.0.csv (uses pinyins_tone3 column)

Output:
- ../../../data/character_set/v1/analysis/pinyin_trie.json
- Console statistics about syllable distribution
"""
import csv
import json
import re
from pathlib import Path
from collections import defaultdict


# CJK Unicode range for detecting CJK-as-pinyin
# Covers all blocks from Extension A through Extension H
CJK_RANGE_START = 0x3400
CJK_RANGE_END = 0x323AF


def is_cjk_as_pinyin(pinyin_str):
    """
    Check if pinyin is actually a CJK character (pypinyin fallback).

    When pypinyin doesn't recognize a character, it returns the character itself.
    Examples: '㐂', '㐃', '㐇'

    Returns: True if pinyin contains CJK characters
    """
    if not pinyin_str:
        return False

    return any(CJK_RANGE_START <= ord(c) <= CJK_RANGE_END for c in pinyin_str)


def normalize_to_tone3(pinyin_str):
    """
    Ensure pinyin is in tone3 format with explicit tone number.

    v1's pinyins_tone3 column stores neutral tone without "0" suffix:
    - "de" should become "de0"
    - "yi1" is already correct

    Returns: pinyin with explicit tone number
    """
    if not pinyin_str:
        return pinyin_str

    # Check if already ends with a digit (0-4)
    if re.search(r'\d$', pinyin_str):
        return pinyin_str  # Already in tone3 format

    # No tone digit, add neutral tone "0"
    return pinyin_str + '0'


def parse_pinyin_field(pinyins_str):
    """
    Parse the pinyins_tone3 field to extract individual pinyin syllables.

    v1 format: "yi1|yi2|yi4" (no frequency annotations)
    Note: Neutral tones stored without "0" (e.g., "de" not "de0")

    Filters out:
    - Empty strings
    - CJK-as-pinyin (pypinyin fallback)

    Normalizes:
    - Adds "0" suffix to neutral tones (de → de0)

    Returns: list of normalized pinyin strings
    """
    if not pinyins_str or pinyins_str.strip() == '':
        return []

    result = []
    for part in pinyins_str.split('|'):
        part = part.strip()
        if not part:
            continue

        # Filter out CJK-as-pinyin
        if is_cjk_as_pinyin(part):
            continue

        # Normalize to ensure explicit tone number
        normalized = normalize_to_tone3(part)
        result.append(normalized)

    return result


def build_trie(characters_data):
    """
    Build character-level Trie from character data.

    v1 simplification: No frequency data, just character lists

    Each node structure:
    {
      "children": {letter: node},
      "is_end": bool,
      "characters": [char1, char2, ...],  # Only at terminal nodes
      "count": int  # Only at terminal nodes (number of unique characters)
    }

    Args:
        characters_data: List of dicts with 'char', 'pinyins_tone3' fields

    Returns:
        Dict representing the root of the Trie
    """
    root = {"children": {}, "is_end": False}

    # syllable -> set of characters (use set to deduplicate)
    syllable_chars = defaultdict(set)

    # Track filtering statistics
    stats = {
        'total_chars': 0,
        'chars_with_valid_pinyin': 0,
        'chars_filtered_cjk': 0,
        'total_syllables': 0
    }

    for row in characters_data:
        char = row['char']
        pinyins_str = row.get('pinyins_tone3', '')

        stats['total_chars'] += 1

        # Skip if no pinyin data
        if not pinyins_str or pinyins_str.strip() == '':
            continue

        # Parse pinyin field (filters out CJK-as-pinyin)
        pinyin_list = parse_pinyin_field(pinyins_str)

        # Track filtering
        original_count = len(pinyins_str.split('|'))
        filtered_count = original_count - len(pinyin_list)
        if filtered_count > 0:
            stats['chars_filtered_cjk'] += 1

        # Skip characters with no valid pinyins
        if not pinyin_list:
            continue

        stats['chars_with_valid_pinyin'] += 1
        stats['total_syllables'] += len(pinyin_list)

        # Add each pinyin to collection
        for pinyin in pinyin_list:
            syllable_chars[pinyin].add(char)

    # Now build the trie from collected syllables
    for pinyin, chars_set in syllable_chars.items():
        # Convert set to sorted list
        chars_list = sorted(chars_set)

        # Walk character by character through pinyin
        node = root
        for letter in pinyin:
            if letter not in node["children"]:
                node["children"][letter] = {"children": {}, "is_end": False}
            node = node["children"][letter]

        # Mark as terminal and store character list
        node["is_end"] = True
        node["characters"] = chars_list
        node["count"] = len(chars_list)

    return root, stats


def collect_all_syllables(node, prefix=""):
    """
    Recursively collect all complete syllables from the Trie.

    Returns: list of (syllable, char_count) tuples
    """
    syllables = []

    if node.get("is_end"):
        syllables.append((
            prefix,
            node["count"]
        ))

    for letter, child in node.get("children", {}).items():
        syllables.extend(collect_all_syllables(child, prefix + letter))

    return syllables


def generate_statistics(trie, build_stats):
    """
    Generate statistics about the Trie.
    """
    print(f"\n{'='*70}")
    print("PINYIN TRIE STATISTICS (v1 - SOT Dataset)")
    print(f"{'='*70}\n")

    # Build statistics
    print("Build Statistics:")
    print(f"  Total characters in dataset: {build_stats['total_chars']:,}")
    print(f"  Characters with valid pinyin: {build_stats['chars_with_valid_pinyin']:,} ({build_stats['chars_with_valid_pinyin']/build_stats['total_chars']*100:.1f}%)")
    print(f"  Characters filtered (CJK-as-pinyin): {build_stats['chars_filtered_cjk']:,}")
    print(f"  Total syllable instances: {build_stats['total_syllables']:,}")

    # Collect all syllables
    syllables = collect_all_syllables(trie)
    syllables.sort(key=lambda x: x[1], reverse=True)  # Sort by char count

    print(f"\nTrie Statistics:")
    print(f"  Total unique pinyin syllables: {len(syllables):,}")

    # Character count distribution
    char_counts = [s[1] for s in syllables]
    print(f"\nCharacter count per syllable:")
    print(f"  Min: {min(char_counts)}")
    print(f"  Max: {max(char_counts)}")
    print(f"  Mean: {sum(char_counts) / len(char_counts):.1f}")
    print(f"  Median: {sorted(char_counts)[len(char_counts)//2]}")
    print(f"  Total characters: {sum(char_counts):,}")

    # Top 20 syllables with most characters (polyphonic)
    print(f"\nTop 20 syllables with most characters:")
    for i, (syllable, char_count) in enumerate(syllables[:20], 1):
        print(f"  {i:2d}. {syllable:8s} - {char_count:2d} chars")

    # Tone distribution analysis (tone3 format)
    tone_syllables = defaultdict(list)
    for syllable, char_count in syllables:
        # Extract tone number from end
        tone_match = re.search(r'(\d)$', syllable)
        if tone_match:
            tone = tone_match.group(1)
            if tone == '0':
                tone_syllables['neutral'].append(syllable)
            else:
                tone_syllables[f'tone{tone}'].append(syllable)
        else:
            tone_syllables['unknown'].append(syllable)

    print(f"\nTone distribution (tone3 format):")
    for tone_key in ['tone1', 'tone2', 'tone3', 'tone4', 'neutral', 'unknown']:
        count = len(tone_syllables[tone_key])
        if count > 0:
            print(f"  {tone_key.capitalize():12s}: {count:,} syllables ({count/len(syllables)*100:.1f}%)")

    # Example neutral tone syllables
    if tone_syllables['neutral']:
        examples = ', '.join(tone_syllables['neutral'][:20])
        print(f"\n  Example neutral tone (first 20): {examples}")

    print(f"\n{'='*70}")

    return syllables


def save_trie_json(trie, output_path):
    """
    Save Trie to JSON file.
    """
    print(f"\nSaving Trie to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trie, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved Trie to {output_path}")


def load_character_data(csv_path='../../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """
    Load character data from SOT v1.0 CSV.
    Returns all characters (filtering happens during trie build).
    """
    print(f"Loading character data from {csv_path}...")

    characters = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)

    print(f"✓ Loaded {len(characters):,} characters from SOT v1.0 dataset")

    return characters


if __name__ == '__main__':
    print("=" * 70)
    print("Build Pinyin Trie - v1 (SOT Dataset)")
    print("=" * 70)
    print("\nNote: Filters out CJK-as-pinyin (pypinyin fallback characters)")
    print("      No frequency data in v1 (corpus-independent)")

    # Load character data
    characters = load_character_data()

    # Build Trie
    print("\nBuilding character-level Trie...")
    trie, build_stats = build_trie(characters)
    print("✓ Trie construction complete")

    # Generate statistics
    syllables = generate_statistics(trie, build_stats)

    # Save to JSON
    output_path = Path('../../../../data/character_set/v1/analysis/pinyin_trie.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_trie_json(trie, output_path)

    print("\n" + "=" * 70)
    print("✓ Pinyin Trie build complete!")
    print("=" * 70)
    print(f"\nOutput: {output_path}")
    print(f"Total syllables: {len(syllables):,}")
    print("\nNext steps:")
    print("  1. Run analyze_trie.py for detailed analysis and charts")
    print("  2. Run compare_v0_v1_tries.py to compare with v0 corpus-based trie")
