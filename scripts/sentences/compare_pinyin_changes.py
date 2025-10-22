#!/usr/bin/env python3
"""
Compare original sentence pinyin vs OpenAI-improved pinyin.

Generates a report showing what changed, statistics, and examples.

Input:
    - ../../app/public/data/sentences/sentences_with_translation.json (original)
    - ../../data/sentences/sentences_pinyin_openai.json (OpenAI output)

Output:
    - ../../data/sentences/pinyin_comparison_report.json (diff report)

Usage:
    python3 compare_pinyin_changes.py
"""

import json
import re
from collections import defaultdict

# File paths
ORIGINAL_FILE = '../../app/public/data/sentences/sentences_with_translation.json'
OPENAI_FILE = '../../data/sentences/sentences_pinyin_openai.json'
REPORT_FILE = '../../data/sentences/pinyin_comparison_report.json'


def normalize_tone_marks_to_numbers(pinyin: str) -> str:
    """
    Convert tone marks to tone numbers.

    Examples:
        nǐ → ni3
        hǎo → hao3
        ma → ma (no tone)
    """
    # Tone mark mappings
    tone_map = {
        # First tone (ā)
        'ā': ('a', '1'), 'ē': ('e', '1'), 'ī': ('i', '1'), 'ō': ('o', '1'), 'ū': ('u', '1'), 'ǖ': ('v', '1'),
        # Second tone (á)
        'á': ('a', '2'), 'é': ('e', '2'), 'í': ('i', '2'), 'ó': ('o', '2'), 'ú': ('u', '2'), 'ǘ': ('v', '2'),
        # Third tone (ǎ)
        'ǎ': ('a', '3'), 'ě': ('e', '3'), 'ǐ': ('i', '3'), 'ǒ': ('o', '3'), 'ǔ': ('u', '3'), 'ǚ': ('v', '3'),
        # Fourth tone (à)
        'à': ('a', '4'), 'è': ('e', '4'), 'ì': ('i', '4'), 'ò': ('o', '4'), 'ù': ('u', '4'), 'ǜ': ('v', '4'),
        # Neutral ü
        'ü': ('v', ''),
    }

    result = []
    tone_number = ''

    for char in pinyin.lower():
        if char in tone_map:
            base, tone = tone_map[char]
            result.append(base)
            if tone:
                tone_number = tone
        else:
            result.append(char)

    return ''.join(result) + tone_number


def normalize_pinyin(pinyin: str) -> str:
    """
    Normalize pinyin for comparison.

    - Converts tone marks to numbers
    - Removes tone numbers for base comparison
    - Handles null/empty
    """
    if not pinyin:
        return ''

    # Convert tone marks to numbers
    with_numbers = normalize_tone_marks_to_numbers(pinyin)

    # Remove tone numbers for base comparison
    base = re.sub(r'[1-4]', '', with_numbers)

    return base.lower().strip()


def parse_openai_pinyin(pinyin_text: str, sentence: str) -> list:
    """
    Parse OpenAI's space-separated pinyin into list of tokens.

    Handles:
    - Punctuation attached to syllables (wù, → wù and ,)
    - Quoted words ("duì" → ", duì, ")

    Returns: List of pinyin tokens (including numbers, punctuation, English)
    """
    if not pinyin_text:
        return []

    # Split by spaces
    raw_tokens = pinyin_text.split()

    # Post-process to split attached punctuation and quotes
    tokens = []
    for token in raw_tokens:
        if not token:  # Skip empty tokens
            continue

        # Strip and split quotes/punctuation from both ends
        cleaned = token
        prefix_punct = []
        suffix_punct = []

        # Strip leading punctuation/quotes
        while cleaned and cleaned[0] in '，。！？；：、…·,.!?;:\'"()[]{}""''、':
            prefix_punct.append(cleaned[0])
            cleaned = cleaned[1:]

        # Strip trailing punctuation/quotes
        while cleaned and cleaned[-1] in '，。！？；：、…·,.!?;:\'"()[]{}""''、':
            suffix_punct.insert(0, cleaned[-1])
            cleaned = cleaned[:-1]

        # Add tokens in order
        tokens.extend(prefix_punct)
        if cleaned:
            tokens.append(cleaned)
        tokens.extend(suffix_punct)

    return tokens


