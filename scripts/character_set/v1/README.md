# SOT Character Set - v1.0 Pipeline

Source of Truth character reference dataset covering all CJK characters in Unicode.

## Overview

**Goal:** Authoritative, corpus-independent character dataset with **97,712 characters** from CJK Unified Ideographs and Extensions A-I (excluding Extension J).

**Scope:** 10 Unicode blocks in strict codepoint order (Extension A, Core, B-I), covering all officially released Han characters as of Unicode 15.1. Extension J is excluded (proposed for Unicode 16, not yet official).

**Key Principles:**
- Single file modified in-place (`sot_characters_v1.0.csv`)
- Idempotent scripts (Steps 2-4 can be re-run independently)
- Minimal schema (no corpus-dependent data)
- Allow NULL for rare characters

## Schema

Final dataset has 7 columns:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | int | No | Stable sequential identifier (1-97712) |
| `char` | str | No | The Chinese character |
| `codepoint` | str | No | Unicode identifier (U+4E00 format) |
| `pinyins_tone3` | str | Yes | Canonical format with tone numbers (yi1\|yi2\|yi4) |
| `pinyins_display` | str | Yes | Display format with tone marks (yī\|yí\|yì) |
| `script_type` | str | Yes | simplified \| traditional \| neutral \| ambiguous |
| `gloss_en` | str | Yes | Primary English definition |

## Build Pipeline

All scripts modify the same file: `../../data/character_set/sot_characters_v1.0.csv`

Run from `scripts/character_set/v1/` directory:

### Step 1: Extract All CJK Characters (Generator)
```bash
python3 build_step1_extract_all_cjk.py
```
- Extracts 97,712 characters from 10 Unicode blocks in **strict codepoint order**
- Creates initial CSV with columns: `id, char, codepoint`
- **Unicode blocks covered (codepoint order):**
  - Extension A (U+3400-U+4DBF): 6,592 chars
  - CJK Unified Ideographs (U+4E00-U+9FFF): 20,992 chars
  - Extension B (U+20000-U+2A6DF): 42,720 chars
  - Extension C (U+2A700-U+2B73F): 4,160 chars
  - Extension D (U+2B740-U+2B81F): 224 chars
  - Extension E (U+2B820-U+2CEAF): 5,776 chars
  - Extension F (U+2CEB0-U+2EBEF): 7,488 chars
  - Extension I (U+2EBF0-U+2EE5F): 624 chars
  - Extension G (U+30000-U+3134F): 4,944 chars
  - Extension H (U+31350-U+323AF): 4,192 chars
- **Excluded:** Extension J (proposed for Unicode 16, not official)
- **Output:** `sot_characters_v1.0.csv` with 3 columns populated

### Step 2: Add Pinyins (Idempotent)
```bash
python3 build_step2_add_pinyins.py
```
- Reads existing CSV, adds/updates `pinyins_tone3` and `pinyins_display` columns
- Uses pypinyin library for both formats (calls pypinyin twice per character)
- **Dual-format storage:**
  - `pinyins_tone3`: Canonical with tone numbers (yi1|yi2|yi4)
  - `pinyins_display`: Display with tone marks (yī|yí|yì)
- Both formats guaranteed to match (same count and order)
- **Coverage:** 48.8% valid pinyin (excellent for BMP, poor for Extensions C-I)
- **CJK-as-pinyin:** When pypinyin doesn't recognize a char, it returns the char itself (treated as NULL)
- **Idempotent:** Can re-run to refresh pinyin data
- **Analysis:** See `../../../data/character_set/v1/PINYIN_COVERAGE_ANALYSIS.md` for detailed statistics

### Step 3: Add English Glosses (Idempotent)
```bash
python3 build_step3_add_gloss.py
```
- Reads existing CSV, adds/updates `gloss_en` column
- Parses Unihan kDefinition field for primary meaning
- Takes first definition if multiple provided
- NULLs allowed for rare characters without definitions
- **Idempotent:** Can re-run to refresh gloss data

