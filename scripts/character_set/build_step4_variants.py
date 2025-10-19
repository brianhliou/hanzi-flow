#!/usr/bin/env python3
"""
Step 4: Add script_type and variants columns
- script_type: simplified, traditional, neutral, or ambiguous
- variants: pipe-separated list of variant characters (bidirectional)
"""
import csv
from collections import defaultdict


def parse_unihan_variants(file_path='../../data/sources/Unihan_Variants.txt'):
    """
    Parse Unihan_Variants.txt for simplified/traditional mappings.

    Returns:
        Dict mapping codepoint -> {
            'simplified': [codepoints],
            'traditional': [codepoints]
        }
    """
    variant_data = defaultdict(lambda: {'simplified': [], 'traditional': []})

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            codepoint, field, value = parts[0], parts[1], parts[2]

            if field == 'kSimplifiedVariant':
                # This char has simplified variant(s)
                simplified_codes = value.split()
                variant_data[codepoint]['simplified'].extend(simplified_codes)

            elif field == 'kTraditionalVariant':
                # This char has traditional variant(s)
                traditional_codes = value.split()
                variant_data[codepoint]['traditional'].extend(traditional_codes)

    return dict(variant_data)


def codepoint_to_char(codepoint):
    """Convert U+4E00 to character."""
    if codepoint.startswith('U+'):
        code = int(codepoint[2:], 16)
        return chr(code)
    return None


def char_to_codepoint(char):
    """Convert character to U+4E00 format."""
    return f"U+{ord(char):04X}"


def determine_script_type_and_variants(char, variant_data):
    """
    Determine script type and variant list for a character.

    Returns:
        (script_type, variant_chars)
        script_type: 'simplified', 'traditional', 'neutral', or 'ambiguous'
        variant_chars: list of variant characters
    """
    codepoint = char_to_codepoint(char)

    if codepoint not in variant_data:
        # No variant data - could be neutral or ambiguous
        return 'neutral', []

    data = variant_data[codepoint]

    # Check if character has self-references (exists in both systems)
    has_simplified_self = codepoint in data['simplified']
    has_traditional_self = codepoint in data['traditional']

    # Collect variant characters (excluding self-references for the variants list)
    simplified_chars = []
    traditional_chars = []

    if data['simplified']:
        for code in data['simplified']:
            # Skip self-references for variants list
            if code == codepoint:
                continue
            variant_char = codepoint_to_char(code)
            if variant_char:
                simplified_chars.append(variant_char)

    if data['traditional']:
        for code in data['traditional']:
            # Skip self-references for variants list
            if code == codepoint:
                continue
            variant_char = codepoint_to_char(code)
            if variant_char:
                traditional_chars.append(variant_char)

    # Determine script type (COUNT self-references here!)
    # IMPORTANT: Unihan semantics are:
    #   kSimplifiedVariant means: "this char HAS a simplified variant" → this char IS traditional
    #   kTraditionalVariant means: "this char HAS a traditional variant" → this char IS simplified
    has_simplified_form = has_simplified_self or bool(simplified_chars)
    has_traditional_form = has_traditional_self or bool(traditional_chars)

    # Combine all variants (excluding self)
    variant_chars = simplified_chars + traditional_chars

    # Classification logic (INVERTED from what you might expect!)
    if has_simplified_form and has_traditional_form:
        # Exists in both systems → neutral
        script_type = 'neutral'
    elif has_simplified_form and not has_traditional_form:
        # Has simplified variant(s) → this IS the traditional form
        script_type = 'traditional'
    elif has_traditional_form and not has_simplified_form:
        # Has traditional variant(s) → this IS the simplified form
        script_type = 'simplified'
    else:
        # No variant data at all
        script_type = 'neutral'

    return script_type, variant_chars


def add_variants_to_csv(input_csv='../../data/build_artifacts/step3_cedict.csv',
                        output_csv='../../data/build_artifacts/step4_variants.csv'):
    """
    Add script_type and variants columns to the CSV.
    """
    print("Parsing Unihan variants...")
    variant_data = parse_unihan_variants()

    print(f"Loaded variant data for {len(variant_data)} characters")

    # Read input CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Add variant columns
    type_counts = defaultdict(int)
    has_variants_count = 0
    max_variants = 0

    for row in rows:
        char = row['char']

        script_type, variant_chars = determine_script_type_and_variants(char, variant_data)

        row['script_type'] = script_type
        row['variants'] = '|'.join(variant_chars)

        type_counts[script_type] += 1
        if variant_chars:
            has_variants_count += 1
            if len(variant_chars) > max_variants:
                max_variants = len(variant_chars)

    # Write output CSV
    fieldnames = ['id', 'char', 'codepoint', 'pinyins', 'script_type',
                  'variants', 'gloss_en', 'examples']

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Total characters: {len(rows)}")
    print(f"\nScript type distribution:")
    for stype in ['simplified', 'traditional', 'neutral', 'ambiguous']:
        count = type_counts[stype]
        print(f"  {stype}: {count} ({count/len(rows)*100:.1f}%)")

    print(f"\nVariant statistics:")
    print(f"  Characters with variants: {has_variants_count}")
    print(f"  Max variants for one character: {max_variants}")

    # Show some examples
    print("\nExample simplified characters:")
    for row in rows:
        if row['script_type'] == 'simplified' and row['variants']:
            print(f"  {row['char']} → {row['variants']}")
            if rows.index(row) >= 4:
                break

    print("\nExample traditional characters:")
    count = 0
    for row in rows:
        if row['script_type'] == 'traditional' and row['variants']:
            print(f"  {row['char']} → {row['variants']}")
            count += 1
            if count >= 5:
                break


def validate_variants_csv(csv_file='../../data/build_artifacts/step4_variants.csv'):
    """
    Validate and analyze the variants CSV.
    """
    print(f"\n{'='*60}")
    print("VALIDATION REPORT")
    print(f"{'='*60}\n")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    # Statistics
    type_counts = defaultdict(int)
    variant_counts = defaultdict(int)

    for row in rows:
        script_type = row['script_type']
        variants = row['variants']

        type_counts[script_type] += 1

        if variants:
            num_variants = len(variants.split('|'))
            variant_counts[num_variants] += 1

    print(f"Total characters: {total}")
    print(f"\nScript type breakdown:")
    for stype in ['simplified', 'traditional', 'neutral', 'ambiguous']:
        count = type_counts[stype]
        pct = count/total*100
        print(f"  {stype:12s}: {count:5d} ({pct:5.1f}%)")

    print(f"\nVariant count distribution:")
    for num in sorted(variant_counts.keys()):
        count = variant_counts[num]
        print(f"  {num} variant(s): {count} characters")

    # Check bidirectional consistency
    print(f"\nBidirectional consistency check:")
    char_map = {row['char']: row for row in rows}
    inconsistent = []

    for row in rows:
        char = row['char']
        variants = row['variants'].split('|') if row['variants'] else []

        for variant in variants:
            if variant in char_map:
                # Check if the variant links back to us
                variant_row = char_map[variant]
                back_variants = variant_row['variants'].split('|') if variant_row['variants'] else []
                if char not in back_variants:
                    inconsistent.append((char, variant))

    if inconsistent:
        print(f"  Found {len(inconsistent)} inconsistent bidirectional links")
        print(f"  Examples (first 5):")
        for char, variant in inconsistent[:5]:
            print(f"    {char} → {variant}, but {variant} doesn't link back")
    else:
        print(f"  ✓ All bidirectional links are consistent!")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    add_variants_to_csv()
    validate_variants_csv()
