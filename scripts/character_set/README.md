# Character Set Build Scripts

Two character dataset pipelines with different purposes:

## v0/ - Learner-Focused Dataset (Legacy)

**Output:** `data/character_set/step6_with_freq.csv`

Corpus-enriched dataset optimized for language learners:
- 20,992 characters (CJK Unified Ideographs core, U+4E00-U+9FFF)
- Includes HSK levels, example words, corpus frequencies
- Dual-format pinyin storage (tone3 + display)
- 6-step pipeline with intermediate snapshots

**Use cases:**
- Language learning applications
- Vocabulary tracking with HSK progression
- Frequency-based character prioritization

See `v0/README.md` for full documentation.

## v1/ - Source of Truth Reference (New)

**Output:** `data/character_set/sot_characters_v1.0.csv`

Authoritative Unicode-based character reference:
- ~97,000 characters (CJK Unified Ideographs + Extensions A-J)
- Minimal schema: `id, char, codepoint, script_type, pinyins, gloss_en`
- Idempotent build scripts (modify single file in-place)
- No corpus dependencies (frequency, HSK, examples → separate tables)

**Use cases:**
- Comprehensive character lookup
- Dictionary applications
- Unicode reference implementation

See `v1/README.md` for full documentation.

## Directory Structure

```
scripts/character_set/
├── v0/                          # Legacy learner-focused pipeline
│   ├── build_step1_base.py
│   ├── build_step2_pinyin_pypinyin.py
│   ├── build_step3_cedict.py
│   ├── build_step4_variants.py
│   ├── build_step5_hsk.py
│   ├── build_step6_freq.py
│   └── README.md
├── v1/                          # New SOT reference pipeline
│   ├── build_step1_extract_all_cjk.py
│   ├── build_step2_add_pinyins.py
│   ├── build_step3_add_gloss.py
│   ├── build_step4_add_script_type.py
│   └── README.md
└── analysis/                    # Shared analysis tools
    ├── build_pinyin_trie.py
    ├── analyze_trie.py
    └── visualize_trie.py
```

## Which Pipeline Should I Use?

- **Building a learner app?** → Use v0 (corpus-enriched with HSK levels)
- **Need comprehensive Unicode coverage?** → Use v1 (SOT reference)
- **Want both?** → Run both pipelines (they produce complementary datasets)
