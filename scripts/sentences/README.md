# Sentence Pipeline Scripts

Scripts to build the sentence dataset from Tatoeba corpus with pinyin, translations, and HSK classifications.

## Architecture

This pipeline follows an **idempotent single-CSV pattern**:
- Raw data: `../../data/sources/tatoeba_sentences.tsv` (read-only source)
- Processed data: `../../data/sentences/sentences.csv` (single source of truth)
- Each build step reads and writes to the same `sentences.csv` file
- All steps are idempotent and safe to re-run
- Export script is independent of step numbering

## Main Pipeline

Run scripts in order from the `scripts/sentences/` directory:

### Step 1: Script Classification
```bash
python3 build_step1_classify.py
```
- Creates initial `sentences.csv` from raw Tatoeba data
- Classifies sentences as simplified, traditional, neutral, or ambiguous
- Uses character script_type from character dataset
- Input: `../../data/sources/tatoeba_sentences.tsv`
- Output: `../../data/sentences/sentences.csv`
- Columns: `id`, `sentence`, `script_type`

### Step 2: Character-Level Pinyin
```bash
python3 build_step2_pinyin.py
```
- Adds pinyin for each character using jieba + pypinyin
- Context-aware segmentation for accurate heteronym selection
- Input/Output: `../../data/sentences/sentences.csv`
- Adds column: `char_pinyin_pairs` (format: `我:wo3|爱:ai4|你:ni3`)
- **Idempotent:** Safe to re-run

### Step 3: English Translation
```bash
python3 build_step3_translate.py [--limit N]
```
- Translates sentences using OpenAI GPT-4o-mini
- Batch processing with incremental saves and resume capability
- Input/Output: `../../data/sentences/sentences.csv`
- Adds column: `english_translation`
- **Idempotent:** Skips sentences that already have translations
- **Note:** Requires `OPENAI_API_KEY` environment variable

### Step 4: HSK Classification
```bash
python3 build_step4_hsk.py
```
- Classifies sentences by maximum character HSK level
- Uses character HSK levels from character dataset
- Input/Output: `../../data/sentences/sentences.csv`
- Adds column: `sentence_hsk_level` (1-6, 7-9, beyond-hsk, or empty)
- Also generates: `analysis/hsk_distribution.png`, `analysis/hsk_statistics.json`
- **Idempotent:** Safe to re-run

### Step 5: Pinyin Refinement (Optional)

**⚠️ Complex multi-substep workflow** - See `step5/README.md` for complete documentation

```bash
python3 build_step5_refine_pinyin.py [--limit N] [--dry-run]
```
- Applies AI-verified pinyin improvements for context-sensitive characters
- Only updates 9 verified characters: 地, 著, 谁, 誰, 覺, 觉, 長, 长, 樂
- **Requires prior execution of step5 substeps** (see `step5/README.md`)
- Input: `../../data/sentences/sentences.csv` + `step5/pinyin_comparison_report.json`
- Output: Updates `char_pinyin_pairs` in `sentences.csv` + `step5/pinyin_changes_applied.log`
- **Idempotent:** Safe to re-run
- **Optional step** - can skip if not using OpenAI enhancement

**Step 5 substeps** (in `step5/` directory):
1. `step5a_generate_openai_pinyin.py` - Generate context-aware pinyin via OpenAI ($8-10, 4-5hrs)
2. `step5b_compare_pinyin.py` - Compare pypinyin vs OpenAI output
3. `build_step5_refine_pinyin.py` - Apply verified changes (main pipeline script)

See `step5/README.md` for detailed workflow documentation.

### Final: Export to JSON
```bash
python3 export_to_json.py
```
- Converts `sentences.csv` to JSON format for web app
- Applies content filters (removes vulgar content, sentences >50 chars, no Chinese)
- Input: `../../data/sentences/sentences.csv`
- Output: `../../app/public/data/sentences/sentences_with_translation.json`
- Final format: ~79,333 filtered sentences with metadata wrapper
- **Note:** This script is step-independent - always reads from `sentences.csv`

## Pipeline Output Files

**Source data:**
- `../../data/sources/tatoeba_sentences.tsv` - Raw Tatoeba data (read-only)

**Processed data:**
- `../../data/sentences/sentences.csv` - **Single source of truth** (14MB)
  - All pipeline steps read/write this file
  - Each step adds columns incrementally
  - Final schema: `id | sentence | script_type | char_pinyin_pairs | english_translation | sentence_hsk_level`

**Step 5 intermediate files** (optional, in `../../data/sentences/step5/`):
- `sentences_pinyin_openai.json` (86MB) - OpenAI context-aware pinyin output
- `pinyin_comparison_report.json` (2.8MB) - Pypinyin vs OpenAI comparison
- `pinyin_changes_applied.log` (324KB) - Applied changes log
- `sentences_pinyin_openai.json.errors.log` - API errors (if any)

