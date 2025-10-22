/**
 * Next Sentence Selection (NSS) - Adaptive sentence picker
 *
 * Selects practice sentences based on character mastery, difficulty (k unknowns),
 * and spaced repetition. Samples 300 candidates, scores them, returns top 10.
 *
 * Key concepts:
 * - k: Number of "unknown" characters (s < θ_known) in a sentence
 * - Scoring: base_gain + novelty - pass_penalty - k_penalty
 * - Batching: Prefetch 10 sentences from pool of 300 candidates
 *
 * Config: selection-config.ts
 * Details: PROJECT_BRIEF.md "How Does NSS Work"
 */

import { db, type SentenceQueue, type SentenceProgress, type WordMastery } from './db';
import { SELECTION_CONFIG } from './selection-config';
import type { Sentence, HskFilter } from './types';
import { nssLog, nssWarn, nssError } from './logger';
import { getCharId } from './characters';

const INITIAL_S = 0.3;  // From mastery.ts

type ScriptFilter = 'simplified' | 'traditional' | 'mixed';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Parse HSK filter to get array of included levels
 * Examples:
 *   "1" → ["1"]
 *   "1-3" → ["1", "2", "3"]
 *   "1-6" → ["1", "2", "3", "4", "5", "6"]
 *   "1-9" → ["1", "2", "3", "4", "5", "6", "7-9"]
 *   "1-beyond" → ["1", "2", "3", "4", "5", "6", "7-9", "beyond-hsk"]
 */
function parseHskFilter(hskFilter: HskFilter): string[] {
  // Map filter to included levels
  const filterMap: Record<HskFilter, string[]> = {
    '1': ['1'],
    '1-2': ['1', '2'],
    '1-3': ['1', '2', '3'],
    '1-4': ['1', '2', '3', '4'],
    '1-5': ['1', '2', '3', '4', '5'],
    '1-6': ['1', '2', '3', '4', '5', '6'],
    '1-9': ['1', '2', '3', '4', '5', '6', '7-9'],
    '1-beyond': ['1', '2', '3', '4', '5', '6', '7-9', 'beyond-hsk']
  };

  return filterMap[hskFilter];
}

/**
 * Count how many words are currently due for review
 */
export async function countDueWords(now: number): Promise<number> {
  const dueWords = await db.words.where('next_review_ts').belowOrEqual(now).count();
  return dueWords;
}

/**
 * Calculate average word mastery across all learned words
 * Used to determine dynamic k_cap during cold start
 */
async function getAverageMastery(): Promise<number> {
  const allWords = await db.words.toArray();

  if (allWords.length === 0) {
    return INITIAL_S;  // Cold start - no words learned yet
  }

  const totalMastery = allWords.reduce((sum, word) => sum + word.s, 0);
  return totalMastery / allWords.length;
}

/**
 * Get detailed mastery statistics for logging
 */
async function getMasteryStats(): Promise<{
  total_words: number;
  avg_s: number;
  min_s: number;
  max_s: number;
  p25_s: number;
  p50_s: number;
  p75_s: number;
}> {
  const allWords = await db.words.toArray();

  if (allWords.length === 0) {
    return {
      total_words: 0,
      avg_s: INITIAL_S,
      min_s: INITIAL_S,
      max_s: INITIAL_S,
      p25_s: INITIAL_S,
      p50_s: INITIAL_S,
      p75_s: INITIAL_S
    };
  }

  const sValues = allWords.map(w => w.s).sort((a, b) => a - b);
  const avg = sValues.reduce((sum, s) => sum + s, 0) / sValues.length;

  return {
    total_words: allWords.length,
    avg_s: avg,
    min_s: sValues[0],
    max_s: sValues[sValues.length - 1],
    p25_s: sValues[Math.floor(sValues.length * 0.25)],
    p50_s: sValues[Math.floor(sValues.length * 0.5)],
    p75_s: sValues[Math.floor(sValues.length * 0.75)]
  };
}

