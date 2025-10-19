#!/usr/bin/env python3
"""
Analyze sentence composition: pure Chinese vs mixed content.
"""
import csv
import re


def analyze_character_composition(sentence):
    """
    Categorize characters in a sentence.

    Returns:
        dict with counts of each character type
    """
    counts = {
        'chinese': 0,
        'ascii_letters': 0,
        'digits': 0,
        'punctuation': 0,
        'whitespace': 0,
        'other': 0
    }

    for char in sentence:
        if re.match(r'[\u4e00-\u9fff]', char):
            counts['chinese'] += 1
        elif re.match(r'[a-zA-Z]', char):
            counts['ascii_letters'] += 1
        elif re.match(r'[0-9]', char):
            counts['digits'] += 1
        elif re.match(r'[\s]', char):
            counts['whitespace'] += 1
        elif re.match(r'[.,!?;:()\[\]{}"\'\-—…、。，！？；：（）【】「」『』《》]', char):
            counts['punctuation'] += 1
        else:
            counts['other'] += 1

    return counts


def categorize_sentence(counts):
    """
    Categorize a sentence based on its character composition.

    Categories:
    - pure_chinese: Only Chinese + punctuation + whitespace
    - has_digits: Contains numbers
    - has_ascii: Contains ASCII letters (names, URLs, etc.)
    - has_other: Contains other unicode
    """
    has_chinese = counts['chinese'] > 0
    has_ascii = counts['ascii_letters'] > 0
    has_digits = counts['digits'] > 0
    has_other = counts['other'] > 0

    if not has_chinese:
        return 'no_chinese'

    if has_ascii:
        return 'has_ascii'
    elif has_digits:
        return 'has_digits'
    elif has_other:
        return 'has_other'
    else:
        return 'pure_chinese'


def analyze_sentences(input_file='../../data/sentences/cmn_sentences_classified.csv'):
    """
    Analyze all sentences and categorize them.
    """
    print(f"Analyzing sentences from {input_file}...\n")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    # Categorize all sentences
    categories = {
        'pure_chinese': [],
        'has_digits': [],
        'has_ascii': [],
        'has_other': [],
        'no_chinese': []
    }

    for row in sentences:
        sentence = row['sentence']
        counts = analyze_character_composition(sentence)
        category = categorize_sentence(counts)

        categories[category].append({
            'sentence': sentence,
            'script_type': row['script_type'],
            'counts': counts
        })

    total = len(sentences)

    # Print statistics
    print("="*60)
    print("SENTENCE COMPOSITION ANALYSIS")
    print("="*60)
    print(f"\nTotal sentences: {total:,}\n")

    print("Composition breakdown:")
    print(f"  Pure Chinese:        {len(categories['pure_chinese']):6,} ({len(categories['pure_chinese'])/total*100:5.1f}%)")
    print(f"  Has digits:          {len(categories['has_digits']):6,} ({len(categories['has_digits'])/total*100:5.1f}%)")
    print(f"  Has ASCII letters:   {len(categories['has_ascii']):6,} ({len(categories['has_ascii'])/total*100:5.1f}%)")
    print(f"  Has other unicode:   {len(categories['has_other']):6,} ({len(categories['has_other'])/total*100:5.1f}%)")
    print(f"  No Chinese:          {len(categories['no_chinese']):6,} ({len(categories['no_chinese'])/total*100:5.1f}%)")

    # Show examples of each category
    print("\n" + "="*60)
    print("EXAMPLES")
    print("="*60)

    print("\n1. Pure Chinese (first 5):")
    for item in categories['pure_chinese'][:5]:
        print(f"   {item['sentence']}")

    print("\n2. Has digits (first 5):")
    for item in categories['has_digits'][:5]:
        sentence = item['sentence']
        counts = item['counts']
        print(f"   {sentence}")
        print(f"      (Chinese: {counts['chinese']}, Digits: {counts['digits']})")

    print("\n3. Has ASCII letters (first 5):")
    for item in categories['has_ascii'][:5]:
        sentence = item['sentence']
        counts = item['counts']
        print(f"   {sentence}")
        print(f"      (Chinese: {counts['chinese']}, ASCII: {counts['ascii_letters']})")

    if categories['has_other']:
        print("\n4. Has other unicode (first 5):")
        for item in categories['has_other'][:5]:
            sentence = item['sentence']
            counts = item['counts']
            print(f"   {sentence}")
            print(f"      (Chinese: {counts['chinese']}, Other: {counts['other']})")

    print("\n" + "="*60)

    return categories


if __name__ == '__main__':
    categories = analyze_sentences()

    print("\n✓ Analysis complete!")
