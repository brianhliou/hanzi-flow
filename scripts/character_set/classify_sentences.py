#!/usr/bin/env python3
"""
Classify Tatoeba sentences as simplified, traditional, neutral, or ambiguous
based on the script_type of their constituent characters.
"""
import csv
import re
from collections import Counter, defaultdict


def load_character_classifications(csv_file='../../data/chinese_characters.csv'):
    """
    Load character -> script_type mapping from the dataset.

    Returns:
        Dict mapping character -> script_type (simplified/traditional/neutral/ambiguous)
    """
    char_script_map = {}

    print(f"Loading character classifications from {csv_file}...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            script_type = row['script_type']
            char_script_map[char] = script_type

    print(f"✓ Loaded {len(char_script_map):,} character classifications")

    return char_script_map


def extract_chinese_characters(text):
    """
    Extract only Chinese characters from text.
    """
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return chinese_chars


def classify_sentence(sentence, char_script_map):
    """
    Classify a sentence based on its character composition.

    Logic:
    - All neutral → neutral
    - All neutral or simplified (with at least one simplified) → simplified
    - All neutral or traditional (with at least one traditional) → traditional
    - Mix of simplified and traditional → ambiguous
    - Contains ambiguous characters → ambiguous
    - No characters or only unknown characters → unknown

    Returns:
        (script_type, char_types_found, total_chars)
    """
    chars = extract_chinese_characters(sentence)

    if not chars:
        return 'unknown', {}, 0

    # Count occurrences of each script type
    type_counts = Counter()

    for char in chars:
        script_type = char_script_map.get(char, 'unknown')
        type_counts[script_type] += 1

    total_chars = len(chars)

    # Classification logic
    has_simplified = type_counts['simplified'] > 0
    has_traditional = type_counts['traditional'] > 0
    has_ambiguous = type_counts['ambiguous'] > 0
    has_neutral = type_counts['neutral'] > 0
    has_unknown = type_counts['unknown'] > 0

    # If any character is ambiguous, sentence is ambiguous
    if has_ambiguous:
        return 'ambiguous', dict(type_counts), total_chars

    # If mix of simplified and traditional, sentence is ambiguous
    if has_simplified and has_traditional:
        return 'ambiguous', dict(type_counts), total_chars

    # Only neutral characters
    if has_neutral and not has_simplified and not has_traditional:
        return 'neutral', dict(type_counts), total_chars

    # Neutral + simplified (at least one simplified)
    if has_simplified and not has_traditional:
        return 'simplified', dict(type_counts), total_chars

    # Neutral + traditional (at least one traditional)
    if has_traditional and not has_simplified:
        return 'traditional', dict(type_counts), total_chars

    # Only unknown characters
    if has_unknown and not has_neutral and not has_simplified and not has_traditional:
        return 'unknown', dict(type_counts), total_chars

    # Shouldn't reach here, but default to unknown
    return 'unknown', dict(type_counts), total_chars


def classify_tatoeba_sentences(char_script_map,
                               input_file='../../data/sentences/cmn_sentences.tsv',
                               output_file='../../data/sentences/cmn_sentences_classified.csv'):
    """
    Parse Tatoeba sentences and classify each one.
    """
    print(f"\nClassifying sentences from {input_file}...")

    classified_sentences = []
    classification_counts = Counter()
    total_sentences = 0

    # Track character type distributions
    char_type_distributions = defaultdict(lambda: Counter())

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue

            sentence = parts[2]

            # Classify the sentence
            script_type, char_types, total_chars = classify_sentence(sentence, char_script_map)

            classified_sentences.append({
                'sentence': sentence,
                'script_type': script_type
            })

            classification_counts[script_type] += 1

            # Track character type distribution for this classification
            for ctype, count in char_types.items():
                char_type_distributions[script_type][ctype] += count

            total_sentences += 1

            if total_sentences % 10000 == 0:
                print(f"  Classified {total_sentences:,} sentences...")

    # Write output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sentence', 'script_type'])
        writer.writeheader()
        writer.writerows(classified_sentences)

    print(f"\n✓ Created {output_file}")
    print(f"  Total sentences classified: {total_sentences:,}")

    return classified_sentences, classification_counts, char_type_distributions


def generate_statistics(classified_sentences, classification_counts, char_type_distributions):
    """
    Generate detailed classification statistics.
    """
    print(f"\n{'='*60}")
    print("SENTENCE CLASSIFICATION STATISTICS")
    print(f"{'='*60}\n")

    total = sum(classification_counts.values())

    print(f"Total sentences: {total:,}\n")

    print("Classification breakdown:")
    for script_type in ['simplified', 'traditional', 'neutral', 'ambiguous', 'unknown']:
        count = classification_counts[script_type]
        pct = count / total * 100 if total > 0 else 0
        print(f"  {script_type:12s}: {count:6,} ({pct:5.1f}%)")

    print("\nCharacter type distribution within each sentence classification:")
    for sentence_type in ['simplified', 'traditional', 'neutral', 'ambiguous']:
        if sentence_type in char_type_distributions:
            print(f"\n  {sentence_type.upper()} sentences contain:")
            char_counts = char_type_distributions[sentence_type]
            total_chars = sum(char_counts.values())
            for char_type in ['simplified', 'traditional', 'neutral', 'ambiguous', 'unknown']:
                count = char_counts.get(char_type, 0)
                pct = count / total_chars * 100 if total_chars > 0 else 0
                print(f"    {char_type:12s} chars: {count:8,} ({pct:5.1f}%)")

    # Show examples
    print("\n" + "="*60)
    print("EXAMPLE SENTENCES")
    print("="*60)

    for script_type in ['simplified', 'traditional', 'neutral', 'ambiguous']:
        examples = [s for s in classified_sentences if s['script_type'] == script_type]
        if examples:
            print(f"\n{script_type.upper()} examples (first 5):")
            for sentence in examples[:5]:
                print(f"  {sentence['sentence']}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    # Step 1: Load character classifications
    char_script_map = load_character_classifications()

    # Step 2: Classify sentences
    classified_sentences, classification_counts, char_type_distributions = classify_tatoeba_sentences(char_script_map)

    # Step 3: Generate statistics
    generate_statistics(classified_sentences, classification_counts, char_type_distributions)

    print("\n✓ Sentence classification complete!")
