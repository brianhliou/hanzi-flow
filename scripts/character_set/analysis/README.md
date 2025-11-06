# Character Set Analysis Scripts

Analysis tools for the Chinese character dataset.

## Scripts

### Core Analysis

**build_pinyin_trie.py** - Build character-level Trie of all pinyin syllables
- Input: `../../../data/character_set/step7_with_freq.csv` (characters with corpus freq > 0)
- Output: `../../../data/character_set/analysis/pinyin_trie.json`
- **Key Feature**: Normalizes all pinyin to tone3 format (e.g., `yì → yi4`) to avoid duplicates
- Structure: Character-level nodes (y → i → 4), terminal nodes store character metadata
- Statistics: 1,392 unique syllables, 4,973 characters, ~7,600 character-syllable mappings

**validate_trie_vs_reference.py** - Validate Trie against reference syllables
- Compares against: `../../../data/audio/syllables_enumeration.json`
- Results: 85.9% overlap (1,373 / 1,598 syllables)
- Identifies extra syllables (19) and missing syllables (225)

**check_duplicate_syllables.py** - Detect duplicate syllables in mixed formats
- Used to discover the tone mark vs tone number duplication issue
- Before normalization: 612 duplicates (69.8% of mappings affected)
- After normalization: 0 duplicates ✓

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
                  "unihan_freq": 32747,
                  "corpus_freq": 11652
                },
                {
                  "char": "医",
                  "unihan_freq": 460,
                  "corpus_freq": 251
                }
              ],
              "count": 11,
              "total_freq": 34667
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
  - `unihan_freq`: frequency from Unihan (data/sources)
  - `corpus_freq`: frequency in sentence corpus
- `count`: number of unique characters for this syllable
- `total_freq`: sum of Unihan frequencies

### Key Design Decisions

1. **Character-level nodes** (not syllable-level)
   - Each letter is a separate node
   - Tone-marked vowels like ā, é treated as single Unicode characters
   - BUT normalized to tone3 format (a1, e2) to avoid duplicates

2. **Tone3 normalization** (tone numbers at end)
   - Converts `yì → yi4`, `zhōng → zhong1`, `de → de0`
   - Eliminates duplicates from mixed Unihan (tone marks) and pypinyin (tone numbers)
   - Before: 2,004 syllables (612 duplicates, 69.8% affected)
   - After: 1,392 syllables (0 duplicates) ✓

3. **Metadata at terminal nodes only**
   - Character list, count, and frequency aggregation
   - Intermediate nodes only store routing information

4. **Frequency disambiguation**
   - `unihan_freq`: from Unihan database (data/sources)
   - `corpus_freq`: actual occurrences in sentence corpus
   - Note: Unihan freq may be 0 for characters added by pypinyin enrichment

## Statistics

### Syllable Distribution
- **Total unique syllables**: 1,392
- **Character count per syllable**: 1-52 (mean: 5.5, median: 4)
- **Most polyphonic**: yi4 (52 chars), yu4 (47 chars), shi4 (44 chars)

### Tone Distribution
- **Tone 1**: 318 syllables (22.8%)
- **Tone 2**: 252 syllables (18.1%)
- **Tone 3**: 304 syllables (21.8%)
- **Tone 4**: 345 syllables (24.8%)
- **Neutral**: 173 syllables (12.4%)

### Frequency Coverage
- **Syllables with Unihan freq > 0**: 1,214 (87.2%)
- **Syllables with Unihan freq = 0**: 178 (12.8%)
  - These are from pypinyin enrichment without Unihan data

### Validation vs Reference
- **Reference**: 1,598 syllables (from syllables_enumeration.json)
- **Overlap**: 1,373 (85.9% coverage)
- **Extra in Trie**: 19 (edge cases: lüe4, m2, n4, ng2, ng4)
- **Missing from Trie**: 225 (valid Mandarin, but not in our corpus)

## Top 20 Most Frequent Syllables

(By Unihan frequency)

| Rank | Syllable | Characters | Total Freq |
|------|----------|------------|------------|
| 1    | de0      | 4          | 88,086     |
| 2    | shi4     | 44         | 38,624     |
| 3    | yi1      | 11         | 34,667     |
| 4    | zhe4     | 4          | 33,428     |
| 5    | le0      | 1          | 30,101     |
| 6    | men0     | 4          | 29,940     |
| 7    | lai2     | 4          | 29,098     |
| 8    | bu4      | 12         | 27,989     |
| 9    | shi2     | 16         | 25,204     |
| 10   | ge4      | 6          | 25,192     |

## Usage

### Build the Trie
```bash
cd scripts/character_set/analysis
python3 build_pinyin_trie.py
```

### Validate against reference
```bash
python3 validate_trie_vs_reference.py
```

### Check for duplicates
```bash
python3 check_duplicate_syllables.py
```

## Dependencies

- Python 3.7+
- Standard library only (json, csv, re, collections, pathlib)
- Optional: matplotlib (for frequency distribution graphs in build_step7_freq.py)

## Future Enhancements

Potential additions:
- Interactive visualization of the Trie structure
- Syllable similarity analysis (edit distance, phonetic neighbors)
- Integration with audio files (data/audio/)
- Syllable difficulty ranking for learners
- Common confusion pairs analysis
