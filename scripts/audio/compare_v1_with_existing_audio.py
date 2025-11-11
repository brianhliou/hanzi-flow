#!/usr/bin/env python3
"""
Compare v1 syllables enumeration with existing audio files.

Identifies:
1. Missing audio: v1 syllables that don't have audio files yet
2. Extra audio: existing audio files not needed for v1
3. Coverage statistics

This helps us determine which new audio files need to be generated.
"""

import json
from pathlib import Path
from typing import Set


def load_v1_syllables(json_path: Path) -> Set[str]:
    """
    Load v1 syllables from enumeration JSON.

    Returns: set of syllable filenames (e.g., 'ma1', 'de0', 'lv3')
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    syllables = set()
    for item in data['syllables']:
        pinyin = item['pinyin_tone3']
        syllables.add(pinyin)

    return syllables


def scan_existing_audio(audio_dir: Path) -> Set[str]:
    """
    Scan existing audio directory for .ogg files.

    Returns: set of filenames without extension (e.g., 'ma1', 'de0')
    """
    audio_files = set()

    if not audio_dir.exists():
        return audio_files

    for file_path in audio_dir.glob('*.ogg'):
        # Get filename without extension
        filename = file_path.stem
        audio_files.add(filename)

    return audio_files


def main():
    # Paths
    project_root = Path(__file__).parent.parent.parent
    v1_enum_path = project_root / 'data' / 'audio' / 'syllables_enumeration_v1.json'
    audio_dir = project_root / 'app' / 'public' / 'data' / 'audio'
    output_path = project_root / 'data' / 'audio' / 'missing_audio_v1.json'

    print("=" * 80)
    print("Compare v1 Syllables with Existing Audio Files")
    print("=" * 80)

    # Load v1 syllables
    print(f"\nLoading v1 syllables from: {v1_enum_path}")
    v1_syllables = load_v1_syllables(v1_enum_path)
    print(f"✓ Loaded {len(v1_syllables):,} v1 syllables")

    # Scan existing audio
    print(f"\nScanning audio directory: {audio_dir}")
    existing_audio = scan_existing_audio(audio_dir)
    print(f"✓ Found {len(existing_audio):,} existing audio files")

    # Compare
    missing = v1_syllables - existing_audio
    extra = existing_audio - v1_syllables
    overlap = v1_syllables & existing_audio

    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)

    print(f"\nCoverage:")
    print(f"  v1 syllables with audio:  {len(overlap):,} / {len(v1_syllables):,} ({len(overlap)/len(v1_syllables)*100:.1f}%)")
    print(f"  Missing audio (need gen):  {len(missing):,}")
    print(f"  Extra audio (not in v1):   {len(extra):,}")

    # Show missing syllables
    if missing:
        print("\n" + "=" * 80)
        print(f"MISSING AUDIO ({len(missing):,} files need generation)")
        print("=" * 80)

        missing_sorted = sorted(missing)

        # Show all missing syllables in columns
        print("\nAll missing syllables:")
        for i in range(0, len(missing_sorted), 10):
            row = missing_sorted[i:i+10]
            print("  " + ", ".join(f"{s:<8}" for s in row))

        # Categorize by tone
        tone_counts = {'neutral': 0, 'tone1': 0, 'tone2': 0, 'tone3': 0, 'tone4': 0, 'other': 0}
        for syll in missing_sorted:
            if syll.endswith('0'):
                tone_counts['neutral'] += 1
            elif syll.endswith('1'):
                tone_counts['tone1'] += 1
            elif syll.endswith('2'):
                tone_counts['tone2'] += 1
            elif syll.endswith('3'):
                tone_counts['tone3'] += 1
            elif syll.endswith('4'):
                tone_counts['tone4'] += 1
            else:
                tone_counts['other'] += 1

        print(f"\nMissing syllables by tone:")
        for tone, count in tone_counts.items():
            if count > 0:
                print(f"  {tone:8s}: {count:4,}")

        # Check for special cases
        special = [s for s in missing_sorted if 'ê' in s or not s[-1].isdigit()]
        if special:
            print(f"\n⚠️  Special cases that may need attention: {len(special)}")
            for s in special:
                print(f"   {s}")

    else:
        print("\n✓ All v1 syllables have audio files!")

    # Show extra files (optional info)
    if extra:
        print("\n" + "=" * 80)
        print(f"EXTRA AUDIO FILES ({len(extra):,} not in v1)")
        print("=" * 80)
        print("(These are from Unihan enumeration but not used in v1)")

        extra_sorted = sorted(extra)
        print(f"\nFirst 50 extra files:")
        for i in range(0, min(50, len(extra_sorted)), 10):
            row = extra_sorted[i:i+10]
            print("  " + ", ".join(f"{s:<8}" for s in row))

        if len(extra_sorted) > 50:
            print(f"  ... and {len(extra_sorted) - 50:,} more")

    # Save missing list to JSON for audio generation script
    if missing:
        output_data = {
            'metadata': {
                'total_v1_syllables': len(v1_syllables),
                'existing_audio': len(existing_audio),
                'overlap': len(overlap),
                'missing': len(missing),
                'coverage_percent': round(len(overlap) / len(v1_syllables) * 100, 2) if v1_syllables else 0
            },
            'missing_syllables': sorted(missing)
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n✓ Saved missing syllables list to: {output_path}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  v1 syllables:        {len(v1_syllables):,}")
    print(f"  Existing audio:      {len(existing_audio):,}")
    print(f"  Coverage:            {len(overlap):,} ({len(overlap)/len(v1_syllables)*100:.1f}%)")
    print(f"  Need to generate:    {len(missing):,}")

    if missing:
        print(f"\nNext step:")
        print(f"  Generate audio for {len(missing):,} missing syllables")
        print(f"  Use: scripts/audio/generate_audio_v1_missing.py")
    else:
        print(f"\n✓ No audio generation needed - all v1 syllables covered!")

    print("=" * 80)


if __name__ == '__main__':
    main()
