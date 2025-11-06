#!/usr/bin/env python3
"""
Build a character-level Trie of all Chinese pinyin syllables from the corpus.

Each node represents ONE letter in normalized tone3 format (tone numbers).
Terminal nodes store metadata about characters that produce that pinyin.

IMPORTANT: Normalizes all pinyin to tone3 format (e.g., yì -> yi4) to avoid duplicates.

Input:
- ../../data/character_set/step7_with_freq.csv (characters with freq > 0)

Output:
- ../../data/character_set/analysis/pinyin_trie.json
- Console statistics about syllable distribution

Note: Pinyin frequencies are from Unihan (data/sources), not sentence corpus frequency.
"""
import csv
import json
import re
from pathlib import Path
from collections import defaultdict


# Tone mark to base vowel + tone number mapping
TONE_MARK_TO_NUMBER = {
    'ā': ('a', '1'), 'á': ('a', '2'), 'ǎ': ('a', '3'), 'à': ('a', '4'),
    'ē': ('e', '1'), 'é': ('e', '2'), 'ě': ('e', '3'), 'è': ('e', '4'),
    'ī': ('i', '1'), 'í': ('i', '2'), 'ǐ': ('i', '3'), 'ì': ('i', '4'),
    'ō': ('o', '1'), 'ó': ('o', '2'), 'ǒ': ('o', '3'), 'ò': ('o', '4'),
    'ū': ('u', '1'), 'ú': ('u', '2'), 'ǔ': ('u', '3'), 'ù': ('u', '4'),
    'ǖ': ('v', '1'), 'ǘ': ('v', '2'), 'ǚ': ('v', '3'), 'ǜ': ('v', '4'),
}


def normalize_to_tone3(pinyin):
    """
    Normalize pinyin to tone3 format (tone numbers at end).

    Examples:
        'yì' -> 'yi4'
        'yi4' -> 'yi4' (already normalized)
        'de' -> 'de0' (neutral tone)
        'lè(283)' -> 'le4(283)' (preserves frequency)

    Returns: normalized pinyin string
    """
    # Extract frequency if present
    freq_match = re.match(r'^(.+?)(\(\d+\))$', pinyin)
    if freq_match:
        base = freq_match.group(1)
        freq_suffix = freq_match.group(2)
    else:
        base = pinyin
        freq_suffix = ''

    # Check if already in tone3 format (ends with digit)
    if re.search(r'\d$', base):
        return pinyin  # Already normalized

    # Convert tone marks to tone3
    tone = '0'  # Default neutral tone
    result = []

    for char in base:
        if char in TONE_MARK_TO_NUMBER:
            base_vowel, tone_num = TONE_MARK_TO_NUMBER[char]
            result.append(base_vowel)
            tone = tone_num
        else:
            result.append(char)

    return ''.join(result) + tone + freq_suffix


def parse_pinyin_field(pinyins_str):
    """
    Parse the pinyins field to extract individual pinyin syllables.
    NORMALIZES all pinyin to tone3 format to avoid duplicates.

    Format: "lè(283)|yuè(54)" or "de" (neutral tone, no frequency)
    Returns: list of (normalized_pinyin, frequency) tuples
    """
    if not pinyins_str or pinyins_str.strip() == '':
        return []

    result = []
    for part in pinyins_str.split('|'):
        part = part.strip()
        if not part:
            continue

        # Normalize to tone3 format FIRST (handles frequency preservation)
        normalized = normalize_to_tone3(part)

        # Extract frequency from normalized pinyin
        match = re.match(r'^([^(]+)\((\d+)\)$', normalized)
        if match:
            pinyin = match.group(1)
            freq = int(match.group(2))
            result.append((pinyin, freq))
        else:
            # No frequency data (neutral tone or enriched pypinyin alternatives)
            result.append((normalized, 0))

    return result


