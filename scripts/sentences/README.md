# Sentence Pipeline Scripts

Scripts to build the sentence dataset from Tatoeba corpus with pinyin, translations, and HSK classifications.

## Source Data

**Raw Input:** `../../data/sentences/step0_raw.tsv`
- Source: Tatoeba Chinese sentence corpus
- Format: Tab-separated values (id, language, sentence)
- ~79,700 sentences

## Main Pipeline

Run scripts in order from the `scripts/sentences/` directory:

### Step 1: Script Classification
```bash
python3 build_step1_classify.py
```
- Classifies sentences as simplified, traditional, neutral, or ambiguous
- Uses character script_type from character dataset
- Input: `step0_raw.tsv`
- Output: `step1_classified.csv`
- Adds column: `script_type`

### Step 2: Character-Level Pinyin
```bash
python3 build_step2_pinyin.py
```
- Adds pinyin for each character using jieba + pypinyin
- Context-aware segmentation for accurate heteronym selection
- Input: `step1_classified.csv`
- Output: `step2_with_pinyin.csv`
- Adds column: `char_pinyin_pairs` (format: `我:wo3|爱:ai4|你:ni3`)

### Step 3: English Translation
```bash
python3 build_step3_translate.py
```
- Translates sentences using OpenAI GPT-4o-mini
- Batch processing with incremental saves and resume capability
- Input: `step2_with_pinyin.csv`
- Output: `step3_with_translation.csv`
- Adds column: `english_translation`
- **Note:** Requires OpenAI API key

### Step 4: HSK Classification
```bash
python3 build_step4_hsk.py
```
- Classifies sentences by maximum character HSK level
- Uses character HSK levels from character dataset
- Input: `step3_with_translation.csv`
- Output: `step4_with_hsk.csv`
- Adds column: `sentence_hsk_level` (1-6, 7-9, or beyond-hsk)
- Also generates analysis outputs (in `analysis/`): `hsk_distribution.png`, `hsk_statistics.json`

### Step 5: Pinyin Refinement (Optional)

**⚠️ Complex multi-substep workflow** - See `step5/README.md` for complete documentation

```bash
python3 build_step5_refine_pinyin.py
```
- Applies AI-verified pinyin improvements for context-sensitive characters
- Only updates 9 verified characters: 地, 著, 谁, 誰, 覺, 觉, 長, 长, 樂
- **Requires prior execution of step5 substeps** (see `step5/README.md`)
- Input: `step4_with_hsk.csv` + `step5/pinyin_comparison_report.json`
- Output: `step5_pinyin_refined.csv` + `step5/pinyin_changes_applied.log`
- **Optional step** - can skip if not using OpenAI enhancement

**Step 5 substeps** (in `step5/` directory):
1. `step5a_generate_openai_pinyin.py` - Generate context-aware pinyin via OpenAI ($8-10, 4-5hrs)
2. `step5b_compare_pinyin.py` - Compare pypinyin vs OpenAI output
3. `build_step5_refine_pinyin.py` - Apply verified changes (main pipeline script)

See `step5/README.md` for detailed workflow documentation.

### Step 6: Export to JSON
```bash
python3 build_step6_export_json.py
```
- Converts CSV to JSON format for web app
- Applies content filters (removes non-Chinese sentences, duplicates)
- Input: `step5_pinyin_refined.csv` (or `step4_with_hsk.csv` if skipping step 5)
- Output: `../../app/public/data/sentences/sentences_with_translation.json`
- Final format: ~79,333 filtered sentences with metadata wrapper

## Pipeline Output Files

Intermediate files in `../../data/sentences/`:
- `step0_raw.tsv` - Raw Tatoeba data
- `step1_classified.csv` - With script classification
- `step2_with_pinyin.csv` - With character-level pinyin
- `step3_with_translation.csv` - With English translations
- `step4_with_hsk.csv` - With HSK classifications
- `step5_pinyin_refined.csv` - **Final CSV** (optional refinement)

Step5 intermediate files in `../../data/sentences/step5/`:
- `sentences_pinyin_openai.json` (86MB) - OpenAI context-aware pinyin output
- `pinyin_comparison_report.json` (2.8MB) - Pypinyin vs OpenAI comparison
- `pinyin_changes_applied.log` (324KB) - Applied changes log
- `sentences_pinyin_openai.json.errors.log` - API errors (if any)

Analysis outputs in `../../data/sentences/analysis/`:
- `hsk_distribution.png`, `hsk_statistics.json` - HSK level distribution
- `script_distribution.png`, `script_statistics.json` - Script type analysis
- `sentence_length_distribution.png` - Length by HSK level (violin plots)
- `overall_sentence_length_distribution.png` - Overall length histogram
- `non_hsk_characters.csv` - Characters not in HSK (frequency list)
- `non_hsk_sentences_examples.csv` - Example sentences with non-HSK chars
- `hsk_distribution_comparison.png` - Before/after HSK filtering comparison

Production file:
- `../../app/public/data/sentences/sentences_with_translation.json` - Used by web app

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

### step0_raw.tsv
```
id | language | sentence
```

### step1_classified.csv
```
id | sentence | script_type
```

### step2_with_pinyin.csv
```
id | sentence | script_type | char_pinyin_pairs
```

### step3_with_translation.csv
```
id | sentence | script_type | char_pinyin_pairs | english_translation
```

### step4_with_hsk.csv
```
id | sentence | script_type | char_pinyin_pairs | english_translation | sentence_hsk_level
```

### step5_pinyin_refined.csv
```
(Same as step4, but with refined pinyin in char_pinyin_pairs)
```

## Rebuilding

To rebuild the entire pipeline:

1. Ensure you have the raw Tatoeba data: `step0_raw.tsv`
2. Run steps 1-6 in order (each step reads from the previous step's output)
3. Step 3 requires OpenAI API key (set in environment variable)
4. Step 5 is optional - skip if not using AI pinyin refinement
5. Final output: JSON file in `/app/public/data/sentences/`

**Dependencies:**
- Python 3.9+
- `jieba` - Chinese word segmentation (step 2)
- `pypinyin` - Pinyin conversion (step 2)
- `openai` - API client (steps 3, 5)
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

- **Backups:** Not needed - use git for version control
- **Incremental processing:** Step 3 (translation) supports resume from partial completion
- **Filtering:** Step 6 filters out sentences with excessive English, numbers, or special characters
- **Production data:** Only step 6 output (`sentences_with_translation.json`) is used by the web app

## Comparison to Character Pipeline

Like the character pipeline, this follows a clean sequential build process:
- Clear step numbering (step0-step6)
- Each step reads previous step's output
- Analysis scripts separated into subdirectories
- No backup files cluttering the main pipeline
