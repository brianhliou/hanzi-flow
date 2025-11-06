# Pinyin Format Migration Plan

**Status**: ✅ Ready for Execution
**Created**: 2025-11-06
**Updated**: 2025-11-06
**Goal**: Eliminate mixed pinyin formats, establish single source of truth, reduce technical debt

## DECISIONS MADE

**✓ Architecture**: Option A - pypinyin-only (eliminate Unihan for pinyin)
**✓ Storage Format**: Store BOTH formats in CSV (pinyins_tone3 + pinyins_display)
**✓ Frequency Location**: Frequencies only in pinyins_tone3 column (canonical)
**✓ Pipeline Structure**: Merge step2+6 → new step2, rename step7 → step6 (6 steps total)
**✓ Frequency Source**: Corpus-based (from sentence data) for both character-level AND pinyin-level

## Problem Summary

**Current State:**
- Mixed pinyin formats in character dataset (tone marks + tone3)
- 612 duplicate syllables (30.5% duplication)
- 69.8% of character-syllable mappings affected
- 6+ places with duplicate conversion logic
- Workaround scripts (`fix_pinyin_format.py`)

**Root Cause:**
- Unihan (step2) outputs tone marks: `lè(283)|yuè(54)`
- pypinyin (step6) outputs tone3: `zheng1|mo4`
- No normalization at ingestion → mixed storage → every consumer must dedupe

## Findings from Codebase Audit

### Existing Conversion Utilities

**Python (Scripts):**
1. `scripts/audio/enumerate_syllables_unihan.py`
   - `convert_tone_mark_to_number()` - converts tone marks → base + tone number
   - `convert_to_tone3()` - full syllable conversion
   - Used for audio enumeration

2. `scripts/character_set/misc/fix_pinyin_format.py`
   - Bidirectional conversion (tone marks ↔ tone3)
   - Created as workaround in Oct 2024
   - 235 lines - should be eliminated

3. `scripts/character_set/analysis/` (newly created)
   - `build_pinyin_trie.py` - normalization
   - `validate_trie_vs_reference.py` - normalization
   - `check_duplicate_syllables.py` - diagnostic

**TypeScript (App):**
1. `app/lib/pinyin.ts`
   - `convertToneMarksToNumbers()` - tone marks → tone3
   - `convertToneNumbers()` - tone3 → tone marks
   - Bidirectional, well-implemented
   - Currently used for app display

### pypinyin Library Capabilities

```python
from pypinyin import pinyin, Style

# Available output formats:
Style.TONE3      # "ni3hao3" - tone numbers (our target internal format)
Style.TONE       # "nǐhǎo" - tone marks (for display)
Style.TONE2      # "ni3ha03" - with explicit neutral
Style.NORMAL     # "nihao" - no tones
```

**Key Discovery**: pypinyin can output ANY format we need!

### Data Sources

**Step 2: Unihan Database**
- Provides: kHanyuPinlu (with frequency), kHanyuPinyin, kMandarin
- Output format: Tone marks with frequency → `lè(283)|yuè(54)`
- Pros: Has frequency data, comprehensive
- Cons: Tone mark format, needs conversion

**Step 6: pypinyin Library**
- Provides: All pronunciations (formal + colloquial)
- Output format: Currently `Style.TONE` (tone marks), but configurable
- Pros: Comprehensive, heteronyms, format flexibility, actively maintained
- Cons: No frequency data (but we compute corpus frequency anyway)

## Proposed Solutions

### ✅ APPROVED: pypinyin-Only with Dual Format Storage

**Eliminate Unihan for pinyin, use only pypinyin outputting BOTH formats**

