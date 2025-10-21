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
 * Example: "shi4" -> "shi", "wo3" -> "wo"
 */
export function removeTones(pinyin: string): string {
  return pinyin.replace(/[1-4]/g, '');
}

/**
 * Check if user's pinyin input matches the expected pinyin.
 * Accepts:
 * - Exact match with correct tone (shi4 = shi4)
 * - Toneless input (shi = shi4)
 * Rejects:
 * - Wrong tone (shi2 ≠ shi4)
 */
export function checkPinyin(userInput: string, expected: string): boolean {
  const normalized = normalizePinyin(userInput);
  const normalizedExpected = normalizePinyin(expected);

  // Exact match (with tones)
  if (normalized === normalizedExpected) {
    return true;
  }

  // Check if user provided a tone number
  const userHasTone = /[1-4]/.test(normalized);

  if (userHasTone) {
    // User typed a tone, so it must match exactly (already failed above)
    return false; // Wrong tone - reject!
  }

  // User didn't type a tone - accept if base pinyin matches
  const normalizedNoTone = removeTones(normalized);
  const expectedNoTone = removeTones(normalizedExpected);

  return normalizedNoTone === expectedNoTone;
}

/**
 * Calculate score percentage.
 */
export function calculateScore(correct: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((correct / total) * 100);
}
