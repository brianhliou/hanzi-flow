# Pinyin Trie Analysis - Key Findings

**Date:** November 6, 2025
**Corpus:** 79,704 sentences from Tatoeba
**Characters analyzed:** 5,002 unique characters (corpus frequency > 0)

---

## Executive Summary

This analysis examines 1,161 unique pinyin syllables actually used in a corpus of ~80K Chinese sentences, revealing patterns in tone distribution, character complexity, and polyphonic pronunciation that differ significantly from theoretical expectations.

---

## Key Statistics

### Syllable Coverage
- **1,161 unique syllables** used in corpus (vs ~1,300 theoretically possible)
- **142 theoretical syllables** (10.9%) never appear in practice
- **100% frequency coverage** - all included syllables are actively used

### Character Distribution
- **5,002 total characters** appear in corpus
- **5,221 character-syllable pairs** (some characters have multiple pronunciations)
- **91.8% monophonic** - most characters have only one pronunciation in practice
- **8.2% polyphonic** - 430 character-syllable pairs from polyphonic characters

### Polyphonic Characters
- **199 polyphonic characters** (3.8% of all characters)
- **Most polyphonic:** 著 (5 pronunciations), 的 (4), 和 (4), 一 (3)
- **Example:** 的 appears 28,594 times total:
  - `de0`: 28,524 (99.8%) - particle usage
  - `di4`: 58 (0.2%) - noun "target"
  - `di1`: 7 (<0.1%) - rare
  - `di2`: 5 (<0.1%) - rare

---

## Tone Distributions

### By Unique Syllables (each syllable counted once)
| Tone | Count | Percentage |
|------|-------|------------|
| Neutral | 25 | 2.2% |
| Tone 1 | 296 | 25.5% |
| Tone 2 | 239 | 20.6% |
| Tone 3 | 283 | 24.4% |
| Tone 4 | 318 | 27.4% |

**Insight:** Fairly balanced distribution across the four main tones, neutral tone rare.

### By Unique Characters (each character counted once)
| Tone | Count | Percentage |
|------|-------|------------|
| Neutral | 35 | 0.7% |
| Tone 1 | 1,273 | 24.4% |
| Tone 2 | 1,273 | 24.4% |
| Tone 3 | 887 | 17.0% |
| Tone 4 | 1,753 | 33.6% |

**Insight:** Tone 4 dominant (33.6%), Tone 3 least common (17.0%).

### By Corpus Frequency (weighted by actual usage)
| Tone | Count | Percentage |
|------|-------|------------|
| Neutral | 86,632 | 8.4% |
| Tone 1 | 212,405 | 20.5% |
| Tone 2 | 202,617 | 19.6% |
| Tone 3 | 207,082 | 20.0% |
| Tone 4 | 326,895 | 31.6% |

**Insight:** Neutral tone jumps to 8.4%! Common particles (的, 了, 地) are heavily used.

**Key Takeaway:** Tone 4 consistently most common across all measures. Neutral tone usage (8.4%) far exceeds its representation in the syllable inventory (2.2%), showing the outsized importance of grammatical particles in Chinese.

---

## Syllable Complexity

### Character Count Distribution
| Characters per Syllable | Number of Syllables |
|-------------------------|---------------------|
| 1 char | 132 syllables |
| 2 chars | 210 syllables |
| 3 chars | 232 syllables |
| 4 chars | 215 syllables |
| 5-10 chars | 187 syllables |
| 11-20 chars | 128 syllables |
| 21-37 chars | 57 syllables |

**Statistics:**
- Min: 1 character per syllable
- Max: 37 characters per syllable (`yi4`)
- Mean: 4.5 characters per syllable
- Median: 3 characters per syllable

### Most Crowded Syllables
1. `yi4` - 37 characters (意, 义, 议, 异, 易, 亿, 艺, 益, ...)
2. `shi4` - 32 characters (是, 事, 市, 式, 试, 视, 世, 士, ...)
3. `ji4` - 30 characters (记, 际, 计, 技, 季, 继, 既, 寄, ...)

### Least Crowded (Unique)
- `wo3` - 1 character (我)
- `le0` - 1 character (了)
- `ni3` - 1 character (你) [in corpus; 您 also exists]

---

## Syllable Depth Distribution

| Depth | Nodes | Description |
|-------|-------|-------------|
| 1 | 23 | Initial consonants (b, c, d, ..., z) |
| 2 | 108 | Two-letter combinations |
| 3 | 460 | Three-letter combinations |
| 4 | 609 | **Peak** - most syllables complete here |
| 5 | 367 | Longer syllables |
| 6 | 73 | Even longer (chang, chuan, etc.) |
| 7 | 8 | Longest syllables (chuang, shuang, zhuang) |

