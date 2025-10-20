/**
 * Word mastery tracking and spaced repetition logic
 */

import { db, type WordMastery, type SentenceProgress } from './db';

// Learning algorithm constants
const ALPHA = 0.2;              // Learning rate for mastery score
const BETA = 0.15;              // EWMA smoothing factor
const INITIAL_S = 0.3;          // Starting mastery score
const INITIAL_STABILITY = 1.0;  // Initial stability (days)
const STABILITY_UP = 1.4;       // Correct answer multiplier
const STABILITY_DOWN = 0.7;     // Wrong answer multiplier
const MIN_STABILITY = 0.5;      // Minimum stability bound (days)
const MAX_STABILITY = 60;       // Maximum stability bound (days)

/**
 * Initialize a new word record with default values
 */
function initializeWord(char_id: number): WordMastery {
  const now = Date.now();

  return {
    char_id,
    s: INITIAL_S,
    stability_days: INITIAL_STABILITY,
    next_review_ts: now + INITIAL_STABILITY * 86400000, // ms
    last_seen_ts: now,
    n_attempts: 0,
    n_correct: 0,
    streak_correct: 0,
    ewma_success: INITIAL_S, // Start with initial mastery as success rate
    last_outcome: 'wrong', // Conservative default
    introduced_ts: now,
  };
}

/**
 * Update mastery score after a single attempt
 * Uses exponential smoothing: s ← s + α·(e−s)
 */
function updateMastery(
  current: WordMastery,
  correct: boolean
): WordMastery {
  const now = Date.now();
  const e = correct ? 1 : 0;

  // Update mastery score with exponential smoothing
  const newS = Math.max(0, Math.min(1, current.s + ALPHA * (e - current.s)));

  // Update stability with bounds
  const unboundedStability = correct
    ? current.stability_days * STABILITY_UP
    : current.stability_days * STABILITY_DOWN;
  const newStability = Math.max(
    MIN_STABILITY,
    Math.min(MAX_STABILITY, unboundedStability)
  );

  // Update streak
  const newStreak = correct ? current.streak_correct + 1 : 0;

  // Update EWMA success rate
  // For first attempt (n_attempts === 0), set directly to outcome
  // For subsequent attempts, use exponential smoothing
  const newEwmaSuccess =
    current.n_attempts === 0
      ? e
      : Math.max(
          0,
          Math.min(1, current.ewma_success + BETA * (e - current.ewma_success))
        );

  return {
    ...current,
    s: newS,
    stability_days: newStability,
    next_review_ts: now + newStability * 86400000,
    last_seen_ts: now,
    n_attempts: current.n_attempts + 1,
    n_correct: current.n_correct + (correct ? 1 : 0),
    streak_correct: newStreak,
    ewma_success: newEwmaSuccess,
    last_outcome: correct ? 'correct' : 'wrong',
  };
}

/**
 * Record attempt results for a sentence
 * Handles duplicate characters by using worst outcome per unique char
 *
 * @param attempts - Array of {char_id, correct} for each character attempted
 */
export async function recordSentenceAttempt(
  attempts: Array<{ char_id: number; correct: boolean }>
): Promise<void> {
  try {
    // Group by char_id and keep worst outcome
    const uniqueAttempts = new Map<number, boolean>();

    for (const { char_id, correct } of attempts) {
      const existing = uniqueAttempts.get(char_id);
      if (existing === undefined) {
        uniqueAttempts.set(char_id, correct);
      } else {
        // Keep worst outcome (false beats true)
        uniqueAttempts.set(char_id, existing && correct);
      }
    }

    // Update each unique character in a transaction
    await db.transaction('rw', db.words, async () => {
      for (const [char_id, correct] of uniqueAttempts.entries()) {
        // Fetch existing record or create new one
        let word = await db.words.get(char_id);

        if (!word) {
          word = initializeWord(char_id);
        }

        // Apply mastery update
        const updated = updateMastery(word, correct);

        // Save back to database
        await db.words.put(updated);
      }
    });

    console.log(`Recorded ${uniqueAttempts.size} word attempts`);
  } catch (error) {
    // Silent error handling - don't block user progress
    console.error('Failed to record sentence attempt:', error);
  }
}

/**
 * Record sentence-level progress
 * Tracks how often a sentence has been practiced and overall pass/fail rate
 *
 * @param sid - Sentence ID from sentences.json
 * @param passed - Whether user got all Chinese characters correct on first attempt
 */
export async function recordSentenceProgress(
  sid: number,
  passed: boolean
): Promise<void> {
  try {
    const now = Date.now();

    // Fetch existing record or create new one
    let sentence = await db.sentences.get(sid);

    if (!sentence) {
      // First time seeing this sentence
      sentence = {
        sid,
        introduced_ts: now,
        last_seen_ts: now,
        seen_count: 0,
        pass_count: 0,
        last_outcome: 'fail', // Will be updated below
      };
    }

    // Update record
    const updated: SentenceProgress = {
      ...sentence,
      last_seen_ts: now,
      seen_count: sentence.seen_count + 1,
      pass_count: sentence.pass_count + (passed ? 1 : 0),
      last_outcome: passed ? 'pass' : 'fail',
    };

    // Save to database
    await db.sentences.put(updated);

    console.log(`Recorded sentence ${sid} progress: ${passed ? 'pass' : 'fail'}`);
  } catch (error) {
    // Silent error handling - don't block user progress
    console.error('Failed to record sentence progress:', error);
  }
}

/**
 * Get mastery data for a specific character
 */
export async function getWordMastery(char_id: number): Promise<WordMastery | undefined> {
  return await db.words.get(char_id);
}

/**
 * Get words due for review (next_review_ts <= now)
 */
export async function getWordsForReview(): Promise<WordMastery[]> {
  const now = Date.now();
  return await db.words.where('next_review_ts').belowOrEqual(now).toArray();
}
