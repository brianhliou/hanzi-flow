# Lessons Learned

This document captures important debugging insights and technical lessons learned during the development of Hanzi Flow.

---

## 1. CSS `transition-all` Can Cause Unexpected Layout Animations

**Date:** 2025-10-21

**Problem:**
Characters on the practice page were smoothly shifting/animating when loading new sentences. The shift was subtle but jarring - characters would appear too close together initially, then smoothly spread apart to equal spacing. This happened consistently with certain multi-line sentences.

**Investigation Process:**
1. Initially suspected it was a React state update timing issue (multiple setState calls)
2. Thought it might be font loading causing reflow
3. Considered CSS centering + line wrapping interactions
4. Eventually discovered through systematic testing that:
   - The issue happened consistently with the same sentences
   - The animation was smooth and quick (not instant)
   - This pointed to CSS transitions

**Root Cause:**
The `transition-all` class was applied to character elements to animate color changes for user feedback. However, `transition-all` animates **ALL** CSS properties, including layout properties like position, margin, and dimensions.

When React re-rendered with a new sentence:
1. Browser calculated initial character positions
2. Browser finalized layout with proper spacing/margins
3. `transition-all` smoothly animated the difference between initial and final positions
4. Result: Visible "shifting" as characters moved to their final positions

**Solution:**
Remove all CSS transitions from character elements. The visual feedback (colors, current character indication) works fine with instant changes - no animation needed.

**Key Takeaways:**
- ⚠️ **Never use `transition-all` unless you fully understand what's being animated**
- Use specific property transitions: `transition: 'color 150ms, transform 150ms'` instead of `transition-all`
- Layout properties (position, margin, width, height) should generally NOT be animated during normal rendering
- When debugging smooth/animated visual issues, always check for CSS transitions
- Test with specific, reproducible examples rather than random cases

**Related Files:**
- `/app/app/practice/page.tsx` - Character rendering component

**Code Before:**
```tsx
<span className="inline-block transition-all">
```

**Code After:**
```tsx
<span className="inline-block">
```

---

## 2. Pinyin Data Quality: Context-Dependent Pronunciations and Alternative Readings

**Date:** 2025-10-21

**Problem:**
Users were being marked incorrect when typing valid alternative pronunciations:
- 谁: Typing `shei2` (colloquial/modern) was marked wrong, only `shui2` (formal/literary) accepted
- 地: Typing `de` (particle usage) was marked wrong, only `di4` (noun meaning) accepted
- Similar issues with other grammatical particles: 的, 得, 了, 着

**Investigation Process:**
1. Discovered pypinyin with `heteronym=False` only returns one pronunciation per character
2. Found character_set (from Unihan/CC-CEDICT) only had formal pronunciations
3. Realized we had THREE conflicting sources:
   - Character_set dictionary (Unihan/CEDICT) - formal/incomplete
   - pypinyin - context-aware but imperfect
   - Real-world Mandarin usage - what users actually say
4. Tested pypinyin with `heteronym=True` - SUCCESS! It knows the alternatives:
   - 谁: `['shui2', 'shei2']`
   - 地: `['di4', 'de']`
   - 的: `['de', 'di1', 'di2', 'di4']`

**Root Cause:**
Multi-layered data pipeline issue:
1. **Character_set generation**: Used Unihan data which has formal/dictionary pronunciations only
2. **Sentence pinyin generation**: Used pypinyin with `heteronym=False`, choosing single pronunciation
3. **Scoring**: Validated against sentence-level pinyin only, not alternative valid readings

**Solution (Three-Phase Approach):**

**Phase 1: Enrich character_set with pypinyin alternatives**
- Created `build_step6_enrich_pypinyin.py`
- Runs pypinyin with `heteronym=True` on each character
- Merges results with existing Unihan pinyins (base form comparison to avoid format duplicates)
- Result: 6.6% of characters genuinely enriched (1,391/20,992) with alternative pronunciations

**Phase 2: Update scoring to validate against character_set**
- Modified `checkPinyin()` to accept character parameter
- Looks up all valid pinyins from enriched character_set
- Accepts ANY valid pronunciation for the character
- Falls back to sentence-level pinyin if character_set unavailable

**Phase 3: Context-aware sentence pinyin regeneration with OpenAI (COMPLETED)**

After Phase 1-2, sentence displays still showed suboptimal pinyins (e.g., 地 showing `di4` when particle usage `de` would be correct). We used OpenAI gpt-4o-mini to regenerate context-aware sentence-level pinyin.

**Process:**
1. **Analysis Phase:**
   - Used OpenAI to regenerate pinyin for all 79,613 sentences
   - Created `improve_pinyin_with_openai.py` with:
     - Batch processing (10 sentences per API call)
     - Checkpointing for resumability
     - Retry logic with exponential backoff
     - Sentence-level format with strict non-Chinese preservation rules
   - Ran `compare_pinyin_changes.py` to analyze differences
   - Found 10,336 changes (1.31% of 788,948 characters)