def build_trie(characters_data):
    """
    Build character-level Trie from character data.
    Syllables are normalized to tone3 format, so duplicates are merged.

    Each node structure:
    {
      "children": {letter: node},
      "is_end": bool,
      "characters": [{"char": str, "unihan_freq": int, "corpus_freq": int}, ...],  # Only at terminal nodes
      "count": int,  # Only at terminal nodes (number of unique characters)
      "total_freq": int  # Only at terminal nodes (sum of Unihan frequencies)
    }

    Args:
        characters_data: List of dicts with 'char', 'pinyins', 'freq' fields

    Returns:
        Dict representing the root of the Trie
    """
    root = {"children": {}, "is_end": False}

    # syllable (normalized) -> {char: (unihan_freq, corpus_freq)}
    # Use dict to deduplicate characters per syllable
    syllable_chars = defaultdict(dict)

    for row in characters_data:
        char = row['char']
        pinyins_str = row.get('pinyins', '')
        corpus_freq = int(row.get('freq', 0))

        # Skip characters not in corpus
        if corpus_freq == 0:
            continue

        # Parse pinyin field (already normalized to tone3)
        pinyin_list = parse_pinyin_field(pinyins_str)

        # Add each normalized pinyin to collection
        for pinyin, unihan_freq in pinyin_list:
            # If character already exists for this syllable, keep the one with higher frequency
            if char in syllable_chars[pinyin]:
                existing_unihan, existing_corpus = syllable_chars[pinyin][char]
                # Keep the entry with higher Unihan frequency
                if unihan_freq > existing_unihan:
                    syllable_chars[pinyin][char] = (unihan_freq, corpus_freq)
            else:
                syllable_chars[pinyin][char] = (unihan_freq, corpus_freq)

    # Now build the trie from collected syllables
    for pinyin, chars_dict in syllable_chars.items():
        # Convert dict to list of character metadata
        chars_list = [
            {
                'char': char,
                'unihan_freq': unihan_freq,
                'corpus_freq': corpus_freq
            }
            for char, (unihan_freq, corpus_freq) in chars_dict.items()
        ]

        # Walk character by character through normalized pinyin
        node = root
        for letter in pinyin:
            if letter not in node["children"]:
                node["children"][letter] = {"children": {}, "is_end": False}
            node = node["children"][letter]

        # Mark as terminal and store metadata
        node["is_end"] = True
        node["characters"] = chars_list
        node["count"] = len(chars_list)
        node["total_freq"] = sum(c['unihan_freq'] for c in chars_list)

    return root


def collect_all_syllables(node, prefix=""):
    """
    Recursively collect all complete syllables from the Trie.

    Returns: list of (syllable, char_count, total_freq) tuples
    """
    syllables = []

    if node.get("is_end"):
        syllables.append((
            prefix,
            node["count"],
            node["total_freq"]
        ))

    for letter, child in node.get("children", {}).items():
        syllables.extend(collect_all_syllables(child, prefix + letter))

    return syllables


