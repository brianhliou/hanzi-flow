'use client';

import { useEffect, useState } from 'react';
import { getAllWords, getAllSentences, type WordMastery } from '@/lib/db';
import { getCorpusMetadata } from '@/lib/sentences';
import { SELECTION_CONFIG } from '@/lib/selection-config';
import { loadCharacterMapping } from '@/lib/characters';
import { playPinyinAudio } from '@/lib/audio';
import { convertToneMarksToNumbers } from '@/lib/pinyin';

interface HskLevelProgress {
  level: string;
  mastered: number;
  seen: number;
  total: number;
  masteredPercentage: number;
  seenPercentage: number;
}

interface UserStatsData {
  // Character stats
  totalCharactersLearned: number;
  charactersMastered: number;
  charactersLearning: number;
  charactersNew: number;
  totalCharsInCorpus: number;

  // HSK progress
  hskProgress: HskLevelProgress[];

  // Sentence stats
  sentencesPracticedUnique: number;
  sentencesMastered: number;

  // Performance stats
  overallAccuracy: number;

  // Character lists by mastery
  masteredWords: WordMastery[];
  learningWords: WordMastery[];
  newWords: WordMastery[];
}

// Reverse lookup: char_id -> {character, pinyin, allPinyins, hskLevel}
let idToCharMap: Map<number, { char: string; pinyin: string; allPinyins: string[]; hskLevel?: string }> | null = null;

// Simple CSV parser that handles quoted fields
function parseCSVLine(line: string): string[] {
  const fields: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      fields.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  // Always push the last field (even if empty due to trailing comma)
  fields.push(current.trim());

  return fields;
}

async function loadIdToCharMap(): Promise<Map<number, { char: string; pinyin: string; altPinyins?: string; hskLevel?: string }>> {
  if (idToCharMap) return idToCharMap;

  const response = await fetch('/data/character_set/chinese_characters.csv');
  if (!response.ok) {
    throw new Error('Failed to load character mapping');
  }

  const csvText = await response.text();
  const lines = csvText.split('\n');

  idToCharMap = new Map();

  // Skip header line
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Parse CSV line: id,char,codepoint,pinyins,script_type,variants,gloss_en,examples,hsk_level
    // Use a simple CSV parser that handles quoted fields
    const fields = parseCSVLine(line);

    if (fields.length < 9) continue;

    const id = parseInt(fields[0], 10);
    const char = fields[1];
    const pinyinsRaw = fields[3];
    const hskLevel = fields[8] || undefined;

    // Extract all pinyins (remove frequency counts)
    // Format: "yī(32747)" or "le(30101)|liǎo(654)"
    const pinyinVariants = pinyinsRaw
      .split('|')
      .map(p => p.replace(/\([^)]+\)/, '').trim())
      .filter(p => p.length > 0);

    const pinyin = pinyinVariants[0] || '?';
    const allPinyins = pinyinVariants;

    idToCharMap.set(id, { char, pinyin, allPinyins, hskLevel });
  }

  console.log(`Loaded ${idToCharMap.size} characters into map`);

  return idToCharMap;
}

function getCharFromId(charId: number): { char: string; pinyin: string; allPinyins: string[]; hskLevel?: string } {
  const result = idToCharMap?.get(charId);
  if (!result) {
    console.warn(`Character ID ${charId} not found in CSV`);
    return { char: '?', pinyin: '?', allPinyins: ['?'] };
  }
  return result;
}