**Analysis outputs** (in `../../data/sentences/analysis/`):
- `hsk_distribution.png`, `hsk_statistics.json` - HSK level distribution
- `script_distribution.png`, `script_statistics.json` - Script type analysis
- `sentence_length_distribution.png` - Length by HSK level (violin plots)
- `overall_sentence_length_distribution.png` - Overall length histogram
- `non_hsk_characters.csv` - Characters not in HSK (frequency list)
- `non_hsk_sentences_examples.csv` - Example sentences with non-HSK chars
- `hsk_distribution_comparison.png` - Before/after HSK filtering comparison

**Production file:**
- `../../app/public/data/sentences/sentences_with_translation.json` (40MB) - Used by web app

## Analysis Scripts

Located in `analysis/` subdirectory - not part of main pipeline:

- `analyze_corpus_stats.py` - Overall corpus statistics (sentences, characters, script types)
- `analyze_hsk_coverage.py` - HSK distribution analysis and comparison charts
- `analyze_script_distribution.py` - Simplified/traditional distribution charts
- `analyze_sentence_length.py` - Length distribution by HSK level (violin plots)
- `analyze_overall_sentence_length.py` - Overall length histogram
- `analyze_sentence_composition.py` - Pure Chinese vs mixed content analysis
- `count_corpus_characters.py` - Count unique characters in corpus
- `count_beyond_hsk_by_script.py` - Analyze non-HSK characters by script type

## Step5 Pinyin Refinement Scripts

Located in `step5/` subdirectory (part of optional step 5 workflow):

- `step5a_generate_openai_pinyin.py` - Generate context-aware pinyin via OpenAI API
- `step5b_compare_pinyin.py` - Compare pypinyin vs OpenAI output
- See `step5/README.md` for complete workflow documentation

## Miscellaneous Scripts

Located in `misc/` subdirectory:

- `fix_translation_quotes.py` - Clean up translation formatting issues

## Column Schema

### tatoeba_sentences.tsv (source)
```
id | language | sentence
```

### sentences.csv (processed - columns added incrementally)

**After Step 1:**
```
id | sentence | script_type
```

**After Step 2:**
```
id | sentence | script_type | char_pinyin_pairs
```

**After Step 3:**
```
id | sentence | script_type | char_pinyin_pairs | english_translation
```

**After Step 4:**
```
id | sentence | script_type | char_pinyin_pairs | english_translation | sentence_hsk_level
```

**After Step 5 (optional):**
```
(Same schema as Step 4, but char_pinyin_pairs has refined pinyin for verified characters)
```

## Rebuilding

To rebuild the entire pipeline from scratch:

1. Ensure source data exists: `../../data/sources/tatoeba_sentences.tsv`
2. Run steps 1-5 in order:
   ```bash
   python3 build_step1_classify.py
   python3 build_step2_pinyin.py
   python3 build_step3_translate.py --limit 0  # Requires OPENAI_API_KEY
   python3 build_step4_hsk.py
   python3 build_step5_refine_pinyin.py  # Optional
   ```
3. Export to JSON:
   ```bash
   python3 export_to_json.py
   ```

**To update existing data:**
- Each step is idempotent - safe to re-run any step
- Step 3 will skip sentences that already have translations
- You can run any individual step to update just that column

**Dependencies:**
- Python 3.9+
- `jieba` - Chinese word segmentation (step 2)
- `pypinyin` - Pinyin conversion (step 2)
- `openai` - API client (steps 3, 5) - requires `OPENAI_API_KEY` environment variable
- `matplotlib` - Visualization (analysis scripts)

## Statistics

- Total sentences: ~79,700 (raw) → ~79,333 (filtered in JSON)
- Unique characters in corpus: 4,973
- HSK distribution:
  - HSK 1-3: ~60% (beginner-intermediate)
  - HSK 4-6: ~25% (intermediate-advanced)
  - HSK 7-9: ~10% (advanced)
  - Beyond HSK: ~5% (specialized/rare characters)

## Notes

- **Single CSV pattern:** All steps read/write the same `sentences.csv` file
- **Idempotent design:** Every step is safe to re-run without breaking existing data
- **Incremental processing:** Step 3 (translation) supports resume from partial completion
- **Content filtering:** Export script filters vulgar content, >50 char sentences, non-Chinese
- **Production data:** Only `sentences_with_translation.json` is used by the web app
- **Version control:** Use git for backups - no need for separate backup files

## Architecture Benefits

This pipeline follows the same **idempotent single-file pattern** as the character pipeline v1:

✅ **Single source of truth** - One `sentences.csv` file, not 5+ redundant copies
✅ **Idempotent steps** - Safe to re-run any step without breaking data
✅ **Step-independent export** - `export_to_json.py` always works, regardless of new steps
✅ **Easier debugging** - One file to inspect, not multiple intermediate versions
✅ **Git-friendly** - Clear diffs, no huge file duplication
✅ **Extensible** - Add new steps (step6, step7...) without refactoring export script
