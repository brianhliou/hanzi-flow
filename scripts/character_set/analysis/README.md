# Character Set Analysis Scripts

Analysis tools for the Chinese character dataset.

## Scripts

### Core Analysis

**build_pinyin_trie.py** - Build character-level Trie of all pinyin syllables
- Input: `../../../data/character_set/step6_with_freq.csv` (characters with corpus freq > 0)
- Output: `../../../data/character_set/analysis/pinyin_trie.json`
- **Key Feature**: Uses `pinyins_tone3` column directly (already in tone3 format)
- Structure: Character-level nodes (y → i → 4), terminal nodes store character metadata
- Statistics: **1,307 unique syllables** (down from 2,004 with old mixed formats), 5,002 characters

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

### Visualizations
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

## Statistics (After Migration)

### Syllable Distribution
- **Total unique syllables**: 1,307 (down from 2,004 with mixed formats)
- **Character count per syllable**: 1-59 (mean: 6.2, median: 4)
- **Most polyphonic**: yi4 (59 chars), yu4 (53 chars), shi4 (46 chars)

### Tone Distribution
- **Tone 1**: 322 syllables (24.6%)
- **Tone 2**: 261 syllables (20.0%)
- **Tone 3**: 319 syllables (24.4%)
- **Tone 4**: 356 syllables (27.2%)
- **Neutral**: 49 syllables (3.7%)

### Frequency Coverage
- **Syllables with pinyin freq > 0**: 1,161 (88.8%)
- **Syllables with pinyin freq = 0**: 146 (11.2%)
  - Characters that exist in corpus but this specific pronunciation not used

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

### Verify migration (already complete)
```bash
python3 compare_unihan_vs_pypinyin.py  # Verify pypinyin coverage
python3 validate_migration.py          # Verify dual-format storage
```

## Dependencies

- Python 3.7+
- Standard library only (json, csv, re, collections, pathlib)
- `pypinyin` - Required for migration verification scripts only (already installed)
- Optional: matplotlib (for frequency distribution graphs in build_step6_freq.py)

## Future Enhancements

Potential additions:
- Interactive visualization of the Trie structure
- Syllable similarity analysis (edit distance, phonetic neighbors)
- Integration with audio files (data/audio/)
- Syllable difficulty ranking for learners
- Common confusion pairs analysis