/**
 * Get dynamic k_cap based on current average mastery level
 * Prevents overwhelming sentences during cold start
 */
async function getDynamicKCap(): Promise<number | null> {
  const avgMastery = await getAverageMastery();

  const { k_cap_by_mastery } = SELECTION_CONFIG;

  // Check thresholds from lowest to highest
  if (avgMastery < k_cap_by_mastery.cold_start.threshold) {
    return k_cap_by_mastery.cold_start.k_cap;
  } else if (avgMastery < k_cap_by_mastery.early.threshold) {
    return k_cap_by_mastery.early.k_cap;
  } else if (avgMastery < k_cap_by_mastery.intermediate.threshold) {
    return k_cap_by_mastery.intermediate.k_cap;
  } else {
    return k_cap_by_mastery.advanced.k_cap;  // null = no cap
  }
}

/**
 * Get difficulty band (k_min, k_max) based on review backlog
 */
export function getDifficultyBand(dueWords: number): { k_min: number; k_max: number } {
  if (dueWords > SELECTION_CONFIG.due_cap) {
    // High backlog - tighten difficulty to focus on review
    return {
      k_min: SELECTION_CONFIG.k_min_backlog,
      k_max: SELECTION_CONFIG.k_max_backlog
    };
  }

  // Normal difficulty
  return {
    k_min: SELECTION_CONFIG.k_min,
    k_max: SELECTION_CONFIG.k_max
  };
}

/**
 * Calculate hours since sentence was last seen
 */
export function hoursSinceSeen(
  sentenceState: SentenceProgress | undefined,
  now: number
): number {
  if (!sentenceState) {
    // Never seen - return max cap
    return SELECTION_CONFIG.max_novelty_hours;
  }

  const ms_since = now - sentenceState.last_seen_ts;
  const hours = ms_since / 3600000;

  // Cap at max_novelty_hours
  return Math.min(hours, SELECTION_CONFIG.max_novelty_hours);
}

/**
 * Check if sentence passes cooldown filter
 */
function passesCooldown(
  sentenceState: SentenceProgress | undefined,
  now: number,
  ignoreCooldown: boolean = false
): boolean {
  if (ignoreCooldown) return true;
  if (!sentenceState) return true;  // Never seen = no cooldown

  const ms_since = now - sentenceState.last_seen_ts;
  const cooldown_ms = SELECTION_CONFIG.cooldown_minutes * 60000;

  return ms_since >= cooldown_ms;
}

/**
 * Check if sentence should be skipped (mastered)
 */
function shouldSkip(
  sentenceState: SentenceProgress | undefined,
  ignoreSkip: boolean = false
): boolean {
  if (ignoreSkip) return false;
  if (!sentenceState) return false;  // Never seen = don't skip

  return (
    sentenceState.ewma_pass >= SELECTION_CONFIG.ewma_skip_threshold &&
    sentenceState.seen_count >= SELECTION_CONFIG.min_seen_for_skip
  );
}

/**
 * Filter sentences by script type and eligibility
 */
