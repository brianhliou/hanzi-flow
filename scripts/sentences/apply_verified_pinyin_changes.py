#!/usr/bin/env python3
"""
Apply verified pinyin changes from OpenAI analysis to CSV.

This script applies ONLY the verified high-confidence pinyin improvements:
- 地 (de vs di4): Particle usage
- 著 (zhe vs zhu4): Aspect marker
- 谁/誰 (shei2 vs shui2): Colloquial pronunciation
- 覺/觉 (jiao4 vs jue2): Sleep vs feel
- 長/长 (chang2 vs zhang3): Long vs grow
- 樂 (yue4 vs le4): Music vs happy

Strategy:
1. Read comparison report to identify specific changes
2. Read CSV with char_pinyin_pairs
3. For each change, verify it's a verified character
4. Update ONLY that character's pinyin in char_pinyin_pairs
5. Write to new CSV (never modify original)

Safety features:
- Dry-run mode (preview changes without applying)
- Incremental limits (test with 1, 10, 100 before full run)
- Detailed logging of every change
- Automatic backup creation
- Never modifies original CSV (writes to new CSV)

Usage:
    # Dry run - preview 10 changes
    python3 apply_verified_pinyin_changes.py --limit 10 --dry-run

    # Test with 1 change
    python3 apply_verified_pinyin_changes.py --limit 1

    # Test with 10 changes
    python3 apply_verified_pinyin_changes.py --limit 10

    # Test with 100 changes
    python3 apply_verified_pinyin_changes.py --limit 100

    # Apply all verified changes (2,870 characters)
    python3 apply_verified_pinyin_changes.py
"""

import csv
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# File paths
INPUT_CSV = '../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv'
COMPARISON_REPORT = '../../data/sentences/pinyin_comparison_report.json'
OUTPUT_CSV = '../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk_UPDATED.csv'
BACKUP_CSV = '../../data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk_BACKUP.csv'
CHANGE_LOG = '../../data/sentences/pinyin_changes_applied.log'

# Verified characters - these are the ONLY ones we'll update
VERIFIED_CHARS = {
    '地',   # Particle de vs noun di4
    '著',   # Aspect marker zhe vs verb zhu4
    '谁',   # Colloquial shei2 vs formal shui2
    '誰',   # Colloquial shei2 vs formal shui2 (traditional)
    '覺',   # Sleep jiao4 vs feel jue2 (traditional)
    '觉',   # Sleep jiao4 vs feel jue2 (simplified)
    '長',   # Long chang2 vs grow zhang3 (traditional)
    '长',   # Long chang2 vs grow zhang3 (simplified)
    '樂',   # Music yue4 vs happy le4 (traditional)
}


