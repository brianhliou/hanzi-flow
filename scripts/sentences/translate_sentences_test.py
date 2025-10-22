#!/usr/bin/env python3
"""
Test Script: Translate Chinese Sentences to English using GPT-4o-mini

This script tests the translation pipeline on a small subset of sentences
before running the full batch.

Usage:
    # Set your OpenAI API key first:
    export OPENAI_API_KEY="sk-your-key-here"

    # Run test with 10 sentences (default):
    python scripts/sentences/translate_sentences_test.py

    # Run test with custom limit:
    python scripts/sentences/translate_sentences_test.py --limit 100

Test sequence:
    - Test 1: 10 sentences (validate setup)
    - Test 2: 100 sentences (validate quality)
    - Test 3: 1,000 sentences (validate scale)
"""

import os
import sys
import csv
import json
import time
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

try:
    import openai
except ImportError:
    print("ERROR: openai library not installed")
    print("Install with: pip install openai")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# OpenAI Configuration
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2  # Low temperature for consistent, accurate translations
MAX_TOKENS_PER_SENTENCE = 500   # Generous limit to handle even the longest sentences

# Batching Configuration
BATCH_SIZE = 10    # Number of sentences to translate per API call

# Costs (as of 2024)
INPUT_COST_PER_1M_TOKENS = 0.15   # $0.15 per 1M input tokens
OUTPUT_COST_PER_1M_TOKENS = 0.60  # $0.60 per 1M output tokens

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_CSV = PROJECT_ROOT / 'data' / 'sentences' / 'cmn_sentences_with_char_pinyin.csv'
OUTPUT_CSV = PROJECT_ROOT / 'data' / 'sentences' / 'cmn_sentences_with_char_pinyin_and_translation.csv'
LOG_FILE = PROJECT_ROOT / 'data' / 'sentences' / 'translation_test.log'


# ============================================================================
# PROMPT ENGINEERING
# ============================================================================

SYSTEM_PROMPT = """You are a Chinese-to-English translator for a language learning application.
Translate Chinese sentences to natural, clear English.

Rules:
1. Output ONLY the translations, nothing else
2. Keep proper nouns (names, places) in their original form
3. One translation per line, numbered
4. Be concise but natural
5. Preserve the tone and meaning of the original

Example:
Input:
1. 我爱你
2. 今天天气很好
3. Muiriel现在20岁了

Output:
1. I love you
2. The weather is nice today
3. Muiriel is 20 now"""


def create_batch_prompt(sentences: List[Tuple[int, str]]) -> str:
    """
    Create a prompt for translating a batch of sentences.

    Args:
        sentences: List of (id, chinese_sentence) tuples

    Returns:
        Formatted prompt string
    """
    numbered_sentences = []
    for i, (_, sentence) in enumerate(sentences, 1):
        numbered_sentences.append(f"{i}. {sentence}")

    sentences_text = '\n'.join(numbered_sentences)

    user_prompt = f"""Translate these Chinese sentences to English:

{sentences_text}"""

    return user_prompt


# ============================================================================
# OPENAI API INTERACTION
# ============================================================================

