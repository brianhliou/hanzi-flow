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

type ScriptFilter = 'simplified' | 'traditional';

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
 * Filter sentences by script type and HSK level
 */
export async function getEligibleSentences(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter
): Promise<Sentence[]> {
  const t0 = performance.now();

  // Step 1: Filter by script type
  let filtered = allSentences.filter(s => {
    // Always exclude ambiguous
    if (s.script_type === 'ambiguous') return false;

    if (scriptFilter === 'simplified') {
      return s.script_type === 'simplified' || s.script_type === 'neutral';
    } else if (scriptFilter === 'traditional') {
      return s.script_type === 'traditional' || s.script_type === 'neutral';
    }
    return false;
  });

  const t1 = performance.now();
  nssLog('⏱️  Filter: Script', {
    input: allSentences.length,
    output: filtered.length,
    time_ms: (t1 - t0).toFixed(2)
  });

  // Fallback: if no sentences match script filter, use all non-ambiguous
  if (filtered.length === 0) {
    nssWarn('No sentences for script filter, using all non-ambiguous');
    filtered = allSentences.filter(s => s.script_type !== 'ambiguous');
  }

  // Step 1.5: Filter by HSK level (ONLY for Simplified script)
  // Traditional sentences have no HSK classification, so skip HSK filtering
  if (scriptFilter === 'simplified') {
    const t2 = performance.now();
    const allowedHskLevels = parseHskFilter(hskFilter);
    const hskFiltered = filtered.filter(s => {
      // If sentence has no HSK level, exclude it
      if (!s.hskLevel) return false;

      // Check if sentence's HSK level is in the allowed set
      return allowedHskLevels.includes(s.hskLevel);
    });

    const t3 = performance.now();
    nssLog('⏱️  Filter: HSK', {
      input: filtered.length,
      output: hskFiltered.length,
      time_ms: (t3 - t2).toFixed(2)
    });

    // Use HSK filtered results (or fall back to script-filtered if HSK filtering removed everything)
    if (hskFiltered.length === 0) {
      nssWarn('No sentences for HSK filter, using script-filtered sentences', {
        hsk_filter: hskFilter,
        script_filtered_count: filtered.length
      });
      // Keep script-filtered sentences as fallback
    } else {
      filtered = hskFiltered;
    }
  }
  // For Traditional script: skip HSK filtering entirely (traditional sentences have no HSK levels)

  return filtered;
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
// REFACTORED: BULK LOADING & METADATA
// ============================================================================

interface SentenceMetadata {
  sentence: Sentence;

  // Filter compliance flags
  passesCooldown: boolean;
  passesSkip: boolean;

  // Multi-threshold unknowns
  k_0_6: number;              // unknowns at θ=0.6 (for FB0-3)
  k_0_8: number;              // unknowns at θ=0.8 (for FB4)
  unknowns_0_6: Array<{ char_id: number; s: number; overdue: boolean }>;
  unknowns_0_8: Array<{ char_id: number; s: number; overdue: boolean }>;

  // Reusable data
  sentenceState: SentenceProgress | null;
  last_seen_ts: number;
}

/**
 * Bulk load character mastery for all unique characters in sentences
 * Replaces thousands of individual db.words.get() calls with one bulkGet()
 */
async function bulkLoadCharMastery(
  sentences: Sentence[]
): Promise<Map<number, WordMastery | undefined>> {
  const startTime = performance.now();

  // Extract all unique char_ids
  const charIds = new Set<number>();
  for (const sentence of sentences) {
    for (const char of sentence.chars) {
      if (!char.pinyin) continue;
      const char_id = getCharId(char.char);
      if (char_id !== null) {
        charIds.add(char_id);
      }
    }
  }

  // Bulk load all character mastery
  const charIdArray = Array.from(charIds);
  const masteries = await db.words.bulkGet(charIdArray);

  // Build map
  const map = new Map<number, WordMastery | undefined>();
  for (let i = 0; i < charIdArray.length; i++) {
    map.set(charIdArray[i], masteries[i]);
  }

  const loadTime = performance.now() - startTime;

  nssLog('💾 Bulk Character Load', {
    characters_loaded: map.size,
    time_ms: loadTime.toFixed(2),
    avg_ms_per_char: (loadTime / map.size).toFixed(3)
  });

  return map;
}

/**
 * Compute metadata for all sentences with pre-loaded character mastery
 * Pre-computes k-counts at both thresholds and filter compliance
 */
async function computeAllMetadata(
  sentences: Sentence[],
  charMasteryMap: Map<number, WordMastery | undefined>,
  now: number
): Promise<SentenceMetadata[]> {
  const startTime = performance.now();

  // Bulk load all sentence states
  const sentenceIds = sentences.map(s => s.id);
  const sentenceStates = await db.sentences.bulkGet(sentenceIds);
  const sentenceStateMap = new Map<number, SentenceProgress | undefined>();
  for (let i = 0; i < sentenceIds.length; i++) {
    sentenceStateMap.set(sentenceIds[i], sentenceStates[i]);
  }

  const metadata: SentenceMetadata[] = [];

  for (const sentence of sentences) {
    const state = sentenceStateMap.get(sentence.id);

    // Compute unknowns at both thresholds
    const { unknowns: unknowns_0_6, k: k_0_6 } = computeUnknowns(sentence, charMasteryMap, 0.6, now);
    const { unknowns: unknowns_0_8, k: k_0_8 } = computeUnknowns(sentence, charMasteryMap, 0.8, now);

    // Compute filter compliance
    const passesCooldown = !state || (now - state.last_seen_ts >= SELECTION_CONFIG.cooldown_minutes * 60 * 1000);
    const passesSkip = !state ||
                       state.ewma_pass < SELECTION_CONFIG.ewma_skip_threshold ||
                       state.seen_count < SELECTION_CONFIG.min_seen_for_skip;

    metadata.push({
      sentence,
      passesCooldown,
      passesSkip,
      k_0_6,
      k_0_8,
      unknowns_0_6,
      unknowns_0_8,
      sentenceState: state ?? null,
      last_seen_ts: state?.last_seen_ts ?? 0
    });
  }

  const computeTime = performance.now() - startTime;

  nssLog('🧮 Metadata Computed', {
    sentences_processed: metadata.length,
    time_ms: computeTime.toFixed(2),
    avg_ms_per_sentence: (computeTime / metadata.length).toFixed(3),
    distribution: {
      passes_cooldown: metadata.filter(m => m.passesCooldown).length,
      passes_skip: metadata.filter(m => m.passesSkip).length,
      k_0_6_avg: (metadata.reduce((sum, m) => sum + m.k_0_6, 0) / metadata.length).toFixed(2),
      k_0_8_avg: (metadata.reduce((sum, m) => sum + m.k_0_8, 0) / metadata.length).toFixed(2)
    }
  });

  return metadata;
}

/**
 * Compute unknowns for a sentence at a specific threshold
 * Helper used by computeAllMetadata
 */
function computeUnknowns(
  sentence: Sentence,
  charMasteryMap: Map<number, WordMastery | undefined>,
  θ_known: number,
  now: number
): { unknowns: Array<{ char_id: number; s: number; overdue: boolean }>; k: number } {
  const seenCharIds = new Set<number>();
  const unknowns: Array<{ char_id: number; s: number; overdue: boolean }> = [];

  for (const char of sentence.chars) {
    if (!char.pinyin) continue;

    const char_id = getCharId(char.char);
    if (char_id === null) continue;

    // Skip if already processed (deduplication)
    if (seenCharIds.has(char_id)) continue;
    seenCharIds.add(char_id);

    const wordMastery = charMasteryMap.get(char_id);
    const s = wordMastery?.s ?? INITIAL_S;

    if (s < θ_known) {
      const overdue = wordMastery ? now >= wordMastery.next_review_ts : false;
      unknowns.push({ char_id, s, overdue });
    }
  }

  return { unknowns, k: unknowns.length };
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
 * REFACTORED: Score sentences from pre-computed metadata
 * Replaces scoreCandidates - no DB lookups needed
 */
function scoreFromMetadata(
  metadataList: SentenceMetadata[],
  k_min: number,
  k_max: number,
  now: number,
  useThreshold: 0.6 | 0.8,  // Which threshold to use
  k_cap: number | null
): ScoredSentence[] {
  const scored: ScoredSentence[] = [];

  for (const meta of metadataList) {
    // Choose which unknowns to use based on threshold
    const unknowns = useThreshold === 0.6 ? meta.unknowns_0_6 : meta.unknowns_0_8;
    const k = unknowns.length;

    // Reject if no unknowns
    if (k === 0) {
      continue;
    }

    // Apply k_cap
    if (k_cap !== null && k > k_cap) {
      continue;
    }

    // Calculate base gain
    let base_gain = 0;
    for (const { s, overdue } of unknowns) {
      let gain = (1 - s);
      if (overdue) {
        gain *= SELECTION_CONFIG.overdue_boost;
      }
      base_gain += gain;
    }

    // Calculate novelty bonus
    const hours = hoursSinceSeen(meta.sentenceState ?? undefined, now);
    const novelty = SELECTION_CONFIG.novelty_weight * Math.log(1 + hours);

    // Calculate sentence mastery penalty
    const pass_penalty = SELECTION_CONFIG.pass_penalty_weight * (meta.sentenceState?.ewma_pass ?? 0);

    // Calculate difficulty penalty
    let k_penalty = 0;
    if (k < k_min || k > k_max) {
      const nearest = k < k_min ? k_min : k_max;
      k_penalty = SELECTION_CONFIG.k_penalty_weight * Math.abs(k - nearest);
    }

    // Final score
    const score = base_gain + novelty - pass_penalty - k_penalty;

    scored.push({
      sid: meta.sentence.id,
      score,
      k,
      last_seen_ts: meta.last_seen_ts
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
// BATCH GENERATION
// ============================================================================

/**
 * Generate a batch of sentences for practice (REFACTORED)
 *
 * New approach: Sample once, bulk load, compute metadata, filter (no resample/rescore)
 */
export async function generateSentenceBatch(
  allSentences: Sentence[],
  scriptFilter: ScriptFilter,
  hskFilter: HskFilter
): Promise<SentenceQueue> {
  const startTime = performance.now();
  const now = Date.now();

  if (allSentences.length === 0) {
    throw new Error('[NSS] No sentences available in corpus');
  }

  // Increment batch counter
  batchCounter++;

  nssLog('🚀 NSS Refactor - Starting', {
    batch_num: batchCounter,
    script_filter: scriptFilter,
    hsk_filter: hskFilter,
    corpus_size: allSentences.length
  });

  // Step 1: Get parameters
  const dueWords = await countDueWords(now);
  let { k_min, k_max } = getDifficultyBand(dueWords);
  const k_cap = await getDynamicKCap();

  // Step 2: Get eligible sentences (script + HSK filtering only)
  const eligible = await getEligibleSentences(allSentences, scriptFilter, hskFilter);

  // Step 3: Sample once (larger than normal)
  const t_shuffle_start = performance.now();
  const sampleSize = Math.min(eligible.length, SELECTION_CONFIG.pool_sample_size * 2);  // 2x larger
  const pool = shuffle(eligible).slice(0, sampleSize);
  const t_shuffle_end = performance.now();

  nssLog('⏱️  Shuffle + Sample', {
    input: eligible.length,
    output: pool.length,
    time_ms: (t_shuffle_end - t_shuffle_start).toFixed(2)
  });

  nssLog('📊 Pool Stats', {
    eligible_pool_size: eligible.length,
    sample_size: pool.length
  });

  // Step 4: Bulk load character mastery
  const charMasteryMap = await bulkLoadCharMastery(pool);

  // Step 5: Compute metadata for all sampled sentences
  const metadata = await computeAllMetadata(pool, charMasteryMap, now);

  // Step 6: Fallback filtering loop
  let scored: ScoredSentence[] = [];
  let fallbackAttempt = 0;

  while (scored.length < SELECTION_CONFIG.batch_size && fallbackAttempt <= 5) {
    let candidates: SentenceMetadata[];
    let useThreshold: 0.6 | 0.8 = 0.6;

    switch (fallbackAttempt) {
      case 0:
        // FB0: All filters, k_band from difficulty, θ=0.6
        nssLog('🎯 FB0: Initial filtering', {
          filters: ['cooldown', 'skip', `k_band=[${k_min},${k_max}]`, 'θ=0.6']
        });
        candidates = metadata.filter(m =>
          m.passesCooldown &&
          m.passesSkip &&
          m.k_0_6 >= k_min &&
          m.k_0_6 <= k_max
        );
        break;

      case 1:
        // FB1: All filters, wider k_band, θ=0.6
        nssWarn('⚠️  FB1: Relaxing k_band', {
          filters: ['cooldown', 'skip', 'k_band=[1,6]', 'θ=0.6']
        });
        k_min = 1;
        k_max = 6;
        candidates = metadata.filter(m =>
          m.passesCooldown &&
          m.passesSkip &&
          m.k_0_6 >= 1 &&
          m.k_0_6 <= 6
        );
        break;

      case 2:
        // FB2: Drop cooldown, θ=0.6
        nssWarn('⚠️  FB2: Ignoring cooldown', {
          filters: ['skip', 'k_band=[1,6]', 'θ=0.6']
        });
        candidates = metadata.filter(m =>
          m.passesSkip &&
          m.k_0_6 >= 1 &&
          m.k_0_6 <= 6
        );
        break;

      case 3:
        // FB3: Drop skip too, θ=0.6
        nssWarn('⚠️  FB3: Dropping ewma skip filter', {
          filters: ['k_band=[1,6]', 'θ=0.6']
        });
        candidates = metadata.filter(m =>
          m.k_0_6 >= 1 &&
          m.k_0_6 <= 6
        );
        break;

      case 4:
        // FB4: Use mastered threshold (0.8)
        nssWarn('⚠️  FB4: Using mastered threshold', {
          filters: ['k_band=[1,6]', 'θ=0.8'],
          note: 'Should find [0.6, 0.8) characters'
        });
        useThreshold = 0.8;
        candidates = metadata.filter(m =>
          m.k_0_8 >= 1 &&
          m.k_0_8 <= 6
        );
        break;

      case 5:
        // FB5: Random fallback
        nssError('❌ FB5: Random selection (all strategies exhausted)');
        candidates = [];  // Set to empty to satisfy TypeScript
        scored = shuffle(metadata)
          .slice(0, SELECTION_CONFIG.batch_size)
          .map(m => ({
            sid: m.sentence.id,
            score: 0,
            k: 0,
            last_seen_ts: m.last_seen_ts
          }));
        break;

      default:
        candidates = [];
    }

    if (fallbackAttempt < 5) {
      nssLog(`Fallback ${fallbackAttempt} filtered`, {
        candidates_found: candidates.length
      });

      // Score filtered candidates
      scored = scoreFromMetadata(candidates, k_min, k_max, now, useThreshold, k_cap);

      nssLog(`Fallback ${fallbackAttempt} scored`, {
        scored_count: scored.length
      });
    }

    if (scored.length >= SELECTION_CONFIG.batch_size) {
      break;
    }

    fallbackAttempt++;
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

  const totalTime = performance.now() - startTime;

  nssLog('✅ Batch Generated (REFACTORED)', {
    batch_num: batchCounter,
    size: shuffled.length,
    total_time_ms: totalTime.toFixed(2),
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
    fallback_level: fallbackAttempt
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
