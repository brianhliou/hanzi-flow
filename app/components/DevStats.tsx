'use client';

import { useState, useEffect } from 'react';
import { getAllWords, getAllSentences, getDatabaseStats, resetDatabase, type WordMastery, type SentenceProgress } from '@/lib/db';
import { loadSentences } from '@/lib/sentences';
import type { Sentence } from '@/lib/types';

/**
 * Development component for inspecting IndexedDB word mastery data
 * Shows stats and allows resetting the database
 */
export default function DevStats() {
  const [stats, setStats] = useState<any>(null);
  const [words, setWords] = useState<WordMastery[]>([]);
  const [sentences, setSentences] = useState<SentenceProgress[]>([]);
  const [showWords, setShowWords] = useState(false);
  const [showSentences, setShowSentences] = useState(false);
  const [loading, setLoading] = useState(true);
  const [charLookup, setCharLookup] = useState<Map<number, string>>(new Map());
  const [sentenceLookup, setSentenceLookup] = useState<Map<number, string>>(new Map());

  const loadData = async () => {
    setLoading(true);
    const statsData = await getDatabaseStats();
    const wordsData = await getAllWords();
    const sentencesData = await getAllSentences();

    // Build character lookup and sentence lookup maps from sentences
    const sentencesCorpus = await loadSentences();
    const charLookup = new Map<number, string>();
    const sentenceLookup = new Map<number, string>();

    for (const sentence of sentencesCorpus) {
      // Build character lookup
      for (const char of sentence.chars) {
        if (char.char_id !== null && !charLookup.has(char.char_id)) {
          charLookup.set(char.char_id, char.char);
        }
      }
      // Build sentence lookup
      sentenceLookup.set(sentence.id, sentence.sentence);
    }

    setStats(statsData);
    setWords(wordsData);
    setSentences(sentencesData);
    setCharLookup(charLookup);
    setSentenceLookup(sentenceLookup);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleReset = async () => {
    if (confirm('Are you sure you want to reset all mastery data? This cannot be undone.')) {
      await resetDatabase();
      await loadData();
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">Loading stats...</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold">IndexedDB Stats (Dev)</h3>
        <button
          onClick={handleReset}
          className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
        >
          Reset Database
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-500 dark:text-gray-400">Total Words</div>
          <div className="text-2xl font-bold">{stats.totalWords}</div>
        </div>
        <div className="bg-white dark:bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-500 dark:text-gray-400">Avg Mastery</div>
          <div className="text-2xl font-bold">{stats.avgMastery}</div>
        </div>
        <div className="bg-white dark:bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-500 dark:text-gray-400">Avg Success</div>
          <div className="text-2xl font-bold">{stats.avgSuccess}</div>
        </div>
        <div className="bg-white dark:bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-500 dark:text-gray-400">Total Attempts</div>
          <div className="text-2xl font-bold">{stats.totalAttempts}</div>
        </div>
      </div>

      {/* Toggle Word List */}
      <button
        onClick={() => setShowWords(!showWords)}
        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        {showWords ? 'Hide' : 'Show'} All Words ({words.length})
      </button>

      {/* Word List */}
      {showWords && words.length > 0 && (
        <div className="max-h-96 overflow-auto bg-white dark:bg-gray-700 p-4 rounded">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-gray-100 dark:bg-gray-800">
              <tr>
                <th className="text-left p-1">ID</th>
                <th className="text-left p-1">Char</th>
                <th className="text-left p-1">Mastery</th>
                <th className="text-left p-1">True %</th>
                <th className="text-left p-1">EWMA</th>
                <th className="text-left p-1">Correct</th>
                <th className="text-left p-1">Attempts</th>
                <th className="text-left p-1">Streak</th>
                <th className="text-left p-1">Stability</th>
                <th className="text-left p-1">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {words.map((word) => {
                const trueSuccessRate = word.n_attempts > 0
                  ? ((word.n_correct / word.n_attempts) * 100).toFixed(1)
                  : '0.0';

                return (
                  <tr key={word.char_id} className="border-t dark:border-gray-600">
                    <td className="p-1">{word.char_id}</td>
                    <td className="p-1 text-lg">{charLookup.get(word.char_id) || '?'}</td>
                    <td className="p-1">{word.s.toFixed(3)}</td>
                    <td className="p-1">{trueSuccessRate}%</td>
                    <td className="p-1">{word.ewma_success.toFixed(3)}</td>
                    <td className="p-1">{word.n_correct}</td>
                    <td className="p-1">{word.n_attempts}</td>
                    <td className="p-1">{word.streak_correct}</td>
                    <td className="p-1">{word.stability_days.toFixed(1)}</td>
                    <td className="p-1">
                      <span
                        className={`px-1 py-0.5 rounded text-xs ${
                          word.last_outcome === 'correct'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}
                      >
                        {word.last_outcome === 'correct' ? '✓' : '✗'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Toggle Sentence List */}
      <button
        onClick={() => setShowSentences(!showSentences)}
        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        {showSentences ? 'Hide' : 'Show'} All Sentences ({sentences.length})
      </button>

      {/* Sentence List */}
      {showSentences && sentences.length > 0 && (
        <div className="max-h-96 overflow-auto bg-white dark:bg-gray-700 p-4 rounded">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-gray-100 dark:bg-gray-800">
              <tr>
                <th className="text-left p-1">SID</th>
                <th className="text-left p-1">Sentence</th>
                <th className="text-left p-1">Pass %</th>
                <th className="text-left p-1">Pass</th>
                <th className="text-left p-1">Seen</th>
                <th className="text-left p-1">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {sentences.map((sent) => {
                const passRate = sent.seen_count > 0
                  ? ((sent.pass_count / sent.seen_count) * 100).toFixed(1)
                  : '0.0';

                return (
                  <tr key={sent.sid} className="border-t dark:border-gray-600">
                    <td className="p-1">{sent.sid}</td>
                    <td className="p-1">{sentenceLookup.get(sent.sid) || '?'}</td>
                    <td className="p-1">{passRate}%</td>
                    <td className="p-1">{sent.pass_count}</td>
                    <td className="p-1">{sent.seen_count}</td>
                    <td className="p-1">
                      <span
                        className={`px-1 py-0.5 rounded text-xs ${
                          sent.last_outcome === 'pass'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}
                      >
                        {sent.last_outcome === 'pass' ? '✓' : '✗'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
