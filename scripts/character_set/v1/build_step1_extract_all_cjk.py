#!/usr/bin/env python3
"""
Step 1: Extract all CJK Unified Ideographs + Extensions A-J (~97k characters)

Creates initial SOT character dataset with:
- id: Sequential integer (1-97000+)
- char: The Chinese character
- codepoint: Unicode identifier (U+4E00 format)

This is the only non-idempotent step. It generates the complete character set.
All subsequent steps will modify this file in-place.
"""
import csv
from pathlib import Path


# Unicode block definitions from docs/CHARACTER_SET.md
# Listed in strict codepoint order (not alphabetical by extension)
# Excludes Extension J (proposed for Unicode 16, not yet official)
CJK_BLOCKS = [
    # Block name, start, end
    ("Extension A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("Extension B", 0x20000, 0x2A6DF),
    ("Extension C", 0x2A700, 0x2B73F),
    ("Extension D", 0x2B740, 0x2B81F),
    ("Extension E", 0x2B820, 0x2CEAF),
    ("Extension F", 0x2CEB0, 0x2EBEF),
    ("Extension I", 0x2EBF0, 0x2EE5F),
    ("Extension G", 0x30000, 0x3134F),
    ("Extension H", 0x31350, 0x323AF),
]


def extract_all_cjk(output_file='../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """
    Extract all CJK characters from Unicode blocks.
    Creates CSV with sequential IDs starting from 1.
    """
    records = []
    char_id = 1

    print("Extracting CJK characters from Unicode blocks...")
    print()

    for block_name, start, end in CJK_BLOCKS:
        block_records = []

        for code in range(start, end + 1):
            char = chr(code)
            codepoint = f"U+{code:04X}"

            block_records.append({
                'id': char_id,
                'char': char,
                'codepoint': codepoint
            })
            char_id += 1

        records.extend(block_records)

        count = len(block_records)
        print(f"✓ {block_name:30} {count:6,} chars  (U+{start:04X}-U+{end:04X})")

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'char', 'codepoint'])
        writer.writeheader()
        writer.writerows(records)

    print()
    print(f"✓ Created {output_file}")
    print(f"  Total characters: {len(records):,}")
    print(f"  First: {records[0]['char']} ({records[0]['codepoint']}) - Extension A")
    print(f"  Last:  {records[-1]['char']} ({records[-1]['codepoint']}) - Extension H")
    print()
    print("Next steps:")
    print("  python3 build_step2_add_pinyins.py      # Add pinyin readings")
    print("  python3 build_step3_add_gloss.py        # Add English glosses")
    print("  python3 build_step4_add_script_type.py  # Add script type classification")


if __name__ == '__main__':
    extract_all_cjk()
