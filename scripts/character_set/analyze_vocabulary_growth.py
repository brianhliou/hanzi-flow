#!/usr/bin/env python3
"""
Generate vocabulary growth visualization by HSK level.

Uses official HSK 3.0 character counts (fixed numbers, not analyzed from data).

Outputs:
- vocabulary_growth_by_hsk.png
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def get_official_hsk_counts():
    """Return official HSK 3.0 character counts."""
    print("Using official HSK 3.0 character counts...")

    # Official HSK 3.0 specification
    growth_data = [
        {'level': '1', 'new_chars': 300, 'cumulative': 300},
        {'level': '2', 'new_chars': 300, 'cumulative': 600},
        {'level': '3', 'new_chars': 300, 'cumulative': 900},
        {'level': '4', 'new_chars': 300, 'cumulative': 1200},
        {'level': '5', 'new_chars': 300, 'cumulative': 1500},
        {'level': '6', 'new_chars': 300, 'cumulative': 1800},
        {'level': '7-9', 'new_chars': 1200, 'cumulative': 3000},
        {'level': 'Beyond HSK', 'new_chars': 1000, 'cumulative': 4000},
    ]

    for item in growth_data:
        print(f"  HSK {item['level']:10s}: {item['new_chars']:4,} new chars, {item['cumulative']:5,} cumulative")

    return growth_data


def plot_vocabulary_growth(growth_data,
                          output_file='../../data/character_set/vocabulary_growth_by_hsk.png'):
    """Generate vocabulary growth visualization."""
    print(f"\nGenerating vocabulary growth chart...")

    levels = [d['level'] for d in growth_data]
    new_chars = [d['new_chars'] for d in growth_data]
    cumulative = [d['cumulative'] for d in growth_data]

    # Create figure with dual y-axis
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Color scheme matching other visualizations
    bar_colors = [
        '#1e40af',  # HSK 1 - dark blue
        '#3b82f6',  # HSK 2 - blue
        '#60a5fa',  # HSK 3 - light blue
        '#93c5fd',  # HSK 4 - lighter blue
        '#bfdbfe',  # HSK 5 - very light blue
        '#dbeafe',  # HSK 6 - pale blue
        '#8b5cf6',  # HSK 7-9 - purple
        '#f59e0b',  # beyond-hsk - orange
    ]

    # Plot 1: Stacked bar chart (new characters per level)
    x_pos = range(len(levels))
    bars = ax1.bar(x_pos, new_chars, color=bar_colors, edgecolor='white', linewidth=2, alpha=0.8)

    ax1.set_xlabel('HSK Level', fontsize=13, fontweight='bold')
    ax1.set_ylabel('New Characters Introduced', fontsize=13, fontweight='bold', color='#1e40af')
    ax1.tick_params(axis='y', labelcolor='#1e40af')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(levels)

    # Add value labels on bars
    for bar, count in zip(bars, new_chars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count):,}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Plot 2: Cumulative line (total vocabulary)
    ax2 = ax1.twinx()
    line = ax2.plot(x_pos, cumulative, color='#dc2626', linewidth=3, marker='o',
                    markersize=8, label='Cumulative Total', zorder=10)

    ax2.set_ylabel('Cumulative Character Count', fontsize=13, fontweight='bold', color='#dc2626')
    ax2.tick_params(axis='y', labelcolor='#dc2626')

    # Add cumulative value labels
    for i, (x, cum) in enumerate(zip(x_pos, cumulative)):
        # Position labels to the right of the line points
        ax2.text(x, cum + 100, f'{cum:,}',
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                color='#dc2626',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#dc2626', alpha=0.8))

    # Add grid
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_axisbelow(True)

    # Titles
    fig.suptitle('HSK 3.0 Vocabulary Growth',
                 fontsize=14, fontweight='bold', y=0.96)

    subtitle_text = 'Official HSK 3.0 character counts by level'
    ax1.text(0.5, 1.04, subtitle_text, transform=ax1.transAxes,
             ha='center', fontsize=9, style='italic', color='#666666')

    # Add legend
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, fc='#3b82f6', label='New Characters (bar)'),
        plt.Line2D([0], [0], color='#dc2626', linewidth=3, marker='o', label='Cumulative Total (line)')
    ]
    ax1.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.9)

    # Footer note
    total_chars = cumulative[-1]
    footer_text = f'Total: {total_chars:,} characters across all HSK levels'
    ax1.text(0.5, -0.12, footer_text, transform=ax1.transAxes,
             ha='center', fontsize=10, style='italic', color='#666666')

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')

    print(f"✓ Saved vocabulary growth chart to {output_file}")
    plt.close()


if __name__ == '__main__':
    # Get official HSK counts
    growth_data = get_official_hsk_counts()

    # Generate visualization
    plot_vocabulary_growth(growth_data)

    print("\n✓ Vocabulary growth visualization complete!")
