#!/usr/bin/env python3
"""
AWS Polly TTS Audio Generation - FULL PRODUCTION RUN

This script generates audio files for ALL valid Mandarin syllables (~1,478).

Before running:
1. Install boto3: pip install boto3
2. Configure AWS credentials (run: aws configure)
3. Run enumeration script first: python scripts/audio/enumerate_syllables_unihan.py
4. Verify test script works: python scripts/audio/generate_audio_test_aws.py

Usage:
    # Test mode (generate 10 files):
    python scripts/audio/generate_audio_aws.py

    # Production mode (generate all ~1,478 files):
    # Set TEST_LIMIT = None in the configuration section below

Expected runtime: ~30-45 minutes for full run (with rate limiting)
Expected output: ~1,478 OGG files in app/public/data/audio/

Features:
- Automatic resume: Skips existing files if interrupted mid-run
- Progress tracking: Saves progress every 50 files
- Double-check: Verifies file existence before making AWS API calls
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
except ImportError:
    print("ERROR: boto3 not installed")
    print("Install with: pip install boto3")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# AWS Configuration (uses default AWS credentials)
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Voice selection
VOICE_ID = 'Zhiyu'  # Mandarin Chinese female voice
ENGINE = 'neural'   # 'neural' (better quality, $16/1M) or 'standard' (cheaper, $4/1M)

# Audio format
OUTPUT_FORMAT = 'ogg_vorbis'  # OGG Vorbis (good compression, web-friendly)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_JSON = PROJECT_ROOT / 'data' / 'audio' / 'syllables_enumeration.json'
OUTPUT_DIR = PROJECT_ROOT / 'app' / 'public' / 'data' / 'audio'

# Generation settings
RATE_LIMIT_DELAY = 0.15  # seconds between requests (avoid throttling)
PROGRESS_SAVE_INTERVAL = 50  # save progress every N files
RESUME_FROM_EXISTING = True  # skip files that already exist

# TEST MODE: Set to None for full run, or a number (e.g., 10) to limit generation
# This is useful for testing before running the full batch
TEST_LIMIT = None


# ============================================================================
# SSML GENERATION
# ============================================================================

def generate_ssml(syllable: Dict) -> str:
    """
    Generate SSML for a single syllable using AWS Polly x-amazon-pinyin.

    Args:
        syllable: Dict with 'pinyin_tone3' key

    Returns:
        SSML string with phoneme tag

    Example:
        syllable = {'pinyin_tone3': 'lv3'}
        → <speak><phoneme alphabet="x-amazon-pinyin" ph="lv3">字</phoneme></speak>

    Note: AWS Polly uses x-amazon-pinyin alphabet with tone numbers 0-4.
          Neutral tones are marked with '0' (e.g., 'a0', 'ma0').
          Our enumeration data already uses this format.
    """
    pinyin = syllable['pinyin_tone3']  # e.g., "ma1", "lv3", "a0"

    # Use a placeholder Chinese character (phoneme will override its pronunciation)
    placeholder = "字"

    # AWS Polly uses our pinyin_tone3 format directly!
    ssml = f"""<speak>
    <phoneme alphabet="x-amazon-pinyin" ph="{pinyin}">{placeholder}</phoneme>
