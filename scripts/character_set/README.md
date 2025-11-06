# Character Set Generation Scripts

Scripts to build the Chinese character dataset from source data.

## Source Data

Located in `../../data/sources/`:
- `Unihan_Variants.txt` - Simplified/Traditional variant mappings
- `cedict_ts.u8` - CC-CEDICT Chinese-English dictionary
- `s2t.json`, `t2s.json` - OpenCC simplified/traditional mappings (not currently used)
- `junda_char_freq.txt` - Jun Da character frequency list (for future use)

**Note**: Pinyin data now comes exclusively from **pypinyin** library (not Unihan_Readings.txt)

## Build Pipeline

All scripts should be run from the `scripts/character_set/` directory. Run in order:

### Step 1: Base Character Set
```bash
python3 build_step1_base.py
```
- Generates 20,992 characters from CJK Unified Ideographs (U+4E00 to U+9FFF)
- Output: `../../data/build_artifacts/step1_base.csv` with columns: `id`, `char`, `codepoint`

### Step 2: Pinyin Readings (pypinyin-only)
```bash
python3 build_step2_pinyin_pypinyin.py
```
- Uses **pypinyin** library as single source of truth for all pronunciations
- Gets all heteronym pronunciations with `heteronym=True`
- **Dual-format storage** (no conversion needed anywhere):
  - `pinyins_tone3`: Canonical format with tone numbers (e.g., `yi1|yi4`) - used for matching/logic
  - `pinyins_display`: Display format with tone marks (e.g., `yī|yì`) - used for rendering
- Both formats guaranteed to have same count and order
- 100% coverage (20,992/20,992 characters)
- Frequencies added later in step6
- Output: `../../data/character_set/step2_pinyin.csv` adds columns: `pinyins_tone3`, `pinyins_display`

### Step 3: Glosses and Examples
```bash
python3 build_step3_cedict.py
```
- Parses CC-CEDICT for English glosses and example words
- Single-character entries → glosses
- Multi-character words → examples (up to 3 per character)
- Passes through both pinyin columns unchanged
- Output: `../../data/character_set/step3_cedict.csv` adds columns: `gloss_en`, `examples`

### Step 4: Script Types and Variants
```bash
python3 build_step4_variants.py
```
- Parses Unihan_Variants.txt for simplified/traditional mappings
- Determines script_type: simplified, traditional, neutral, or ambiguous
- Creates bidirectional variant links (e.g., 发 ↔ 發|髮)
- Filters out self-referential variants
- Passes through both pinyin columns unchanged
- Output: `../../data/character_set/step4_variants.csv` adds columns: `script_type`, `variants`

### Step 5: HSK Level Classification
```bash
python3 build_step5_hsk.py
```
- Downloads HSK 3.0 character lists (levels 1-9) from elkmovie/hsk30 repo
- Saves source files to `../../data/sources/elkmovie_hsk30/` (HSK_1.txt through HSK_7-9.txt)
- Assigns HSK levels to simplified characters from official lists
- Propagates HSK levels to traditional variants via our variant mappings
- Characters not in HSK 1-9 curriculum: assigned empty/null hsk_level
- Uses dynamic fieldnames, so automatically passes through both pinyin columns
- Output: `../../data/character_set/step5_hsk.csv` adds column: `hsk_level`

### Step 6: Character and Pinyin Frequency Data (FINAL STEP)
```bash
python3 build_step6_freq.py
```
- Counts **both character-level and pinyin-level** frequencies from sentence corpus
- Reads from: `../../data/sentences/step5_pinyin_refined.csv` (or `step4_with_hsk.csv` as fallback)
- Parses `char_pinyin_pairs` column to extract characters and char-pinyin tuples
- **Character-level frequency**: Total occurrences (stored in `freq` column)
- **Pinyin-level frequency**: Each character-pinyin pair counted separately
  - Adds frequency data to `pinyins_tone3`: `yi1(8867)|yi2(1825)|yi4(1299)`
  - Keeps `pinyins_display` clean (no frequencies): `yī|yí|yì`
- Statistics:
  - 5,002 characters appear in corpus (23.8% of total)
  - 790,413 total character occurrences
  - 5,272 unique char-pinyin pairs tracked
  - Top character: 我 (wo3(32055)) - 32,055 occurrences
- Optionally generates distribution graphs (requires `matplotlib`)
- Output: `../../data/character_set/step6_with_freq.csv` adds column: `freq` and enriches `pinyins_tone3`
- Also generates (in `analysis/`): `frequency_distribution.png`
- **FINAL DATASET** with dual-format pinyins, HSK levels, and corpus-based frequencies

## Final Dataset

**Latest Build Output**: `../../data/character_set/step6_with_freq.csv`