#### Final Architecture
```
┌────────────────────────────────────────────────────────────┐
│  Step 2: pypinyin-based pinyin (BOTH formats)             │
│  - Style.TONE3 → pinyins_tone3: yi1|yi4                   │
│  - Style.TONE → pinyins_display: yī|yì                    │
│  - heteronym=True for all pronunciations                  │
│  - Guaranteed consistency (same library, same order)      │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│  Steps 3-5: Pass through both columns                     │
│  - step3_cedict.csv (glosses/examples)                    │
│  - step4_variants.csv (variants)                          │
│  - step5_hsk.csv (HSK levels)                             │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│  Step 6: Add corpus frequencies (RENAMED from step7)      │
│  - Count character-pinyin pairs from sentence corpus      │
│  - Add freq to pinyins_tone3: yi1(11652)|yi4(543)        │
│  - Keep pinyins_display unchanged: yī|yì                  │
│  - Also add total char freq column                        │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│  FINAL: step6_with_freq.csv                               │
│  - pinyins_tone3: yi1(11652)|yi4(543) ← canonical + freq │
│  - pinyins_display: yī|yì ← for rendering (no freq)      │
│  - freq: 12195 ← total character frequency                │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│  App: Use pinyins_display directly                        │
│  - No conversion needed                                    │
│  - Can optimize later if desired                           │
└────────────────────────────────────────────────────────────┘
```

#### Changes Required

**1. Create New Step 2 (pypinyin with BOTH formats)**
```python
# New: scripts/character_set/build_step2_pinyin_pypinyin.py

def add_pinyin_to_csv():
    """Add pinyins in BOTH formats using pypinyin"""
    for row in characters:
        char = row['char']

        # Get tone3 format
        tone3_result = pinyin(char, style=Style.TONE3, heteronym=True)
        # Get tone mark format
        display_result = pinyin(char, style=Style.TONE, heteronym=True)

        if tone3_result and len(tone3_result) > 0:
            # Verify same count (sanity check)
            assert len(tone3_result[0]) == len(display_result[0]), \
                f"Format mismatch for {char}"

            # Store BOTH formats
            row['pinyins_tone3'] = '|'.join(tone3_result[0])
            row['pinyins_display'] = '|'.join(display_result[0])
        else:
            row['pinyins_tone3'] = ''
            row['pinyins_display'] = ''

# Output CSV columns:
# id, char, codepoint, pinyins_tone3, pinyins_display
```

**2. Update Steps 3-5 (pass through both columns)**
```python
# build_step3_cedict.py, build_step4_variants.py, build_step5_hsk.py
# No logic changes needed - just pass through both pinyin columns
# Output includes: pinyins_tone3, pinyins_display, + their new columns
```

**3. Rename & Update Step 7 → Step 6 (add frequencies)**
```python
# Rename: build_step7_freq.py → build_step6_freq.py
# Update paths: step6_enriched.csv → step5_hsk.csv (input)
#               step7_with_freq.csv → step6_with_freq.csv (output)

def parse_sentence_corpus():
    """Count character-pinyin pairs from sentence corpus"""
    char_counter = Counter()  # character → total count
    char_pinyin_counter = Counter()  # (character, pinyin_tone3) → count

    for row in reader:
        pairs = parse_char_pinyin_pairs(row['char_pinyin_pairs'])
        # pairs = [('地', 'de'), ('的', 'de'), ...]

        for char, pinyin in pairs:
            if is_chinese_character(char):
                char_counter[char] += 1
                char_pinyin_counter[(char, pinyin)] += 1

    return char_counter, char_pinyin_counter

def add_frequency_to_csv(char_counter, char_pinyin_counter):
    """Add corpus frequencies to pinyins_tone3 column only"""
    for row in rows:
        char = row['char']

        # Get tone3 pinyins (canonical)
        pinyins_tone3_list = row['pinyins_tone3'].split('|') if row['pinyins_tone3'] else []

        # Add frequencies to tone3 format (canonical)
        pinyins_with_freq = []
        for py in pinyins_tone3_list:
            freq = char_pinyin_counter.get((char, py), 0)
            if freq > 0:
                pinyins_with_freq.append(f"{py}({freq})")
            else:
                pinyins_with_freq.append(py)  # No freq data

        row['pinyins_tone3'] = '|'.join(pinyins_with_freq)
        # row['pinyins_display'] unchanged (no freq)

        # Total character frequency
        row['freq'] = char_counter.get(char, 0)

# Final output columns:
# ..., pinyins_tone3, pinyins_display, ..., freq
```

