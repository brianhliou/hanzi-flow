# Character Set Generation Scripts

Scripts to build the Chinese character dataset from source data.

## Source Data

Located in `../../data/sources/`:
- `Unihan_Readings.txt` - Pinyin readings from Unicode Unihan database
- `Unihan_Variants.txt` - Simplified/Traditional variant mappings
- `cedict_ts.u8` - CC-CEDICT Chinese-English dictionary
- `s2t.json`, `t2s.json` - OpenCC simplified/traditional mappings (not currently used)
- `junda_char_freq.txt` - Jun Da character frequency list (for future use)

## Build Pipeline

All scripts should be run from the `scripts/character_set/` directory. Run in order:

### Step 1: Base Character Set
```bash
python3 build_step1_base.py
```
- Generates 20,992 characters from CJK Unified Ideographs (U+4E00 to U+9FFF)
- Output: `../../data/build_artifacts/step1_base.csv` with columns: `id`, `char`, `codepoint`

### Step 2: Pinyin Readings
```bash
python3 build_step2_pinyin.py
```
- Parses Unihan_Readings.txt for pinyin data
- Uses kHanyuPinlu (with frequency), kHanyuPinyin, and kMandarin fields
- Format: `lè(283)|yuè(54)` for polyphonic characters with frequency data
- Output: `../../data/build_artifacts/step2_pinyin.csv` adds column: `pinyins`

### Step 3: Glosses and Examples
```bash
python3 build_step3_cedict.py
```
- Parses CC-CEDICT for English glosses and example words
- Single-character entries → glosses
- Multi-character words → examples (up to 3 per character)
- Output: `../../data/build_artifacts/step3_cedict.csv` adds columns: `gloss_en`, `examples`

### Step 4: Script Types and Variants
```bash
python3 build_step4_variants.py
```
- Parses Unihan_Variants.txt for simplified/traditional mappings
- Determines script_type: simplified, traditional, neutral, or ambiguous
- Creates bidirectional variant links (e.g., 发 ↔ 發|髮)
- Filters out self-referential variants
- Output: `../../data/build_artifacts/step4_variants.csv` adds columns: `script_type`, `variants`

### Step 5: HSK Level Classification
```bash
python3 build_step5_hsk.py
```
- Downloads HSK 3.0 character lists (levels 1-9) from krmanik/HSK-3.0 repo
- Saves source files to `../../data/sources/hsk30/` (HSK_1.txt through HSK_7-9.txt)
- Assigns HSK levels to simplified characters from official lists
- Propagates HSK levels to traditional variants via our variant mappings
- Characters not in HSK 1-9 curriculum: assigned empty/null hsk_level
- Output: `../../data/build_artifacts/step5_hsk.csv` adds column: `hsk_level`
- Final step: Copy to `../../data/chinese_characters.csv` and `../../app/public/data/character_set/chinese_characters.csv`

## Final Dataset

**Source of Truth**: `../../data/chinese_characters.csv`

This is the production dataset for the app. All columns from step5:

Copy of `step5_hsk.csv` with all columns:
- `id` - Sequential integer (1-20992)
- `char` - The Chinese character
- `codepoint` - Unicode identifier (e.g., U+4E00)
- `pinyins` - Pipe-separated pinyin readings with optional frequency (e.g., `lè(283)|yuè(54)`)
- `script_type` - Enum: simplified, traditional, neutral, or ambiguous
- `variants` - Pipe-separated variant characters (e.g., `發|髮`)
- `gloss_en` - Short English gloss from CC-CEDICT
- `examples` - Pipe-separated example words (up to 3)
- `hsk_level` - HSK level (1, 2, 3, 4, 5, 6, or "7-9") or empty for non-HSK characters

## Coverage Statistics

- **99.7%** have pinyin (20,924 / 20,992)
- **22.8%** polyphonic (4,795 characters with multiple pronunciations)
- **67.4%** have English glosses (14,152 characters)
- **41.1%** have example words (8,618 characters)
- **34.6%** have variants (7,254 characters)
- **20.0%** have HSK levels (4,192 characters in HSK 1-9 curriculum)

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
- `step1_base.csv` - Base character set
- `step2_pinyin.csv` - With pinyin
- `step3_cedict.csv` - With glosses and examples
- `step4_variants.csv` - With script types and variants
- `step5_hsk.csv` - Complete with HSK levels (final output)

## Rebuilding

If source data is updated:
1. Re-run all steps in order (each step reads from the previous step's output)
2. Copy final `step5_hsk.csv` to:
   - `../../data/chinese_characters.csv` (main dataset)
   - `../../app/public/data/character_set/chinese_characters.csv` (production/frontend)

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
