# Hanzi Flow - Project Brief

## Vision
Build the most efficient system for learning to read and type Chinese through adaptive, sentence-level interaction. Instead of flashcards, the app functions as a self-adjusting reading environment that teaches recognition, recall, and real-world typing fluency in one loop.

## Problem Statement
Existing tools like Anki or Pleco isolate words from sentences and rely on manual deck management. Learners either memorize disconnected vocabulary or struggle with native text that's too difficult. No app unifies reading comprehension, pinyin typing, and spaced repetition around real usage data.

## Core Concept
A frictionless, data-driven learning flow: the learner reads authentic sentences at just the right difficulty, types what they see using pinyin, and the system continuously adapts to maintain a 90–95% comprehension level. No deck creation, no guessing what to study next—just flow-state learning.

---

## Current Technical Stack

### Backend/Data Pipeline
- **Language**: Python 3.9
- **Libraries**: jieba (word segmentation), pypinyin (pinyin conversion), csv, matplotlib
- **Data Sources**:
  - Unicode Unihan database (character readings, variants, radicals)
  - CC-CEDICT (Chinese-English dictionary)
  - Tatoeba corpus (CMN - Mandarin Chinese sentences)
  - OpenCC (simplified/traditional mappings)

### Frontend
- **Framework**: Next.js 15.5.6 (App Router)
- **UI Library**: React 19.2.0
- **Language**: TypeScript 5.9.3
- **Styling**: Tailwind CSS 4.1.14
- **Architecture**: No src/ directory, uses `/app` router pattern

### Data Format
- **Processing**: CSV format (20,992 characters, 79,704 sentences)
- **Frontend Consumption**: JSON format (currently 1,000 sentences)
- **Storage**: File-based (no database yet)

---

## Project Structure

```
/hanzi-flow/
├── data/                          # Processed datasets
│   ├── chinese_characters.csv     # 20,992 characters with pinyin, glosses, variants
│   ├── sources/                   # Raw data files (Unihan, CEDICT, etc.)
│   ├── sentences/                 # Sentence datasets at various processing stages
│   └── build_artifacts/           # Intermediate build outputs
│
├── scripts/
│   └── character_set/             # 4-step character dataset build pipeline
│       ├── build_step1_base.py           # Generate base character set (U+4E00-U+9FFF)
│       ├── build_step2_pinyin.py         # Add pinyin from Unihan
│       ├── build_step3_cedict.py         # Add glosses and example words
│       ├── build_step4_variants.py       # Add script types and variants
│       ├── classify_sentences.py         # Classify sentences by script type
│       ├── add_pinyin_to_sentences.py    # Add sentence-level pinyin
│       ├── add_character_pinyin_mapping.py  # Context-aware char pinyin
│       └── convert_sentences_to_json.py  # Export for frontend
│
├── hanzi-flow-app/                # Next.js web application
│   ├── app/
│   │   ├── page.tsx               # Landing page
│   │   ├── practice/
│   │   │   └── page.tsx           # Main practice interface
│   │   └── layout.tsx             # Root layout
│   ├── lib/
│   │   ├── types.ts               # TypeScript interfaces
│   │   ├── scoring.ts             # Pinyin validation and scoring logic
│   │   └── sentences.ts           # Data loading utilities
│   ├── public/
│   │   └── data/
│   │       └── sentences.json     # 1,000 practice sentences
│   └── package.json
│
└── PROJECT_BRIEF.md               # This file
```

---

## Data Models

### Character Dataset Schema
**File**: `data/chinese_characters.csv` (20,992 characters)

```csv
id,char,codepoint,pinyins,script_type,variants,gloss_en,examples
1,一,U+4E00,yī(32747),neutral,,one,一一|一一對應|一一对应
2,丁,U+4E01,dīng(16),neutral,,surname Ding,一丁不識|一丁不识|一丁點
```