export async function getEligibleSentences(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter,
  now: number,
  options: {
    ignoreCooldown?: boolean;
    ignoreSkip?: boolean;
  } = {}
): Promise<Sentence[]> {
  // Step 1: Filter by script type
  let filtered = allSentences.filter(s => {
    // Always exclude ambiguous
    if (s.script_type === 'ambiguous') return false;

    if (scriptFilter === 'simplified') {
      return s.script_type === 'simplified' || s.script_type === 'neutral';
    } else if (scriptFilter === 'traditional') {
      return s.script_type === 'traditional' || s.script_type === 'neutral';
    } else {  // mixed
      return true;
    }
  });

  // Fallback: if no sentences match script filter, use all non-ambiguous
  if (filtered.length === 0) {
    nssWarn('No sentences for script filter, using all non-ambiguous');
    filtered = allSentences.filter(s => s.script_type !== 'ambiguous');
  }

  // Step 1.5: Filter by HSK level
  const allowedHskLevels = parseHskFilter(hskFilter);
  const hskFiltered = filtered.filter(s => {
    // If sentence has no HSK level, exclude it (we decided to ignore unclassified sentences)
    if (!s.hskLevel) return false;

    // Check if sentence's HSK level is in the allowed set
    return allowedHskLevels.includes(s.hskLevel);
  });

  // Use HSK filtered results (or fall back to script-filtered if HSK filtering removed everything)
  if (hskFiltered.length === 0) {
    nssWarn('No sentences for HSK filter, using script-filtered sentences', {
      hsk_filter: hskFilter,
      script_filtered_count: filtered.length
    });
    filtered = filtered;  // Keep script-filtered sentences as fallback
  } else {
    filtered = hskFiltered;
  }

  // Step 2: Filter by cooldown and mastery skip
  const eligible: Sentence[] = [];

  for (const sentence of filtered) {
    const state = await db.sentences.get(sentence.id);

    // Check cooldown
    if (!passesCooldown(state, now, options.ignoreCooldown)) {
      continue;
    }

    // Check mastery skip
    if (shouldSkip(state, options.ignoreSkip)) {
      continue;
    }

    eligible.push(sentence);
  }

  return eligible;
}

/**
 * Shuffle array in place (Fisher-Yates)
 */
function shuffle<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// ============================================================================
// SCORING
// ============================================================================

interface ScoredSentence {
  sid: number;
  score: number;
  k: number;  // Number of unknown words
  last_seen_ts: number;
}

/**
 * Helper to count unknowns in a sentence (used for rejection tracking)
 */
async function countUnknowns(sentence: Sentence, θ_known: number): Promise<number> {
  let count = 0;

  for (const char of sentence.chars) {
    if (!char.pinyin) continue;

    const char_id = getCharId(char.char);
    if (char_id === null) continue;

    const wordMastery = await db.words.get(char_id);
    const s = wordMastery?.s ?? INITIAL_S;

    if (s < θ_known) {
      count++;
    }
  }

  return count;
}

/**
 * Score a single sentence based on word mastery, novelty, and difficulty
 */
export async function scoreSentence(
  sentence: Sentence,
  k_min: number,
  k_max: number,
  now: number,
  options: {
    θ_known?: number;
    k_cap?: number | null;
  } = {}
): Promise<ScoredSentence | null> {
  const θ_known = options.θ_known ?? SELECTION_CONFIG.θ_known;
  const k_cap = options.k_cap !== undefined ? options.k_cap : await getDynamicKCap();

  // Step 1: Identify unknown words
  const unknowns: { char_id: number; s: number; overdue: boolean }[] = [];

  for (const char of sentence.chars) {
    // Skip non-Chinese characters (punctuation, etc.)
    if (!char.pinyin) continue;

    // Look up character ID
    const char_id = getCharId(char.char);
    if (char_id === null) continue;

    const wordMastery = await db.words.get(char_id);
    const s = wordMastery?.s ?? INITIAL_S;

    if (s < θ_known) {
      const overdue = wordMastery
        ? now >= wordMastery.next_review_ts
        : false;

      unknowns.push({ char_id, s, overdue });
    }
  }

  const k = unknowns.length;

  // Reject if no unknowns (nothing to learn)
  if (k === 0) {
    return null;
  }

  // Apply dynamic k_cap to prevent overwhelming sentences
  if (k_cap !== null && k > k_cap) {
    return null;
  }

  // Step 2: Calculate base gain (sum of learning potential)
  let base_gain = 0;
  for (const { s, overdue } of unknowns) {
    let gain = (1 - s);

    // Boost overdue words (SRS priority)
    if (overdue) {
      gain *= SELECTION_CONFIG.overdue_boost;
    }

    base_gain += gain;
  }

  // Step 3: Calculate novelty bonus
  const sentenceState = await db.sentences.get(sentence.id);
  const hours = hoursSinceSeen(sentenceState, now);
  const novelty = SELECTION_CONFIG.novelty_weight * Math.log(1 + hours);

  // Step 4: Calculate sentence mastery penalty
  const pass_penalty = SELECTION_CONFIG.pass_penalty_weight * (sentenceState?.ewma_pass ?? 0);

  // Step 5: Calculate difficulty penalty (if outside k_band)
  let k_penalty = 0;
  if (k < k_min || k > k_max) {
    const nearest = k < k_min ? k_min : k_max;
    k_penalty = SELECTION_CONFIG.k_penalty_weight * Math.abs(k - nearest);
  }

  // Step 6: Final score
  const score = base_gain + novelty - pass_penalty - k_penalty;

  return {
    sid: sentence.id,
    score,
    k,
    last_seen_ts: sentenceState?.last_seen_ts ?? 0
  };
}

