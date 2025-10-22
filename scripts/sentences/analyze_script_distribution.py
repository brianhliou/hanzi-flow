#!/usr/bin/env python3
"""
Analyze and visualize script type distribution (Simplified vs Traditional vs Mixed).

Shows the composition of the sentence corpus by script type, demonstrating
the app's comprehensive multi-script support.

Inputs:
- sentences_with_translation.json

Outputs:
- script_distribution.png
- script_statistics.json
"""
import json
from collections import Counter
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def load_sentences(json_path='../../app/public/data/sentences/sentences_with_translation.json'):
    """Load sentence data from production JSON."""
    print(f"Loading sentences from {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sentences = data.get('sentences', [])
    print(f"✓ Loaded {len(sentences):,} sentences")

    return sentences


def analyze_script_distribution(sentences):
    """Analyze script type distribution."""
    print("\nAnalyzing script types...")

    script_counts = Counter()
    char_counts_by_script = {}

    for sentence in sentences:
        script_type = sentence.get('script_type', 'unknown')
        script_counts[script_type] += 1

        # Also count total characters by script type
        chinese_chars = sentence.get('sentence', '')
        if script_type not in char_counts_by_script:
            char_counts_by_script[script_type] = 0
        # Count only Chinese characters
        char_counts_by_script[script_type] += sum(1 for c in chinese_chars if '\u4e00' <= c <= '\u9fff')

    return script_counts, char_counts_by_script


def print_statistics(script_counts, char_counts_by_script, total_sentences):
    """Print detailed statistics."""
    print(f"\n{'='*60}")
    print("SCRIPT TYPE DISTRIBUTION")
    print(f"{'='*60}\n")

    print("By sentence count:")
    for script_type in ['simplified', 'traditional', 'neutral', 'ambiguous', 'unknown']:
        count = script_counts.get(script_type, 0)
        pct = (count / total_sentences * 100) if total_sentences > 0 else 0
        label = script_type.capitalize()
        print(f"  {label:12s}: {count:6,} sentences ({pct:5.1f}%)")

    print(f"\n  {'Total':12s}: {total_sentences:6,} sentences")

    total_chars = sum(char_counts_by_script.values())
    print(f"\nBy character count:")
    for script_type in ['simplified', 'traditional', 'neutral', 'ambiguous', 'unknown']:
        char_count = char_counts_by_script.get(script_type, 0)
        pct = (char_count / total_chars * 100) if total_chars > 0 else 0
        label = script_type.capitalize()
        print(f"  {label:12s}: {char_count:8,} characters ({pct:5.1f}%)")

    print(f"\n  {'Total':12s}: {total_chars:8,} characters")
    print(f"\n{'='*60}")


def plot_script_distribution(script_counts, total_sentences,
                            output_file='../../data/sentences/script_distribution.png'):
    """Generate script distribution visualization."""
    print(f"\nGenerating script distribution chart...")

    # Prepare data - only include categories with data
    all_script_types = ['simplified', 'traditional', 'neutral', 'ambiguous']
    script_types = []
    counts = []
    for st in all_script_types:
        count = script_counts.get(st, 0)
        if count > 0:
            script_types.append(st)
            counts.append(count)

    percentages = [(count / total_sentences * 100) for count in counts]

    # Create figure with single plot (bar chart only)
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 7))

    # Add main title (closer to subtitle)
    fig.suptitle('Script Type Distribution in Sentence Corpus',
                 fontsize=14, fontweight='bold', y=0.94)

    # Plot 1: Bar chart
    # Define colors and English labels (avoid Chinese characters to prevent font issues)
    color_map = {
        'simplified': '#3b82f6',
        'traditional': '#f59e0b',
        'neutral': '#10b981',
        'ambiguous': '#8b5cf6'
    }
    label_map = {
        'simplified': 'Simplified',
        'traditional': 'Traditional',
        'neutral': 'Neutral',
        'ambiguous': 'Ambiguous'
    }

    colors = [color_map[st] for st in script_types]
    labels = [label_map[st] for st in script_types]

    bars = ax1.bar(labels, counts, color=colors, edgecolor='white', linewidth=2)

    ax1.set_ylabel('Number of Sentences', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Script Type', fontsize=13, fontweight='bold')
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_axisbelow(True)

    # Add value labels
    for bar, count, pct in zip(bars, counts, percentages):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Format y-axis and set limit with headroom for labels
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax1.set_ylim(0, 40000)  # Fixed upper limit to ensure labels don't clip

    # Add note about script classification (below title, above chart)
    note_text = 'Simplified/Traditional includes sentences with neutral characters. '
    note_text += 'Neutral = sentences with only shared characters.'
    ax1.text(0.5, 1.02, note_text, transform=ax1.transAxes,
             ha='center', fontsize=9, style='italic', color='#666666')

    # Add subtitle with total (below chart, more space from x-axis label)
    ax1.text(0.5, -0.15, f'Total: {total_sentences:,} sentences across all script types',
             transform=ax1.transAxes, ha='center', fontsize=10, style='italic', color='#666666')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Leave room for title and subtitle
    plt.savefig(output_file, dpi=150, bbox_inches='tight')

    print(f"✓ Saved script distribution chart to {output_file}")
    plt.close()


def save_statistics(script_counts, char_counts_by_script, total_sentences,
                   output_json='../../data/sentences/script_statistics.json'):
    """Save statistics to JSON file."""
    stats = {
        'total_sentences': total_sentences,
        'by_sentence_count': {},
        'by_character_count': {}
    }

    # Sentence counts
    for script_type, count in script_counts.items():
        stats['by_sentence_count'][script_type] = {
            'count': count,
            'percentage': round((count / total_sentences * 100), 2)
        }

    # Character counts
    total_chars = sum(char_counts_by_script.values())
    for script_type, count in char_counts_by_script.items():
        stats['by_character_count'][script_type] = {
            'count': count,
            'percentage': round((count / total_chars * 100), 2) if total_chars > 0 else 0
        }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved statistics to {output_json}")


if __name__ == '__main__':
    # Load sentences
    sentences = load_sentences()

    total_sentences = len(sentences)

    # Analyze script distribution
    script_counts, char_counts_by_script = analyze_script_distribution(sentences)

    # Print statistics
    print_statistics(script_counts, char_counts_by_script, total_sentences)

    # Generate visualization
    plot_script_distribution(script_counts, total_sentences)

    # Save statistics
    save_statistics(script_counts, char_counts_by_script, total_sentences)

    print("\n✓ Script distribution analysis complete!")
