/**
 * Tone mark mapping for each vowel (index 0-4 for neutral, tone1-4)
 */
const TONE_MARKS: Record<string, string[]> = {
  'a': ['a', 'ā', 'á', 'ǎ', 'à'],
  'e': ['e', 'ē', 'é', 'ě', 'è'],
  'i': ['i', 'ī', 'í', 'ǐ', 'ì'],
  'o': ['o', 'ō', 'ó', 'ǒ', 'ò'],
  'u': ['u', 'ū', 'ú', 'ǔ', 'ù'],
  'ü': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ'],
  'v': ['v', 'ǖ', 'ǘ', 'ǚ', 'ǜ'], // v is alternative for ü
};

/**
 * Convert pinyin with tone numbers to tone marks.
 *
 * Rules for tone placement:
 * 1. If 'a' or 'e' exists, tone goes there
 * 2. Otherwise, tone goes on 'o'
 * 3. If no a/e/o, tone goes on last vowel (handles "iu" -> "iú")
 *
 * Examples:
 * - "wo3" -> "wǒ"
 * - "ni3" -> "nǐ"
 * - "shi4" -> "shì"
 * - "liu2" -> "liú" (tone on 'u' not 'i')
 * - "nv3" -> "nǚ"
 */
export function convertToneNumbers(pinyin: string): string {
  if (!pinyin) return '';

  // Extract tone number (default to 0 for neutral)
  const match = pinyin.match(/([a-züv]+)([1-4])?$/i);
  if (!match) return pinyin;

  const [, syllable, toneStr] = match;
  const tone = parseInt(toneStr || '0', 10);

  // If no tone or invalid, return as-is
  if (tone < 0 || tone > 4) return pinyin;

  const lower = syllable.toLowerCase();

  // Find which vowel gets the tone mark
  let targetIndex = -1;

  // Rule 1: 'a' or 'e' gets priority
  if (lower.includes('a')) {
    targetIndex = lower.indexOf('a');
  } else if (lower.includes('e')) {
    targetIndex = lower.indexOf('e');
  } else if (lower.includes('o')) {
    targetIndex = lower.indexOf('o');
  } else {
    // Rule 3: Last vowel (handles "iu" case)
    const vowels = ['i', 'u', 'ü', 'v'];
    for (let i = lower.length - 1; i >= 0; i--) {
      if (vowels.includes(lower[i])) {
        targetIndex = i;
        break;
      }
    }
  }

  if (targetIndex === -1) return pinyin; // No vowel found

  // Replace the target vowel with its tone-marked version
  const targetVowel = lower[targetIndex];
  const toneMarks = TONE_MARKS[targetVowel];

  if (!toneMarks) return pinyin;

  const markedVowel = toneMarks[tone];
  const result = lower.substring(0, targetIndex) + markedVowel + lower.substring(targetIndex + 1);

  return result;
}
