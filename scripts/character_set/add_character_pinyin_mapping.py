#!/usr/bin/env python3
"""
Create character-to-pinyin mappings for sentences.
Uses jieba + pypinyin for context-aware conversion.

Output format: char:pinyin pairs separated by |
Example: 我:wo3|爱:ai4|你:ni3

Non-Chinese handling:
- Multi-char tokens (English words, numbers): kept as single token with empty pinyin
- Whitespace: skipped entirely
- Punctuation: kept as single char with empty pinyin (consistent with other non-Chinese)
"""
import csv
import re
import jieba
from pypinyin import pinyin, Style


def is_chinese_char(char):
    """Check if character is a Chinese character."""
    return bool(re.match(r'[\u4e00-\u9fff]', char))


def create_char_pinyin_mapping(sentence):
    """
    Create character-to-pinyin mapping for a sentence.

    For Chinese characters: use pypinyin with context
    For multi-char non-Chinese tokens (words, numbers): keep as single token with empty pinyin
    For punctuation: keep as single char with empty pinyin
    For whitespace: skip entirely

    Returns:
        List of (char, pinyin) tuples
    """
    # Step 1: Segment with jieba for context
    words = jieba.lcut(sentence)

    # Step 2: Process each word
    char_pinyin_pairs = []

    for word in words:
        # Skip whitespace tokens entirely
        if word.strip() == '':
            continue

        # Check if this is a multi-character non-Chinese token
        # (English words, numbers like "123", etc.)
        has_chinese = any(is_chinese_char(c) for c in word)
        is_multi_char_non_chinese = len(word) > 1 and not has_chinese

        if is_multi_char_non_chinese:
            # Keep the entire token as one unit with empty pinyin
            char_pinyin_pairs.append((word, ''))
        else:
            # Process character by character
            word_pinyin = pinyin(word, style=Style.TONE3, heteronym=False)

            for i, char in enumerate(word):
                # Skip whitespace characters
                if char.strip() == '':
                    continue

                # Check if this is a Chinese character
                if is_chinese_char(char):
                    # Use pypinyin result for Chinese characters
                    if i < len(word_pinyin):
                        py = word_pinyin[i][0]
                        char_pinyin_pairs.append((char, py))
                    else:
                        # Shouldn't happen, but handle gracefully
                        char_pinyin_pairs.append((char, ''))
                else:
                    # Non-Chinese single char (punctuation, single digit, etc.)
                    # Map to empty string for consistency
                    char_pinyin_pairs.append((char, ''))

    return char_pinyin_pairs


def format_char_pinyin_pairs(pairs):
    """
    Format pairs as pipe-separated string: char:pinyin|char:pinyin
    """
    return '|'.join([f"{char}:{py}" for char, py in pairs])


def process_sentences(input_file='../../data/sentences/cmn_sentences_classified.csv',
                     output_file='../../data/sentences/cmn_sentences_with_char_pinyin.csv'):
    """
    Add character-to-pinyin mappings to all sentences.
    """
    print("Loading sentences...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    print(f"Processing {len(sentences):,} sentences...\n")

    # Add character-pinyin mapping to each sentence
    for i, row in enumerate(sentences, 1):
        sentence = row['sentence']

        # Generate character-to-pinyin pairs
        pairs = create_char_pinyin_mapping(sentence)
        row['char_pinyin_pairs'] = format_char_pinyin_pairs(pairs)

        if i % 10000 == 0:
            print(f"  Processed {i:,} sentences...")

    # Write output
    fieldnames = ['sentence', 'script_type', 'char_pinyin_pairs']

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentences)

    print(f"\n✓ Created {output_file}")
    print(f"  Total sentences: {len(sentences):,}")

    # Show some examples
    print("\nExample sentences with character-pinyin mapping:")
    print("="*60)
    for i, row in enumerate(sentences[:10], 1):
        print(f"\n{i}. {row['sentence']}")
        print(f"   Type: {row['script_type']}")
        print(f"   Mapping: {row['char_pinyin_pairs'][:100]}{'...' if len(row['char_pinyin_pairs']) > 100 else ''}")

    # Validation
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)

    # Count sentences by composition
    pure_chinese_count = 0
    has_non_chinese_count = 0

    for row in sentences:
        pairs_str = row['char_pinyin_pairs']
        pairs = [p.split(':')[0] for p in pairs_str.split('|')]

        # Check if any pair is a multi-char token (non-Chinese)
        has_multi_char_token = any(len(p) > 1 for p in pairs)

        if has_multi_char_token:
            has_non_chinese_count += 1
        else:
            pure_chinese_count += 1

    print(f"\nComposition breakdown:")
    print(f"  Pure Chinese (chars only): {pure_chinese_count:,} ({pure_chinese_count/len(sentences)*100:.1f}%)")
    print(f"  Has non-Chinese tokens:    {has_non_chinese_count:,} ({has_non_chinese_count/len(sentences)*100:.1f}%)")

    print(f"\n✓ All {len(sentences):,} sentences processed successfully!")
    print("  Multi-char tokens (English words, numbers) kept as single units.")
    print("  Whitespace characters removed.")


def test_conversion():
    """
    Test the conversion on example sentences.
    """
    print("Testing character-pinyin mapping...")
    print("="*60)

    test_cases = [
        "我爱你",
        "我叫Jack。",
        "今天是6月18号。",
        "银行在哪里？",
        "Image Viewer是一款软件。",
    ]

    for sentence in test_cases:
        pairs = create_char_pinyin_mapping(sentence)
        formatted = format_char_pinyin_pairs(pairs)
        print(f"\n{sentence}")
        print(f"→ {formatted}")

    print("\n" + "="*60)


if __name__ == '__main__':
    # First, run a quick test
    test_conversion()

    # Then process all sentences
    print("\n")
    process_sentences()

    print("\n✓ Character-pinyin mapping complete!")