/**
 * Score multiple sentences
 */
async function scoreCandidates(
  sentences: Sentence[],
  k_min: number,
  k_max: number,
  now: number,
  options: {
    θ_known?: number;
    k_cap?: number | null;
  } = {}
): Promise<ScoredSentence[]> {
  const scored: ScoredSentence[] = [];
  let rejectedNoUnknowns = 0;
  let rejectedKCap = 0;

  for (const sentence of sentences) {
    const result = await scoreSentence(sentence, k_min, k_max, now, options);
    if (result) {
      scored.push(result);
    } else {
      // Track why it was rejected
      // Need to re-check to determine reason (not ideal but simple)
      const unknownCount = await countUnknowns(sentence, options.θ_known ?? SELECTION_CONFIG.θ_known);
      if (unknownCount === 0) {
        rejectedNoUnknowns++;
      } else {
        const k_cap = options.k_cap !== undefined ? options.k_cap : await getDynamicKCap();
        if (k_cap !== null && unknownCount > k_cap) {
          rejectedKCap++;
        }
      }
    }
  }

  // Log rejection statistics
  if (rejectedNoUnknowns > 0 || rejectedKCap > 0) {
    nssLog('Scoring rejections', {
      total_candidates: sentences.length,
      scored: scored.length,
      rejected_no_unknowns: rejectedNoUnknowns,
      rejected_k_cap: rejectedKCap,
      rejection_rate: ((rejectedNoUnknowns + rejectedKCap) / sentences.length * 100).toFixed(1) + '%'
    });
  }

  return scored;
}

/**
 * Sort scored sentences by score (desc), then k (desc), then last_seen_ts (asc)
 */
function sortScored(scored: ScoredSentence[]): ScoredSentence[] {
  return scored.sort((a, b) => {
    // Primary: score descending
    if (a.score !== b.score) return b.score - a.score;

    // Secondary: k descending (prefer more unknowns within same score)
    if (a.k !== b.k) return b.k - a.k;

    // Tertiary: last_seen_ts ascending (prefer older)
    return a.last_seen_ts - b.last_seen_ts;
  });
}

/**
 * Take top N scored sentences (no duplicates)
 */
function takeTopN(scored: ScoredSentence[], n: number): ScoredSentence[] {
  const sorted = sortScored(scored);
  return sorted.slice(0, n);
}

// ============================================================================
// FALLBACK CASCADE
// ============================================================================

/**
 * Progressive fallback to find sentences when normal criteria fail
 */
async function applyFallbacks(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter,
  now: number,
  attempt: number
): Promise<{ pool: Sentence[]; k_min: number; k_max: number; θ_known: number }> {
  let { k_min, k_max } = getDifficultyBand(await countDueWords(now));
  let θ_known: number = SELECTION_CONFIG.θ_known;

  switch (attempt) {
    case 1:
      // Relax k_band
      nssWarn('Fallback 1: Relaxing k_band to [1, 6]');
      k_min = 1;
      k_max = 6;
      break;

    case 2:
      // Ignore cooldown
      nssWarn('Fallback 2: Ignoring cooldown');
      k_min = 1;
      k_max = 6;
      break;

    case 3:
      // Lower θ_known
      nssWarn('Fallback 3: Lowering θ_known to 0.65');
      k_min = 1;
      k_max = 6;
      θ_known = 0.65;
      break;

    case 4:
      // Drop ewma skip
      nssWarn('Fallback 4: Dropping ewma skip filter');
      k_min = 1;
      k_max = 6;
      θ_known = 0.65;
      break;

    default:
      // Absolute fallback: random selection
      nssError('Fallback 5: All strategies exhausted, using random selection');
      break;
  }

  const pool = await getEligibleSentences(allSentences, scriptFilter, hskFilter, now, {
    ignoreCooldown: attempt >= 2,
    ignoreSkip: attempt >= 4
  });

  return { pool, k_min, k_max, θ_known };
}

