#!/usr/bin/env python3
"""
Generate syllables enumeration from v1 Pinyin Trie (SOT character set).

This replaces the Unihan-based enumeration for v1, using the actual
syllables found in the v1 trie as the source of truth.

Input:
- data/character_set/v1/analysis/pinyin_trie.json

Output:
- data/audio/syllables_enumeration_v1.json

The output format matches v0's enumeration for compatibility with
audio generation scripts.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


def collect_syllables_from_trie(trie: Dict, prefix: str = "") -> Set[str]:
    """
    Recursively collect all terminal syllables from trie.

    Returns: set of syllable strings in tone3 format (e.g., 'ma1', 'de0', 'lv3')
    """
    syllables = set()

    if trie.get("is_end"):
        syllables.add(prefix)

    for letter, child in trie.get("children", {}).items():
        syllables.update(collect_syllables_from_trie(child, prefix + letter))

    return syllables


def parse_syllable(pinyin_tone3: str) -> Dict:
    """
    Parse a tone3 format syllable into components.

    Args:
        pinyin_tone3: e.g., 'ma1', 'de0', 'lv3', 'a1'

    Returns:
        dict with: base, tone, pinyin_tone3, base_proper
    """
    # Extract base and tone
    # Format: letters followed by optional digit (0-4)
    match = re.match(r'^([a-z]+?)(\d?)$', pinyin_tone3)

    if not match:
        # Handle edge cases like 'ê1', 'ê2', etc.
        match = re.match(r'^(.+?)(\d?)$', pinyin_tone3)
        if not match:
            raise ValueError(f"Could not parse syllable: {pinyin_tone3}")

    base = match.group(1)
    tone_str = match.group(2)

    # Convert tone string to int or None
    if tone_str:
        tone = int(tone_str)
    else:
        # No tone digit means neutral (should not happen in v1 trie, but handle it)
        tone = 0
        pinyin_tone3 = base + '0'

    # Convert v back to ü for display (proper pinyin)
    base_proper = base.replace('v', 'ü')

    return {
        'base': base,
        'base_proper': base_proper,
        'tone': tone,
        'pinyin_tone3': pinyin_tone3,
    }


def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent
    trie_path = project_root / 'data' / 'character_set' / 'v1' / 'analysis' / 'pinyin_trie.json'
    output_json = project_root / 'data' / 'audio' / 'syllables_enumeration_v1.json'

    # Create output directory
    output_json.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Generate Syllables Enumeration from v1 Trie (SOT Character Set)")
    print("=" * 80)

    # Load v1 trie
    print(f"\nLoading v1 trie from: {trie_path}")
    with open(trie_path, 'r', encoding='utf-8') as f:
        trie = json.load(f)
    print("✓ Trie loaded")

    # Collect syllables
    print("\nExtracting syllables from trie...")
    syllables_set = collect_syllables_from_trie(trie)
    print(f"✓ Found {len(syllables_set):,} unique syllables")

    # Parse syllables into metadata
    print("\nParsing syllable metadata...")
    syllables_list = []

    for syll in sorted(syllables_set):
        try:
            metadata = parse_syllable(syll)
            syllables_list.append(metadata)
        except ValueError as e:
            print(f"⚠️  Warning: {e}")

    print(f"✓ Parsed {len(syllables_list):,} syllables")

    # Check for special cases
    special_cases = [s for s in syllables_list if 'ê' in s['base']]
    if special_cases:
        print(f"\n⚠️  Found {len(special_cases)} special cases with non-standard romanization:")
        for s in special_cases:
            print(f"   {s['pinyin_tone3']} (base: {s['base']})")

    # Analyze tone distribution
    tone_counts = {}
    for s in syllables_list:
        tone = s['tone']
        tone_counts[tone] = tone_counts.get(tone, 0) + 1

    # Create output
    output = {
        'metadata': {
            'total_syllables': len(syllables_list),
            'source': 'v1 Pinyin Trie (SOT character set, 97k chars)',
            'trie_source': str(trie_path.relative_to(project_root)),
            'format': 'tone3 (tone numbers 0-4)',
            'special_cases': len(special_cases),
            'tone_distribution': {
                'neutral': tone_counts.get(0, 0),
                'tone1': tone_counts.get(1, 0),
                'tone2': tone_counts.get(2, 0),
                'tone3': tone_counts.get(3, 0),
                'tone4': tone_counts.get(4, 0),
            }
        },
        'syllables': syllables_list
    }

    # Write output
    print(f"\nWriting output to: {output_json}")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("✓ Enumeration complete!")
    print("=" * 80)

    print(f"\nSummary:")
    print(f"  Total syllables: {len(syllables_list):,}")
    print(f"  Output file: {output_json}")

    print(f"\nTone distribution:")
    for tone_name, count in output['metadata']['tone_distribution'].items():
        pct = (count / len(syllables_list) * 100) if len(syllables_list) > 0 else 0
        print(f"  {tone_name:8s}: {count:4,} ({pct:5.1f}%)")

    if special_cases:
        print(f"\n⚠️  Special cases: {len(special_cases)} syllables")
        print(f"   These may need special handling in AWS Polly")

    # Show examples
    print(f"\n" + "=" * 80)
    print("Sample syllables:")
    print("=" * 80)
    for i, s in enumerate(syllables_list[:20], 1):
        tone_label = f"tone{s['tone']}" if s['tone'] > 0 else "neutral"
        print(f"  {i:2d}. {s['pinyin_tone3']:8s} (base: {s['base']:6s}, {tone_label:8s}) -> {s['pinyin_tone3']}.ogg")

    if len(syllables_list) > 20:
        print(f"  ... and {len(syllables_list) - 20:,} more")

    print("\n" + "=" * 80)
    print("Next steps:")
    print("  1. Review syllables_enumeration_v1.json")
    print("  2. Compare with v0 to find new syllables")
    print("  3. Generate audio for new syllables only")
    print("=" * 80)


if __name__ == '__main__':
    main()
