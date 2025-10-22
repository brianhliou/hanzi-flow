#!/usr/bin/env python3
"""
Generate character coverage curve visualization.

Shows the relationship between number of characters learned and percentage
of corpus text covered. Demonstrates the power law of Chinese character
frequency - learning the most common 1000 characters provides ~90% coverage.

Inputs:
- chinese_characters.csv (with freq column)

Outputs:
- character_coverage_curve.png
"""
import csv
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def load_character_data(csv_path='../../data/chinese_characters_with_freq.csv'):
    """Load character frequency data (includes freq column)."""
    print(f"Loading character data from {csv_path}...")

    characters = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq = int(row.get('freq', 0))
            if freq > 0:  # Only include characters that appear in corpus
                characters.append({
                    'char': row['char'],
                    'freq': freq,
                    'hsk_level': row.get('hsk_level', '').strip()
                })

    # Sort by frequency (descending)
    characters.sort(key=lambda x: x['freq'], reverse=True)

    print(f"✓ Loaded {len(characters):,} characters with frequency > 0")

    return characters


def calculate_coverage_curve(characters):
    """Calculate cumulative coverage percentage for each character rank."""
    total_occurrences = sum(c['freq'] for c in characters)

    cumulative_freq = 0
    coverage_curve = []

    for i, char in enumerate(characters, 1):
        cumulative_freq += char['freq']
        coverage_pct = (cumulative_freq / total_occurrences) * 100
        coverage_curve.append({
            'rank': i,
            'char': char['char'],
            'coverage': coverage_pct,
            'hsk_level': char['hsk_level']
        })

    return coverage_curve, total_occurrences


def get_hsk_boundaries():
    """Return official HSK 3.0 cumulative character counts."""
    # Official HSK 3.0 specification (cumulative counts)
    boundaries = {
        '1': 300,
        '2': 600,
        '3': 900,
        '4': 1200,
        '5': 1500,
        '6': 1800,
        '7-9': 3000
    }
    return boundaries


def plot_coverage_curve(coverage_curve, hsk_boundaries, total_occurrences,
                        output_file='../../data/character_set/character_coverage_curve.png'):
    """Generate the coverage curve visualization."""
    print(f"\nGenerating coverage curve chart...")

    # Extract data for plotting
    ranks = [p['rank'] for p in coverage_curve]
    coverages = [p['coverage'] for p in coverage_curve]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot main curve
    ax.plot(ranks, coverages, linewidth=3, color='#3b82f6', label='Coverage curve')

    # Highlight the "sweet spot" region (80-95% coverage) - optimal learning efficiency
    ax.axhspan(80, 95, alpha=0.1, color='green', label='Optimal learning efficiency (80-95% coverage)')

    # Add milestone markers
    milestones = [
        (500, '500 chars', 10, -40),    # Move down for cleaner layout
        (1000, '1000 chars', 10, -40),  # Move down for cleaner layout
        (2000, '2000 chars', 10, -40),  # Move down to avoid overlap
        (3000, '3000 chars', 10, -40)   # Move down to avoid overlap
    ]

    for rank, label, offset_x, offset_y in milestones:
        if rank <= len(coverage_curve):
            coverage_at_rank = coverage_curve[rank - 1]['coverage']
            ax.axvline(x=rank, color='#ef4444', linestyle='--', alpha=0.5, linewidth=1.5)
            ax.plot(rank, coverage_at_rank, 'o', color='#ef4444', markersize=10, zorder=5)
            ax.annotate(f'{label}\n{coverage_at_rank:.1f}% coverage',
                       xy=(rank, coverage_at_rank),
                       xytext=(offset_x, offset_y), textcoords='offset points',
                       fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

    # Add HSK level boundaries as vertical lines
    hsk_colors = {
        '1': '#1e40af',
        '2': '#3b82f6',
        '3': '#60a5fa',
        '4': '#dc2626',  # Make 4-6 more visible with red
        '5': '#dc2626',
        '6': '#dc2626',
        '7-9': '#8b5cf6'
    }

    for level, rank in hsk_boundaries.items():
        if level in hsk_colors:
            ax.axvline(x=rank, color=hsk_colors[level], linestyle=':', alpha=0.6, linewidth=2)
            # Add small label at top (all aligned at same height)
            if rank <= max(ranks):
                coverage_at_rank = coverage_curve[rank - 1]['coverage']
                ax.text(rank, 102, f'HSK {level}',
                       rotation=0, fontsize=8, ha='center', color=hsk_colors[level],
                       fontweight='bold')

    # Customize axes
    ax.set_xlabel('Number of Characters Learned (ranked by frequency)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Percentage of Corpus Covered (%)', fontsize=13, fontweight='bold')
    ax.set_title('Character Learning Coverage Curve\nShows % of characters you can read in the corpus by learning the top N most frequent characters',
                 fontsize=14, fontweight='bold', pad=20)

    # Set axis limits
    ax.set_xlim(0, min(5000, max(ranks)))
    ax.set_ylim(0, 105)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)

    # Add legend
    ax.legend(loc='lower right', fontsize=11, framealpha=0.9)

    # Add annotation box with key insights (moved to right side)
    insight_text = 'Key Insights:\n'
    insight_text += f'• Top 500 characters: {coverage_curve[499]["coverage"]:.1f}% coverage\n'
    insight_text += f'• Top 1000 characters: {coverage_curve[999]["coverage"]:.1f}% coverage\n'
    insight_text += f'• Top 2000 characters: {coverage_curve[1999]["coverage"]:.1f}% coverage\n'
    insight_text += f'• Diminishing returns beyond 2000 chars'

    ax.text(0.98, 0.50, insight_text,
            transform=ax.transAxes, fontsize=10,
            verticalalignment='center', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')

    print(f"✓ Saved coverage curve to {output_file}")
    plt.close()


def print_statistics(coverage_curve):
    """Print key statistics about the coverage curve."""
    print(f"\n{'='*60}")
    print("COVERAGE STATISTICS")
    print(f"{'='*60}\n")

    milestones = [100, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000]

    print("Coverage by character count:")
    for milestone in milestones:
        if milestone <= len(coverage_curve):
            coverage = coverage_curve[milestone - 1]['coverage']
            print(f"  {milestone:5,} characters: {coverage:6.2f}% coverage")

    # Find characters needed for specific coverage thresholds
    print("\nCharacters needed for coverage thresholds:")
    thresholds = [50, 70, 80, 90, 95, 99]

    for threshold in thresholds:
        for point in coverage_curve:
            if point['coverage'] >= threshold:
                print(f"  {threshold:2}% coverage: {point['rank']:5,} characters")
                break

    print(f"\n{'='*60}")


if __name__ == '__main__':
    # Load character data
    characters = load_character_data()

    # Calculate coverage curve
    coverage_curve, total_occurrences = calculate_coverage_curve(characters)

    # Get HSK boundaries (official counts)
    hsk_boundaries = get_hsk_boundaries()

    # Print statistics
    print_statistics(coverage_curve)

    # Generate visualization
    plot_coverage_curve(coverage_curve, hsk_boundaries, total_occurrences)

    print("\n✓ Coverage curve analysis complete!")
