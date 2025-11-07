# Hanzi Flow - Project Brief

**Master Chinese Reading with HSK 3.0-Aligned Adaptive Practice**

A privacy-first, local-first web application for learning Chinese characters through contextual sentence practice. Uses an adaptive algorithm to select sentences based on your mastery level, with support for both Simplified and Traditional Chinese.

🔗 **[Live Demo](https://hanziflow.vercel.app)**

---

## Vision

Build the most efficient system for learning to read and type Chinese through adaptive, sentence-level interaction. Instead of flashcards, the app functions as a self-adjusting reading environment that teaches recognition, recall, and real-world typing fluency in one loop.

### Problem Statement

Existing tools like Anki or Pleco isolate words from sentences and rely on manual deck management. Learners either memorize disconnected vocabulary or struggle with native text that's too difficult. No app unifies reading comprehension, pinyin typing, and spaced repetition around real usage data.

### Core Concept

A frictionless, data-driven learning flow: the learner reads authentic sentences at just the right difficulty, types what they see using pinyin, and the system continuously adapts to maintain a 90–95% comprehension level. No deck creation, no guessing what to study next—just flow-state learning.

---

## Current Status

**Project Status**: Production-ready

**Last Updated**: 2025-11-06

**Next Milestone**: Mobile PWA optimization + deployment to production

### What's Built

#### Core Features ✓
- **Adaptive Learning**: NSS (Next Sentence Selection) algorithm picks optimal sentences
- **Mastery Tracking**: EWMA-based scoring with spaced repetition scheduling
- **HSK 3.0 Aligned**: Complete coverage of HSK levels 1-9 (3,000 official characters)
- **Rich Dataset**: 79,000+ sentences from real-world usage (Tatoeba corpus)
- **Privacy-First**: 100% local-first, all data in browser (IndexedDB)
- **Script Support**: Simplified, Traditional, or Mixed mode
- **Progress Tracking**: Visual stats dashboard with mastery breakdown
- **Audio Pronunciation**: Native speaker audio for all pinyin syllables

#### Data Pipeline ✓
- **Character Dataset**: 20,992 CJK characters with dual-format pinyin
- **100% Pinyin Coverage**: pypinyin-only approach with frequency tracking
- **Context-Aware Pinyin**: 2,870 AI-verified improvements for polyphonic characters
- **HSK Classification**: Sentence-level and character-level HSK tagging
- **English Translations**: OpenAI-generated translations for all sentences
- **Production-Ready**: Complete 6-step character + 6-step sentence pipeline

**Recent highlights:** Pinyin format migration, context-aware refinement, stats dashboard, HSK 3.0 integration (see ROADMAP.md for details)

---

## Tech Stack at a Glance

**Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind CSS + IndexedDB (Dexie.js)

**Data Pipeline**: Python 3.9+ (pypinyin, jieba, pandas)

**Data Sources**: Tatoeba (sentences), CC-CEDICT (dictionary), elkmovie/hsk30 (HSK lists)

**AI Enhancement**: OpenAI GPT-4o-mini (translations, pinyin refinement)

**Deployment**: Vercel (static hosting)

---

## Project Structure

```
hanzi-flow/
├── app/                # Next.js application (pages, components, core logic)
├── scripts/            # Data pipelines (character_set, sentences, audio)
├── data/               # Intermediate pipeline outputs + raw sources
└── docs/               # All documentation
```

See DEVELOPER_GUIDE.md for complete structure details.

---

## Quick Links

### For Users
- **[README.md](../README.md)**: User-facing documentation, installation, features
- **[Live Demo](https://hanziflow.vercel.app)**: Try it now

### For Developers
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)**: Setup, workflows, common tasks
- **[TECHNICAL_OVERVIEW.md](./TECHNICAL_OVERVIEW.md)**: Architecture, NSS algorithm, data models
- **[ROADMAP.md](./ROADMAP.md)**: Feature roadmap, priorities, completed milestones

### For Contributors
- **[ROADMAP.md](./ROADMAP.md)**: See "Contribution Ideas" section
- **[KNOWN_ISSUES.md](./KNOWN_ISSUES.md)**: Known bugs and limitations
- **[LESSONS_LEARNED.md](./LESSONS_LEARNED.md)**: Technical insights from development

### For Data Pipeline
- **[scripts/character_set/README.md](../scripts/character_set/README.md)**: Character pipeline docs
- **[scripts/sentences/README.md](../scripts/sentences/README.md)**: Sentence pipeline docs
- **[docs/migrations/](./migrations/)**: Pipeline migration history

---

## Frequently Asked Questions

### Why local-first?
Privacy, instant start, works offline, no server costs, user owns their data. Trade-off: No cross-device sync.

### Why sentence-based learning?
Provides context, mimics real reading, allows difficulty calibration, enables typing practice in natural flow. Better than isolated flashcards.

### How does this compare to Anki/Pleco/Skritter?
We automate sentence selection (vs Anki's manual decks), force active recall via typing (vs Pleco's passive reading), and focus on typing over handwriting (vs Skritter). Unique combination of adaptive selection + sentence context + SRS in one loop.

See TECHNICAL_OVERVIEW.md for architecture details and design decisions.

---

## Data Sources & Licensing

This project builds upon excellent open-source datasets:

- **Sentences**: [Tatoeba](https://tatoeba.org/) (CC BY 2.0 FR) - 79,704 Chinese-English sentence pairs
- **Dictionary**: [CC-CEDICT](https://cc-cedict.org/) (CC BY-SA 4.0) - Chinese-English dictionary
- **HSK Classification**: [elkmovie/hsk30](https://github.com/elkmovie/hsk30) (MIT) - Official HSK 3.0 character lists
- **Audio**: Generated using AWS Polly (Zhiyu voice)

All processed data is included in this repository under compatible licenses.

---

## Contributing

Hanzi Flow is an open-source Chinese learning platform built with extensibility and community collaboration in mind. Contributions, feature requests, and bug reports are welcome!

**Areas for contribution**:
- Additional sentence sources (different domains, difficulty levels)
- Mobile PWA optimization
- Alternative SRS algorithms
- Browser extension version

See [ROADMAP.md](./ROADMAP.md) for detailed contribution ideas.

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

## Acknowledgments

- [Tatoeba Project](https://tatoeba.org/) for sentence data
- [MDBG](https://www.mdbg.net/) for CC-CEDICT dictionary
- [elkmovie](https://github.com/elkmovie) for HSK 3.0 character lists
- All contributors to open Chinese language learning resources

---

## Contact & Resources

- **Repository**: https://github.com/brianhliou/hanzi-flow
- **Live Demo**: https://hanziflow.vercel.app
- **Issues**: https://github.com/brianhliou/hanzi-flow/issues

**Tech Resources**:
- Next.js: https://nextjs.org/docs
- pypinyin: https://github.com/mozillazg/python-pinyin
- jieba: https://github.com/fxsjy/jieba
- Tatoeba: https://tatoeba.org/en/downloads
- CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict
- HSK 3.0: https://github.com/elkmovie/hsk30
