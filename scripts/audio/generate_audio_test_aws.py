#!/usr/bin/env python3
"""
AWS Polly TTS Audio Generation - TEST PROTOTYPE

This script tests AWS Polly generation for a small sample of syllables.
Use this to validate:
- AWS credentials and Polly access
- SSML x-amazon-pinyin format
- Audio output quality
- Tone accuracy

Before running:
1. Install boto3: pip install boto3
2. Configure AWS credentials (one of):
   - Run: aws configure
   - Or set environment variables:
     export AWS_ACCESS_KEY_ID="your-key"
     export AWS_SECRET_ACCESS_KEY="your-secret"
     export AWS_DEFAULT_REGION="us-east-1"

Usage:
    python scripts/audio/generate_audio_test_aws.py
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
# Available: ogg_vorbis, mp3, pcm
OUTPUT_FORMAT = 'ogg_vorbis'  # OGG Vorbis (good compression)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_JSON = PROJECT_ROOT / 'data' / 'audio' / 'syllables_enumeration.json'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'audio' / 'test_output_aws'

# Test settings
TEST_LIMIT = 10  # Only generate first 10 syllables
RATE_LIMIT_DELAY = 0.1  # seconds between requests


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

        # AWS Polly doesn't return duration directly
        # We'll need to calculate it from file or leave it as 0
        # (Could use ffprobe or similar to get duration if needed)

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
            print("      → Make sure your IAM user/role has 'polly:DescribeVoices' permission")

        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def select_test_syllables(all_syllables: List[Dict], limit: int) -> List[Dict]:
    """
    Select a diverse set of syllables for testing.

    Selects syllables to cover:
    - Different tones (1, 2, 3, 4, neutral)
    - ü/v syllables (lv, nv)
    - Common and rare syllables

    Returns:
        List of selected syllable dicts
    """
    selected = []

    # Manually pick diverse examples
    targets = [
        'a0',     # neutral tone (AWS Polly format)
        'ma1',    # tone 1
        'ma2',    # tone 2
        'ma3',    # tone 3
        'ma4',    # tone 4
        'lv3',    # ü syllable with tone 3
        'ni3',    # common syllable
        'hao3',   # common word
        'zhang1', # complex syllable
        'zhong1'  # another common one
    ]

    # Find these syllables in the list
    for target in targets[:limit]:
        for syll in all_syllables:
            if syll['pinyin_tone3'] == target:
                selected.append(syll)
                break

    # If we didn't find enough, pad with first N syllables
    while len(selected) < limit:
        for syll in all_syllables:
            if syll not in selected:
                selected.append(syll)
                if len(selected) >= limit:
                    break

    return selected[:limit]


# ============================================================================
# MAIN TEST SCRIPT
# ============================================================================

def main():
    print("=" * 70)
    print("AWS Polly TTS Audio Generation - TEST PROTOTYPE")
    print("=" * 70)

    # 1. Validate configuration
    print("\n[1/7] Validating configuration...")
    if not validate_config():
        sys.exit(1)

    print(f"   ✓ AWS region: {AWS_REGION}")
    print(f"   ✓ Voice: {VOICE_ID} ({ENGINE} engine)")
    print(f"   ✓ Output format: {OUTPUT_FORMAT}")
    print(f"   ✓ Input file: {INPUT_JSON}")

    # 2. Initialize AWS Polly client
    print("\n[2/7] Initializing AWS Polly client...")
    try:
        polly_client = boto3.client('polly', region_name=AWS_REGION)
        print("   ✓ Polly client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize Polly client: {e}")
        sys.exit(1)

    # 3. Test AWS credentials
    print("\n[3/7] Testing AWS credentials and Polly access...")
    if not test_aws_credentials(polly_client):
        sys.exit(1)
    print("   ✓ AWS credentials valid and Polly accessible")

    # 4. Load syllables
    print("\n[4/7] Loading syllables...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_syllables = data['syllables']
    print(f"   ✓ Loaded {len(all_syllables)} total syllables")

    # 5. Select test syllables
    print(f"\n[5/7] Selecting {TEST_LIMIT} test syllables...")
    test_syllables = select_test_syllables(all_syllables, TEST_LIMIT)

    print("   Selected syllables:")
    for i, syll in enumerate(test_syllables, 1):
        in_dataset = "✓" if syll['exists_in_dataset'] else " "
        print(f"      {i:2}. [{in_dataset}] {syll['pinyin_tone3']:8} (AWS format: '{syll['pinyin_tone3']}')")

    # 6. Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[6/7] Output directory: {OUTPUT_DIR}")

    # 7. Generate audio files
    print(f"\n[7/7] Generating {len(test_syllables)} audio files...")
    results = []

    for i, syllable in enumerate(test_syllables, 1):
        filename = f"{syllable['filename']}.ogg"
        output_path = str(OUTPUT_DIR / filename)

        print(f"   [{i}/{len(test_syllables)}] Generating {filename}...", end=' ')

        result = synthesize_syllable(syllable, polly_client, output_path)

        if result['status'] == 'success':
            print(f"✓ ({result['file_size']} bytes)")
        else:
            print(f"✗ FAILED")
            print(f"       Error: {result['error']}")
            if result.get('ssml'):
                print(f"       SSML: {result['ssml'][:100]}...")

        results.append({
            'syllable': syllable,
            **result
        })

        # Rate limiting
        if i < len(test_syllables):
            time.sleep(RATE_LIMIT_DELAY)

    # 8. Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    print(f"   Total:    {len(results)}")
    print(f"   Success:  {success_count} ✓")
    print(f"   Failed:   {failed_count} ✗")

    if success_count > 0:
        total_size = sum(r['file_size'] for r in results if r['status'] == 'success')
        avg_size = total_size / success_count
        print(f"\n   Avg file size: {avg_size:.0f} bytes")
        print(f"   Total size:    {total_size:,} bytes ({total_size/1024:.1f} KB)")

    # Show failed syllables details
    if failed_count > 0:
        print(f"\n   Failed syllables:")
        for r in results:
            if r['status'] == 'failed':
                print(f"      - {r['syllable']['pinyin_tone3']}: {r['error']}")

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)

    if success_count > 0:
        print(f"\n✓ Generated files are in: {OUTPUT_DIR}")
        print("\nNext steps:")
        print("  1. Listen to the generated files to verify quality")
        print("  2. Check tone accuracy (especially ma1, ma2, ma3, ma4)")
        print("  3. Verify ü syllables (lv3 should sound like 'lü' with tone 3)")
        print("  4. Compare quality to your expectations")
        print("  5. If all looks good, run full generation script")

    if failed_count > 0:
        print(f"\n⚠ {failed_count} syllable(s) failed - check errors above")

    # Save detailed results to JSON
    results_file = OUTPUT_DIR / 'test_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

    # Show pricing estimate
    if success_count > 0:
        total_chars = sum(len(r.get('ssml', '')) for r in results if r['status'] == 'success')
        if ENGINE == 'neural':
            cost = (total_chars / 1_000_000) * 16  # $16 per 1M chars
            print(f"\nCost estimate for this test: ${cost:.4f} (neural voice)")
        else:
            cost = (total_chars / 1_000_000) * 4  # $4 per 1M chars
            print(f"\nCost estimate for this test: ${cost:.4f} (standard voice)")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
