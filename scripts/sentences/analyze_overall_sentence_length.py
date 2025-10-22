#!/usr/bin/env python3
"""
Analyze overall sentence length distribution (all HSK levels combined).

Shows the aggregate sentence length pattern across the entire corpus.

Inputs:
- sentences_with_translation.json

Outputs:
- overall_sentence_length_distribution.png
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np


def load_sentences(json_path='../../app/public/data/sentences/sentences_with_translation.json'):
    """Load sentence data from production JSON."""
    print(f"Loading sentences from {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sentences = data.get('sentences', [])
    print(f"✓ Loaded {len(sentences):,} sentences")

    return sentences


def analyze_overall_lengths(sentences):
    """Analyze overall sentence lengths."""
    print("\nAnalyzing overall sentence lengths...")

    lengths = []

    for sentence in sentences:
        chinese_text = sentence.get('sentence', '')
        # Count only Chinese characters
        char_count = sum(1 for c in chinese_text if '\u4e00' <= c <= '\u9fff')

        if char_count > 0:
            lengths.append(char_count)

    # Calculate statistics
    stats = {
        'count': len(lengths),
        'mean': np.mean(lengths),
        'median': np.median(lengths),
        'std': np.std(lengths),
        'min': min(lengths),
        'max': max(lengths),
        'q25': np.percentile(lengths, 25),
        'q75': np.percentile(lengths, 75),
        'q90': np.percentile(lengths, 90),
        'q95': np.percentile(lengths, 95)
    }

    print(f"  Total sentences: {stats['count']:,}")
    print(f"  Mean: {stats['mean']:.1f} characters")
    print(f"  Median: {stats['median']:.1f} characters")
    print(f"  Range: [{stats['min']}-{stats['max']}] characters")
    print(f"  25th percentile: {stats['q25']:.1f}")
    print(f"  75th percentile: {stats['q75']:.1f}")
    print(f"  90th percentile: {stats['q90']:.1f}")
    print(f"  95th percentile: {stats['q95']:.1f}")

    return lengths, stats


def plot_overall_distribution(lengths, stats,
                              output_file='../../data/sentences/overall_sentence_length_distribution.png'):
    """Generate overall sentence length distribution histogram."""
    print(f"\nGenerating overall distribution chart...")

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create histogram (limit to reasonable range to avoid long tail)
    max_display = 50  # Show up to 50 characters
    lengths_capped = [min(l, max_display) for l in lengths]

    # Calculate bins
    bins = range(0, max_display + 2)

    # Plot histogram
    n, bins_edges, patches = ax.hist(lengths_capped, bins=bins, edgecolor='black',
                                     color='#3b82f6', alpha=0.7, linewidth=0.5)

    # Add vertical lines for key statistics
    ax.axvline(stats['median'], color='red', linewidth=2.5, linestyle='-',
               label=f'Median: {stats["median"]:.0f} chars', zorder=10)
    ax.axvline(stats['mean'], color='darkgreen', linewidth=2.5, linestyle='--',
               label=f'Mean: {stats["mean"]:.1f} chars', zorder=10)
    ax.axvline(stats['q25'], color='orange', linewidth=2, linestyle=':',
               label=f'25th percentile: {stats["q25"]:.0f} chars', alpha=0.7, zorder=10)
    ax.axvline(stats['q75'], color='orange', linewidth=2, linestyle=':',
               label=f'75th percentile: {stats["q75"]:.0f} chars', alpha=0.7, zorder=10)

    # Customize plot
    ax.set_xlabel('Sentence Length (character count)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Number of Sentences', fontsize=13, fontweight='bold')

    # Add horizontal grid lines
    ax.yaxis.grid(True, linestyle='-', alpha=0.2, linewidth=1.5, color='gray')
    ax.set_axisbelow(True)

    # Titles
    fig.suptitle('Overall Sentence Length Distribution',
                 fontsize=14, fontweight='bold', y=0.96)

    subtitle_text = f'Histogram of sentence lengths across all HSK levels (showing 1-{max_display} characters)'
    ax.text(0.5, 1.04, subtitle_text, transform=ax.transAxes,
            ha='center', fontsize=9, style='italic', color='#666666')

    # Add legend
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

    # Add statistics box
    stats_text = f'Statistics:\n'
    stats_text += f'Total: {stats["count"]:,} sentences\n'
    stats_text += f'Median: {stats["median"]:.0f} chars\n'
    stats_text += f'Mean: {stats["mean"]:.1f} chars\n'
    stats_text += f'Std Dev: {stats["std"]:.1f}\n'
    stats_text += f'90th %ile: {stats["q90"]:.0f} chars\n'
    stats_text += f'95th %ile: {stats["q95"]:.0f} chars'

    ax.text(0.02, 0.98, stats_text.strip(),
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    # Footer
    over_max = sum(1 for l in lengths if l > max_display)
    if over_max > 0:
        footer_text = f'Note: {over_max:,} sentences longer than {max_display} characters not shown in detail'
        ax.text(0.5, -0.10, footer_text, transform=ax.transAxes,
                ha='center', fontsize=9, style='italic', color='#666666')

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')

    print(f"✓ Saved overall distribution chart to {output_file}")
    plt.close()


if __name__ == '__main__':
    # Load sentences
    sentences = load_sentences()

    # Analyze lengths
    lengths, stats = analyze_overall_lengths(sentences)

    # Generate visualization
    plot_overall_distribution(lengths, stats)

    print("\n✓ Overall sentence length analysis complete!")