def log_change(message: str, log_file: str):
    """Log change to both console and file."""
    print(f"  {message}")
    with open(log_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


def load_comparison_report(report_file: str) -> dict:
    """Load the comparison report with all changes."""
    with open(report_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_char_pinyin_pairs(pairs_str: str) -> list:
    """
    Parse char_pinyin_pairs string into list of (char, pinyin) tuples.

    Format: "我:wo3|該:gai1|去:qu4|睡:shui4|覺:jue2|了:le|。:"
    Returns: [('我', 'wo3'), ('該', 'gai1'), ..., ('。', '')]
    """
    if not pairs_str or pairs_str.strip() == '':
        return []

    pairs = []
    for pair in pairs_str.split('|'):
        if ':' not in pair:
            continue
        char, pinyin = pair.split(':', 1)
        pairs.append((char, pinyin))

    return pairs


def format_char_pinyin_pairs(pairs: list) -> str:
    """
    Format list of (char, pinyin) tuples back to string.

    Input: [('我', 'wo3'), ('該', 'gai1'), ...]
    Output: "我:wo3|該:gai1|去:qu4|..."
    """
    return '|'.join(f"{char}:{pinyin}" for char, pinyin in pairs)


def normalize_pinyin(pinyin: str) -> str:
    """
    Normalize pinyin for comparison (remove tone marks, keep tone numbers).

    This matches the comparison script's normalization.
    """
    if not pinyin:
        return ''

    # Tone mark mappings
    tone_map = {
        # First tone
        'ā': ('a', '1'), 'ē': ('e', '1'), 'ī': ('i', '1'), 'ō': ('o', '1'), 'ū': ('u', '1'), 'ǖ': ('v', '1'),
        # Second tone
        'á': ('a', '2'), 'é': ('e', '2'), 'í': ('i', '2'), 'ó': ('o', '2'), 'ú': ('u', '2'), 'ǘ': ('v', '2'),
        # Third tone
        'ǎ': ('a', '3'), 'ě': ('e', '3'), 'ǐ': ('i', '3'), 'ǒ': ('o', '3'), 'ǔ': ('u', '3'), 'ǚ': ('v', '3'),
        # Fourth tone
        'à': ('a', '4'), 'è': ('e', '4'), 'ì': ('i', '4'), 'ò': ('o', '4'), 'ù': ('u', '4'), 'ǜ': ('v', '4'),
        # Neutral ü
        'ü': ('v', ''),
    }

    result = []
    tone_number = ''

    for char in pinyin.lower():
        if char in tone_map:
            base, tone = tone_map[char]
            result.append(base)
            if tone:
                tone_number = tone
        else:
            result.append(char)

    return ''.join(result) + tone_number


def apply_changes(
    csv_rows: list,
    report: dict,
    limit: int = None,
    dry_run: bool = False,
    log_file: str = CHANGE_LOG
) -> list:
    """
    Apply verified pinyin changes to CSV rows.

    Args:
        csv_rows: List of row dicts from CSV
        report: Comparison report with changes
        limit: Maximum number of changes to apply (None = all)
        dry_run: If True, don't actually modify, just log what would change
        log_file: Path to log file

    Returns:
        Modified CSV rows (or original if dry_run)
    """
    # Initialize log file
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Pinyin Changes Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}\n")
        f.write(f"Limit: {limit if limit else 'ALL'}\n")
        f.write("=" * 70 + "\n\n")

    # Create sentence lookup: id -> row
    row_lookup = {row['id']: row for row in csv_rows}

    # Track changes
    changes_applied = 0
    changes_skipped = 0

    # Process each sentence with changes from the report
    for sentence_change in report['sentence_changes']:
        if limit and changes_applied >= limit:
            log_change(f"Reached limit of {limit} changes, stopping.", log_file)
            break

        sentence_id = str(sentence_change['id'])  # CSV IDs are strings
        sentence_text = sentence_change['sentence']

        # Get the row from CSV
        if sentence_id not in row_lookup:
            log_change(f"⚠️  Sentence {sentence_id} not found in CSV, skipping", log_file)
            continue

        row = row_lookup[sentence_id]

        # Parse char_pinyin_pairs
        pairs = parse_char_pinyin_pairs(row['char_pinyin_pairs'])

        # Process each character change in this sentence
        for change in sentence_change['changes']:
            if limit and changes_applied >= limit:
                break

            char = change['char']
            before_pinyin = change['before']
            after_pinyin = change['after']

            # ONLY apply if this is a verified character
            if char not in VERIFIED_CHARS:
                changes_skipped += 1
                continue

            # Find this character in the pairs and update it
            found = False
            for i, (pair_char, pair_pinyin) in enumerate(pairs):
                if pair_char == char and pair_pinyin == before_pinyin:
                    # Verify the change makes sense
                    before_normalized = normalize_pinyin(before_pinyin)
                    after_normalized = normalize_pinyin(after_pinyin)

                    if before_normalized == after_normalized:
                        # Just a tone mark difference, skip
                        changes_skipped += 1
                        break

                    # Apply the change
                    if not dry_run:
                        pairs[i] = (pair_char, after_pinyin)

                    changes_applied += 1
                    log_change(
                        f"{'[DRY RUN] ' if dry_run else ''}Changed sentence {sentence_id}: "
                        f"'{sentence_text[:50]}...' - {char}: {before_pinyin} → {after_pinyin}",
                        log_file
                    )
                    found = True
                    break

            if not found and char in VERIFIED_CHARS:
                log_change(
                    f"⚠️  Could not find char '{char}' with pinyin '{before_pinyin}' "
                    f"in sentence {sentence_id}",
                    log_file
                )

        # Update the row with modified pairs
        if not dry_run:
            row['char_pinyin_pairs'] = format_char_pinyin_pairs(pairs)

    # Summary
    log_change("", log_file)
    log_change("=" * 70, log_file)
    log_change("SUMMARY", log_file)
    log_change("=" * 70, log_file)
    log_change(f"Changes applied:  {changes_applied}", log_file)
    log_change(f"Changes skipped:  {changes_skipped} (non-verified characters)", log_file)

    return csv_rows


def main():
    parser = argparse.ArgumentParser(
        description='Apply verified pinyin changes from OpenAI analysis to CSV'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of changes to apply (for testing). Default: apply all'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually applying them'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Apply Verified Pinyin Changes (CSV)")
    print("=" * 70)

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be applied")

    print(f"\nVerified characters: {', '.join(sorted(VERIFIED_CHARS))}")
    print(f"Limit: {args.limit if args.limit else 'ALL'}")

    # Load data
    print(f"\n[1/5] Loading comparison report...")
    report = load_comparison_report(COMPARISON_REPORT)
    print(f"  ✓ Loaded report with {len(report['sentence_changes'])} sentences with changes")

    print(f"\n[2/5] Loading CSV...")
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        csv_rows = list(reader)
    print(f"  ✓ Loaded {len(csv_rows)} rows")

    # Create backup (if not dry run)
    if not args.dry_run:
        print(f"\n[3/5] Creating backup...")
        shutil.copy2(INPUT_CSV, BACKUP_CSV)
        print(f"  ✓ Backup created: {BACKUP_CSV}")
    else:
        print(f"\n[3/5] Skipping backup (dry run mode)")

    # Apply changes
    print(f"\n[4/5] Applying changes...")
    modified_rows = apply_changes(
        csv_rows,
        report,
        limit=args.limit,
        dry_run=args.dry_run,
        log_file=CHANGE_LOG
    )

    # Save output (if not dry run)
    if not args.dry_run:
        print(f"\n[5/5] Saving modified CSV...")
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(modified_rows)
        print(f"  ✓ Saved to: {OUTPUT_CSV}")
    else:
        print(f"\n[5/5] Skipping save (dry run mode)")

    # Final summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)

    if args.dry_run:
        print(f"\n✓ Dry run complete - see what would change in:")
        print(f"    {CHANGE_LOG}")
        print(f"\nTo apply changes, re-run without --dry-run flag")
    else:
        print(f"\n✓ Changes applied successfully!")
        print(f"\nFiles created:")
        print(f"  - Modified CSV:   {OUTPUT_CSV}")
        print(f"  - Backup:         {BACKUP_CSV}")
        print(f"  - Change log:     {CHANGE_LOG}")
        print(f"\nNext steps:")
        print(f"  1. Review change log: {CHANGE_LOG}")
        print(f"  2. Update your data pipeline to use:")
        print(f"     {OUTPUT_CSV}")
        print(f"  3. Regenerate production JSON from updated CSV")

    return 0


if __name__ == '__main__':
    exit(main())
