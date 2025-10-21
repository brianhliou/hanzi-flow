'use client';

import { useEffect, useState } from 'react';
import { getAllWords, getAllSentences, type WordMastery } from '@/lib/db';
import { getCorpusMetadata } from '@/lib/sentences';
import { SELECTION_CONFIG } from '@/lib/selection-config';
import { loadCharacterMapping } from '@/lib/characters';

interface UserStatsData {
  // Character stats
  totalCharactersLearned: number;
  charactersMastered: number;
  charactersLearning: number;
  charactersNew: number;
  totalCharsInCorpus: number;

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

// Reverse lookup: char_id -> character
let idToCharMap: Map<number, string> | null = null;

async function loadIdToCharMap(): Promise<Map<number, string>> {
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

    // Parse CSV line: id,char,script_type,...
    const match = line.match(/^(\d+),([^,]+),/);
    if (match) {
      const id = parseInt(match[1], 10);
      const char = match[2];
      idToCharMap.set(id, char);
    }
  }

  return idToCharMap;
}

function getCharFromId(charId: number): string {
  return idToCharMap?.get(charId) ?? '?';
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

        setStats({
          totalCharactersLearned: words.length,
          charactersMastered: masteredWords.length,
          charactersLearning: learningWords.length,
          charactersNew: newWords.length,
          totalCharsInCorpus: metadata.totalCharsInCorpus,
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
    <div className="space-y-8">
      {/* Character Progress */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Character Progress</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

      {/* Sentence Practice */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Sentence Practice</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        <h2 className="text-xl font-semibold mb-4">Mastery Breakdown</h2>
        <div className="space-y-4">
          <MasteryCategory
            label="Mastered"
            count={stats.charactersMastered}
            description={isDev
              ? `High proficiency (≥${SELECTION_CONFIG.mastered_threshold} mastery)`
              : "High proficiency"}
            color="green"
            words={stats.masteredWords}
          />
          <MasteryCategory
            label="Learning"
            count={stats.charactersLearning}
            description={isDev
              ? `Making progress (${SELECTION_CONFIG.learning_threshold}-${SELECTION_CONFIG.mastered_threshold} mastery)`
              : "Making progress"}
            color="blue"
            words={stats.learningWords}
          />
          <MasteryCategory
            label="New / Struggling"
            count={stats.charactersNew}
            description={isDev
              ? `Recently encountered (<${SELECTION_CONFIG.learning_threshold} mastery)`
              : "Recently encountered"}
            color="yellow"
            words={stats.newWords}
          />
        </div>
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
    <div className={`rounded-lg border p-6 ${colorClasses[color]}`}>
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
        {label}
      </div>
      <div className="text-3xl font-bold mb-1">
        {value}
        {suffix && <span className="text-lg text-gray-500 dark:text-gray-400 ml-1">{suffix}</span>}
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
        <div className="px-6 pb-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="flex flex-wrap gap-3">
            {words.map((word) => (
              <div
                key={word.char_id}
                className="inline-flex items-center justify-between gap-3 w-24 px-4 py-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600"
              >
                <span className="text-2xl font-medium">
                  {getCharFromId(word.char_id)}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {word.s.toFixed(2)}
                </span>
              </div>
            ))}
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
