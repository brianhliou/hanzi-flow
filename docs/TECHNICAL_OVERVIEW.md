# Technical Overview

Detailed technical documentation for Hanzi Flow's architecture, algorithms, and data models.

---

## Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Storage**: IndexedDB via Dexie.js
- **Deployment**: Vercel

### Data Processing
- **Language**: Python 3.9+
- **Libraries**:
  - pypinyin (pinyin conversion)
  - jieba (word segmentation)
  - pandas, matplotlib (analysis)
- **Data Sources**:
  - Tatoeba corpus (sentences)
  - CC-CEDICT (dictionary)
  - elkmovie/hsk30 (HSK 3.0 lists)
- **AI Enhancement**: OpenAI GPT-4o-mini (translations, pinyin refinement)

### Data Format
- **Processing**: CSV format (sequential pipeline)
- **Frontend**: JSON format
- **Storage**: File-based (no database in pipeline)

---

## System Architecture

### Data Flow

```
Raw Sources (Tatoeba, CEDICT, HSK)
    ↓
Character Pipeline (6 steps) → step6_with_freq.csv
    ↓
Sentence Pipeline (4-6 steps) → step5_pinyin_refined.csv
    ↓
JSON Export → app/public/data/
    ↓
Next.js App (loads JSON into memory)
    ↓
IndexedDB (user progress only)
```

### Frontend Architecture

```
Practice Page
    ↓
Sentence Selection (NSS Algorithm)
    ↓
Character Input & Scoring
    ↓
Mastery Update (EWMA)
    ↓
IndexedDB Persistence
```

**Key Libraries**:
- `sentence-selection.ts` - NSS adaptive algorithm (22KB, core intelligence)
- `mastery.ts` - EWMA-based character mastery tracking
- `db.ts` - IndexedDB persistence (Dexie.js)
- `scoring.ts` - Pinyin validation against character_set
- `selection-config.ts` - Tunable algorithm parameters

---

## Data Models

### Character Dataset Schema

**File**: `data/character_set/step6_with_freq.csv` (20,992 characters)

```csv
id,char,codepoint,pinyins_tone3,pinyins_display,script_type,variants,gloss_en,examples,hsk_level,freq
1,一,U+4E00,yi1(8867)|yi2(1825)|yi4(1299),yī|yí|yì,neutral,,one,一一|一一對應|一一对应,1,11991
2,丁,U+4E01,ding1(73)|zheng1,dīng|zhēng,neutral,,surname Ding,一丁不識|一丁不识|一丁點,7-9,73
```