**Peak at depth 4:** Most syllables are 4-5 letters long (e.g., `tian1`, `wang2`, `hao3`).

**Longest syllables (depth 7, all -uang):**
- chuang1, chuang2, chuang3, chuang4
- shuang1, shuang3
- zhuang1, zhuang4

---

## Most Common Syllables

### Top 10 by Frequency
| Rank | Syllable | Chars | Frequency | Notes |
|------|----------|-------|-----------|-------|
| 1 | wo3 | 1 | 32,055 | 我 (I/me) |
| 2 | de0 | 3 | 29,973 | 的/得/地 (particles) |
| 3 | ta1 | 6 | 20,827 | 他/她/它 (he/she/it) |
| 4 | shi4 | 32 | 20,510 | 是 (to be) + 31 other chars |
| 5 | le0 | 1 | 17,783 | 了 (aspect marker) |
| 6 | ni3 | 4 | 14,845 | 你/您 (you) |
| 7 | zai4 | 4 | 11,636 | 在 (at/in) |
| 8 | bu4 | 8 | 10,841 | 不 (not) |
| 9 | you3 | 3 | 10,413 | 有 (to have) |
| 10 | yi1 | 9 | 9,884 | 一 (one) |

**Insight:** Top 10 syllables account for 194,807 occurrences (18.8% of all character instances). Function words and basic vocabulary dominate.

### Least Common (frequency = 1)
20 syllables appear exactly once in the entire corpus: a2, tuan1, tun3, kun3, kui3, en4, rang2, rui3, hong4, heng4, mao3, jiong3, jiao2, lang1, leng4, pou1, pei1, cuan1, chuai1, chuai4

---

## Surprising Findings

### 1. Neutral Tone Discrepancy
- **By syllables:** Only 2.2% (25 syllables)
- **By usage:** 8.4% (86,632 instances)
- **Why:** Extremely common particles (的, 了, 么, 吗) are neutral tone

### 2. Polyphonic Reality Check
- **Theory:** Many characters have multiple pronunciations in dictionaries
- **Practice:** Only 3.8% of corpus characters are actually polyphonic
- **Example:** 的 has 4 pronunciations, but `de0` is used 99.8% of the time

### 3. Syllable Homophony
- `yi4` maps to 37 different characters - context is crucial!
- Yet `wo3` maps to only 我 - zero ambiguity
- Average: 4.5 characters per syllable

### 4. Missing Syllables
- 142 theoretically valid syllables never appear in 80K sentences
- Either extremely rare or literary/archaic

---

## Data Quality Notes

- **Corpus:** 79,704 sentences from Tatoeba
- **Total character instances:** 1,035,631
- **Frequency definitions:**
  - `pinyin_freq`: How many times THIS CHARACTER was pronounced with THIS SPECIFIC PINYIN
  - `corpus_freq`: How many times THIS CHARACTER appears total (all pronunciations)
  - For polyphonic characters, corpus_freq = sum of all pinyin_freq values
- **Filtering:** Only includes characters with corpus frequency > 0

---

## Visualizations Generated

1. **tone_distributions.png** - 3-panel comparison of tone distributions
2. **depth_distribution.png** - Node count by syllable depth
3. **polyphonic_characters.png** - Top 20 characters with most pronunciations
4. **syllable_complexity.png** - Character count distribution per syllable
5. **pinyin_trie_visualization.svg** - Interactive full Trie structure

---

## Applications

This analysis enables:
- **Language learning:** Focus on most common syllables and patterns
- **Text-to-speech:** Pronunciation disambiguation for polyphonic characters
- **Input methods:** Predictive typing based on syllable frequency
- **Linguistic research:** Empirical data on spoken Chinese phonology

---

## Methodology

**Data Pipeline:**
1. Extract characters from 79,704 sentences
2. Generate pinyin with frequency tracking (pypinyin + corpus analysis)
3. Build character-level Trie structure (each node = one letter)
4. Analyze distributions, patterns, and edge cases
5. Generate visualizations and statistical summaries

**Tools:** Python 3.9+, matplotlib, graphviz, pandas (analysis)

---

*Analysis generated by `scripts/character_set/analysis/analyze_trie.py`*
*Trie built by `scripts/character_set/analysis/build_pinyin_trie.py`*
*Visualizations by `scripts/character_set/analysis/visualize_trie.py`*
