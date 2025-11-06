#!/usr/bin/env python3
"""
Step 7: Add character frequency data to the character dataset.

Counts character occurrences in the sentence corpus and adds a 'freq' column.
Also generates statistics and distribution graphs.

Input:
- step6_enriched.csv (character dataset with hsk_level)
- step5_pinyin_refined.csv or step4_with_hsk.csv (sentence corpus with char_pinyin_pairs)

Output: step7_with_freq.csv (has both hsk_level and freq)
"""
import csv
import os
from pathlib import Path
from collections import Counter

# Optional: matplotlib for distribution graphs (not required for CSV generation)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Note: matplotlib not available - will skip distribution graph generation")


def find_sentence_corpus():
    """
    Find the most recent sentence corpus CSV file.

    Priority:
    1. step5_pinyin_refined.csv (if exists)
    2. step4_with_hsk.csv (fallback)

    Returns:
        Path to CSV file
    """
    base_path = Path('../../data/sentences')

    # Try step5 first (most refined)
    step5_path = base_path / 'step5_pinyin_refined.csv'
    if step5_path.exists():
        return step5_path

    # Fall back to step4
    step4_path = base_path / 'step4_with_hsk.csv'
    if step4_path.exists():
        return step4_path

    raise FileNotFoundError(
        "Could not find sentence corpus CSV file. "
        "Expected step5_pinyin_refined.csv or step4_with_hsk.csv in ../../data/sentences/"
    )


def parse_char_pinyin_pairs(pairs_str):
    """
    Parse char_pinyin_pairs column and extract characters.

    Format: "我:wo3|爱:ai4|你:ni3|。:"
    Returns: list of characters (including punctuation with empty pinyin)
    """
    if not pairs_str or pairs_str.strip() == '':
        return []

    chars = []
    for pair in pairs_str.split('|'):
        if ':' not in pair:
            continue
        char = pair.split(':', 1)[0]
        if char:
            chars.append(char)

    return chars


def is_chinese_character(char):
    """Check if character is in CJK Unified Ideographs range (our character set)."""
    if not char or len(char) != 1:
        return False
    return 0x4E00 <= ord(char) <= 0x9FFF


