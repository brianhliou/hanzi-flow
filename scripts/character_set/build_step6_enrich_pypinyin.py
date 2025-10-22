#!/usr/bin/env python3
"""
Step 6: Enrich character set with pypinyin heteronym alternatives.

This step adds missing colloquial/alternative pronunciations that pypinyin knows
but aren't in the Unihan dictionary data.

Examples:
- 谁: Unihan has shuí, pypinyin adds shéi (colloquial)
- 地: Unihan has dì, pypinyin adds de (particle usage)
- 的: Unihan has de, pypinyin adds dī/dí/dì (rare usages)

Input: ../../data/character_set/step5_hsk.csv
Output: ../../data/character_set/step6_enriched.csv
"""

import csv
import re
from pathlib import Path

try:
    from pypinyin import pinyin, Style
except ImportError:
    print("ERROR: pypinyin library not installed")
    print("Install with: pip install pypinyin")
    exit(1)


def normalize_pinyin_to_base(py: str) -> str:
    """
    Normalize pinyin to base form (no tones, no formatting).

    This is used to detect if two pinyins are genuinely different.

    Examples:
    - 'shéi' → 'shei'
    - 'shei2' → 'shei'
    - 'de' → 'de'
    - 'dì' → 'di'
    """
    # Remove any whitespace
    py = py.strip().lower()

    # Remove tone numbers (1-5)
    py = re.sub(r'[1-5]', '', py)

    # Remove tone marks by replacing with base vowels
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
        'ü': 'v'
    }
    for old, new in tone_map.items():
        py = py.replace(old, new)

    return py


def parse_existing_pinyins(pinyins_str: str) -> set:
    """
    Parse existing pinyins from character_set format and return BASE forms.

    Format: 'lè(283)|yuè(54)' or 'shuí(1065)' or 'de|di1|di2'
    Returns: set of base pinyins (no tones, no frequency data)

    Examples:
    - 'lè(283)|yuè(54)' → {'le', 'yue'}
    - 'shuí(1065)' → {'shui'}
    - 'de|dì' → {'de', 'di'}
    """
    if not pinyins_str or pinyins_str.strip() == '':
        return set()

    result = set()
    parts = pinyins_str.split('|')

    for part in parts:
        # Remove frequency data: 'lè(283)' → 'lè'
        py = re.sub(r'\(\d+\)', '', part).strip()
        if py:
            # Normalize to base form for comparison
            result.add(normalize_pinyin_to_base(py))

    return result


def get_pypinyin_alternatives(char: str) -> set:
    """
    Get all pypinyin heteronym pronunciations for a character.

    Returns: set of BASE FORM pinyins (no tones)
    """
    try:
        result = pinyin(char, style=Style.TONE, heteronym=True)
        if result and len(result) > 0:
            # result is like [['shuí', 'shéi']]
            pronunciations = result[0]
            # Normalize to base form to detect genuinely different pronunciations
            return {normalize_pinyin_to_base(py) for py in pronunciations}
    except Exception as e:
        print(f"Warning: Failed to get pypinyin for '{char}': {e}")

    return set()


def get_pypinyin_with_tones(char: str) -> dict:
    """
    Get pypinyin pronunciations with tone marks.

    Returns: dict mapping base form → tone mark format
    Example: {'shui': 'shuí', 'shei': 'shéi'}
    """
    try:
        result = pinyin(char, style=Style.TONE, heteronym=True)
        if result and len(result) > 0:
            pronunciations = result[0]
            mapping = {}
            for py in pronunciations:
                base = normalize_pinyin_to_base(py)
                mapping[base] = py
            return mapping
    except Exception as e:
        print(f"Warning: Failed to get pypinyin for '{char}': {e}")

    return {}