**Fields**:
- `id`: Sequential integer (1-20,992)
- `char`: Chinese character
- `codepoint`: Unicode identifier (e.g., U+4E00)
- `pinyins`: Pipe-separated readings with optional frequency: `lè(283)|yuè(54)` or single `yī`
- `script_type`: `simplified`, `traditional`, `neutral`, or `ambiguous`
- `variants`: Pipe-separated variant characters (simplified/traditional pairs)
- `gloss_en`: English definition from CC-CEDICT
- `examples`: Pipe-separated example words containing this character

**Coverage Statistics**:
- Pinyin: 99.7% (20,924/20,992)
- Polyphonic characters: 22.8% (4,795)
- English glosses: 67.4% (14,152)
- Example words: 41.1% (8,618)
- Variant mappings: 34.6% (7,254)

**Script Type Distribution**:
- Simplified: 12.5% (2,618)
- Traditional: 22.1% (4,634)
- Neutral: 65.4% (13,738)
- Ambiguous: 0.0% (2)

### Sentence Data Schema
**File**: `hanzi-flow-app/public/data/sentences.json` (1,000 sentences from 79,704 total)

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

---

## What's Built (MVP Status)

### Data Pipeline ✓
- [x] Complete character dataset (20,992 CJK Unified Ideographs)
- [x] Pinyin readings with frequency data from Unihan
- [x] English glosses and example words from CC-CEDICT
- [x] Simplified/Traditional variant mappings
- [x] Script type classification
- [x] Sentence corpus (79,704 from Tatoeba)
- [x] Context-aware character-level pinyin mapping (jieba + pypinyin)
- [x] JSON export for frontend consumption

### Frontend ✓
- [x] Landing page with value props and "How It Works"
- [x] Interactive practice interface
- [x] Character-by-character sentence display with audio
- [x] Pinyin input with tone number validation (supports v/ü substitution)
- [x] Real-time feedback (✓/✗ indicators)
- [x] Sentence-level scoring with English translations
- [x] Progress tracking across sentences
- [x] Result review after each sentence
- [x] Responsive design with dark mode support
- [x] Script preference system (simplified/traditional/mixed)
- [x] HSK level preference system (cumulative filtering: 1, 1-2, 1-3, 1-4, 1-5, 1-6, 1-9)
- [x] Settings page with database reset
- [x] Navigation component across all pages
- [x] First-run modal for script and HSK level selection

### Core Components
- **Practice Page** (`app/practice/page.tsx`): Main learning interface
  - Highlights current character
  - Accepts pinyin input (tone3 format: wo3, ni3, ta1)
  - Validates against context-aware pinyin
  - Shows results and advances to next character/sentence
  - Displays English translations after completion

- **Scoring System** (`lib/scoring.ts`):
  - Normalizes user input (lowercase, trim, v→ü conversion)
  - Compares against expected pinyin
  - Calculates accuracy percentage

- **Data Loading** (`lib/sentences.ts`, `lib/characters.ts`):
  - In-memory caching for fast navigation
  - Preloading on homepage for instant practice start
  - Character ID mapping for mastery tracking

---

### Advanced Features (Recently Completed) ✓

#### Mastery Tracking System
- [x] **IndexedDB Persistence** (`lib/db.ts`)
  - Word-level mastery tracking (Dexie.js wrapper)
  - Sentence-level progress tracking
  - Queue management for NSS algorithm
  - ~Database reset utility

- [x] **EWMA-based Mastery** (`lib/mastery.ts`)
  - Exponentially Weighted Moving Average for word mastery (α=0.15)
  - Sentence-level pass rate tracking (α=0.2)
  - SRS scheduling with next_review_ts
  - Cumulative scoring and attempt tracking

#### Next Sentence Selection (NSS) Algorithm
- [x] **Adaptive Difficulty** (`lib/sentence-selection.ts`)
  - Dynamic k-band (2-5 unknowns normal, 1-3 under backlog)
  - Cold start protection with dynamic k_cap (12→10→8→none based on avg mastery)
  - Overdue word boosting (1.2x weight)
  - Sentence novelty scoring (time-based)
  - Pass penalty to avoid grinding

