#!/usr/bin/env python3
"""
Step 2: Add pinyin columns to the base CSV
- pinyins: pipe-separated list of pinyin readings with optional frequency

Data sources (in priority order):
1. kHanyuPinlu - has pinyin with frequency counts
2. kHanyuPinyin - has multiple readings
3. kMandarin - single/primary reading
"""
import csv
import re
from collections import defaultdict


def parse_unihan_readings(file_path='../../data/sources/Unihan_Readings.txt'):
    """
    Parse Unihan_Readings.txt for pinyin data.

    Returns:
        Dict mapping codepoint -> {
            'pinyins': ['lè', 'yuè'],
            'freqs': [283, 54]
        }
    """
    readings = {}

    # First pass: collect all reading fields for each codepoint
    temp_data = defaultdict(dict)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            codepoint, field, value = parts[0], parts[1], parts[2]

            if field in ['kMandarin', 'kHanyuPinyin', 'kHanyuPinlu']:
                temp_data[codepoint][field] = value

    # Second pass: extract pinyins and frequencies
    for codepoint, fields in temp_data.items():
        pinyins = []
        freqs = []

        # Priority 1: kHanyuPinlu (has frequency data)
        if 'kHanyuPinlu' in fields:
            # Format: "lè(283) yuè(54)" or "yī(32747)"
            pinlu_value = fields['kHanyuPinlu']
            # Match pattern: pinyin(frequency)
            matches = re.findall(r'(\w+)\((\d+)\)', pinlu_value)
            if matches:
                pinyins = [match[0] for match in matches]
                freqs = [int(match[1]) for match in matches]

        # Priority 2: kHanyuPinyin (multiple readings, no frequency)
        elif 'kHanyuPinyin' in fields:
            # Format: "10263.070:dān,qiú" (has location prefix)
            hanyu_value = fields['kHanyuPinyin']
            # Extract part after colon
            if ':' in hanyu_value:
                pinyin_part = hanyu_value.split(':')[1]
                pinyins = pinyin_part.split(',')

        # Priority 3: kMandarin (single reading)
        elif 'kMandarin' in fields:
            # Format: "lè" or "lè yuè" (space-separated if multiple)
            mandarin_value = fields['kMandarin']
            pinyins = mandarin_value.split()

        if pinyins:
            readings[codepoint] = {
                'pinyins': pinyins,
                'freqs': freqs if freqs else []
            }

    return readings


def add_pinyin_to_csv(input_csv='../../data/build_artifacts/step1_base.csv',
                      output_csv='../../data/build_artifacts/step2_pinyin.csv'):
    """
    Add pinyin column to the base CSV.
    Format: lè(283)|yuè(54) or just lè if no frequency data
    """
    print("Parsing Unihan readings...")
    readings = parse_unihan_readings()

    print(f"Loaded readings for {len(readings)} characters")

    # Read input CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Add pinyin column
    missing_count = 0
    multi_pinyin_count = 0
    has_freq_count = 0

    for row in rows:
        codepoint = row['codepoint']

        if codepoint in readings:
            data = readings[codepoint]
            pinyins = data['pinyins']
            freqs = data['freqs']

            # Build combined format: pinyin(freq)|pinyin(freq)
            pinyin_parts = []
            for i, pinyin in enumerate(pinyins):
                if freqs and i < len(freqs):
                    pinyin_parts.append(f"{pinyin}({freqs[i]})")
                else:
                    pinyin_parts.append(pinyin)

            row['pinyins'] = '|'.join(pinyin_parts)

            if len(pinyins) > 1:
                multi_pinyin_count += 1
            if freqs:
                has_freq_count += 1
        else:
            row['pinyins'] = ''
            missing_count += 1

    # Write output CSV
    fieldnames = ['id', 'char', 'codepoint', 'pinyins']

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Total characters: {len(rows)}")
    print(f"  Characters with pinyin: {len(rows) - missing_count}")
    print(f"  Characters with multiple pinyins: {multi_pinyin_count}")
    print(f"  Characters with frequency data: {has_freq_count}")
    print(f"  Missing pinyin: {missing_count}")

    # Show some examples
    print("\nExample entries:")
    example_count = 0
    for row in rows[:500]:  # Check first 500
        if row.get('pinyins'):
            print(f"  {row['char']} → {row['pinyins']}")
            example_count += 1
            if example_count >= 10:  # Show 10 examples
                break


def validate_pinyin_csv(csv_file='../../data/build_artifacts/step2_pinyin.csv'):
    """
    Validate and analyze the pinyin CSV.
    """
    print(f"\n{'='*60}")
    print("VALIDATION REPORT")
    print(f"{'='*60}\n")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    # Statistics
    missing_pinyin = []
    has_pinyin = []
    single_pinyin = []
    multi_pinyin = []
    has_freq = []
    no_freq = []
    max_pronunciations = 0
    pinyin_distribution = {}

    for row in rows:
        char = row['char']
        pinyins = row['pinyins']

        if not pinyins:
            missing_pinyin.append(char)
        else:
            has_pinyin.append(char)

            # Split by pipe to count pronunciations
            pinyin_list = pinyins.split('|')
            num_pronunciations = len(pinyin_list)

            # Track distribution
            pinyin_distribution[num_pronunciations] = pinyin_distribution.get(num_pronunciations, 0) + 1

            if num_pronunciations > max_pronunciations:
                max_pronunciations = num_pronunciations

            if num_pronunciations == 1:
                single_pinyin.append((char, pinyins))
            else:
                multi_pinyin.append((char, pinyins))

            # Check if has frequency data
            if '(' in pinyins:
                has_freq.append((char, pinyins))
            else:
                no_freq.append((char, pinyins))

    # Print summary
    print(f"Total characters: {total}")
    print(f"Characters with pinyin: {len(has_pinyin)} ({len(has_pinyin)/total*100:.1f}%)")
    print(f"Characters missing pinyin: {len(missing_pinyin)} ({len(missing_pinyin)/total*100:.1f}%)")

    print(f"\nPinyin pronunciation counts:")
    print(f"  Single pronunciation: {len(single_pinyin)} ({len(single_pinyin)/total*100:.1f}%)")
    print(f"  Multiple pronunciations: {len(multi_pinyin)} ({len(multi_pinyin)/total*100:.1f}%)")
    print(f"  Max pronunciations for one character: {max_pronunciations}")

    print(f"\nPronunciation distribution:")
    for num in sorted(pinyin_distribution.keys()):
        count = pinyin_distribution[num]
        print(f"  {num} pronunciation(s): {count} characters")

    print(f"\nFrequency data:")
    print(f"  With frequency data: {len(has_freq)} ({len(has_freq)/total*100:.1f}%)")
    print(f"  Without frequency data: {len(no_freq)} ({len(no_freq)/total*100:.1f}%)")

    # Show examples
    if multi_pinyin:
        print(f"\nExample polyphonic characters (first 10):")
        for char, pinyins in multi_pinyin[:10]:
            print(f"  {char} → {pinyins}")

    if missing_pinyin:
        print(f"\nExample characters missing pinyin (first 20):")
        print(f"  {' '.join(missing_pinyin[:20])}")

    if no_freq:
        print(f"\nExample characters without frequency data (first 10):")
        for char, pinyins in no_freq[:10]:
            print(f"  {char} → {pinyins}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    add_pinyin_to_csv()
    validate_pinyin_csv()
