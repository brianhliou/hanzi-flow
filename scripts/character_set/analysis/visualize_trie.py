#!/usr/bin/env python3
"""
Visualize the Pinyin Trie as a tree diagram.

Generates a PNG showing the tree structure with:
- Each node labeled with its letter/digit
- Terminal nodes (complete syllables) highlighted
- Arrows connecting parent to child nodes

Output: pinyin_trie_visualization.png
"""
import json
import sys
from pathlib import Path

try:
    import graphviz
except ImportError:
    print("Error: graphviz library not installed")
    print("Install with: pip install graphviz")
    print("Also requires system graphviz: brew install graphviz (macOS) or apt-get install graphviz (Linux)")
    sys.exit(1)


def add_trie_nodes(dot, node, parent_id=None, prefix="", node_id_counter=[0]):
    """
    Recursively add nodes and edges to the graph.

    Args:
        dot: graphviz.Digraph object
        node: Current trie node
        parent_id: ID of parent node (for edge creation)
        prefix: Current syllable prefix (for display)
        node_id_counter: Mutable list holding counter for unique node IDs
    """
    # Generate unique ID for this node
    node_id_counter[0] += 1
    current_id = f"node_{node_id_counter[0]}"

    # Get the letter for this node (last char of prefix)
    if prefix:
        letter = prefix[-1]
    else:
        letter = "ROOT"

    # Create tooltip showing the syllable built so far
    if prefix:
        tooltip = f"{prefix}"
        if node.get('is_end'):
            char_count = node.get('count', 0)
            char_word = "char" if char_count == 1 else "chars"
            tooltip += f" ({char_count} {char_word})"
    else:
        tooltip = "Root node"

    # Determine node styling
    if node.get('is_end'):
        # Terminal node - this is a complete syllable
        # Make it larger and colored
        dot.node(
            current_id,
            letter,
            shape='circle',
            style='filled',
            fillcolor='lightblue',
            fontsize='14',
            width='0.5',
            tooltip=tooltip
        )
    else:
        # Intermediate node
        dot.node(
            current_id,
            letter,
            shape='circle',
            fontsize='12',
            width='0.4',
            tooltip=tooltip
        )

    # Add edge from parent to this node
    if parent_id:
        dot.edge(parent_id, current_id)

    # Recursively add children
    for letter, child in sorted(node.get('children', {}).items()):
        add_trie_nodes(dot, child, current_id, prefix + letter, node_id_counter)


def visualize_trie(trie_path='../../../data/character_set/analysis/pinyin_trie.json',
                  output_path='../../../data/character_set/analysis/pinyin_trie_visualization',
                  format='png',
                  compact=False):
    """
    Create a visualization of the Trie structure.

    Args:
        trie_path: Path to pinyin_trie.json
        output_path: Output path (without extension)
        format: Output format ('png' or 'svg')
        compact: Use compact spacing to reduce size
    """
    print("=" * 70)
    print(f"Pinyin Trie Visualization ({format.upper()})")
    print("=" * 70)

    # Load Trie
    print(f"\nLoading Trie from {trie_path}...")
    with open(trie_path, 'r', encoding='utf-8') as f:
        trie = json.load(f)

    # Create directed graph
    print("Creating graph...")
    dot = graphviz.Digraph(
        comment='Pinyin Trie Structure',
        format=format
    )

    # Configure graph layout
    # LR = left to right layout (horizontal tree)
    # TB = top to bottom layout (vertical tree)
    dot.attr(rankdir='LR')  # Horizontal layout
    dot.attr('node', shape='circle')

    if format == 'png':
        dot.attr(dpi='150')  # Higher resolution for PNG

    # Add graph styling
    if compact:
        # Compact spacing for full tree
        dot.attr('graph',
                 bgcolor='white',
                 pad='0.3',
                 nodesep='0.15',
                 ranksep='0.5')  # Increased from 0.3 for better horizontal spacing
        dot.attr('node', width='0.3', fontsize='12')  # Increased from 10
    else:
        # Normal spacing
        dot.attr('graph',
                 bgcolor='white',
                 pad='0.5',
                 nodesep='0.3',
                 ranksep='0.7')  # Increased from 0.5
        dot.attr('node', width='0.4', fontsize='14')  # Increased from 12

    # Build the graph
    print("Building graph structure...")
    print("  - Blue circles: Complete syllables (terminal nodes)")
    print("  - White circles: Partial syllables (intermediate nodes)")

    add_trie_nodes(dot, trie)

    # Save to file
    print(f"\nRendering to {output_path}.{format}...")
    print("  (This may take a minute for large trees...)")

    try:
        dot.render(output_path, cleanup=True)
        print(f"✓ Visualization saved to {output_path}.{format}")
    except Exception as e:
        print(f"Error rendering graph: {e}")
        print("\nTip: Make sure system graphviz is installed:")
        print("  macOS: brew install graphviz")
        print("  Linux: sudo apt-get install graphviz")
        return False

    # Print file size
    output_file = Path(f"{output_path}.{format}")
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\nFile size: {size_mb:.2f} MB")

    print("\n" + "=" * 70)
    print("✓ Visualization complete!")
    print("=" * 70)

    return True


