#!/usr/bin/env python3
"""
Step 5: Add HSK level classification to character dataset
- Downloads HSK 3.0 character lists (levels 1-9) to data/sources/
- Assigns HSK levels to simplified characters
- Propagates HSK levels to traditional variants via our variant mappings
- Characters not in HSK 1-9: assigned null/empty hsk_level

Data Source: elkmovie/hsk30 (https://github.com/elkmovie/hsk30)
- More accurate than krmanik (fixes OCR errors: 入/人, 抛/拋)
- All 3,000 characters (300 per level 1-6, 1,200 for 7-9)
"""
import csv
import urllib.request
import os
import re
from collections import defaultdict


# HSK 3.0 data source (elkmovie/hsk30 repo - more accurate than krmanik)
HSK_CHARLIST_URL = "https://raw.githubusercontent.com/elkmovie/hsk30/main/charlist.txt"

# Where to save downloaded files
HSK_SOURCE_DIR = '../../data/sources/elkmovie_hsk30'


def download_hsk_files():
    """
    Download and parse HSK 3.0 charlist from elkmovie/hsk30 repo.
    Extracts individual level files for easier inspection.

    Returns:
        Dict mapping level -> local file path
    """
    # Create directory if it doesn't exist
    os.makedirs(HSK_SOURCE_DIR, exist_ok=True)

    print(f"Downloading HSK 3.0 character list from elkmovie/hsk30...")

    # Download the full charlist.txt
    charlist_path = os.path.join(HSK_SOURCE_DIR, 'charlist.txt')

    print(f"  Downloading {HSK_CHARLIST_URL}...")
    try:
        urllib.request.urlretrieve(HSK_CHARLIST_URL, charlist_path)
        print(f"  ✓ Saved to {charlist_path}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        raise

    # Parse the charlist and extract characters by level
    print(f"\n  Parsing charlist and extracting levels...")

    with open(charlist_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find section headers for each level
    level_start_lines = {}
    for i, line in enumerate(lines):
        if '一级汉字表' in line:
            level_start_lines[1] = i + 1
        elif '二级汉字表' in line:
            level_start_lines[2] = i + 1
        elif '三级汉字表' in line:
            level_start_lines[3] = i + 1
        elif '四级汉字表' in line:
            level_start_lines[4] = i + 1
        elif '五级汉字表' in line:
            level_start_lines[5] = i + 1
        elif '六级汉字表' in line:
            level_start_lines[6] = i + 1
        elif '七一九级汉字表' in line or '七至九级汉字表' in line:
            level_start_lines['7-9'] = i + 1

    # Extract characters for each level
    local_files = {}
    level_order = [1, 2, 3, 4, 5, 6, '7-9']

    for level in level_order:
        start = level_start_lines[level]
        expected_count = 1200 if level == '7-9' else 300

        chars = []
        for line_idx in range(start, len(lines)):
            line = lines[line_idx].strip()
            # Format: "123\t字"
            match = re.match(r'^\d+\t(.)', line)
            if match:
                char = match.group(1)
                chars.append(char)

            if len(chars) >= expected_count:
                break

        # Save to individual file
        level_file = os.path.join(HSK_SOURCE_DIR, f'HSK_{level}.txt')
        with open(level_file, 'w', encoding='utf-8') as f:
            for char in chars:
                f.write(f"{char}\n")

        print(f"    HSK {str(level):3s}: {len(chars):4d} characters → HSK_{level}.txt")
        local_files[level] = level_file

    print(f"\n✓ Downloaded and extracted {len(local_files)} HSK level files to {HSK_SOURCE_DIR}/")

    return local_files


def parse_hsk_files(local_files):
    """
    Parse HSK files into character -> level mapping.

    Args:
        local_files: Dict mapping level -> file path

    Returns:
        Dict mapping character -> hsk_level (string)
    """
    hsk_map = {}

    print("\nParsing HSK character files...")

    for level, filepath in sorted(local_files.items(), key=lambda x: (isinstance(x[0], str), x[0])):
        print(f"  Parsing HSK {level}...", end=" ")

        with open(filepath, 'r', encoding='utf-8') as f:
            chars = [line.strip() for line in f if line.strip()]

        for char in chars:
            if char in hsk_map:
                # Conflict: character appears in multiple levels
                # Keep the lower level (more basic)
                print(f"\n    WARNING: {char} appears in HSK {hsk_map[char]} and HSK {level}, keeping HSK {min(hsk_map[char], level)}")
                hsk_map[char] = min(hsk_map[char], level)
            else:
                hsk_map[char] = level

        print(f"✓ ({len(chars)} characters)")

    print(f"\n✓ Parsed {len(hsk_map)} unique HSK characters")

    # Show distribution
    level_counts = defaultdict(int)
    for level in hsk_map.values():
        level_counts[level] += 1

    print("\nHSK level distribution:")
    for level in sorted(level_counts.keys(), key=lambda x: (isinstance(x, str), x)):
        count = level_counts[level]
        print(f"  HSK {str(level):3s}: {count:4d} characters")

    return hsk_map


def build_variant_map(input_csv='../../data/character_set/step4_variants.csv'):
    """
    Build bidirectional variant mapping from our character dataset.

    Returns:
        Dict mapping character -> list of variant characters
    """
    variant_map = defaultdict(list)

    print(f"\nBuilding variant mappings from {input_csv}...")

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            char = row['char']
            variants_str = row.get('variants', '')

            if variants_str:
                variant_list = variants_str.split('|')

                # Forward mapping: char -> variants
                variant_map[char].extend(variant_list)

                # Reverse mapping: variant -> char
                for variant in variant_list:
                    if char not in variant_map[variant]:
                        variant_map[variant].append(char)

    print(f"✓ Built variant map for {len(variant_map)} characters")

    return variant_map


def add_hsk_levels(input_csv='../../data/character_set/step4_variants.csv',
                   output_csv='../../data/character_set/step5_hsk.csv'):
    """
    Add HSK level column to character dataset.
    """
    # Step 1: Download HSK character lists to data/sources/
    local_files = download_hsk_files()

    # Step 2: Parse HSK files
    hsk_map = parse_hsk_files(local_files)

    # Step 3: Build variant mappings from our dataset
    variant_map = build_variant_map(input_csv)

    # Step 4: Read input CSV
    print(f"\nReading {input_csv}...")
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"✓ Loaded {len(rows)} characters")

    # Step 5: Assign HSK levels
    print("\nAssigning HSK levels...")

    direct_assignments = 0
    variant_propagations = 0
    conflicts = []

    for row in rows:
        char = row['char']
        hsk_level = None

        # Check if character is directly in HSK list
        if char in hsk_map:
            hsk_level = hsk_map[char]
            direct_assignments += 1

        # Check if any variant is in HSK list
        elif char in variant_map:
            for variant in variant_map[char]:
                if variant in hsk_map:
                    variant_hsk = hsk_map[variant]

                    if hsk_level is None:
                        hsk_level = variant_hsk
                        variant_propagations += 1
                    elif hsk_level != variant_hsk:
                        # Multiple variants with different HSK levels
                        # Keep the minimum (most basic)
                        old_level = hsk_level
                        hsk_level = min(hsk_level, variant_hsk)
                        conflicts.append((char, old_level, variant_hsk, hsk_level))

        # Assign to row (convert to string, empty string if null, for CSV compatibility)
        # Note: hsk_level can be int (1-6) or string ("7-9")
        row['hsk_level'] = str(hsk_level) if hsk_level is not None else ''

    print(f"✓ Direct HSK assignments: {direct_assignments}")
    print(f"✓ Variant propagations: {variant_propagations}")
    print(f"✓ Characters without HSK level: {len(rows) - direct_assignments - variant_propagations}")

    if conflicts:
        print(f"\n⚠ Found {len(conflicts)} characters with conflicting variant HSK levels:")
        for char, old, new, final in conflicts[:10]:
            print(f"  {char}: HSK {old} vs HSK {new} → using HSK {final}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more")

    # Step 6: Write output CSV
    fieldnames = list(rows[0].keys())  # All existing columns + hsk_level

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Total characters: {len(rows)}")

    # Step 7: Generate statistics
    generate_statistics(rows)


def generate_statistics(rows):
    """
    Generate detailed HSK classification statistics.
    """
    print(f"\n{'='*60}")
    print("HSK CLASSIFICATION STATISTICS")
    print(f"{'='*60}\n")

    total = len(rows)

    # Count by HSK level
    level_counts = defaultdict(int)
    no_hsk_count = 0

    for row in rows:
        hsk_level = row['hsk_level']
        if hsk_level:
            # Keep as string (could be "1"-"6" or "7-9")
            level_counts[hsk_level] += 1
        else:
            no_hsk_count += 1

    print("Characters by HSK level:")
    # Sort with integers first, then strings
    sorted_levels = sorted(level_counts.keys(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
    for level in sorted_levels:
        count = level_counts[level]
        pct = count / total * 100
        print(f"  HSK {level:3s}: {count:5,} ({pct:5.2f}%)")

    print(f"  No HSK  : {no_hsk_count:5,} ({no_hsk_count/total*100:5.2f}%)")

    total_hsk = sum(level_counts.values())
    print(f"\nTotal HSK characters: {total_hsk:,} ({total_hsk/total*100:.1f}%)")
    print(f"Total non-HSK characters: {no_hsk_count:,} ({no_hsk_count/total*100:.1f}%)")

    # Show examples of each level
    print(f"\n{'='*60}")
    print("EXAMPLE CHARACTERS BY HSK LEVEL")
    print(f"{'='*60}")

    sorted_levels = sorted(level_counts.keys(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
    for level in sorted_levels:
        examples = [row['char'] for row in rows if row['hsk_level'] == level][:20]
        print(f"\nHSK {level} (first 20):")
        print(f"  {''.join(examples)}")

    print(f"\nNo HSK level (first 50):")
    no_hsk_examples = [row['char'] for row in rows if not row['hsk_level']][:50]
    print(f"  {''.join(no_hsk_examples)}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    add_hsk_levels()
    print("\n✓ HSK level classification complete!")
