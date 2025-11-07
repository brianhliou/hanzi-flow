# Developer Guide

Complete guide for setting up and working with Hanzi Flow.

---

## Quick Start

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for data pipeline)
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/brianhliou/hanzi-flow.git
cd hanzi-flow

# Install frontend dependencies
cd app
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to start practicing!

### Production Build

```bash
cd app
npm run build
npm start
```

---

## Development Workflows

### Running the Frontend

```bash
cd app
npm run dev       # Development mode (with dev-only features)
npm run build     # Production build
npm start         # Run production build locally
```

**Dev-Only Features** (when `NODE_ENV=development`):
- Skip button to cycle through sentences without scoring
- Queue size display
- Sentence ID display in header
- Extended NSS logging
- DevStats component

### Working with Data Pipelines

Both pipelines require Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install pypinyin jieba  # Required for both pipelines
```

### Rebuilding Character Dataset

**Prerequisites**: Ensure source data exists in `data/sources/` (CC-CEDICT, Unihan, HSK lists)

**Location**: `scripts/character_set/`

**Steps** (run in order):

```bash
cd scripts/character_set

# Step 1: Generate base character set (20,992 CJK characters)
python3 build_step1_base.py

# Step 2: Add dual-format pinyin via pypinyin
python3 build_step2_pinyin_pypinyin.py

# Step 3: Add English glosses from CC-CEDICT
python3 build_step3_cedict.py

# Step 4: Add script types and variants
python3 build_step4_variants.py

# Step 5: Add HSK levels (downloads from GitHub)
python3 build_step5_hsk.py

# Step 6: Add character & pinyin frequencies
python3 build_step6_freq.py
```

**Output**: `data/character_set/step6_with_freq.csv` (FINAL dataset)

**Copy to production** (if needed):
```bash
cp data/character_set/step6_with_freq.csv app/public/data/character_set/
```

**Documentation**: See [scripts/character_set/README.md](../scripts/character_set/README.md) for complete details

**Time**: ~30 seconds for full rebuild (all 6 steps)

### Rebuilding Sentence Dataset

**Prerequisites**:
- Tatoeba source: `data/sentences/step0_raw.tsv`
- OpenAI API key (for steps 3 and 5): `export OPENAI_API_KEY=your_key_here`

**Location**: `scripts/sentences/`

**Steps** (run in order):

```bash
cd scripts/sentences

# Step 1: Classify script type
python3 build_step1_classify.py

# Step 2: Add character-level pinyin
python3 build_step2_pinyin.py

# Step 3: Add English translations (requires OpenAI API, ~$10, 4-5hrs)
python3 build_step3_translate.py

# Step 4: Classify sentence HSK levels
python3 build_step4_hsk.py

# Step 5: [Optional] Apply pinyin refinements
# Requires prior OpenAI processing (see step5/README.md)
python3 build_step5_refine_pinyin.py

# Step 6: Export to production JSON
python3 build_step6_export_json.py
```

**Output**:
- CSV: `data/sentences/step5_pinyin_refined.csv` (or step4 if skipping step5)
- JSON: `app/public/data/sentences/sentences_with_translation.json` (production file)

**Documentation**:
- Pipeline overview: [scripts/sentences/README.md](../scripts/sentences/README.md)
- Step 5 refinement: [scripts/sentences/step5/README.md](../scripts/sentences/step5/README.md)

**Time**:
- Steps 1-2: ~5 minutes
- Step 3 (translation): 4-5 hours with OpenAI API
- Step 4: ~2 minutes
- Step 5 (refinement): 4-5 hours with OpenAI API (optional)
- Step 6: ~30 seconds

### Running Analysis Scripts

Both pipelines have analysis scripts in their `analysis/` subdirectories.

**Character analysis**:
```bash
cd scripts/character_set/analysis

# Build Pinyin Trie (1,307 unique syllables)
python3 build_pinyin_trie.py

# Visualize Trie structure
python3 visualize_trie.py

# Validate migration (dual-format consistency)
python3 validate_migration.py
```

**Sentence analysis**:
```bash
cd scripts/sentences/analysis

