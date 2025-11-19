# Roadmap

**Current Status:** Production-ready MVP

**Last Updated:** 2025-11-19

## Completed Features

### Core Learning Experience
- ✅ Adaptive sentence selection (NSS algorithm)
- ✅ Character-by-character pinyin input with real-time feedback
- ✅ EWMA-based mastery tracking with spaced repetition
- ✅ Progress statistics dashboard
- ✅ HSK 3.0 filtering (levels 1-9)
- ✅ Script preference (Simplified/Traditional/Mixed)
- ✅ Audio pronunciation for pinyin syllables

### Data Infrastructure
- ✅ 79,000+ sentence corpus from Tatoeba
- ✅ 20,992 character dataset with dual-format pinyin
- ✅ 100% pinyin coverage via pypinyin
- ✅ Context-aware pinyin (2,870 AI-verified improvements)
- ✅ 6-step character pipeline
- ✅ 6-step sentence pipeline with optional refinement
- ✅ HSK classification (character + sentence level)
- ✅ English translations via OpenAI

### Technical Achievements
- ✅ Pinyin format migration (eliminated 612 duplicate syllables)
- ✅ Local-first architecture (IndexedDB, no backend)
- ✅ Batch prefetching for seamless practice
- ✅ Development logging system

## Planned Features

### High Priority
- **Mobile PWA optimization** - Installable app, offline support, touch keyboard handling
- **HSK stats integration** - Progress breakdown by HSK level on stats page
- **Review mode** - Practice overdue characters, filter by low mastery

### Backlog

**Core Learning Experience**
- **NSS Phase 2 (Character-aware sampling)** - Biased sampling to prioritize overdue characters (70% review / 30% new)
- **Pronunciation trainer** - Record and evaluate user pronunciation against native audio
  - Handle Sandhi (音变) - Validate against surface tones after tone change rules (third-tone sandhi, 一/不 tone changes, neutral tone)
- **Sentence-level audio** - Full sentence pronunciation (TTS or pre-recorded)
- **Interleaved practice modes** - Rotate between sentence completion, reverse (EN→CN), listening-only, speed drills
- **Dialogue mode** - Multi-turn conversation practice with contextual sentences
- **Reading comprehension passages** - Multi-sentence stories with integrated practice
- **Vocabulary mode** - Practice 2+ character words instead of sentences

**Learning Science & Analytics**
- **Error pattern recognition** - Track tone confusions, similar pinyin, heteronym mistakes
- **Metacognition layer** - Self-assessment after sentences (confidence rating, guess tracking)
- **Tone error analytics** - Track confusion patterns, generate targeted drills
- **Learning velocity dashboard** - Track characters/week, project HSK timeline, identify fast/slow improvers
- **Character relationship mapping** - Visual graph of radicals, phonetic components, semantic families with mastery overlay
- **Forgetting curve prediction** - Show predicted retention, optimal review timing per character
- **Personal best tracking** - Longest streak, fastest sentence, best accuracy day (compete with yourself)

**Content & Media**
- **Custom corpus** - Import personal sentence lists, topic filtering
- **Media-linked sentences** - Tag sentences with source material (books, news, shows)
- **AI sentence generator** - Generate practice sentences with HSK/topic constraints
- **Grammar explanations** - AI-generated pattern explanations for sentences

**User Experience**
- **Character detail view** - Click character to see etymology, stroke order, compounds
- **AI etymology explainer** - Oracle bone → modern evolution, mnemonic stories
- **Keyboard shortcuts (power user mode)** - h=hint, s=skip, r=review, ?=definition
- **Distraction-free Zen mode** - Fullscreen minimal UI, Pomodoro integration
- **Custom themes/fonts** - Size, serif/sans, high contrast, dyslexia-friendly, calligraphy fonts
- **Achievement unlocks (hidden)** - Discover milestones organically without pressure

**Data & Integration**
- **Export/import progress** - Backup and restore user data across devices
- **Browser extension** - Highlight Chinese on any webpage, add to practice queue
- **Anki deck export** - Export practiced sentences with mastery tags
- **Note-taking integration** - Obsidian/Notion plugins for embedded practice stats

**Advanced Features**
- **Conversational AI partner** - Chat practice with adaptive difficulty
- **Character writing practice** - Stroke order, handwriting recognition

## Out of Scope (For Now)

### Philosophically Opposed
These conflict with core values and are unlikely to be added:

- ❌ **Ads or paywalls for core features** - Conflicts with accessibility and open-source philosophy
- ❌ **User tracking or data selling** - Privacy-first is non-negotiable
- ❌ **Mandatory daily streaks** - Conflicts with flow-state learning (pressure-free practice)
- ❌ **Intrusive popups or interruptions** - Maintains continuous practice flow

### Not Prioritized for MVP
These may be considered as the project evolves:

- 🔒 **User accounts / cloud sync** - Local-first for MVP, but optional sync could enable cross-device learning
- 🔒 **Social features / leaderboards** - Privacy concerns for MVP, but opt-in pseudonymous communities possible
- 🔒 **Advanced gamification** - Flow-state focus for MVP, but subtle optional achievements could enhance motivation
- 🔒 **Other Chinese variants** - Mandarin focus for MVP (Cantonese, Classical Chinese could be future expansions)