def merge_pinyins(existing: set, pypinyin_alts: set, char: str) -> set:
    """
    Merge existing and pypinyin alternatives (base form comparison).

    Args:
        existing: set of base form pinyins from character_set
        pypinyin_alts: set of base form pinyins from pypinyin
        char: the character (used to get original tone mark format)

    Returns: set of NEW pinyins with tone marks to add, or None if no new alternatives
    """
    # New alternatives = pypinyin - existing (base form comparison)
    new_base_forms = pypinyin_alts - existing

    if not new_base_forms:
        # No new alternatives
        return None

    # Get the tone mark format for the new base forms
    tone_mapping = get_pypinyin_with_tones(char)
    new_pinyins_with_tones = set()
    for base in new_base_forms:
        if base in tone_mapping:
            new_pinyins_with_tones.add(tone_mapping[base])

    return new_pinyins_with_tones if new_pinyins_with_tones else None


def enrich_character_set(
    input_file: str = '../../data/character_set/step5_hsk.csv',
    output_file: str = '../../data/character_set/step6_enriched.csv'
):
    """
    Enrich character set with pypinyin alternatives.
    """
    print("=" * 70)
    print("Step 6: Enrich with pypinyin heteronym alternatives")
    print("=" * 70)

    # Read input
    print(f"\nReading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        characters = list(reader)

    print(f"Loaded {len(characters):,} characters")

    # Enrich with pypinyin
    print("\nEnriching pinyins with pypinyin alternatives...")
    enriched_count = 0
    examples = []

    for i, row in enumerate(characters, 1):
        char = row['char']
        existing_pinyins_str = row.get('pinyins', '')

        # Get existing pinyins (BASE FORM - normalized)
        existing = parse_existing_pinyins(existing_pinyins_str)

        # Get pypinyin alternatives (BASE FORM)
        pypinyin_alts = get_pypinyin_alternatives(char)

        # Merge (compares base forms, returns tone number format)
        new_alts = merge_pinyins(existing, pypinyin_alts, char)

        if new_alts:
            # Add new alternatives to existing string
            new_pinyins_str = existing_pinyins_str + '|' + '|'.join(sorted(new_alts))
            row['pinyins'] = new_pinyins_str
            enriched_count += 1

            # Collect examples for display
            if len(examples) < 10:
                examples.append({
                    'char': char,
                    'before': existing_pinyins_str,
                    'after': new_pinyins_str,
                    'added': sorted(new_alts)
                })

        if i % 5000 == 0:
            print(f"  Processed {i:,} characters... ({enriched_count:,} enriched)")

    # Write output
    print(f"\nWriting: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(characters)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total characters:     {len(characters):,}")
    print(f"Enriched:             {enriched_count:,} ({enriched_count/len(characters)*100:.1f}%)")
    print(f"Unchanged:            {len(characters) - enriched_count:,}")

    # Show examples
    if examples:
        print("\n" + "=" * 70)
        print("EXAMPLES (first 10 enrichments)")
        print("=" * 70)
        for ex in examples:
            print(f"\n{ex['char']}:")
            print(f"  Before: {ex['before']}")
            print(f"  After:  {ex['after']}")
            print(f"  Added:  {', '.join(ex['added'])}")

    print("\n" + "=" * 70)
    print("✓ Enrichment complete!")
    print("=" * 70)

    # Key improvements
    print("\nKey improvements:")

    # Check for specific cases
    shui_char = next((c for c in characters if c['char'] == '谁'), None)
    if shui_char and 'shéi' in shui_char['pinyins']:
        print("  ✓ 谁: Added shéi (colloquial pronunciation)")

    di_char = next((c for c in characters if c['char'] == '地'), None)
    if di_char and '|de' in di_char['pinyins']:
        print("  ✓ 地: Added de (particle usage)")

    de_char = next((c for c in characters if c['char'] == '的'), None)
    if de_char and ('dī' in de_char['pinyins'] or 'dí' in de_char['pinyins']):
        print("  ✓ 的: Added alternative pronunciations")

    print("\nNext steps:")
    print("  1. Review examples above")
    print("  2. Copy to production locations:")
    print("     - ../../data/chinese_characters.csv")
    print("     - ../../app/public/data/character_set/chinese_characters.csv")


if __name__ == '__main__':
    enrich_character_set()
