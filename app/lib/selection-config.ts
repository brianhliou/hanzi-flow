/**
 * Next Sentence Selection (NSS) Configuration
 *
 * Tunable parameters for adaptive sentence selection algorithm.
 * Balances word-level spaced repetition with sentence-level mastery.
 */

export const SELECTION_CONFIG = {
  // ============================================================================
  // DIFFICULTY BAND
  // ============================================================================

  /** Word mastery threshold - words with s < θ_known are considered "unknown" */
  θ_known: 0.7,

  /** Minimum unknown words per sentence (normal mode) */
  k_min: 2,

  /** Maximum unknown words per sentence (normal mode) */
  k_max: 5,

  /** Minimum unknown words when backlog high (tighter difficulty) */
  k_min_backlog: 1,

  /** Maximum unknown words when backlog high (tighter difficulty) */
  k_max_backlog: 3,

  // ============================================================================
  // BACKLOG CONTROL
  // ============================================================================

  /** Review backlog threshold - if due_words > due_cap, tighten difficulty */
  due_cap: 80,

  // ============================================================================
  // COOLDOWN & SKIP
  // ============================================================================

  /** Don't repeat sentence within this many minutes */
  cooldown_minutes: 60,

  /** Skip sentence if ewma_pass >= this threshold (mastered) */
  ewma_skip_threshold: 0.9,

  /** Minimum attempts required before considering sentence for skip */
  min_seen_for_skip: 2,

  // ============================================================================
  // SCORING WEIGHTS
  // ============================================================================

  /** Multiplier for words due for review (SRS boost) */
  overdue_boost: 1.2,

  /** Weight for novelty (time since last seen) */
  novelty_weight: 0.05,

  /** Weight for sentence ewma pass penalty (avoid grinding) */
  pass_penalty_weight: 0.1,

  /** Penalty for difficulty outside k_band */
  k_penalty_weight: 0.2,

  // ============================================================================
  // BATCHING
  // ============================================================================

  /** Number of sentences to generate per batch */
  batch_size: 10,

  /** Start prefetching next batch when this many sentences remain */
  prefetch_threshold: 2,

  /** Number of candidate sentences to sample and score per batch generation */
  pool_sample_size: 200,

  /** Optional: invalidate queue after this duration (ms). Set to 0 to disable. */
  queue_max_age_ms: 0,  // Disabled - keep queue indefinitely

  // ============================================================================
  // NOVELTY CAP
  // ============================================================================

  /** Maximum hours for novelty calculation (cap for never-seen sentences) */
  max_novelty_hours: 72,

  // ============================================================================
  // COLD START PROTECTION
  // ============================================================================

  /** Dynamic k_cap based on average word mastery to prevent overwhelming sentences */
  k_cap_by_mastery: {
    /** Cold start: when average mastery is very low */
    cold_start: { threshold: 0.4, k_cap: 12 },
    /** Early learning: building initial vocabulary */
    early: { threshold: 0.6, k_cap: 10 },
    /** Intermediate: comfortable with basics */
    intermediate: { threshold: 0.75, k_cap: 8 },
    /** Advanced: no cap needed, k_penalty handles it */
    advanced: { threshold: 1.0, k_cap: null }
  },
} as const;

export type SelectionConfig = typeof SELECTION_CONFIG;
