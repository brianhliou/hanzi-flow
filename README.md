# Hanzi Flow

**Master Chinese Reading with HSK 3.0-Aligned Adaptive Practice**

A privacy-first, local-first web application for learning Chinese characters through contextual sentence practice. Uses an adaptive algorithm to select sentences based on your mastery level, with support for both Simplified and Traditional Chinese.

🔗 **[Live Demo](https://hanziflow.vercel.app)**

![Hanzi Flow Practice Interface](.github/screenshot.png)
*Character-by-character sentence practice with real-time feedback*

## Features

### 🎯 **HSK 3.0 Curriculum Aligned**
- Complete coverage of HSK levels 1-9 (3,000 official characters)
- ~1,000 additional "Beyond HSK" characters for advanced learners
- 79,000+ sentences from real-world usage (Tatoeba corpus)

### 🧠 **Adaptive Learning (NSS Algorithm)**
- Next Sentence Selection (NSS) algorithm picks optimal sentences
- Balances new character introduction with spaced repetition
- Adjusts difficulty based on your real-time performance
- Queue-based prefetching for seamless practice sessions

### 🔒 **100% Private & Local-First**
- All data stored in browser (IndexedDB)
- No backend, no tracking, no accounts
- Works offline after first load
- Your progress never leaves your device

### 🌐 **Flexible Script Support**
- Simplified Chinese (简体)
- Traditional Chinese (繁體)
- Mixed mode (both scripts)
- Automatic script classification for all sentences

### 📊 **Progress Tracking**
- Character-level mastery scores (0-1 scale)
- Sentence-level success rates
- Visual stats dashboard
- Exponentially weighted moving averages for recency bias

### 🔊 **Audio Pronunciation**
- Native speaker audio for all pinyin syllables
- Plays automatically on incorrect answers (optional)
- Supports all tone variations including ü/v

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/brianhliou/hanzi-flow.git
cd hanzi-flow

# Install dependencies
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

## Data Pipeline

The project includes a complete data processing pipeline with **dual-format pinyin storage** (tone3 + display) to eliminate format conversions:

```
data/sources/          # Raw data from Tatoeba, CC-CEDICT, HSK lists
    ↓
scripts/               # Python processing scripts (character_set, sentences, audio)
    ↓
data/                  # Intermediate CSV files
    ↓
app/public/data/       # Production JSON for the app
```

### Regenerating Data

**Prerequisites:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install pypinyin jieba  # Required for both pipelines
```

**Character Set Pipeline** (6 steps):
```bash
cd scripts/character_set

# Run pipeline in order (steps 1-6)
python3 build_step1_base.py              # Generate 20,992 CJK characters
python3 build_step2_pinyin_pypinyin.py   # Add dual-format pinyin (pypinyin)
python3 build_step3_cedict.py            # Add glosses and examples
python3 build_step4_variants.py          # Add script types and variants
python3 build_step5_hsk.py               # Add HSK levels (downloads from GitHub)
python3 build_step6_freq.py              # Add character & pinyin frequencies

# Output: data/character_set/step6_with_freq.csv (final dataset)
```

**Sentence Pipeline** (4-6 steps):
```bash
cd scripts/sentences

# Core pipeline (steps 1-4, no API required)
python3 build_step1_classify.py          # Classify script type
python3 build_step2_pinyin.py            # Add character-level pinyin
python3 build_step3_translate.py         # Add English translations (requires OpenAI API)
python3 build_step4_hsk.py               # Classify sentence HSK levels

# Optional: Pinyin refinement (requires OpenAI API, ~$10, 4-5hrs)
# See scripts/sentences/step5/README.md for detailed workflow
python3 build_step5_refine_pinyin.py     # Apply verified pinyin improvements

# Export to production JSON
python3 build_step6_export_json.py       # Generate app/public/data/sentences/*.json

# Output: data/sentences/step4_with_hsk.csv (or step5_pinyin_refined.csv)
```

**See also:**
- `scripts/character_set/README.md` - Complete character pipeline documentation
- `scripts/sentences/README.md` - Complete sentence pipeline documentation
- `docs/migrations/` - Data pipeline migration history

## Tech Stack

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- Dexie.js (IndexedDB wrapper)

**Data Processing:**
- Python 3.9+
- pandas, matplotlib (for analysis)
- CSV processing and JSON generation

**Deployment:**
- Vercel (recommended)
- Works on any static host

## Project Structure

```
hanzi-flow/
├── app/                     # Next.js application
│   ├── app/                # App router pages
│   ├── components/         # React components
│   ├── lib/               # Core logic (NSS, mastery, scoring)
│   └── public/data/       # Production data files (JSON, audio)
├── scripts/               # Data processing pipeline
│   ├── character_set/    # Character set processing (6 steps)
│   ├── sentences/        # Sentence processing & HSK classification (4-6 steps)
│   ├── audio/            # Audio generation scripts
│   └── utils/            # Shared utilities (pinyin conversion)
├── data/                  # Intermediate data files
│   ├── sources/          # Raw data sources (Tatoeba, CC-CEDICT, Unihan)
│   ├── character_set/    # Character pipeline outputs (step1-6)
│   ├── sentences/        # Sentence pipeline outputs (step0-6)
│   └── audio/            # Audio enumeration and metadata
├── docs/                  # Documentation
│   ├── PROJECT_BRIEF.md  # Detailed project documentation
│   ├── KNOWN_ISSUES.md   # Current limitations and planned improvements
│   ├── LESSONS_LEARNED.md # Development insights and technical decisions
│   └── migrations/       # Data pipeline migration history
└── venv/                  # Python virtual environment
```

## Data Sources

This project builds upon excellent open-source datasets:

- **Sentences**: [Tatoeba](https://tatoeba.org/) (CC BY 2.0 FR)
- **Dictionary**: [CC-CEDICT](https://cc-cedict.org/) (CC BY-SA 4.0)
- **HSK Classification**: [elkmovie/hsk30](https://github.com/elkmovie/hsk30) (MIT)
- **Audio**: Generated using AWS Polly (Zhiyu voice)

All processed data is included in this repository under compatible licenses.

## How It Works

### Next Sentence Selection (NSS)

The adaptive algorithm works in batches:

1. **Filter** eligible sentences (script type, HSK level, cooldown)
2. **Sample** 300 random candidates from eligible pool
3. **Score** each candidate based on:
   - Base gain: Characters due for review (SRS)
   - Novelty bonus: Time since sentence last seen
   - Pass penalty: Avoid over-practicing mastered sentences
   - k-penalty: Prefer target difficulty band (2-5 unknown chars)
4. **Select** top 8 sentences, shuffle to mix difficulty
5. **Queue** for practice, prefetch next batch in background

### Mastery Tracking

Each character tracks:
- **Mastery score (s)**: Exponential smoothing of success rate
- **Stability**: Spaced repetition interval (days)
- **EWMA success**: Recency-weighted performance
- **Streak**: Consecutive correct/wrong attempts

## Configuration

Key parameters in `app/lib/selection-config.ts`:

```typescript
batch_size: 8              // Sentences per batch
prefetch_threshold: 2      // Start prefetch when 2 remain
pool_sample_size: 300      // Candidate pool size
k_min: 2, k_max: 5        // Target difficulty (unknown chars)
θ_known: 0.7              // Mastery threshold for "known"
```

## Development

### Dev-Only Features

When running in development mode (`NODE_ENV=development`):
- Skip button to cycle through sentences without scoring
- Queue size display
- Sentence ID display in header
- Extended NSS logging

### Adding New Data

See pipeline documentation for detailed instructions:
- **Characters**: `scripts/character_set/README.md` - Full 6-step pipeline
- **Sentences**: `scripts/sentences/README.md` - Full 4-6 step pipeline with optional refinement
- **Audio**: `scripts/audio/README.md` - Syllable enumeration and TTS generation
- **Migrations**: `docs/migrations/` - History of major data pipeline changes

## Documentation

- **[docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)** - Detailed project overview and technical design
- **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)** - Current limitations and planned improvements
- **[docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md)** - Development insights and technical decisions
- **[docs/migrations/](docs/migrations/)** - Data pipeline migration history

## Contributing

This is primarily a personal learning project, but bug reports and suggestions are welcome! Please open an issue before submitting major PRs.

### Areas for Contribution
- Additional sentence sources (different domains, difficulty levels)
- Support for other Chinese variants (Cantonese, Classical Chinese)
- Mobile app version (React Native)
- Browser extension for popup practice
- Alternative SRS algorithms

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Tatoeba Project](https://tatoeba.org/) for sentence data
- [MDBG](https://www.mdbg.net/) for CC-CEDICT dictionary
- [elkmovie](https://github.com/elkmovie) for HSK 3.0 character lists
- All contributors to open Chinese language learning resources

---

**Made with ❤️ by [Brian Liou](https://brianhliou.github.io/)**

*Local-first, privacy-first, learning-first.*
