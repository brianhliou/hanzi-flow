# Step 5: Pinyin Refinement (Optional)

This directory contains the 3-substep workflow for refining pinyin using OpenAI's context-aware analysis.

## Overview

Pypinyin assigns pinyin automatically based on character readings, but lacks context for heteronyms (characters with multiple valid pronunciations). For example:
- 地 (de vs di4): Particle vs noun
- 著 (zhe vs zhu4): Aspect marker vs verb
- 谁/誰 (shei2 vs shui2): Colloquial vs formal

This workflow uses OpenAI GPT-4o-mini to generate context-aware pinyin, compares it against pypinyin output, and selectively applies verified improvements.

## Workflow (3 Substeps)

### Step 5a: Generate OpenAI Pinyin
```bash
python3 step5a_generate_openai_pinyin.py
```

**What it does:**
- Reads production sentence JSON (79k sentences with pypinyin)
- Sends batches of 10 sentences to OpenAI GPT-4o-mini
- Generates context-aware pinyin with tone marks for ALL characters
- Saves incrementally with checkpointing (resume on failure)

**Input:** `../../../app/public/data/sentences/sentences_with_translation.json`
**Output:** `../../../data/sentences/step5/sentences_pinyin_openai.json` (86MB)

**Cost:** ~$8-10
**Time:** 4-5 hours (with 2s rate limit delay)

**Options:**
```bash
# Test with 10 sentences
python3 step5a_generate_openai_pinyin.py --limit 10

# Test with 100 sentences
python3 step5a_generate_openai_pinyin.py --limit 100

# Full run (all sentences)
python3 step5a_generate_openai_pinyin.py
```

---

### Step 5b: Compare Pypinyin vs OpenAI
```bash
python3 step5b_compare_pinyin.py
```

**What it does:**
- Compares original pypinyin against OpenAI output character-by-character
- Identifies all differences (10,336 changes across 788k characters = 1.3%)
- Generates detailed report with examples and frequency analysis

**Inputs:**
- `../../../app/public/data/sentences/sentences_with_translation.json` (original)
- `../../../data/sentences/step5/sentences_pinyin_openai.json` (OpenAI)

**Output:** `../../../data/sentences/step5/pinyin_comparison_report.json` (2.8MB)

**Report includes:**
- Total changes by character (e.g., 覺 changed 120 times)
- Top changed characters with examples
- Sentence-level change details

---

### Step 5c: Apply Verified Changes
```bash
cd ../../  # Return to scripts/sentences/
python3 build_step5_refine_pinyin.py
```

**What it does:**
- Reads comparison report from step 5b
- Applies changes for ONLY 9 verified characters:
  - 地, 著, 谁, 誰, 覺, 觉, 長, 长, 樂
- Updates `char_pinyin_pairs` in CSV format
- Logs all applied changes

**Inputs:**
- `../../data/sentences/step4_with_hsk.csv`
- `../../data/sentences/step5/pinyin_comparison_report.json`

**Outputs:**
- `../../data/sentences/step5_pinyin_refined.csv` (final output)
- `../../data/sentences/step5/pinyin_changes_applied.log` (324KB change log)

**Safety features:**
- Dry-run mode (preview changes)
- Incremental limits (test with 1, 10, 100 first)
- Only updates verified characters (manually curated list)

**Options:**
```bash
# Dry run - preview 10 changes
python3 build_step5_refine_pinyin.py --limit 10 --dry-run

# Test with 1 change
python3 build_step5_refine_pinyin.py --limit 1

# Apply all verified changes
python3 build_step5_refine_pinyin.py
```

---

## Why This Approach?

1. **Selective application:** Only 9 characters are updated (high-confidence improvements)
2. **Cost-effective:** $8-10 one-time cost for comprehensive analysis
3. **Reproducible:** All intermediate files saved for review
4. **Safe:** Dry-run mode + incremental testing + detailed logging

## Intermediate Files

All intermediate files stored in `data/sentences/step5/`:
- `sentences_pinyin_openai.json` (86MB) - Full OpenAI output
- `sentences_pinyin_openai.json.errors.log` - API errors during generation
- `pinyin_comparison_report.json` (2.8MB) - Detailed diff analysis
- `pinyin_changes_applied.log` (324KB) - What changes were applied

## Verified Characters

These 9 characters are the ONLY ones updated by step 5c:

| Character | Issue | Example |
|-----------|-------|---------|
| 地 | Particle (de) vs noun (di4) | 我慢慢**地**走 |
| 著 | Aspect marker (zhe) vs verb (zhu4) | 看**著**电视 |
| 谁/誰 | Colloquial (shei2) vs formal (shui2) | **谁**在那儿？ |
| 覺/觉 | Sleep (jiao4) vs feel (jue2) | 睡**覺** |
| 長/长 | Long (chang2) vs grow (zhang3) | **長**大 |
| 樂 | Music (yue4) vs happy (le4) | 音**樂** |

## Full Pipeline Context

Step 5 is optional in the main sentence pipeline:
- **Step 4** → `step4_with_hsk.csv` (with HSK classification)
- **Step 5** → `step5_pinyin_refined.csv` (optional pinyin refinement) ← YOU ARE HERE
- **Step 6** → Production JSON export

If you skip step 5, step 6 will read from step 4 instead.

## Cost & Time Breakdown

| Substep | Cost | Time | Output Size |
|---------|------|------|-------------|
| 5a (OpenAI) | $8-10 | 4-5 hrs | 86MB |
| 5b (Compare) | Free | ~1 min | 2.8MB |
| 5c (Apply) | Free | ~5 sec | 324KB log |
| **Total** | **$8-10** | **~5 hrs** | **89MB intermediate** |

## Notes

- Step 5a can be resumed if interrupted (uses checkpointing)
- The 86MB OpenAI output is not tracked in git (too large)
- Comparison report and change log are tracked for reproducibility
- Only run step 5a once - reuse outputs for subsequent refinements