- [x] **Batch Generation & Prefetching**
  - Generates batches of 10 sentences
  - Prefetches next batch when 2 remain
  - 5-level fallback cascade for edge cases
  - Script-type filtering (simplified/traditional/mixed)
  - HSK level filtering (cumulative: "1-3" includes levels 1, 2, and 3)
  - Queue invalidation when preferences change

- [x] **Comprehensive Logging** (`lib/logger.ts`)
  - NSS algorithm debugging (development only)
  - Rejection tracking (no unknowns / k_cap violations)
  - Mastery distribution stats (every 10 batches)
  - Auto-save to log files (development only)

#### Environment Gating
- [x] **Development vs Production**
  - NSS logs gated to development only
  - Debug console.logs wrapped in NODE_ENV checks
  - File logging API (development only)
  - DevStats component (development only)
  - Clean production builds with minimal logging

---

## What's NOT Yet Built (Roadmap)

### Immediate Priority (Current Sprint)
- [ ] **User-Facing Stats Page**
  - Total characters practiced
  - Characters mastered (s ≥ threshold)
  - Unique sentences seen vs total attempts
  - Overall accuracy percentage
  - Mastery breakdown (learning/proficient/mastered buckets)
  - Progress bars showing X / Y characters in corpus

### High Priority (Post-MVP Launch)
- [x] **HSK Level Data Pipeline** ✓ COMPLETED
  - ✓ Integrated HSK 3.0 character lists (9 levels) - elkmovie/hsk30
  - ✓ Tagged sentences with HSK level (based on character composition)
  - ✓ User preference: filter practice by HSK level (cumulative ranges)
  - ✓ UI: First-run modal and settings page with character counts
  - ✓ NSS integration: Queue invalidation and filtering
  - **Impact**: Aligns with curriculum, huge value for learners

- [ ] **HSK Stats Integration**
  - Show progress by HSK level on stats page
  - Character mastery breakdown by HSK level
  - Visual progress indicators per level
  - **Effort**: 2-3 hours
  - **Impact**: Helps users track curriculum progress

- [ ] **Mobile PWA Optimization**
  - Make app installable on phones (manifest.json)
  - Offline support (service workers)
  - Better touch keyboard handling
  - Mobile-optimized layouts
  - **Effort**: 8-12 hours
  - **Impact**: Most language learning happens on mobile

### Medium Priority (Nice to Have)
- [ ] **Review Mode**
  - Practice mode: "Learn New" vs "Review"
  - Filter sentences by overdue words (past next_review_ts)
  - Filter by low mastery (s < 0.5)
  - Word-level review (isolated character practice, no sentences)
  - **Effort**: 6-8 hours
  - **Impact**: Addresses forgetting curve

- [ ] **Character Detail View**
  - Click character → show detailed info
  - Etymology, stroke order diagrams
  - Example compounds, usage notes
  - Requires external data (Unihan, HanziJS, Hanzi Writer)
  - **Effort**: 4-8 hours
  - **Impact**: Educational value for learners

- [ ] **Sentence-Level Audio**
  - Full sentence pronunciation (not just characters)
  - Requires TTS API (Google/Azure) or pre-recorded audio
  - **Effort**: Depends on audio source
  - **Impact**: Listening comprehension practice

### Lower Priority (Future)
- [ ] **Tone Error Analytics**
  - Track specific tone confusion (tone 2 vs tone 3)
  - Tone-specific practice drills
  - Optional tone-less practice mode

- [ ] **Custom Corpus Management**
  - Import custom sentence lists
  - Topic/domain filtering (news, literature, spoken)
  - Sentence difficulty ratings

- [ ] **Character Writing Practice**
  - Reverse mode: show pinyin, type character (requires Chinese IME)
  - Stroke order practice
  - Handwriting recognition (premium feature)

