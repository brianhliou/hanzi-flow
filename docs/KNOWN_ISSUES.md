# Known Issues

## Practice Page

### ~~Subtle layout shift when transitioning between sentences~~ [RESOLVED]
**Status:** ✅ Resolved

**Description:**
When moving to a new sentence on the practice page, there was a subtle visual shift where characters would smoothly animate from their initial positions to final positions, appearing to shift apart to create equal spacing.

**Root cause:**
The `transition-all` CSS class on character elements was animating ALL properties including layout/position changes. When React re-rendered with a new sentence, the browser's layout calculation changes were being smoothly animated instead of happening instantly.

**Solution:**
Removed all CSS transitions from character elements. Changed from `className="inline-block transition-all"` to `className="inline-block"` and removed the inline `transition` style property.

**Resolution date:** 2025-10-21

**Related code:**
- `/app/app/practice/page.tsx` line 538 (removed transition-all)
- `/app/app/practice/page.tsx` line 563-565 (removed transition style)

---

### "Hanzi Flow" text blinks on practice page load
**Status:** Known limitation - accepted

**Description:**
When loading the practice page (especially on fast connections/refreshes), the "Hanzi Flow" text in the navigation briefly disappears and reappears, creating a quick blink effect.

**Root cause:**
This is a Next.js hydration mismatch issue. The server-side render cannot access localStorage to check if user preferences (script type and HSK level) are set, so it initially renders with `showPreferencesModal = false`. When the client-side JavaScript hydrates and checks localStorage in the useEffect hook (lines 88-113), it may update the modal state, causing React to re-render the entire page including the Navigation component.

