#!/usr/bin/env python3
"""
Fix pinyin format inconsistency in chinese_characters.csv

Problem: Mixed formats from build_step6 enrichment
- Existing: tone marks (zhòng, chóng)
- Added: tone numbers (tong2)

Solution: Convert all TONE3 format → TONE format (tone marks)
"""

import csv
import re
from pathlib import Path

# Reverse mapping: tone number → tone mark
# Based on enumerate_syllables_unihan.py logic
TONE_NUMBER_TO_MARK = {
    'a': {1: 'ā', 2: 'á', 3: 'ǎ', 4: 'à'},
    'e': {1: 'ē', 2: 'é', 3: 'ě', 4: 'è'},
    'i': {1: 'ī', 2: 'í', 3: 'ǐ', 4: 'ì'},
    'o': {1: 'ō', 2: 'ó', 3: 'ǒ', 4: 'ò'},
    'u': {1: 'ū', 2: 'ú', 3: 'ǔ', 4: 'ù'},
    'ü': {1: 'ǖ', 2: 'ǘ', 3: 'ǚ', 4: 'ǜ'},
    'v': {1: 'ǖ', 2: 'ǘ', 3: 'ǚ', 4: 'ǜ'},  # v is alternate for ü
}


def convert_tone3_to_tone_mark(pinyin_tone3: str) -> str:
    """
    Convert TONE3 format (tone numbers) to TONE format (tone marks).

    Examples:
        'tong2' → 'tóng'
        'shei2' → 'shéi'
        'de' → 'de' (neutral tone, unchanged)
        'zhong4' → 'zhòng'

    Algorithm:
    1. Extract tone number (1-4) from end
    2. Find the vowel to mark (a/o/e first, then i/u/ü)
    3. Replace vowel with tone-marked version
    """
    # Check if ends with tone number (1-4)
    match = re.match(r'^(.+?)([1-4])$', pinyin_tone3)
    if not match:
        # No tone number = neutral tone, return as-is
        return pinyin_tone3

    base = match.group(1)
    tone = int(match.group(2))

    # Find which vowel to mark (pinyin tone placement rules)
    # Priority: a > o > e > i/u (last one if both)
    # Special: iu → iū, ui → uì

    # Convert to list for easy manipulation
    chars = list(base)

    # Find vowel to mark
    vowel_index = -1

    # Rule 1: 'a' or 'o' always gets the tone
    for i, char in enumerate(chars):
        if char in ['a', 'o']:
            vowel_index = i
            break

    # Rule 2: 'e' gets the tone
    if vowel_index == -1:
        for i, char in enumerate(chars):
            if char == 'e':
                vowel_index = i
                break

    # Rule 3: If i and u together, mark the second one
    if vowel_index == -1:
        # Find 'iu' or 'ui'
        for i in range(len(chars) - 1):
            if chars[i] in ['i', 'u'] and chars[i+1] in ['i', 'u']:
                vowel_index = i + 1
                break

    # Rule 4: Mark any remaining vowel
    if vowel_index == -1:
        for i, char in enumerate(chars):
            if char in ['i', 'u', 'ü', 'v']:
                vowel_index = i
                break

    # If we found a vowel, apply tone mark
    if vowel_index != -1:
        vowel = chars[vowel_index]
        if vowel in TONE_NUMBER_TO_MARK and tone in TONE_NUMBER_TO_MARK[vowel]:
            chars[vowel_index] = TONE_NUMBER_TO_MARK[vowel][tone]

    return ''.join(chars)


def has_tone_number(pinyin: str) -> bool:
    """Check if pinyin string ends with a tone number (1-4)."""
    return bool(re.search(r'[1-4]$', pinyin))


def fix_pinyin_field(pinyins_str: str) -> tuple[str, int]:
    """
    Fix mixed format pinyins in a field.

    Returns: (fixed_string, count_converted)
    """
    if not pinyins_str or pinyins_str.strip() == '':
        return pinyins_str, 0

    parts = pinyins_str.split('|')
    converted_count = 0
    fixed_parts = []

    for part in parts:
        # Extract base pinyin (remove frequency count)
        pinyin_match = re.match(r'^([^(]+)(\(\d+\))?$', part.strip())
        if not pinyin_match:
            fixed_parts.append(part)
            continue

        pinyin = pinyin_match.group(1)
        freq = pinyin_match.group(2) or ''

        # Convert if has tone number
        if has_tone_number(pinyin):
            converted = convert_tone3_to_tone_mark(pinyin)
            fixed_parts.append(converted + freq)
            converted_count += 1
        else:
            fixed_parts.append(part)

    return '|'.join(fixed_parts), converted_count


def fix_csv(
    input_file: str = '../../app/public/data/character_set/chinese_characters.csv',
    output_file: str = '../../app/public/data/character_set/chinese_characters_fixed.csv'
):
    """
    Fix pinyin format in CSV file.
    """
    print("=" * 70)
    print("Fix Pinyin Format Inconsistency")
    print("=" * 70)

    # Read input
    print(f"\nReading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        characters = list(reader)

    print(f"Loaded {len(characters):,} characters")

    # Fix pinyins
    print("\nConverting TONE3 → TONE format...")
    total_conversions = 0
    affected_chars = 0
    examples = []

    for i, row in enumerate(characters, 1):
        char = row['char']
        pinyins_before = row.get('pinyins', '')

        pinyins_after, count = fix_pinyin_field(pinyins_before)

        if count > 0:
            row['pinyins'] = pinyins_after
            total_conversions += count
            affected_chars += 1

            # Collect examples
            if len(examples) < 10:
                examples.append({
                    'char': char,
                    'before': pinyins_before,
                    'after': pinyins_after,
                    'count': count
                })

        if i % 5000 == 0:
            print(f"  Processed {i:,} characters... ({affected_chars:,} fixed)")

    # Write output
    print(f"\nWriting: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(characters)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total characters:         {len(characters):,}")
    print(f"Characters affected:      {affected_chars:,} ({affected_chars/len(characters)*100:.1f}%)")
    print(f"Total conversions:        {total_conversions:,}")

    # Show examples
    if examples:
        print("\n" + "=" * 70)
        print("EXAMPLES (first 10 conversions)")
        print("=" * 70)
        for ex in examples:
            print(f"\n{ex['char']}:")
            print(f"  Before: {ex['before']}")
            print(f"  After:  {ex['after']}")
            print(f"  Count:  {ex['count']} conversions")

    print("\n" + "=" * 70)
    print("✓ Fix complete!")
    print("=" * 70)
    print("\nNext steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. If looks good, replace original:")
    print(f"     mv {output_file} {input_file}")
    print(f"  3. Also copy to: ../../data/chinese_characters.csv")


if __name__ == '__main__':
    fix_csv()
