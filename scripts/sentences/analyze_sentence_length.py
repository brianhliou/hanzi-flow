#!/usr/bin/env python3
"""
Analyze and visualize sentence length distribution by HSK level.

Shows how sentence complexity (measured by character count) increases
across HSK levels, demonstrating curriculum progression.

Inputs:
- sentences_with_translation.json

Outputs:
- sentence_length_distribution.png
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from collections import defaultdict
import numpy as np


def load_sentences(json_path='../../app/public/data/sentences/sentences_with_translation.json'):
    """Load sentence data from production JSON."""
    print(f"Loading sentences from {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sentences = data.get('sentences', [])
    print(f"✓ Loaded {len(sentences):,} sentences")

    return sentences


def analyze_sentence_lengths(sentences):
    """Analyze sentence lengths by HSK level."""
    print("\nAnalyzing sentence lengths by HSK level...")

    lengths_by_hsk = defaultdict(list)

    for sentence in sentences:
        hsk_level = sentence.get('hskLevel', '').strip()
        chinese_text = sentence.get('sentence', '')

        # Count only Chinese characters
        char_count = sum(1 for c in chinese_text if '\u4e00' <= c <= '\u9fff')

        if hsk_level and char_count > 0:
            lengths_by_hsk[hsk_level].append(char_count)

    # Calculate statistics
    stats = {}
    for level in ['1', '2', '3', '4', '5', '6', '7-9', 'beyond-hsk']:
        if level in lengths_by_hsk:
            lengths = lengths_by_hsk[level]
            stats[level] = {
                'count': len(lengths),
                'mean': np.mean(lengths),
                'median': np.median(lengths),
                'min': min(lengths),
                'max': max(lengths),
                'std': np.std(lengths)
            }
            print(f"  HSK {level:10s}: {len(lengths):6,} sentences, "
                  f"mean={stats[level]['mean']:.1f}, median={stats[level]['median']:.1f}, "
                  f"range=[{stats[level]['min']}-{stats[level]['max']}]")

    return lengths_by_hsk, stats


def plot_sentence_length_distribution(lengths_by_hsk, stats,
                                      output_file='../../data/sentences/sentence_length_distribution.png'):
    """Generate sentence length distribution visualization using violin plots."""
    print(f"\nGenerating sentence length distribution chart...")

    # Prepare data
    levels = ['1', '2', '3', '4', '5', '6', '7-9', 'beyond-hsk']
    levels_present = [l for l in levels if l in lengths_by_hsk]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Prepare data for violin plot
    data_to_plot = [lengths_by_hsk[level] for level in levels_present]

    # Color scheme matching other visualizations
    colors = {
        '1': '#1e40af',
        '2': '#3b82f6',
        '3': '#60a5fa',
        '4': '#93c5fd',
        '5': '#bfdbfe',
        '6': '#dbeafe',
        '7-9': '#8b5cf6',
        'beyond-hsk': '#f59e0b'
    }
    violin_colors = [colors[level] for level in levels_present]

    # Create violin plot (shows distribution shape without overwhelming outliers)
    # Only show median since mean and median are very close (overlapping)
    positions = range(1, len(levels_present) + 1)
    parts = ax.violinplot(data_to_plot, positions=positions, showmeans=False, showmedians=True,
                          widths=0.7)

    # Color the violin plots
    for i, (pc, color) in enumerate(zip(parts['bodies'], violin_colors)):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1)

    # Style the median lines
    parts['cmedians'].set_edgecolor('red')
    parts['cmedians'].set_linewidth(2.5)

    # Set x-axis labels
    ax.set_xticks(positions)
    ax.set_xticklabels(levels_present)

    # Customize plot
    ax.set_xlabel('HSK Level', fontsize=13, fontweight='bold')
    ax.set_ylabel('Sentence Length (character count)', fontsize=13, fontweight='bold')

    # Add horizontal grid lines (more frequent and visible)
    ax.yaxis.set_major_locator(plt.MultipleLocator(25))  # Grid line every 25 characters
    ax.yaxis.grid(True, linestyle='-', alpha=0.2, linewidth=1.5, color='gray')
    ax.set_axisbelow(True)

    # Titles
    fig.suptitle('Sentence Length Distribution by HSK Level',
                 fontsize=14, fontweight='bold', y=0.96)

    subtitle_text = 'Violin plots showing sentence complexity progression across HSK levels'
    ax.text(0.5, 1.04, subtitle_text, transform=ax.transAxes,
            ha='center', fontsize=9, style='italic', color='#666666')

    # Add legend (moved to upper left) - only showing median since mean/median are nearly identical
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', linewidth=2.5, label='Median (mean is nearly identical)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.9)

    # Add statistics annotation (moved to left side)
    stats_text = 'Mean sentence lengths:\n'
    for level in levels_present:
        if level in stats:
            stats_text += f'HSK {level}: {stats[level]["mean"]:.1f} chars\n'

    ax.text(0.02, 0.50, stats_text.strip(),
            transform=ax.transAxes, fontsize=9,
            verticalalignment='center', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Footer
    total_sentences = sum(len(lengths_by_hsk[l]) for l in levels_present)
    footer_text = f'Total: {total_sentences:,} sentences analyzed'
    ax.text(0.5, -0.12, footer_text, transform=ax.transAxes,
            ha='center', fontsize=10, style='italic', color='#666666')

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')

    print(f"✓ Saved sentence length distribution chart to {output_file}")
    plt.close()


if __name__ == '__main__':
    # Load sentences
    sentences = load_sentences()

    # Analyze lengths
    lengths_by_hsk, stats = analyze_sentence_lengths(sentences)

    # Generate visualization
    plot_sentence_length_distribution(lengths_by_hsk, stats)

    print("\n✓ Sentence length analysis complete!")
