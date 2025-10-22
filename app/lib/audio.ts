/**
 * Audio playback utilities for pinyin pronunciation
 */

// Global audio cache - persists across page navigation within session
const audioCache = new Map<string, HTMLAudioElement>();

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

  try {
    // Try to get from cache first
    let audio = audioCache.get(normalizedPinyin);

    if (!audio) {
      // Not cached, create new and cache it
      const audioPath = `/data/audio/${normalizedPinyin}.ogg`;
      audio = new Audio(audioPath);
      audioCache.set(normalizedPinyin, audio);
    }

    // Clone the audio element so we can play multiple times simultaneously
    const playableAudio = audio.cloneNode(true) as HTMLAudioElement;

    // Return a promise that resolves when audio finishes
    return new Promise((resolve, reject) => {
      playableAudio.onended = () => resolve();
      playableAudio.onerror = () => {
        console.warn(`Audio file not found: ${normalizedPinyin}.ogg`);
        reject(new Error(`Audio file not found: ${normalizedPinyin}.ogg`));
      };

      playableAudio.play().catch((error) => {
        console.warn(`Failed to play audio: ${normalizedPinyin}.ogg`, error);
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

  // Check cache first - don't preload if already cached
  if (audioCache.has(normalizedPinyin)) {
    return;
  }

  const audioPath = `/data/audio/${normalizedPinyin}.ogg`;
  const audio = new Audio();
  audio.preload = 'auto';
  audio.src = audioPath;

  // Store in cache for future use
  audioCache.set(normalizedPinyin, audio);
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
