#!/usr/bin/env python3
"""
Step 4: Add script type classification to SOT character dataset (IDEMPOTENT)

Adds 'script_type' column classifying characters as:
- simplified: Has traditional variant only (this is the simplified form)
- traditional: Has simplified variant only (this is the traditional form)
- neutral: Has no variants, OR has both variants (rare merger cases)

Note: Characters with both simplified and traditional variants (0.44% of dataset,
432 chars) are treated as neutral for simplicity. These represent edge cases in
the Unihan data where characters have complex variant relationships in both
directions (e.g., 万, 个, 乐). Since these don't fit cleanly into a single
script category, they're treated as neutral/shared.

Uses Unihan kSimplifiedVariant and kTraditionalVariant fields.

This script is idempotent - it can be re-run to refresh script type data.
"""

import csv
from pathlib import Path


def parse_unihan_variants(unihan_file='../../../data/sources/Unihan_Variants.txt'):
    """
    Parse Unihan_Variants.txt for kSimplifiedVariant and kTraditionalVariant.

    Returns:
        tuple: (simplified_variants, traditional_variants)
        - simplified_variants: {codepoint: variant_codepoint}
        - traditional_variants: {codepoint: variant_codepoint}
    """
    simplified_variants = {}
    traditional_variants = {}

    print(f"Parsing {unihan_file}...")

    with open(unihan_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue

            # Parse tab-separated format: U+XXXX\tkVariantType\tU+YYYY
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue

            codepoint = parts[0]
            variant_type = parts[1]
            variant_value = parts[2]

            if variant_type == 'kSimplifiedVariant':
                simplified_variants[codepoint] = variant_value
            elif variant_type == 'kTraditionalVariant':
                traditional_variants[codepoint] = variant_value

    print(f"  Found {len(simplified_variants):,} simplified variants")
    print(f"  Found {len(traditional_variants):,} traditional variants")

    return simplified_variants, traditional_variants


def classify_script_type(codepoint, simplified_variants, traditional_variants):
    """
    Classify a character's script type based on its variants.

    Logic:
    - Has simplified variant only → traditional (this char is traditional form)
    - Has traditional variant only → simplified (this char is simplified form)
    - Has both → neutral (rare merger case, treat as shared)
    - Has neither → neutral (shared between scripts)

    Returns:
        str: 'simplified', 'traditional', or 'neutral'
    """
    has_simplified = codepoint in simplified_variants
    has_traditional = codepoint in traditional_variants

    if has_simplified and has_traditional:
        # Rare case: character has both variants (merger)
        # Treat as neutral since it doesn't fit cleanly into one category
        return 'neutral'
    elif has_simplified:
        # This character has a simplified variant, so it's the traditional form
        return 'traditional'
    elif has_traditional:
        # This character has a traditional variant, so it's the simplified form
        return 'simplified'
    else:
        # No variants - neutral character used in both or neither script
        return 'neutral'


def add_script_types(csv_file='../../../data/character_set/v1/sot_characters_v1.0.csv'):
    """
    Add or update 'script_type' column in the SOT character CSV.
    IDEMPOTENT: Safe to re-run.
    """
    print("=" * 80)
    print("Step 4: Add script type classification (idempotent)")
    print("=" * 80)
    print()

    csv_path = Path(csv_file)

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_file}")
        print("Run build_step1_extract_all_cjk.py through build_step3_add_gloss.py first")
        exit(1)

    # Parse Unihan variants
    simplified_variants, traditional_variants = parse_unihan_variants()

    # Read existing CSV
    print(f"\nReading: {csv_file}")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows):,} characters")

    # Check if script_type column already exists
    has_script_type = 'script_type' in existing_fieldnames
    if has_script_type:
        print("⚠️  'script_type' column exists - will update values")
    else:
        print("✓ Adding new 'script_type' column")

    # Process characters
    print("\nClassifying script types...")
    simplified_count = 0
    traditional_count = 0
    neutral_count = 0
    updated_count = 0

    for i, row in enumerate(rows, 1):
        codepoint = row['codepoint']

        # Classify script type
        script_type = classify_script_type(codepoint, simplified_variants, traditional_variants)

        # Track if we're updating
        if has_script_type and row.get('script_type') != script_type:
            updated_count += 1

        row['script_type'] = script_type

        # Statistics
        if script_type == 'simplified':
            simplified_count += 1
        elif script_type == 'traditional':
            traditional_count += 1
        elif script_type == 'neutral':
            neutral_count += 1

        if i % 10000 == 0:
            print(f"  Processed {i:,} / {len(rows):,} characters...")

    # Prepare fieldnames (add script_type if not exists)
    if has_script_type:
        fieldnames = existing_fieldnames
    else:
        # Insert script_type before gloss_en
        fieldnames = list(existing_fieldnames)
        if 'gloss_en' in fieldnames:
            gloss_idx = fieldnames.index('gloss_en')
            fieldnames.insert(gloss_idx, 'script_type')
        else:
            # If gloss_en doesn't exist, add at end
            fieldnames.append('script_type')

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
    print(f"Simplified:                    {simplified_count:,} ({simplified_count/len(rows)*100:.1f}%)")
    print(f"Traditional:                   {traditional_count:,} ({traditional_count/len(rows)*100:.1f}%)")
    print(f"Neutral:                       {neutral_count:,} ({neutral_count/len(rows)*100:.1f}%)")

    if has_script_type:
        print(f"\nUpdated values:                {updated_count:,} characters")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    # Examples of each type
    for script_type in ['simplified', 'traditional', 'neutral']:
        examples = [row for row in rows if row.get('script_type') == script_type]
        if examples:
            print(f"\n{script_type.upper()} (first 10):")
            for row in examples[:10]:
                gloss = row.get('gloss_en', '')[:40] if row.get('gloss_en') else '(no gloss)'
                print(f"  {row['char']} ({row['codepoint']}): {gloss}")

    print("\n" + "=" * 80)
    print("✓ Step 4 complete!")
    print("=" * 80)
    print("\nAll pipeline steps complete!")
    print(f"Final dataset: {csv_file}")
    print("Columns: id, char, codepoint, pinyins_tone3, pinyins_display, script_type, gloss_en")


if __name__ == '__main__':
    add_script_types()
