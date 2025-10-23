#!/usr/bin/env python3
"""
Analyze character frequency from Tatoeba sentences and add to dataset.
Also generates statistics and distribution graphs.
"""
import csv
import re
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def extract_chinese_characters(text):
    """
    Extract only Chinese characters from text.
    Filters out punctuation, numbers, Latin characters, etc.
    """
    # Match CJK Unified Ideographs (our character set range)
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return chinese_chars


def parse_tatoeba_sentences(file_path='../../data/sentences/cmn_sentences.tsv'):
    """
    Parse Tatoeba sentences and count character frequency.

    Returns:
        Counter mapping character -> frequency count
    """
    char_counter = Counter()
    total_sentences = 0

    print(f"Parsing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue

            sentence = parts[2]  # Third column is the sentence

            # Extract Chinese characters
            chars = extract_chinese_characters(sentence)
            char_counter.update(chars)

            total_sentences += 1

            if total_sentences % 10000 == 0:
                print(f"  Processed {total_sentences:,} sentences...")

    print(f"\n✓ Processed {total_sentences:,} sentences")
    print(f"  Unique characters found: {len(char_counter):,}")
    print(f"  Total character occurrences: {sum(char_counter.values()):,}")

    return char_counter


def add_frequency_to_csv(char_counter,
                         input_csv='../../data/chinese_characters.csv',
                         output_csv='../../data/chinese_characters_with_freq.csv'):
    """
    Add frequency column to the character dataset.
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


def plot_frequency_distribution(rows, output_file='../../data/character_set/frequency_distribution.png'):
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
    # Step 1: Count character frequency from Tatoeba
    char_counter = parse_tatoeba_sentences()

    # Step 2: Add frequency to CSV
    rows = add_frequency_to_csv(char_counter)

    # Step 3: Generate statistics
    generate_statistics(rows)

    # Step 4: Plot distribution
    plot_frequency_distribution(rows)

    print("\n✓ Analysis complete!")
