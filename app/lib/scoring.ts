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
 * Accepts both with tones (shi4) and without tones (shi).
 */
export function checkPinyin(userInput: string, expected: string): boolean {
  const normalized = normalizePinyin(userInput);
  const normalizedExpected = normalizePinyin(expected);

  // Exact match (with tones)
  if (normalized === normalizedExpected) {
    return true;
  }

  // Match without tones
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