def extract_chinese_pinyins(chars: list) -> list:
    """
    Extract only Chinese character pinyins from chars array.

    Returns: List of (char, pinyin_with_tone_number) tuples
    """
    result = []
    for c in chars:
        # Skip non-Chinese (pinyin is null or empty)
        if c.get('pinyin') in [None, '', 'null']:
            continue

        char = c['char']
        pinyin = c['pinyin']

        # Skip if not actually Chinese character
        if not (0x4E00 <= ord(char) <= 0x9FFF):
            continue

        result.append((char, pinyin))

    return result


def is_chinese_char(char: str) -> bool:
    """Check if character is Chinese (CJK Unified Ideographs)."""
    if not char or len(char) != 1:
        return False
    return 0x4E00 <= ord(char) <= 0x9FFF


def extract_chinese_only(chars: list) -> list:
    """
    Extract only Chinese characters with their pinyins.

    Returns: [(char, pinyin), ...]
    """
    result = []
    for c in chars:
        char = c['char']
        pinyin = c.get('pinyin')

        # Only include actual Chinese characters with pinyin
        if is_chinese_char(char) and pinyin not in [None, '', 'null']:
            result.append((char, pinyin))

    return result


def has_tone_marks(text: str) -> bool:
    """Check if text contains pinyin tone marks."""
    tone_chars = 'āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü'
    return any(c in tone_chars for c in text)


def is_likely_english_name(token: str) -> bool:
    """
    Check if token is likely an English name or word.

    Rules:
    - All ASCII letters
    - Length > 3 OR starts with uppercase
    """
    if not all(ord(c) < 128 for c in token):
        return False

    # Long ASCII words are likely English
    if len(token) > 3:
        return True

    # Capitalized words are likely names (Tom, Jim, Ann)
    if token and token[0].isupper():
        return True

    return False


def extract_chinese_pinyin_only(pinyin_text: str) -> list:
    """
    Extract only Chinese character pinyins from OpenAI output.

    Filters out: numbers, punctuation, English words/names.

    Returns: [pinyin, pinyin, ...]
    """
    tokens = parse_openai_pinyin(pinyin_text, '')

    chinese_pinyins = []
    for token in tokens:
        # Skip empty
        if not token:
            continue

        # Skip numbers
        if token.isdigit():
            continue

        # Skip punctuation
        if token in '，。！？；：、…·,.!?;:\'"()[]{}""''、':
            continue

        # If it has tone marks, it's definitely Chinese pinyin
        if has_tone_marks(token):
            chinese_pinyins.append(token)
            continue

        # Filter out English names/words
        if is_likely_english_name(token):
            continue

        # Otherwise assume it's Chinese pinyin (including neutral tone like 'de', 'me')
        chinese_pinyins.append(token)

    return chinese_pinyins


def compare_sentence(original_chars: list, openai_chars: list) -> dict:
    """
    Compare original vs OpenAI pinyin for a single sentence.

    Strategy: Compare chars arrays directly, only for Chinese characters.

    Returns: {
        'total_chars': int,
        'changed': int,
        'unchanged': int,
        'changes': [{'char': str, 'before': str, 'after': str}, ...]
    }
    """
    changes = []
    unchanged_count = 0
    total_chinese_chars = 0

    # Compare character by character
    for orig_c, openai_c in zip(original_chars, openai_chars):
        char = orig_c['char']
        orig_pinyin = orig_c.get('pinyin')
        openai_pinyin = openai_c.get('pinyin')

        # Skip non-Chinese characters (pinyin is None)
        if orig_pinyin in [None, '', 'null']:
            continue

        # Skip if not actually Chinese character
        if not is_chinese_char(char):
            continue

        total_chinese_chars += 1

        # Convert OpenAI tone marks to tone numbers for comparison
        if openai_pinyin:
            openai_pinyin_normalized = normalize_tone_marks_to_numbers(openai_pinyin)
        else:
            openai_pinyin_normalized = ''

        # Normalize for comparison (remove tones)
        original_base = normalize_pinyin(orig_pinyin)
        openai_base = normalize_pinyin(openai_pinyin_normalized)

        if original_base != openai_base:
            changes.append({
                'char': char,
                'before': orig_pinyin,
                'after': openai_pinyin_normalized
            })
        else:
            unchanged_count += 1

    return {
        'total_chars': total_chinese_chars,
        'changed': len(changes),
        'unchanged': unchanged_count,
        'changes': changes
    }


