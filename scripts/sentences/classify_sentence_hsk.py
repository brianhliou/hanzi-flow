#!/usr/bin/env python3
"""
Classify sentences by HSK level based on maximum character HSK level.

Input:
- cmn_sentences_with_char_pinyin_and_translation_TEST.csv
- chinese_characters.csv (with hsk_level column)

Output:
- cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv (adds sentence_hsk_level column)
- hsk_distribution.png (bar chart)
- hsk_statistics.json (distribution stats)
"""

import csv
import json
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


def hsk_sort_key(level_str):
    """
    Custom sort key for HSK levels.
    Treats "7-9" as 7 for comparison purposes.

    Args:
        level_str: HSK level as string ("1"-"6" or "7-9")

    Returns:
        Integer sort key

    Examples:
        "1" → 1
        "6" → 6
        "7-9" → 7
    """
    if level_str == "7-9":
        return 7
    return int(level_str)


def load_char_hsk_mapping(csv_path='../../data/chinese_characters.csv'):
    """
    Load character → HSK level mapping from character dataset.

    Args:
        csv_path: Path to chinese_characters.csv

    Returns:
        Dict mapping character → hsk_level (string or empty string)
    """
    char_hsk_map = {}

    print(f"Loading character HSK mapping from {csv_path}...")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            hsk_level = row.get('hsk_level', '')
            char_hsk_map[char] = hsk_level

    # Count how many have HSK levels
    total_chars = len(char_hsk_map)
    chars_with_hsk = sum(1 for level in char_hsk_map.values() if level)

    print(f"✓ Loaded {total_chars:,} characters")
    print(f"  Characters with HSK levels: {chars_with_hsk:,} ({chars_with_hsk/total_chars*100:.1f}%)")

    return char_hsk_map


def classify_sentence_hsk(char_pinyin_pairs, char_hsk_map):
    """
    Calculate sentence HSK level from char:pinyin pairs.

    Uses maximum HSK level of all Chinese characters in the sentence,
    ignoring punctuation and characters without HSK levels.

    Args:
        char_pinyin_pairs: Pipe-separated pairs like "我:wo3|爱:ai4|你:ni3"
        char_hsk_map: Dict mapping character → hsk_level

    Returns:
        HSK level string ("1"-"6", "7-9", or "" for no HSK chars)
    """
    if not char_pinyin_pairs:
        return ""

    hsk_levels = []

    # Parse pairs
    pairs = char_pinyin_pairs.split('|')

    for pair in pairs:
        if ':' not in pair:
            continue

        char, pinyin = pair.split(':', 1)

        # Skip non-Chinese characters (no pinyin)
        if not pinyin or pinyin.strip() == '':
            continue

        # Look up HSK level
        hsk_level = char_hsk_map.get(char, '')

        # Skip if no HSK level
        if not hsk_level:
            continue

        hsk_levels.append(hsk_level)

    # Calculate max HSK level
    if len(hsk_levels) == 0:
        return ""  # No HSK characters found

    # Return maximum using custom sort key
    return max(hsk_levels, key=hsk_sort_key)


def classify_sentences(input_csv='../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_TEST.csv',
                       output_csv='../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv',
                       char_csv='../../data/chinese_characters.csv'):
    """
    Classify all sentences by HSK level.

    Args:
        input_csv: Input sentence CSV path
        output_csv: Output sentence CSV path (with sentence_hsk_level column)
        char_csv: Character dataset CSV path
    """
    print(f"\n{'='*60}")
    print("SENTENCE HSK CLASSIFICATION")
    print(f"{'='*60}\n")

    # Step 1: Load character HSK mapping
    char_hsk_map = load_char_hsk_mapping(char_csv)

    # Step 2: Load sentences
    print(f"\nLoading sentences from {input_csv}...")

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    print(f"✓ Loaded {len(sentences):,} sentences")

    # Step 3: Classify each sentence
    print("\nClassifying sentences by HSK level...")

    for i, sentence in enumerate(sentences, 1):
        char_pinyin_pairs = sentence.get('char_pinyin_pairs', '')
        sentence_hsk_level = classify_sentence_hsk(char_pinyin_pairs, char_hsk_map)
        sentence['sentence_hsk_level'] = sentence_hsk_level

        if i % 10000 == 0:
            print(f"  Classified {i:,} sentences...")

    print(f"✓ Classified all {len(sentences):,} sentences")

    # Step 4: Write output CSV
    print(f"\nWriting output to {output_csv}...")

    # Determine fieldnames (all existing + sentence_hsk_level)
    fieldnames = list(sentences[0].keys())

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentences)

    print(f"✓ Created {output_csv}")

    return sentences


