# Audio Generation Scripts

Scripts for generating Mandarin Chinese syllable audio using **AWS Polly**.

## Prerequisites

### 1. Install boto3

```bash
pip install boto3
```

### 2. Configure AWS Credentials

**Option A: Using AWS CLI** (recommended)
```bash
# Install AWS CLI if you don't have it
# https://aws.amazon.com/cli/

# Configure credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: your-access-key
# AWS Secret Access Key: your-secret-key
# Default region: us-east-1 (or your preferred region)
# Default output format: json
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. Verify AWS Access

```bash
# Test AWS credentials
aws sts get-caller-identity

# Check if Polly is accessible
aws polly describe-voices --language-code cmn-CN
```

You should see the Zhiyu voice listed.

---

## Scripts

### `enumerate_syllables_unihan.py`

**Purpose**: Generate complete enumeration of all valid Mandarin syllables (~1,478).

**Usage**:
```bash
python scripts/audio/enumerate_syllables_unihan.py
```

**Output**: `data/audio/syllables_enumeration.json`

This must be run first before audio generation.

---

### `generate_audio_test_aws.py`

**Purpose**: Test AWS Polly with 10 sample syllables to validate setup.

**Usage**:
```bash
python scripts/audio/generate_audio_test_aws.py
```

**What it does**:
- Validates AWS credentials
- Tests Polly access and Zhiyu voice availability
- Selects 10 diverse syllables (different tones, ü syllables, etc.)
- Generates audio files using AWS Polly with SSML x-amazon-pinyin
- Saves to `data/audio/test_output_aws/`
- Provides detailed output and validation

**Expected output**:
```
[1/10] Generating a.ogg... ✓ (8,234 bytes)
[2/10] Generating ma1.ogg... ✓ (9,103 bytes)
...
✓ 10 files generated successfully
```

**Next steps after test**:
1. **Listen to the files** - verify audio quality
2. **Check tone accuracy** - especially ma1, ma2, ma3, ma4
3. **Verify ü pronunciation** - lv3 should sound like "lǚ"
4. If all good → run full generation (script coming next)

---

### `generate_audio.py` (TODO)

Will generate all 1,478 syllables (~30-45 minutes).

---

### `test_player.html`

**Purpose**: Interactive web player to listen to generated test audio.

**Usage**:
```bash
# After running the test script, open in browser:
open scripts/audio/test_player.html
```

**Features**:
- Click to play any syllable
- Tone indicators (color-coded by tone)
- Shows duration after playback
- Perfect for verifying tone accuracy

---

## Troubleshooting

### "AWS credentials not configured" or NoCredentialsError

**Solution**:
```bash
# Option 1: Use AWS CLI
aws configure

# Option 2: Set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### "InvalidClientTokenId" or "SignatureDoesNotMatch"

**Problem**: Wrong AWS credentials.

**Solution**:
- Double-check your access key ID and secret access key
- Make sure there are no extra spaces when copying
- Try generating new credentials in AWS IAM

### "AccessDenied" or permission errors

**Problem**: Your AWS user/role doesn't have Polly permissions.

**Solution**:
1. Go to AWS IAM Console
2. Find your user/role
3. Attach policy: `AmazonPollyFullAccess` (or create custom policy with `polly:SynthesizeSpeech` and `polly:DescribeVoices`)

### "ERROR: boto3 not installed"

Install boto3:
```bash
pip install boto3
```

### "Input file not found"

Run the syllable enumeration script first:
```bash
python scripts/audio/enumerate_syllables_unihan.py
```

This creates `data/audio/syllables_enumeration.json`.

---

## File Structure

```
scripts/audio/
├── README.md                          # This file
├── enumerate_syllables_unihan.py      # Step 1: Create syllable list
├── generate_audio_test_aws.py         # Step 2: Test with 10 syllables
├── generate_audio.py                  # Step 3: Full generation (TODO)
└── test_player.html                   # Audio player for testing

data/audio/
├── syllables_enumeration.json         # Input (1,478 syllables)
├── test_output_aws/                   # Test output (10 files)
│   ├── a.ogg
│   ├── ma1.ogg
│   ├── ...
│   └── test_results.json
└── syllables/                         # Full output (1,478 files, after full run)
    ├── a.ogg
    ├── a1.ogg
    ├── ...
    └── zuo4.ogg
```

---

## AWS Polly Costs

**Free Tier**: 5 million characters/month for 12 months (covers our needs!)

**After free tier**:
- **Standard voices**: $4 per 1 million characters
- **Neural voices** (Zhiyu): $16 per 1 million characters

**Our usage**:
- Test run: ~300 characters (~$0.005 with neural, or **FREE** with free tier)
- Full run: ~4,500 characters (~$0.07 with neural, or **FREE** with free tier)

Each syllable uses ~3 characters in SSML.

---

## Voice Information

### AWS Polly - Mandarin Chinese

**Zhiyu** - Female voice
- Available in both **standard** and **neural** engines
- Neural version provides more natural intonation
- Better performance on English in code-mixing scenarios
- Clear, bright, and natural-sounding

**Engine selection** (in script):
- `ENGINE = 'neural'` - Better quality, $16/1M chars (or free tier)
- `ENGINE = 'standard'` - Good quality, $4/1M chars (or free tier)

---

## Technical Details

### SSML Format

AWS Polly uses **x-amazon-pinyin** alphabet for Mandarin Chinese:

```xml
<speak>
  <phoneme alphabet="x-amazon-pinyin" ph="ma1">字</phoneme>
</speak>
```

**Tone format**: Uses tone numbers 1-4 and neutral (no number)
- `ma1` - Tone 1 (high flat)
- `ma2` - Tone 2 (rising)
- `ma3` - Tone 3 (falling-rising)
- `ma4` - Tone 4 (falling)
- `ma` - Neutral tone

**Perfect match!** This format exactly matches our `pinyin_tone3` field in the enumeration, so no conversion is needed.

### Multi-syllable Format

For multi-syllable words, separate with hyphens:
```xml
<phoneme alphabet="x-amazon-pinyin" ph="ni3-hao3">你好</phoneme>
```

---

## Development Workflow

1. **Generate syllable enumeration** (once):
   ```bash
   python scripts/audio/enumerate_syllables_unihan.py
   ```

2. **Test with 10 syllables**:
   ```bash
   python scripts/audio/generate_audio_test_aws.py
   ```

3. **Verify quality**:
   ```bash
   open scripts/audio/test_player.html
   ```

4. **If good, run full generation** (coming next):
   ```bash
   python scripts/audio/generate_audio.py
   ```

5. **Copy to frontend** (after generation):
   ```bash
   cp -r data/audio/syllables/* hanzi-flow-app/public/audio/syllables/
   ```

---

## Why AWS Polly?

✅ **Simple format** - Uses our `pinyin_tone3` data directly
✅ **Free tier** - 5M chars/month for 12 months
✅ **Familiar** - Standard AWS service
✅ **boto3** - Standard Python AWS SDK
✅ **Good quality** - Neural voices sound natural
✅ **Reliable** - Production-ready AWS infrastructure

---

## Getting Help

If you run into issues:

1. Check the **Troubleshooting** section above
2. Run with verbose output to see detailed errors
3. Verify AWS credentials: `aws sts get-caller-identity`
4. Check Polly access: `aws polly describe-voices --language-code cmn-CN`
5. Make sure boto3 is installed: `pip list | grep boto3`

For AWS-specific issues, see: https://docs.aws.amazon.com/polly/
