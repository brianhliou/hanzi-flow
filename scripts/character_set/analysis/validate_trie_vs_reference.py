#!/usr/bin/env python3
"""
Validate Pinyin Trie against reference syllables_enumeration.json.

Converts between tone mark format (ā, á) and tone number format (a1, a2).
"""
import json
import re


# Tone mark to tone number mapping
TONE_MARK_TO_NUMBER = {
    # First tone
    'ā': ('a', 1), 'ē': ('e', 1), 'ī': ('i', 1), 'ō': ('o', 1), 'ū': ('u', 1), 'ǖ': ('v', 1),
    # Second tone
    'á': ('a', 2), 'é': ('e', 2), 'í': ('i', 2), 'ó': ('o', 2), 'ú': ('u', 2), 'ǘ': ('v', 2),
    # Third tone
    'ǎ': ('a', 3), 'ě': ('e', 3), 'ǐ': ('i', 3), 'ǒ': ('o', 3), 'ǔ': ('u', 3), 'ǚ': ('v', 3),
    # Fourth tone
    'à': ('a', 4), 'è': ('e', 4), 'ì': ('i', 4), 'ò': ('o', 4), 'ù': ('u', 4), 'ǜ': ('v', 4),
}


def convert_tone_mark_to_tone3(pinyin):
    """
    Convert tone mark format to tone3 format.

    Examples:
        'ā' -> 'a1'
        'zhōng' -> 'zhong1'
        'de' -> 'de0' (neutral tone)
    """
    # Find tone-marked vowel
    tone = 0
    result = []

    for char in pinyin:
        if char in TONE_MARK_TO_NUMBER:
            base_vowel, tone = TONE_MARK_TO_NUMBER[char]
            result.append(base_vowel)
        else:
            result.append(char)

    # If no tone found, it's neutral tone (tone 0)
    return ''.join(result) + str(tone)


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

    # Trie syllables are already in tone3 format, no conversion needed
    tone3_syllables = {s: [s] for s in syllables_list}

    return tone3_syllables


if __name__ == '__main__':
    print("=" * 70)
    print("Validate Pinyin Trie vs Reference Syllables")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    trie_syllables = load_trie_syllables()
    ref_syllables, ref_metadata = load_reference_syllables()

    trie_set = set(trie_syllables.keys())

    print(f"✓ Trie: {len(trie_set):,} syllables (tone3 format)")
    print(f"✓ Reference: {len(ref_syllables):,} syllables (tone3 format)")
    print(f"\nReference metadata:")
    for key, value in ref_metadata.items():
        print(f"  {key}: {value}")

    # Compare
    in_trie_not_ref = trie_set - ref_syllables
    in_ref_not_trie = ref_syllables - trie_set
    overlap = trie_set & ref_syllables

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
        print("(These are likely from pypinyin enrichment)")

        sorted_diff = sorted(list(in_trie_not_ref))
        print(f"\nFirst 50 examples:")
        for i in range(0, min(50, len(sorted_diff)), 5):
            line = sorted_diff[i:i+5]
            print(f"  {', '.join(line)}")

        # Show which original tone mark syllables map to these
        print(f"\nExample mappings (tone3 -> tone mark):")
        for tone3 in sorted_diff[:10]:
            originals = trie_syllables[tone3]
            print(f"  {tone3:8s} <- {', '.join(originals)}")

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
