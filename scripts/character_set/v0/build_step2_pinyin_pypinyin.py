#!/usr/bin/env python3
"""
Step 2: Add pinyin columns using pypinyin (dual-format storage).

This replaces the old Unihan-based pinyin extraction. We now use pypinyin as the
single source of truth for pronunciations.

Output columns:
- pinyins_tone3: canonical format with tone numbers (yi1|yi4)
- pinyins_display: display format with tone marks (yī|yì)

Both formats are stored redundantly to avoid conversion logic throughout the codebase.
Frequencies will be added later in step6 (frequency enrichment).

Input: ../../data/build_artifacts/step1_base.csv
Output: ../../data/build_artifacts/step2_pinyin.csv
"""

import csv
from pathlib import Path

try:
    from pypinyin import pinyin, Style
except ImportError:
    print("ERROR: pypinyin library not installed")
    print("Install with: pip install pypinyin")
    exit(1)


def get_character_pinyins(char: str) -> tuple[list[str], list[str]]:
    """
    Get all pinyin pronunciations for a character in both formats.

    Returns:
        (tone3_list, display_list) where:
        - tone3_list: ['yi1', 'yi4'] (canonical format with tone numbers)
        - display_list: ['yī', 'yì'] (display format with tone marks)

    Both lists have the same length and order (guaranteed by pypinyin).
    """
    try:
        # Get both formats using heteronym=True for all pronunciations
        tone3_result = pinyin(char, style=Style.TONE3, heteronym=True)
        display_result = pinyin(char, style=Style.TONE, heteronym=True)

        if tone3_result and len(tone3_result) > 0:
            tone3_list = tone3_result[0]  # [['yi1', 'yi4']]
            display_list = display_result[0]  # [['yī', 'yì']]

            # Verify consistency (should always match)
            if len(tone3_list) != len(display_list):
                print(f"⚠️  WARNING: Format mismatch for '{char}': {tone3_list} vs {display_list}")

            return tone3_list, display_list
    except Exception as e:
        print(f"⚠️  ERROR processing '{char}': {e}")

    return [], []


def add_pinyin_to_csv(
    input_csv='../../data/character_set/step1_base.csv',
    output_csv='../../data/character_set/step2_pinyin.csv'
):
    """
    Add dual-format pinyin columns to the base CSV using pypinyin.
    """
    print("=" * 80)
    print("Step 2: Add pinyin using pypinyin (dual-format)")
    print("=" * 80)

    # Read input CSV
    print(f"\nReading: {input_csv}")
    input_path = Path(input_csv)

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows):,} characters")

    # Add pinyin columns
    print("\nExtracting pinyins from pypinyin...")
    missing_count = 0
    single_pinyin_count = 0
    multi_pinyin_count = 0
    max_pronunciations = 0
    pronunciation_distribution = {}

    for i, row in enumerate(rows, 1):
        char = row['char']

        # Get both formats
        tone3_list, display_list = get_character_pinyins(char)

        if tone3_list:
            # Store as pipe-separated
            row['pinyins_tone3'] = '|'.join(tone3_list)
            row['pinyins_display'] = '|'.join(display_list)

            num_pronunciations = len(tone3_list)

            # Track statistics
            pronunciation_distribution[num_pronunciations] = \
                pronunciation_distribution.get(num_pronunciations, 0) + 1

            if num_pronunciations > max_pronunciations:
                max_pronunciations = num_pronunciations

            if num_pronunciations == 1:
                single_pinyin_count += 1
            else:
                multi_pinyin_count += 1
        else:
            row['pinyins_tone3'] = ''
            row['pinyins_display'] = ''
            missing_count += 1

        if i % 5000 == 0:
            print(f"  Processed {i:,} / {len(rows):,} characters...")

    # Write output CSV
    print(f"\nWriting: {output_csv}")
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['id', 'char', 'codepoint', 'pinyins_tone3', 'pinyins_display']

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total characters:              {len(rows):,}")
    print(f"Characters with pinyin:        {len(rows) - missing_count:,} ({(len(rows) - missing_count)/len(rows)*100:.1f}%)")
    print(f"  - Single pronunciation:      {single_pinyin_count:,}")
    print(f"  - Multiple pronunciations:   {multi_pinyin_count:,}")
    print(f"Characters missing pinyin:     {missing_count:,} ({missing_count/len(rows)*100:.1f}%)")
    print(f"Max pronunciations:            {max_pronunciations}")

    print("\nPronunciation distribution:")
    for num in sorted(pronunciation_distribution.keys()):
        count = pronunciation_distribution[num]
        pct = count / len(rows) * 100
        print(f"  {num} pronunciation(s): {count:,} characters ({pct:.1f}%)")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    # Show polyphonic characters
    print("\nPolyphonic characters (first 10):")
    example_count = 0
    for row in rows:
        if '|' in row.get('pinyins_tone3', ''):
            print(f"  {row['char']}:")
            print(f"    tone3:   {row['pinyins_tone3']}")
            print(f"    display: {row['pinyins_display']}")
            example_count += 1
            if example_count >= 10:
                break

    # Show missing pinyin characters
    if missing_count > 0:
        print(f"\nCharacters missing pinyin (first 20):")
        missing_chars = [row['char'] for row in rows if not row.get('pinyins_tone3')]
        print(f"  {' '.join(missing_chars[:20])}")

    print("\n" + "=" * 80)
    print("✓ Step 2 complete!")
    print("=" * 80)
    print("\nNext step: build_step3_cedict.py")


if __name__ == '__main__':
    add_pinyin_to_csv()
