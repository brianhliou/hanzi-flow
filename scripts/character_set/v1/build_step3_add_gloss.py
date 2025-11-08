#!/usr/bin/env python3
"""
Step 3: Add English glosses to SOT character dataset (IDEMPOTENT)

Adds 'gloss_en' column with English definitions from Unihan kDefinition.
Allows NULL for rare characters without definitions.

This script is idempotent - it can be re-run to refresh gloss data.
"""

import csv
from pathlib import Path


def parse_unihan_definitions(unihan_file='../../../data/sources/Unihan_Readings.txt'):
    """
    Parse Unihan_Readings.txt for kDefinition entries.

    Returns:
        dict: {codepoint: definition} e.g., {"U+4E00": "one"}
    """
    definitions = {}

    print(f"Parsing {unihan_file}...")

    with open(unihan_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue

            # Parse tab-separated format: U+XXXX\tkDefinition\tdefinition text
            parts = line.strip().split('\t')
            if len(parts) >= 3 and parts[1] == 'kDefinition':
                codepoint = parts[0]
                definition = parts[2]
                definitions[codepoint] = definition

    print(f"  Found {len(definitions):,} definitions")
    return definitions


def add_glosses(csv_file='../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """
    Add or update 'gloss_en' column in the SOT character CSV.
    IDEMPOTENT: Safe to re-run.
    """
    print("=" * 80)
    print("Step 3: Add English glosses (idempotent)")
    print("=" * 80)
    print()

    csv_path = Path(csv_file)

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_file}")
        print("Run build_step1_extract_all_cjk.py and build_step2_add_pinyins.py first")
        exit(1)

    # Parse Unihan definitions
    definitions = parse_unihan_definitions()

    # Read existing CSV
    print(f"\nReading: {csv_file}")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows):,} characters")

    # Check if gloss_en column already exists
    has_gloss = 'gloss_en' in existing_fieldnames
    if has_gloss:
        print("⚠️  'gloss_en' column exists - will update values")
    else:
        print("✓ Adding new 'gloss_en' column")

    # Process characters
    print("\nAdding English glosses from Unihan kDefinition...")
    null_count = 0
    found_count = 0
    updated_count = 0

    for i, row in enumerate(rows, 1):
        codepoint = row['codepoint']

        # Get definition from Unihan
        gloss = definitions.get(codepoint, '')

        # Track if we're updating
        if has_gloss and row.get('gloss_en') != gloss:
            updated_count += 1

        row['gloss_en'] = gloss

        # Statistics
        if gloss:
            found_count += 1
        else:
            null_count += 1

        if i % 10000 == 0:
            print(f"  Processed {i:,} / {len(rows):,} characters...")

    # Prepare fieldnames (add gloss_en if not exists)
    if has_gloss:
        fieldnames = existing_fieldnames
    else:
        # Add gloss_en at the end
        fieldnames = list(existing_fieldnames) + ['gloss_en']

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
    print(f"Characters with gloss:         {found_count:,} ({found_count/len(rows)*100:.1f}%)")
    print(f"Characters with NULL gloss:    {null_count:,} ({null_count/len(rows)*100:.1f}%)")

    if has_gloss:
        print(f"\nUpdated values:                {updated_count:,} characters")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    # Common characters with glosses
    print("\nCharacters with glosses (first 20):")
    example_count = 0
    for row in rows:
        if row.get('gloss_en'):
            print(f"  {row['char']} ({row['codepoint']}): {row['gloss_en'][:60]}{'...' if len(row['gloss_en']) > 60 else ''}")
            example_count += 1
            if example_count >= 20:
                break

    # NULL gloss characters
    if null_count > 0:
        print(f"\nCharacters with NULL gloss (first 20):")
        null_chars = [(row['char'], row['codepoint']) for row in rows if not row.get('gloss_en')]
        for char, codepoint in null_chars[:20]:
            print(f"  {char} ({codepoint})")

    print("\n" + "=" * 80)
    print("✓ Step 3 complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("  python3 build_step4_add_script_type.py  # Add script type classification")


if __name__ == '__main__':
    add_glosses()
