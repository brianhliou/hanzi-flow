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
- Final step: Copy to `../../data/chinese_characters.csv`

## Final Dataset

**Source of Truth**: `../../data/chinese_characters.csv`

This is the production dataset for the app. All columns from step4:

Copy of `step4_variants.csv` with all columns:
- `id` - Sequential integer (1-20992)
- `char` - The Chinese character
- `codepoint` - Unicode identifier (e.g., U+4E00)
- `pinyins` - Pipe-separated pinyin readings with optional frequency (e.g., `lè(283)|yuè(54)`)
- `script_type` - Enum: simplified, traditional, neutral, or ambiguous
- `variants` - Pipe-separated variant characters (e.g., `發|髮`)
- `gloss_en` - Short English gloss from CC-CEDICT
- `examples` - Pipe-separated example words (up to 3)

## Coverage Statistics

- **99.7%** have pinyin (20,924 / 20,992)
- **22.8%** polyphonic (4,795 characters with multiple pronunciations)
- **67.4%** have English glosses (14,152 characters)
- **41.1%** have example words (8,618 characters)
- **34.6%** have variants (7,254 characters)

## Script Type Distribution

- **Simplified**: 12.5% (2,618 characters)
- **Traditional**: 22.1% (4,634 characters)
- **Neutral**: 65.4% (13,738 characters)
- **Ambiguous**: 0.0% (2 characters - rare merger cases)

## Build Artifacts

Intermediate CSVs are stored in `../../data/build_artifacts/` for audit purposes:
- `step1_base.csv` - Base character set
- `step2_pinyin.csv` - With pinyin
- `step3_cedict.csv` - With glosses and examples
- `step4_variants.csv` - Complete with all columns

## Rebuilding

If source data is updated:
1. Re-run all steps in order (each step reads from the previous step's output)
2. Copy final `step4_variants.csv` to `../../data/chinese_characters.csv`
