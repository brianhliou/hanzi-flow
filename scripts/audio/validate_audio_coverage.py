#!/usr/bin/env python3
"""
Validate Audio Coverage

This script validates that:
1. Every pinyin in chinese_characters.csv has a corresponding entry in syllables_enumeration.json
2. Every syllable in syllables_enumeration.json has a corresponding .ogg audio file

The tricky part is format conversion:
- CSV has tone marks: nǚ, zhèi, měi
- Enumeration JSON has tone numbers: nv3, zhei4, mei3
- Audio files use tone numbers: nv3.ogg, zhei4.ogg, mei3.ogg
"""

import csv
import json
import os
from pathlib import Path

# Tone mark mapping for conversion
TONE_MARKS = {
    'a': ['a', 'ā', 'á', 'ǎ', 'à'],
    'e': ['e', 'ē', 'é', 'ě', 'è'],
    'i': ['i', 'ī', 'í', 'ǐ', 'ì'],
    'o': ['o', 'ō', 'ó', 'ǒ', 'ò'],
    'u': ['u', 'ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ'],
    'v': ['v', 'ǖ', 'ǘ', 'ǚ', 'ǜ'],
}

def convert_tone_marks_to_numbers(pinyin):
    """
    Convert pinyin with tone marks to tone numbers.
    Examples: nǚ -> nv3, zhèi -> zhei4, měi -> mei3, de -> de0
    """
    if not pinyin:
        return ''

    result = ''
    tone_found = 0

    for char in pinyin:
        replaced = False
        for base_vowel, tone_marks in TONE_MARKS.items():
            tone_index = tone_marks.index(char) if char in tone_marks else -1
            if tone_index != -1:
                result += base_vowel
                if tone_index > 0:
                    tone_found = tone_index
                replaced = True
                break

        if not replaced:
            result += char

    # Convert ü to v for audio file compatibility
    return (result + str(tone_found)).replace('ü', 'v')

def strip_frequency(pinyin):
    """
    Strip frequency data from pinyin.
    Example: "lè(283)" -> "lè"
    """
    import re
    return re.sub(r'\(\d+\)', '', pinyin)

def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / 'app/public/data/character_set/chinese_characters.csv'
    json_path = project_root / 'data/audio/syllables_enumeration.json'
    audio_dir = project_root / 'app/public/data/audio'

    print("=" * 80)
    print("Audio Coverage Validation")
    print("=" * 80)
    print()

    # =========================================================================
    # Step 1: Extract all pinyins from CSV
    # =========================================================================
    print("[1/3] Extracting pinyins from chinese_characters.csv...")

    csv_pinyins_raw = set()
    csv_pinyins_converted = set()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) >= 4:
                pinyins_field = row[3]  # Column 4: pinyins

                # Split by pipe, strip frequency data
                for pinyin in pinyins_field.split('|'):
                    pinyin_clean = strip_frequency(pinyin).strip()
                    if pinyin_clean:
                        csv_pinyins_raw.add(pinyin_clean)
                        converted = convert_tone_marks_to_numbers(pinyin_clean)
                        csv_pinyins_converted.add(converted)

    print(f"   ✓ Found {len(csv_pinyins_raw)} unique pinyins (with tone marks)")
    print(f"   ✓ Converted to {len(csv_pinyins_converted)} unique pinyins (with tone numbers)")
    print()

    # =========================================================================
    # Step 2: Extract all syllables from JSON
    # =========================================================================
    print("[2/3] Extracting syllables from syllables_enumeration.json...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    json_syllables = set()
    for syllable in data['syllables']:
        filename = syllable['filename']
        json_syllables.add(filename)

    print(f"   ✓ Found {len(json_syllables)} syllables in enumeration")
    print()

    # =========================================================================
    # Step 3: Check audio files exist
    # =========================================================================
    print("[3/3] Checking audio files exist...")

    audio_files = set()
    for ogg_file in audio_dir.glob('*.ogg'):
        # Strip .ogg extension
        audio_files.add(ogg_file.stem)

    print(f"   ✓ Found {len(audio_files)} .ogg files")
    print()

    # =========================================================================
    # Validation 1: CSV pinyins → JSON syllables
    # =========================================================================
    print("=" * 80)
    print("Validation 1: CSV pinyins → JSON syllables")
    print("=" * 80)

    missing_from_json = csv_pinyins_converted - json_syllables

    if missing_from_json:
        print(f"❌ FAILED: {len(missing_from_json)} pinyins from CSV are missing in JSON:")
        print()
        for pinyin in sorted(missing_from_json):
            # Find which character(s) use this pinyin
            chars_with_pinyin = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 4:
                        pinyins_field = row[3]
                        for p in pinyins_field.split('|'):
                            p_clean = strip_frequency(p).strip()
                            p_converted = convert_tone_marks_to_numbers(p_clean)
                            if p_converted == pinyin:
                                chars_with_pinyin.append(row[1])
                                break

            chars_str = ', '.join(chars_with_pinyin[:5])
            if len(chars_with_pinyin) > 5:
                chars_str += f', ... ({len(chars_with_pinyin)} total)'

            print(f"   - {pinyin:15s} (used by: {chars_str})")
        print()
    else:
        print("✅ PASSED: All CSV pinyins are in JSON syllables")
        print()

    # =========================================================================
    # Validation 2: JSON syllables → Audio files
    # =========================================================================
    print("=" * 80)
    print("Validation 2: JSON syllables → Audio files")
    print("=" * 80)

    missing_audio = json_syllables - audio_files

    if missing_audio:
        print(f"❌ FAILED: {len(missing_audio)} syllables from JSON are missing audio files:")
        print()
        for syllable in sorted(missing_audio):
            print(f"   - {syllable}.ogg")
        print()
    else:
        print("✅ PASSED: All JSON syllables have audio files")
        print()

    # =========================================================================
    # Validation 3: Extra audio files (not in JSON)
    # =========================================================================
    print("=" * 80)
    print("Validation 3: Extra audio files (not in JSON)")
    print("=" * 80)

    extra_audio = audio_files - json_syllables

    if extra_audio:
        print(f"⚠️  WARNING: {len(extra_audio)} audio files not in JSON:")
        print()
        for filename in sorted(extra_audio):
            print(f"   - {filename}.ogg")
        print()
    else:
        print("✅ PASSED: No extra audio files")
        print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"CSV pinyins:        {len(csv_pinyins_converted)}")
    print(f"JSON syllables:     {len(json_syllables)}")
    print(f"Audio files:        {len(audio_files)}")
    print()
    print(f"Missing from JSON:  {len(missing_from_json)}")
    print(f"Missing audio:      {len(missing_audio)}")
    print(f"Extra audio:        {len(extra_audio)}")
    print()

    if missing_from_json or missing_audio:
        print("❌ VALIDATION FAILED")
        return 1
    else:
        print("✅ ALL VALIDATIONS PASSED")
        return 0

if __name__ == '__main__':
    exit(main())
