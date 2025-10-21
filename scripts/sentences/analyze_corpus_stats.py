#!/usr/bin/env python3
"""
Analyze corpus statistics from the sentence dataset.

Calculates:
- Total sentences
- Total unique Chinese characters (with pinyin)
- Character frequency distribution
- Script type distribution
"""

import csv
import json
from collections import Counter
from pathlib import Path

def analyze_corpus(csv_path: str):
    """Analyze the sentence corpus and return statistics."""

    unique_chars = set()
    sentence_count = 0
    script_type_counts = Counter()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)  # Default delimiter is ','

        for row in reader:
            sentence_count += 1
            script_type = row.get('script_type', 'unknown')
            script_type_counts[script_type] += 1

            # Parse character-pinyin mapping
            char_pinyin_str = row.get('char_pinyin_pairs', '')
            if not char_pinyin_str:
                continue

            # Format: "char1:pinyin1|char2:pinyin2|..."
            pairs = char_pinyin_str.split('|')
            for pair in pairs:
                if ':' not in pair:
                    continue

                char, pinyin = pair.split(':', 1)

                # Only count Chinese characters (those with pinyin)
                if pinyin and pinyin.strip():
                    unique_chars.add(char)

    stats = {
        'totalSentences': sentence_count,
        'totalCharsInCorpus': len(unique_chars),
        'scriptTypeDistribution': dict(script_type_counts),
        'generatedAt': None  # Will be set by caller
    }

    return stats

def main():
    # Path to sentence dataset
    csv_path = Path(__file__).parent.parent / 'data' / 'sentences' / 'cmn_sentences_with_char_pinyin.csv'

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        return

    print("Analyzing corpus...")
    stats = analyze_corpus(str(csv_path))

    print("\n" + "="*50)
    print("CORPUS STATISTICS")
    print("="*50)
    print(f"Total Sentences: {stats['totalSentences']:,}")
    print(f"Unique Chinese Characters: {stats['totalCharsInCorpus']:,}")
    print(f"\nScript Type Distribution:")
    for script_type, count in sorted(stats['scriptTypeDistribution'].items()):
        pct = (count / stats['totalSentences']) * 100
        print(f"  {script_type:12s}: {count:6,} ({pct:5.1f}%)")
    print("="*50)

    # Optionally write to JSON
    output_path = Path(__file__).parent.parent / 'data' / 'sentences' / 'corpus_stats.json'
    from datetime import datetime
    stats['generatedAt'] = datetime.now().isoformat()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\nStatistics written to: {output_path}")

if __name__ == '__main__':
    main()
