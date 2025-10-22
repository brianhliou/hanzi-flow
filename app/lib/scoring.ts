/**
 * Pinyin Input Validation & Scoring
 *
 * Validates user pinyin input against expected character readings, handles
 * tone marks, fuzzy matching (v→ü), and calculates sentence-level accuracy.
 *
 * Features:
 * - Tone-aware validation (with/without tone numbers)
 * - Fuzzy matching for common input variations (v→ü, case-insensitive)
 * - Per-character correctness tracking
 * - Sentence-level scoring (average of unique character correctness)
 * - Validates against character_set for alternative pronunciations
 *
 * Used by: practice/page.tsx for real-time input validation
 */

import { getValidPinyins } from './characters';
import { convertToneMarksToNumbers } from './pinyin';

/**
 * Normalize pinyin input for comparison.
 * Handles variations like:
 * - Case insensitive (NI3 vs ni3)
 * - ü can be typed as v (standard pinyin input convention)
 *   Examples: nü/nv, lü/lv, nüe/nve
 */
export function normalizePinyin(input: string): string {
  return input.toLowerCase().trim().replace(/v/g, 'ü');
}

/**
 * Remove tone numbers from pinyin.
 * Example: "shi4" -> "shi", "wo3" -> "wo", "de0" -> "de"
 */
export function removeTones(pinyin: string): string {
  return pinyin.replace(/[0-4]/g, '');
}

/**
 * Strip frequency data from pinyin
 * Example: "lè(283)" → "lè", "shei2" → "shei2"
 */
function stripFrequency(pinyin: string): string {
  return pinyin.replace(/\(\d+\)/, '');
}

/**
 * Check if user's pinyin input matches any valid pronunciation for the character.
 * Validates against character_set to accept alternative pronunciations.
 *
 * Accepts:
 * - Exact match with correct tone (shi4 = shi4)
 * - Toneless input (shi = shi4)
 * - Alternative valid pronunciations (shei2 for 谁, de for 地 when used as particle)
 * Rejects:
 * - Wrong tone (shi2 ≠ shi4) if tone is provided
 *
 * @param userInput - User's pinyin input
 * @param expected - Expected pinyin from sentence data (may be outdated)
 * @param char - The character being validated (optional, for character_set lookup)
 */
export function checkPinyin(userInput: string, expected: string, char?: string): boolean {
  const normalized = normalizePinyin(userInput);

  // Get all valid pinyins from character_set if character is provided
  let validPinyins: string[] = [];
  if (char) {
    try {
      const rawPinyins = getValidPinyins(char);
      // Strip frequency data, convert tone marks to numbers, and normalize
      // ["lè(283)", "yuè(54)", "zhèi"] → ["le4", "yue4", "zhei4"]
      validPinyins = rawPinyins.map(p => {
        const stripped = stripFrequency(p);
        const withToneNumbers = convertToneMarksToNumbers(stripped);
        return normalizePinyin(withToneNumbers);
      });
    } catch (e) {
      // Character mapping not loaded, fall back to sentence-level pinyin only
      validPinyins = [];
    }
  }

  // Always include the expected pinyin from sentence data
  const normalizedExpected = normalizePinyin(expected);
  if (normalizedExpected && !validPinyins.includes(normalizedExpected)) {
    validPinyins.push(normalizedExpected);
  }

  // Check if user provided a tone number
  const userHasTone = /[1-4]/.test(normalized);

  // Try exact match against all valid pinyins
  if (validPinyins.some(p => p === normalized)) {
    return true;
  }

  if (userHasTone) {
    // User typed a tone, so it must match exactly (already failed above)
    return false; // Wrong tone - reject!
  }

  // User didn't type a tone - accept if base pinyin matches any valid pronunciation
  const normalizedNoTone = removeTones(normalized);

  return validPinyins.some(p => removeTones(p) === normalizedNoTone);
}

/**
 * Calculate score percentage.
 */
export function calculateScore(correct: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((correct / total) * 100);
}
