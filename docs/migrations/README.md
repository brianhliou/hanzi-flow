# Data Pipeline Migrations

History of major data pipeline refactors and migrations.

## Migrations

### [Pinyin Format Migration (November 2025)](./pinyin-format-2025-11/)

**Status**: ✅ Complete (Data Pipeline) - App integration pending

**Problem**: Mixed pinyin formats (Unihan tone marks + pypinyin tone numbers) causing 612 duplicate syllables (30.5% duplication).

**Solution**: Migrated to pypinyin-only with dual-format storage (pinyins_tone3 + pinyins_display).

**Results**:
- Eliminated 612 duplicate syllables (100% → 0%)
- Reduced unique syllables: 2,004 → 1,307 (-35%)
- 100% pinyin coverage (up from 99.7%)
- Added pinyin-level frequencies
- Simplified pipeline: 7 steps → 6 steps

**Documents**:
- [MIGRATION_SUMMARY.md](./pinyin-format-2025-11/MIGRATION_SUMMARY.md) - Executive summary
- [MIGRATION_PLAN.md](./pinyin-format-2025-11/MIGRATION_PLAN.md) - Detailed implementation plan
- [MIGRATION_COMPLETE.md](./pinyin-format-2025-11/MIGRATION_COMPLETE.md) - Completion report with validation

**See also**: [LESSONS_LEARNED.md](../LESSONS_LEARNED.md) Section 4 for root cause analysis

---

## Migration Process Template

For future migrations, follow this structure:

1. **Problem Analysis** - Document the issue and impact
2. **Proposed Solutions** - Evaluate options with tradeoffs
3. **Migration Plan** - Detailed phased approach with rollback
4. **Verification** - Automated validation at each checkpoint
5. **Completion Report** - Results, files changed, what to inspect
6. **Lessons Learned** - Update LESSONS_LEARNED.md