**Why it happens:**
- localStorage is only available client-side, not during server-side rendering
- Server renders: "no modal needed" (can't check localStorage)
- Client hydrates: checks localStorage and may update `showPreferencesModal` state
- The state change triggers a re-render, briefly causing the blink

**Impact:**
- Minor visual glitch only on practice page load
- Does not affect functionality
- Only noticeable on fast page loads
- More apparent when preferences are already set (no modal shown)

**Possible solutions (not implemented):**
1. Switch from localStorage to cookies (cookies are sent to server and can be read during SSR)
2. Add a loading state that delays showing Navigation until preferences are checked
3. Add CSS fade-in animation to mask the hydration
4. Use `suppressHydrationWarning` on affected elements

**Decision:**
Accepted as-is. This is a common tradeoff in Next.js applications using client-side storage. The blink is minimal and doesn't impact user experience significantly. A proper fix would require refactoring to use cookies instead of localStorage, which is not worth the complexity for this minor issue.

**Related code:**
- `/app/app/practice/page.tsx` lines 88-113 (localStorage check in useEffect)
- `/app/app/practice/page.tsx` line 23 (`showPreferencesModal` state)
- `/app/components/Navigation.tsx` (Navigation component that blinks)

---

### Auto-skip mastered characters with fully-mastered HSK level creates practice trap
**Status:** Partially mitigated - architectural fix needed

**Description:**
When a user enables "Skip Mastered Characters" in settings AND has mastered all (or most) characters in their selected HSK level, they can get stuck in a trap where:
1. Every sentence auto-advances (all characters flash green and skip)
2. No actual practice occurs
3. User must manually press Space after each sentence
4. Process repeats indefinitely with no clear indication of the problem

**Example scenario:**
- User filters to HSK 1 (300 characters)
- User has mastered all 300 characters (mastery ≥ 0.8)
- User enables "Skip Mastered Characters" setting
- User tries to practice → every sentence auto-skips through in ~2 seconds

**Root cause:**
NSS (Next Sentence Selection) algorithm is decoupled from the auto-skip preference:
- **NSS** uses `θ_known = 0.6` to determine "unknown" characters for sentence selection
- **Auto-skip** uses `mastered_threshold = 0.8` to determine which characters to skip
- **Gap**: Characters with mastery ∈ [0.6, 0.8) are considered "known" by NSS but not auto-skipped
- **Problem**: When all characters have mastery ≥ 0.8, NSS sees k=0 unknowns for every sentence
- **Fallback**: NSS falls back to random sentence selection after exhausting normal strategies
- **Result**: Random fully-mastered sentences get selected and flash through uselessly

**Technical details:**

NSS rejection cascade (sentence-selection.ts):
```typescript
// Lines 365-379: Only characters with s < 0.6 are "unknowns"
if (s < θ_known) {  // θ_known = 0.6
  unknowns.push({ char_id, s, overdue });
}
const k = unknowns.length;

// Reject if no unknowns
if (k === 0) {
  return null;  // All HSK 1 sentences rejected!
}

// Lines 638-649: Fallback 5 - random selection
if (fallbackAttempt === 5) {
  scored = shuffle(allSentences)
    .filter(s => s.script_type !== 'ambiguous')
    .slice(0, SELECTION_CONFIG.batch_size)
    .map(s => ({ sid: s.id, score: 0, k: 0, last_seen_ts: 0 }));
}
```

Auto-skip behavior (practice/page.tsx:201-238):
```typescript
// Auto-skip if character mastery >= 0.8
const isMastered = wordMastery && wordMastery.s >= SELECTION_CONFIG.mastered_threshold;

if (isMastered) {
  setMasteredIndices((prev) => new Set(prev).add(state.currentCharIndex));
  // Character flashes green and auto-advances after 100ms
}
```

**Data corruption issue (FIXED):**
Previously, fully auto-skipped sentences were recorded with score = 0 because no attempts were logged. This created misleading data where:
- Sentence `ewma_pass` moved toward 0 (appears "difficult")
- Reality: sentence has all mastered characters (nothing to learn)
- NSS interpreted low `ewma_pass` as "needs more practice" → selected more often
- User trapped in loop selecting same fully-mastered sentences

**Quick fix implemented (2025-11-13):**
Modified practice/page.tsx lines 286-293 to detect when all Chinese characters were auto-skipped and record sentence score as 1.0 instead of 0:

```typescript
const chineseCharCount = currentSentence.chars.filter(c => c.pinyin).length;
const sentenceScore = charScores.size > 0
  ? Array.from(charScores.values()).reduce(...) / charScores.size
  : chineseCharCount > 0 && masteredIndices.size === chineseCharCount
    ? 1.0  // All Chinese characters were mastered and auto-skipped
    : 0;   // No characters practiced (defensive fallback)
```

**What this fixes:**
- ✅ Prevents sentence data corruption (no longer records as 0%)
- ✅ Allows sentences to naturally hit skip threshold (ewma_pass → 0.9)
- ✅ Provides gradual escape from trap as sentences get skipped
- ❌ Still doesn't prevent NSS from selecting fully-mastered sentences initially
- ❌ User still experiences 2-3 seconds of green flash-through per sentence
- ❌ No clear indication to user that they should change HSK level

**Proper architectural fix needed:**
NSS should be aware of the skip-mastered preference:

1. Pass `skipMastered` boolean into `getNextSentence()` / `generateSentenceBatch()`
2. When `skipMastered = true`, adjust scoring logic:
   - Consider characters with s ≥ 0.8 as "effectively skipped"
   - Reject sentences where all Chinese characters have s ≥ 0.8
   - Use adjusted k-count for difficulty band placement
3. When no suitable sentences found, show friendly error:
   ```
   "🎉 You've mastered all HSK 1 characters!

   Try increasing your HSK level in Settings to continue learning."
   ```

**Workarounds for users (temporary):**
1. Disable "Skip Mastered Characters" in Settings
2. Increase HSK level filter (e.g., HSK 1 → HSK 2)
3. Switch to "Beyond HSK" filter to access non-HSK characters

**Impact:**
- Severity: Medium (affects users who've completed an HSK level with skip enabled)
- Frequency: Rare in early learning, increases as users progress
- User experience: Confusing and frustrating (looks like bug)
- Data integrity: Fixed by quick fix (no longer pollutes sentence mastery data)

**Related code:**
- `/app/app/practice/page.tsx` lines 201-238 (auto-skip logic)
- `/app/app/practice/page.tsx` lines 286-293 (sentence scoring fix)
- `/app/lib/sentence-selection.ts` lines 338-423 (NSS scoring)
- `/app/lib/sentence-selection.ts` lines 626-656 (NSS fallback cascade)
- `/app/lib/selection-config.ts` line 14 (`θ_known = 0.6`)
- `/app/lib/selection-config.ts` line 108 (`mastered_threshold = 0.8`)

**Priority:** Medium - Quick fix prevents data corruption, but proper architectural fix would improve UX

---

## Data Quality

### ~~Incorrect pinyin for 谁 character~~ [RESOLVED]
**Status:** ✅ Resolved (Oct 2025)

**Description:**
The character 谁/誰 (who) was incorrectly listed with formal pinyin `shuí` instead of colloquial `shei2` which is used in modern spoken Mandarin.

**Solution:**
Fixed via OpenAI-powered context-aware pinyin refinement in sentence pipeline step 5. Applied 726 corrections for 谁/誰 across the corpus, changing formal `shuí` to colloquial `shei2` where appropriate.

**Technical details:**
- See `scripts/sentences/step5/README.md` for pinyin refinement workflow
- See `LESSONS_LEARNED.md` Section 2 for complete analysis
- Output: `data/sentences/step5_pinyin_refined.csv`

**Note:** While the workflow is complex (requires OpenAI API processing), the corrections have been applied to production data and are included in the repository.

### ~~Incorrect pinyin for 地 when used as adverbial particle~~ [RESOLVED]
**Status:** ✅ Resolved (Oct 2025)

**Description:**
The character 地 has multiple pronunciations depending on context:
- `di4` when meaning "earth/ground/land" (noun)
- `de` (neutral tone) when used as an adverbial particle (adjective + 地 + verb pattern)

Previously, pypinyin + jieba often assigned `di4` even when used as a particle, which is grammatically incorrect.

**Solution:**
Fixed via OpenAI-powered context-aware pinyin refinement in sentence pipeline step 5. Applied 805 corrections for 地, properly distinguishing between noun usage (`di4`) and particle usage (`de`).

**Other polyphonic characters also fixed:**
- 著/着 (696 corrections): Aspect marker `zhe` vs verb `zhuo2`/`zhao2`
- 覺/觉 (139 corrections): Sleep `jiao4` vs feel `jue2`
- 長/长 (349 corrections): Long `chang2` vs grow `zhang3`
- 樂 (155 corrections): Music `yue4` vs happy `le4`

**Technical details:**
- See `scripts/sentences/step5/README.md` for pinyin refinement workflow
- See `LESSONS_LEARNED.md` Section 2 for complete analysis
- Total applied: 2,870 character-level pinyin improvements across 2,720 sentences

**Note:** While the workflow is complex (requires OpenAI API processing), the corrections have been applied to production data and are included in the repository.

---

## Data Pipeline Technical Debt

### Audio pipeline uses Unihan instead of corpus data
**Status:** Open - migration planned

**Description:**
The audio generation pipeline (`scripts/audio/enumerate_syllables_unihan.py`) currently generates syllable lists from the Unihan database instead of our actual corpus data. This means we may be generating audio for syllables that never appear in our sentence corpus, while the syllable enumeration format also lacks the dual-format storage used by the character pipeline.

**Issues:**
1. **Unihan source instead of corpus**: `enumerate_syllables_unihan.py` extracts syllables from Unihan_Readings.txt instead of step6_with_freq.csv
   - Generates syllables that may never be used
   - Ignores frequency data from actual corpus
   - Requires tone mark conversion (Unihan uses tone marks)

2. **Outdated validation script**: `validate_audio_coverage.py` assumes character CSV has only tone marks
   - Comments say "CSV has tone marks: nǚ, zhèi, měi" (OUTDATED)
   - Character CSV now has dual formats: `pinyins_tone3` AND `pinyins_display`
   - Script does unnecessary conversion that could use tone3 directly

3. **Missing dual-format in syllables_enumeration.json**: Output JSON only has tone3 format
   - Doesn't include display format (tone marks) like character data
   - Inconsistent with character pipeline dual-format approach

**Impact:**
- Potential audio generation for unused syllables (wasted TTS API calls)
- Cannot prioritize audio generation by frequency
- Unnecessary format conversions in validation
- Inconsistent data formats across pipelines

**Proposed solution:**
Migrate audio pipeline to use step6_with_freq.csv as source of truth:

1. **Rewrite `enumerate_syllables_unihan.py`** → `enumerate_syllables_corpus.py`
   - Read from `data/character_set/step6_with_freq.csv`
   - Parse `pinyins_tone3` column directly (no conversion needed)
   - Filter to pinyins with frequency > 0 (corpus-driven)
   - Use pinyin-level frequency data for prioritization

2. **Update `syllables_enumeration.json` structure**:
   ```json
   {
     "syllables": [
       {
         "pinyin_tone3": "yi1",
         "pinyin_display": "yī",
         "filename": "yi1",
         "frequency": 8867,
         "char_count": 3
       }
     ]
   }
   ```

3. **Fix `validate_audio_coverage.py`**:
   - Read from `pinyins_tone3` column directly
   - Remove unnecessary tone mark conversion
   - Update validation logic for dual-format data

**Benefits:**
- Corpus-driven: Only generate audio for syllables actually used
- Frequency-aware: Prioritize common syllables
- No format conversion: Use pinyins_tone3 directly
- Consistent with character pipeline: Same data source and format

**Related files:**
- `scripts/audio/enumerate_syllables_unihan.py` - Current Unihan-based script
- `scripts/audio/validate_audio_coverage.py` - Validation script (needs update)
- `data/audio/syllables_enumeration.json` - Current output format
- `data/character_set/step6_with_freq.csv` - Proposed new source

**Related documentation:**
- See `docs/migrations/pinyin-format-2025-11/` for character pipeline dual-format migration
- Character pipeline successfully eliminated all format conversions

**Priority:** Medium - Not blocking but would improve efficiency and consistency

---

## Future Enhancements / Roadmap

### Interactive Pinyin Trie Explorer (Blog Post Feature)
**Status:** Planned

**Description:**
Create an interactive web-based lookup tool for the blog post about Pinyin Trie analysis. Users can type a Chinese character and instantly see all its pronunciations, frequencies, and usage statistics.

**Proposed features:**
- **Character lookup:** Type or paste any Chinese character
- **Display results:**
  - All pronunciations (with pinyin_freq and corpus_freq)
  - Main vs alternative usage percentages
  - Example sentences for each pronunciation
  - Visual indicator showing pronunciation distribution
- **Reverse lookup:** Type pinyin to see all matching characters
- **Interactive:** Click on related characters to explore polyphonic relationships

**Technical approach:**
1. Export Trie data to JavaScript-friendly JSON format
2. Create simple HTML/JavaScript interface (no build step needed for blog)
3. Client-side search (no backend required)
4. Embed in GitHub Pages blog post via iframe or inline

**Example UI:**
```
Search: 的
━━━━━━━━━━━━━━━━━━━━━━━━━━
的 (28,594 total occurrences)

Pronunciations:
  de0   ████████████████████ 28,524 (99.8%) - particle
  di4   ▌                        58 (0.2%) - target
  di1   ▌                         7 (<0.1%) - rare
  di2   ▌                         5 (<0.1%) - rare

Type: Polyphonic (4 pronunciations)
Related: 地(de0), 得(de2, de0)
```

**Benefits:**
- Makes blog post interactive and engaging
- Demonstrates practical application of the analysis
- Allows readers to explore their own characters of interest
- No installation required - runs in browser

**Files to create:**
- `docs/blog/pinyin-trie/trie_explorer.html` - Standalone interactive tool
- `docs/blog/pinyin-trie/trie_data.js` - Exported Trie data
- `scripts/character_set/analysis/export_trie_for_web.py` - Export script

**Priority:** Medium - Would enhance blog post but not essential for publishing

**Related analysis:**
- `data/character_set/analysis/PINYIN_TRIE_ANALYSIS.md` - Key findings for blog
- `data/character_set/analysis/pinyin_trie.json` - Source data