### Explicitly Decided Against (For Now)
- ❌ **Study Streaks / Session Tracking**
  - Feels forced/gamified
  - Adds complexity (what is a "session"?)
  - User prefers casual grinding

- ❌ **Session Summary Popups**
  - "You practiced 10 sentences!" feels clumsy
  - Prefer continuous flow over chunked sessions

- ❌ **User Accounts / Cloud Sync**
  - Local-first approach (IndexedDB)
  - Portable, no server costs
  - Privacy-friendly

---

## Current Design Work: Stats Page

### Production View (User-Facing)
**Goal**: Motivate users, show progress, avoid technical jargon

```
┌─────────────────────────────────────┐
│ Your Progress                        │
├─────────────────────────────────────┤
│                                      │
│  Total Characters Practiced: 232     │
│  Characters Mastered: 87             │
│  Sentences Practiced: 42             │
│  Total Attempts: 127                 │
│  Overall Accuracy: 73%               │
│                                      │
│  Mastery Breakdown:                  │
│  ████████░░  Learning (145 chars)    │
│  ████░░░░░░  Proficient (62 chars)   │
│  ██░░░░░░░░  Mastered (25 chars)     │
│                                      │
│  Progress: 232 / 1,847 (12.6%)       │
│  ████░░░░░░░░░░░░░░░░                │
└─────────────────────────────────────┘
```

**Thresholds** (subject to tuning):
- Learning: s < 0.6
- Proficient: 0.6 ≤ s < 0.8
- Mastered: s ≥ 0.8

**Open Questions**:
1. What s-value = "learned"? (0.7? 0.75? 0.8?)
2. Accuracy: word-level or sentence-level? (Leaning word-level)
3. Should "characters practiced" show total corpus size or just characters that appear in sentences?

### Development View (Superset)
Same as production, **plus**:
- Raw IndexedDB metrics (avg mastery, avg success, total attempts)
- NSS algorithm health indicators
- Database table viewers (characters, sentences)
- Reset database button

**Layout**: Production stats at top, developer stats below in collapsible sections

---

## Key Technical Decisions

### Why Context-Aware Pinyin?
Chinese characters are often polyphonic (多音字). The same character can have different pronunciations depending on context:
- 了: `le` (particle) vs `liao3` (to finish)
- 行: `xing2` (okay) vs `hang2` (row/line)
- 长: `zhang3` (to grow) vs `chang2` (long)

We use **jieba** for word segmentation, then **pypinyin** to generate context-appropriate pinyin. This ensures learners practice the correct pronunciation for each usage.

### Why Sentence-Based Learning?
- Provides context for vocabulary (vs. isolated flashcards)
- Mimics real reading scenarios
- Allows difficulty calibration (sentence-level character distribution)
- Enables typing practice in natural language flow
- Supports both recognition (reading) and recall (typing)

### Why Tone Numbers (TONE3 Format)?
- Easier to type than tone marks (wǒ → wo3)
- Standard input method for Chinese IME users
- Consistent with how learners type Chinese on keyboards
- Simpler validation logic
- Can optionally display tone marks in UI while accepting numbers as input

### Why IndexedDB (Not PostgreSQL)?
- **Local-first**: No server, no auth, instant start
- **Privacy**: All data stays on user's device
- **Portable**: Export/import via browser
- **Fast**: No network latency
- **Free**: No hosting costs for MVP
- **Trade-off**: No cross-device sync (acceptable for portfolio project)

### How Does NSS Work?
**Next Sentence Selection** adaptively picks sentences based on:

1. **Difficulty (k unknowns)**:
   - Target: 2-5 unknown characters per sentence (normal)
   - Tightens to 1-3 under review backlog (>80 due words)
   - Cold start cap: 12→10→8 unknowns based on avg mastery

