#!/usr/bin/env python3
"""
Add pinyin to sentences using jieba + pypinyin.
Uses context-aware word segmentation to disambiguate polyphonic characters.
"""
import csv
import jieba
from pypinyin import pinyin, Style


def add_pinyin_to_sentence(sentence):
    """
    Convert a Chinese sentence to pinyin with tone numbers.

    Uses jieba for word segmentation, then pypinyin for conversion.
    Returns space-separated pinyin.

    Args:
        sentence: Chinese text string

    Returns:
        Pinyin string with tone numbers (e.g., "wo3 ai4 ni3")
    """
    # Step 1: Segment with jieba
    words = jieba.lcut(sentence)

    # Step 2: Convert each word to pinyin
    pinyin_results = []
    for word in words:
        # Get pinyin for this word (context helps disambiguation)
        word_pinyin = pinyin(word, style=Style.TONE3, heteronym=False)
        # Flatten the result (pypinyin returns list of lists)
        word_pinyin_flat = [p[0] for p in word_pinyin]
        pinyin_results.extend(word_pinyin_flat)

    # Join with spaces
    return ' '.join(pinyin_results)


def process_sentences(input_file='../../data/sentences/cmn_sentences_classified.csv',
                     output_file='../../data/sentences/cmn_sentences_with_pinyin.csv'):
    """
    Add pinyin to all sentences.
    """
    print("Loading sentences...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    print(f"Processing {len(sentences):,} sentences...")

    # Add pinyin to each sentence
    for i, row in enumerate(sentences, 1):
        sentence = row['sentence']

        # Generate pinyin
        sentence_pinyin = add_pinyin_to_sentence(sentence)
        row['pinyin'] = sentence_pinyin

        if i % 10000 == 0:
            print(f"  Processed {i:,} sentences...")

    # Write output
    fieldnames = ['sentence', 'script_type', 'pinyin']

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentences)

    print(f"\n✓ Created {output_file}")
    print(f"  Total sentences: {len(sentences):,}")

    # Show some examples
    print("\nExample sentences with pinyin:")
    for i, row in enumerate(sentences[:10], 1):
        print(f"\n{i}. {row['sentence']}")
        print(f"   Pinyin: {row['pinyin']}")
        print(f"   Type: {row['script_type']}")


def test_conversion():
    """
    Test the conversion on some example sentences.
    """
    print("Testing pinyin conversion...")
    print("="*60)

    test_cases = [
        "我爱你",
        "银行在哪里？",
        "他在银行工作。",
        "这个行李太重了。",
        "我们试试看！",
        "你好吗？",
    ]

    for sentence in test_cases:
        pinyin_result = add_pinyin_to_sentence(sentence)
        print(f"\n{sentence}")
        print(f"→ {pinyin_result}")

    print("\n" + "="*60)


if __name__ == '__main__':
    # First, run a quick test
    test_conversion()

    # Then process all sentences
    print("\n")
    process_sentences()

    print("\n✓ Pinyin conversion complete!")
