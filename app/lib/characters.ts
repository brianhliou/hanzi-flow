/**
 * Character type detection utilities
 */

/**
 * Check if a string is punctuation.
 * Common Chinese and English punctuation marks.
 */
export function isPunctuation(str: string): boolean {
  if (!str) return false;

  const punctuationMarks = new Set([
    '，', '。', '！', '？', '：', '；', '、',  // Chinese
    ',', '.', '!', '?', ':', ';',              // English
    '\u201C', '\u201D', '\u2018', '\u2019', '「', '」', '『', '』', // Quotes
    '（', '）', '(', ')',                       // Parentheses
    '—', '…', '·', '"'                         // Others
  ]);

  return punctuationMarks.has(str);
}

/**
 * Check if a string is alphanumeric (numbers, letters).
 * Includes both half-width and full-width characters.
 */
export function isAlphanumeric(str: string): boolean {
  if (!str) return false;

  // Match letters (a-z, A-Z), numbers (0-9), or full-width equivalents
  // Full-width: U+FF00-U+FFEF
  const alphanumericRegex = /^[a-zA-Z0-9\uFF00-\uFFEF]+$/;

  return alphanumericRegex.test(str);
}

/**
 * Determine the type of a character/token.
 */
export type CharType = 'chinese' | 'alphanumeric' | 'punctuation';

export function getCharType(char: string, pinyin?: string): CharType {
  // If has pinyin, it's Chinese
  if (pinyin && pinyin.trim() !== '') {
    return 'chinese';
  }

  // No pinyin - check if punctuation or alphanumeric
  if (isPunctuation(char)) {
    return 'punctuation';
  }

  if (isAlphanumeric(char)) {
    return 'alphanumeric';
  }

  // Default to punctuation for unknown non-Chinese chars
  return 'punctuation';
}