**4. Update reference data**
```python
# scripts/audio/enumerate_syllables_unihan.py
# Rename to: enumerate_syllables_pypinyin.py

# Generate both formats using pypinyin (same as character CSV):
def build_reference():
    for char in all_corpus_chars:
        tone3_result = pinyin(char, style=Style.TONE3, heteronym=True)
        display_result = pinyin(char, style=Style.TONE, heteronym=True)

        for t3, disp in zip(tone3_result[0], display_result[0]):
            syllables[t3] = {
                "pinyin_tone3": t3,      # "yi4"
                "pinyin_display": disp,  # "yì"
                "base": extract_base(t3),  # "yi"
                "tone": extract_tone(t3)   # 4
            }
```

**5. Delete obsolete files**
- `scripts/character_set/build_step2_pinyin.py` (old Unihan-based, replaced)
- `scripts/character_set/build_step6_enrich_pypinyin.py` (merged into new step2)
- `scripts/character_set/misc/fix_pinyin_format.py` (no longer needed)
- Old `data/character_set/step2_pinyin.csv` through `step6_enriched.csv` (will be regenerated)
- Old `data/character_set/step7_with_freq.csv` (renamed to step6_with_freq.csv)

#### Benefits
- ✅ **Zero format inconsistencies** - single source (pypinyin), guaranteed consistency
- ✅ **Dual format storage** - both tone3 (canonical) and display (tone marks) in CSV
- ✅ **Simpler pipeline** - 6 steps instead of 7 (merge step2+6)
- ✅ **No conversion needed in app** - use pinyins_display directly
- ✅ **Corpus-based frequencies** - both character-level AND pinyin-level from sentence data
- ✅ **Comprehensive coverage** - pypinyin knows formal + colloquial pronunciations
- ✅ **Future-proof** - actively maintained library
- ✅ **Eliminate technical debt** - delete 3 workaround/duplicate scripts

#### Tradeoffs
- ⚠️ Lose Unihan frequency data
  - ✅ **Mitigation**: Corpus frequencies more relevant and complete (covers all pypinyin outputs)
  - ✅ **Better**: Context-aware from OpenAI-refined sentence pinyins
- ⚠️ Redundant storage (two pinyin columns)
  - ✅ **Acceptable**: Clarity > optimization, can optimize later
  - ✅ **Benefit**: No conversion logic needed anywhere
- ⚠️ pypinyin might differ from Unihan for obscure characters
  - ✅ **Mitigation**: Verify coverage with sample check (Phase 1)
  - ✅ **Estimate**: >99% overlap for characters in corpus

---

### Option B: Keep Both Sources, Normalize Immediately

**Keep Unihan + pypinyin, but normalize at ingestion**

#### Architecture
```
┌─────────────────────────────────────────────┐
│  Step 2: Unihan → NORMALIZE → tone3        │
│  - Parse Unihan (tone marks)               │
│  - Convert to tone3 immediately            │
│  - Output: yi4(32747)|yi1(1065)            │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Step 6: pypinyin → FORCE tone3            │
│  - Use Style.TONE3 directly                │
│  - Merge with existing (base comparison)   │
│  - Output: yi4(32747)|yi1(1065)|yi2        │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  ALL DATA: 100% tone3 format               │
│  - Format validation between steps         │
└─────────────────────────────────────────────┘
```

#### Changes Required

