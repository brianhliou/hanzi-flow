#!/usr/bin/env python3
"""
Improve sentence-level pinyin using OpenAI for context-aware pronunciation.

This script processes all sentences and uses OpenAI to generate natural,
context-appropriate pinyin with tone marks.

Strategy:
1. Process all sentences (no filtering)
2. Batch 10 sentences per API call (efficient like translation script)
3. Incremental saves with checkpointing (resume on failure)
4. Start with small sample, then scale up

Input: ../../app/public/data/sentences/sentences_with_translation.json
Output: ../../data/sentences/sentences_pinyin_openai.json

Cost estimate: ~80k sentences, batched × $0.0001 = ~$8-10
Time estimate: ~4-5 hours (with 2s rate limit delay)

Usage:
    # Test with 10 sentences
    python3 improve_pinyin_with_openai.py --limit 10

    # Test with 100 sentences
    python3 improve_pinyin_with_openai.py --limit 100

    # Full run (all sentences)
    python3 improve_pinyin_with_openai.py
"""

import json
import os
import time
import argparse
from pathlib import Path
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError

# No filtering - process all sentences for comprehensive improvement

# File paths
INPUT_FILE = '../../app/public/data/sentences/sentences_with_translation.json'
OUTPUT_DIR = '../../data/sentences'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'sentences_pinyin_openai.json')
PARTIAL_FILE = OUTPUT_FILE + '.jsonl'  # JSON Lines for incremental saves
CHECKPOINT_FILE = OUTPUT_FILE + '.checkpoint'

# API settings
BATCH_SIZE = 10  # Process 10 sentences per API call
RATE_LIMIT_DELAY = 2.0  # 2 second delay between API calls (safe for Tier 1: 500 RPM)
MAX_RETRIES = 3  # Retry failed API calls up to 3 times
RETRY_DELAY = 5  # Wait 5 seconds before retrying
API_TIMEOUT = 60  # 60 second timeout for API calls
ERROR_LOG_FILE = OUTPUT_FILE + '.errors.log'  # Log file for errors


def log_error(message: str):
    """Log error message to both console and file."""
    print(f"  ⚠️  {message}")
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


