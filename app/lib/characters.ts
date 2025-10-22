/**
 * Character type detection utilities and character ID mapping
 */

// ============================================================================
// CHARACTER ID MAPPING
// ============================================================================

let charToIdMap: Map<string, number> | null = null;
let charToPinyinsMap: Map<string, string[]> | null = null;

/**
 * Load character ID and pinyin mapping from CSV
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
  charToPinyinsMap = new Map();

  // Skip header line
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Parse CSV line: id,char,codepoint,pinyins,...
    // Use proper CSV parsing to handle quoted fields
    const fields = parseCSVLine(line);
    if (fields.length >= 4) {
      const id = parseInt(fields[0], 10);
      const char = fields[1];
      const pinyinsStr = fields[3]; // pinyins column

      charToIdMap.set(char, id);

      // Parse pinyins: "lè(283)|yuè(54)|le4|yue4" → ["lè(283)", "yuè(54)", "le4", "yue4"]
      if (pinyinsStr && pinyinsStr.trim()) {
        const pinyinsList = pinyinsStr.split('|').map(p => p.trim()).filter(p => p);
        charToPinyinsMap.set(char, pinyinsList);
      }
    }
  }

  if (process.env.NODE_ENV === 'development') {
    console.log(`✓ Cached ${charToIdMap.size} character mappings in memory`);
    console.log(`✓ Cached ${charToPinyinsMap.size} pinyin mappings in memory`);
  }
  return charToIdMap;
}

/**
 * Simple CSV line parser that handles quoted fields
 */
function parseCSVLine(line: string): string[] {
  const fields: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  fields.push(current); // Add last field

  return fields;
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

/**
 * Get all valid pinyins for a character from character_set
 * Returns empty array for non-Chinese characters or if character not found
 *
 * Format: ["lè(283)", "yuè(54)", "le4", "yue4"]
 * Note: May include frequency data like "lè(283)" - caller should strip if needed
 */
export function getValidPinyins(char: string): string[] {
  if (!charToPinyinsMap) {
    throw new Error('Character mapping not loaded. Call loadCharacterMapping() first.');
  }
  return charToPinyinsMap.get(char) ?? [];
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
