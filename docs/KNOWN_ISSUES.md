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

### Incorrect pinyin for 谁 character
**Status:** Open - needs investigation

**Description:**
The character 谁 (who) is listed with pinyin `shui2` in all 428 occurrences in the sentence data. However, the standard modern Mandarin pronunciation is `shei2`, not `shui2`. While `shui2` is an alternate/literary pronunciation, `shei2` is what's used in spoken language and should be the primary accepted answer.

**Impact:**
- Users familiar with the standard pronunciation `shei2` will get marked wrong
- This is particularly frustrating because `shei2` is the correct modern spoken form
- Affects 428 sentences in the corpus

**Possible solutions:**
1. **Update source data**: Change all instances from `shui2` to `shei2`
2. **Accept both pronunciations**: Modify scoring logic to accept both `shei2` and `shui2` as correct
3. **Character-specific exceptions**: Create a mapping of characters with multiple valid pronunciations

**Data source:**
The pinyin data likely comes from the original Tatoeba dataset or character mapping file. Need to investigate:
- `/data/sentences/cmn_sentences_with_char_pinyin.csv` (if exists)
- Character mapping generation scripts in `/scripts/sentences/`

**Next steps:**
- Verify the source of the pinyin data
- Determine if there are other characters with similar alternate pronunciation issues
- Decide on preferred solution (update data vs. accept multiple pronunciations)

### Incorrect pinyin for 地 when used as adverbial particle
**Status:** Open - needs investigation

**Description:**
The character 地 has multiple pronunciations depending on context:
- `di4` when meaning "earth/ground/land" (noun)
- `de` (neutral tone) when used as an adverbial particle (similar to how 的 works)

In sentence 27131: "后来我意识到北京人比较慢地散步。", the character 地 is used adverbially (慢地 = slowly), so it should be pronounced `de`, not `di4`. However, our data has it as `di4`.

**Impact:**
- Users who correctly identify the grammatical function and pronounce it as `de` will be marked wrong
- This is a common grammar pattern in Chinese (adjective + 地 + verb)
- Unknown how many sentences are affected

**Related issue:**
This is similar to the 谁 (shei2/shui2) issue - characters with context-dependent pronunciations.

**Other characters with similar issues:**
- 的 (de/di2/di4) - usually `de` but can be `di2` in 的确, `di4` in 目的
- 得 (de/de2/dei3) - grammar particle `de`, verb `de2` (obtain), modal `dei3` (must)
- 了 (le/liao3) - aspect marker `le`, verb `liao3` (finish/understand)
- 着 (zhe/zhao2/zhuo2/zhuó) - aspect marker `zhe`, other meanings have different tones
- 为 (wei2/wei4) - depends on meaning and context

**Possible solutions:**
1. **Manual review**: Find all instances where 地/的/得 are used as particles and correct to neutral tone
2. **Grammar-aware pinyin**: Use NLP to detect grammatical function and assign correct pronunciation
3. **Accept multiple**: Add exceptions to accept both pronunciations for these characters
4. **Update source data**: If the source (Tatoeba) has errors, this affects all derived data

**Next steps:**
- Search for other instances of 地 used as adverbial particle (look for pattern: adjective + 地 + verb)
- Investigate other grammatical particles (的, 得, 了, 着, etc.)
- Consider creating a comprehensive list of context-dependent pronunciation characters

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
