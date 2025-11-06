#!/usr/bin/env python3
"""
Analyze the Pinyin Trie and generate statistical reports with visualizations.

Generates:
- Tone distribution charts (3 versions: unique syllables, unique characters, frequency-weighted)
- Depth distribution chart
- Most/least common syllables
- Summary statistics

Output:
- Console report with statistics
- PNG charts in data/character_set/analysis/
"""
import json
import re
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib


def collect_all_syllables(node, prefix=""):
    """
    Recursively collect all complete syllables from the Trie.

    Returns: list of (syllable, characters_data) tuples
    where characters_data is list of {char, pinyin_freq, corpus_freq}
    """
    syllables = []

    if node.get("is_end"):
        syllables.append((prefix, node.get("characters", [])))

    for letter, child in node.get("children", {}).items():
        syllables.extend(collect_all_syllables(child, prefix + letter))

    return syllables


def analyze_depth_distribution(trie):
    """
    Analyze node distribution by depth.

    Returns: dict {depth: node_count}
    """
    def count_by_depth(node, depth=0):
        counts = {depth: 1}

        for child in node.get('children', {}).values():
            child_counts = count_by_depth(child, depth + 1)
            for d, count in child_counts.items():
                counts[d] = counts.get(d, 0) + count

        return counts

    return count_by_depth(trie)


def extract_tone(syllable):
    """
    Extract tone number from syllable.

    Returns: '0' (neutral), '1', '2', '3', '4', or None
    """
    match = re.search(r'(\d)$', syllable)
    if match:
        return match.group(1)
    return None


def analyze_tone_distributions(syllables):
    """
    Analyze tone distributions in three ways.

    Args:
        syllables: list of (syllable, characters_data) tuples

    Returns: dict with three distributions
    """
    # 1. By unique syllables (each syllable counted once)
    syllable_tones = defaultdict(int)

    # 2. By unique characters (each character counted once)
    character_tones = defaultdict(int)

    # 3. By frequency-weighted characters (weighted by corpus frequency)
    frequency_tones = defaultdict(int)

    for syllable, chars_data in syllables:
        tone = extract_tone(syllable)
        if tone is None:
            continue

        tone_key = 'neutral' if tone == '0' else f'tone{tone}'

        # Count syllable once
        syllable_tones[tone_key] += 1

        # Count each character
        character_tones[tone_key] += len(chars_data)

        # Weight by corpus frequency
        for char_info in chars_data:
            corpus_freq = char_info.get('corpus_freq', 0)
            frequency_tones[tone_key] += corpus_freq

    return {
        'syllables': syllable_tones,
        'characters': character_tones,
        'frequency': frequency_tones
    }