// ============================================================================
// BATCH GENERATION
// ============================================================================

/**
 * Generate a batch of sentences for practice
 */
export async function generateSentenceBatch(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter
): Promise<SentenceQueue> {
  const now = Date.now();

  if (allSentences.length === 0) {
    throw new Error('[NSS] No sentences available in corpus');
  }

  // Step 1: Get difficulty band based on review backlog
  const dueWords = await countDueWords(now);
  let { k_min, k_max } = getDifficultyBand(dueWords);

  // Get dynamic k_cap for cold start protection
  const k_cap = await getDynamicKCap();
  const avgMastery = await getAverageMastery();

  // Increment batch counter for periodic stats
  batchCounter++;

  nssLog('Starting batch generation', {
    batch_num: batchCounter,
    due_words: dueWords,
    k_band: [k_min, k_max],
    k_cap: k_cap ?? 'none',
    avg_mastery: avgMastery.toFixed(3),
    hsk_filter: hskFilter
  });

  // Every 10 batches, log detailed mastery stats
  if (batchCounter % 10 === 0) {
    const masteryStats = await getMasteryStats();
    nssLog('📊 Periodic Mastery Stats', {
      total_words_tracked: masteryStats.total_words,
      mastery_distribution: {
        min: masteryStats.min_s.toFixed(3),
        p25: masteryStats.p25_s.toFixed(3),
        p50: masteryStats.p50_s.toFixed(3),
        p75: masteryStats.p75_s.toFixed(3),
        max: masteryStats.max_s.toFixed(3),
        avg: masteryStats.avg_s.toFixed(3)
      },
      current_k_cap: k_cap ?? 'none'
    });
  }

  // Step 2: Build candidate pool
  let eligible = await getEligibleSentences(allSentences, scriptFilter, hskFilter, now);

  // Sample pool (or use all if less than pool_sample_size)
  const poolSize = Math.min(eligible.length, SELECTION_CONFIG.pool_sample_size);
  const pool = shuffle(eligible).slice(0, poolSize);

  // Step 3: Score candidates
  let scored = await scoreCandidates(pool, k_min, k_max, now, { k_cap });

  // Step 4: Apply fallbacks if needed
  let fallbackAttempt = 0;
  let θ_known: number = SELECTION_CONFIG.θ_known;

  while (scored.length < SELECTION_CONFIG.batch_size && fallbackAttempt < 5) {
    fallbackAttempt++;
    const fallback = await applyFallbacks(allSentences, scriptFilter, hskFilter, now, fallbackAttempt);

    k_min = fallback.k_min;
    k_max = fallback.k_max;
    θ_known = fallback.θ_known;

    if (fallbackAttempt === 5) {
      // Absolute fallback: random selection
      scored = shuffle(allSentences)
        .filter(s => s.script_type !== 'ambiguous')
        .slice(0, SELECTION_CONFIG.batch_size)
        .map(s => ({
          sid: s.id,
          score: 0,
          k: 0,
          last_seen_ts: 0
        }));
      break;
    }

    // Resample and rescore with fallback criteria
    const fallbackPool = shuffle(fallback.pool).slice(0, SELECTION_CONFIG.pool_sample_size);
    scored = await scoreCandidates(fallbackPool, k_min, k_max, now, { θ_known, k_cap });
    nssLog('Fallback attempt', { attempt: fallbackAttempt, scored_count: scored.length });
  }

  // Step 5: Select top N
  const selected = takeTopN(scored, SELECTION_CONFIG.batch_size);

  // Shuffle selected to mix difficulty
  const shuffled = shuffle(selected);

  // Calculate k distribution histogram
  const kValues = shuffled.map(s => s.k).sort((a, b) => a - b);
  const kHistogram: Record<number, number> = {};
  kValues.forEach(k => {
    kHistogram[k] = (kHistogram[k] || 0) + 1;
  });

  nssLog('Generated batch', {
    size: shuffled.length,
    k: {
      avg: (shuffled.reduce((sum, s) => sum + s.k, 0) / shuffled.length).toFixed(1),
      min: Math.min(...kValues),
      max: Math.max(...kValues),
      distribution: kHistogram
    },
    score: {
      avg: (shuffled.reduce((sum, s) => sum + s.score, 0) / shuffled.length).toFixed(2),
      range: [
        Math.min(...shuffled.map(s => s.score)).toFixed(2),
        Math.max(...shuffled.map(s => s.score)).toFixed(2)
      ]
    },
    fallbacks: fallbackAttempt
  });

  // Step 6: Create queue
  const queue: SentenceQueue = {
    id: 1,  // Singleton
    sentences: shuffled.map(s => s.sid),
    current_index: 0,
    generated_at: now,
    script_filter: scriptFilter,
    hsk_filter: hskFilter
  };

  return queue;
}

