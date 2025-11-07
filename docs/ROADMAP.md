# Roadmap

**Current Status:** Production-ready MVP

**Last Updated:** 2025-11-06

---

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

---

## Planned Features

### High Priority
- **Mobile PWA optimization** - Installable app, offline support, touch keyboard handling
- **HSK stats integration** - Progress breakdown by HSK level on stats page
- **Review mode** - Practice overdue characters, filter by low mastery

### Medium Priority
- **Pronunciation trainer** - Record and evaluate user pronunciation against native audio
  - Handle Sandhi (音变) - Validate against surface tones after tone change rules (third-tone sandhi, 一/不 tone changes, neutral tone)
- **Character detail view** - Click character to see etymology, stroke order, compounds
- **Sentence-level audio** - Full sentence pronunciation (TTS or pre-recorded)
- **Export/import progress** - Backup and restore user data across devices

### Lower Priority
- **Tone error analytics** - Track confusion patterns, targeted drills
- **Custom corpus** - Import personal sentence lists, topic filtering
- **Vocabulary mode** - Practice 2+ character words instead of sentences
- **Character writing practice** - Stroke order, handwriting recognition

---

## Explicitly Not Planned

- ❌ **Study streaks / session tracking** - Conflicts with flow-state learning principle
- ❌ **Session summary popups** - Interrupts continuous practice flow
- ❌ **User accounts / cloud sync (MVP)** - Local-first is core principle
- ❌ **Cantonese / Classical Chinese (MVP)** - Mandarin focus for now

---

## Contributing

Want to contribute? Check:
- This roadmap for planned features
- `KNOWN_ISSUES.md` for bugs and limitations
- GitHub issues for active discussions

Open an issue before starting work on major features.