def plot_tone_distributions(distributions, output_dir):
    """
    Create bar charts for all three tone distributions.
    """
    # Use a non-interactive backend to avoid display issues
    matplotlib.use('Agg')

    tone_labels = ['Neutral', 'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4']
    tone_keys = ['neutral', 'tone1', 'tone2', 'tone3', 'tone4']
    colors = ['#95E1D3', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Pinyin Tone Distributions', fontsize=16, fontweight='bold')

    titles = [
        'By Unique Syllables\n(each syllable counted once)',
        'By Unique Characters\n(each character counted once)',
        'By Corpus Frequency\n(characters weighted by usage)'
    ]

    dist_keys = ['syllables', 'characters', 'frequency']

    for idx, (ax, title, dist_key) in enumerate(zip(axes, titles, dist_keys)):
        dist = distributions[dist_key]
        values = [dist.get(key, 0) for key in tone_keys]
        total = sum(values)

        # Create bar chart
        bars = ax.bar(tone_labels, values, color=colors, edgecolor='black', linewidth=1.2)

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            percentage = (value / total * 100) if total > 0 else 0
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:,}\n({percentage:.1f}%)',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=11)
        ax.set_xlabel('Tone', fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # Add padding to y-axis to prevent label clipping
        ax.set_ylim(0, max(values) * 1.15)

    plt.tight_layout()
    output_path = output_dir / 'tone_distributions.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved tone distribution chart to {output_path}")


def plot_depth_distribution(depth_counts, output_dir):
    """
    Create bar chart for node distribution by depth.
    """
    matplotlib.use('Agg')

    # Skip depth 0 (root node) - not meaningful for visualization
    depths = [d for d in sorted(depth_counts.keys()) if d > 0]
    counts = [depth_counts[d] for d in depths]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(depths, counts, color='#6C5CE7', edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{count:,}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_title('Trie Node Distribution by Depth', fontsize=14, fontweight='bold')
    ax.set_xlabel('Depth (letters from root)', fontsize=11)
    ax.set_ylabel('Node Count', fontsize=11)
    ax.set_xticks(depths)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.tight_layout()
    output_path = output_dir / 'depth_distribution.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved depth distribution chart to {output_path}")


def plot_polyphonic_characters(polyphonic, output_dir):
    """
    Create bar chart for top 20 polyphonic characters.
    """
    matplotlib.use('Agg')

    # Configure matplotlib to use fonts that support Chinese characters
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Noto Sans CJK', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

    # Get top 20
    top_20 = polyphonic[:20]

    chars = [char for char, _ in top_20]
    pronunciation_counts = [len(pronunciations) for _, pronunciations in top_20]

    fig, ax = plt.subplots(figsize=(14, 8))
    bars = ax.bar(range(len(chars)), pronunciation_counts, color='#E74C3C', edgecolor='black', linewidth=1.2)

    # Add value labels on top of bars
    for i, (bar, count) in enumerate(zip(bars, pronunciation_counts)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{count}',
               ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_title('Top 20 Polyphonic Characters\n(characters with most pronunciations used in corpus)',
                 fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Pronunciations', fontsize=11)
    ax.set_xlabel('Character', fontsize=11)
    ax.set_xticks(range(len(chars)))
    ax.set_xticklabels(chars, fontsize=16, fontweight='bold')  # Increased size for visibility
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max(pronunciation_counts) * 1.15)

    plt.tight_layout()
    output_path = output_dir / 'polyphonic_characters.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved polyphonic characters chart to {output_path}")


def plot_syllable_complexity(complexity, output_dir):
    """
    Create bar chart for syllable complexity (character count distribution).
    """
    matplotlib.use('Agg')

    by_count = complexity['by_count']

    # Get counts and syllable counts for each
    char_counts = sorted(by_count.keys())
    syllable_counts = [len(by_count[c]) for c in char_counts]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(char_counts, syllable_counts, color='#3498DB', edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar, count in zip(bars, syllable_counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{count}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_title('Syllable Complexity Distribution\n(number of syllables by character count)',
                 fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Syllables', fontsize=11)
    ax.set_xlabel('Characters per Syllable', fontsize=11)
    ax.set_xticks(char_counts)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max(syllable_counts) * 1.15)

    # Add statistics text
    stats_text = f"Min: {complexity['min']}  Max: {complexity['max']}  Mean: {complexity['mean']:.1f}  Median: {complexity['median']}"
    ax.text(0.5, 0.98, stats_text, transform=ax.transAxes,
           ha='center', va='top', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    output_path = output_dir / 'syllable_complexity.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved syllable complexity chart to {output_path}")


def plot_syllable_tone_heatmap(matrix_data, output_dir):
    """
    Create heatmap of base syllables × tones showing character count.
    """
    import numpy as np
    matplotlib.use('Agg')

    matrix = matrix_data['matrix']
    base_syllables = matrix_data['base_syllables']
    tones = matrix_data['tones']

    # Create 2D array for heatmap
    # Rows = base syllables, Columns = tones
    data = np.zeros((len(base_syllables), len(tones)))

    for i, base in enumerate(base_syllables):
        for j, tone in enumerate(tones):
            data[i, j] = matrix[base][tone]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, max(12, len(base_syllables) * 0.15)))

    # Create heatmap
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')

    # Set ticks and labels
    ax.set_xticks(range(len(tones)))
    ax.set_xticklabels(['Neutral (0)', 'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4'], fontsize=10)
    ax.set_yticks(range(len(base_syllables)))
    ax.set_yticklabels(base_syllables, fontsize=7)

    # Add x-axis labels at top as well (for long vertical scrolling)
    ax.tick_params(top=True, labeltop=True, bottom=True, labelbottom=True)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Number of Characters', rotation=270, labelpad=20, fontsize=11)

    # Add cell values
    for i in range(len(base_syllables)):
        for j in range(len(tones)):
            value = int(data[i, j])
            if value > 0:
                # Determine text color based on cell brightness
                text_color = 'white' if value > data.max() * 0.6 else 'black'
                ax.text(j, i, str(value), ha='center', va='center',
                       color=text_color, fontsize=7, fontweight='bold')

    ax.set_title(f'Syllable × Tone Matrix\n({len(base_syllables)} base syllables across 5 tones)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Tone', fontsize=11, fontweight='bold')
    ax.set_ylabel('Base Syllable (without tone)', fontsize=11, fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / 'syllable_tone_matrix.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved syllable×tone heatmap to {output_path}")


def analyze_common_syllables(syllables):
    """
    Find most and least common syllables by frequency.

    Args:
        syllables: list of (syllable, characters_data) tuples

    Returns: tuple of (most_common_list, least_common_list)
    """
    # Calculate total frequency for each syllable
    syllable_freqs = []
    for syllable, chars_data in syllables:
        total_freq = sum(c.get('pinyin_freq', 0) for c in chars_data)
        char_count = len(chars_data)
        syllable_freqs.append((syllable, total_freq, char_count))

    # Sort by frequency
    syllable_freqs.sort(key=lambda x: x[1], reverse=True)

    # Get top 20 and bottom 20 (with freq > 0)
    most_common = syllable_freqs[:20]

    # For least common, only include those with freq > 0
    with_freq = [s for s in syllable_freqs if s[1] > 0]
    least_common = with_freq[-20:] if len(with_freq) >= 20 else with_freq

    return most_common, least_common


def analyze_polyphonic_characters(syllables):
    """
    Analyze polyphonic characters (characters with multiple pronunciations).

    Returns: list of (char, pronunciations) sorted by number of pronunciations
    where pronunciations is list of (syllable, pinyin_freq) tuples
    """
    # char -> [(syllable, pinyin_freq, corpus_freq)]
    char_pronunciations = defaultdict(list)

    for syllable, chars_data in syllables:
        for char_info in chars_data:
            char = char_info['char']
            pinyin_freq = char_info['pinyin_freq']
            corpus_freq = char_info['corpus_freq']
            char_pronunciations[char].append((syllable, pinyin_freq, corpus_freq))

    # Filter to only polyphonic (multiple pronunciations)
    polyphonic = []
    for char, pronunciations in char_pronunciations.items():
        if len(pronunciations) > 1:
            # Sort pronunciations by frequency (descending)
            pronunciations.sort(key=lambda x: x[1], reverse=True)
            polyphonic.append((char, pronunciations))

    # Sort by number of pronunciations (descending)
    polyphonic.sort(key=lambda x: len(x[1]), reverse=True)

    return polyphonic


def analyze_syllable_complexity(syllables):
    """
    Analyze syllable complexity (character count per syllable).

    Returns: dict with complexity statistics
    """
    # Group syllables by character count
    by_char_count = defaultdict(list)

    for syllable, chars_data in syllables:
        char_count = len(chars_data)
        total_freq = sum(c.get('pinyin_freq', 0) for c in chars_data)
        by_char_count[char_count].append((syllable, total_freq, char_count))

    # Calculate statistics
    all_counts = [len(chars_data) for _, chars_data in syllables]

    return {
        'by_count': by_char_count,
        'min': min(all_counts),
        'max': max(all_counts),
        'mean': sum(all_counts) / len(all_counts),
        'median': sorted(all_counts)[len(all_counts) // 2]
    }


def analyze_syllable_tone_matrix(syllables):
    """
    Create a matrix of base syllables (without tone) × tones.

    Returns: dict with:
        - matrix: dict {base_syllable: {tone: char_count}}
        - base_syllables: sorted list of base syllables
        - tones: list of tones [0, 1, 2, 3, 4]
    """
    # Pattern to extract tone number (last digit)
    tone_pattern = re.compile(r'([0-4])$')

    matrix = defaultdict(lambda: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0})

    for syllable, chars_data in syllables:
        # Extract tone from syllable
        match = tone_pattern.search(syllable)
        if match:
            tone = int(match.group(1))
            base = syllable[:-1]  # Remove tone digit
            char_count = len(chars_data)
            matrix[base][tone] = char_count

    # Sort base syllables alphabetically
    base_syllables = sorted(matrix.keys())

    return {
        'matrix': matrix,
        'base_syllables': base_syllables,
        'tones': [0, 1, 2, 3, 4],
        'total_bases': len(base_syllables)
    }


def print_summary_statistics(syllables, depth_counts, distributions):
    """
    Print comprehensive summary statistics.
    """
    print("\n" + "=" * 70)
    print("PINYIN TRIE ANALYSIS SUMMARY")
    print("=" * 70)

    # Basic counts
    total_syllables = len(syllables)
    total_chars = sum(len(chars_data) for _, chars_data in syllables)
    total_corpus_freq = sum(
        c.get('corpus_freq', 0)
        for _, chars_data in syllables
        for c in chars_data
    )

    print(f"\nBasic Statistics:")
    print(f"  Total unique syllables: {total_syllables:,}")
    print(f"  Total unique characters: {total_chars:,}")
    print(f"  Total corpus frequency: {total_corpus_freq:,}")
    print(f"  Max depth: {max(depth_counts.keys())}")
    print(f"  Total nodes: {sum(depth_counts.values()):,}")

    # Tone distributions
    print(f"\n" + "-" * 70)
    print("Tone Distributions:")
    print("-" * 70)

    tone_labels = {
        'neutral': 'Neutral',
        'tone1': 'Tone 1',
        'tone2': 'Tone 2',
        'tone3': 'Tone 3',
        'tone4': 'Tone 4'
    }

    for dist_name, dist_label in [
        ('syllables', 'By Unique Syllables'),
        ('characters', 'By Unique Characters'),
        ('frequency', 'By Corpus Frequency')
    ]:
        dist = distributions[dist_name]
        total = sum(dist.values())

        print(f"\n{dist_label} (Total: {total:,}):")
        for key in ['neutral', 'tone1', 'tone2', 'tone3', 'tone4']:
            count = dist.get(key, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {tone_labels[key]:10s}: {count:6,} ({pct:5.1f}%)")

    # Depth distribution
    print(f"\n" + "-" * 70)
    print("Node Distribution by Depth:")
    print("-" * 70)
    for depth in sorted(depth_counts.keys()):
        count = depth_counts[depth]
        print(f"  Depth {depth}: {count:4,} nodes")


def print_common_syllables(most_common, least_common):
    """
    Print most and least common syllables.
    """
    print(f"\n" + "-" * 70)
    print("Most Common Syllables (by pinyin frequency):")
    print("-" * 70)
    print(f"{'Rank':<6} {'Syllable':<10} {'Chars':<8} {'Frequency':<12}")
    print("-" * 70)
    for i, (syllable, freq, char_count) in enumerate(most_common, 1):
        print(f"{i:<6} {syllable:<10} {char_count:<8} {freq:,}")

    print(f"\n" + "-" * 70)
    print("Least Common Syllables (with frequency > 0):")
    print("-" * 70)
    print(f"{'Rank':<6} {'Syllable':<10} {'Chars':<8} {'Frequency':<12}")
    print("-" * 70)
    for i, (syllable, freq, char_count) in enumerate(reversed(least_common), 1):
        print(f"{i:<6} {syllable:<10} {char_count:<8} {freq:,}")


def main():
    print("=" * 70)
    print("Pinyin Trie Analysis")
    print("=" * 70)

    # Load Trie
    trie_path = Path('../../../data/character_set/analysis/pinyin_trie.json')
    print(f"\nLoading Trie from {trie_path}...")

    with open(trie_path, 'r', encoding='utf-8') as f:
        trie = json.load(f)

    print("✓ Trie loaded")

    # Collect syllables
    print("\nAnalyzing syllables...")
    syllables = collect_all_syllables(trie)
    print(f"✓ Found {len(syllables):,} syllables")

    # Analyze depth distribution
    print("\nAnalyzing depth distribution...")
    depth_counts = analyze_depth_distribution(trie)
    print(f"✓ Max depth: {max(depth_counts.keys())}")

    # Analyze tone distributions
    print("\nAnalyzing tone distributions...")
    distributions = analyze_tone_distributions(syllables)
    print("✓ Tone distributions calculated")

    # Analyze common syllables
    print("\nFinding most/least common syllables...")
    most_common, least_common = analyze_common_syllables(syllables)
    print("✓ Common syllables identified")

    # Analyze polyphonic characters
    print("\nAnalyzing polyphonic characters...")
    polyphonic = analyze_polyphonic_characters(syllables)
    print(f"✓ Found {len(polyphonic):,} polyphonic characters")

    # Analyze syllable complexity
    print("\nAnalyzing syllable complexity...")
    complexity = analyze_syllable_complexity(syllables)
    print("✓ Syllable complexity calculated")

    # Analyze syllable × tone matrix
    print("\nAnalyzing syllable × tone matrix...")
    matrix_data = analyze_syllable_tone_matrix(syllables)
    print(f"✓ Found {matrix_data['total_bases']:,} base syllables across 5 tones")

    # Print summary statistics
    print_summary_statistics(syllables, depth_counts, distributions)
    print_common_syllables(most_common, least_common)

    # Print polyphonic character summary
    print(f"\n" + "-" * 70)
    print(f"Polyphonic Characters:")
    print("-" * 70)
    print(f"Total polyphonic characters: {len(polyphonic):,} ({len(polyphonic)/len([c for _, chars in syllables for c in chars])*100:.1f}% of all characters)")
    print(f"\nTop 10 most polyphonic:")
    for i, (char, pronunciations) in enumerate(polyphonic[:10], 1):
        pron_str = ", ".join([f"{syl}({freq:,})" for syl, freq, _ in pronunciations[:3]])
        if len(pronunciations) > 3:
            pron_str += f" ... ({len(pronunciations)-3} more)"
        print(f"  {i:2d}. {char} ({len(pronunciations)} pronunciations): {pron_str}")

    # Generate charts
    print(f"\n" + "=" * 70)
    print("Generating Charts:")
    print("=" * 70 + "\n")

    output_dir = trie_path.parent
    plot_tone_distributions(distributions, output_dir)
    plot_depth_distribution(depth_counts, output_dir)
    plot_polyphonic_characters(polyphonic, output_dir)
    plot_syllable_complexity(complexity, output_dir)
    plot_syllable_tone_heatmap(matrix_data, output_dir)

    print("\n" + "=" * 70)
    print("✓ Analysis complete!")
    print("=" * 70)
    print(f"\nOutputs:")
    print(f"  - {output_dir / 'tone_distributions.png'}")
    print(f"  - {output_dir / 'depth_distribution.png'}")
    print(f"  - {output_dir / 'polyphonic_characters.png'}")
    print(f"  - {output_dir / 'syllable_complexity.png'}")
    print(f"  - {output_dir / 'syllable_tone_matrix.png'}")


if __name__ == '__main__':
    main()
