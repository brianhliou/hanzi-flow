#!/usr/bin/env python3
"""
Validate Sentences Audio Coverage

Check that every pinyin used in the sentences corpus has:
1. An entry in syllables_enumeration.json
2. A corresponding .ogg audio file

This is the critical validation - we only need audio for pinyins actually used in practice.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

def main():
    project_root = Path(__file__).parent.parent.parent
    sentences_csv = project_root / 'data/sentences/cmn_sentences_with_char_pinyin_and_translation_and_hsk.csv'
    json_path = project_root / 'data/audio/syllables_enumeration.json'
    audio_dir = project_root / 'app/public/data/audio'

    print("=" * 80)
    print("Sentences Audio Coverage Validation")
    print("=" * 80)
    print()

    # =========================================================================
    # Step 1: Extract all pinyins from sentences
    # =========================================================================
    print("[1/3] Extracting pinyins from sentences corpus...")

    sentence_pinyins = set()
    pinyin_usage = defaultdict(list)  # Track which sentences use each pinyin

    with open(sentences_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            sentence_id = row['id']
            char_pinyin_pairs = row['char_pinyin_pairs']

            # Parse char:pinyin|char:pinyin format
            for pair in char_pinyin_pairs.split('|'):
                if ':' in pair:
                    char, pinyin = pair.split(':', 1)
                    if pinyin:  # Skip empty pinyins (punctuation)
                        sentence_pinyins.add(pinyin)
                        pinyin_usage[pinyin].append((sentence_id, char))

    print(f"   ✓ Found {len(sentence_pinyins)} unique pinyins in sentences")
    print()

    # =========================================================================
    # Step 2: Load syllables from JSON
    # =========================================================================
    print("[2/3] Loading syllables from enumeration...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    json_syllables = set()
    for syllable in data['syllables']:
        json_syllables.add(syllable['filename'])

    print(f"   ✓ Found {len(json_syllables)} syllables in enumeration")
    print()

    # =========================================================================
    # Step 3: Check audio files exist
    # =========================================================================
    print("[3/3] Checking audio files...")

    audio_files = set()
    for ogg_file in audio_dir.glob('*.ogg'):
        audio_files.add(ogg_file.stem)

    print(f"   ✓ Found {len(audio_files)} .ogg files")
    print()

    # =========================================================================
    # Validation 1: Sentences pinyins → JSON syllables
    # =========================================================================
    print("=" * 80)
    print("Validation 1: Sentence pinyins → JSON syllables")
    print("=" * 80)

    missing_from_json = sentence_pinyins - json_syllables

    if missing_from_json:
        print(f"❌ FAILED: {len(missing_from_json)} pinyins from sentences are missing in JSON:")
        print()
        for pinyin in sorted(missing_from_json)[:20]:  # Show first 20
            examples = pinyin_usage[pinyin][:3]
            example_str = ', '.join([f"'{char}' (ID {sid})" for sid, char in examples])
            print(f"   - {pinyin:15s} (used by: {example_str})")

        if len(missing_from_json) > 20:
            print(f"   ... and {len(missing_from_json) - 20} more")
        print()
    else:
        print("✅ PASSED: All sentence pinyins are in JSON syllables")
        print()

    # =========================================================================
    # Validation 2: Sentences pinyins → Audio files
    # =========================================================================
    print("=" * 80)
    print("Validation 2: Sentence pinyins → Audio files")
    print("=" * 80)

    missing_audio = sentence_pinyins - audio_files

    if missing_audio:
        print(f"❌ FAILED: {len(missing_audio)} pinyins from sentences are missing audio files:")
        print()
        for pinyin in sorted(missing_audio)[:20]:
            examples = pinyin_usage[pinyin][:3]
            example_str = ', '.join([f"'{char}' (ID {sid})" for sid, char in examples])
            print(f"   - {pinyin}.ogg (used by: {example_str})")

        if len(missing_audio) > 20:
            print(f"   ... and {len(missing_audio) - 20} more")
        print()
    else:
        print("✅ PASSED: All sentence pinyins have audio files")
        print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"Sentence pinyins:   {len(sentence_pinyins)}")
    print(f"JSON syllables:     {len(json_syllables)}")
    print(f"Audio files:        {len(audio_files)}")
    print()
    print(f"Missing from JSON:  {len(missing_from_json)}")
    print(f"Missing audio:      {len(missing_audio)}")
    print()

    # Coverage percentage
    if sentence_pinyins:
        coverage = (len(sentence_pinyins - missing_audio) / len(sentence_pinyins)) * 100
        print(f"Coverage:           {coverage:.2f}%")
        print()

    if missing_from_json or missing_audio:
        print("❌ VALIDATION FAILED - Missing audio for sentences!")
        return 1
    else:
        print("✅ ALL VALIDATIONS PASSED - Complete audio coverage for sentences!")
        return 0

if __name__ == '__main__':
    exit(main())