# Corpus statistics
python3 analyze_corpus_stats.py

# HSK distribution analysis
python3 analyze_hsk_coverage.py

# Script type distribution
python3 analyze_script_distribution.py

# Sentence length analysis (requires matplotlib)
python3 analyze_sentence_length.py
```

---

## Common Tasks

### Adding New Sentences

1. Add sentences to `data/sentences/step0_raw.tsv` (format: id, language, sentence)
2. Run sentence pipeline (steps 1-6)
3. Production JSON automatically updated in step 6

### Updating HSK Classifications

HSK data is downloaded automatically in step 5 of character pipeline. To force refresh:

```bash
cd scripts/character_set
rm -rf ../../data/sources/elkmovie_hsk30/
python3 build_step5_hsk.py  # Will re-download
```

### Regenerating Audio Files

See [scripts/audio/README.md](../scripts/audio/README.md) for audio generation workflow.

**Note**: Audio pipeline currently uses Unihan (migration to corpus-based planned).

### Resetting User Progress (Development)

From the app's Settings page, click "Reset Database" to clear all IndexedDB data (mastery, sentences, queue).

Or programmatically:
```javascript
// In browser console
await db.delete()
location.reload()
```

### Tuning NSS Algorithm

Edit `app/lib/selection-config.ts` to adjust parameters:

```typescript
export const NSS_CONFIG = {
  batch_size: 8,              // Sentences per batch
  prefetch_threshold: 2,      // Start prefetch when 2 remain
  pool_sample_size: 300,      // Candidate pool size
  k_min: 2, k_max: 5,        // Target difficulty range
  θ_known: 0.7,              // Mastery threshold for "known"
  cooldown_minutes: 20,       // Min time between same sentence
  overdue_boost: 2.0,        // Multiplier for overdue characters
  // ... see file for all parameters
}
```

Changes take effect immediately in development mode.

### Viewing NSS Logs (Development Only)

NSS algorithm logs are gated to development mode and saved to `app/logs/`.

To view logs:
```bash
cd app/logs
ls -lt  # List by most recent
tail -f nss_log_*.txt  # Follow latest log
```

---

## Project Structure

```
hanzi-flow/
├── app/                           # Next.js web application
│   ├── app/                      # App router pages
│   │   ├── page.tsx              # Landing page
│   │   ├── practice/             # Main practice interface
│   │   ├── stats/                # Progress statistics dashboard
│   │   └── settings/             # User preferences
│   ├── components/               # React components
│   │   ├── Navigation.tsx        # Shared navigation
│   │   ├── UserStats.tsx         # Stats visualization
│   │   └── DevStats.tsx          # Development-only stats
│   ├── lib/                      # Core logic
│   │   ├── sentence-selection.ts # NSS adaptive algorithm
│   │   ├── mastery.ts            # EWMA mastery tracking
│   │   ├── db.ts                 # IndexedDB persistence
│   │   ├── scoring.ts            # Pinyin validation
│   │   └── selection-config.ts   # NSS configuration
│   ├── public/data/              # Production data files
│   │   ├── sentences/            # JSON sentence data
│   │   ├── audio/                # Pinyin audio files
│   │   └── character_set/        # Character data
│   ├── package.json
│   └── tsconfig.json
│
├── scripts/                       # Data processing pipelines
│   ├── character_set/            # 6-step character pipeline
│   │   ├── build_step1_base.py
│   │   ├── build_step2_pinyin_pypinyin.py
│   │   ├── build_step3_cedict.py
│   │   ├── build_step4_variants.py
│   │   ├── build_step5_hsk.py
│   │   ├── build_step6_freq.py
│   │   ├── analysis/             # Pinyin Trie, validation
│   │   └── README.md
│   ├── sentences/                # 4-6 step sentence pipeline
│   │   ├── build_step1_classify.py
│   │   ├── build_step2_pinyin.py
│   │   ├── build_step3_translate.py
│   │   ├── build_step4_hsk.py
│   │   ├── build_step5_refine_pinyin.py
│   │   ├── build_step6_export_json.py
│   │   ├── step5/                # Pinyin refinement substeps
│   │   ├── analysis/             # Corpus statistics
│   │   └── README.md
│   ├── audio/                    # Audio generation
│   │   └── README.md
│   └── utils/                    # Shared utilities
│
├── data/                         # Intermediate data files
│   ├── character_set/            # Pipeline outputs (step1-6)
│   │   ├── step6_with_freq.csv   # FINAL character dataset
│   │   └── analysis/             # Pinyin Trie, distributions
│   ├── sentences/                # Pipeline outputs (step0-6)
│   │   ├── step5_pinyin_refined.csv  # FINAL sentence dataset
│   │   ├── step5/                # OpenAI refinement artifacts
│   │   └── analysis/             # HSK distribution, length analysis
│   └── sources/                  # Raw source data
│       ├── cedict_ts.u8          # CC-CEDICT dictionary
│       ├── Unihan_Variants.txt   # Character variants
│       └── elkmovie_hsk30/       # HSK 3.0 lists (auto-downloaded)
│
├── docs/                         # Documentation
│   ├── PROJECT_BRIEF.md          # Vision and current status
│   ├── TECHNICAL_OVERVIEW.md     # Architecture and algorithms
│   ├── DEVELOPER_GUIDE.md        # This file
│   ├── ROADMAP.md                # Feature roadmap
│   ├── KNOWN_ISSUES.md           # Current limitations
│   ├── LESSONS_LEARNED.md        # Technical insights
│   └── migrations/               # Pipeline migration history
│
├── README.md                     # User-facing documentation
└── venv/                         # Python virtual environment
```

---

## Dependencies

### Frontend Dependencies (package.json)

**Core**:
- next: 15.5.6
- react: 19.2.0
- typescript: 5.9.3

**UI**:
- tailwindcss: 4.1.14
- @tailwindcss/postcss: 4.0.0

**Data**:
- dexie: 4.0.10 (IndexedDB wrapper)

**Development**:
- @types/node, @types/react
- eslint, typescript-eslint

### Python Dependencies (Data Pipeline)

**Required**:
- pypinyin: Pinyin conversion
- jieba: Chinese word segmentation

**Optional** (for analysis scripts):
- pandas: Data analysis
- matplotlib: Visualization
- openai: API client (only for steps 3 & 5)

Install:
```bash
pip install pypinyin jieba
pip install pandas matplotlib  # Optional
pip install openai  # Only if running translation/refinement
```

---

## Testing

### Manual Testing Checklist

**Practice Flow**:
- [ ] Load practice page
- [ ] Complete a sentence (all characters correct)
- [ ] Make intentional mistakes (check feedback)
- [ ] Navigate to next sentence
- [ ] Check queue prefetching (no wait time)

**Settings**:
- [ ] Change script preference (simplified/traditional/mixed)
- [ ] Change HSK level filter
- [ ] Reset database (confirm data cleared)

**Stats Page**:
- [ ] View progress statistics
- [ ] Check mastery breakdown visualization
- [ ] Verify character counts match practice history

**Data Pipeline**:
- [ ] Run character pipeline (all 6 steps)
- [ ] Verify CSV format and row counts
- [ ] Run sentence pipeline (steps 1-4)
- [ ] Verify JSON export

### Automated Testing

Currently no automated tests. Future consideration: Unit tests for NSS algorithm, mastery calculations.

---

## Debugging

### NSS Algorithm Issues

**Enable logging** (development mode only):
1. Logs automatically saved to `app/logs/`
2. Check `nss_log_*.txt` for:
   - Batch generation details
   - Sentence scoring breakdown
   - Rejection reasons (no unknowns / k_cap violations)
   - Mastery distribution stats (every 10 batches)

**Common issues**:
- **No sentences available**: Check HSK level filter, script preference
- **Queue empty**: Check browser console for errors
- **Same sentences repeating**: Adjust cooldown in selection-config.ts

### Mastery Tracking Issues

**Inspect IndexedDB** (browser DevTools):
1. Open DevTools → Application → IndexedDB → hanzi-flow-db
2. Check tables:
   - `characterMastery`: Character-level progress
   - `sentenceProgress`: Sentence-level pass rates
   - `queue`: Current practice queue

**Reset if corrupted**:
```javascript
// Browser console
await db.delete()
location.reload()
```

### Data Pipeline Issues

**Character pipeline**:
- Missing pypinyin: `pip install pypinyin`
- CEDICT not found: Check `data/sources/cedict_ts.u8` exists
- HSK download fails: Check internet connection

**Sentence pipeline**:
- Missing jieba: `pip install jieba`
- OpenAI API errors: Check API key, rate limits, balance
- Step 5 refinement fails: Ensure step5 substeps completed first (see step5/README.md)

---

## Performance Optimization

### Frontend

**Data loading**:
- Sentences loaded into memory on app start (~15MB)
- Character data loaded on demand (~2MB)
- Consider lazy loading if corpus grows significantly

**NSS Algorithm**:
- Sampling 300 from 80k sentences: <50ms
- Scoring 300 candidates: <10ms
- Queue prefetching: Background, non-blocking

### Data Pipeline

**Character pipeline**:
- Already optimized (~30 seconds for full rebuild)
- Frequency counting is the bottleneck (step 6)

**Sentence pipeline**:
- OpenAI API calls dominate (steps 3 & 5)
- Batch processing implemented (10 sentences per call)
- Checkpointing allows resume from interruption

---

## Deployment

### Vercel (Recommended)

1. Connect GitHub repository to Vercel
2. Configure build settings:
   - Framework: Next.js
   - Build command: `cd app && npm run build`
   - Output directory: `app/.next`
3. Deploy

**Environment variables**: None required (no backend)

### Static Hosting

The app can be deployed to any static host:

```bash
cd app
npm run build
npm run export  # If using static export
```

Upload `app/out/` or `app/.next/` to host.

---

## Contributing

### Areas for Contribution

- Additional sentence sources (different domains, difficulty levels)
- Support for other Chinese variants (Cantonese, Classical Chinese)
- Mobile app version (React Native)
- Browser extension for popup practice
- Alternative SRS algorithms
- Automated testing suite

### Guidelines

1. Open an issue before starting major work
2. Follow existing code style (TypeScript, ESLint)
3. Test with multiple HSK levels and script types
4. Update documentation if changing architecture
5. Add entry to LESSONS_LEARNED.md for notable insights

---

## FAQ

### How do I add a new data source?

1. Place source file in `data/sources/`
2. Create new pipeline step or modify existing step
3. Document in appropriate README.md
4. Update TECHNICAL_OVERVIEW.md with schema changes

### Can I use a different TTS provider for audio?

Yes. Audio generation is separate from main pipeline. See [scripts/audio/README.md](../scripts/audio/README.md).

### How do I change the mastery calculation?

Edit `app/lib/mastery.ts` - adjust EWMA alpha, stability growth rate, or scoring formula.

### Can I run this with a backend database?

Yes, but requires refactoring. Currently optimized for local-first architecture. Would need:
1. API endpoints for sentence selection
2. User authentication
3. Server-side NSS calculation
4. Database for user progress (PostgreSQL/MongoDB)

### Why is step 3 (translation) so expensive?

OpenAI API costs ~$0.0001 per sentence (~80k sentences = ~$10). Alternative: Use existing translations from Tatoeba (many sentences have multiple translations).

### How do I debug NSS algorithm behavior?

1. Enable development mode: `npm run dev`
2. Check `app/logs/nss_log_*.txt` for detailed scoring
3. Use DevStats component (shows queue size, current sentence ID)
4. Adjust parameters in `app/lib/selection-config.ts`

---

## Getting Help

- **Documentation**: Check the docs/ directory for relevant guides
- **GitHub Issues**: Open an issue for bugs or questions
- **Debugging**: See the "Debugging" section above for common issues