**Fields**:
- `id`: Sequential integer (1-20,992)
- `char`: Chinese character
- `codepoint`: Unicode identifier (e.g., U+4E00)
- `pinyins_tone3`: Canonical format with tone numbers AND pinyin-level frequencies: `yi1(8867)|yi4(1299)`
- `pinyins_display`: Display format with tone marks, NO frequencies: `yī|yì`
- `script_type`: `simplified`, `traditional`, `neutral`, or `ambiguous`
- `variants`: Pipe-separated variant characters (simplified/traditional pairs)
- `gloss_en`: English definition from CC-CEDICT
- `examples`: Pipe-separated example words containing this character
- `hsk_level`: HSK level (1, 2, 3, 4, 5, 6, or "7-9") or empty for non-HSK characters
- `freq`: Character frequency count in sentence corpus (0 if character doesn't appear)

**Coverage Statistics**:
- Pinyin: 100% (20,992/20,992) - pypinyin provides complete coverage
- Polyphonic characters: 29.6% (6,206 characters with multiple pronunciations)
- Pinyin-level frequencies: 5,272 unique char-pinyin pairs tracked
- English glosses: 67.4% (14,152)
- Example words: 41.1% (8,618)
- Variant mappings: 34.6% (7,254)
- HSK classification: 20.0% (4,193 characters in HSK 1-9 curriculum)
- Corpus usage: 23.8% (5,002 characters with freq > 0)

**Script Type Distribution**:
- Simplified: 12.5% (2,618)
- Traditional: 22.1% (4,634)
- Neutral: 65.4% (13,738)
- Ambiguous: 0.0% (2)

**HSK Level Distribution**:
- HSK 1: 2.0% (415 characters - 300 simplified + 115 traditional variants)
- HSK 2: 2.0% (429 characters)
- HSK 3: 2.1% (435 characters)
- HSK 4: 2.1% (432 characters)
- HSK 5: 2.0% (423 characters)
- HSK 6: 2.0% (414 characters)
- HSK 7-9: 7.8% (1,644 characters - 1,200 simplified + 444 traditional variants)
- No HSK: 80.0% (16,800 characters - archaic, rare, or specialized)

### Sentence Dataset Schema

**File**: `data/sentences/step5_pinyin_refined.csv` (~79,700 sentences)

**Production JSON**: `app/public/data/sentences/sentences_with_translation.json`

```json
{
  "id": 1,
  "sentence": "我們試試看！",
  "english_translation": "Let's give it a try!",
  "script_type": "traditional",
  "hskLevel": "3",
  "chars": [
    {"char": "我", "pinyin": "wo3"},
    {"char": "們", "pinyin": "men"},
    {"char": "試", "pinyin": "shi4"},
    {"char": "試", "pinyin": "shi4"},
    {"char": "看", "pinyin": "kan4"},
    {"char": "！", "pinyin": ""}
  ]
}
```

**Fields**:
- `id`: Sentence identifier
- `sentence`: Full Chinese text
- `english_translation`: English translation of the sentence
- `script_type`: `simplified`, `traditional`, `neutral`, or `ambiguous`
- `hskLevel`: HSK level classification ("1"-"6" or "7-9"), optional (unclassified sentences excluded from practice)
- `chars`: Array of character-pinyin pairs
  - `char`: Individual character
  - `pinyin`: Context-aware pinyin in TONE3 format (e.g., `wo3`, `men`, `shi4`)
  - Empty string for non-Chinese characters (punctuation, numbers)

**Pinyin Format**:
- Tone numbers: 1, 2, 3, 4 (no number for neutral tone)
- Style: TONE3 (pypinyin Style)
- Context-aware via jieba word segmentation
- Handles polyphonic characters based on context
- Enhanced with 2,870 AI-verified improvements for common polyphonic characters

---

## Next Sentence Selection (NSS) Algorithm

> **📖 See [`NSS_ALGORITHM.md`](./NSS_ALGORITHM.md) for complete technical documentation**

The NSS algorithm is an adaptive, batch-based sentence selector that maintains 90-95% comprehension by balancing multiple factors:

- **Character mastery** (EWMA-based learning curves)
- **Spaced repetition** (SRS scheduling with overdue boost)
- **Optimal difficulty** (2-5 unknown characters per sentence)
- **Novelty** (time since last seen)
- **Sentence mastery** (avoid grinding same sentences)

### How It Works

The algorithm operates in a 5-stage pipeline:

1. **Filter** → Get eligible sentences (script, HSK, cooldown, skip)
2. **Sample** → Random 300 from eligible pool
3. **Score** → Calculate score based on mastery, novelty, difficulty
4. **Fallback** → If <8 scored, progressively relax constraints (5 levels)
5. **Select** → Top 8, shuffle, queue for practice

### Key Concepts

**Difficulty (k unknowns):**
- Target: 2-5 unknown characters per sentence (normal mode)
- Tightens to 1-3 under review backlog (>80 due words)
- Unknown threshold: θ_known = 0.6 (characters with s < 0.6)

**Mastery Tracking:**
- Each character has mastery score `s` ∈ [0, 1] updated via EWMA
- SRS scheduling: stability starts at 1 hour, grows 1.2x on success
- Characters past `next_review_ts` get 2.0x boost in scoring

**Batch & Prefetch:**
- Generates 8 sentences per batch
- Prefetches next batch when 2 remain for smooth UX
- Queue invalidates on preference changes (script/HSK filter)

### Implementation

- **Code:** `app/lib/sentence-selection.ts`
- **Config:** `app/lib/selection-config.ts`
- **Docs:** [`NSS_ALGORITHM.md`](./NSS_ALGORITHM.md) (detailed technical reference)

---

## Key Design Decisions

### Why Context-Aware Pinyin?

Chinese characters are often polyphonic (多音字). The same character can have different pronunciations depending on context:
- 地: `de` (particle) vs `di4` (earth/ground)
- 了: `le` (particle) vs `liao3` (to finish)
- 著/着: `zhe` (aspect marker) vs `zhao2`/`zhuo2` (verb)
- 谁: `shei2` (colloquial) vs `shui2` (formal)

We use **jieba** for word segmentation, then **pypinyin** to generate context-appropriate pinyin. Additionally, we've applied **2,870 AI-verified pinyin improvements** via OpenAI to fix common polyphonic character issues that pypinyin alone misses. This ensures learners practice the correct pronunciation for each usage.

### Why Sentence-Based Learning?

- Provides context for vocabulary (vs. isolated flashcards)
- Mimics real reading scenarios
- Allows difficulty calibration (sentence-level character distribution)
- Enables typing practice in natural language flow
- Supports both recognition (reading) and recall (typing)

### Why Dual-Format Pinyin Storage?

**Decision**: Store both `pinyins_tone3` (yi1) and `pinyins_display` (yī) redundantly in the dataset.

**Why tone numbers for input?**
- Easier to type than tone marks (wǒ → wo3)
- Standard input method for Chinese IME users
- Consistent with how learners type Chinese on keyboards
- Simpler validation logic

**Why dual format?**
- Zero conversion code needed (eliminated 6+ conversion utilities)
- Guaranteed consistency (both generated from single pypinyin source)
- Clearer semantics (tone3 for logic/matching, display for UI rendering)
- App can display tone marks while accepting tone numbers as input
- Storage cost minimal (~300KB), simplicity benefit massive

**Migration**: Completed Nov 2025 - eliminated 612 duplicate syllables (30.5% duplication) that existed under old mixed-format system. See: [docs/migrations/pinyin-format-2025-11/](./migrations/pinyin-format-2025-11/)

### Why IndexedDB (Not PostgreSQL)?

- **Local-first**: No server, no auth, instant start
- **Privacy**: All data stays on user's device
- **Portable**: Export/import via browser
- **Fast**: No network latency
- **Free**: No hosting costs for MVP
- **Trade-off**: No cross-device sync (acceptable for portfolio project)

### Why EWMA over Leitner/SM-2?

- Simpler implementation (no interval calculation)
- Gradual adaptation (vs discrete boxes/intervals)
- Works naturally with sentence-level scoring
- Mastery can both increase AND decrease (realistic forgetting)

### Why pypinyin as Single Source?

**Before Nov 2025**: Used both Unihan (tone marks) and pypinyin (tone3) → 612 duplicate syllables (30.5%)

**After migration**:
1. **Comprehensive coverage** - 100% (vs 99.7% with Unihan)
2. **Context awareness** - Can detect different usages
3. **Heteronym support** - `heteronym=True` gives all valid pronunciations
4. **Format flexibility** - Can output any format we need (TONE3, TONE)
5. **Well maintained** - Active library with good docs
6. **Simpler pipeline** - One source = one format = no conversion needed

---

## Data Pipeline Overview

### Character Set Pipeline (6 steps)

```
step1: Generate 20,992 CJK base characters
step2: Add dual-format pinyin via pypinyin (tone3 + display)
step3: Add English glosses from CC-CEDICT
step4: Add script types and variants (simplified/traditional)
step5: Add HSK levels (1-9 from elkmovie/hsk30)
step6: Add character & pinyin frequencies from corpus
```

**Output**: `data/character_set/step6_with_freq.csv`

See: [scripts/character_set/README.md](../scripts/character_set/README.md) for complete documentation

### Sentence Pipeline (4-6 steps)

```
step1: Classify script type
step2: Add character-level pinyin
step3: Add translations (OpenAI)
step4: Classify HSK levels
step5: [Optional] Refine pinyin with OpenAI (2,870 improvements applied)
step6: Export to production JSON
```

**Output**: `data/sentences/step5_pinyin_refined.csv` → `app/public/data/sentences/*.json`

See: [scripts/sentences/README.md](../scripts/sentences/README.md) for complete documentation

### Data Sources

- **Sentences**: [Tatoeba](https://tatoeba.org/) (CC BY 2.0 FR)
- **Dictionary**: [CC-CEDICT](https://cc-cedict.org/) (CC BY-SA 4.0)
- **HSK Classification**: [elkmovie/hsk30](https://github.com/elkmovie/hsk30) (MIT)
- **Audio**: Generated using AWS Polly (Zhiyu voice)

---

## Performance Considerations

### Frontend

- **Data Loading**: JSON files loaded into memory on app start (~15MB total)
- **IndexedDB**: Only stores user progress data (mastery, sentences, queue)
- **NSS Performance**: Samples 300 from ~80k sentences in <50ms
- **Queue Prefetching**: Background prefetch prevents wait time between sentences

### Data Pipeline

- **Character Pipeline**: ~30 seconds for full rebuild (6 steps)
- **Sentence Pipeline**:
  - Steps 1-2: ~5 minutes (79k sentences)
  - Step 3 (translation): 4-5 hours with OpenAI API (~$10 cost)
  - Step 5 (refinement): 4-5 hours with OpenAI API (~$10 cost)
- **JSON Export**: ~30 seconds

---

## Security & Privacy

### Local-First Architecture

- **No user accounts**: No authentication, no registration
- **No backend**: All data processing happens in browser
- **No tracking**: No analytics, no telemetry
- **No server calls**: Works offline after first load
- **Data ownership**: User owns their progress data in IndexedDB

### Data Storage

- **User progress**: IndexedDB (can be exported/cleared by user)
- **Sentence corpus**: Static JSON files (public)
- **Character data**: Static JSON files (public)

---

## Future Technical Considerations

### Phase 2 - Character-Aware Sampling (Planned)

*Not currently implemented - documented for future reference*

**Problem**: With 80,000 sentences and random sampling of 300 candidates, probability of selecting a specific sentence is only 0.375%. Even if a sentence contains characters due for review, it's unlikely to be sampled.

**Proposed Solution**: Multi-level sampling strategy
1. Get priority characters (50-100 chars needing review/practice)
2. Find sentences containing those characters
3. Biased sampling: 70% from review pool, 30% from new material
4. Score and select as usual

**Trade-offs**: More complex, potential performance impact, risk of over-fitting

**Decision**: Start with Phase 1 parameter tuning. Only implement if insufficient.