def visualize_trie_subtree(trie_path, output_path, max_depth=3, format='svg'):
    """
    Create a visualization of just the first few levels of the Trie.
    Useful for getting an overview without overwhelming detail.

    Args:
        trie_path: Path to pinyin_trie.json
        output_path: Output path (without extension)
        max_depth: Maximum depth to visualize
        format: Output format ('png' or 'svg')
    """
    print("=" * 70)
    print(f"Pinyin Trie Visualization (first {max_depth} levels only, {format.upper()})")
    print("=" * 70)

    # Load Trie
    print(f"\nLoading Trie from {trie_path}...")
    with open(trie_path, 'r', encoding='utf-8') as f:
        trie = json.load(f)

    # Create directed graph
    print("Creating graph...")
    dot = graphviz.Digraph(
        comment='Pinyin Trie Structure (Partial)',
        format=format
    )

    dot.attr(rankdir='LR')
    dot.attr('node', shape='circle', fontsize='14')

    if format == 'png':
        dot.attr(dpi='150')

    dot.attr('graph', bgcolor='white', pad='0.5', nodesep='0.3', ranksep='0.7')

    # Build graph with depth limit
    def add_nodes_with_depth(dot, node, parent_id=None, prefix="", depth=0, node_counter=[0]):
        if depth > max_depth:
            return

        node_counter[0] += 1
        current_id = f"node_{node_counter[0]}"
        letter = prefix[-1] if prefix else "ROOT"

        # Create tooltip showing the syllable built so far
        if prefix:
            tooltip = f"{prefix}"
            if node.get('is_end'):
                char_count = node.get('count', 0)
                char_word = "char" if char_count == 1 else "chars"
                tooltip += f" ({char_count} {char_word})"
        else:
            tooltip = "Root node"

        # Style nodes
        if node.get('is_end'):
            dot.node(current_id, letter, style='filled', fillcolor='lightblue', tooltip=tooltip)
        else:
            dot.node(current_id, letter, tooltip=tooltip)

        if parent_id:
            dot.edge(parent_id, current_id)

        # Add children up to max depth
        if depth < max_depth:
            for letter, child in sorted(node.get('children', {}).items()):
                add_nodes_with_depth(dot, child, current_id, prefix + letter, depth + 1, node_counter)
        elif node.get('children'):
            # Add indicator that there are more children
            node_counter[0] += 1
            more_id = f"node_{node_counter[0]}"
            dot.node(more_id, "...", shape='none', fontsize='10')
            dot.edge(current_id, more_id, style='dotted')

    print(f"Building graph (depth limit: {max_depth})...")
    add_nodes_with_depth(dot, trie)

    # Render
    print(f"\nRendering to {output_path}.{format}...")
    try:
        dot.render(output_path, cleanup=True)
        print(f"✓ Visualization saved to {output_path}.{format}")

        output_file = Path(f"{output_path}.{format}")
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"\nFile size: {size_mb:.2f} MB")

        print("\n" + "=" * 70)
        print("✓ Partial visualization complete!")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def visualize_trie_branch(trie_path, output_path, focus_letter='h', format='svg'):
    """
    Create a visualization of a single branch of the Trie with full depth.
    Shows placeholder nodes for other branches at root level.

    Args:
        trie_path: Path to pinyin_trie.json
        output_path: Output path (without extension)
        focus_letter: Letter to focus on (default: 'h')
        format: Output format ('png' or 'svg')
    """
    print("=" * 70)
    print(f"Pinyin Trie Branch Visualization ('{focus_letter}' branch, {format.upper()})")
    print("=" * 70)

    # Load Trie
    print(f"\nLoading Trie from {trie_path}...")
    with open(trie_path, 'r', encoding='utf-8') as f:
        trie = json.load(f)

    # Create directed graph
    print(f"Creating focused graph for '{focus_letter}' branch...")
    dot = graphviz.Digraph(
        comment=f'Pinyin Trie - {focus_letter.upper()} Branch',
        format=format
    )

    # Configure graph layout
    dot.attr(rankdir='LR')  # Horizontal layout
    dot.attr('node', shape='circle')
    dot.attr('graph',
             bgcolor='white',
             pad='0.5',
             nodesep='0.3',
             ranksep='0.7')
    dot.attr('node', width='0.4', fontsize='14')

    if format == 'png':
        dot.attr(dpi='150')

    # Add root node
    root_id = "node_root"
    dot.node(root_id, "ROOT", tooltip="Root node")

    # Add placeholder for letters before focus_letter
    placeholder_before_id = "node_placeholder_before"
    dot.node(placeholder_before_id, "...",
             shape='plaintext',
             fontsize='20',
             tooltip="Other branches")
    dot.edge(root_id, placeholder_before_id, style='dashed')

    # Add the focused branch (recursively expand all children)
    if focus_letter in trie.get('children', {}):
        node_id_counter = [0]
        focused_node = trie['children'][focus_letter]
        add_trie_nodes(dot, focused_node, root_id, focus_letter, node_id_counter)
    else:
        print(f"Warning: Letter '{focus_letter}' not found in Trie")
        return False

    # Add placeholder for letters after focus_letter
    placeholder_after_id = "node_placeholder_after"
    dot.node(placeholder_after_id, "...",
             shape='plaintext',
             fontsize='20',
             tooltip="Other branches")
    dot.edge(root_id, placeholder_after_id, style='dashed')

    # Save to file
    print(f"\nRendering to {output_path}.{format}...")
    print("  - Blue circles: Complete syllables (terminal nodes)")
    print("  - White circles: Partial syllables (intermediate nodes)")
    print("  - Dashed lines: Other branches not shown")

    try:
        dot.render(output_path, cleanup=True)
        print(f"✓ Visualization saved to {output_path}.{format}")
    except Exception as e:
        print(f"Error rendering graph: {e}")
        return False

    # Print file size
    output_file = Path(f"{output_path}.{format}")
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        if size_mb < 1:
            size_kb = output_file.stat().st_size / 1024
            print(f"\nFile size: {size_kb:.1f} KB")
        else:
            print(f"\nFile size: {size_mb:.2f} MB")

    print("\n" + "=" * 70)
    print("✓ Branch visualization complete!")
    print("=" * 70)

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Visualize Pinyin Trie structure')
    parser.add_argument(
        '--depth',
        type=int,
        help='Only visualize first N levels (useful for overview)'
    )
    parser.add_argument(
        '--branch',
        type=str,
        help='Focus on a single branch (e.g., --branch h)'
    )
    parser.add_argument(
        '--output',
        default='../../../data/character_set/analysis/pinyin_trie_visualization',
        help='Output path (without extension)'
    )
    parser.add_argument(
        '--format',
        choices=['png', 'svg'],
        default='svg',
        help='Output format (png or svg, default: svg)'
    )
    parser.add_argument(
        '--compact',
        action='store_true',
        help='Use compact spacing (recommended for full tree)'
    )

    args = parser.parse_args()

    trie_path = '../../../data/character_set/analysis/pinyin_trie.json'

    if args.branch:
        # Single branch visualization
        output = args.output.replace('_visualization', f'_visualization_{args.branch}_branch')
        visualize_trie_branch(trie_path, output, args.branch, format=args.format)
    elif args.depth:
        # Partial visualization
        output = args.output.replace('_visualization', f'_visualization_depth{args.depth}')
        visualize_trie_subtree(trie_path, output, args.depth, format=args.format)
    else:
        # Full visualization
        print("\nGenerating full Trie visualization...")
        print(f"Format: {args.format.upper()}")
        print(f"Compact spacing: {args.compact}")
        print()

        visualize_trie(trie_path, args.output, format=args.format, compact=args.compact)