def translate_batch(
    client: openai.OpenAI,
    sentences: List[Tuple[int, str]]
) -> Tuple[List[str], Dict]:
    """
    Translate a batch of sentences using GPT-4o-mini.

    Args:
        client: OpenAI client instance
        sentences: List of (id, chinese_sentence) tuples

    Returns:
        Tuple of (translations list, stats dict)
    """
    user_prompt = create_batch_prompt(sentences)

    try:
        # Calculate max_tokens based on sentence length
        # Give more tokens for longer sentences
        max_tokens = MAX_TOKENS_PER_SENTENCE * len(sentences)

        print(f"(calling API...)", end=' ', flush=True)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=max_tokens,
            timeout=60.0  # 60 second timeout
        )
        print(f"(got response)", end=' ', flush=True)

        # Extract response text
        response_text = response.choices[0].message.content

        # Parse translations
        translations = parse_batch_response(response_text, len(sentences))

        # Calculate cost
        usage = response.usage
        cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens)

        stats = {
            'prompt_tokens': usage.prompt_tokens,
            'completion_tokens': usage.completion_tokens,
            'total_tokens': usage.total_tokens,
            'cost': cost,
            'status': 'success'
        }

        return translations, stats

    except openai.RateLimitError as e:
        print(f"\n   RATE LIMIT ERROR: {e}")
        print(f"   Waiting 60 seconds before retrying...")
        time.sleep(60)
        # Return empty translations - caller can retry
        return [''] * len(sentences), {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'cost': 0,
            'status': 'rate_limited',
            'error': str(e)
        }
    except openai.APITimeoutError as e:
        print(f"\n   TIMEOUT ERROR: {e}")
        # Return empty translations on error
        return [''] * len(sentences), {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'cost': 0,
            'status': 'timeout',
            'error': str(e)
        }
    except Exception as e:
        print(f"\n   ERROR: {e}")
        # Return empty translations on error
        return [''] * len(sentences), {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'cost': 0,
            'status': 'failed',
            'error': str(e)
        }


def parse_batch_response(response_text: str, expected_count: int) -> List[str]:
    """
    Parse numbered translation response from GPT.

    Expected format:
        1. Translation one
        2. Translation two
        3. Translation three

    Args:
        response_text: Raw response from GPT
        expected_count: Number of translations expected

    Returns:
        List of translation strings

    Raises:
        ValueError: If parsing fails or count mismatch
    """
    lines = response_text.strip().split('\n')
    translations = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pattern 1: "1. Translation text"
        match = re.match(r'^\d+\.\s*(.+)$', line)
        if match:
            translation = match.group(1).strip()
            translations.append(translation)
        # Pattern 2: Just text (no number) - only if we're missing translations
        elif len(translations) < expected_count and not line.startswith('#'):
            translations.append(line)

    # Validation
    if len(translations) != expected_count:
        raise ValueError(
            f"Expected {expected_count} translations, got {len(translations)}. "
            f"Response: {response_text[:200]}..."
        )

    return translations


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD for token usage."""
    input_cost = (prompt_tokens / 1_000_000) * INPUT_COST_PER_1M_TOKENS
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_COST_PER_1M_TOKENS
    return input_cost + output_cost


# ============================================================================
# VALIDATION
# ============================================================================

def validate_translation(chinese: str, english: str) -> Tuple[bool, str]:
    """
    Validate translation quality.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not english or not english.strip():
        return False, "Empty translation"

    # Translation shouldn't be identical to input
    if english.strip() == chinese.strip():
        return False, "Translation identical to input"

    # Translation shouldn't be mostly Chinese characters
    chinese_char_count = sum(1 for c in english if '\u4e00' <= c <= '\u9fff')
    if chinese_char_count > len(english) * 0.3:
        return False, f"Too many Chinese characters ({chinese_char_count}/{len(english)})"

    # Translation should have reasonable length
    if len(english.strip()) < 2:
        return False, "Translation too short"

    # Check for common error patterns (refusal messages from model)
    # Be specific to avoid false positives with legitimate translations
    error_phrases = [
        "I cannot translate", "I can't translate", "I'm unable to translate",
        "I cannot help", "I can't help", "I'm unable to help",
        "translation failed", "unable to provide"
    ]
    english_lower = english.lower()
    for phrase in error_phrases:
        if phrase.lower() in english_lower:
            return False, f"Contains error phrase: {phrase}"

    return True, ""


# ============================================================================
# DATA PROCESSING
# ============================================================================

def load_sentences(csv_path: Path, limit: int = None) -> List[Dict]:
    """
    Load sentences from CSV.

    Returns:
        List of sentence dicts with keys: id, sentence, script_type, char_pinyin_pairs
    """
    sentences = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sentences.append({
                'id': row['id'],  # Read ID from CSV
                'sentence': row['sentence'],
                'script_type': row['script_type'],
                'char_pinyin_pairs': row['char_pinyin_pairs']
            })

            if limit and len(sentences) >= limit:
                break

    return sentences


