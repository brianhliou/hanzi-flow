/**
 * Utility to load snapshot data into fake IndexedDB for testing
 */

import { db, type WordMastery, type SentenceProgress } from '@/lib/db';
import snapshot from '../fixtures/user-snapshot.json';

export interface Snapshot {
  timestamp: number;
  dateExported: string;
  stats: {
    totalWords: number;
    avgMastery: string;
    avgSuccess: string;
    totalAttempts: number;
  };
  words: WordMastery[];
  sentences: SentenceProgress[];
  metadata: {
    totalWords: number;
    totalSentences: number;
    avgMastery: string;
    description: string;
  };
}

/**
 * Load the user snapshot into IndexedDB
 */
export async function loadSnapshot(): Promise<void> {
  const data = snapshot as Snapshot;

  // Clear existing data
  await db.words.clear();
  await db.sentences.clear();
  await db.queue.clear();

  // Load words
  await db.words.bulkAdd(data.words);

  // Load sentences
  await db.sentences.bulkAdd(data.sentences);

  console.log(`✓ Loaded snapshot: ${data.words.length} words, ${data.sentences.length} sentences`);
}

/**
 * Clear all data from IndexedDB
 */
export async function clearDatabase(): Promise<void> {
  await db.words.clear();
  await db.sentences.clear();
  await db.queue.clear();
}

/**
 * Get snapshot data without loading into DB
 */
export function getSnapshotData(): Snapshot {
  return snapshot as Snapshot;
}

/**
 * Get words in a specific mastery range
 */
export function getWordsInRange(min: number, max: number): WordMastery[] {
  const data = snapshot as Snapshot;
  return data.words.filter(w => w.s >= min && w.s < max);
}

/**
 * Get character IDs for testing specific scenarios
 */
export function getCharacterIdsByMastery() {
  const data = snapshot as Snapshot;

  return {
    unknown: data.words.filter(w => w.s < 0.6).map(w => w.char_id),
    knownButNotMastered: data.words.filter(w => w.s >= 0.6 && w.s < 0.8).map(w => w.char_id),
    mastered: data.words.filter(w => w.s >= 0.8).map(w => w.char_id),
  };
}
