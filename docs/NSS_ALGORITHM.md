# Next Sentence Selection (NSS) Algorithm

**Author:** Brian Liou
**Last Updated:** 2025-11-16
**Implementation:** `app/lib/sentence-selection.ts`

## Overview

The NSS algorithm is an adaptive, batch-based sentence selector that maintains 90-95% comprehension by selecting sentences with optimal difficulty. It balances multiple factors:

- **Character mastery** (EWMA-based learning curves)
- **Spaced repetition** (SRS scheduling with overdue boost)
- **Optimal difficulty** (2-5 unknown characters per sentence)
- **Novelty** (time since last seen)
- **Sentence mastery** (avoid grinding same sentences)

## Core Pipeline

The algorithm operates in 5 stages:

```
1. FILTER    → Get eligible sentences (script, HSK, cooldown, skip)
2. SAMPLE    → Take random 300 from eligible pool
3. SCORE     → Calculate score for each candidate (with k-band, θ_known)
4. FALLBACK  → If <8 scored, progressively relax constraints
5. SELECT    → Take top 8, shuffle, queue
```

## Two-Stage Architecture

**CRITICAL UNDERSTANDING:** The algorithm has two distinct constraint stages:

### Stage 1: Pool Filtering (`getEligibleSentences`)

Filters the corpus to create an "eligible pool" based on:
- **Script type** (simplified/traditional/neutral, exclude ambiguous)
- **HSK level** (user's selected range, simplified only)
- **Cooldown** (20 minutes since last seen) - controlled by `ignoreCooldown` option
- **ewma_skip** (sentence mastery ≥ 0.9) - controlled by `ignoreSkip` option

**Key insight:** These filters determine which sentences enter the pool. If a sentence fails these checks, it won't be sampled at all.

### Stage 2: Scoring Constraints (`scoreCandidates`)

Applies scoring rules to the 300 sampled candidates:
- **k_band** (k_min, k_max) - Difficulty range
- **θ_known** threshold - What counts as "unknown"
- **k_cap** - Cold start protection

**Key insight:** These constraints reject candidates during scoring, but don't affect the pool. A sentence can be in the sample pool but get rejected with `score = null` if it doesn't meet scoring constraints.

## Fallback Cascade (The Confusing Part!)

When `scored.length < 8` after initial scoring, the algorithm enters a **progressive relaxation cascade**. Understanding which stage each fallback affects is crucial:

### Fallback 0 (Initial Attempt)

**Pool Filtering:**
- Script: user preference
- HSK: user preference
- Cooldown: enforced (20 min)
- ewma_skip: enforced (≥ 0.9 excluded)
- **Pool size:** e.g., 5,000 sentences

**Sampling:** Random 300 from pool

**Scoring:**
- k_band: `[2, 5]` normal, or `[1, 3]` if backlog >80
- θ_known: `0.6`

---

### Fallback 1: Relax k_band

**Code:** `applyFallbacks:517-522`

**Pool Filtering:**
- `ignoreCooldown: false` (attempt 1 < 2)
- `ignoreSkip: false` (attempt 1 < 4)
- **Pool size:** Same as initial (e.g., 5,000)
- **Pool changes?** ❌ No

**Sampling:** ✅ NEW random 300 from same pool

**Scoring:**
- k_band: `[1, 6]` ⬅️ **RELAXED** (was [2, 5])
- θ_known: `0.6` (unchanged)

**What changed:** Only scoring k_band. Same sentences in pool, just rescored with wider difficulty range.

---

### Fallback 2: Ignore Cooldown

**Code:** `applyFallbacks:524-529`

**Pool Filtering:**
- `ignoreCooldown: true` ⬅️ **CHANGED** (attempt 2 ≥ 2)
- `ignoreSkip: false` (attempt 2 < 3)
- **Pool size:** Larger (e.g., 8,000 - includes recently-seen)
- **Pool changes?** ✅ Yes (expanded)

**Sampling:** ✅ NEW random 300 from larger pool

**Scoring:**
- k_band: `[1, 6]` (unchanged from FB1)
- θ_known: `0.6` (unchanged)

**What changed:** Pool expanded to include sentences seen <20 minutes ago. Fresh 300 samples from this larger pool.

---

### Fallback 3: Drop ewma_skip

**Code:** `applyFallbacks:531-536`

**Pool Filtering:**
- `ignoreCooldown: true` (unchanged from FB2)
- `ignoreSkip: true` ⬅️ **CHANGED** (attempt 3 ≥ 3)
- **Pool size:** Larger (e.g., 9,000 - includes mastered sentences)
- **Pool changes?** ✅ Yes (expanded)

**Sampling:** ✅ NEW random 300 from larger pool

**Scoring:**
- k_band: `[1, 6]` (unchanged)
- θ_known: `0.6` (unchanged)

**What changed:** Pool now includes sentences with `ewma_pass ≥ 0.9` (fully mastered sentences). These sentences were previously excluded.

**The trap:** Even though mastered sentences are now in the pool, they may still get rejected during scoring if `k = 0` (all characters ≥ 0.6).

---

### Fallback 4: Random Selection

**Code:** `sentence-selection.ts:634-646`

**Pool Filtering:** Uses eligible pool from FB3
- Script: ✅ Respects user preference (simplified/traditional)
- HSK: ✅ Respects user selection (1-3, etc.)
- Cooldown: Ignored (from FB2)
- Skip: Ignored (from FB3)

**Sampling:** None (no scoring)

**Selection:**
```typescript
scored = shuffle(fallback.pool)
  .slice(0, 8)
  .map(s => ({ sid: s.id, score: 0, k: 0, last_seen_ts: 0 }));
```

**What changed:** Gives up on scoring optimization but still respects user's basic learning preferences (script type and HSK level). Random selection from eligible pool.

**When this happens:** This is the "emergency fallback" when all other strategies fail. Often triggered in the **mastered-character trap** scenario.

---

## Fallback Summary Table

| Fallback | Pool Changes? | Pool Size | Resample? | Scoring Changes |
|----------|---------------|-----------|-----------|-----------------|
| **0 (Initial)** | - | 5,000 | 300 samples | k_band=[2,5], θ=0.6 |
| **1: k_band** | ❌ Same | 5,000 | ✅ New 300 | k_band=[1,6] |
| **2: Cooldown** | ✅ Larger | 8,000 | ✅ New 300 | - |
| **3: Skip** | ✅ Larger | 9,000 | ✅ New 300 | - |
| **4: Random** | ❌ Same | 9,000 | Direct 8 | No scoring (random) |

## Why Resampling Matters

**Every fallback resamples 300 sentences**, even when the pool doesn't change. This is important because:

1. **Randomness helps:** Even with the same pool, different samples might score better
2. **Avoids determinism:** Prevents always selecting the same sentences when constraints are tight
3. **Fresh chances:** Pool expansions (FB2, FB3) include new candidates that weren't available before

**However:** If the fundamental problem (e.g., all sentences have k=0) applies to the entire pool, resampling won't help. This is why the mastered-character trap eventually falls to random selection.

## The Mastered-Character Trap

See `docs/KNOWN_ISSUES.md:62-188` for full details.

**What happens:**
1. User enables "Skip Mastered Characters" (threshold = 0.8)
2. User masters all HSK 1 characters (all s ≥ 0.8)
3. NSS uses θ_known = 0.6 to count unknowns
4. All sentences have k=0 (all chars ≥ 0.6)
5. All sentences rejected during scoring: `if (k === 0) return null;`
6. Fallbacks 1-2 don't help (k still 0)
7. Fallback 3 adds mastered sentences to pool, but they still have k=0 → rejected
8. **Fallback 4 triggers:** Random sentences selected → all flash green

**Why Fallback 3 doesn't save us:**
- FB3 adds mastered sentences to the **pool** (Stage 1)
- But scoring (Stage 2) still rejects them for k=0
- The mismatch between θ_known (0.6) and mastered_threshold (0.8) creates the trap

**Proper fix:** Make NSS aware of `skipMastered` preference and use mastered_threshold (0.8) instead of θ_known (0.6) when calculating k-count.

## Key Parameters

From `app/lib/selection-config.ts`:

```typescript
// Difficulty
θ_known: 0.6              // Unknown threshold (for k-counting)
k_min: 2, k_max: 5       // Normal difficulty band
k_min_backlog: 1         // Tighter when backlog >80
k_max_backlog: 3

// Filters
cooldown_minutes: 20     // Min time between same sentence
ewma_skip_threshold: 0.9 // Skip fully-mastered sentences
min_seen_for_skip: 2     // Min attempts before skipping

// Scoring
overdue_boost: 2.0       // SRS multiplier
novelty_weight: 0.05     // Time-based bonus
pass_penalty_weight: 0.1 // Sentence mastery penalty
k_penalty_weight: 0.35   // Difficulty penalty

// Batching
batch_size: 8            // Sentences per batch
pool_sample_size: 300    // Candidates to score
prefetch_threshold: 2    // When to prefetch next batch

// Mastery (for display/stats)
mastered_threshold: 0.8  // "Mastered" character
learning_threshold: 0.4  // "Learning" character
```

## Common Misconceptions

### ❌ "Higher θ_known = more unknowns"
**Wrong!** Higher θ_known = fewer unknowns. If θ_known = 0.65, characters with s=0.62 are now "known" (was "unknown" at θ=0.6).

### ❌ "Fallback 3 fixes the mastered-character trap"
**Wrong!** FB3 adds mastered sentences to the pool, but scoring still rejects them for k=0. Only FB4 (random) "fixes" it by bypassing scoring entirely.

### ❌ "Each fallback uses the same 300 samples"
**Wrong!** Each fallback resamples a fresh 300, either from the same pool (FB1) or an expanded pool (FB2, FB3).

### ❌ "k_band and θ_known filter the pool"
**Wrong!** They're scoring constraints (Stage 2), not pool filters (Stage 1). Pool is filtered by script/HSK/cooldown/skip only.

## Code References

- **Main pipeline:** `sentence-selection.ts:568-700` (`generateSentenceBatch`)
- **Fallback logic:** `sentence-selection.ts:506-559` (`applyFallbacks`)
- **Pool filtering:** `sentence-selection.ts:213-287` (`getEligibleSentences`)
- **Scoring:** `sentence-selection.ts:428-503` (`scoreCandidates`)
- **Configuration:** `selection-config.ts:8-114`

## Further Reading

- **Technical Overview:** `docs/TECHNICAL_OVERVIEW.md:172-270` (high-level summary)
- **Known Issues:** `docs/KNOWN_ISSUES.md:62-188` (mastered-character trap)
- **Project Brief:** `docs/PROJECT_BRIEF.md` (NSS vision and goals)
