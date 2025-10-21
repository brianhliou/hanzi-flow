/**
 * Character type detection utilities and character ID mapping
 */

// ============================================================================
// CHARACTER ID MAPPING
// ============================================================================

let charToIdMap: Map<string, number> | null = null;

/**
 * Load character ID mapping from CSV
 */
export async function loadCharacterMapping(): Promise<Map<string, number>> {
  // Return from cache if available
  if (charToIdMap) {
    if (process.env.NODE_ENV === 'development') {
      console.log('📦 Returning character mapping from in-memory cache');
    }
    return charToIdMap;
  }

  if (process.env.NODE_ENV === 'development') {
    console.log('🌐 Loading character mapping from network...');
  }
  const response = await fetch('/data/character_set/chinese_characters.csv');
  if (!response.ok) {
    throw new Error('Failed to load character mapping');
  }

  const csvText = await response.text();
  const lines = csvText.split('\n');

  charToIdMap = new Map();

  // Skip header line
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Parse CSV line: id,char,script_type,...
    const match = line.match(/^(\d+),([^,]+),/);
    if (match) {
      const id = parseInt(match[1], 10);
      const char = match[2];
      charToIdMap.set(char, id);
    }
  }

  if (process.env.NODE_ENV === 'development') {
    console.log(`✓ Cached ${charToIdMap.size} character mappings in memory`);
  }
  return charToIdMap;
}

/**
 * Get character ID for a given character
 * Returns null for non-Chinese characters (punctuation, etc.)
 */
export function getCharId(char: string): number | null {
  if (!charToIdMap) {
    throw new Error('Character mapping not loaded. Call loadCharacterMapping() first.');
  }
  return charToIdMap.get(char) ?? null;
}

// ============================================================================
// CHARACTER TYPE DETECTION
// ============================================================================

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
