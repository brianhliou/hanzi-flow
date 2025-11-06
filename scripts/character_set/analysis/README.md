# Character Set Analysis Scripts

Analysis tools for the Chinese character dataset, with focus on pinyin syllable analysis and visualization.

## Scripts

### Core Analysis

**build_pinyin_trie.py** - Build character-level Trie of all pinyin syllables
- Input: `../../../data/character_set/step6_with_freq.csv` (characters with corpus freq > 0)
- Output: `../../../data/character_set/analysis/pinyin_trie.json`
- **Key Feature**: Filters to `pinyin_freq > 0` (only syllables actually used in corpus)
- Structure: Character-level nodes (y → i → 4), terminal nodes store character metadata
- Statistics: **1,161 unique syllables** used in corpus, 5,002 characters, 5,221 char-syllable pairs

**analyze_trie.py** - Comprehensive statistical analysis and visualization
- Input: `pinyin_trie.json`
- Outputs: 5 PNG charts + console report
- Analyzes: tone distributions, syllable complexity, polyphonic characters, depth distribution, syllable×tone matrix
- Generates: `PINYIN_TRIE_ANALYSIS.md` with key findings
- **New**: Syllable×tone heatmap shows 401 base syllables across 5 tones with character counts

**visualize_trie.py** - Interactive SVG visualization of Trie structure
- Input: `pinyin_trie.json`
- Outputs: SVG visualizations (full tree + depth-limited overviews + focused branches)
- Features: Interactive tooltips, zoomable, shows syllable + character count
- Usage: `--depth N` for overview, `--branch LETTER` for focused branch, `--format svg|png`, `--compact` for spacing
- **New**: `--branch h` generates focused visualization of single branch with full depth

**compare_unihan_vs_pypinyin.py** - Verification script (used during migration)
- Validates pypinyin coverage vs old Unihan+pypinyin approach
- Results: 100% coverage (20,992/20,992 characters)
- Checks dual-format consistency: Perfect (0 mismatches)

**validate_migration.py** - Migration validation script
- Verifies dual-format storage correctness
- Ensures frequencies only in pinyins_tone3, not in pinyins_display
- Validates format count matching between tone3 and display columns

### Visualization

**analyze_coverage_curve.py** - Generate character coverage curve
- Output: `../../../data/character_set/analysis/character_coverage_curve.png`
- Shows: Coverage % vs characters learned

**analyze_vocabulary_growth.py** - Generate vocabulary growth by HSK level
- Output: `../../../data/character_set/analysis/vocabulary_growth_by_hsk.png`
- Shows: Cumulative character count across HSK 1-9 and beyond

## Outputs

All outputs are stored in `../../../data/character_set/analysis/`:

### Data Files
- `pinyin_trie.json` - Complete pinyin Trie (1.6MB, 51K lines)
- `PINYIN_TRIE_ANALYSIS.md` - Comprehensive analysis summary with key findings

### Trie Visualizations
- `pinyin_trie_visualization.svg` - Full Trie (all 7 levels, interactive tooltips)
- `pinyin_trie_visualization_depth1.svg` - Root + first level overview
- `pinyin_trie_visualization_depth2.svg` - First 2 levels overview
- `pinyin_trie_visualization_depth3.svg` - First 3 levels overview
- `pinyin_trie_visualization_h_branch.svg` - H-branch focused view (full depth with placeholders)

### Statistical Charts
- `tone_distributions.png` - 3-panel tone comparison (by syllables, characters, frequency)
- `depth_distribution.png` - Node count by depth (depths 1-7)
- `polyphonic_characters.png` - Top 20 characters with most pronunciations
- `syllable_complexity.png` - Character count distribution per syllable
- `syllable_tone_matrix.png` - Heatmap of 401 base syllables × 5 tones with character counts