def generate_statistics(trie):
    """
    Generate statistics about the Trie.
    """
    print(f"\n{'='*70}")
    print("PINYIN TRIE STATISTICS (Normalized to Tone3 Format)")
    print(f"{'='*70}\n")

    # Collect all syllables
    syllables = collect_all_syllables(trie)
    syllables.sort(key=lambda x: x[2], reverse=True)  # Sort by total frequency

    print(f"Total unique pinyin syllables: {len(syllables):,}")

    # Character count distribution
    char_counts = [s[1] for s in syllables]
    print(f"\nCharacter count per syllable:")
    print(f"  Min: {min(char_counts)}")
    print(f"  Max: {max(char_counts)}")
    print(f"  Mean: {sum(char_counts) / len(char_counts):.1f}")
    print(f"  Median: {sorted(char_counts)[len(char_counts)//2]}")

    # Frequency distribution
    freqs = [s[2] for s in syllables]
    non_zero_freqs = [f for f in freqs if f > 0]
    zero_freq_count = len(freqs) - len(non_zero_freqs)

    print(f"\nFrequency data (from Unihan):")
    print(f"  Syllables with frequency > 0: {len(non_zero_freqs):,} ({len(non_zero_freqs)/len(syllables)*100:.1f}%)")
    print(f"  Syllables with frequency = 0: {zero_freq_count:,} ({zero_freq_count/len(syllables)*100:.1f}%)")

    if non_zero_freqs:
        print(f"  Min frequency (non-zero): {min(non_zero_freqs):,}")
        print(f"  Max frequency: {max(non_zero_freqs):,}")
        print(f"  Mean frequency (non-zero): {sum(non_zero_freqs)/len(non_zero_freqs):.1f}")

    # Top 20 most frequent syllables
    print(f"\nTop 20 most frequent syllables (by Unihan frequency):")
    for i, (syllable, char_count, total_freq) in enumerate(syllables[:20], 1):
        print(f"  {i:2d}. {syllable:8s} - {char_count:2d} chars, total freq: {total_freq:,}")

    # Syllables with most characters (polyphonic)
    syllables_by_chars = sorted(syllables, key=lambda x: x[1], reverse=True)
    print(f"\nTop 20 most polyphonic syllables (most characters):")
    for i, (syllable, char_count, total_freq) in enumerate(syllables_by_chars[:20], 1):
        print(f"  {i:2d}. {syllable:8s} - {char_count:2d} chars, total freq: {total_freq:,}")

    # Tone distribution analysis (tone3 format)
    tone_syllables = defaultdict(list)
    for syllable, char_count, total_freq in syllables:
        # Extract tone number from end
        tone_match = re.search(r'(\d)$', syllable)
        if tone_match:
            tone = tone_match.group(1)
            if tone == '0':
                tone_syllables['neutral'].append(syllable)
            else:
                tone_syllables[f'tone{tone}'].append(syllable)
        else:
            tone_syllables['unknown'].append(syllable)

    print(f"\nTone distribution (tone3 format):")
    for tone_key in ['tone1', 'tone2', 'tone3', 'tone4', 'neutral', 'unknown']:
        count = len(tone_syllables[tone_key])
        if count > 0:
            print(f"  {tone_key.capitalize():12s}: {count:,} syllables ({count/len(syllables)*100:.1f}%)")

    # Example neutral tone syllables
    if tone_syllables['neutral']:
        examples = ', '.join(tone_syllables['neutral'][:20])
        print(f"\n  Example neutral tone (first 20): {examples}")

    print(f"\n{'='*70}")

    return syllables


def save_trie_json(trie, output_path):
    """
    Save Trie to JSON file.
    """
    print(f"\nSaving Trie to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trie, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved Trie to {output_path}")


def load_character_data(csv_path='../../../data/character_set/step7_with_freq.csv'):
    """
    Load character data from CSV.
    Returns only characters with corpus frequency > 0.
    """
    print(f"Loading character data from {csv_path}...")

    characters = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq = int(row.get('freq', 0))
            if freq > 0:
                characters.append(row)

    print(f"✓ Loaded {len(characters):,} characters (corpus freq > 0)")

    return characters


if __name__ == '__main__':
    print("=" * 70)
    print("Build Pinyin Trie (Normalized to Tone3 Format)")
    print("=" * 70)
    print("\nNote: All pinyin normalized to tone3 (e.g., yì->yi4) to avoid duplicates")

    # Load character data
    characters = load_character_data()

    # Build Trie
    print("\nBuilding character-level Trie...")
    trie = build_trie(characters)
    print("✓ Trie construction complete")

    # Generate statistics
    syllables = generate_statistics(trie)

    # Save to JSON
    output_path = Path('../../../data/character_set/analysis/pinyin_trie.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_trie_json(trie, output_path)

    print("\n" + "=" * 70)
    print("✓ Pinyin Trie build complete!")
    print("=" * 70)
    print(f"\nOutput: {output_path}")
    print(f"Total syllables: {len(syllables):,}")
    print("\nNext steps:")
    print("  1. Review pinyin_trie.json structure")
    print("  2. Validate against data/audio/syllables_enumeration.json")
    print("  3. Consider creating visualization (optional)")