export default function UserStats() {
  const [stats, setStats] = useState<UserStatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const isDev = process.env.NODE_ENV === 'development';

  useEffect(() => {
    async function calculateStats() {
      try {
        const [words, sentences, metadata] = await Promise.all([
          getAllWords(),
          getAllSentences(),
          getCorpusMetadata(),
          loadIdToCharMap()
        ]);

        // Character breakdown by mastery
        const masteredWords = words.filter(w => w.s >= SELECTION_CONFIG.mastered_threshold);
        const learningWords = words.filter(w =>
          w.s >= SELECTION_CONFIG.learning_threshold &&
          w.s < SELECTION_CONFIG.mastered_threshold
        );
        const newWords = words.filter(w => w.s < SELECTION_CONFIG.learning_threshold);

        // Sort by mastery score (descending - highest first)
        masteredWords.sort((a, b) => b.s - a.s);
        learningWords.sort((a, b) => b.s - a.s);
        newWords.sort((a, b) => b.s - a.s);

        // Overall accuracy
        const totalAttempts = words.reduce((sum, w) => sum + w.n_attempts, 0);
        const totalCorrect = words.reduce((sum, w) => sum + w.n_correct, 0);
        const accuracy = totalAttempts > 0 ? totalCorrect / totalAttempts : 0;

        // Sentence stats
        const uniqueSentences = sentences.length;
        const masteredSentences = sentences.filter(s => s.ewma_pass >= 0.95).length;

        // HSK Progress calculation
        // Count both mastered and seen characters by HSK level
        const hskCounts: Record<string, { mastered: number; seen: number; total: number }> = {
          '1': { mastered: 0, seen: 0, total: 300 },
          '2': { mastered: 0, seen: 0, total: 300 },
          '3': { mastered: 0, seen: 0, total: 300 },
          '4': { mastered: 0, seen: 0, total: 300 },
          '5': { mastered: 0, seen: 0, total: 300 },
          '6': { mastered: 0, seen: 0, total: 300 },
          '7-9': { mastered: 0, seen: 0, total: 1200 },
        };

        // Count characters for each HSK level
        for (const word of words) {
          const charData = getCharFromId(word.char_id);
          if (charData.hskLevel && hskCounts[charData.hskLevel]) {
            // All characters in 'words' are seen
            hskCounts[charData.hskLevel].seen++;
            // Count mastered characters (≥0.8 mastery)
            if (word.s >= SELECTION_CONFIG.mastered_threshold) {
              hskCounts[charData.hskLevel].mastered++;
            }
          }
        }

        // Build HSK progress array
        const hskProgress: HskLevelProgress[] = [
          {
            level: '1',
            ...hskCounts['1'],
            masteredPercentage: (hskCounts['1'].mastered / hskCounts['1'].total) * 100,
            seenPercentage: (hskCounts['1'].seen / hskCounts['1'].total) * 100,
          },
          {
            level: '2',
            ...hskCounts['2'],
            masteredPercentage: (hskCounts['2'].mastered / hskCounts['2'].total) * 100,
            seenPercentage: (hskCounts['2'].seen / hskCounts['2'].total) * 100,
          },
          {
            level: '3',
            ...hskCounts['3'],
            masteredPercentage: (hskCounts['3'].mastered / hskCounts['3'].total) * 100,
            seenPercentage: (hskCounts['3'].seen / hskCounts['3'].total) * 100,
          },
          {
            level: '4',
            ...hskCounts['4'],
            masteredPercentage: (hskCounts['4'].mastered / hskCounts['4'].total) * 100,
            seenPercentage: (hskCounts['4'].seen / hskCounts['4'].total) * 100,
          },
          {
            level: '5',
            ...hskCounts['5'],
            masteredPercentage: (hskCounts['5'].mastered / hskCounts['5'].total) * 100,
            seenPercentage: (hskCounts['5'].seen / hskCounts['5'].total) * 100,
          },
          {
            level: '6',
            ...hskCounts['6'],
            masteredPercentage: (hskCounts['6'].mastered / hskCounts['6'].total) * 100,
            seenPercentage: (hskCounts['6'].seen / hskCounts['6'].total) * 100,
          },
          {
            level: '7-9',
            ...hskCounts['7-9'],
            masteredPercentage: (hskCounts['7-9'].mastered / hskCounts['7-9'].total) * 100,
            seenPercentage: (hskCounts['7-9'].seen / hskCounts['7-9'].total) * 100,
          },
        ];

        setStats({
          totalCharactersLearned: words.length,
          charactersMastered: masteredWords.length,
          charactersLearning: learningWords.length,
          charactersNew: newWords.length,
          totalCharsInCorpus: metadata.totalCharsInCorpus,
          hskProgress,
          sentencesPracticedUnique: uniqueSentences,
          sentencesMastered: masteredSentences,
          overallAccuracy: accuracy,
          masteredWords,
          learningWords,
          newWords,
        });
      } catch (error) {
        console.error('Failed to calculate stats:', error);
      } finally {
        setLoading(false);
      }
    }

    calculateStats();
  }, []);

  if (loading) {
    return (
      <div className="text-center text-gray-500 py-8">
        Loading stats...
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center text-gray-500 py-8">
        Failed to load stats
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Character Progress */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Character Progress</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <StatCard
            label="Characters Learned"
            value={stats.totalCharactersLearned}
            suffix={`/ ${stats.totalCharsInCorpus}`}
            description={`${((stats.totalCharactersLearned / stats.totalCharsInCorpus) * 100).toFixed(1)}% of corpus`}
          />
          <StatCard
            label="Overall Accuracy"
            value={`${(stats.overallAccuracy * 100).toFixed(1)}%`}
            description="Across all attempts"
          />
        </div>
      </section>

      {/* HSK Progress */}
      <section>
        <h2 className="text-xl font-semibold mb-3">HSK Progress</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stats.hskProgress.map((level) => (
            <HskProgressBar
              key={level.level}
              level={level.level}
              mastered={level.mastered}
              seen={level.seen}
              total={level.total}
              masteredPercentage={level.masteredPercentage}
              seenPercentage={level.seenPercentage}
            />
          ))}
        </div>
      </section>

      {/* Sentence Practice */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Sentence Practice</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <StatCard
            label="Sentences Practiced"
            value={stats.sentencesPracticedUnique}
            description="Different sentences seen"
          />
          <StatCard
            label="Sentences Mastered"
            value={stats.sentencesMastered}
            description={isDev
              ? "Consistently accurate (≥95% EWMA)"
              : "Consistently accurate"}
            color="green"
          />
        </div>
      </section>

      {/* Mastery Breakdown */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Mastery Breakdown</h2>
        <MasteryBreakdownTabs
          masteredWords={stats.masteredWords}
          learningWords={stats.learningWords}
          newWords={stats.newWords}
          isDev={isDev}
        />
      </section>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  suffix?: string;
  description?: string;
  color?: 'green' | 'blue' | 'yellow' | 'gray';
}

function StatCard({ label, value, suffix, description, color = 'gray' }: StatCardProps) {
  const colorClasses = {
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    gray: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
  };

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
        {label}
      </div>
      <div className="text-2xl font-bold mb-1">
        {value}
        {suffix && <span className="text-base text-gray-500 dark:text-gray-400 ml-1">{suffix}</span>}
      </div>
      {description && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {description}
        </div>
      )}
    </div>
  );
}

interface MasteryCategoryProps {
  label: string;
  count: number;
  description: string;
  color: 'green' | 'blue' | 'yellow';
  words: WordMastery[];
}

function MasteryCategory({ label, count, description, color, words }: MasteryCategoryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const colorClasses = {
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
  };

  return (
    <div className={`rounded-lg border ${colorClasses[color]}`}>
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <div className="flex-1">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
            {label}
          </div>
          <div className="text-3xl font-bold mb-1">
            {count}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {description}
          </div>
        </div>
        <div className="text-gray-400 ml-4">
          {isExpanded ? '▼' : '▶'}
        </div>
      </button>

      {/* Character list - expandable */}
      {isExpanded && words.length > 0 && (
        <div className="pl-6 pr-3 pb-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="flex flex-wrap gap-3 justify-start">
            {words.map((word) => {
              const { char, pinyin } = getCharFromId(word.char_id);
              return (
                <div
                  key={word.char_id}
                  className="w-32 px-4 py-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600"
                >
                  {/* Line 1: Character + Score */}
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-3xl font-medium">
                      {char}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {word.s.toFixed(2)}
                    </span>
                  </div>
                  {/* Line 2: Pinyin */}
                  <div className="text-base text-gray-600 dark:text-gray-300">
                    {pinyin}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {isExpanded && words.length === 0 && (
        <div className="px-6 pb-6 border-t border-gray-200 dark:border-gray-700 pt-4 text-gray-500 dark:text-gray-400 text-sm">
          No characters in this category yet
        </div>
      )}
    </div>
  );
}

interface HskProgressBarProps {
  level: string;
  mastered: number;
  seen: number;
  total: number;
  masteredPercentage: number;
  seenPercentage: number;
}

function HskProgressBar({ level, mastered, seen, total, masteredPercentage, seenPercentage }: HskProgressBarProps) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-base">HSK {level}</span>
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {mastered} mastered • {seen} seen
          </span>
        </div>
        <span className="font-semibold text-sm text-gray-700 dark:text-gray-300">
          {seen}/{total}
        </span>
      </div>
      {/* Two-tone progress bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 relative overflow-hidden">
        {/* Seen portion (lighter color) */}
        <div
          className="absolute top-0 left-0 h-2 bg-blue-300 dark:bg-blue-700 transition-all"
          style={{ width: `${Math.min(seenPercentage, 100)}%` }}
        />
        {/* Mastered portion (darker color, overlaid) */}
        <div
          className="absolute top-0 left-0 h-2 bg-green-600 dark:bg-green-500 transition-all"
          style={{ width: `${Math.min(masteredPercentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

interface MasteryBreakdownTabsProps {
  masteredWords: WordMastery[];
  learningWords: WordMastery[];
  newWords: WordMastery[];
  isDev: boolean;
}

function MasteryBreakdownTabs({ masteredWords, learningWords, newWords, isDev }: MasteryBreakdownTabsProps) {
  const [activeTab, setActiveTab] = useState<'mastered' | 'learning' | 'new'>('learning');

  const tabs = [
    {
      id: 'mastered' as const,
      label: 'Mastered',
      count: masteredWords.length,
      description: isDev
        ? `High proficiency (≥${SELECTION_CONFIG.mastered_threshold} mastery)`
        : 'High proficiency',
      words: masteredWords,
      color: 'green',
    },
    {
      id: 'learning' as const,
      label: 'Learning',
      count: learningWords.length,
      description: isDev
        ? `Making progress (${SELECTION_CONFIG.learning_threshold}-${SELECTION_CONFIG.mastered_threshold} mastery)`
        : 'Making progress',
      words: learningWords,
      color: 'blue',
    },
    {
      id: 'new' as const,
      label: 'New / Struggling',
      count: newWords.length,
      description: isDev
        ? `Recently encountered (<${SELECTION_CONFIG.learning_threshold} mastery)`
        : 'Recently encountered',
      words: newWords,
      color: 'yellow',
    },
  ];

  const activeTabData = tabs.find(t => t.id === activeTab)!;

  const getTabColorClasses = (tabId: string, isActive: boolean) => {
    if (!isActive) {
      return 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100';
    }

    const colorMap = {
      mastered: 'border-green-600 text-green-600 dark:text-green-400',
      learning: 'border-blue-600 text-blue-600 dark:text-blue-400',
      new: 'border-yellow-600 text-yellow-600 dark:text-yellow-400',
    };
    return colorMap[tabId as keyof typeof colorMap];
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab.id
                ? getTabColorClasses(tab.id, true)
                : 'border-transparent ' + getTabColorClasses(tab.id, false)
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-4">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {activeTabData.description}
        </p>

        {activeTabData.words.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No characters in this category yet
          </div>
        ) : (
          <div className="flex flex-wrap gap-3 justify-start">
            {activeTabData.words.map((word) => {
              const { char, pinyin, allPinyins, hskLevel } = getCharFromId(word.char_id);

              return (
                <div
                  key={word.char_id}
                  className="w-44 px-3 py-2.5 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600 flex flex-col"
                >
                  {/* Line 1: Character + Primary Pinyin */}
                  <div className="flex items-baseline gap-2 mb-1.5">
                    <span className="text-3xl font-medium">{char}</span>
                    <button
                      onClick={() => playPinyinAudio(convertToneMarksToNumbers(pinyin))}
                      className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      {pinyin}
                    </button>
                  </div>

                  {/* Line 2: Alt Pinyins (if any, wraps max 2 lines) */}
                  {allPinyins.length > 1 && (
                    <div className="flex flex-wrap items-start content-start gap-1 mb-1.5 h-[2.75rem] overflow-hidden">
                      {allPinyins.slice(1).map((py, idx) => {
                        const pinyinWithNumbers = convertToneMarksToNumbers(py);
                        return (
                          <button
                            key={idx}
                            onClick={() => playPinyinAudio(pinyinWithNumbers)}
                            className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                          >
                            {py}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Spacer to push footer to bottom */}
                  <div className="flex-1"></div>

                  {/* Footer: Score and HSK (pinned to bottom) */}
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
                    <span>{word.s.toFixed(2)}</span>
                    <span>{hskLevel ? `HSK ${hskLevel}` : 'Beyond HSK'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