### Step 4: Add Script Type (Idempotent)
```bash
python3 build_step4_add_script_type.py
```
- Reads existing CSV, adds/updates `script_type` column
- Uses Unihan kSimplifiedVariant/kTraditionalVariant mappings
- Logic:
  - Has simplified variant → **traditional**
  - Has traditional variant → **simplified**
  - Has both or circular reference → **ambiguous**
  - Has neither → **neutral**
- NULLs allowed initially, classified as neutral if no data
- **Idempotent:** Can re-run to refresh script type classifications

## Final Output

**File:** `../../data/character_set/sot_characters_v1.0.csv`

All 7 columns populated:
```csv
id,char,codepoint,pinyins_tone3,pinyins_display,script_type,gloss_en
1,㐀,U+3400,qiu1,qiū,neutral,
2,㐁,U+3401,tian2,tián,neutral,to lick; to taste
3,一,U+4E00,yi1,yī,neutral,one
...
```

## Data Sources

- **Unicode blocks:** Official Unicode Standard (CJK Unified Ideographs)
- **Pinyins:** pypinyin library only (no fallback)
- **Glosses:** Unihan kDefinition field
- **Script types:** Unihan kSimplifiedVariant + kTraditionalVariant

**Note:** No fallback to Unihan kMandarin for pinyins. When pypinyin doesn't recognize a character, it returns the character itself - these are treated as NULL values. See coverage analysis for details.

## Coverage Expectations

Based on actual data analysis (see `../../../data/character_set/v1/PINYIN_COVERAGE_ANALYSIS.md`):

| Field | Expected Coverage | Notes |
|-------|-------------------|-------|
| **pinyins** | **48.8%** (53,356 / 109,226 syllables) | Excellent for BMP (95%+), poor for Extensions C-I (<10%) |
| **gloss_en** | ~40% | Less documentation for rare characters |
| **script_type** | ~30% | Only characters with variants classified |

### Pinyin Coverage by Block

| Block | Coverage | Note |
|-------|----------|------|
| CJK Core | 99.8% | ✅ Excellent |
| Extension A | 89.7% | ✅ Excellent |
| Extension B | 36.1% | ⚠️ Moderate |
| Extensions C-I | <10% | ❌ Poor (rare/archaic chars) |

**Why low coverage?** pypinyin doesn't recognize rare/historical characters (51.2% return character-as-pinyin). This is expected and acceptable for an SOT dataset covering all Unicode Han characters.

## Differences from v0 Pipeline

| Feature | v0 (Learner) | v1 (SOT) |
|---------|--------------|----------|
| Character count | 20,992 | 97,712 |
| Unicode blocks | BMP only (Core) | 10 blocks (Extension A + Core + B-I) |
| HSK levels | ✓ | ✗ (separate table) |
| Example words | ✓ | ✗ (separate table) |
| Corpus frequency | ✓ | ✗ (corpus-dependent) |
| Variants column | ✓ | ✗ (future) |
| Build pattern | Sequential snapshots | Idempotent updates |
| NULLs allowed | No (BMP is well-documented) | Yes (Extensions sparse) |

## Rebuilding Individual Steps

Steps 2-4 are idempotent and can be re-run independently:

```bash
# Update just pinyins (e.g., after pypinyin library update)
python3 build_step2_add_pinyins.py

# Update just glosses (e.g., after Unihan update)
python3 build_step3_add_gloss.py

# Update just script types (e.g., after variant logic fix)
python3 build_step4_add_script_type.py
```

Each script:
1. Reads `sot_characters_v1.0.csv`
2. Updates its specific column(s)
3. Writes back to same file

## Dependencies

- Python 3.7+
- `pypinyin` library: `pip install pypinyin`
- Unihan data files in `../../data/sources/`:
  - `Unihan_Readings.txt` (for kMandarin fallback)
  - `Unihan_Variants.txt` (for script type classification)

## Future Enhancements

Potential additions (not in v1.0):
- `variants` column (script variant mappings)
- `radical` column (Kangxi radical)
- `stroke_count` column
- Separate HSK mapping table
- Separate example words table
- Separate frequency table (corpus-dependent)
