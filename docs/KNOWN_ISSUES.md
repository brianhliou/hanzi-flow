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
