#!/usr/bin/env python3
"""
Export syllables gained in v1 (not present in v0) to a file for inspection.
"""
import json
from pathlib import Path


def load_trie(trie_path):
    """Load trie from JSON file."""
    with open(trie_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def collect_syllables(node, prefix=""):
    """Recursively collect all terminal syllables from Trie."""
    syllables = {}

    if node.get("is_end"):
        syllables[prefix] = node.get("characters", [])

    for letter, child in node.get("children", {}).items():
        syllables.update(collect_syllables(child, prefix + letter))

    return syllables


def main():
    print("Exporting gained syllables (v1 - v0)...")

    # Load both tries
    v0_path = Path('../../../../data/character_set/v0/analysis/pinyin_trie.json')
    v1_path = Path('../../../../data/character_set/v1/analysis/pinyin_trie.json')

    v0_trie = load_trie(v0_path)
    v1_trie = load_trie(v1_path)

    # Collect syllables
    v0_syllables = collect_syllables(v0_trie)
    v1_syllables = collect_syllables(v1_trie)

    v0_set = set(v0_syllables.keys())
    v1_set = set(v1_syllables.keys())

    # Find gained syllables
    gained = v1_set - v0_set
    gained_sorted = sorted(gained)

    # Write to file
    output_path = Path('../../../../data/character_set/v1/analysis/gained_syllables.txt')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SYLLABLES GAINED IN V1 (NOT PRESENT IN V0)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total gained: {len(gained):,} syllables\n")
        f.write(f"v0 syllables: {len(v0_set):,}\n")
        f.write(f"v1 syllables: {len(v1_set):,}\n")
        f.write(f"Expansion: {len(v1_set)/len(v0_set):.2f}x\n\n")

        f.write("=" * 80 + "\n")
        f.write("ALL GAINED SYLLABLES (alphabetically sorted)\n")
        f.write("=" * 80 + "\n\n")

        # Write in columns of 10 for readability
        for i in range(0, len(gained_sorted), 10):
            row = gained_sorted[i:i+10]
            f.write("  " + ", ".join(f"{s:<8}" for s in row) + "\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED BREAKDOWN WITH CHARACTER EXAMPLES\n")
        f.write("=" * 80 + "\n\n")

        for syllable in gained_sorted:
            chars = v1_syllables[syllable]
            if isinstance(chars, list):
                char_count = len(chars)
                # Show first 10 characters as examples
                examples = chars[:10]
                example_str = ' '.join(examples)
                if char_count > 10:
                    example_str += f" ... (+{char_count - 10} more)"
            else:
                char_count = 0
                example_str = "(no characters)"

            f.write(f"{syllable:<10} - {char_count:4d} chars: {example_str}\n")

    print(f"✓ Exported {len(gained):,} gained syllables to:")
    print(f"  {output_path}")
    print(f"\nSummary:")
    print(f"  v0: {len(v0_set):,} syllables")
    print(f"  v1: {len(v1_set):,} syllables")
    print(f"  Gained: {len(gained):,} syllables")


if __name__ == '__main__':
    main()
