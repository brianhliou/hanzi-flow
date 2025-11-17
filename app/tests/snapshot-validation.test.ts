/**
 * Snapshot Validation Tests
 *
 * Tests that validate the exported snapshot data and basic DB operations.
 * These tests work without needing the full corpus (40MB JSON file).
 *
 * Future work: Add NSS integration tests when we have a small test corpus.
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { db } from '@/lib/db';
import {
  loadSnapshot,
  clearDatabase,
  getSnapshotData,
  getWordsInRange,
  getCharacterIdsByMastery
} from './utils/snapshot-loader';

describe('Snapshot Data Validation', () => {
  test('Snapshot has expected structure', () => {
    const snapshot = getSnapshotData();

    expect(snapshot).toHaveProperty('timestamp');
    expect(snapshot).toHaveProperty('dateExported');
    expect(snapshot).toHaveProperty('words');
    expect(snapshot).toHaveProperty('sentences');
    expect(snapshot).toHaveProperty('metadata');
  });

  test('Snapshot metadata matches actual data', () => {
    const snapshot = getSnapshotData();

    expect(snapshot.metadata.totalWords).toBe(snapshot.words.length);
    expect(snapshot.metadata.totalSentences).toBe(snapshot.sentences.length);
    expect(snapshot.words.length).toBe(1098);
    expect(snapshot.sentences.length).toBe(455);
  });

  test('Word mastery distribution is correct', () => {
    const charIds = getCharacterIdsByMastery();

    // Should match our earlier analysis
    expect(charIds.unknown.length).toBe(725);              // s < 0.6
    expect(charIds.knownButNotMastered.length).toBe(200);  // 0.6 <= s < 0.8
    expect(charIds.mastered.length).toBe(173);             // s >= 0.8

    // Total should equal all words
    const total = charIds.unknown.length +
                  charIds.knownButNotMastered.length +
                  charIds.mastered.length;
    expect(total).toBe(1098);
  });

  test('All word records have required fields', () => {
    const snapshot = getSnapshotData();

    for (const word of snapshot.words) {
      expect(word).toHaveProperty('char_id');
      expect(word).toHaveProperty('s');
      expect(word).toHaveProperty('stability_days');
      expect(word).toHaveProperty('next_review_ts');
      expect(word).toHaveProperty('last_seen_ts');
      expect(word).toHaveProperty('n_attempts');
      expect(word).toHaveProperty('n_correct');
      expect(word).toHaveProperty('streak_correct');
      expect(word).toHaveProperty('ewma_success');
      expect(word).toHaveProperty('last_outcome');
      expect(word).toHaveProperty('introduced_ts');

      // Validate types
      expect(typeof word.char_id).toBe('number');
      expect(typeof word.s).toBe('number');
      expect(word.s).toBeGreaterThanOrEqual(0);
      expect(word.s).toBeLessThanOrEqual(1);
      expect(['correct', 'wrong']).toContain(word.last_outcome);
    }
  });

  test('All sentence records have required fields', () => {
    const snapshot = getSnapshotData();

    for (const sent of snapshot.sentences) {
      expect(sent).toHaveProperty('sid');
      expect(sent).toHaveProperty('introduced_ts');
      expect(sent).toHaveProperty('last_seen_ts');
      expect(sent).toHaveProperty('seen_count');
      expect(sent).toHaveProperty('pass_count');
      expect(sent).toHaveProperty('cumulative_score');
      expect(sent).toHaveProperty('ewma_pass');
      expect(sent).toHaveProperty('last_outcome');

      // Validate types
      expect(typeof sent.sid).toBe('number');
      expect(['pass', 'fail']).toContain(sent.last_outcome);
      expect(sent.ewma_pass).toBeGreaterThanOrEqual(0);
      expect(sent.ewma_pass).toBeLessThanOrEqual(1);
    }
  });

  test('getWordsInRange filters correctly', () => {
    // Get words in [0.6, 0.8) range
    const knownNotMastered = getWordsInRange(0.6, 0.8);
    expect(knownNotMastered.length).toBe(200);

    // All should be in range
    for (const word of knownNotMastered) {
      expect(word.s).toBeGreaterThanOrEqual(0.6);
      expect(word.s).toBeLessThan(0.8);
    }
  });
});

describe('Database Operations', () => {
  beforeEach(async () => {
    await clearDatabase();
  });

  test('Can load snapshot into IndexedDB', async () => {
    await loadSnapshot();

    const wordCount = await db.words.count();
    const sentenceCount = await db.sentences.count();

    expect(wordCount).toBe(1098);
    expect(sentenceCount).toBe(455);
  });

  test('Can query words by mastery level', async () => {
    await loadSnapshot();

    // Note: 's' field is not indexed, so we filter in memory
    const allWords = await db.words.toArray();
    const knownNotMastered = allWords.filter(w => w.s >= 0.6 && w.s < 0.8);

    expect(knownNotMastered.length).toBe(200);
  });

  test('Can query mastered characters', async () => {
    await loadSnapshot();

    // Note: 's' field is not indexed, so we filter in memory
    const allWords = await db.words.toArray();
    const mastered = allWords.filter(w => w.s >= 0.8);

    expect(mastered.length).toBe(173);
  });

  test('Can clear database', async () => {
    await loadSnapshot();
    expect(await db.words.count()).toBe(1098);

    await clearDatabase();
    expect(await db.words.count()).toBe(0);
    expect(await db.sentences.count()).toBe(0);
  });

  test('Can get specific word mastery', async () => {
    await loadSnapshot();

    // Get first word from snapshot
    const snapshot = getSnapshotData();
    const firstWord = snapshot.words[0];

    const wordMastery = await db.words.get(firstWord.char_id);
    expect(wordMastery).toBeDefined();
    expect(wordMastery!.char_id).toBe(firstWord.char_id);
    expect(wordMastery!.s).toBe(firstWord.s);
  });

  test('Can get specific sentence progress', async () => {
    await loadSnapshot();

    const snapshot = getSnapshotData();
    const firstSentence = snapshot.sentences[0];

    const sentenceProgress = await db.sentences.get(firstSentence.sid);
    expect(sentenceProgress).toBeDefined();
    expect(sentenceProgress!.sid).toBe(firstSentence.sid);
    expect(sentenceProgress!.ewma_pass).toBe(firstSentence.ewma_pass);
  });
});

describe('Character Mastery Helpers', () => {
  test('getCharacterIdsByMastery returns correct buckets', () => {
    const { unknown, knownButNotMastered, mastered } = getCharacterIdsByMastery();

    // Check counts
    expect(unknown.length).toBe(725);
    expect(knownButNotMastered.length).toBe(200);
    expect(mastered.length).toBe(173);

    // All should be arrays of numbers
    expect(unknown.every(id => typeof id === 'number')).toBe(true);
    expect(knownButNotMastered.every(id => typeof id === 'number')).toBe(true);
    expect(mastered.every(id => typeof id === 'number')).toBe(true);

    // Should have no overlaps
    const unknownSet = new Set(unknown);
    const knownSet = new Set(knownButNotMastered);
    const masteredSet = new Set(mastered);

    expect(unknown.filter(id => knownSet.has(id)).length).toBe(0);
    expect(unknown.filter(id => masteredSet.has(id)).length).toBe(0);
    expect(knownButNotMastered.filter(id => masteredSet.has(id)).length).toBe(0);
  });
});

/**
 * TODO: Future NSS Integration Tests
 *
 * To add NSS algorithm tests, we need:
 * 1. Small test corpus fixture (100 sentences, not 40MB)
 * 2. Mock fetch() to return test corpus
 * 3. Mock loadCharacterMapping() to return test character data
 *
 * Example test structure:
 *
 * describe('NSS Algorithm', () => {
 *   beforeEach(async () => {
 *     await loadSnapshot();
 *     mockFetchWithTestCorpus();
 *   });
 *
 *   test('Generates batch of 8 sentences', async () => {
 *     const result = await generateSentenceBatch(testCorpus, 'simplified', '1-2');
 *     expect(result.sentences).toHaveLength(8);
 *   });
 *
 *   test('Respects script filter', async () => {
 *     const result = await generateSentenceBatch(testCorpus, 'simplified', '1-2');
 *     // Verify all sentences are simplified or neutral
 *   });
 * });
 */
