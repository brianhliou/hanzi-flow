#!/usr/bin/env python3
"""
Fix extra surrounding quotes in English translations.

This script removes surrounding quotes from English translations when they are
NOT present in the original Chinese sentence. GPT sometimes adds quotes for
CSV formatting which we don't want.

Usage:
    python scripts/sentences/fix_translation_quotes.py
"""

import csv
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_CSV = PROJECT_ROOT / 'data' / 'sentences' / 'cmn_sentences_with_char_pinyin_and_translation.csv'
OUTPUT_CSV = INPUT_CSV  # Overwrite the same file


def has_quotes(text: str) -> bool:
    """Check if text contains any type of quotation marks."""
    quote_chars = ['"', '"', '"', "'", "'", "'", '「', '」', '『', '』']
    return any(q in text for q in quote_chars)


def fix_translation_quotes(chinese: str, english: str) -> str:
    """
    Remove surrounding quotes from English if they're not in Chinese.

    Args:
        chinese: Original Chinese sentence
        english: English translation

    Returns:
        Fixed English translation
    """
    # Only process if English starts and ends with quotes
    if not (english.startswith('"') and english.endswith('"')):
        return english

    # Check if Chinese has quotes
    if has_quotes(chinese):
        # Chinese has quotes, keep them in English
        return english

    # Chinese doesn't have quotes, remove extra ones from English
    return english[1:-1]


def main():
    print("=" * 70)
    print("Fix Extra Quotes in Translations")
    print("=" * 70)

    # Read CSV
    print(f"\nReading: {INPUT_CSV}")
    sentences = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            sentences.append(row)

    print(f"Loaded {len(sentences)} sentences")

    # Fix quotes
    print("\nFixing translations...")
    fixed_count = 0
    for row in sentences:
        chinese = row['sentence']
        english = row['english_translation']

        if not english:  # Skip empty translations
            continue

        fixed_english = fix_translation_quotes(chinese, english)

        if fixed_english != english:
            fixed_count += 1
            print(f"\n  ID {row['id']}:")
            print(f"    Chinese: {chinese[:60]}...")
            print(f"    Before:  {english[:60]}...")
            print(f"    After:   {fixed_english[:60]}...")
            row['english_translation'] = fixed_english

    # Write back
    print(f"\nWriting fixed translations: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentences)

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total sentences:     {len(sentences)}")
    print(f"Fixed translations:  {fixed_count}")
    print(f"Unchanged:           {len(sentences) - fixed_count}")

    if fixed_count > 0:
        print(f"\n✓ Fixed {fixed_count} translations with extra quotes")
    else:
        print(f"\n✓ No translations needed fixing")


if __name__ == '__main__':
    main()
