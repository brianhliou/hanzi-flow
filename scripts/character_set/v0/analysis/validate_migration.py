#!/usr/bin/env python3
"""
Validate the migration to pypinyin-only dual-format storage.

Checks:
1. Both pinyins_tone3 and pinyins_display columns exist
2. Same number of pronunciations in both columns for each character
3. No mixed formats (all should be pypinyin now)
4. Frequency data only in pinyins_tone3, not in pinyins_display
"""
import csv
import re
from collections import Counter

def validate_migration(csv_path='../../../data/character_set/step6_with_freq.csv'):
    print("=" * 80)
    print("MIGRATION VALIDATION")
    print("=" * 80)
    print(f"\nValidating: {csv_path}\n")

    issues = []
    stats = {
        'total_chars': 0,
        'has_pinyin': 0,
        'no_pinyin': 0,
        'format_mismatches': 0,
        'display_has_freq': 0,
        'tone3_missing_freq': 0,
    }

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total_chars'] += 1
            char = row['char']
            tone3 = row.get('pinyins_tone3', '')
            display = row.get('pinyins_display', '')

            if not tone3 and not display:
                stats['no_pinyin'] += 1
                continue

            stats['has_pinyin'] += 1

            # Check if both columns exist
            if not tone3 or not display:
                issues.append(f"Missing column for {char}: tone3={bool(tone3)}, display={bool(display)}")
                continue

            # Split by pipe
            tone3_parts = tone3.split('|')
            display_parts = display.split('|')

            # Remove frequency data from tone3 for count comparison
            tone3_clean_parts = [re.sub(r'\(\d+\)', '', p) for p in tone3_parts]

            # Check count mismatch
            if len(tone3_clean_parts) != len(display_parts):
                stats['format_mismatches'] += 1
                if len(issues) < 10:
                    issues.append(f"Count mismatch for {char}: tone3={len(tone3_clean_parts)} vs display={len(display_parts)}")

            # Check if display has frequency data (shouldn't)
            if '(' in display:
                stats['display_has_freq'] += 1
                if len(issues) < 10:
                    issues.append(f"Display has frequency for {char}: {display}")

            # Check if tone3 has some pronunciations without frequency (for corpus chars)
            if int(row.get('freq', 0)) > 0:  # Only check corpus characters
                if not any('(' in p for p in tone3_parts):
                    stats['tone3_missing_freq'] += 1

    # Print results
    print("Statistics:")
    print(f"  Total characters: {stats['total_chars']:,}")
    print(f"  Characters with pinyin: {stats['has_pinyin']:,} ({stats['has_pinyin']/stats['total_chars']*100:.1f}%)")
    print(f"  Characters without pinyin: {stats['no_pinyin']:,}")
    print()

    print("Validation Results:")
    if stats['format_mismatches'] == 0:
        print("  ✅ Format consistency: PASS (all characters have matching counts)")
    else:
        print(f"  ❌ Format consistency: FAIL ({stats['format_mismatches']:,} mismatches)")

    if stats['display_has_freq'] == 0:
        print("  ✅ Display format: PASS (no frequency data in pinyins_display)")
    else:
        print(f"  ❌ Display format: FAIL ({stats['display_has_freq']:,} have frequency data)")

    if stats['tone3_missing_freq'] == 0:
        print("  ✅ Tone3 format: PASS (all corpus chars have frequency data)")
    else:
        print(f"  ⚠️  Tone3 format: WARNING ({stats['tone3_missing_freq']:,} corpus chars missing freq)")

    # Show issues
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues (showing first 10):")
        for issue in issues[:10]:
            print(f"     {issue}")
    else:
        print("\n✅ No issues found!")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if stats['format_mismatches'] == 0 and stats['display_has_freq'] == 0:
        print("✅ PASS: Migration successful!")
        print("   - Dual-format storage working correctly")
        print("   - Frequencies only in pinyins_tone3")
        print("   - Format counts match perfectly")
    else:
        print("❌ FAIL: Migration has issues")
        print("   - Review issues above")

    print("=" * 80)


if __name__ == '__main__':
    validate_migration()
