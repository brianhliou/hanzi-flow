#!/usr/bin/env python3
"""
Step 2: Add pinyin readings to SOT character dataset (IDEMPOTENT)

Adds dual-format pinyin columns:
- pinyins_tone3: Canonical format with tone numbers (yi1|yi4)
- pinyins_display: Display format with tone marks (yī|yì)

Uses pypinyin for both formats. Allows NULL for rare characters.

This script is idempotent - it can be re-run to refresh pinyin data.
"""

import csv
from pathlib import Path

try:
    from pypinyin import pinyin, Style
except ImportError:
    print("ERROR: pypinyin library not installed")
    print("Install with: pip install pypinyin")
    exit(1)


def get_character_pinyins(char: str) -> tuple[str, str]:
    """
    Get all pinyin pronunciations for a character in both formats.

    Returns:
        (tone3_str, display_str) where:
        - tone3_str: "yi1|yi4" (canonical format with tone numbers)
        - display_str: "yī|yì" (display format with tone marks)
        Both empty strings if no pinyin found.
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

            return '|'.join(tone3_list), '|'.join(display_list)
    except Exception as e:
        print(f"⚠️  ERROR processing '{char}': {e}")

    return '', ''  # Return empty strings for NULL


def add_pinyins(csv_file='../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """
    Add or update dual-format pinyin columns in the SOT character CSV.
    IDEMPOTENT: Safe to re-run.
    """
    print("=" * 80)
    print("Step 2: Add pinyin readings (dual-format, idempotent)")
    print("=" * 80)

    csv_path = Path(csv_file)

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_file}")
        print("Run build_step1_extract_all_cjk.py first")
        exit(1)

    # Read existing CSV
    print(f"\nReading: {csv_file}")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows):,} characters")

    # Check if pinyin columns already exist
    has_tone3 = 'pinyins_tone3' in existing_fieldnames
    has_display = 'pinyins_display' in existing_fieldnames

    if has_tone3 and has_display:
        print("⚠️  Pinyin columns exist - will update values")
    elif has_tone3 or has_display:
        print("⚠️  WARNING: Only one pinyin column exists - will add missing column")
    else:
        print("✓ Adding new pinyin columns (tone3 + display)")

    # Process characters
    print("\nExtracting pinyins from pypinyin...")
    null_count = 0
    single_count = 0
    multi_count = 0
    max_pronunciations = 0
    updated_count = 0

    for i, row in enumerate(rows, 1):
        char = row['char']

        # Get both formats
        tone3_str, display_str = get_character_pinyins(char)

        # Track if we're updating
        if has_tone3 and row.get('pinyins_tone3') != tone3_str:
            updated_count += 1

        row['pinyins_tone3'] = tone3_str
        row['pinyins_display'] = display_str

        # Statistics
        if not tone3_str:
            null_count += 1
        else:
            num_pronunciations = len(tone3_str.split('|'))
            max_pronunciations = max(max_pronunciations, num_pronunciations)

            if num_pronunciations == 1:
                single_count += 1
            else:
                multi_count += 1

        if i % 10000 == 0:
            print(f"  Processed {i:,} / {len(rows):,} characters...")

    # Prepare fieldnames (add pinyin columns if not exists)
    if has_tone3 and has_display:
        fieldnames = existing_fieldnames
    else:
        # Insert both columns after codepoint
        fieldnames = list(existing_fieldnames)
        codepoint_idx = fieldnames.index('codepoint')

        # Remove if they exist in wrong position
        if 'pinyins_tone3' in fieldnames:
            fieldnames.remove('pinyins_tone3')
        if 'pinyins_display' in fieldnames:
            fieldnames.remove('pinyins_display')

        # Insert both after codepoint
        fieldnames.insert(codepoint_idx + 1, 'pinyins_tone3')
        fieldnames.insert(codepoint_idx + 2, 'pinyins_display')

    # Write back to same file
    print(f"\nWriting: {csv_file}")
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total characters:              {len(rows):,}")
    print(f"Characters with pinyin:        {len(rows) - null_count:,} ({(len(rows) - null_count)/len(rows)*100:.1f}%)")
    print(f"  - Single pronunciation:      {single_count:,}")
    print(f"  - Multiple pronunciations:   {multi_count:,}")
    print(f"Characters with NULL pinyin:   {null_count:,} ({null_count/len(rows)*100:.1f}%)")
    print(f"Max pronunciations:            {max_pronunciations}")

    if has_tone3:
        print(f"\nUpdated values:                {updated_count:,} characters")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    # Common characters
    print("\nCommon characters:")
    for row in rows[:10]:
        if row['pinyins_tone3']:
            print(f"  {row['char']} ({row['codepoint']})")
            print(f"    tone3:   {row['pinyins_tone3']}")
            print(f"    display: {row['pinyins_display']}")

    # Polyphonic characters
    print("\nPolyphonic characters (first 10):")
    example_count = 0
    for row in rows:
        if '|' in row.get('pinyins_tone3', ''):
            print(f"  {row['char']} ({row['codepoint']})")
            print(f"    tone3:   {row['pinyins_tone3']}")
            print(f"    display: {row['pinyins_display']}")
            example_count += 1
            if example_count >= 10:
                break

    # NULL pinyin characters
    if null_count > 0:
        print(f"\nCharacters with NULL pinyin (first 20):")
        null_chars = [(row['char'], row['codepoint']) for row in rows if not row.get('pinyins_tone3')]
        for char, codepoint in null_chars[:20]:
            print(f"  {char} ({codepoint})")

    print("\n" + "=" * 80)
    print("✓ Step 2 complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("  python3 build_step3_add_gloss.py        # Add English glosses")
    print("  python3 build_step4_add_script_type.py  # Add script type classification")


if __name__ == '__main__':
    add_pinyins()
