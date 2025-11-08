#!/usr/bin/env python3
"""
Step 1: Build base CSV with id, char, codepoint
CJK Unified Ideographs: U+4E00 to U+9FFF (20,992 characters)
"""
import csv


def build_base_csv(output_file='../../data/build_artifacts/step1_base.csv'):
    """
    Create CSV with integer id, character, and codepoint.
    """
    records = []

    # CJK Unified Ideographs range
    for code in range(0x4E00, 0x9FFF + 1):
        char = chr(code)
        codepoint = f"U+{code:04X}"

        # Sequential integer ID starting from 1
        char_id = code - 0x4E00 + 1

        records.append({
            'id': char_id,
            'char': char,
            'codepoint': codepoint
        })

    # Write to CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'char', 'codepoint'])
        writer.writeheader()
        writer.writerows(records)

    print(f"✓ Created {output_file}")
    print(f"  Total characters: {len(records)}")
    print(f"  Range: U+4E00 to U+9FFF")
    print(f"  First char: {records[0]['char']} ({records[0]['codepoint']})")
    print(f"  Last char: {records[-1]['char']} ({records[-1]['codepoint']})")


if __name__ == '__main__':
    build_base_csv()