2. **Scoring Formula**:
   ```
   score = base_gain + novelty - pass_penalty - k_penalty

   base_gain = Σ(1 - s) × 2.0 if overdue  [tuned: was 1.2]
   novelty = 0.05 × log(1 + hours_since_seen)
   pass_penalty = 0.1 × ewma_pass
   k_penalty = 0.35 × |k - k_band| if outside band  [tuned: was 0.2]
   ```

3. **Batch Generation**:
   - Sample 300 candidates from eligible pool  [tuned: was 200]
   - Score all, select top 10
   - Shuffle to mix difficulty
   - Prefetch next batch when 2 remain

4. **Fallback Cascade** (if <10 sentences scored):
   1. Relax k_band to [1, 6]
   2. Ignore cooldown (20 min)  [tuned: was 60 min]
   3. Lower θ_known to 0.65
   4. Drop ewma_skip filter
   5. Random selection (emergency)

**Why EWMA over Leitner/SM-2?**
- Simpler implementation (no interval calculation)
- Gradual adaptation (vs discrete boxes/intervals)
- Works naturally with sentence-level scoring
- Mastery can both increase AND decrease (realistic forgetting)

**Recent Tuning (Phase 1 - Same-Day Review Optimization)**:
- **SRS Timing**: Reduced initial stability from 1 day to 1 hour for same-day review
- **Growth Rate**: Slower stability growth (1.2x vs 1.4x) keeps words in review rotation longer
- **Review Boost**: Increased overdue_boost from 1.2 to 2.0 for stronger SRS signal
- **Difficulty**: Stronger k_penalty (0.35 vs 0.2) better enforces difficulty band
- **Repetition**: Reduced cooldown to 20 min for more same-day practice opportunities
- **Sampling**: Increased pool from 200 to 300 for better candidate selection

**Future Consideration (Phase 2 - Character-Aware Sampling)**:

*Not currently implemented - documented for future reference*

**Problem**: With 80,000 sentences in corpus and random sampling of 300 candidates, probability of selecting a specific sentence is only 0.375%. Even if a sentence was practiced 1 hour ago and contains characters due for review, it's unlikely to be sampled again.

**Proposed Solution**: Multi-level sampling strategy
1. **Get priority characters** (50-100 chars needing review/practice)
   - Sort by priority: `(1-s) × overdue_factor × recency_weight`
2. **Find sentences containing those characters**
   - Build review-focused candidate pool
3. **Biased sampling**:
   - 70% from review pool (contains due/struggling characters)
   - 30% from new material pool
   - Total: 300 candidates
4. **Score and select as usual**

**Trade-offs**:
- **Pros**: Direct targeting of characters needing attention, higher review probability
- **Cons**: More complex architecture, potential performance impact, risk of over-fitting to specific sentences
- **Decision**: Start with Phase 1 parameter tuning. Only implement if Phase 1 insufficient.

**Alternative Approaches Considered**:
- Cycle-based (instead of time-based) review scheduling
- Hybrid time + cycle approach
- Smaller "active corpus" rotation (5k-10k sentences)
- All deferred in favor of simpler parameter tuning

---

## Development Workflow

### Adding New Characters
1. Ensure character is in Unicode CJK Unified Ideographs range (U+4E00-U+9FFF)
2. Run `python3 scripts/character_set/build_step1_base.py` if regenerating from scratch
3. Subsequent steps automatically pull from Unihan and CEDICT data sources
4. Final output: `data/chinese_characters.csv`

### Adding New Sentences
1. Add sentences to `data/sentences/cmn_sentences.tsv` (tab-separated: ID, Chinese, English)
2. Run classification: `python3 scripts/character_set/classify_sentences.py`
3. Add sentence-level pinyin: `python3 scripts/character_set/add_pinyin_to_sentences.py`
4. Add character-level pinyin: `python3 scripts/character_set/add_character_pinyin_mapping.py`
5. Convert to JSON: `python3 scripts/character_set/convert_sentences_to_json.py`
6. Output: `hanzi-flow-app/public/data/sentences.json`

