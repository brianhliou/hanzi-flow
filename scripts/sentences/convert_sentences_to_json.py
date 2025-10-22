#!/usr/bin/env python3
"""
Convert sentence CSV to JSON format for the web app.
Includes English translations and corpus metadata.
Applies content filters to remove unwanted sentences.
"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# =============================================================================
# SENTENCE FILTERS
# =============================================================================
# Patterns to filter out sentences (case-insensitive regex)
# Add new patterns here to filter additional content
FILTER_PATTERNS = [
    r'Tatoeba',           # Remove sentences mentioning Tatoeba website
    r'鸡巴',              # Vulgar slang (male genitalia)
    r'婊子',              # Bitch
    r'屄',                # Vulgar (female genitalia)
    r'肏',                # Fuck
    # r'offensive_word',  # Future: Add profanity filters here
]

# Maximum sentence length (in characters)
MAX_SENTENCE_LENGTH = 50


def should_filter_sentence(sentence, english_translation):
    """
    Check if a sentence should be filtered out based on FILTER_PATTERNS and length.

    Args:
        sentence: Chinese sentence text
        english_translation: English translation text

    Returns:
        (should_filter: bool, reason: str) - True if sentence should be removed
    """
    # Check length first (faster)
    if len(sentence) > MAX_SENTENCE_LENGTH:
        return True, f"too long ({len(sentence)} chars > {MAX_SENTENCE_LENGTH})"

    combined_text = f"{sentence} {english_translation}"

    for pattern in FILTER_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            return True, f"matches pattern: {pattern}"

    return False, ""


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


def calculate_unique_chars(converted_sentences):
    """
    Calculate unique Chinese characters from converted sentences.

    Args:
        converted_sentences: List of sentence objects with 'chars' field

    Returns:
        Number of unique Chinese characters (those with pinyin)
    """
    unique_chars = set()

    for sentence in converted_sentences:
        for char_obj in sentence['chars']:
            # Only count Chinese characters (those with pinyin)
            if char_obj['pinyin']:
                unique_chars.add(char_obj['char'])

    return len(unique_chars)


def convert_to_json(input_file='../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk_UPDATED.csv',
                   output_file='../../app/public/data/sentences/sentences_with_translation.json',
                   limit=None):
    """
    Convert CSV to JSON format for the web app with metadata wrapper.
    Includes HSK level classification for sentences.

    Args:
        input_file: Input CSV path (with HSK levels)
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
    filter_stats = defaultdict(int)  # Track why sentences were filtered

    for row in sentences:
        # Check content filters first
        should_filter, filter_reason = should_filter_sentence(
            row['sentence'],
            row['english_translation']
        )
        if should_filter:
            filter_stats[filter_reason] += 1
            continue

        pairs = parse_char_pinyin_pairs(row['char_pinyin_pairs'])

        # Skip sentences with no Chinese characters at all
        has_chinese = any(p['pinyin'] for p in pairs)
        if not has_chinese:
            filter_stats['no Chinese characters'] += 1
            continue

        sentence_obj = {
            'id': int(row['id']),  # Preserve original CSV ID
            'sentence': row['sentence'],
            'english_translation': row['english_translation'],
            'script_type': row['script_type'],
            'chars': pairs
        }

        # Add HSK level if present (empty string means unclassified)
        hsk_level = row.get('sentence_hsk_level', '').strip()
        if hsk_level:
            sentence_obj['hskLevel'] = hsk_level

        converted.append(sentence_obj)

        # Apply limit
        if limit and len(converted) >= limit:
            break

    print(f"\nConverted {len(converted):,} sentences")

    # Show filtering stats
    if filter_stats:
        total_filtered = sum(filter_stats.values())
        print(f"\nFiltered out {total_filtered:,} sentences:")
        for reason, count in sorted(filter_stats.items(), key=lambda x: -x[1]):
            print(f"  - {count:,} sentences: {reason}")

    # Calculate unique characters
    print("Calculating unique characters in corpus...")
    unique_char_count = calculate_unique_chars(converted)
    print(f"Found {unique_char_count:,} unique Chinese characters")

    # Create metadata wrapper
    output_data = {
        'metadata': {
            'totalSentences': len(converted),
            'totalCharsInCorpus': unique_char_count,
            'generatedAt': datetime.now().isoformat(),
            'version': '2.0'  # Updated version with HSK levels
        },
        'sentences': converted
    }

    # Write JSON with custom formatting:
    # - Metadata block: prettified
    # - Sentences: one per line (compact)
    print(f"\nWriting JSON to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('{\n')

        # Write metadata block (pretty)
        f.write('  "metadata": ')
        f.write(json.dumps(output_data['metadata'], ensure_ascii=False, indent=4).replace('\n', '\n  '))
        f.write(',\n')

        # Write sentences array header
        f.write('  "sentences": [\n')

        # Write each sentence on one line
        for i, sentence in enumerate(converted):
            f.write('    ')
            f.write(json.dumps(sentence, ensure_ascii=False, separators=(',', ': ')))
            if i < len(converted) - 1:
                f.write(',\n')
            else:
                f.write('\n')

        # Close sentences array and root object
        f.write('  ]\n')
        f.write('}\n')

    print(f"\n✓ Created {output_file}")

    # Show file size
    import os
    file_size = os.path.getsize(output_file)
    print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    # Show metadata
    print("\nMetadata:")
    print(f"  Total sentences: {output_data['metadata']['totalSentences']:,}")
    print(f"  Unique characters: {output_data['metadata']['totalCharsInCorpus']:,}")
    print(f"  Generated at: {output_data['metadata']['generatedAt']}")
    print(f"  Version: {output_data['metadata']['version']}")

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
