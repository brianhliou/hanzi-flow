#!/usr/bin/env python3
"""
Convert sentence CSV to JSON format for the web app.
Includes English translations.
"""
import csv
import json


def parse_char_pinyin_pairs(pairs_str):
    """
    Parse pipe-separated char:pinyin pairs into structured format.

    Returns:
        List of {char, pinyin} objects
    """
    if not pairs_str:
        return []

    pairs = []
    for pair in pairs_str.split('|'):
        if ':' in pair:
            char, pinyin = pair.split(':', 1)

            pairs.append({
                'char': char,
                'pinyin': pinyin if pinyin else None
            })

    return pairs


def convert_to_json(input_file='../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_TEST.csv',
                   output_file='../../app/public/data/sentences/sentences_with_translation.json',
                   limit=None):
    """
    Convert CSV to JSON format for the web app.

    Args:
        input_file: Input CSV path
        output_file: Output JSON path
        limit: Max number of sentences (None for all)
    """
    print(f"Reading sentences from {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    print(f"Loaded {len(sentences):,} sentences")

    # Convert to structured format
    converted = []
    filtered_count = 0

    for row in sentences:
        pairs = parse_char_pinyin_pairs(row['char_pinyin_pairs'])

        # Skip sentences with no Chinese characters at all
        has_chinese = any(p['pinyin'] for p in pairs)
        if not has_chinese:
            filtered_count += 1
            continue

        converted.append({
            'id': int(row['id']),  # Preserve original CSV ID
            'sentence': row['sentence'],
            'english_translation': row['english_translation'],  # NEW
            'script_type': row['script_type'],
            'chars': pairs
        })

        # Apply limit
        if limit and len(converted) >= limit:
            break

    print(f"\nConverted {len(converted):,} sentences")
    if filtered_count > 0:
        print(f"Filtered out {filtered_count:,} sentences (no Chinese characters)")

    # Write JSON (minified - no indentation)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False)

    print(f"\n✓ Created {output_file}")

    # Show file size
    import os
    file_size = os.path.getsize(output_file)
    print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    # Show examples
    print("\nExample sentences:")
    for item in converted[:5]:
        print(f"\n{item['id']}. {item['sentence']} ({item['script_type']})")
        print(f"   EN: {item['english_translation']}")
        chars_preview = ' '.join([f"{c['char']}:{c['pinyin']}" for c in item['chars'][:5]])
        if len(item['chars']) > 5:
            chars_preview += '...'
        print(f"   Chars: {chars_preview}")


if __name__ == '__main__':
    convert_to_json(
        limit=None  # Process all sentences
    )

    print("\n✓ Conversion complete!")