def get_pinyin_batch_with_retry(sentences: list, client: OpenAI) -> list:
    """
    Get pinyin batch with retry logic for robustness.

    Retries up to MAX_RETRIES times on transient errors.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return get_pinyin_batch(sentences, client)
        except (APIConnectionError, APITimeoutError) as e:
            # Transient network/timeout errors - retry
            if attempt < MAX_RETRIES - 1:
                log_error(f"Transient error (attempt {attempt + 1}/{MAX_RETRIES}): {type(e).__name__}: {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                continue
            else:
                log_error(f"Failed after {MAX_RETRIES} attempts: {type(e).__name__}: {e}")
                raise
        except RateLimitError as e:
            # Rate limit - wait longer and retry
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (attempt + 2) * 2  # Longer wait for rate limits
                log_error(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), waiting {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                log_error(f"Rate limit exceeded after {MAX_RETRIES} attempts: {e}")
                raise
        except APIError as e:
            # Other API errors - log and raise immediately (likely non-retryable)
            log_error(f"API error: {type(e).__name__}: {e}")
            raise
        except Exception as e:
            # Unexpected errors - log and raise
            log_error(f"Unexpected error: {type(e).__name__}: {e}")
            raise

    # Should never reach here
    raise Exception("Retry logic failed unexpectedly")


def get_pinyin_batch(sentences: list, client: OpenAI) -> list:
    """
    Get context-aware pinyin for a batch of sentences using OpenAI.

    Uses sentence-level format with strict preservation of non-Chinese elements.

    Args:
        sentences: List of sentence dicts with 'id', 'sentence', 'chars' keys
        client: OpenAI client

    Returns: List of sentence dicts with updated 'chars' array
    """
    # Build prompt with sentence-level format
    prompt_parts = []
    prompt_parts.append("For each Chinese sentence below, provide the natural, context-appropriate pinyin with tone marks (ā, á, ǎ, à).")
    prompt_parts.append("")
    prompt_parts.append("CRITICAL RULES:")
    prompt_parts.append("- Chinese characters → convert to pinyin with tone marks, ONE SYLLABLE PER CHARACTER")
    prompt_parts.append("- Multi-character words → separate each character's pinyin (唯一 → wéi yī, NOT wéiyī)")
    prompt_parts.append("- Quoted words → separate quotes from pinyin (\"对\" → \" duì \", NOT \"duì\")")
    prompt_parts.append("- Numbers → preserve EXACTLY as they appear (6, 18, ６, １８)")
    prompt_parts.append("- Punctuation → preserve EXACTLY as they appear (，, 。, ！, ?, \", etc.)")
    prompt_parts.append("- English names → preserve EXACTLY (Tom, Jim, Muiriel, Ann, etc.)")
    prompt_parts.append("- Chinese transliterations of names (罗杰斯, 史密斯) → convert to pinyin")
    prompt_parts.append("- Separate all tokens with single spaces")
    prompt_parts.append("")
    prompt_parts.append("Output format:")
    prompt_parts.append("[sentence_id]: [pinyin mixed with preserved non-Chinese]")
    prompt_parts.append("")
    prompt_parts.append("Example:")
    prompt_parts.append("Input: 今天是6月18号，Tom说\"你好\"！")
    prompt_parts.append("Output: 123: jīn tiān shì 6 yuè 18 hào ， Tom shuō \" nǐ hǎo \" ！")
    prompt_parts.append("")
    prompt_parts.append("Example with multi-character word:")
    prompt_parts.append("Input: 月球是地球唯一的卫星。")
    prompt_parts.append("Output: 456: yuè qiú shì dì qiú wéi yī de wèi xīng 。")
    prompt_parts.append("")
    prompt_parts.append("Sentences:")

    # Add each sentence
    for sentence in sentences:
        prompt_parts.append(f"{sentence['id']}: {sentence['sentence']}")

    prompt = '\n'.join(prompt_parts)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # Deterministic
        timeout=API_TIMEOUT,
    )

    # Parse response - one line per sentence
    response_text = response.choices[0].message.content.strip()
    response_lines = response_text.split('\n')

    # Create mapping: sentence_id -> pinyin_tokens
    pinyin_map = {}
    for line in response_lines:
        line = line.strip()
        if not line or ':' not in line:
            continue

        # Parse: "123: jīn tiān shì 6 yuè 18 hào"
        try:
            parts = line.split(':', 1)
            if len(parts) == 2:
                sid = int(parts[0].strip())
                pinyin_text = parts[1].strip()
                pinyin_map[sid] = pinyin_text.split()  # Split by spaces
        except ValueError:
            continue

    # Update sentences with new pinyins
    for sentence in sentences:
        sid = sentence['id']
        if sid not in pinyin_map:
            continue

        pinyin_tokens = pinyin_map[sid]

        # Save raw OpenAI output for debugging
        sentence['openai_raw'] = ' '.join(pinyin_tokens)

        char_index = 0

        # Align tokens with chars
        for token in pinyin_tokens:
            if char_index >= len(sentence['chars']):
                break

            char_obj = sentence['chars'][char_index]

            # Check if token matches the original character (number, punct, English)
            if token == char_obj['char']:
                # Non-Chinese element preserved - move to next
                char_index += 1
            else:
                # This is pinyin for a Chinese character
                char_obj['pinyin'] = token
                char_index += 1

    return sentences


def load_checkpoint() -> int:
    """Load checkpoint index if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return int(f.read().strip())
    return 0


def save_checkpoint(index: int):
    """Save checkpoint index."""
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(str(index))


def append_to_partial(sentences: list):
    """Append processed sentences to partial file (JSON Lines format)."""
    with open(PARTIAL_FILE, 'a', encoding='utf-8') as f:
        for sentence in sentences:
            f.write(json.dumps(sentence, ensure_ascii=False) + '\n')