def parse_sentence_corpus():
    """
    Parse sentence corpus CSV and count character frequency.

    Reads from step5_pinyin_refined.csv or step4_with_hsk.csv.
    Uses char_pinyin_pairs column to extract characters.

    Returns:
        Counter mapping character -> frequency count
    """
    char_counter = Counter()
    total_sentences = 0

    corpus_path = find_sentence_corpus()
    print(f"Parsing sentence corpus: {corpus_path}")

    with open(corpus_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Parse char_pinyin_pairs to get characters
            char_pinyin = row.get('char_pinyin_pairs', '')
            chars = parse_char_pinyin_pairs(char_pinyin)

            # Count only Chinese characters (filter out punctuation)
            chinese_chars = [c for c in chars if is_chinese_character(c)]
            char_counter.update(chinese_chars)

            total_sentences += 1

            if total_sentences % 10000 == 0:
                print(f"  Processed {total_sentences:,} sentences...")

    print(f"\n✓ Processed {total_sentences:,} sentences")
    print(f"  Unique characters found: {len(char_counter):,}")
    print(f"  Total character occurrences: {sum(char_counter.values()):,}")

    return char_counter


def add_frequency_to_csv(char_counter,
                         input_csv='../../data/character_set/step6_enriched.csv',
                         output_csv='../../data/character_set/step7_with_freq.csv'):
    """
    Add frequency column to the character dataset.

    Takes step6_enriched.csv (has hsk_level) and adds freq column.
    """
    print(f"\nReading {input_csv}...")

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Add frequency column
    has_freq = 0
    no_freq = 0

    for row in rows:
        char = row['char']
        freq = char_counter.get(char, 0)
        row['freq'] = freq

        if freq > 0:
            has_freq += 1
        else:
            no_freq += 1

    # Write output CSV with new column
    fieldnames = list(rows[0].keys())  # Preserve existing column order + freq

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Characters with frequency > 0: {has_freq:,} ({has_freq/len(rows)*100:.1f}%)")
    print(f"  Characters with frequency = 0: {no_freq:,} ({no_freq/len(rows)*100:.1f}%)")

    return rows


def generate_statistics(rows):
    """
    Generate detailed frequency statistics.
    """
    print(f"\n{'='*60}")
    print("FREQUENCY STATISTICS")
    print(f"{'='*60}\n")

    freqs = [int(row['freq']) for row in rows]
    non_zero_freqs = [f for f in freqs if f > 0]

    total_chars = len(freqs)
    chars_in_corpus = len(non_zero_freqs)
    chars_not_in_corpus = total_chars - chars_in_corpus

    print(f"Total characters in dataset: {total_chars:,}")
    print(f"Characters appearing in corpus: {chars_in_corpus:,} ({chars_in_corpus/total_chars*100:.1f}%)")
    print(f"Characters NOT in corpus: {chars_not_in_corpus:,} ({chars_not_in_corpus/total_chars*100:.1f}%)")

    if non_zero_freqs:
        print(f"\nFrequency statistics (non-zero only):")
        print(f"  Min frequency: {min(non_zero_freqs):,}")
        print(f"  Max frequency: {max(non_zero_freqs):,}")
        print(f"  Mean frequency: {sum(non_zero_freqs)/len(non_zero_freqs):.1f}")
        print(f"  Median frequency: {sorted(non_zero_freqs)[len(non_zero_freqs)//2]:,}")

        # Percentiles
        sorted_freqs = sorted(non_zero_freqs, reverse=True)
        p50 = sorted_freqs[int(len(sorted_freqs) * 0.5)]
        p75 = sorted_freqs[int(len(sorted_freqs) * 0.75)]
        p90 = sorted_freqs[int(len(sorted_freqs) * 0.90)]
        p95 = sorted_freqs[int(len(sorted_freqs) * 0.95)]
        p99 = sorted_freqs[int(len(sorted_freqs) * 0.99)]

        print(f"\nFrequency percentiles:")
        print(f"  Top 50% threshold: {p50:,}")
        print(f"  Top 75% threshold: {p75:,}")
        print(f"  Top 90% threshold: {p90:,}")
        print(f"  Top 95% threshold: {p95:,}")
        print(f"  Top 99% threshold: {p99:,}")

        # Coverage analysis
        total_occurrences = sum(non_zero_freqs)
        cumulative = 0
        for threshold in [100, 500, 1000, 2000, 3000, 5000]:
            count = sum(1 for f in sorted_freqs if f >= threshold)
            coverage = sum(f for f in sorted_freqs if f >= threshold)
            if count > 0:
                print(f"  {count:,} chars appear ≥{threshold:,} times (cover {coverage/total_occurrences*100:.1f}% of text)")

        # Top 20 most frequent
        char_freq_pairs = [(row['char'], int(row['freq'])) for row in rows if int(row['freq']) > 0]
        char_freq_pairs.sort(key=lambda x: x[1], reverse=True)

        print(f"\nTop 20 most frequent characters:")
        for i, (char, freq) in enumerate(char_freq_pairs[:20], 1):
            print(f"  {i:2d}. {char} - {freq:,} occurrences")

    print(f"\n{'='*60}")

    return freqs


def plot_frequency_distribution(rows, output_file='../../data/character_set/analysis/frequency_distribution.png'):
    """
    Generate distribution graphs.
    Creates two plots:
    1. Full distribution (log scale) - shows Zipf's law power distribution
    2. Head distribution (top characters) - shows practical coverage for learners
    """
    print(f"\nGenerating frequency distribution graphs...")

    freqs = [int(row['freq']) for row in rows]
    non_zero_freqs = [f for f in freqs if f > 0]
    zero_count = len(freqs) - len(non_zero_freqs)

    # Sort by frequency
    sorted_freqs = sorted(non_zero_freqs, reverse=True)

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    # Add main title
    total_chars = len(freqs)
    corpus_chars = len(sorted_freqs)
    fig.suptitle('Character Frequency Distribution in Sentence Corpus',
                 fontsize=14, fontweight='bold', y=0.98)

    # Plot 1: Full distribution (log scale)
    ax1.plot(range(1, len(sorted_freqs) + 1), sorted_freqs, linewidth=2, color='#3b82f6')
    ax1.set_xlabel('Character Rank (by frequency)', fontsize=11)
    ax1.set_ylabel('Frequency (log scale)', fontsize=11)
    ax1.set_title(f'Full Distribution (Zipf\'s Law)\n{corpus_chars:,} characters in corpus',
                  fontsize=11)
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, len(sorted_freqs))

    # Add reference lines
    ax1.axhline(y=100, color='#ef4444', linestyle='--', alpha=0.5, linewidth=1.5, label='≥100 occurrences')
    ax1.axhline(y=1000, color='#f59e0b', linestyle='--', alpha=0.5, linewidth=1.5, label='≥1,000 occurrences')
    ax1.legend(fontsize=9, loc='upper right')

    # Plot 2: Head distribution (top 2000 characters)
    top_n = min(2000, len(sorted_freqs))
    ax2.plot(range(1, top_n + 1), sorted_freqs[:top_n], linewidth=2, color='#10b981')
    ax2.set_xlabel('Character Rank (by frequency)', fontsize=11)
    ax2.set_ylabel('Frequency (linear scale)', fontsize=11)
    ax2.set_title(f'Top {top_n:,} Most Common Characters\nShows steep decline in frequency (80/20 rule)',
                  fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, top_n)

    # Add coverage annotations
    total_occurrences = sum(sorted_freqs)
    top_500_coverage = sum(sorted_freqs[:500]) / total_occurrences * 100 if len(sorted_freqs) >= 500 else 0
    top_1000_coverage = sum(sorted_freqs[:1000]) / total_occurrences * 100 if len(sorted_freqs) >= 1000 else 0
    top_2000_coverage = sum(sorted_freqs[:2000]) / total_occurrences * 100 if len(sorted_freqs) >= 2000 else 0

    annotation_text = f'Coverage Milestones:\n'
    annotation_text += f'Top 500:   {top_500_coverage:.1f}%\n'
    annotation_text += f'Top 1000: {top_1000_coverage:.1f}%\n'
    annotation_text += f'Top 2000: {top_2000_coverage:.1f}%'

    ax2.text(0.98, 0.97, annotation_text,
             transform=ax2.transAxes, fontsize=9, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved distribution graph to {output_file}")

    plt.close()


if __name__ == '__main__':
    print("=" * 70)
    print("Step 7: Add character frequency data")
    print("=" * 70)

    # Step 1: Count character frequency from sentence corpus
    char_counter = parse_sentence_corpus()

    # Step 2: Add frequency to CSV (input: step6, output: step7)
    rows = add_frequency_to_csv(char_counter)

    # Step 3: Generate statistics
    generate_statistics(rows)

    # Step 4: Plot distribution (optional - requires matplotlib)
    if MATPLOTLIB_AVAILABLE:
        plot_frequency_distribution(rows)
    else:
        print("\n⚠️  Skipping distribution graph (matplotlib not installed)")
        print("   To generate graphs: pip install matplotlib")

    print("\n" + "=" * 70)
    print("✓ Step 7 complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review step7_with_freq.csv")
    print("  2. Check frequency_distribution.png")
    print("  3. When ready, copy to production if needed")
