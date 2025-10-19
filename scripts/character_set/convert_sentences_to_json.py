#!/usr/bin/env python3
"""
Convert sentence CSV to JSON format for the web app.
Filters to pure Chinese sentences only for MVP.
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


def is_pure_chinese_sentence(pairs):
    """
    Check if sentence contains only Chinese characters (and punctuation).
    Returns True if no multi-char tokens (English words, numbers).
    """
    for pair in pairs:
        # Multi-char tokens indicate non-Chinese content
        if len(pair['char']) > 1:
            return False
    return True


def convert_to_json(input_file='../../data/sentences/cmn_sentences_with_char_pinyin.csv',
                   output_file='../../app/public/data/sentences.json',
                   limit=100,
                   pure_chinese_only=True):
    """
    Convert CSV to JSON format for the web app.

    Args:
        input_file: Input CSV path
        output_file: Output JSON path
        limit: Max number of sentences (None for all)
        pure_chinese_only: If True, only include pure Chinese sentences
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

        # Filter if needed
        if pure_chinese_only and not is_pure_chinese_sentence(pairs):
            filtered_count += 1
            continue

        # Include ALL characters (Chinese, alphanumeric, punctuation)
        # Keep non-Chinese chars for proper sentence rendering
        all_chars = pairs

        # Skip sentences with no Chinese characters
        has_chinese = any(p['pinyin'] for p in pairs)
        if not has_chinese:
            filtered_count += 1
            continue

        converted.append({
            'id': len(converted) + 1,
            'sentence': row['sentence'],
            'script_type': row['script_type'],
            'chars': all_chars
        })

        # Apply limit
        if limit and len(converted) >= limit:
            break

    print(f"\nConverted {len(converted):,} sentences")
    if filtered_count > 0:
        print(f"Filtered out {filtered_count:,} sentences (non-Chinese content)")

    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Created {output_file}")

    # Show examples
    print("\nExample sentences:")
    for item in converted[:5]:
        print(f"\n{item['id']}. {item['sentence']} ({item['script_type']})")
        chars_preview = ' '.join([f"{c['char']}:{c['pinyin']}" for c in item['chars'][:5]])
        if len(item['chars']) > 5:
            chars_preview += '...'
        print(f"   {chars_preview}")


if __name__ == '__main__':
    convert_to_json(
        limit=100,  # Start with 100 sentences for MVP
        pure_chinese_only=False  # TEMP: Include mixed content for testing
    )

    print("\n✓ Conversion complete!")
