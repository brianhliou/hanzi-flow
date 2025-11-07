# Hanzi Flow

**Master Chinese Reading with HSK 3.0-Aligned Adaptive Practice**

A privacy-first, local-first web application for learning Chinese characters through contextual sentence practice. Uses an adaptive algorithm to select sentences based on your mastery level, with support for both Simplified and Traditional Chinese.

🔗 **[Live Demo](https://hanziflow.vercel.app)**

![Hanzi Flow Practice Interface](.github/screenshot.png)
*Character-by-character sentence practice with real-time feedback*

## ✨ Key Features

- 🎯 **HSK 3.0 Aligned** - Complete coverage of HSK levels 1-9 (3,000+ characters), 79,000+ sentences
- 🧠 **Adaptive Learning** - NSS algorithm picks optimal sentences based on your mastery level
- 🔒 **100% Private** - All data stored in browser (IndexedDB), no backend, no tracking, works offline
- 🌐 **Flexible Scripts** - Simplified, Traditional, or Mixed mode with automatic classification
- 📊 **Progress Tracking** - Character-level mastery scores, visual stats dashboard, spaced repetition
- 🔊 **Audio Support** - Native speaker audio for all pinyin syllables

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+ (only if rebuilding data pipelines)

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

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory, including:
- Vision and architecture
- Development workflows and setup
- Data pipeline documentation
- Feature roadmap
- Technical insights and debugging tips

**Start here:** [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) for an overview with links to all other documentation.

## 🛠️ Tech Stack

**Frontend:** Next.js 15 + React 19 + TypeScript + Tailwind CSS + IndexedDB (Dexie.js)

**Data Pipeline:** Python 3.9+ (pypinyin, jieba, pandas)

**Data Sources:** Tatoeba (sentences), CC-CEDICT (dictionary), elkmovie/hsk30 (HSK lists)

**Deployment:** Vercel (or any static host)

---

## 📊 Data Sources

This project builds upon excellent open-source datasets:

- **Sentences**: [Tatoeba](https://tatoeba.org/) (CC BY 2.0 FR) - 79,704 Chinese-English sentence pairs
- **Dictionary**: [CC-CEDICT](https://cc-cedict.org/) (CC BY-SA 4.0) - Chinese-English dictionary
- **HSK Classification**: [elkmovie/hsk30](https://github.com/elkmovie/hsk30) (MIT) - Official HSK 3.0 character lists
- **Audio**: Generated using AWS Polly (Zhiyu voice)

All processed data is included in this repository under compatible licenses.

## 🤝 Contributing

Hanzi Flow is an open-source Chinese learning platform built with extensibility and community collaboration in mind. Contributions, feature requests, and bug reports are welcome!

**Before contributing:**
1. Check the [`docs/`](docs/) directory for roadmap, architecture, and known issues
2. Open an issue to discuss major changes before submitting PRs
3. See documentation for contribution ideas and development workflows

**Key areas for contribution:**
- Additional sentence sources and content
- Mobile and PWA optimization
- Alternative learning algorithms
- New practice modes and features

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Tatoeba Project](https://tatoeba.org/) for sentence data
- [MDBG](https://www.mdbg.net/) for CC-CEDICT dictionary
- [elkmovie](https://github.com/elkmovie) for HSK 3.0 character lists
- All contributors to open Chinese language learning resources

**Questions?** Check the [documentation](docs/) or open an [issue](https://github.com/brianhliou/hanzi-flow/issues).