// ============================================================================
// PUBLIC API
// ============================================================================

// Prefetch worker
let nextBatchPromise: Promise<SentenceQueue> | null = null;

// Batch counter for periodic stats logging
let batchCounter = 0;

/**
 * Get the next sentence ID for practice
 *
 * Main entry point for adaptive sentence selection.
 * Manages queue, prefetching, and regeneration.
 */
export async function getNextSentence(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter
): Promise<number> {
  // Step 1: Load current queue
  let queue = await db.queue.get(1);

  // Step 2: Invalidate if script filter or HSK filter changed
  if (queue && (queue.script_filter !== scriptFilter || queue.hsk_filter !== hskFilter)) {
    nssLog('Filter changed, invalidating queue', {
      script_changed: queue.script_filter !== scriptFilter,
      hsk_changed: queue.hsk_filter !== hskFilter
    });
    queue = undefined;
    nextBatchPromise = null;
  }

  // Step 3: If no queue or exhausted, generate/use prefetched
  if (!queue || queue.current_index >= queue.sentences.length) {
    if (nextBatchPromise) {
      nssLog('Queue exhausted, awaiting prefetched batch');
      queue = await nextBatchPromise;
      nextBatchPromise = null;
    } else {
      nssLog('⚠️ Queue exhausted, no prefetch available - generating batch (blocking)');
      queue = await generateSentenceBatch(allSentences, scriptFilter, hskFilter);
    }

    await db.queue.put(queue);
  }

  // Step 4: Trigger prefetch if near end
  if (queue.current_index >= queue.sentences.length - SELECTION_CONFIG.prefetch_threshold) {
    if (!nextBatchPromise) {
      nssLog('Prefetching next batch (async)', {
        current_index: queue.current_index,
        remaining: queue.sentences.length - queue.current_index
      });
      nextBatchPromise = generateSentenceBatch(allSentences, scriptFilter, hskFilter);
      // Don't await - let it run in background
    }
  }

  // Step 5: Get current sentence
  const sid = queue.sentences[queue.current_index];
  const position = queue.current_index + 1; // 1-indexed for readability
  const remaining = queue.sentences.length - queue.current_index - 1;

  queue.current_index++;
  await db.queue.put(queue);

  // Only log every 5 sentences to reduce noise
  if (position % 5 === 1 || remaining === 0) {
    nssLog('Selected sentence', {
      position: `${position}/${queue.sentences.length}`,
      remaining
    });
  }

  return sid;
}