**1. Update step2: Add normalization**
```python
# scripts/character_set/build_step2_pinyin.py

from utils.pinyin_converter import convert_to_tone3

def parse_unihan_readings():
    # ... existing parsing ...

    # NEW: Normalize to tone3
    pinyins_normalized = []
    for pinyin, freq in pinyins_with_freq:
        tone3 = convert_to_tone3(pinyin)
        pinyins_normalized.append(f"{tone3}({freq})")

    return '|'.join(pinyins_normalized)
```

**2. Update step6: Use TONE3 style**
```python
# scripts/character_set/build_step6_enrich_pypinyin.py

def get_pypinyin_with_tones(char):
    # OLD: style=Style.TONE
    # NEW: style=Style.TONE3
    result = pinyin(char, style=Style.TONE3, heteronym=True)
    ...
```

**3. Create conversion utility**
```python
# NEW: scripts/utils/pinyin_converter.py

def convert_to_tone3(pinyin_with_marks):
    """Convert tone marks → tone3 format"""
    # Reuse logic from app/lib/pinyin.ts or enumerate_syllables_unihan.py
    ...

def convert_to_tone_marks(pinyin_tone3):
    """Convert tone3 → tone marks for display"""
    # Reuse logic from app/lib/pinyin.ts
    ...
```

**4. Add validation**
```python
def validate_pinyin_format(pinyins_str):
    """Ensure all pinyins are tone3 format"""
    for pinyin in pinyins_str.split('|'):
        base = re.sub(r'\(\d+\)', '', pinyin)
        if not re.match(r'^[a-z]+[0-4]$', base):
            raise ValueError(f"Invalid format: {pinyin}")
```

#### Benefits
- ✅ Keep Unihan frequency data
- ✅ Keep both data sources (redundancy)
- ✅ Consistent format throughout pipeline

#### Tradeoffs
- ⚠️ More complex than Option A
- ⚠️ Still need conversion utility
- ⚠️ Two sources = more maintenance
- ⚠️ Redundancy adds little value (pypinyin knows everything Unihan knows)

---

## Recommendation: Option A (pypinyin-Only)

**Rationale:**
1. **Simplicity** - One source → one format → no conversions
2. **pypinyin coverage** - Comprehensive, includes everything we need
3. **Corpus frequency** - We already compute actual usage frequency (more relevant than Unihan)
4. **Maintainability** - Fewer moving parts, fewer places to break
5. **Technical debt elimination** - Delete workaround scripts entirely

**Verification Before Commitment:**
- [ ] Sample 100 random characters: Compare Unihan vs pypinyin coverage
- [ ] Check obscure characters: Verify pypinyin has them
- [ ] Compare pinyin differences: Document any discrepancies
- [ ] Expected result: >99% coverage, <1% differences (acceptable)

---

## Implementation Phases

### Phase 1: Foundation & Verification (1.5 hours)

**Goals:**
- Verify pypinyin coverage is sufficient
- Verify pypinyin outputs match between formats
- No data changes yet

**Tasks:**
1. **Create comparison script**
   ```bash
   scripts/character_set/analysis/compare_unihan_vs_pypinyin.py
   ```
   - Sample 500-1000 characters from corpus
   - Compare Unihan pinyins vs pypinyin pinyins
   - Report: coverage %, differences, missing characters
   - Output: verification_report.txt

2. **Verify pypinyin dual-format consistency**
   ```python
   # Test that Style.TONE3 and Style.TONE return same count/order
   for char in sample_chars:
       tone3 = pinyin(char, style=Style.TONE3, heteronym=True)
       display = pinyin(char, style=Style.TONE, heteronym=True)
       assert len(tone3[0]) == len(display[0]), f"Mismatch for {char}"
   ```

3. **~~Create conversion utility~~** (NOT NEEDED)
   - We'll store both formats directly
   - No conversion logic required in pipeline
   - App can use pinyins_display directly

**Verification Checkpoint:**
- [ ] pypinyin coverage >99% for corpus characters
- [ ] pypinyin dual formats have same count/order for all test characters
- [ ] **Decision point**: Proceed with migration (if coverage good)