### Running the Frontend
```bash
cd hanzi-flow-app
npm install
npm run dev
```
Navigate to `http://localhost:3000`

### Data Pipeline Dependencies
```bash
python3 -m pip install jieba pypinyin
```

---

## Design Principles

1. **Efficiency over entertainment**: Optimize for learning speed, not gamification
2. **Flow state learning**: Maintain 90-95% comprehension to balance challenge and confidence
3. **Authentic materials**: Real sentences from corpora, not artificial examples
4. **Minimal manual curation**: System adapts automatically based on user progress
5. **Functional fluency**: Recognition + recall + typing in one integrated loop
6. **Data-driven decisions**: Analytics inform study priorities, not guesswork

---

## Common Questions

**Q: Why both simplified and traditional?**
A: Learners have different goals. Mainland readers need simplified, Taiwan/HK readers need traditional. The neutral character subset (65.4%) works for both. Users can filter by script type.

**Q: How is difficulty calculated?**
A: Currently not implemented. Planned approach: character frequency (Jun Da corpus) + user's known character set. Sentences with 90-95% known characters are "ideal difficulty."

**Q: Why Tatoeba and not other corpora?**
A: Tatoeba provides free, sentence-aligned Chinese-English pairs. Future: integrate news corpora (scraped articles), literature (public domain), and spoken transcripts.

**Q: What about handwriting practice?**
A: Out of scope for MVP. Focus is on recognition and typing (pinyin input method), which covers 90% of digital Chinese usage. Handwriting could be a future premium feature.

**Q: How does this compare to Anki/Pleco/Skritter?**
- **Anki**: More flexible for arbitrary memorization, but requires manual deck curation. We automate sentence selection.
- **Pleco**: Excellent dictionary and reader, but passive. We force active recall via typing.
- **Skritter**: Handwriting-focused. We focus on typing (more practical for digital natives).
- **Unique**: We combine adaptive selection + sentence context + typing practice + SRS in one loop.

---

## Success Metrics (Future)

- **Learning efficiency**: Characters mastered per hour of study
- **Retention rate**: Percentage of characters retained after 30 days
- **Reading speed**: Characters per minute in comprehension tests
- **Typing fluency**: Pinyin input speed (characters per minute)
- **Engagement**: Daily active users, streak length, session duration
- **Coverage**: Percentage of HSK levels completed, total unique characters seen

---

## Getting Started (For New Contributors/Agents)

1. **Explore the data**: Check `data/chinese_characters.csv` and `data/sentences/cmn_sentences_with_char_pinyin.csv`
2. **Run the app**: `cd hanzi-flow-app && npm install && npm run dev`
3. **Test the practice flow**: Visit `/practice` and try typing pinyin
4. **Read the code**: Start with `app/practice/page.tsx` (main UI logic)
5. **Check recent commits**: `git log --oneline -10` to see latest changes
6. **Review this doc**: Understand what's built vs what's planned

---

## Contact & Resources

- **Repository**: (Add GitHub URL when available)
- **Tech Docs**:
  - Next.js: https://nextjs.org/docs
  - pypinyin: https://github.com/mozillazg/python-pinyin
  - jieba: https://github.com/fxsjy/jieba
  - Unicode Unihan: https://unicode.org/charts/unihan.html
  - CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict
  - Tatoeba: https://tatoeba.org/en/downloads
- **HSK Data Sources**:
  - elkmovie/hsk30: https://github.com/elkmovie/hsk30
    - Official HSK 3.0 character lists (9 levels, 3,000 total characters)
    - Extracted from official PDF and OCR'ed using Pleco OCR
    - Used as source of truth for sentence HSK classification

---

**Last Updated**: 2025-10-21
**Project Status**: Advanced MVP - NSS algorithm complete, mastery tracking live, HSK filtering live, stats page in progress
**Next Milestone**: User-facing stats page + production deployment