</speak>"""

    return ssml


# ============================================================================
# AWS POLLY SYNTHESIS
# ============================================================================

def synthesize_syllable(
    syllable: Dict,
    polly_client,
    output_path: str
) -> Dict:
    """
    Synthesize a single syllable using AWS Polly.

    Returns:
        dict with keys: status, duration_ms, file_size, error
    """
    try:
        # Generate SSML
        ssml = generate_ssml(syllable)

        # Call AWS Polly
        response = polly_client.synthesize_speech(
            Text=ssml,
            TextType='ssml',
            OutputFormat=OUTPUT_FORMAT,
            VoiceId=VOICE_ID,
            Engine=ENGINE
        )

        # Check if we got audio stream
        if 'AudioStream' not in response:
            return {
                'status': 'failed',
                'duration_ms': 0,
                'file_size': 0,
                'error': 'No AudioStream in response',
                'ssml': ssml
            }

        # Read and save audio data
        audio_data = response['AudioStream'].read()

        with open(output_path, 'wb') as f:
            f.write(audio_data)

        # Get file stats
        file_size = len(audio_data)

        return {
            'status': 'success',
            'duration_ms': 0,  # Not available from Polly directly
            'file_size': file_size,
            'error': None,
            'ssml': ssml
        }

    except NoCredentialsError:
        return {
            'status': 'failed',
            'duration_ms': 0,
            'file_size': 0,
            'error': 'AWS credentials not found. Run "aws configure" or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY',
            'ssml': ssml if 'ssml' in locals() else None
        }

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        return {
            'status': 'failed',
            'duration_ms': 0,
            'file_size': 0,
            'error': f"AWS ClientError [{error_code}]: {error_msg}",
            'ssml': ssml if 'ssml' in locals() else None
        }

    except Exception as e:
        return {
            'status': 'failed',
            'duration_ms': 0,
            'file_size': 0,
            'error': str(e),
            'ssml': ssml if 'ssml' in locals() else None
        }


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

def load_progress(progress_file: Path) -> Dict:
    """Load progress from JSON file."""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'completed': [],
        'failed': [],
        'total_processed': 0,
        'total_success': 0,
        'total_failed': 0,
        'total_size': 0,
    }


def save_progress(progress: Dict, progress_file: Path):
    """Save progress to JSON file."""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> bool:
    """
    Validate that all required configuration is present.

    Returns:
        True if valid, False otherwise
    """
    errors = []

    # Check input file exists
    if not INPUT_JSON.exists():
        errors.append(f"Input file not found: {INPUT_JSON}")
        errors.append("Run: python scripts/audio/enumerate_syllables_unihan.py")

    # Print errors if any
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    return True


def test_aws_credentials(polly_client) -> bool:
    """
    Test if AWS credentials are valid and Polly is accessible.

    Returns:
        True if credentials work, False otherwise
    """
    try:
        # Try to list voices (minimal API call to test credentials)
        response = polly_client.describe_voices(LanguageCode='cmn-CN')

        # Check if Zhiyu voice is available
        voices = response.get('Voices', [])
        zhiyu_available = any(v['Id'] == 'Zhiyu' for v in voices)

        if not zhiyu_available:
            print("   ⚠ Warning: Zhiyu voice not found in available voices")
            print("   Available Chinese voices:")
            for voice in voices:
                print(f"      - {voice['Id']} ({voice.get('Gender', 'Unknown')})")

        return True

    except NoCredentialsError:
        print("   ❌ AWS credentials not configured")
        print("\n   Please configure AWS credentials:")
        print("      Option 1: Run 'aws configure'")
        print("      Option 2: Set environment variables:")
        print("         export AWS_ACCESS_KEY_ID='your-key'")
        print("         export AWS_SECRET_ACCESS_KEY='your-secret'")
        print("         export AWS_DEFAULT_REGION='us-east-1'")
        return False

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"   ❌ AWS Error [{error_code}]: {error_msg}")

        if error_code == 'InvalidClientTokenId':
            print("      → Your AWS access key ID is invalid")
        elif error_code == 'SignatureDoesNotMatch':
            print("      → Your AWS secret access key is incorrect")
        elif error_code == 'AccessDenied':
            print("      → Your AWS credentials don't have permission to access Polly")
            print("      → Make sure your IAM user/role has 'polly:SynthesizeSpeech' permission")

        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


# ============================================================================
# MAIN GENERATION SCRIPT
# ============================================================================

def main():
    print("=" * 70)
    print("AWS Polly TTS Audio Generation - FULL PRODUCTION RUN")
    print("=" * 70)

    # 1. Validate configuration
    print("\n[1/8] Validating configuration...")
    if not validate_config():
        sys.exit(1)

    print(f"   ✓ AWS region: {AWS_REGION}")
    print(f"   ✓ Voice: {VOICE_ID} ({ENGINE} engine)")
    print(f"   ✓ Output format: {OUTPUT_FORMAT}")
    print(f"   ✓ Input file: {INPUT_JSON}")

    # 2. Initialize AWS Polly client
    print("\n[2/8] Initializing AWS Polly client...")
    try:
        polly_client = boto3.client('polly', region_name=AWS_REGION)
        print("   ✓ Polly client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize Polly client: {e}")
        sys.exit(1)

    # 3. Test AWS credentials
    print("\n[3/8] Testing AWS credentials and Polly access...")
    if not test_aws_credentials(polly_client):
        sys.exit(1)
    print("   ✓ AWS credentials valid and Polly accessible")

    # 4. Load syllables
    print("\n[4/8] Loading syllables...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_syllables = data['syllables']
    total_syllables = len(all_syllables)
    print(f"   ✓ Loaded {total_syllables} syllables")
    print(f"   ✓ Used in dataset: {data['metadata']['used_in_dataset']}")
    print(f"   ✓ Coverage: {data['metadata']['coverage_percent']}%")

    # 5. Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[5/8] Output directory: {OUTPUT_DIR}")

    # 6. Load progress
    progress_file = OUTPUT_DIR / 'generation_progress.json'
    progress = load_progress(progress_file)
    print(f"\n[6/8] Progress tracking:")
    print(f"   ✓ Previously processed: {progress['total_processed']}")
    print(f"   ✓ Previously succeeded: {progress['total_success']}")
    print(f"   ✓ Previously failed: {progress['total_failed']}")

    # 7. Determine which syllables to generate
    print(f"\n[7/8] Preparing generation...")

    completed_set = set(progress['completed'])
    failed_set = set(progress['failed'])

    if RESUME_FROM_EXISTING:
        # Check for existing files on disk
        existing_files = {f.stem for f in OUTPUT_DIR.glob('*.ogg')}
        skip_set = completed_set | existing_files
        to_generate = [s for s in all_syllables if s['filename'] not in skip_set]
        print(f"   ✓ Resume mode: ON")
        print(f"   ✓ Existing files: {len(existing_files)}")
        print(f"   ✓ Skipping: {len(skip_set)} syllables")
    else:
        to_generate = all_syllables
        print(f"   ✓ Resume mode: OFF (regenerating all)")

    # Apply TEST_LIMIT if set
    if TEST_LIMIT is not None:
        to_generate = to_generate[:TEST_LIMIT]
        print(f"\n   ⚠ TEST MODE: Limited to {TEST_LIMIT} syllables")
        print(f"   ⚠ Set TEST_LIMIT = None for full production run")

    print(f"   ✓ To generate: {len(to_generate)} syllables")

    if len(to_generate) == 0:
        print("\n✓ All syllables already generated!")
        sys.exit(0)

    # Confirm before proceeding
    print(f"\n{'=' * 70}")
    print("Ready to generate audio files")
    print("=" * 70)
    print(f"\nWill generate {len(to_generate)} files")
    print(f"Estimated time: {len(to_generate) * RATE_LIMIT_DELAY / 60:.1f} minutes")

    # Calculate estimated cost
    avg_ssml_chars = 100  # rough estimate
    total_chars = len(to_generate) * avg_ssml_chars
    if ENGINE == 'neural':
        cost = (total_chars / 1_000_000) * 16
        print(f"Estimated cost: ${cost:.4f} (neural voice, likely FREE with free tier)")
    else:
        cost = (total_chars / 1_000_000) * 4
        print(f"Estimated cost: ${cost:.4f} (standard voice, likely FREE with free tier)")

    print(f"\nPress Ctrl+C to cancel, or Enter to continue...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n⚠ Cancelled by user")
        sys.exit(0)

    # 8. Generate audio files
    print(f"\n[8/8] Generating {len(to_generate)} audio files...")
    print("=" * 70)

    start_time = time.time()
    results = []

    for i, syllable in enumerate(to_generate, 1):
        filename = f"{syllable['filename']}.ogg"
        output_path = OUTPUT_DIR / filename

        # Show progress
        percent = (i / len(to_generate)) * 100
        print(f"[{i}/{len(to_generate)}] ({percent:.1f}%) {filename:15} ", end='', flush=True)

        # Double-check: Skip if file already exists (in case of mid-run failure)
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"⊙ (exists, {file_size:,} bytes)")
            progress['completed'].append(syllable['filename'])
            progress['total_success'] += 1
            progress['total_processed'] += 1
            progress['total_size'] += file_size
            results.append({
                'syllable': syllable,
                'status': 'skipped',
                'file_size': file_size,
                'error': None,
            })
            continue

        result = synthesize_syllable(syllable, polly_client, str(output_path))

        if result['status'] == 'success':
            print(f"✓ ({result['file_size']:,} bytes)")
            progress['completed'].append(syllable['filename'])
            progress['total_success'] += 1
            progress['total_size'] += result['file_size']
        else:
            print(f"✗ FAILED")
            print(f"   Error: {result['error']}")
            progress['failed'].append(syllable['filename'])
            progress['total_failed'] += 1

        progress['total_processed'] += 1
        results.append({
            'syllable': syllable,
            **result
        })

        # Save progress periodically
        if i % PROGRESS_SAVE_INTERVAL == 0:
            save_progress(progress, progress_file)

        # Rate limiting
        if i < len(to_generate):
            time.sleep(RATE_LIMIT_DELAY)

    # Save final progress
    save_progress(progress, progress_file)

    elapsed_time = time.time() - start_time

    # 9. Summary
    print("\n" + "=" * 70)
    print("Generation Complete!")
    print("=" * 70)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    print(f"\nThis run:")
    print(f"   Total:    {len(results)}")
    print(f"   Success:  {success_count} ✓")
    print(f"   Failed:   {failed_count} ✗")
    print(f"   Time:     {elapsed_time / 60:.1f} minutes")

    print(f"\nOverall progress:")
    print(f"   Total processed:  {progress['total_processed']} / {total_syllables}")
    print(f"   Total success:    {progress['total_success']}")
    print(f"   Total failed:     {progress['total_failed']}")

    if progress['total_success'] > 0:
        avg_size = progress['total_size'] / progress['total_success']
        print(f"\n   Avg file size:    {avg_size:.0f} bytes")
        print(f"   Total size:       {progress['total_size']:,} bytes ({progress['total_size']/1024/1024:.1f} MB)")

    # Show failed syllables details (if any)
    if failed_count > 0:
        print(f"\n   Failed syllables in this run:")
        for r in results:
            if r['status'] == 'failed':
                print(f"      - {r['syllable']['pinyin_tone3']}: {r['error']}")

    print("\n" + "=" * 70)
    if progress['total_success'] == total_syllables:
        print("✓ All syllables generated successfully!")
    elif progress['total_processed'] < total_syllables:
        print(f"⚠ Partial completion: {progress['total_processed']}/{total_syllables}")
        print(f"  Run the script again to resume from where it left off.")

    print("=" * 70)

    print(f"\n✓ Generated files are in: {OUTPUT_DIR}")
    print(f"✓ Progress saved to: {progress_file}")

    # Save detailed results
    results_file = OUTPUT_DIR / 'generation_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'run_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_time_minutes': elapsed_time / 60,
            'results': results,
            'summary': {
                'total': len(results),
                'success': success_count,
                'failed': failed_count,
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"✓ Detailed results saved to: {results_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        print("Progress has been saved. Run the script again to resume.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
