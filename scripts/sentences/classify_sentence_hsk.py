#!/usr/bin/env python3
"""
Classify sentences by HSK level based on maximum character HSK level.

Input:
- cmn_sentences_with_char_pinyin_and_translation.csv
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

    NEW LOGIC: If sentence contains ANY non-HSK Chinese characters,
    classify as "beyond-hsk". Otherwise use maximum HSK level.

    Args:
        char_pinyin_pairs: Pipe-separated pairs like "我:wo3|爱:ai4|你:ni3"
        char_hsk_map: Dict mapping character → hsk_level

    Returns:
        HSK level string ("1"-"6", "7-9", "beyond-hsk", or "" for no Chinese chars)
    """
    if not char_pinyin_pairs:
        return ""

    hsk_levels = []
    has_non_hsk = False

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

        if hsk_level:
            # Has HSK level
            hsk_levels.append(hsk_level)
        else:
            # Chinese character without HSK level
            has_non_hsk = True

    # If contains any non-HSK character, classify as beyond-hsk
    if has_non_hsk:
        return "beyond-hsk"

    # No Chinese characters at all
    if len(hsk_levels) == 0:
        return ""

    # Pure HSK sentence - return maximum level
    return max(hsk_levels, key=hsk_sort_key)


def classify_sentences(input_csv='../../data/sentences/cmn_sentences_with_char_pinyin_and_translation.csv',
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
    ordered_levels = ['1', '2', '3', '4', '5', '6', '7-9', 'beyond-hsk', 'null']

    for level in ordered_levels:
        count = level_counts.get(level, 0)
        pct = count / total_sentences * 100
        if level == 'null':
            label = "No HSK"
        elif level == 'beyond-hsk':
            label = "Beyond HSK"
        else:
            label = f"HSK {level}"
        print(f"  {label:11s}: {count:6,} ({pct:5.1f}%)")

    print(f"\nTotal sentences: {total_sentences:,}")

    # Calculate additional stats
    sentences_with_hsk = sum(level_counts[level] for level in ordered_levels if level not in ['null', 'beyond-hsk'])
    sentences_beyond_hsk = level_counts.get('beyond-hsk', 0)
    sentences_without_hsk = level_counts.get('null', 0)

    print(f"\nSentences with HSK 1-9: {sentences_with_hsk:,} ({sentences_with_hsk/total_sentences*100:.1f}%)")
    print(f"Sentences beyond HSK: {sentences_beyond_hsk:,} ({sentences_beyond_hsk/total_sentences*100:.1f}%)")
    print(f"Sentences without Chinese (null): {sentences_without_hsk:,} ({sentences_without_hsk/total_sentences*100:.1f}%)")

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

    # Exclude 'null' from chart (too small, mention in subtitle instead)
    levels_for_chart = [l for l in ordered_levels if l != 'null']
    counts_for_chart = [level_counts.get(level, 0) for level in levels_for_chart]
    percentages_for_chart = [(count / total_sentences * 100) for count in counts_for_chart]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    # Color scheme: HSK 1-6 in blue gradient, 7-9 in purple, beyond-hsk in orange
    colors = [
        '#1e40af',  # HSK 1 - dark blue
        '#3b82f6',  # HSK 2 - blue
        '#60a5fa',  # HSK 3 - light blue
        '#93c5fd',  # HSK 4 - lighter blue
        '#bfdbfe',  # HSK 5 - very light blue
        '#dbeafe',  # HSK 6 - pale blue
        '#8b5cf6',  # HSK 7-9 - purple (grouped advanced levels)
        '#f59e0b',  # beyond-hsk - orange (non-HSK characters)
    ]
    bars = ax.bar(levels_for_chart, counts_for_chart, color=colors, edgecolor='white', linewidth=1.5)

    # Customize chart
    ax.set_xlabel('HSK Level', fontsize=13, fontweight='bold')
    ax.set_ylabel('Number of Sentences', fontsize=13, fontweight='bold')

    # Title with subtitle showing total sentences
    null_count = level_counts.get('null', 0)
    subtitle = f'Total: {total_sentences:,} sentences'
    if null_count > 0:
        subtitle += f' ({null_count} without Chinese characters excluded from chart)'
    ax.set_title('Sentence Distribution by HSK Level\n' + subtitle,
                 fontsize=14, fontweight='bold', pad=20)

    # Add value labels on bars with counts and percentages
    for i, (bar, count, pct) in enumerate(zip(bars, counts_for_chart, percentages_for_chart)):
        height = bar.get_height()
        # Show count and percentage
        label = f'{int(height):,}\n({pct:.1f}%)'
        ax.text(bar.get_x() + bar.get_width()/2., height,
                label,
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)

    # Format y-axis and set limit with headroom for legend
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.set_ylim(0, 18000)  # Fixed upper limit to ensure legend doesn't overlap

    # Add legend explaining special categories
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#3b82f6', label='HSK 1-6: Official beginner to intermediate'),
        Patch(facecolor='#8b5cf6', label='HSK 7-9: Advanced levels (grouped)'),
        Patch(facecolor='#f59e0b', label='Beyond HSK: Contains non-HSK characters')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)

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