This is the complete character dataset with all enrichment layers. All columns:
- `id` - Sequential integer (1-20992)
- `char` - The Chinese character
- `codepoint` - Unicode identifier (e.g., U+4E00)
- `pinyins_tone3` - Canonical format with tone numbers AND frequencies (e.g., `yi1(8867)|yi4(1299)`)
- `pinyins_display` - Display format with tone marks, NO frequencies (e.g., `yī|yì`)
- `script_type` - Enum: simplified, traditional, neutral, or ambiguous
- `variants` - Pipe-separated variant characters (e.g., `發|髮`)
- `gloss_en` - Short English gloss from CC-CEDICT
- `examples` - Pipe-separated example words (up to 3)
- `hsk_level` - HSK level (1, 2, 3, 4, 5, 6, or "7-9") or empty for non-HSK characters
- `freq` - Character frequency count in sentence corpus (0 if character doesn't appear)

**Key Change**: Dual-format pinyin storage eliminates need for format conversion throughout the codebase.

## Coverage Statistics

- **100%** have pinyin (20,992 / 20,992) - pypinyin provides complete coverage
- **29.6%** polyphonic (6,206 characters with multiple pronunciations)
- **67.4%** have English glosses (14,152 characters)
- **41.1%** have example words (8,618 characters)
- **34.6%** have variants (7,254 characters)
- **20.0%** have HSK levels (4,193 characters in HSK 1-9 curriculum)
- **23.8%** appear in corpus (5,002 characters with freq > 0)

## Script Type Distribution

- **Simplified**: 12.5% (2,618 characters)
- **Traditional**: 22.1% (4,634 characters)
- **Neutral**: 65.4% (13,738 characters)
- **Ambiguous**: 0.0% (2 characters - rare merger cases)

## HSK Level Distribution

- **HSK 1**: 2.0% (415 characters - 300 simplified + 115 traditional variants)
- **HSK 2**: 2.0% (429 characters - 299 simplified + 130 traditional variants)
- **HSK 3**: 2.1% (435 characters)
- **HSK 4**: 2.1% (432 characters)
- **HSK 5**: 2.0% (423 characters)
- **HSK 6**: 2.0% (414 characters)
- **HSK 7-9**: 7.8% (1,644 characters - 1,200 simplified + 444 traditional variants)
- **No HSK**: 80.0% (16,800 characters - archaic, rare, or specialized)

## Build Artifacts

Intermediate CSVs are stored in `../../data/character_set/` for audit purposes:
- `step1_base.csv` - Base character set (20,992 characters)
- `step2_pinyin.csv` - With dual-format pinyins (pinyins_tone3 + pinyins_display)
- `step3_cedict.csv` - With glosses and examples
- `step4_variants.csv` - With script types and variants
- `step5_hsk.csv` - With HSK levels
- `step6_with_freq.csv` - **FINAL OUTPUT** with character and pinyin-level frequencies

**Obsolete files** (deleted, preserved in git history):
- `build_step2_pinyin.py` - Old Unihan-based pinyin extraction
- `build_step6_enrich_pypinyin.py` - Old enrichment step (merged into step2)
- `build_step7_freq.py` - Old frequency step (renamed to step6 with enhancements)
- `misc/fix_pinyin_format.py` - Format conversion workaround (no longer needed)
- `step6_enriched.csv` - Old step6 data output
- `step7_with_freq.csv` - Old step7 data output

Analysis outputs are stored in `../../data/character_set/analysis/`:
- `pinyin_trie.json` - Character-level Trie (1,307 unique syllables, down from 2,004)
- `frequency_distribution.png` - Character frequency distribution (Zipf's law)
- `verification_report.txt` - pypinyin coverage validation results

## Analysis Scripts

Located in `analysis/` subdirectory - not part of main pipeline.

### Pinyin Trie Analysis
- `build_pinyin_trie.py` - Build character-level Trie of all pinyin syllables
  - Uses `pinyins_tone3` column directly (already in tone3 format)
  - **Output: 1,307 unique syllables** (down from 2,004 with old mixed-format system)
  - Stores character metadata with pinyin-level and corpus frequencies
  - **No normalization needed** - pypinyin provides consistent format
- `compare_unihan_vs_pypinyin.py` - Verification script (used during migration)
  - Validates pypinyin coverage: 100% (20,992/20,992 characters)
  - Checks dual-format consistency: Perfect (0 mismatches)
- `validate_migration.py` - Migration validation script
  - Verifies dual-format storage correctness
  - Ensures frequencies only in pinyins_tone3, not in pinyins_display

## Rebuilding

If source data is updated:
1. Re-run all steps in order (steps 1-6, each step reads from the previous step's output)
2. Final output: `step6_with_freq.csv` contains the complete dataset
3. When ready for app integration: Copy to `../../app/public/data/character_set/chinese_characters.csv`

**Dependencies**:
- Step 2 requires `pypinyin`: `pip install pypinyin`
- Step 6 optionally uses `matplotlib` for distribution graphs (not required for CSV generation)

**Key Improvements in New Pipeline**:
- **100% pypinyin coverage** (vs. 99.7% with old Unihan-based approach)
- **Zero duplicate syllables** (was 612 duplicates / 30.5% with mixed formats)
- **Pinyin-level frequencies** - each pronunciation tracked separately
- **No format conversion needed** - dual-format storage eliminates conversion utilities
- **Simpler pipeline** - 6 steps instead of 7, fewer workarounds

## HSK Data Source

HSK 3.0 character lists are downloaded from:
- **Repository**: https://github.com/elkmovie/hsk30
- **License**: MIT License (Copyright 2021 Pleco Inc.)
- **Source**: OCR'd from official Chinese government HSK 3.0 PDF
- **Levels**: 1-6 (300 chars each), 7-9 grouped (1,200 chars)
- **Format**: Tab-separated format (number + character), simplified Chinese only
- **Local Cache**: `../../data/sources/elkmovie_hsk30/`
- **Accuracy**: All 3,000 characters complete (fixes OCR errors in other datasets)

**Why elkmovie over krmanik?**
The elkmovie dataset fixes critical OCR errors found in the krmanik/HSK-3.0 dataset:
- HSK 2: 入 (rù, "enter") was mis-recognized as duplicate 人 (rén, "person")
- HSK 7-9: 抛 (pāo, simplified "throw") was mis-recognized as 拋 (traditional variant)

**Note**: Traditional character HSK levels are derived by propagating simplified character levels through our variant mappings. This assumes semantic equivalence between simplified/traditional pairs at the same difficulty level.