2. **Verification Phase:**
   - Identified 2,870 high-confidence improvements (27.8% of changes):
     - 地 (805): Particle `de` vs noun `di4` ✅
     - 著 (696): Aspect marker `zhe` vs verb `zhuó` ✅
     - 谁/誰 (726): Colloquial `shei2` vs formal `shuí` ✅
     - 覺/觉 (139): Sleep `jiào` vs feel `jué` ✅
     - 長/长 (349): Long `cháng` vs grow `zhǎng` ✅
     - 樂 (155): Music `yuè` vs happy `lè` ✅
   - Identified ~632 errors/questionable changes (6.1%):
     - 了 (136): OpenAI wrong (e.g., 了如指掌 gave `le` instead of `liǎo`) ❌
     - 是/的/回 (496): Alignment errors from wrong sentence pinyin ❌
   - Remaining 6,834 (66.1%): Need case-by-case review

3. **Selective Application:**
   - Created `apply_verified_pinyin_changes.py` with safety features:
     - Only updates 9 verified characters (地, 著, 谁, 誰, 覺, 觉, 長, 长, 樂)
     - Dry-run mode for testing
     - Incremental limits (1, 10, 100 for testing)
     - Automatic backup creation
     - Detailed change logging
     - Never modifies original CSV
   - Applied 2,870 character-level pinyin updates to CSV
   - Updated pipeline to use `_UPDATED.csv`
   - Regenerated production JSON with improvements

**Results:**
- ✅ **2,870 pinyin improvements** applied to 2,720 sentences
- ✅ **Production JSON regenerated** with context-aware pinyins
- ✅ **Visual discrepancies eliminated** for major polyphonic characters
- ✅ **No data corruption** - all other columns preserved, structure intact
- 🎯 **Conservative approach** - only applied high-confidence changes, ignored questionable ones

**Key Takeaways:**
- ⚠️ **Context matters for Chinese pinyin** - Many characters have different pronunciations based on grammatical function
- Dictionary data (Unihan/CEDICT) favors formal/literary pronunciations over colloquial usage
- pypinyin with `heteronym=True` is valuable for discovering alternatives but has limitations
- **OpenAI can provide context-aware pinyin** but requires careful prompt engineering and verification
- When applying AI-generated data improvements:
  - ✅ Analyze all changes first (comparison report)
  - ✅ Verify high-confidence patterns manually
  - ✅ Apply selectively, not wholesale
  - ✅ Use incremental testing (1, 10, 100 before full run)
  - ✅ Create backups and detailed logs
  - ✅ Never modify source data directly
- **Prompt engineering matters:** Multiple iterations needed to get proper output format:
  - Sentence-level format (not character-by-character) preserves context
  - Explicit rules for preserving non-Chinese elements (numbers, punctuation, English)
  - "ONE SYLLABLE PER CHARACTER" rule prevents compound word artifacts
  - Example-driven prompts work better than rule-only prompts
- **Rate limiting is critical:** 2-second delays between API calls prevent rate limit errors
- **Error handling is essential:** Network issues, timeouts, and alignment errors will happen at scale

**Characters most affected:**
- Grammatical particles: 地/的/得 (de), 了 (le), 着/著 (zhe)
- Colloquial alternatives: 谁/誰 (shei2 vs shui2)
- Context-dependent: 覺/觉 (jiao4 vs jue2), 長/长 (chang2 vs zhang3), 樂 (yue4 vs le4)

**Related Files:**
- `/scripts/character_set/build_step6_enrich_pypinyin.py` - Enrichment script
- `/app/lib/characters.ts` - Added `getValidPinyins()` function
- `/app/lib/scoring.ts` - Updated `checkPinyin()` to validate against character_set
- `/app/app/practice/page.tsx` - Pass character to `checkPinyin()`
- `/scripts/sentences/improve_pinyin_with_openai.py` - OpenAI pinyin regeneration
- `/scripts/sentences/compare_pinyin_changes.py` - Analysis tool
- `/scripts/sentences/apply_verified_pinyin_changes.py` - Selective update tool
- `/scripts/sentences/convert_sentences_to_json.py` - Updated to use `_UPDATED.csv`

**Code Changes:**
```typescript
// Before: Only validated against sentence pinyin
checkPinyin(userInput, currentChar.pinyin)

// After: Validates against all character_set alternatives
checkPinyin(userInput, currentChar.pinyin, currentChar.char)
```

**Data Improvement:**
```csv
# Phase 1 - Character set enrichment:
# Before (step5_hsk.csv):
15874,谁,U+8C01,shuí(1065),simplified,誰,who,...

# After (step6_enriched.csv):
15874,谁,U+8C01,shuí(1065)|shei2,simplified,誰,who,...
```