### Phase 2: Pipeline Rewrite (3 hours)

**Goals:**
- Create new step2 (pypinyin with dual formats)
- Update steps 3-5 to pass through both columns
- Rename step7 → step6 and add pinyin-level frequencies
- Add validation

**Tasks:**
1. **Create new step2**
   ```bash
   scripts/character_set/build_step2_pinyin_pypinyin.py
   ```
   - Replace Unihan with pypinyin
   - Output BOTH formats: `Style.TONE3` and `Style.TONE`
   - Add assertion: verify same count/order
   - Output columns: pinyins_tone3, pinyins_display

2. **Update steps 3-5 (minor)**
   ```bash
   build_step3_cedict.py, build_step4_variants.py, build_step5_hsk.py
   ```
   - No logic changes
   - Just ensure both pinyin columns are passed through
   - Verify fieldnames include both

3. **Rename & update step7 → step6**
   ```bash
   mv build_step7_freq.py build_step6_freq.py
   ```
   - Update input path: step6_enriched → step5_hsk
   - Update output path: step7_with_freq → step6_with_freq
   - Add pinyin-level frequency counting (not just character-level)
   - Parse sentence corpus char_pinyin_pairs
   - Add freq to pinyins_tone3 only (canonical)

4. **Update README documentation**
   - Document: "pinyins_tone3 (canonical), pinyins_display (for rendering)"
   - Update pipeline: 6 steps instead of 7
   - Update file naming: step6_with_freq.csv (final)

**Verification Checkpoint:**
- [ ] New step2 outputs both format columns correctly
- [ ] Steps 3-5 pass through both columns
- [ ] Step6 adds frequencies to pinyins_tone3 only
- [ ] Character count matches old pipeline (20,992)
- [ ] Sample 50 characters manually - both formats look correct

### Phase 3: Data Migration (2 hours)

**Goals:**
- Run new pipeline
- Validate output
- Compare with old data

**Tasks:**
1. **Backup current data**
   ```bash
   git status  # Ensure clean
   # Git history is our backup
   ```

2. **Run new pipeline** (steps 1-6)
   ```bash
   cd scripts/character_set
   python3 build_step1_base.py
   python3 build_step2_pinyin_pypinyin.py  # NEW - dual formats
   python3 build_step3_cedict.py           # Updated - pass through both
   python3 build_step4_variants.py         # Updated - pass through both
   python3 build_step5_hsk.py              # Updated - pass through both
   python3 build_step6_freq.py             # RENAMED from step7, updated for pinyin-level freq
   ```

3. **Validation suite**
   ```bash
   scripts/character_set/analysis/validate_migration.py
   ```
   - Compare old vs new:
     - Character count (should match: 20,992)
     - Characters with pinyin (should be similar: ~99.7%)
     - Pinyin count per character (compare sample)
   - Check format:
     - pinyins_tone3: all tone3 format (e.g., yi4, zhong1, de0)
     - pinyins_display: all tone marks (e.g., yì, zhōng, de)
     - Same count/order between columns
     - Frequencies in pinyins_tone3 only
   - Check frequencies:
     - Character-level freq column populated
     - Pinyin-level freqs in pinyins_tone3
     - Total makes sense (sum of pinyin freqs ≈ character freq)

4. **Manual spot checks**
   - Review 100 random characters
   - Check polyphonic characters (的, 地, 了, etc.)
   - Verify frequency data intact

**Verification Checkpoint:**
- [ ] Character counts match (20,992)
- [ ] Pinyin coverage similar to old (~99.7%)
- [ ] Both format columns populated correctly
- [ ] pinyins_tone3 has frequencies, pinyins_display does not
- [ ] Spot checks look good
- [ ] No obvious regressions

### Phase 4: Trie & Analysis Update (1 hour)

