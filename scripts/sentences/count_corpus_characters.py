#!/usr/bin/env python3
"""
Count unique characters in the sentence corpus and analyze HSK distribution.
"""

import csv
from pathlib import Path

def main():
    # Load all characters that appear in sentences
    sentence_chars = set()
    csv_path = Path('../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv')

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char_pinyin = row.get('char_pinyin_pairs', '')
            pairs = char_pinyin.split('|')
            for pair in pairs:
                if ':' in pair:
                    char = pair.split(':', 1)[0]
                    if char.strip():
                        sentence_chars.add(char)

    print(f'Total unique characters in sentence corpus: {len(sentence_chars)}')
    print()

    # Now check how many have HSK levels
    char_csv = Path('../../app/public/data/character_set/chinese_characters.csv')
    hsk_chars = set()
    beyond_hsk_chars = set()

    with open(char_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            hsk_level = row.get('hsk_level', '').strip()

            # Only count characters that appear in our sentences
            if char in sentence_chars:
                if hsk_level and hsk_level != 'beyond-hsk':
                    hsk_chars.add(char)
                elif hsk_level == 'beyond-hsk':
                    beyond_hsk_chars.add(char)

    print(f'Characters with HSK 1-9 levels (in corpus): {len(hsk_chars)}')
    print(f'Characters with beyond-hsk (in corpus): {len(beyond_hsk_chars)}')
    print(f'Total HSK + beyond-hsk: {len(hsk_chars) + len(beyond_hsk_chars)}')
    print(f'Characters in corpus without any HSK classification: {len(sentence_chars) - len(hsk_chars) - len(beyond_hsk_chars)}')

if __name__ == '__main__':
    main()
