#!/usr/bin/env python3
"""
Step 6: Add character and pinyin frequency data to the character dataset.

Counts both character-level and pinyin-level frequencies from the sentence corpus:
- Character frequency: Total occurrences of each character (stored in 'freq' column)
- Pinyin frequency: Occurrences of each character-pinyin pair (added to pinyins_tone3)

This is the final step in the character pipeline. The old step6 (pypinyin enrichment)
was merged into step2, and step7 was renamed/enhanced to become this step6.

Input:
- step5_hsk.csv (character dataset with hsk_level)
- step5_pinyin_refined.csv (sentence corpus with char_pinyin_pairs)

Output: step6_with_freq.csv (has freq + pinyin frequencies)
"""
import csv
import os
from pathlib import Path
from collections import Counter, defaultdict

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
    Parse char_pinyin_pairs column and extract both characters and (char, pinyin) pairs.

    Format: "我:wo3|爱:ai4|你:ni3|。:"

    Returns:
        (chars, char_pinyin_tuples) where:
        - chars: list of characters
        - char_pinyin_tuples: list of (char, pinyin) tuples (for pinyin-level freq)
    """
    if not pairs_str or pairs_str.strip() == '':
        return [], []

    chars = []
    char_pinyin_tuples = []

    for pair in pairs_str.split('|'):
        if ':' not in pair:
            continue
        parts = pair.split(':', 1)
        char = parts[0]
        pinyin = parts[1] if len(parts) > 1 else ''

        if char:
            chars.append(char)
            # Only track pinyin pairs for characters with pinyin (not punctuation)
            if pinyin:
                char_pinyin_tuples.append((char, pinyin))

    return chars, char_pinyin_tuples


def is_chinese_character(char):
    """Check if character is in CJK Unified Ideographs range (our character set)."""
    if not char or len(char) != 1:
        return False
    return 0x4E00 <= ord(char) <= 0x9FFF


def parse_sentence_corpus():
    """
    Parse sentence corpus CSV and count both character and pinyin frequencies.

    Reads from step5_pinyin_refined.csv or step4_with_hsk.csv.
    Uses char_pinyin_pairs column to extract characters and pinyin.

    Returns:
        (char_counter, char_pinyin_counter) where:
        - char_counter: Counter mapping character -> frequency count
        - char_pinyin_counter: Counter mapping (char, pinyin) -> frequency count
    """
    char_counter = Counter()
    char_pinyin_counter = Counter()
    total_sentences = 0

    corpus_path = find_sentence_corpus()
    print(f"Parsing sentence corpus: {corpus_path}")

    with open(corpus_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Parse char_pinyin_pairs to get both characters and pairs
            char_pinyin = row.get('char_pinyin_pairs', '')
            chars, char_pinyin_tuples = parse_char_pinyin_pairs(char_pinyin)

            # Count only Chinese characters (filter out punctuation)
            chinese_chars = [c for c in chars if is_chinese_character(c)]
            char_counter.update(chinese_chars)

            # Count character-pinyin pairs
            chinese_pairs = [(c, p) for c, p in char_pinyin_tuples if is_chinese_character(c)]
            char_pinyin_counter.update(chinese_pairs)

            total_sentences += 1

            if total_sentences % 10000 == 0:
                print(f"  Processed {total_sentences:,} sentences...")

    print(f"\n✓ Processed {total_sentences:,} sentences")
    print(f"  Unique characters found: {len(char_counter):,}")
    print(f"  Total character occurrences: {sum(char_counter.values()):,}")
    print(f"  Unique char-pinyin pairs: {len(char_pinyin_counter):,}")
    print(f"  Total pair occurrences: {sum(char_pinyin_counter.values()):,}")

    return char_counter, char_pinyin_counter


def build_pinyin_freq_map(char_pinyin_counter):
    """
    Build a mapping from character to {pinyin: frequency}.

    Args:
        char_pinyin_counter: Counter of (char, pinyin) tuples

    Returns:
        Dict mapping char -> {pinyin: freq, pinyin: freq, ...}
    """
    pinyin_freq_map = defaultdict(dict)

    for (char, pinyin), freq in char_pinyin_counter.items():
        pinyin_freq_map[char][pinyin] = freq

    return dict(pinyin_freq_map)


def add_frequency_to_csv(char_counter, pinyin_freq_map,
                         input_csv='../../data/character_set/step5_hsk.csv',
                         output_csv='../../data/character_set/step6_with_freq.csv'):
    """
    Add character frequency and pinyin frequencies to the character dataset.

    Takes step5_hsk.csv and adds:
    - 'freq' column: character-level frequency
    - Updates pinyins_tone3: adds (freq) to each pinyin (e.g., "yi1(1234)|yi4(567)")
    - Keeps pinyins_display as-is (no frequency data)
    """
    print(f"\nReading {input_csv}...")

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Add frequency columns
    has_char_freq = 0
    no_char_freq = 0
    has_pinyin_freq = 0

    for row in rows:
        char = row['char']

        # Add character-level frequency
        char_freq = char_counter.get(char, 0)
        row['freq'] = char_freq

        if char_freq > 0:
            has_char_freq += 1
        else:
            no_char_freq += 1

        # Add pinyin-level frequencies to pinyins_tone3 column
        existing_pinyins_tone3 = row.get('pinyins_tone3', '')

        if existing_pinyins_tone3 and char in pinyin_freq_map:
            pinyin_freqs = pinyin_freq_map[char]

            # Split existing pinyins and add frequencies
            pinyin_parts = existing_pinyins_tone3.split('|')
            enriched_parts = []

            for py in pinyin_parts:
                # Check if this pinyin has a frequency
                if py in pinyin_freqs:
                    enriched_parts.append(f"{py}({pinyin_freqs[py]})")
                    has_pinyin_freq += 1
                else:
                    # Keep pinyin without frequency if not found in corpus
                    enriched_parts.append(py)

            row['pinyins_tone3'] = '|'.join(enriched_parts)

    # Write output CSV with new column
    fieldnames = list(rows[0].keys())  # Preserve existing column order + freq

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created {output_csv}")
    print(f"  Characters with frequency > 0: {has_char_freq:,} ({has_char_freq/len(rows)*100:.1f}%)")
    print(f"  Characters with frequency = 0: {no_char_freq:,} ({no_char_freq/len(rows)*100:.1f}%)")
    print(f"  Pinyin pronunciations with frequency data: {has_pinyin_freq:,}")

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
            # Also show their pinyins with frequencies
            row = next((r for r in rows if r['char'] == char), None)
            pinyins = row.get('pinyins_tone3', '') if row else ''
            print(f"  {i:2d}. {char} ({pinyins}) - {freq:,} occurrences")

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
    print("Step 6: Add character and pinyin frequency data")
    print("=" * 70)

    # Step 1: Count frequencies from sentence corpus (both character and pinyin-level)
    char_counter, char_pinyin_counter = parse_sentence_corpus()

    # Step 2: Build pinyin frequency map
    pinyin_freq_map = build_pinyin_freq_map(char_pinyin_counter)

    # Step 3: Add frequencies to CSV (input: step5, output: step6)
    rows = add_frequency_to_csv(char_counter, pinyin_freq_map)

    # Step 4: Generate statistics
    generate_statistics(rows)

    # Step 5: Plot distribution (optional - requires matplotlib)
    if MATPLOTLIB_AVAILABLE:
        plot_frequency_distribution(rows)
    else:
        print("\n⚠️  Skipping distribution graph (matplotlib not installed)")
        print("   To generate graphs: pip install matplotlib")

    print("\n" + "=" * 70)
    print("✓ Step 6 complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review step6_with_freq.csv")
    print("  2. Check frequency_distribution.png")
    print("  3. Copy to production: data/character_set/chinese_characters.csv")