def generate_statistics(sentences,
                       output_json='../../data/sentences/hsk_statistics.json',
                       output_chart='../../data/sentences/hsk_distribution.png'):
    """
    Generate distribution statistics and visualizations.

    Args:
        sentences: List of sentence dicts with sentence_hsk_level field
        output_json: Path to save statistics JSON
        output_chart: Path to save distribution chart
    """
    print(f"\n{'='*60}")
    print("HSK LEVEL DISTRIBUTION")
    print(f"{'='*60}\n")

    total_sentences = len(sentences)

    # Count by HSK level
    level_counts = Counter()

    for sentence in sentences:
        hsk_level = sentence.get('sentence_hsk_level', '')
        if hsk_level:
            level_counts[hsk_level] += 1
        else:
            level_counts['null'] += 1

    # Print distribution table
    print("Sentence distribution by HSK level:")

    # Define order for display
    ordered_levels = ['1', '2', '3', '4', '5', '6', '7-9', 'null']

    for level in ordered_levels:
        count = level_counts.get(level, 0)
        pct = count / total_sentences * 100
        label = f"HSK {level}" if level != 'null' else "No HSK"
        print(f"  {label:8s}: {count:6,} ({pct:5.1f}%)")

    print(f"\nTotal sentences: {total_sentences:,}")

    # Calculate additional stats
    sentences_with_hsk = sum(level_counts[level] for level in ordered_levels if level != 'null')
    sentences_without_hsk = level_counts.get('null', 0)

    print(f"\nSentences with HSK classification: {sentences_with_hsk:,} ({sentences_with_hsk/total_sentences*100:.1f}%)")
    print(f"Sentences without HSK (null): {sentences_without_hsk:,} ({sentences_without_hsk/total_sentences*100:.1f}%)")

    # Save statistics to JSON
    stats = {
        'total_sentences': total_sentences,
        'sentences_with_hsk': sentences_with_hsk,
        'sentences_without_hsk': sentences_without_hsk,
        'distribution': {
            level: {
                'count': level_counts.get(level, 0),
                'percentage': round(level_counts.get(level, 0) / total_sentences * 100, 2)
            }
            for level in ordered_levels
        }
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved statistics to {output_json}")

    # Generate bar chart
    print(f"\nGenerating distribution chart...")

    levels_for_chart = ordered_levels
    counts_for_chart = [level_counts.get(level, 0) for level in levels_for_chart]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create bars
    colors = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff', '#8b5cf6', '#94a3b8']
    bars = ax.bar(levels_for_chart, counts_for_chart, color=colors)

    # Customize chart
    ax.set_xlabel('HSK Level', fontsize=12)
    ax.set_ylabel('Number of Sentences', fontsize=12)
    ax.set_title('Sentence Distribution by HSK Level', fontsize=14, fontweight='bold')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=10)

    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)

    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.tight_layout()
    plt.savefig(output_chart, dpi=150, bbox_inches='tight')

    print(f"✓ Saved chart to {output_chart}")

    # Show example sentences
    print(f"\n{'='*60}")
    print("EXAMPLE SENTENCES BY HSK LEVEL")
    print(f"{'='*60}")

    for level in ordered_levels:
        examples = [s for s in sentences if s.get('sentence_hsk_level') == ('' if level == 'null' else level)]
        if examples:
            label = f"HSK {level}" if level != 'null' else "No HSK"
            print(f"\n{label} (first 5):")
            for sentence in examples[:5]:
                print(f"  {sentence['sentence']}")
                print(f"    EN: {sentence.get('english_translation', 'N/A')}")

    print(f"\n{'='*60}")


def main():
    """Main entry point."""
    # Classify sentences
    sentences = classify_sentences()

    # Generate statistics and charts
    generate_statistics(sentences)

    print("\n✓ Sentence HSK classification complete!")


if __name__ == '__main__':
    main()