def finalize_output():
    """Convert JSON Lines partial file to final JSON structure."""
    print(f"\nFinalizing output...")

    # Read all lines from partial file
    sentences = []
    with open(PARTIAL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            sentences.append(json.loads(line))

    # Load original metadata
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    # Create final output structure (same as input format, just with updated pinyin)
    output_data = {
        'metadata': {
            'totalSentences': len(sentences),
            'processedFrom': original_data.get('metadata', {}).get('totalSentences', 0),
            'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'source': 'openai-gpt-4o-mini',
            'description': 'Context-aware pinyin with tone marks generated by OpenAI (character-by-character)'
        },
        'sentences': sentences
    }

    # Write final output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Wrote final output: {OUTPUT_FILE}")

    # Clean up
    os.remove(PARTIAL_FILE)
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    print(f"✓ Cleaned up temporary files")


def main():
    parser = argparse.ArgumentParser(description='Improve sentence pinyin with OpenAI')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of sentences to process (for testing)')
    args = parser.parse_args()

    print("=" * 70)
    print("OpenAI Sentence Pinyin Improvement")
    print("=" * 70)

    # Create output directory if needed
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load input sentences
    print(f"\nReading: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_sentences = data['sentences']
    print(f"Loaded {len(all_sentences):,} total sentences")

    # Apply limit if specified (for testing)
    sentences_to_process = all_sentences
    if args.limit:
        sentences_to_process = all_sentences[:args.limit]
        print(f"Limited to {len(sentences_to_process):,} sentences for testing")

    # Check for checkpoint
    start_index = load_checkpoint()
    if start_index > 0:
        print(f"\n✓ Resuming from checkpoint: {start_index:,} sentences already processed")
        sentences_to_process = sentences_to_process[start_index:]

    # Initialize OpenAI client
    client = OpenAI()

    # Process in batches
    print(f"\nProcessing {len(sentences_to_process):,} sentences in batches of {BATCH_SIZE}...")
    print("(This may take a while - progress is saved incrementally)\n")

    total_processed = start_index

    failed_batches = []

    for i in range(0, len(sentences_to_process), BATCH_SIZE):
        batch = sentences_to_process[i:i + BATCH_SIZE]
        batch_start_id = batch[0]['id']
        batch_end_id = batch[-1]['id']

        try:
            # Get improved pinyin from OpenAI (with retry logic)
            improved_batch = get_pinyin_batch_with_retry(batch, client)

            # Save to partial file immediately
            append_to_partial(improved_batch)

            # Update checkpoint
            total_processed += len(improved_batch)
            save_checkpoint(total_processed)

            # Progress update
            if (i + BATCH_SIZE) % 100 == 0 or (i + BATCH_SIZE) >= len(sentences_to_process):
                print(f"  Processed {total_processed:,} sentences...")

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            # Log the error and track failed batch
            log_error(f"Failed to process batch (sentences {batch_start_id}-{batch_end_id}): {type(e).__name__}: {e}")
            failed_batches.append({
                'start_id': batch_start_id,
                'end_id': batch_end_id,
                'sentence_ids': [s['id'] for s in batch],
                'error': str(e)
            })

            # Save original batch to partial file (with unchanged pinyin)
            # This ensures we don't lose progress and can continue
            append_to_partial(batch)

            # Update checkpoint to skip this batch
            total_processed += len(batch)
            save_checkpoint(total_processed)

            print(f"  ⚠️  Skipped batch, continuing with next batch...")

            # Continue processing remaining batches
            continue

    # Finalize output
    finalize_output()

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Total sentences processed: {total_processed:,}")

    if failed_batches:
        print(f"\n⚠️  WARNING: {len(failed_batches)} batches failed and were skipped:")
        for fb in failed_batches:
            print(f"  - Sentences {fb['start_id']}-{fb['end_id']}: {fb['error']}")
        print(f"\nFailed batches saved with original pinyin (unchanged).")
        print(f"Check error log for details: {ERROR_LOG_FILE}")
        print(f"\nTo retry failed batches, you can manually reprocess them later.")
    else:
        print(f"\n✓ All batches processed successfully!")

    print(f"\nOutput: {OUTPUT_FILE}")
    print("\nNext steps:")
    print("  1. Review output file")
    if failed_batches:
        print(f"  2. Check error log: {ERROR_LOG_FILE}")
        print(f"  3. Run compare_pinyin_changes.py to see what changed")
        print(f"  4. Manually review/fix failed batches if needed")
    else:
        print("  2. Run compare_pinyin_changes.py to see what changed")
        print("  3. If satisfied, copy to production location")

    return 0


if __name__ == '__main__':
    exit(main())
