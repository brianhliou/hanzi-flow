#!/usr/bin/env python3
"""
Check for duplicate syllables in the Trie (same syllable, different format).

For example: "lè" (tone mark) vs "le4" (tone number) are the same syllable.
"""
import json
import re


# Tone mark to tone number mapping
TONE_MARK_TO_NUMBER = {
    'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
    'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
    'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
    'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
    'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
    'ǖ': ('v', 1), 'ǘ': ('v', 2), 'ǚ': ('v', 3), 'ǜ': ('v', 4),
}


def normalize_to_tone3(pinyin):
    """
    Normalize any pinyin format to tone3 (tone number at end).

    Examples:
        'lè' -> 'le4'
        'le4' -> 'le4'
        'de' -> 'de0'
    """
    # Check if already in tone3 format (ends with digit)
    if re.search(r'\d$', pinyin):
        return pinyin

    # Convert tone marks to tone3
    tone = 0
    result = []

    for char in pinyin:
        if char in TONE_MARK_TO_NUMBER:
            base_vowel, tone = TONE_MARK_TO_NUMBER[char]
            result.append(base_vowel)
        else:
            result.append(char)

    # If no tone found, assume neutral (tone 0)
    return ''.join(result) + str(tone)


def collect_syllables_with_metadata(node, prefix=''):
    """Collect syllables with their character count."""
    syllables = []
    if node.get('is_end'):
        syllables.append((prefix, node['count']))
    for letter, child in node.get('children', {}).items():
        syllables.extend(collect_syllables_with_metadata(child, prefix + letter))
    return syllables


def analyze_duplicates():
    """Find and analyze duplicate syllables."""
    print("=" * 70)
    print("Check for Duplicate Syllables (Mixed Format Issue)")
    print("=" * 70)

    # Load trie
    with open('../../../data/character_set/analysis/pinyin_trie.json') as f:
        trie = json.load(f)

    syllables = collect_syllables_with_metadata(trie)

    # Normalize all to tone3 and group
    normalized_map = {}  # tone3 -> [(original, char_count), ...]

    for original, char_count in syllables:
        normalized = normalize_to_tone3(original)

        if normalized not in normalized_map:
            normalized_map[normalized] = []
        normalized_map[normalized].append((original, char_count))

    # Find duplicates (normalized syllables with multiple original forms)
    duplicates = {k: v for k, v in normalized_map.items() if len(v) > 1}

    print(f"\nTotal unique syllables (raw): {len(syllables):,}")
    print(f"Total unique syllables (normalized to tone3): {len(normalized_map):,}")
    print(f"Duplicate syllables (same pronunciation, different format): {len(duplicates):,}")

    if duplicates:
        print(f"\n{'='*70}")
        print(f"DUPLICATES FOUND ({len(duplicates):,} syllables)")
        print(f"{'='*70}\n")

        # Sort by total character count (to show most impactful duplicates)
        sorted_dups = sorted(
            duplicates.items(),
            key=lambda x: sum(c for _, c in x[1]),
            reverse=True
        )

        print(f"Top 30 duplicates (by total character count):\n")
        for i, (normalized, variants) in enumerate(sorted_dups[:30], 1):
            total_chars = sum(c for _, c in variants)
            print(f"{i:2d}. {normalized:10s} ({total_chars:3d} chars total)")
            for original, char_count in variants:
                print(f"     '{original}' - {char_count} chars")
            print()

        # Statistics
        total_duplicate_chars = sum(
            sum(c for _, c in variants)
            for variants in duplicates.values()
        )
        total_chars = sum(c for _, c in syllables)

        print(f"{'='*70}")
        print(f"Impact: {total_duplicate_chars:,} / {total_chars:,} character-syllable mappings")
        print(f"        ({total_duplicate_chars/total_chars*100:.1f}% affected by duplicates)")
        print(f"{'='*70}")

    else:
        print("\n✓ No duplicates found - all syllables are in consistent format")

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)

    return duplicates


if __name__ == '__main__':
    analyze_duplicates()