**Goals:**
- Update Trie builder to use pinyins_tone3 column directly
- Remove normalization logic (no longer needed)
- Regenerate reference data with both formats

**Tasks:**
1. **Update Trie builder**
   ```python
   # scripts/character_set/analysis/build_pinyin_trie.py
   # CHANGE: Read from pinyins_tone3 column instead of pinyins
   # REMOVE: normalize_to_tone3() function (no longer needed)
   # REMOVE: TONE_MARK_TO_NUMBER mapping (no longer needed)
   # Input already in tone3 format, no conversion required

   def parse_pinyin_field(pinyins_str):
       # Parse pinyins_tone3: "yi1(11652)|yi4(543)"
       # Extract tone3 and freq
       # No normalization needed!
   ```

2. **Rebuild Trie**
   ```bash
   cd scripts/character_set/analysis
   python3 build_pinyin_trie.py
   ```
   - Should still get 1,392 syllables
   - Zero duplicates (no normalization = no dupes!)
   - Simpler code

3. **Update reference data script**
   ```bash
   # Rename: enumerate_syllables_unihan.py → enumerate_syllables_pypinyin.py
   scripts/audio/enumerate_syllables_pypinyin.py
   ```
   - Use pypinyin (same as character CSV)
   - Output both formats using Style.TONE3 and Style.TONE
   - Generate: data/audio/syllables_enumeration.json

**Verification Checkpoint:**
- [ ] Trie has 1,392 syllables (same as before)
- [ ] Zero duplicates (no normalization needed)
- [ ] Trie code simpler (no conversion logic)
- [ ] Reference data has both formats from pypinyin

### Phase 5: Cleanup (1 hour)

**Goals:**
- Delete obsolete code
- Update documentation
- Test app

**Tasks:**
1. **Delete obsolete files**
   ```bash
   # Old pipeline scripts (replaced):
   rm scripts/character_set/build_step2_pinyin.py  # Replaced by build_step2_pinyin_pypinyin.py
   rm scripts/character_set/build_step6_enrich_pypinyin.py  # Merged into new step2

   # Workaround scripts (no longer needed):
   rm scripts/character_set/misc/fix_pinyin_format.py

   # Old data files (regenerated with new pipeline):
   rm data/character_set/step2_pinyin.csv  # Old format
   rm data/character_set/step3_cedict.csv  # Will regenerate
   rm data/character_set/step4_variants.csv
   rm data/character_set/step5_hsk.csv
   rm data/character_set/step6_enriched.csv  # Old step6
   rm data/character_set/step7_with_freq.csv  # Renamed to step6_with_freq.csv

   # Optionally delete old analysis data if regenerating:
   # rm data/character_set/analysis/pinyin_trie.json  # Will rebuild
   ```

2. **Rename files**
   ```bash
   # Rename step7 → step6
   git mv scripts/character_set/build_step7_freq.py scripts/character_set/build_step6_freq.py

   # Rename Unihan → pypinyin (audio reference)
   git mv scripts/audio/enumerate_syllables_unihan.py scripts/audio/enumerate_syllables_pypinyin.py
   ```

3. **Update documentation**
   - `scripts/character_set/README.md`
     - Update pipeline steps (1-6 instead of 1-7)
     - Document dual format storage
     - Update file names (step6_with_freq.csv)
   - `scripts/character_set/analysis/README.md`
     - Update Trie builder description (no normalization)
   - `LESSONS_LEARNED.md`
     - Mark migration as complete
     - Add "Resolved" status

4. **Test app**
   - Run app locally: `npm run dev`
   - Check character display uses pinyins_display
   - Test practice mode with various characters
   - Verify scoring accepts valid alternatives
   - Check console for errors

5. **Git commit**
   ```bash
   git add -A
   git status  # Review changes
   git commit -m "Migrate to pypinyin-only: dual-format storage, 6-step pipeline, eliminate mixed formats and workarounds"
   git push
   ```

