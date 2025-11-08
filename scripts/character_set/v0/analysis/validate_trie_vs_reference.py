#!/usr/bin/env python3
"""
Validate Pinyin Trie against reference syllables_enumeration.json.

Both sources use tone3 format (tone numbers), no conversion needed.
"""
import json


def collect_syllables(node, prefix=''):
    """Recursively collect all terminal syllables from Trie."""
    syllables = []
    if node.get('is_end'):
        syllables.append(prefix)
    for letter, child in node.get('children', {}).items():
        syllables.extend(collect_syllables(child, prefix + letter))
    return syllables


def load_reference_syllables(ref_path='../../../data/audio/syllables_enumeration.json'):
    """Load reference syllables in tone3 format."""
    with open(ref_path) as f:
        data = json.load(f)

    syllables = set()
    for entry in data['syllables']:
        syllables.add(entry['pinyin_tone3'])

    return syllables, data['metadata']


def load_trie_syllables(trie_path='../../../data/character_set/analysis/pinyin_trie.json'):
    """Load syllables from our Trie (already in tone3 format)."""
    with open(trie_path) as f:
        trie = json.load(f)

    syllables_list = collect_syllables(trie)

    # Return as set for comparison
    return set(syllables_list)


if __name__ == '__main__':
    print("=" * 70)
    print("Validate Pinyin Trie vs Reference Syllables")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    trie_syllables = load_trie_syllables()
    ref_syllables, ref_metadata = load_reference_syllables()

    print(f"✓ Trie: {len(trie_syllables):,} syllables (tone3 format)")
    print(f"✓ Reference: {len(ref_syllables):,} syllables (tone3 format)")
    print(f"\nReference metadata:")
    for key, value in ref_metadata.items():
        print(f"  {key}: {value}")

    # Compare
    in_trie_not_ref = trie_syllables - ref_syllables
    in_ref_not_trie = ref_syllables - trie_syllables
    overlap = trie_syllables & ref_syllables

    print(f"\n{'='*70}")
    print("COMPARISON")
    print(f"{'='*70}\n")

    print(f"Overlap: {len(overlap):,} syllables ({len(overlap)/len(ref_syllables)*100:.1f}% of reference)")
    print(f"In Trie but NOT in reference: {len(in_trie_not_ref):,}")
    print(f"In reference but NOT in Trie: {len(in_ref_not_trie):,}")

    # Show examples
    if in_trie_not_ref:
        print(f"\n{'='*70}")
        print(f"IN TRIE BUT NOT IN REFERENCE ({len(in_trie_not_ref):,} syllables)")
        print(f"{'='*70}")
        print("(These syllables are in our corpus but not in Unihan reference)")

        sorted_diff = sorted(list(in_trie_not_ref))
        print(f"\nFirst 50 examples:")
        for i in range(0, min(50, len(sorted_diff)), 5):
            line = sorted_diff[i:i+5]
            print(f"  {', '.join(line)}")

    if in_ref_not_trie:
        print(f"\n{'='*70}")
        print(f"IN REFERENCE BUT NOT IN TRIE ({len(in_ref_not_trie):,} syllables)")
        print(f"{'='*70}")
        print("(These syllables exist in standard Mandarin but not in our corpus)")

        sorted_missing = sorted(list(in_ref_not_trie))
        print(f"\nFirst 50 examples:")
        for i in range(0, min(50, len(sorted_missing)), 5):
            line = sorted_missing[i:i+5]
            print(f"  {', '.join(line)}")

    print(f"\n{'='*70}")
    print("✓ Validation complete!")
    print(f"{'='*70}")
