# Pinyin Format Migration - Executive Summary

**Status**: ✅ Planning Complete - Ready for Execution
**Date**: 2025-11-06

## Quick Overview

**Problem**: Mixed pinyin formats causing 612 duplicate syllables, scattered conversion logic, technical debt

**Solution**: Migrate to pypinyin-only with dual-format storage (tone3 + display)

**Impact**:
- Eliminate 612 duplicates (30.5% → 0%)
- Simplify pipeline (7 steps → 6 steps)
- Delete 3 workaround scripts
- Better frequencies (corpus-based vs Unihan)

## Final Decisions

### 1. Architecture: pypinyin-Only ✓
- **Eliminate Unihan** for pinyin (keep for other fields if needed)
- **Single source**: pypinyin for all pronunciations
- **Why**: Comprehensive, format-flexible, actively maintained

### 2. Storage Format: Dual Columns ✓
```csv
pinyins_tone3: yi1|yi4          ← canonical (with frequencies)
pinyins_display: yī|yì          ← for rendering (no frequencies)
```

- **Why**: No conversion needed anywhere, guaranteed consistency, can optimize later
- **Trade-off**: Redundant storage (acceptable - clarity > optimization)

### 3. Frequency Source: Sentence Corpus ✓
- **Character-level**: Total occurrences in corpus
- **Pinyin-level**: Each character-pinyin pair counted separately
- **Source**: `step5_pinyin_refined.csv` (OpenAI-refined, context-aware)
- **Why**: More relevant than Unihan, context-aware, complete coverage

### 4. Pipeline Structure: 6 Steps ✓
```
OLD (7 steps):                  NEW (6 steps):
1. Base                         1. Base
2. Pinyin (Unihan)             2. Pinyin (pypinyin, dual format) ← MERGED
3. CEDICT                       3. CEDICT
4. Variants                     4. Variants
5. HSK                          5. HSK
6. Enrich (pypinyin)           [deleted - merged into step2]
7. Frequency                    6. Frequency ← RENAMED, ENHANCED
```

## Implementation Plan

**Total Time**: ~8.5 hours over 2-3 sessions

### Session 1: Verification & Pipeline Rewrite (~4.5 hours)
- **Phase 1**: Verify pypinyin coverage >99%
- **Phase 2**: Write new step2, update steps 3-5, rename step7→6

### Session 2: Migration & Updates (~3 hours)
- **Phase 3**: Run new pipeline, validate output
- **Phase 4**: Update Trie builder, regenerate reference data

### Session 3: Cleanup & Testing (~1 hour)
- **Phase 5**: Delete obsolete code, update docs, test app

## Key Files Changed

**Created:**
- `scripts/character_set/build_step2_pinyin_pypinyin.py` (new)

**Modified:**
- `scripts/character_set/build_step3_cedict.py` (pass through both columns)
- `scripts/character_set/build_step4_variants.py` (pass through both columns)
- `scripts/character_set/build_step5_hsk.py` (pass through both columns)
- `scripts/character_set/build_step6_freq.py` (renamed from step7, add pinyin-level freq)
- `scripts/character_set/analysis/build_pinyin_trie.py` (remove normalization)
- `scripts/audio/enumerate_syllables_pypinyin.py` (renamed from unihan)

**Deleted:**
- `scripts/character_set/build_step2_pinyin.py` (old Unihan-based)
- `scripts/character_set/build_step6_enrich_pypinyin.py` (merged into new step2)
- `scripts/character_set/misc/fix_pinyin_format.py` (workaround - no longer needed)

## Expected Results

**Data Quality:**
- ✅ 1,392 unique syllables (down from 2,004)
- ✅ 0 duplicates (down from 612)
- ✅ 100% format consistency (pypinyin for both formats)
- ✅ Corpus-based frequencies (character + pinyin level)

**Code Quality:**
- ✅ 0 conversion utilities needed (down from 6+)
- ✅ 6 pipeline steps (down from 7)
- ✅ 0 workaround scripts (down from 2)
- ✅ Simpler Trie builder (no normalization logic)

**Developer Experience:**
- ✅ Single source of truth (pypinyin)
- ✅ Clear data format (pinyins_tone3 = canonical, pinyins_display = rendering)
- ✅ Better documentation
- ✅ No mixed formats to debug

## Risk Mitigation

**Verification Checkpoints:**
- Phase 1: Verify coverage before proceeding
- Phase 2: Validate pipeline output before data migration
- Phase 3: Compare old vs new data before cleanup
- Each phase has clear success criteria

**Rollback Plan:**
- Git history = backup
- Can revert at any checkpoint
- Old scripts preserved until final cleanup

## Success Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Duplicate syllables | 612 | 0 | **-100%** |
| Conversion scripts | 6+ | 0 | **Eliminated** |
| Pipeline steps | 7 | 6 | **-14%** |
| Format consistency | Mixed | 100% dual | **Clean** |
| Frequency source | Unihan | Corpus | **More relevant** |

## Next Action

**START PHASE 1**: Create `compare_unihan_vs_pypinyin.py` to verify pypinyin coverage

---

**For detailed implementation plan, see**: `PINYIN_FORMAT_MIGRATION_PLAN.md`
**For lessons learned, see**: `LESSONS_LEARNED.md` (Section 4)
