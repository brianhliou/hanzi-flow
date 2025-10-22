#!/usr/bin/env python3
"""
Count beyond-HSK characters by script type.
"""

import csv
from pathlib import Path

def main():
    # Load the non-HSK characters from our analysis
    non_hsk_chars = set()
    non_hsk_csv = Path('../../data/sentences/non_hsk_characters.csv')

    with open(non_hsk_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            non_hsk_chars.add(row['character'])

    print(f'Total beyond-HSK characters in corpus: {len(non_hsk_chars)}')
    print()

    # Now check their script types in chinese_characters.csv
    char_csv = Path('../../app/public/data/character_set/chinese_characters.csv')

    script_counts = {
        'simplified': 0,
        'traditional': 0,
        'neutral': 0,
        'not_found': 0
    }

    simplified_or_neutral = []

    with open(char_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            if char in non_hsk_chars:
                script_type = row.get('script_type', '').strip()

                if script_type == 'simplified':
                    script_counts['simplified'] += 1
                    simplified_or_neutral.append(char)
                elif script_type == 'traditional':
                    script_counts['traditional'] += 1
                elif script_type == 'neutral':
                    script_counts['neutral'] += 1
                    simplified_or_neutral.append(char)
                else:
                    script_counts['not_found'] += 1

    print('Beyond-HSK characters by script type:')
    print(f'  Simplified:  {script_counts["simplified"]}')
    print(f'  Traditional: {script_counts["traditional"]}')
    print(f'  Neutral:     {script_counts["neutral"]}')
    print(f'  Not found:   {script_counts["not_found"]}')
    print()
    print(f'Simplified + Neutral: {len(simplified_or_neutral)}')
    print()

    # Show some examples
    print('First 20 examples (Simplified + Neutral):')
    for char in simplified_or_neutral[:20]:
        print(f'  {char}')

if __name__ == '__main__':
    main()
