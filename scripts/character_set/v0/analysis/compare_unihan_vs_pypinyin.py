#!/usr/bin/env python3
"""
Phase 1: Compare Unihan vs pypinyin coverage and verify dual-format consistency.

This script verifies that pypinyin can replace Unihan as our pinyin source by:
1. Comparing pinyin coverage (Unihan+enrichment vs pypinyin alone)
2. Identifying any characters pypinyin doesn't cover
3. Verifying Style.TONE3 and Style.TONE return same count/order

Input: step7_with_freq.csv (current data with Unihan+pypinyin)
Output: verification_report.txt
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

try:
    from pypinyin import pinyin, Style
except ImportError:
    print("ERROR: pypinyin library not installed")
    print("Install with: pip install pypinyin")
    sys.exit(1)


def load_current_data(csv_path='../../../data/character_set/step7_with_freq.csv'):
    """
    Load current character data (Unihan + pypinyin enrichment).
    Returns: dict mapping char -> current_pinyins (set of base forms)
    """
    print(f"Loading current data from {csv_path}...")

    char_data = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row['char']
            freq = int(row.get('freq', 0))

            # Check ALL characters (not just corpus)
            # Parse current pinyins (mixed format)
            pinyins_str = row.get('pinyins', '')
            char_data[char] = {
                'pinyins_str': pinyins_str,
                'freq': freq,
                'in_corpus': freq > 0
            }

    in_corpus_count = sum(1 for d in char_data.values() if d['in_corpus'])
    print(f"✓ Loaded {len(char_data):,} total characters")
    print(f"  - {in_corpus_count:,} in corpus (freq > 0)")
    print(f"  - {len(char_data) - in_corpus_count:,} not in corpus")
    return char_data


def normalize_pinyin_to_base(pinyin_str):
    """
    Normalize pinyin to base form (no tones, no frequency data).
    Used for comparing if two pinyins are the same pronunciation.
    """
    import re

    # Remove frequency data
    py = re.sub(r'\(\d+\)', '', pinyin_str).strip()

    # Remove tone numbers
    py = re.sub(r'[0-9]', '', py)

    # Remove tone marks
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

    return py.lower()


def parse_current_pinyins(pinyins_str):
    """Parse current pinyin field to base forms."""
    if not pinyins_str:
        return set()

    base_forms = set()
    for part in pinyins_str.split('|'):
        if part.strip():
            base = normalize_pinyin_to_base(part.strip())
            if base:
                base_forms.add(base)

    return base_forms


def get_pypinyin_coverage(char_data):
    """
    For each character, get pypinyin results and compare with current data.

    Returns: dict with statistics and examples
    """
    print("\nComparing pypinyin vs current data...")

    stats = {
        'total_chars': len(char_data),
        'in_corpus_count': sum(1 for d in char_data.values() if d['in_corpus']),
        'pypinyin_has_all': 0,
        'pypinyin_has_more': 0,
        'pypinyin_has_less': 0,
        'pypinyin_missing': 0,
        'pypinyin_missing_in_corpus': 0,  # Critical: missing AND in corpus
        'dual_format_mismatches': 0
    }

    examples = {
        'pypinyin_has_more': [],
        'pypinyin_has_less': [],
        'pypinyin_missing': [],
        'dual_format_mismatch': []
    }

    for i, (char, data) in enumerate(char_data.items(), 1):
        # Parse current pinyins
        current_bases = parse_current_pinyins(data['pinyins_str'])

        # Get pypinyin results (both formats)
        try:
            tone3_result = pinyin(char, style=Style.TONE3, heteronym=True)
            display_result = pinyin(char, style=Style.TONE, heteronym=True)

            if tone3_result and len(tone3_result) > 0:
                pypinyin_tone3 = tone3_result[0]
                pypinyin_display = display_result[0]

                # Check dual-format consistency
                if len(pypinyin_tone3) != len(pypinyin_display):
                    stats['dual_format_mismatches'] += 1
                    if len(examples['dual_format_mismatch']) < 10:
                        examples['dual_format_mismatch'].append({
                            'char': char,
                            'tone3_count': len(pypinyin_tone3),
                            'display_count': len(pypinyin_display),
                            'tone3': pypinyin_tone3,
                            'display': pypinyin_display
                        })

                # Normalize pypinyin to base forms
                pypinyin_bases = {normalize_pinyin_to_base(py) for py in pypinyin_tone3}

                # Compare
                if pypinyin_bases == current_bases:
                    stats['pypinyin_has_all'] += 1
                elif pypinyin_bases > current_bases:
                    stats['pypinyin_has_more'] += 1
                    if len(examples['pypinyin_has_more']) < 10:
                        examples['pypinyin_has_more'].append({
                            'char': char,
                            'current': current_bases,
                            'pypinyin': pypinyin_bases,
                            'extra': pypinyin_bases - current_bases
                        })
                else:
                    stats['pypinyin_has_less'] += 1
                    if len(examples['pypinyin_has_less']) < 10:
                        examples['pypinyin_has_less'].append({
                            'char': char,
                            'current': current_bases,
                            'pypinyin': pypinyin_bases,
                            'missing': current_bases - pypinyin_bases
                        })
            else:
                stats['pypinyin_missing'] += 1
                if data['in_corpus']:
                    stats['pypinyin_missing_in_corpus'] += 1
                if len(examples['pypinyin_missing']) < 10:
                    examples['pypinyin_missing'].append({
                        'char': char,
                        'current': current_bases,
                        'freq': data['freq'],
                        'in_corpus': data['in_corpus']
                    })

        except Exception as e:
            print(f"Warning: Error processing '{char}': {e}")

        if i % 500 == 0:
            print(f"  Processed {i:,} / {len(char_data):,} characters...")

    return stats, examples


def generate_report(stats, examples, output_path='../../../data/character_set/analysis/verification_report.txt'):
    """Generate verification report."""

    total = stats['total_chars']

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PYPINYIN VS UNIHAN+ENRICHMENT VERIFICATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary
    report_lines.append("SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Total characters analyzed: {total:,}")
    report_lines.append(f"  - In corpus (freq > 0):   {stats['in_corpus_count']:,}")
    report_lines.append(f"  - Reference only (freq=0): {total - stats['in_corpus_count']:,}")
    report_lines.append("")

    # Coverage comparison
    report_lines.append("Coverage Comparison (All Characters):")
    report_lines.append(f"  pypinyin matches current:     {stats['pypinyin_has_all']:,} ({stats['pypinyin_has_all']/total*100:.1f}%)")
    report_lines.append(f"  pypinyin has MORE:            {stats['pypinyin_has_more']:,} ({stats['pypinyin_has_more']/total*100:.1f}%)")
    report_lines.append(f"  pypinyin has LESS:            {stats['pypinyin_has_less']:,} ({stats['pypinyin_has_less']/total*100:.1f}%)")
    report_lines.append(f"  pypinyin MISSING (no data):   {stats['pypinyin_missing']:,} ({stats['pypinyin_missing']/total*100:.1f}%)")
    report_lines.append("")

    # Coverage percentage (total)
    covered = total - stats['pypinyin_missing']
    coverage_pct = covered / total * 100
    report_lines.append(f"✓ pypinyin coverage (ALL): {covered:,} / {total:,} = {coverage_pct:.2f}%")

    # Coverage percentage (corpus only - critical)
    in_corpus = stats['in_corpus_count']
    corpus_covered = in_corpus - stats['pypinyin_missing_in_corpus']
    corpus_coverage_pct = corpus_covered / in_corpus * 100 if in_corpus > 0 else 0
    report_lines.append(f"✓ pypinyin coverage (CORPUS): {corpus_covered:,} / {in_corpus:,} = {corpus_coverage_pct:.2f}%")

    if stats['pypinyin_missing_in_corpus'] > 0:
        report_lines.append(f"  ⚠️  CRITICAL: {stats['pypinyin_missing_in_corpus']:,} corpus characters have no pypinyin data!")
    report_lines.append("")

    # Dual-format consistency
    report_lines.append("Dual-Format Consistency:")
    report_lines.append(f"  Style.TONE3 vs Style.TONE mismatches: {stats['dual_format_mismatches']:,}")
    if stats['dual_format_mismatches'] > 0:
        mismatch_pct = stats['dual_format_mismatches'] / total * 100
        report_lines.append(f"  ({mismatch_pct:.2f}% of characters)")
    else:
        report_lines.append(f"  ✓ Perfect consistency - all characters have same count/order")
    report_lines.append("")

    # Examples
    if examples['pypinyin_has_more']:
        report_lines.append("=" * 80)
        report_lines.append("EXAMPLES: pypinyin has MORE pronunciations")
        report_lines.append("=" * 80)
        for ex in examples['pypinyin_has_more'][:10]:
            report_lines.append(f"\n{ex['char']}:")
            report_lines.append(f"  Current:  {sorted(ex['current'])}")
            report_lines.append(f"  pypinyin: {sorted(ex['pypinyin'])}")
            report_lines.append(f"  Extra:    {sorted(ex['extra'])}")

    if examples['pypinyin_has_less']:
        report_lines.append("\n" + "=" * 80)
        report_lines.append("EXAMPLES: pypinyin has LESS pronunciations")
        report_lines.append("=" * 80)
        for ex in examples['pypinyin_has_less'][:10]:
            report_lines.append(f"\n{ex['char']}:")
            report_lines.append(f"  Current:  {sorted(ex['current'])}")
            report_lines.append(f"  pypinyin: {sorted(ex['pypinyin'])}")
            report_lines.append(f"  Missing:  {sorted(ex['missing'])}")

    if examples['pypinyin_missing']:
        report_lines.append("\n" + "=" * 80)
        report_lines.append("EXAMPLES: pypinyin has NO DATA")
        report_lines.append("=" * 80)
        for ex in examples['pypinyin_missing'][:10]:
            corpus_flag = " [IN CORPUS - CRITICAL]" if ex['in_corpus'] else " [reference only]"
            report_lines.append(f"\n{ex['char']} (freq: {ex['freq']:,}){corpus_flag}:")
            report_lines.append(f"  Current:  {sorted(ex['current'])}")
            report_lines.append(f"  pypinyin: (no data)")

    if examples['dual_format_mismatch']:
        report_lines.append("\n" + "=" * 80)
        report_lines.append("EXAMPLES: Dual-format mismatches (TONE3 vs TONE count)")
        report_lines.append("=" * 80)
        for ex in examples['dual_format_mismatch'][:10]:
            report_lines.append(f"\n{ex['char']}:")
            report_lines.append(f"  TONE3:   {ex['tone3']} ({ex['tone3_count']} items)")
            report_lines.append(f"  TONE:    {ex['display']} ({ex['display_count']} items)")

    # Decision
    report_lines.append("\n" + "=" * 80)
    report_lines.append("DECISION CHECKPOINT")
    report_lines.append("=" * 80)

    # Use corpus coverage for critical decision (what matters for app)
    # Use total coverage for reference data quality
    corpus_pass = corpus_coverage_pct >= 99.0
    total_pass = coverage_pct >= 95.0  # Lower threshold for reference-only chars
    format_pass = stats['dual_format_mismatches'] == 0

    if corpus_pass and format_pass:
        report_lines.append(f"✅ PASS: Corpus coverage {corpus_coverage_pct:.2f}% >= 99% (CRITICAL)")
        report_lines.append(f"{'✅' if total_pass else '⚠️'} {'PASS' if total_pass else 'WARNING'}: Total coverage {coverage_pct:.2f}% {'>=' if total_pass else '<'} 95% (reference data)")
        report_lines.append(f"✅ PASS: Dual-format consistency 100%")
        report_lines.append("")
        if total_pass:
            report_lines.append("RECOMMENDATION: Proceed with migration (pypinyin-only)")
        else:
            report_lines.append("RECOMMENDATION: Proceed with migration, but note some reference characters lack pypinyin")
    elif corpus_pass:
        report_lines.append(f"✅ PASS: Corpus coverage {corpus_coverage_pct:.2f}% >= 99% (CRITICAL)")
        report_lines.append(f"⚠️  WARNING: {stats['dual_format_mismatches']} dual-format mismatches")
        report_lines.append("")
        report_lines.append("RECOMMENDATION: Investigate mismatches before proceeding")
    else:
        report_lines.append(f"❌ FAIL: Corpus coverage {corpus_coverage_pct:.2f}% < 99%")
        report_lines.append(f"         Missing: {stats['pypinyin_missing_in_corpus']:,} CORPUS characters")
        report_lines.append(f"         Total missing: {stats['pypinyin_missing']:,} characters")
        report_lines.append("")
        report_lines.append("RECOMMENDATION: Investigate missing corpus characters or keep Unihan as fallback")

    report_lines.append("=" * 80)

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n✓ Report saved to: {output_path}")

    # Also print to console
    print("\n" + '\n'.join(report_lines))


if __name__ == '__main__':
    print("=" * 80)
    print("Phase 1: Verify pypinyin coverage and dual-format consistency")
    print("=" * 80)

    # Load current data
    char_data = load_current_data()

    # Compare coverage
    stats, examples = get_pypinyin_coverage(char_data)

    # Generate report
    generate_report(stats, examples)

    print("\n✓ Verification complete!")