### Other Visualizations
- `character_coverage_curve.png` - Coverage analysis
- `frequency_distribution.png` - Character frequency distribution (Zipf's law)
- `vocabulary_growth_by_hsk.png` - HSK vocabulary growth

## Pinyin Trie Structure

The Trie uses **character-level nodes** in **normalized tone3 format**:

```json
{
  "children": {
    "y": {
      "children": {
        "i": {
          "children": {
            "1": {
              "children": {},
              "is_end": true,
              "characters": [
                {
                  "char": "一",
                  "pinyin_freq": 8867,
                  "corpus_freq": 11991
                },
                {
                  "char": "医",
                  "pinyin_freq": 238,
                  "corpus_freq": 251
                }
              ],
              "count": 15,
              "total_freq": 9884
            }
          }
        }
      }
    }
  }
}
```

### Node Structure

**Intermediate nodes:**
- `children`: dict mapping letter → child node
- `is_end`: false

**Terminal nodes:**
- `children`: empty dict
- `is_end`: true
- `characters`: array of character objects with:
  - `char`: the Chinese character
  - `pinyin_freq`: frequency of this specific char-pinyin pair in corpus
  - `corpus_freq`: total character frequency in corpus (all pronunciations)
- `count`: number of unique characters for this syllable
- `total_freq`: sum of pinyin frequencies

### Key Design Decisions

1. **Character-level nodes** (not syllable-level)
   - Each letter is a separate node
   - All pinyin in tone3 format (tone numbers at end): yi4, zhong1, de0

2. **No normalization needed** (pypinyin provides consistent format)
   - Uses `pinyins_tone3` column directly from step6_with_freq.csv
   - Old mixed formats (Unihan tone marks + pypinyin tone numbers) eliminated
   - **Result**: 1,307 unique syllables (down from 2,004 with old system)
   - Zero duplicate syllables (was 612 duplicates / 30.5%)

3. **Metadata at terminal nodes only**
   - Character list, count, and frequency aggregation
   - Intermediate nodes only store routing information

4. **Dual frequency tracking**
   - `pinyin_freq`: frequency of this specific char-pinyin pair (from corpus)
   - `corpus_freq`: total character frequency across all pronunciations
   - Example: 的 appears 28,594 times total, but `de` pronunciation = 28,524 times

## Statistics (Corpus-Driven Analysis)

### Syllable Distribution
- **Total unique syllables**: 1,161 (only syllables with pinyin_freq > 0)
- **Base syllables (without tone)**: 401 unique base forms across 5 tones
- **Character count per syllable**: 1-37 (mean: 4.5, median: 3)
- **Most polyphonic**: yi4 (37 chars), shi4 (32 chars), ji4 (30 chars)
- **100% frequency coverage**: All included syllables are actively used in corpus

### Tone Distribution (by unique syllables)
- **Neutral**: 25 syllables (2.2%)
- **Tone 1**: 296 syllables (25.5%)
- **Tone 2**: 239 syllables (20.6%)
- **Tone 3**: 283 syllables (24.4%)
- **Tone 4**: 318 syllables (27.4%)

### Character Distribution
- **Total characters**: 5,002 (corpus frequency > 0)
- **Character-syllable pairs**: 5,221 (accounting for polyphonic characters)
- **Monophonic characters**: 91.8% (most characters have one pronunciation)
- **Polyphonic characters**: 199 (3.8% of corpus characters)
  - Most polyphonic: 著 (5 pronunciations), 的 (4), 和 (4), 一 (3)

## Top 20 Most Frequent Syllables

(By pinyin frequency from corpus)

| Rank | Syllable | Characters | Total Freq |
|------|----------|------------|------------|
| 1    | wo3      | 1          | 32,055     |
| 2    | de0      | 4          | 29,973     |
| 3    | ta1      | 8          | 20,827     |
| 4    | shi4     | 46         | 20,510     |
| 5    | le0      | 1          | 17,783     |
| 6    | ni3      | 10         | 14,845     |
| 7    | zai4     | 5          | 11,636     |
| 8    | bu4      | 12         | 10,841     |
| 9    | you3     | 3          | 10,413     |
| 10   | yi1      | 15         | 9,884      |
| 11   | zhe4     | 5          | 9,320      |
| 12   | men0     | 2          | 8,751      |
| 13   | dao4     | 11         | 6,980      |
| 14   | ren2     | 5          | 6,765      |
| 15   | ge4      | 6          | 6,711      |
| 16   | shi2     | 17         | 6,124      |
| 17   | mu3      | 7          | 5,834      |
| 18   | yao4     | 13         | 5,749      |
| 19   | me0      | 5          | 5,587      |
| 20   | hen3     | 4          | 5,403      |

## Usage

### Build the Trie
```bash
cd scripts/character_set/analysis
python3 build_pinyin_trie.py
```

### Run Statistical Analysis
```bash
# Generates 5 charts + PINYIN_TRIE_ANALYSIS.md
python3 analyze_trie.py
```

### Generate Visualizations
```bash
# Full Trie visualization with interactive tooltips
python3 visualize_trie.py

# Depth-limited overviews (faster to load)
python3 visualize_trie.py --depth 1
python3 visualize_trie.py --depth 2
python3 visualize_trie.py --depth 3

# Focused branch visualization (full depth, single branch)
python3 visualize_trie.py --branch h

# Options
python3 visualize_trie.py --format png  # Output as PNG instead of SVG
python3 visualize_trie.py --compact     # Tighter spacing for full tree
```

### Verify migration (already complete)
```bash
python3 compare_unihan_vs_pypinyin.py  # Verify pypinyin coverage
python3 validate_migration.py          # Verify dual-format storage
```

## Dependencies

- Python 3.7+
- Standard library: json, csv, re, collections, pathlib, argparse
- **matplotlib** - Required for statistical chart generation (analyze_trie.py)
  - Install: `pip install matplotlib`
- **graphviz** - Required for Trie visualization (visualize_trie.py)
  - Install Python package: `pip install graphviz`
  - Install system package: `brew install graphviz` (macOS) or apt/yum on Linux
- `pypinyin` - Required for migration verification scripts only (already installed)

## Future Enhancements

Potential additions:
- **Interactive Trie Explorer** (planned for blog post) - See `docs/KNOWN_ISSUES.md`
  - Character lookup: Type any Chinese character to see all pronunciations
  - Reverse lookup: Type pinyin to see all matching characters
  - Frequency visualization and pronunciation distribution
  - Client-side web tool (no backend required)
- Syllable similarity analysis (edit distance, phonetic neighbors)
- Integration with audio files (data/audio/)
- Syllable difficulty ranking for learners
- Common confusion pairs analysis

## Related Documentation

- `data/character_set/analysis/PINYIN_TRIE_ANALYSIS.md` - Comprehensive analysis findings
- `docs/KNOWN_ISSUES.md` - Roadmap items including Interactive Trie Explorer
- `docs/LESSONS_LEARNED.md` - Design decisions and lessons from Trie development
- `docs/migrations/pinyin-format-2025-11/` - Dual-format migration documentation
