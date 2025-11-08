#!/usr/bin/env python3
"""
Analyze Step 2 output for anomalies and quality issues.

Checks for:
1. Characters returned as "pinyin" (pypinyin doesn't recognize)
2. Non-Latin characters in pinyin
3. Invalid tone numbers (not 0-4)
4. Invalid tone marks
5. Distribution by Unicode block
"""

import csv
import re
from collections import defaultdict


# Unicode block boundaries
BLOCKS = [
    ("Extension A", 0x3400, 0x4DBF),
    ("CJK Core", 0x4E00, 0x9FFF),
    ("Extension B", 0x20000, 0x2A6DF),
    ("Extension C", 0x2A700, 0x2B73F),
    ("Extension D", 0x2B740, 0x2B81F),
    ("Extension E", 0x2B820, 0x2CEAF),
    ("Extension F", 0x2CEB0, 0x2EBEF),
    ("Extension I", 0x2EBF0, 0x2EE5F),
    ("Extension G", 0x30000, 0x3134F),
    ("Extension H", 0x31350, 0x323AF),
]


def get_block_name(codepoint_str):
    """Get Unicode block name from codepoint string like U+4E00."""
    code = int(codepoint_str[2:], 16)
    for name, start, end in BLOCKS:
        if start <= code <= end:
            return name
    return "Unknown"


def is_valid_pinyin(pinyin_str):
    """
    Check if a pinyin string looks valid (Latin letters only).
    Returns (is_valid, reason)
    """
    if not pinyin_str:
        return False, "empty"

    # Check if it's just the character itself (CJK character as pinyin)
    if any(0x3400 <= ord(c) <= 0x323AF for c in pinyin_str):
        return False, "contains_cjk"

    # Check if it contains only Latin letters, digits (for tone3), and valid tone marks
    # Valid: a-z, A-Z, 0-9, and tone marks: āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüńň
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    tone_marks = set("āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüńň")

    for char in pinyin_str:
        if char not in valid_chars and char not in tone_marks:
            return False, f"invalid_char_{char}"

    return True, "valid"


def check_tone_numbers(tone3_str):
    """Check for invalid tone numbers in tone3 format."""
    invalid_tones = []
    for syllable in tone3_str.split('|'):
        # Extract digits from syllable
        digits = re.findall(r'\d+', syllable)
        for d in digits:
            if d not in ['0', '1', '2', '3', '4']:
                invalid_tones.append(d)
    return invalid_tones


def analyze_csv(csv_file='../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """Comprehensive analysis of Step 2 output."""

    print("=" * 80)
    print("STEP 2 OUTPUT ANALYSIS")
    print("=" * 80)
    print()

    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Statistics by block
    block_stats = defaultdict(lambda: {
        'total': 0,
        'valid_pinyin': 0,
        'contains_cjk': 0,
        'invalid_chars': 0,
        'empty': 0
    })

    # Overall statistics
    total_chars = len(rows)
    valid_count = 0
    invalid_count = 0
    invalid_tones = []

    # Examples
    cjk_as_pinyin_examples = []
    invalid_char_examples = []
    unrenderable_with_valid = []

    for row in rows:
        char = row['char']
        codepoint = row['codepoint']
        tone3 = row['pinyins_tone3']
        display = row['pinyins_display']

        block = get_block_name(codepoint)
        block_stats[block]['total'] += 1

        # Check each syllable in tone3
        for syllable in tone3.split('|'):
            is_valid, reason = is_valid_pinyin(syllable)

            if is_valid:
                block_stats[block]['valid_pinyin'] += 1
                valid_count += 1

                # Check if character is unrenderable (beyond BMP + Ext A)
                code = int(codepoint[2:], 16)
                if code > 0x4DBF:  # Beyond Extension A
                    unrenderable_with_valid.append((char, codepoint, tone3, display))

            else:
                invalid_count += 1
                if reason == "contains_cjk":
                    block_stats[block]['contains_cjk'] += 1
                    if len(cjk_as_pinyin_examples) < 20:
                        cjk_as_pinyin_examples.append((char, codepoint, tone3, display, block))
                elif reason == "empty":
                    block_stats[block]['empty'] += 1
                else:
                    block_stats[block]['invalid_chars'] += 1
                    if len(invalid_char_examples) < 20:
                        invalid_char_examples.append((char, codepoint, tone3, display, reason, block))

        # Check for invalid tone numbers
        bad_tones = check_tone_numbers(tone3)
        if bad_tones:
            invalid_tones.extend([(char, codepoint, tone3, bad_tones)])

    # Print results
    print("SUMMARY BY UNICODE BLOCK")
    print("-" * 80)
    print(f"{'Block':<15} {'Total':>8} {'Valid':>8} {'CJK':>8} {'Invalid':>8} {'Empty':>8}")
    print("-" * 80)

    for block_name, start, end in BLOCKS:
        stats = block_stats[block_name]
        total = stats['total']
        valid = stats['valid_pinyin']
        cjk = stats['contains_cjk']
        invalid = stats['invalid_chars']
        empty = stats['empty']

        print(f"{block_name:<15} {total:>8,} {valid:>8,} {cjk:>8,} {invalid:>8,} {empty:>8,}")

    print("-" * 80)
    print(f"{'TOTAL':<15} {total_chars:>8,} {valid_count:>8,} "
          f"{sum(s['contains_cjk'] for s in block_stats.values()):>8,} "
          f"{sum(s['invalid_chars'] for s in block_stats.values()):>8,} "
          f"{sum(s['empty'] for s in block_stats.values()):>8,}")

    print()
    print("OVERALL STATISTICS")
    print("-" * 80)
    print(f"Total characters:        {total_chars:>8,}")
    print(f"Valid pinyin syllables:  {valid_count:>8,} ({valid_count/(valid_count+invalid_count)*100:.1f}%)")
    print(f"Invalid pinyin:          {invalid_count:>8,} ({invalid_count/(valid_count+invalid_count)*100:.1f}%)")

    print()
    print("EXAMPLES: CJK Character as Pinyin (first 20)")
    print("-" * 80)
    for char, codepoint, tone3, display, block in cjk_as_pinyin_examples[:20]:
        print(f"{char} ({codepoint}) [{block}]")
        print(f"  tone3:   {tone3}")
        print(f"  display: {display}")

    if invalid_char_examples:
        print()
        print("EXAMPLES: Invalid Characters in Pinyin (first 20)")
        print("-" * 80)
        for char, codepoint, tone3, display, reason, block in invalid_char_examples[:20]:
            print(f"{char} ({codepoint}) [{block}] - {reason}")
            print(f"  tone3:   {tone3}")
            print(f"  display: {display}")

    if invalid_tones:
        print()
        print("INVALID TONE NUMBERS FOUND")
        print("-" * 80)
        for char, codepoint, tone3, bad_tones in invalid_tones[:20]:
            print(f"{char} ({codepoint}): {tone3}")
            print(f"  Bad tones: {bad_tones}")
    else:
        print()
        print("✓ All tone numbers are valid (0-4)")

    print()
    print("UNRENDERABLE CHARS WITH VALID PINYIN (first 20)")
    print("-" * 80)
    for char, codepoint, tone3, display in unrenderable_with_valid[:20]:
        code = int(codepoint[2:], 16)
        block = get_block_name(codepoint)
        print(f"{char} ({codepoint}) [{block}]")
        print(f"  tone3:   {tone3}")
        print(f"  display: {display}")

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    analyze_csv()