def main():
    print("=" * 70)
    print("Pinyin Comparison: Original vs OpenAI")
    print("=" * 70)

    # Load original data
    print(f"\nReading original: {ORIGINAL_FILE}")
    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    # Load OpenAI data
    print(f"Reading OpenAI output: {OPENAI_FILE}")
    with open(OPENAI_FILE, 'r', encoding='utf-8') as f:
        openai_data = json.load(f)

    # Create lookup: sentence_id -> openai sentence
    openai_lookup = {s['id']: s for s in openai_data['sentences']}

    print(f"\nOriginal sentences: {len(original_data['sentences']):,}")
    print(f"OpenAI sentences: {len(openai_data['sentences']):,}")

    # Compare each sentence
    print("\nComparing sentences...")

    report = {
        'metadata': {
            'original_total': len(original_data['sentences']),
            'openai_total': len(openai_data['sentences']),
            'compared': 0,
            'total_chars': 0,
            'total_changed': 0,
            'total_unchanged': 0
        },
        'changes_by_char': defaultdict(lambda: {'count': 0, 'examples': []}),
        'sentence_changes': []
    }

    for original_sentence in original_data['sentences']:
        sid = original_sentence['id']

        # Skip if not in OpenAI output
        if sid not in openai_lookup:
            continue

        openai_sentence = openai_lookup[sid]

        # Compare chars arrays directly
        comparison = compare_sentence(
            original_sentence['chars'],
            openai_sentence['chars']
        )

        # Update metadata
        report['metadata']['compared'] += 1
        report['metadata']['total_chars'] += comparison['total_chars']
        report['metadata']['total_changed'] += comparison['changed']
        report['metadata']['total_unchanged'] += comparison['unchanged']

        # Track changes by character
        for change in comparison['changes']:
            char = change['char']
            report['changes_by_char'][char]['count'] += 1

            # Save up to 5 examples per character
            if len(report['changes_by_char'][char]['examples']) < 5:
                report['changes_by_char'][char]['examples'].append({
                    'sentence_id': sid,
                    'sentence': original_sentence['sentence'],
                    'before': change['before'],
                    'after': change['after']
                })

        # Save sentence-level changes (only if there were changes)
        if comparison['changed'] > 0:
            report['sentence_changes'].append({
                'id': sid,
                'sentence': original_sentence['sentence'],
                'total_chars': comparison['total_chars'],
                'changed': comparison['changed'],
                'changes': comparison['changes']
            })

    # Convert defaultdict to regular dict for JSON serialization
    report['changes_by_char'] = dict(report['changes_by_char'])

    # Sort changes by frequency
    sorted_chars = sorted(
        report['changes_by_char'].items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    report['top_changed_chars'] = [
        {'char': char, 'count': data['count'], 'examples': data['examples']}
        for char, data in sorted_chars[:20]
    ]

    # Write report
    print(f"\nWriting report: {REPORT_FILE}")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Sentences compared:     {report['metadata']['compared']:,}")
    print(f"Total characters:       {report['metadata']['total_chars']:,}")
    print(f"Changed:                {report['metadata']['total_changed']:,} ({report['metadata']['total_changed']/report['metadata']['total_chars']*100:.1f}%)")
    print(f"Unchanged:              {report['metadata']['total_unchanged']:,} ({report['metadata']['total_unchanged']/report['metadata']['total_chars']*100:.1f}%)")
    print(f"Sentences with changes: {len(report['sentence_changes']):,}")

    # Top changed characters
    print("\n" + "=" * 70)
    print("TOP 10 MOST CHANGED CHARACTERS")
    print("=" * 70)
    for item in report['top_changed_chars'][:10]:
        print(f"\n{item['char']}: {item['count']:,} changes")
        for ex in item['examples'][:2]:
            print(f"  {ex['sentence']}")
            print(f"    {ex['before']} → {ex['after']}")

    print("\n" + "=" * 70)
    print(f"✓ Report saved: {REPORT_FILE}")
    print("=" * 70)


if __name__ == '__main__':
    main()
