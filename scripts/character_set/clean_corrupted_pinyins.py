#!/usr/bin/env python3
"""
Clean Corrupted Pinyins from CSV

Removes invalid pinyin entries that have:
1. Numbers mixed in (e.g., "lǔ 74609.020")
2. Special combining diacritics (e.g., "m̀", "ê̌")
3. Chinese characters in the pinyin field (e.g., "兙")

These are data quality issues from the source (Unihan database).
"""

import csv
import re
from pathlib import Path

def is_corrupted_pinyin(pinyin):
    """
    Check if a pinyin string is corrupted.

    Returns: (is_corrupted, reason)
    """
    if not pinyin:
        return False, None

    # Check for numbers (after stripping frequency data)
    if re.search(r'\d', pinyin):
        return True, 'has_numbers'

    # Check for combining diacritical marks (U+0300-U+036F)
    # These are special phonetic marks, not standard Mandarin pinyin
    if re.search(r'[\u0300-\u036f]', pinyin):
        return True, 'has_special_marks'

    # Check if first character is a CJK character (U+4E00-U+9FFF)
    # This means the pinyin field contains a Chinese character instead of pronunciation
    if pinyin and ord(pinyin[0]) >= 0x4E00:
        return True, 'is_chinese_char'

    return False, None

def strip_frequency(pinyin):
    """Strip frequency data like (1234) from pinyin."""
    return re.sub(r'\(\d+\)', '', pinyin).strip()

def main():
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / 'app/public/data/character_set/chinese_characters.csv'

    print("=" * 80)
    print("Cleaning Corrupted Pinyins from CSV")
    print("=" * 80)
    print()

    # Read all rows
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Track changes
    total_chars = len(rows) - 1  # Exclude header
    chars_modified = 0
    pinyins_removed = {
        'has_numbers': 0,
        'has_special_marks': 0,
        'is_chinese_char': 0
    }

    # Process each row (skip header)
    for i in range(1, len(rows)):
        if len(rows[i]) < 4:
            continue

        char_id = rows[i][0]
        char = rows[i][1]
        pinyins_field = rows[i][3]

        # Split pinyins and check each one
        pinyins = pinyins_field.split('|')
        clean_pinyins = []
        row_modified = False

        for pinyin in pinyins:
            pinyin_clean = strip_frequency(pinyin).strip()
            is_corrupt, reason = is_corrupted_pinyin(pinyin_clean)

            if is_corrupt:
                # Skip this corrupted pinyin
                pinyins_removed[reason] += 1
                row_modified = True
                print(f"Removing from {char} (ID {char_id}): {repr(pinyin)} [{reason}]")
            else:
                # Keep valid pinyin
                clean_pinyins.append(pinyin)

        if row_modified:
            chars_modified += 1
            rows[i][3] = '|'.join(clean_pinyins)

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total characters:           {total_chars}")
    print(f"Characters modified:        {chars_modified}")
    print()
    print(f"Pinyins removed:")
    print(f"  With numbers:             {pinyins_removed['has_numbers']}")
    print(f"  With special marks:       {pinyins_removed['has_special_marks']}")
    print(f"  Chinese chars as pinyin:  {pinyins_removed['is_chinese_char']}")
    print(f"  Total removed:            {sum(pinyins_removed.values())}")
    print()

    # Confirm before writing
    response = input("Write cleaned data to CSV? (y/N): ")
    if response.lower() != 'y':
        print("Aborted. No changes made.")
        return

    # Write back to CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print()
    print(f"✓ Cleaned CSV written to: {csv_path}")

if __name__ == '__main__':
    main()
