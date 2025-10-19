#!/usr/bin/env python3
"""
Step 3: Add gloss_en and examples from CC-CEDICT
- gloss_en: Short English gloss for single-character entries
- examples: 2-3 common multi-character words containing this character
"""
import csv
import re
from collections import defaultdict


def parse_cedict(file_path='../../data/sources/cedict_ts.u8'):
    """
    Parse CC-CEDICT for glosses and example words.

    Returns:
        Dict mapping character -> {
            'gloss': 'person; people',
            'examples': ['人丁', '人世', '人中']
        }
    """
    char_data = defaultdict(lambda: {'gloss': '', 'examples': []})

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # CC-CEDICT format: traditional simplified [pinyin] /gloss1/gloss2/
            match = re.match(r'^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$', line)
            if not match:
                continue

            trad, simp, pinyin, glosses = match.groups()

            # Split glosses by /
            gloss_list = [g.strip() for g in glosses.split('/') if g.strip()]

            # For single characters, store gloss (first gloss only)
            if len(trad) == 1 and not char_data[trad]['gloss']:
                char_data[trad]['gloss'] = gloss_list[0] if gloss_list else ''

            if len(simp) == 1 and simp != trad and not char_data[simp]['gloss']:
                char_data[simp]['gloss'] = gloss_list[0] if gloss_list else ''

            # For multi-character words, add as examples
            # Collect examples for each character (limit to 3 per character)
            if len(trad) > 1:
                for char in trad:
                    if len(char_data[char]['examples']) < 3:
                        # Store the word if not already present
                        if trad not in char_data[char]['examples']:
                            char_data[char]['examples'].append(trad)

            if len(simp) > 1 and simp != trad:
                for char in simp:
                    if len(char_data[char]['examples']) < 3:
                        if simp not in char_data[char]['examples']:
                            char_data[char]['examples'].append(simp)

    return dict(char_data)


def add_cedict_to_csv(input_csv='../../data/build_artifacts/step2_pinyin.csv',
                      output_csv='../../data/build_artifacts/step3_cedict.csv'):
    """
    Add gloss_en and examples columns to the CSV.
    """
    print("Parsing CC-CEDICT...")
    cedict_data = parse_cedict()

    print(f"Loaded data for {len(cedict_data)} characters")

    # Read input CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Add CEDICT columns
    has_gloss = 0
    has_examples = 0
    missing_both = 0

    for row in rows:
        char = row['char']

        if char in cedict_data:
            data = cedict_data[char]
            row['gloss_en'] = data['gloss']
            row['examples'] = '|'.join(data['examples'])

            if data['gloss']:
                has_gloss += 1
            if data['examples']:
                has_examples += 1
        else:
            row['gloss_en'] = ''
            row['examples'] = ''
            missing_both += 1

    # Write output CSV
    fieldnames = ['id', 'char', 'codepoint', 'pinyins', 'gloss_en', 'examples']

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Total characters: {len(rows)}")
    print(f"  Characters with gloss: {has_gloss}")
    print(f"  Characters with examples: {has_examples}")
    print(f"  Missing both: {missing_both}")

    # Show some examples
    print("\nExample entries:")
    example_count = 0
    for row in rows[:1000]:
        if row.get('gloss_en') or row.get('examples'):
            gloss = row['gloss_en'][:50] if row['gloss_en'] else '(no gloss)'
            examples = row['examples'][:60] if row['examples'] else '(no examples)'
            print(f"  {row['char']} → {gloss}")
            print(f"       examples: {examples}")
            example_count += 1
            if example_count >= 5:
                break


def validate_cedict_csv(csv_file='../../data/build_artifacts/step3_cedict.csv'):
    """
    Validate and analyze the CEDICT-enriched CSV.
    """
    print(f"\n{'='*60}")
    print("VALIDATION REPORT")
    print(f"{'='*60}\n")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    # Statistics
    has_gloss = 0
    has_examples = 0
    has_both = 0
    has_neither = 0
    example_counts = defaultdict(int)

    for row in rows:
        gloss = row['gloss_en']
        examples = row['examples']

        if gloss:
            has_gloss += 1
        if examples:
            has_examples += 1
            num_examples = len(examples.split('|'))
            example_counts[num_examples] += 1

        if gloss and examples:
            has_both += 1
        elif not gloss and not examples:
            has_neither += 1

    print(f"Total characters: {total}")
    print(f"Characters with gloss: {has_gloss} ({has_gloss/total*100:.1f}%)")
    print(f"Characters with examples: {has_examples} ({has_examples/total*100:.1f}%)")
    print(f"Characters with both: {has_both} ({has_both/total*100:.1f}%)")
    print(f"Characters with neither: {has_neither} ({has_neither/total*100:.1f}%)")

    print(f"\nExample word distribution:")
    for num in sorted(example_counts.keys()):
        count = example_counts[num]
        print(f"  {num} example(s): {count} characters")

    # Show characters with neither
    if has_neither > 0:
        missing_chars = [row['char'] for row in rows if not row['gloss_en'] and not row['examples']]
        print(f"\nCharacters missing both gloss and examples (first 30):")
        print(f"  {' '.join(missing_chars[:30])}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    add_cedict_to_csv()
    validate_cedict_csv()