```csv
# Phase 3 - Sentence-level context-aware pinyin:
# Before (original CSV):
79,你知不知道他们是谁?,你:ni3|知:zhi1|...|谁:shui2|?:,...

# After (UPDATED CSV with OpenAI improvements):
79,你知不知道他们是谁?,你:ni3|知:zhi1|...|谁:shei2|?:,...
```

**OpenAI Analysis Results:**
```
Total sentences:       79,603
Total characters:      788,948
Changed:               10,336 (1.31%)
Unchanged:             778,612 (98.69%)

Verified improvements: 2,870 (27.8% of changes) ✅
Errors/Questionable:   632 (6.1% of changes) ❌
Needs review:          6,834 (66.1% of changes) 🤔
```

---

## 3. Vertical Scrollbar Causes Navigation Alignment Shifts Between Pages

**Date:** 2025-10-21

**Problem:**
Navigation elements ("Hanzi Flow" and nav links) appeared slightly shifted to the right on the practice page compared to the settings and stats pages. Additionally, there was a jarring visual shift when navigating from settings → stats page, where the navigation would quickly jump right then back left.

**Investigation Process:**
1. Initially suspected different padding values or CSS structure between pages
2. Verified Navigation component was identical across all pages (same px-8 padding)
3. Checked computed positions in DevTools - all showed identical values
4. Measured computed widths of navigation elements - found tiny difference:
   - Settings page: 206.523px
   - Practice page: 206.281px
   - Difference: 0.242px
5. User observation: Settings/stats pages had vertical scrollbar, practice page didn't
6. **AHA moment**: Scrollbar takes up viewport width, causing `mx-auto` centering to shift

**Root Cause:**
Inconsistent vertical scrollbar presence across pages:
- **Practice page**: Content fits in viewport → no scrollbar → wider viewport
- **Settings/stats pages**: Content overflows → scrollbar appears → narrower viewport (scrollbar ~15-17px)

The Navigation component uses `max-w-4xl mx-auto` which centers based on available viewport width. When the viewport width changes due to scrollbar presence, the centering calculation shifts everything by ~7-8px (half the scrollbar width), making "Hanzi Flow" appear at different positions.

The jarring shift on stats page was caused by:
1. Stats loads with placeholder content (no scrollbar needed yet)
2. Data loads asynchronously from IndexedDB
3. Content renders, causing page to grow
4. Scrollbar appears, viewport shrinks
5. Navigation re-centers to narrower width → visible jump

**Additional Contributing Factor:**
Font rendering differences when navigation links are bold (`font-medium`) vs normal weight caused the right-side nav container to have slightly different widths (206.523px vs 206.281px). With `justify-between` layout, this tiny difference on the right side pushed the left side ("Hanzi Flow") by the same amount.

**Solution:**
Force vertical scrollbar to always be present on all pages using CSS:

```css
html {
  /* Force scrollbar to always show to prevent layout shift */
  overflow-y: scroll;
}
```

This reserves the scrollbar gutter space even when content doesn't overflow, ensuring:
- Consistent viewport width across all pages
- No layout shift when content loads and grows
- Navigation stays perfectly aligned

**Key Takeaways:**
- ⚠️ **Scrollbars affect viewport width** - appearance/disappearance causes layout shifts
- Use `overflow-y: scroll` on `html` to prevent scrollbar-induced layout shifts
- `mx-auto` centering is viewport-width dependent - scrollbar changes the center point
- DevTools computed positions can match but still have visual differences due to scrollbar
- Tiny font rendering differences (0.242px) become visible with `justify-between` layouts
- When debugging alignment issues, check scrollbar state across all pages
- Async content loading can trigger delayed scrollbar appearance
- **Testing tip**: Measure computed widths of flex children, not just container positions

**Related Files:**
- `/app/app/globals.css` - Added `overflow-y: scroll` to html element
- `/app/components/Navigation.tsx` - Navigation component (unchanged, but affected)

**Code Before:**
```css
@import "tailwindcss";

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Code After:**
```css
@import "tailwindcss";

html {
  /* Force scrollbar to always show to prevent layout shift */
  overflow-y: scroll;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Debugging Measurements:**
```
Practice page (no scrollbar):
- Right nav container width: 206.281px
- Viewport affected: wider by ~15px

Settings page (with scrollbar):
- Right nav container width: 206.523px
- Viewport affected: narrower by ~15px
- Result: Navigation centered differently
```

---

## Template for Future Entries

**Date:** YYYY-MM-DD

**Problem:**
[Brief description of the issue]

**Investigation Process:**
[How you debugged it, what you tried]

**Root Cause:**
[What actually caused the problem]

**Solution:**
[How you fixed it]

**Key Takeaways:**
[Bullet points of lessons learned]

**Related Files:**
[Files that were modified or are relevant]

**Code Before/After:**
[Optional code snippets showing the change]