**Final Verification:**
- [ ] Obsolete files deleted
- [ ] Documentation updated (README, LESSONS_LEARNED)
- [ ] App displays tone marks correctly (using pinyins_display)
- [ ] Scoring works for all valid alternatives
- [ ] No console errors
- [ ] Committed and pushed

---

## Rollback Plan

If migration fails at any phase:

**Phase 1-2 (Before data changes):**
- Simply don't proceed
- Keep existing pipeline
- Zero rollback needed

**Phase 3-5 (After data changes):**
```bash
# Revert to previous commit
git log --oneline -10  # Find commit before migration
git reset --hard <commit-hash>
git push --force  # Only if already pushed

# Rebuild old pipeline to restore data
cd scripts/character_set
./run_full_pipeline.sh  # Or manual steps 1-7 with old scripts
```

---

## Success Criteria

**After migration complete:**
- ✅ Dual-format storage: pinyins_tone3 (canonical) + pinyins_display (tone marks)
- ✅ Single source: pypinyin for both formats (guaranteed consistency)
- ✅ Zero duplicate syllables in Trie
- ✅ Character count unchanged (20,992)
- ✅ Pinyin coverage >99%
- ✅ Corpus-based frequencies (both character-level AND pinyin-level)
- ✅ App uses pinyins_display directly (no conversion needed)
- ✅ Scoring works for all valid alternatives
- ✅ Obsolete code deleted (old step2, old step6, fix_pinyin_format.py)
- ✅ Documentation updated
- ✅ Pipeline simpler (6 steps instead of 7)

**Measurements:**
| Metric | Before | After |
|--------|--------|-------|
| Syllables (Trie) | 2,004 | 1,392 |
| Duplicates | 612 (30.5%) | 0 (0%) |
| Format consistency | Mixed (58% marks + 33% tone3 + 9% neutral) | Dual (100% tone3 canonical + 100% marks display) |
| Pinyin source | Unihan + pypinyin | pypinyin only |
| Conversion utilities | 6+ scattered | 0 (direct storage) |
| Pipeline steps | 7 | 6 |
| Workaround scripts | 2 (235 lines) | 0 |
| Frequency source | Unihan (unknown corpus) | Sentence corpus (context-aware) |
| CSV columns | pinyins (mixed) | pinyins_tone3 + pinyins_display |

---

## Timeline

**Conservative estimate: 8.5 hours total**
- Phase 1: 1.5 hours (verification - no conversion utility needed)
- Phase 2: 3 hours (pipeline rewrite)
- Phase 3: 2 hours (data migration)
- Phase 4: 1 hour (trie & reference updates)
- Phase 5: 1 hour (cleanup & testing)

**Could be done in one focused day**

**Recommendation: Do in 2-3 sessions**
- Session 1: Phase 1 + 2 (verification + pipeline rewrite) ~ 4.5 hours
- Session 2: Phase 3 + 4 (migration + analysis updates) ~ 3 hours
- Session 3: Phase 5 (cleanup + testing) ~ 1 hour

---

## Next Steps

**✅ PLAN APPROVED - Ready to Execute**

1. ✅ **Review complete** - Final decisions made:
   - Option A: pypinyin-only
   - Dual-format storage (tone3 + display)
   - Frequencies only in canonical format
   - 6-step pipeline

2. **Start Phase 1** - Verification (1.5 hours)
   - Create comparison script (Unihan vs pypinyin)
   - Verify dual-format consistency
   - **Decision checkpoint**: If coverage >99%, proceed

3. **Execute Phases 2-5** with verification at each checkpoint

4. **Expected outcome**:
   - Clean, consistent data (one source, dual format)
   - Simpler pipeline (6 steps, no workarounds)
   - Better frequencies (corpus-based, context-aware)

---

**Document Status**: ✅ **APPROVED - Ready for Execution**
**Created**: 2025-11-06
**Last Updated**: 2025-11-06 (finalized after decision discussion)