def load_existing_translations(output_path: Path) -> Dict[str, str]:
    """
    Load existing translations from previous runs.

    Returns:
        Dict mapping sentence_id -> english_translation
    """
    if not output_path.exists():
        return {}

    existing = {}
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            translation = row.get('english_translation', '').strip()
            if translation:  # Only keep non-empty translations
                existing[row['id']] = translation

    return existing


def save_translated_sentences(sentences: List[Dict], output_path: Path):
    """
    Save sentences with translations to CSV.

    Args:
        sentences: List of dicts with keys: id, sentence, script_type,
                   char_pinyin_pairs, english_translation
    """
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['id', 'sentence', 'script_type', 'char_pinyin_pairs', 'english_translation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentences)


# ============================================================================
# MAIN TEST SCRIPT
# ============================================================================

def setup_logging():
    """Set up logging to both file and console."""
    # Create logger
    logger = logging.getLogger('translation')
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers = []

    # File handler (all messages including DEBUG)
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (only INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def main():
    parser = argparse.ArgumentParser(description='Test Chinese to English translation')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of sentences to translate (default: 10, use 0 for all)')
    args = parser.parse_args()

    # Handle limit=0 as "process all"
    if args.limit == 0:
        args.limit = None

    # Set up logging
    logger = setup_logging()

    print("=" * 70)
    print("Chinese to English Translation - TEST RUN")
    print("=" * 70)
    logger.info("=" * 70)
    if args.limit is None:
        logger.info("Starting translation test run with limit=ALL (processing entire dataset)")
        print("   Mode: Processing ALL sentences")
    else:
        logger.info("Starting translation test run with limit=%d", args.limit)
        print(f"   Mode: Processing first {args.limit} sentences")
    logger.info("Log file: %s", LOG_FILE)

    # 1. Validate API key
    print("\n[1/6] Validating OpenAI API key...")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("\n   Set it with:")
        print("      export OPENAI_API_KEY='sk-your-key-here'")
        sys.exit(1)

    print(f"   ✓ API key found (ends with: ...{api_key[-4:]})")

    # 2. Initialize OpenAI client
    print("\n[2/6] Initializing OpenAI client...")
    try:
        client = openai.OpenAI(api_key=api_key)
        print("   ✓ Client initialized")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        sys.exit(1)

    # 3. Load sentences
    print(f"\n[3/6] Loading sentences (limit: {args.limit})...")
    if not INPUT_CSV.exists():
        print(f"   ❌ ERROR: Input file not found: {INPUT_CSV}")
        sys.exit(1)

    sentences = load_sentences(INPUT_CSV, limit=args.limit)
    print(f"   ✓ Loaded {len(sentences)} sentences")

    # Load existing translations
    existing_translations = load_existing_translations(OUTPUT_CSV)
    if existing_translations:
        print(f"   ✓ Found {len(existing_translations)} existing translations")
        # Pre-populate existing translations
        for sentence in sentences:
            if sentence['id'] in existing_translations:
                sentence['english_translation'] = existing_translations[sentence['id']]
            else:
                sentence['english_translation'] = None
    else:
        print(f"   ℹ No existing translations found (starting fresh)")
        for sentence in sentences:
            sentence['english_translation'] = None

    # Count how many need translation
    needs_translation = [s for s in sentences if not s['english_translation']]
    already_translated = len(sentences) - len(needs_translation)

    print(f"   ✓ Already translated: {already_translated}")
    print(f"   ✓ Need translation:   {len(needs_translation)}")

    if len(needs_translation) == 0:
        print("\n✓ All sentences in this range already translated!")
        print(f"   Output file: {OUTPUT_CSV}")
        sys.exit(0)

    # Show sample
    print("\n   Sample sentences to translate:")
    for i, s in enumerate(needs_translation[:3], 1):
        print(f"      {i}. {s['sentence'][:50]}{'...' if len(s['sentence']) > 50 else ''}")

    # 4. Estimate cost (only for sentences that need translation)
    print(f"\n[4/6] Estimating cost...")
    if len(needs_translation) > 0:
        avg_chinese_chars = sum(len(s['sentence']) for s in needs_translation) / len(needs_translation)
        estimated_input_tokens = len(needs_translation) * (avg_chinese_chars * 1.5 + 100)  # +100 for prompt
        estimated_output_tokens = len(needs_translation) * 20  # ~20 tokens per translation
        estimated_cost = calculate_cost(estimated_input_tokens, estimated_output_tokens)

        print(f"   Estimated input tokens:  {estimated_input_tokens:,.0f}")
        print(f"   Estimated output tokens: {estimated_output_tokens:,.0f}")
        print(f"   Estimated cost:          ${estimated_cost:.4f}")
    else:
        estimated_cost = 0
        print(f"   No new translations needed - cost: $0.00")

    # 5. Translate in batches
    print(f"\n[5/6] Translating {len(needs_translation)} sentences...")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Temperature: {TEMPERATURE}")
    print("   " + "-" * 66)

    start_time = time.time()
    total_stats = {
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0,
        'cost': 0,
        'successful': 0,
        'failed': 0,
        'validation_failed': 0,
        'skipped': already_translated
    }

    # Process in batches (only sentences that need translation)
    batch_num = 0
    i = 0
    while i < len(needs_translation):
        # Adaptive batch size: reduce for very long sentences
        batch_size = BATCH_SIZE

        # Check if next sentence is very long (>200 chars)
        if i < len(needs_translation) and len(needs_translation[i]['sentence']) > 200:
            batch_size = min(5, BATCH_SIZE)  # Reduce to 5 for long sentences
            print(f"\n   ⚠ Long sentence detected ({len(needs_translation[i]['sentence'])} chars), using smaller batch size ({batch_size})")

        batch = needs_translation[i:i + batch_size]
        batch_num += 1

        print(f"\n   Batch {batch_num} ({len(batch)} sentences)...", end=' ', flush=True)
        i += len(batch)

        # Prepare batch for translation
        batch_input = [(s['id'], s['sentence']) for s in batch]

        # Translate with retry for rate limits
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            translations, stats = translate_batch(client, batch_input)

            # Break on success or permanent failure
            if stats['status'] in ['success', 'failed']:
                break

            # Retry on rate limit or timeout
            if stats['status'] in ['rate_limited', 'timeout']:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"      Retrying ({retry_count}/{max_retries})...", end=' ', flush=True)
                else:
                    print(f"      Max retries reached, skipping batch")
                    break

        if stats['status'] == 'success':
            print(f"✓ (${stats['cost']:.4f})")
            # Debug: show first translation
            if translations and translations[0]:
                print(f"      Sample: {batch[0]['sentence'][:30]} → {translations[0][:50]}")

            # Validate and assign translations
            for j, (sentence, translation) in enumerate(zip(batch, translations)):
                is_valid, error_msg = validate_translation(sentence['sentence'], translation)

                if is_valid:
                    sentence['english_translation'] = translation
                    total_stats['successful'] += 1
                else:
                    warning_msg = f"Validation failed for sentence {sentence['id']}: {error_msg}"
                    print(f"      ⚠ Warning: {warning_msg}")
                    logger.warning("Sentence %s: %s | Chinese: %s | Translation: %s",
                                 sentence['id'], error_msg, sentence['sentence'], translation)
                    sentence['english_translation'] = translation  # Keep it anyway for review
                    total_stats['validation_failed'] += 1

            # Update stats
            total_stats['prompt_tokens'] += stats['prompt_tokens']
            total_stats['completion_tokens'] += stats['completion_tokens']
            total_stats['total_tokens'] += stats['total_tokens']
            total_stats['cost'] += stats['cost']
        else:
            error_msg = stats.get('error', 'Unknown error')
            print(f"✗ FAILED")
            logger.error("Batch failed: %s | Sentences: %s",
                        error_msg, [s['id'] for s in batch])
            total_stats['failed'] += len(batch)
            # Assign empty translations
            for sentence in batch:
                sentence['english_translation'] = ''
                logger.error("Sentence %s failed: %s", sentence['id'], sentence['sentence'])

        # Save progress after each batch (in case of interruption)
        save_translated_sentences(sentences, OUTPUT_CSV)

        # Delay to respect rate limits
        # For Tier 1 (500 RPM), we need at least 0.12s between requests
        # Using 2 seconds to be very safe and avoid hitting limits
        if i < len(needs_translation):
            time.sleep(2.0)

    elapsed_time = time.time() - start_time

    # 6. Save results
    print(f"\n[6/6] Saving results...")
    save_translated_sentences(sentences, OUTPUT_CSV)
    print(f"   ✓ Saved to: {OUTPUT_CSV}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTranslation Results:")
    print(f"   Total sentences:       {len(sentences)}")
    print(f"   Already translated:    {total_stats['skipped']} ⊙")
    print(f"   Newly translated:      {total_stats['successful']} ✓")
    print(f"   Validation warnings:   {total_stats['validation_failed']} ⚠")
    print(f"   Failed:                {total_stats['failed']} ✗")

    print(f"\nToken Usage:")
    print(f"   Input tokens:          {total_stats['prompt_tokens']:,}")
    print(f"   Output tokens:         {total_stats['completion_tokens']:,}")
    print(f"   Total tokens:          {total_stats['total_tokens']:,}")

    print(f"\nCost:")
    print(f"   Actual cost:           ${total_stats['cost']:.4f}")
    print(f"   Estimated cost:        ${estimated_cost:.4f}")
    print(f"   Difference:            ${abs(total_stats['cost'] - estimated_cost):.4f}")

    print(f"\nPerformance:")
    print(f"   Time elapsed:          {elapsed_time:.1f} seconds")
    print(f"   Sentences per second:  {len(sentences) / elapsed_time:.1f}")

    # Show sample translations
    print(f"\n" + "=" * 70)
    print("SAMPLE TRANSLATIONS (first 5)")
    print("=" * 70)
    for i, s in enumerate(sentences[:5], 1):
        print(f"\n{i}. Chinese:  {s['sentence']}")
        print(f"   English:  {s['english_translation']}")
        is_valid, msg = validate_translation(s['sentence'], s['english_translation'])
        if not is_valid:
            print(f"   ⚠ Warning: {msg}")

    # Extrapolate to full dataset
    if len(sentences) < 79704:
        print(f"\n" + "=" * 70)
        print("EXTRAPOLATION TO FULL DATASET (79,704 sentences)")
        print("=" * 70)

        ratio = 79704 / len(sentences)
        full_cost = total_stats['cost'] * ratio
        full_time_seconds = elapsed_time * ratio
        full_time_minutes = full_time_seconds / 60

        print(f"\nEstimated for full dataset:")
        print(f"   Total cost:            ${full_cost:.2f}")
        print(f"   Total time:            {full_time_minutes:.1f} minutes ({full_time_seconds/60/60:.1f} hours)")
        print(f"   Input tokens:          {total_stats['prompt_tokens'] * ratio:,.0f}")
        print(f"   Output tokens:         {total_stats['completion_tokens'] * ratio:,.0f}")

    print("\n" + "=" * 70)
    print("✓ Test complete!")
    print("=" * 70)

    # Log summary
    logger.info("Translation complete - Total: %d, Successful: %d, Failed: %d, Warnings: %d",
                len(sentences), total_stats['successful'], total_stats['failed'],
                total_stats['validation_failed'])

    print(f"\nOutput:")
    print(f"   ✓ Translations: {OUTPUT_CSV}")
    print(f"   ✓ Log file:     {LOG_FILE}")

    if total_stats['validation_failed'] > 0 or total_stats['failed'] > 0:
        print(f"\n⚠ Check log file for warnings and errors:")
        print(f"   {LOG_FILE}")

    print(f"\nNext steps:")
    print(f"   1. Review sample translations above")
    print(f"   2. Check output file: {OUTPUT_CSV}")
    print(f"   3. Review log for any issues: {LOG_FILE}")
    print(f"   4. If quality looks good, run with larger --limit")
    print(f"   5. Suggested sequence: 10 → 100 → 1000 → full dataset")


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
