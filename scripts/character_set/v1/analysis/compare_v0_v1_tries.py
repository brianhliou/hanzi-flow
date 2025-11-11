#!/usr/bin/env python3
"""
Compare v0 (corpus-based, 20k chars) and v1 (SOT, 97k chars) Pinyin Tries.

Generates programmatic comparison with statistics and differences:
- Syllable set differences
- Character count comparisons
- Tone distribution changes
- Depth distribution changes

This helps understand what we gain/lose from the v1 expansion.
"""
import json
import re
from pathlib import Path
from collections import defaultdict


def load_trie(trie_path):
    """Load trie from JSON file."""
    with open(trie_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def collect_syllables(node, prefix=""):
    """
    Recursively collect all terminal syllables from Trie.

    Returns: dict {syllable: characters_data}
    where characters_data varies by version:
    - v0: list of dicts with 'char', 'pinyin_freq', 'corpus_freq'
    - v1: list of strings (just characters)
    """
    syllables = {}

    if node.get("is_end"):
        syllables[prefix] = node.get("characters", [])

    for letter, child in node.get("children", {}).items():
        syllables.update(collect_syllables(child, prefix + letter))

    return syllables


def extract_tone(syllable):
    """Extract tone number from syllable (0-4)."""
    match = re.search(r'(\d)$', syllable)
    if match:
        return int(match.group(1))
    return None


def analyze_tone_distribution(syllables):
    """
    Analyze tone distribution.

    Returns: dict {tone: count}
    """
    tones = defaultdict(int)

    for syllable in syllables:
        tone = extract_tone(syllable)
        if tone is not None:
            tones[tone] += 1

    return tones


def analyze_depth_distribution(trie):
    """
    Analyze depth distribution of terminal nodes.

    Returns: dict {depth: count}
    """
    def count_by_depth(node, depth=0):
        counts = {}
        if node.get('is_end'):
            counts[depth] = 1
        for child in node.get('children', {}).values():
            child_counts = count_by_depth(child, depth + 1)
            for d, count in child_counts.items():
                counts[d] = counts.get(d, 0) + count
        return counts

    return count_by_depth(trie)


def get_character_count(chars_data, version):
    """
    Get character count from characters data.

    Args:
        chars_data: Either list of dicts (v0) or list of strings (v1)
        version: 'v0' or 'v1'
    """
    if version == 'v0':
        # v0: list of dicts with 'char' field
        return len(chars_data)
    else:
        # v1: list of strings
        return len(chars_data)


def extract_characters_set(chars_data, version):
    """
    Extract set of unique characters from characters data.

    Args:
        chars_data: Either list of dicts (v0) or list of strings (v1)
        version: 'v0' or 'v1'

    Returns: set of characters
    """
    if version == 'v0':
        # v0: list of dicts with 'char' field
        return {item['char'] for item in chars_data}
    else:
        # v1: list of strings
        return set(chars_data)


def main():
    print("=" * 80)
    print("COMPARE V0 (CORPUS-BASED) VS V1 (SOT) PINYIN TRIES")
    print("=" * 80)

    # Load both tries
    v0_path = Path('../../../../data/character_set/v0/analysis/pinyin_trie.json')
    v1_path = Path('../../../../data/character_set/v1/analysis/pinyin_trie.json')

    print(f"\nLoading tries...")
    print(f"  v0: {v0_path}")
    print(f"  v1: {v1_path}")

    v0_trie = load_trie(v0_path)
    v1_trie = load_trie(v1_path)

    print("✓ Both tries loaded")

    # Collect syllables
    print(f"\nCollecting syllables...")
    v0_syllables = collect_syllables(v0_trie)
    v1_syllables = collect_syllables(v1_trie)

    v0_syllable_set = set(v0_syllables.keys())
    v1_syllable_set = set(v1_syllables.keys())

    print(f"  v0: {len(v0_syllable_set):,} unique syllables")
    print(f"  v1: {len(v1_syllable_set):,} unique syllables")

    # ========================================================================
    # SYLLABLE SET COMPARISON
    # ========================================================================
    print("\n" + "=" * 80)
    print("SYLLABLE SET COMPARISON")
    print("=" * 80)

    overlap = v0_syllable_set & v1_syllable_set
    only_v0 = v0_syllable_set - v1_syllable_set
    only_v1 = v1_syllable_set - v0_syllable_set

    print(f"\nOverlap: {len(overlap):,} syllables ({len(overlap)/len(v0_syllable_set)*100:.1f}% of v0)")
    print(f"Only in v0: {len(only_v0):,} syllables")
    print(f"Only in v1: {len(only_v1):,} syllables")

    if only_v0:
        print(f"\n{'─'*80}")
        print(f"SYLLABLES IN V0 BUT NOT IN V1 ({len(only_v0):,})")
        print(f"{'─'*80}")
        print("(These are in the corpus but filtered out in v1)")
        print("\nAll examples:")
        sorted_v0_only = sorted(list(only_v0))
        for i in range(0, len(sorted_v0_only), 10):
            line = sorted_v0_only[i:i+10]
            print(f"  {', '.join(line)}")

    if only_v1:
        print(f"\n{'─'*80}")
        print(f"SYLLABLES IN V1 BUT NOT IN V0 ({len(only_v1):,})")
        print(f"{'─'*80}")
        print("(New syllables from expanded character set)")
        print("\nFirst 100 examples:")
        sorted_v1_only = sorted(list(only_v1))
        for i in range(0, min(100, len(sorted_v1_only)), 10):
            line = sorted_v1_only[i:i+10]
            print(f"  {', '.join(line)}")

        if len(sorted_v1_only) > 100:
            print(f"  ... and {len(sorted_v1_only) - 100:,} more")

    # ========================================================================
    # CHARACTER COUNT COMPARISON (for overlapping syllables)
    # ========================================================================
    print("\n" + "=" * 80)
    print("CHARACTER COUNT COMPARISON (Overlapping Syllables)")
    print("=" * 80)

    # Analyze character counts for overlapping syllables
    char_count_diffs = []

    for syllable in sorted(overlap):
        v0_chars = extract_characters_set(v0_syllables[syllable], 'v0')
        v1_chars = extract_characters_set(v1_syllables[syllable], 'v1')

        v0_count = len(v0_chars)
        v1_count = len(v1_chars)
        diff = v1_count - v0_count

        if diff != 0:
            char_count_diffs.append((syllable, v0_count, v1_count, diff, v0_chars, v1_chars))

    print(f"\nTotal overlapping syllables: {len(overlap):,}")
    print(f"Syllables with different character counts: {len(char_count_diffs):,}")

    if char_count_diffs:
        # Sort by absolute difference
        char_count_diffs.sort(key=lambda x: abs(x[3]), reverse=True)

        print(f"\nTop 20 syllables with largest character count differences:")
        print(f"{'Syllable':<10} {'v0':>6} {'v1':>6} {'Diff':>6} {'New in v1'}")
        print("─" * 80)

        for syllable, v0_count, v1_count, diff, v0_chars, v1_chars in char_count_diffs[:20]:
            new_chars = v1_chars - v0_chars
            lost_chars = v0_chars - v1_chars

            if diff > 0:
                # v1 has more
                char_info = f"+{len(new_chars)}: {' '.join(sorted(new_chars)[:5])}"
                if len(new_chars) > 5:
                    char_info += "..."
            else:
                # v0 has more (v1 lost some)
                char_info = f"-{len(lost_chars)}: {' '.join(sorted(lost_chars)[:5])}"
                if len(lost_chars) > 5:
                    char_info += "..."

            print(f"{syllable:<10} {v0_count:>6} {v1_count:>6} {diff:>+6} {char_info}")

        # Summary statistics
        gains = [diff for _, _, _, diff, _, _ in char_count_diffs if diff > 0]
        losses = [diff for _, _, _, diff, _, _ in char_count_diffs if diff < 0]

        print(f"\nSummary of differences:")
        if gains:
            print(f"  Syllables with MORE chars in v1: {len(gains):,}")
            print(f"    Max gain: {max(gains)} characters")
            print(f"    Avg gain: {sum(gains)/len(gains):.1f} characters")
        if losses:
            print(f"  Syllables with FEWER chars in v1: {len(losses):,}")
            print(f"    Max loss: {min(losses)} characters")
            print(f"    Avg loss: {sum(losses)/len(losses):.1f} characters")

    # ========================================================================
    # TONE DISTRIBUTION COMPARISON
    # ========================================================================
    print("\n" + "=" * 80)
    print("TONE DISTRIBUTION COMPARISON")
    print("=" * 80)

    v0_tones = analyze_tone_distribution(v0_syllable_set)
    v1_tones = analyze_tone_distribution(v1_syllable_set)

    tone_labels = {0: 'Neutral', 1: 'Tone 1', 2: 'Tone 2', 3: 'Tone 3', 4: 'Tone 4'}

    print(f"\n{'Tone':<12} {'v0 Count':>12} {'v0 %':>8} {'v1 Count':>12} {'v1 %':>8} {'Diff':>8}")
    print("─" * 80)

    for tone in [0, 1, 2, 3, 4]:
        v0_count = v0_tones.get(tone, 0)
        v1_count = v1_tones.get(tone, 0)
        v0_pct = (v0_count / len(v0_syllable_set) * 100) if v0_syllable_set else 0
        v1_pct = (v1_count / len(v1_syllable_set) * 100) if v1_syllable_set else 0
        diff = v1_count - v0_count

        print(f"{tone_labels[tone]:<12} {v0_count:>12,} {v0_pct:>7.1f}% {v1_count:>12,} {v1_pct:>7.1f}% {diff:>+8,}")

    # ========================================================================
    # DEPTH DISTRIBUTION COMPARISON
    # ========================================================================
    print("\n" + "=" * 80)
    print("DEPTH DISTRIBUTION COMPARISON")
    print("=" * 80)

    v0_depths = analyze_depth_distribution(v0_trie)
    v1_depths = analyze_depth_distribution(v1_trie)

    all_depths = sorted(set(v0_depths.keys()) | set(v1_depths.keys()))

    print(f"\n{'Depth':<8} {'v0 Count':>12} {'v1 Count':>12} {'Diff':>8}")
    print("─" * 80)

    for depth in all_depths:
        v0_count = v0_depths.get(depth, 0)
        v1_count = v1_depths.get(depth, 0)
        diff = v1_count - v0_count

        print(f"{depth:<8} {v0_count:>12,} {v1_count:>12,} {diff:>+8,}")

    # ========================================================================
    # TOTAL CHARACTER COUNT COMPARISON
    # ========================================================================
    print("\n" + "=" * 80)
    print("TOTAL CHARACTER COUNT COMPARISON")
    print("=" * 80)

    v0_total_chars = sum(get_character_count(chars, 'v0') for chars in v0_syllables.values())
    v1_total_chars = sum(get_character_count(chars, 'v1') for chars in v1_syllables.values())

    print(f"\nTotal unique characters across all syllables:")
    print(f"  v0: {v0_total_chars:,} characters")
    print(f"  v1: {v1_total_chars:,} characters")
    print(f"  Difference: {v1_total_chars - v0_total_chars:+,} characters ({(v1_total_chars/v0_total_chars-1)*100:+.1f}%)")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nSyllable Coverage:")
    print(f"  v0 → v1 overlap: {len(overlap):,} / {len(v0_syllable_set):,} ({len(overlap)/len(v0_syllable_set)*100:.1f}%)")
    print(f"  Lost syllables (v0 → v1): {len(only_v0):,}")
    print(f"  Gained syllables (v0 → v1): {len(only_v1):,}")
    print(f"  Net change: {len(v1_syllable_set) - len(v0_syllable_set):+,} syllables")

    print(f"\nCharacter Coverage:")
    print(f"  v0 total: {v0_total_chars:,}")
    print(f"  v1 total: {v1_total_chars:,}")
    print(f"  Net change: {v1_total_chars - v0_total_chars:+,} characters")

    print(f"\nExpansion Factor:")
    print(f"  Syllables: {len(v1_syllable_set) / len(v0_syllable_set):.2f}x")
    print(f"  Characters: {v1_total_chars / v0_total_chars:.2f}x")

    print("\n" + "=" * 80)
    print("✓ Comparison complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
