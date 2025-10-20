/**
 * Audio playback utilities for pinyin pronunciation
 */

/**
 * Normalize pinyin to ensure neutral tone (empty string) is converted to tone 0.
 * Audio files use tone number 0 for neutral tone.
 *
 * @param pinyin - Pinyin with tone number (e.g., "wo3", "shi4") or empty for neutral
 * @returns Normalized pinyin (e.g., "wo3", "de0")
 */
function normalizePinyin(pinyin: string): string {
  if (!pinyin || pinyin.trim() === '') {
    return '';
  }

  // Check if pinyin already has a tone number (0-4)
  const hasToneNumber = /[0-4]$/.test(pinyin);

  if (hasToneNumber) {
    return pinyin;
  }

  // No tone number - treat as neutral tone (0)
  return `${pinyin}0`;
}

/**
 * Play audio for a given pinyin syllable with tone number.
 *
 * @param pinyin - Pinyin with tone number (e.g., "wo3", "shi4") or empty for neutral tone
 * @returns Promise that resolves when audio finishes playing
 */
export async function playPinyinAudio(pinyin: string): Promise<void> {
  const normalizedPinyin = normalizePinyin(pinyin);

  if (!normalizedPinyin) {
    return;
  }

  // Construct audio file path
  const audioPath = `/data/audio/${normalizedPinyin}.ogg`;

  try {
    const audio = new Audio(audioPath);

    // Return a promise that resolves when audio finishes
    return new Promise((resolve, reject) => {
      audio.onended = () => resolve();
      audio.onerror = () => {
        console.warn(`Audio file not found: ${audioPath}`);
        reject(new Error(`Audio file not found: ${audioPath}`));
      };

      audio.play().catch((error) => {
        console.warn(`Failed to play audio: ${audioPath}`, error);
        reject(error);
      });
    });
  } catch (error) {
    console.warn(`Error playing audio for ${pinyin}:`, error);
    throw error;
  }
}

/**
 * Preload audio file for better performance.
 *
 * @param pinyin - Pinyin with tone number or empty for neutral
 */
export function preloadPinyinAudio(pinyin: string): void {
  const normalizedPinyin = normalizePinyin(pinyin);

  if (!normalizedPinyin) {
    return;
  }

  const audioPath = `/data/audio/${normalizedPinyin}.ogg`;
  const audio = new Audio();
  audio.preload = 'auto';
  audio.src = audioPath;
}

/**
 * Preload multiple audio files.
 *
 * @param pinyinList - Array of pinyin syllables to preload
 */
export function preloadMultiplePinyinAudio(pinyinList: string[]): void {
  pinyinList.forEach(pinyin => {
    preloadPinyinAudio(pinyin);
  });
}
