/**
 * IndexedDB database schema using Dexie.js
 * Stores word-level mastery data for spaced repetition and adaptive learning
 */

import Dexie, { Table } from 'dexie';

/**
 * Word mastery record
 * Tracks learning progress for a single character
 */
export interface WordMastery {
  char_id: number;           // Primary key - character ID from chinese_characters.csv
  s: number;                 // Mastery score [0,1] - exponential smoothing
  stability_days: number;    // Spaced repetition interval (days)
  next_review_ts: number;    // Next review timestamp (epoch ms)
  last_seen_ts: number;      // Last interaction timestamp (epoch ms)
  n_attempts: number;        // Total number of attempts
  n_correct: number;         // Total number of correct attempts
  streak_correct: number;    // Current consecutive correct streak
  ewma_success: number;      // Exponentially weighted moving average success rate (recency-weighted)
  last_outcome: 'correct' | 'wrong';  // Result of most recent attempt
  introduced_ts: number;     // First seen timestamp (epoch ms)
}

/**
 * Sentence progress record
 * Tracks how often a sentence has been practiced and user success rate
 */
export interface SentenceProgress {
  sid: number;               // Primary key - sentence ID from cmn_sentences_with_char_pinyin.csv
  introduced_ts: number;     // First time sentence was shown (epoch ms)
  last_seen_ts: number;      // Most recent practice timestamp (epoch ms)
  seen_count: number;        // Total times sentence has been practiced
  pass_count: number;        // Total times all Chinese chars were correct on first attempt
  last_outcome: 'pass' | 'fail';  // Result of most recent attempt
}

/**
 * Hanzi Flow IndexedDB Database
 */
class HanziFlowDB extends Dexie {
  // Typed tables
  words!: Table<WordMastery, number>;
  sentences!: Table<SentenceProgress, number>;

  constructor() {
    super('HanziFlowDB');

    // Schema version 1: word mastery only
    this.version(1).stores({
      // Primary key: char_id
      // Indexes: next_review_ts (for review queue), last_seen_ts (for recency queries)
      words: 'char_id, next_review_ts, last_seen_ts'
    });

    // Schema version 2: add sentence progress tracking
    this.version(2).stores({
      words: 'char_id, next_review_ts, last_seen_ts',
      // Primary key: sid
      // Indexes: last_seen_ts (for recency queries)
      sentences: 'sid, last_seen_ts'
    });
  }
}

// Export singleton instance
export const db = new HanziFlowDB();

/**
 * Development utility: Get all word records for debugging
 */
export async function getAllWords(): Promise<WordMastery[]> {
  return await db.words.toArray();
}

/**
 * Development utility: Get all sentence records for debugging
 */
export async function getAllSentences(): Promise<SentenceProgress[]> {
  return await db.sentences.toArray();
}

/**
 * Development utility: Clear all data
 */
export async function resetDatabase(): Promise<void> {
  await db.words.clear();
  await db.sentences.clear();
  console.log('Database cleared');
}

/**
 * Development utility: Get database stats
 */
export async function getDatabaseStats() {
  const count = await db.words.count();
  const words = await db.words.toArray();

  if (count === 0) {
    return {
      totalWords: 0,
      avgMastery: 0,
      avgSuccess: 0,
      totalAttempts: 0,
    };
  }

  const avgMastery = words.reduce((sum, w) => sum + w.s, 0) / count;
  const avgSuccess = words.reduce((sum, w) => sum + w.ewma_success, 0) / count;
  const totalAttempts = words.reduce((sum, w) => sum + w.n_attempts, 0);

  return {
    totalWords: count,
    avgMastery: avgMastery.toFixed(3),
    avgSuccess: avgSuccess.toFixed(3),
    totalAttempts,
  };
}
