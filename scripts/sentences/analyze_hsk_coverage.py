#!/usr/bin/env python3
"""
Analyze HSK character coverage in sentence corpus.

Compares two approaches:
1. BEFORE: Classify sentences based only on HSK characters (ignore non-HSK)
2. AFTER: Separate sentences containing any non-HSK characters into new category

Outputs:
- Before/after distribution comparison
- Statistics on non-HSK character usage
- Example sentences from "contains non-HSK" category
- Updated distribution visualization
"""
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
import matplotlib.pyplot as plt


def load_hsk_characters():
    """
    Load all HSK characters from chinese_characters.csv.
    This includes both Simplified and Traditional characters with HSK mappings.

    Returns:
        dict: {character: hsk_level}
    """
    hsk_chars = {}
    char_csv = Path('../../data/chinese_characters.csv')

    with open(char_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            hsk_level = row.get('hsk_level', '').strip()

            # Only include characters with HSK levels
            if hsk_level:
                hsk_chars[char] = hsk_level

    return hsk_chars


def is_chinese_char(char):
    """Check if character is in CJK Unified Ideographs range."""
    code = ord(char)
    return 0x4E00 <= code <= 0x9FFF


def classify_sentence_before(chars, hsk_chars):
    """
    BEFORE approach: Classify based only on HSK characters, ignore non-HSK.

    Returns:
        str or None: HSK level ("1"-"6", "7-9") or None if no HSK chars
    """
    hsk_levels = []

    for char in chars:
        if not is_chinese_char(char):
            continue

        if char in hsk_chars:
            hsk_levels.append(hsk_chars[char])

    if not hsk_levels:
        return None

    # Return highest level found
    # Order: 1 < 2 < 3 < 4 < 5 < 6 < 7-9
    level_priority = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7-9': 7}
    max_level = max(hsk_levels, key=lambda x: level_priority.get(x, 0))
    return max_level


def classify_sentence_after(chars, hsk_chars):
    """
    AFTER approach: Separate sentences with any non-HSK characters.

    Returns:
        tuple: (hsk_level or None, has_non_hsk: bool, non_hsk_chars: list)
    """
    hsk_levels = []
    non_hsk_chars = []

    for char in chars:
        if not is_chinese_char(char):
            continue

        if char in hsk_chars:
            hsk_levels.append(hsk_chars[char])
        else:
            non_hsk_chars.append(char)

    has_non_hsk = len(non_hsk_chars) > 0

    if not hsk_levels:
        hsk_level = None
    else:
        # Return highest level found
        level_priority = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7-9': 7}
        hsk_level = max(hsk_levels, key=lambda x: level_priority.get(x, 0))

    return hsk_level, has_non_hsk, non_hsk_chars


def analyze_corpus():
    """Main analysis function."""
    print("=" * 80)
    print("HSK COVERAGE ANALYSIS")
    print("=" * 80)

    # Load HSK character mappings
    print("\n[1/5] Loading HSK character lists...")
    hsk_chars = load_hsk_characters()
    print(f"   Loaded {len(hsk_chars):,} HSK characters (levels 1-9)")

    # Load sentences
    print("\n[2/5] Loading sentence corpus...")
    input_file = '../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv'

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sentences = list(reader)

    print(f"   Loaded {len(sentences):,} sentences")

    # Analyze both approaches
    print("\n[3/5] Classifying sentences with both approaches...")

    before_distribution = Counter()
    after_distribution = Counter()
    after_non_hsk_distribution = Counter()

    non_hsk_char_freq = Counter()
    non_hsk_sentences = []

    for row in sentences:
        sentence = row['sentence']

        # BEFORE approach (current)
        before_level = classify_sentence_before(sentence, hsk_chars)
        if before_level:
            before_distribution[before_level] += 1
        else:
            before_distribution['null'] += 1

        # AFTER approach (proposed)
        after_level, has_non_hsk, non_hsk_chars_found = classify_sentence_after(sentence, hsk_chars)

        if has_non_hsk:
            # Sentence contains non-HSK characters
            after_distribution['contains_non_hsk'] += 1

            # Track which HSK level it WOULD have been
            if after_level:
                after_non_hsk_distribution[after_level] += 1

            # Track non-HSK character frequency
            for char in non_hsk_chars_found:
                non_hsk_char_freq[char] += 1

            # Save example sentences
            if len(non_hsk_sentences) < 100:  # Keep first 100 examples
                non_hsk_sentences.append({
                    'id': row['id'],
                    'sentence': sentence,
                    'english': row.get('english_translation', ''),
                    'non_hsk_chars': '|'.join(non_hsk_chars_found),
                    'would_be_hsk': after_level or 'null',
                    'before_hsk': before_level or 'null'
                })
        else:
            # Pure HSK sentence
            if after_level:
                after_distribution[after_level] += 1
            else:
                after_distribution['null'] += 1

    # Print results
    print("\n[4/5] Analysis Results")
    print("\n" + "=" * 80)
    print("BEFORE (Current Approach - Ignore Non-HSK Characters)")
    print("=" * 80)

    total_before = sum(before_distribution.values())
    for level in ['1', '2', '3', '4', '5', '6', '7-9', 'null']:
        count = before_distribution.get(level, 0)
        pct = (count / total_before * 100) if total_before > 0 else 0
        print(f"  HSK {level:5s}: {count:6,} sentences ({pct:5.2f}%)")
    print(f"  {'TOTAL':7s}: {total_before:6,} sentences")

    print("\n" + "=" * 80)
    print("AFTER (Proposed - Separate Non-HSK)")
    print("=" * 80)

    total_after = sum(after_distribution.values())
    for level in ['1', '2', '3', '4', '5', '6', '7-9', 'contains_non_hsk', 'null']:
        count = after_distribution.get(level, 0)
        pct = (count / total_after * 100) if total_after > 0 else 0
        label = level if level != 'contains_non_hsk' else 'NON-HSK'
        print(f"  HSK {label:12s}: {count:6,} sentences ({pct:5.2f}%)")
    print(f"  {'TOTAL':15s}: {total_after:6,} sentences")

    # Show what the non-HSK sentences WOULD have been
    non_hsk_count = after_distribution.get('contains_non_hsk', 0)
    if non_hsk_count > 0:
        print(f"\n  Non-HSK sentences breakdown (what level they'd be without non-HSK chars):")
        for level in ['1', '2', '3', '4', '5', '6', '7-9', 'null']:
            count = after_non_hsk_distribution.get(level, 0)
            pct = (count / non_hsk_count * 100) if non_hsk_count > 0 else 0
            if count > 0:
                print(f"    Would be HSK {level:5s}: {count:6,} ({pct:5.2f}%)")

    # Non-HSK character analysis
    print("\n" + "=" * 80)
    print("NON-HSK CHARACTER ANALYSIS")
    print("=" * 80)
    print(f"  Total unique non-HSK characters found: {len(non_hsk_char_freq):,}")
    print(f"  Top 30 most frequent non-HSK characters:")

    for i, (char, freq) in enumerate(non_hsk_char_freq.most_common(30), 1):
        print(f"    {i:2d}. '{char}' - {freq:,} occurrences")

    # Save detailed outputs
    print("\n[5/5] Saving detailed outputs...")

    # Save non-HSK character frequency
    output_dir = Path('../../data/sentences')

    with open(output_dir / 'non_hsk_characters.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['character', 'frequency', 'codepoint'])
        for char, freq in non_hsk_char_freq.most_common():
            writer.writerow([char, freq, f'U+{ord(char):04X}'])
    print(f"   ✓ Saved: {output_dir / 'non_hsk_characters.csv'}")

    # Save example non-HSK sentences
    with open(output_dir / 'non_hsk_sentences_examples.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'sentence', 'english', 'non_hsk_chars', 'would_be_hsk', 'before_hsk'])
        writer.writeheader()
        writer.writerows(non_hsk_sentences)
    print(f"   ✓ Saved: {output_dir / 'non_hsk_sentences_examples.csv'}")

    # Generate comparison visualization
    print("\n   Generating distribution comparison chart...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # BEFORE distribution
    levels_before = ['1', '2', '3', '4', '5', '6', '7-9', 'null']
    counts_before = [before_distribution.get(level, 0) for level in levels_before]
    colors_before = ['#3b82f6'] * 7 + ['#94a3b8']

    ax1.bar(levels_before, counts_before, color=colors_before)
    ax1.set_title('BEFORE: Current Approach\n(Ignore Non-HSK Characters)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('HSK Level', fontsize=12)
    ax1.set_ylabel('Number of Sentences', fontsize=12)
    ax1.set_ylim(0, max(counts_before) * 1.1)

    for i, (level, count) in enumerate(zip(levels_before, counts_before)):
        ax1.text(i, count + max(counts_before) * 0.02, f'{count:,}', ha='center', fontsize=10)

    # AFTER distribution
    levels_after = ['1', '2', '3', '4', '5', '6', '7-9', 'NON-HSK', 'null']
    counts_after = [
        after_distribution.get('1', 0),
        after_distribution.get('2', 0),
        after_distribution.get('3', 0),
        after_distribution.get('4', 0),
        after_distribution.get('5', 0),
        after_distribution.get('6', 0),
        after_distribution.get('7-9', 0),
        after_distribution.get('contains_non_hsk', 0),
        after_distribution.get('null', 0)
    ]
    colors_after = ['#3b82f6'] * 7 + ['#f59e0b', '#94a3b8']

    ax2.bar(levels_after, counts_after, color=colors_after)
    ax2.set_title('AFTER: Proposed Approach\n(Separate Non-HSK Category)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('HSK Level', fontsize=12)
    ax2.set_ylabel('Number of Sentences', fontsize=12)
    ax2.set_ylim(0, max(counts_after) * 1.1)

    for i, (level, count) in enumerate(zip(levels_after, counts_after)):
        ax2.text(i, count + max(counts_after) * 0.02, f'{count:,}', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_dir / 'hsk_distribution_comparison.png', dpi=150, bbox_inches='tight')
    print(f"   ✓ Saved: {output_dir / 'hsk_distribution_comparison.png'}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nOutputs saved to data/sentences/:")
    print("  - non_hsk_characters.csv (all non-HSK chars with frequency)")
    print("  - non_hsk_sentences_examples.csv (100 example sentences)")
    print("  - hsk_distribution_comparison.png (before/after visualization)")

    # Summary recommendation
    print("\n" + "=" * 80)
    print("DECISION GUIDANCE")
    print("=" * 80)

    non_hsk_pct = (after_distribution.get('contains_non_hsk', 0) / total_after * 100)

    print(f"\nIf we add 'contains non-HSK' category:")
    print(f"  - {after_distribution.get('contains_non_hsk', 0):,} sentences ({non_hsk_pct:.1f}%) move to new category")
    print(f"  - Pure HSK sentences: {total_after - after_distribution.get('contains_non_hsk', 0):,}")

    # Check impact on beginner levels
    hsk1_before = before_distribution.get('1', 0)
    hsk1_after = after_distribution.get('1', 0)
    hsk1_loss = hsk1_before - hsk1_after
    hsk1_loss_pct = (hsk1_loss / hsk1_before * 100) if hsk1_before > 0 else 0

    print(f"\n  Impact on HSK 1 (beginner level):")
    print(f"    Before: {hsk1_before:,} sentences")
    print(f"    After:  {hsk1_after:,} sentences")
    print(f"    Loss:   {hsk1_loss:,} sentences ({hsk1_loss_pct:.1f}%)")

    if non_hsk_pct > 20:
        print("\n  ⚠️  HIGH IMPACT: >20% of corpus would move to non-HSK category")
        print("      Consider: Is this too restrictive for learners?")
    elif non_hsk_pct > 10:
        print("\n  ⚙️  MODERATE IMPACT: 10-20% of corpus affected")
        print("      Review: Are these mostly proper nouns/names (acceptable)?")
    else:
        print("\n  ✓ LOW IMPACT: <10% of corpus affected")
        print("      Recommendation: Safe to add non-HSK category")


if __name__ == '__main__':
    analyze_corpus()
