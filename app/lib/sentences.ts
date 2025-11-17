import type { Sentence } from './types';
import { isDebugMode } from './debug';

/**
 * Corpus metadata from sentences JSON
 */
export interface SentenceMetadata {
  totalSentences: number;
  totalCharsInCorpus: number;
  generatedAt: string;
  version: string;
}

// In-memory cache - persists across route navigation but not page refresh
let cachedSentences: Sentence[] | null = null;
let cachedMetadata: SentenceMetadata | null = null;

/**
 * Get corpus metadata (cached)
 */
export async function getCorpusMetadata(): Promise<SentenceMetadata> {
  // Load sentences if not cached (will populate metadata)
  if (!cachedMetadata) {
    await loadSentences();
  }

  return cachedMetadata!;
}

export async function loadSentences(): Promise<Sentence[]> {
  // Return from cache if available
  if (cachedSentences) {
    if (isDebugMode()) {
      console.log('📦 Returning sentences from in-memory cache');
    }
    return cachedSentences;
  }

  if (isDebugMode()) {
    console.log('🌐 Loading sentences from network...');
  }
  const response = await fetch('/data/sentences/sentences.json');
  if (!response.ok) {
    throw new Error('Failed to load sentences');
  }
  const data = await response.json();

  // Extract metadata and sentences from new format
  const metadata: SentenceMetadata = data.metadata;
  const sentences: Sentence[] = data.sentences;

  // Cache metadata
  cachedMetadata = metadata;

  // TEMP: Prioritize test sentences with alphanumeric/punctuation - REMOVE THIS BLOCK LATER
  // Sentences to load first (in order)
  const prioritySentences = [
    "今天是６月１８号，也是Muiriel的生日！",
    "生日快乐，Muiriel！",
    "Muiriel现在20岁了。",
    "\"密码是\"\"Muiriel\"\"。\""
  ];

  // Extract priority sentences from the full list
  const priorityItems: Sentence[] = [];
  const prioritySet = new Set(prioritySentences);

  prioritySentences.forEach(targetSentence => {
    const found = sentences.find((s: Sentence) => s.sentence === targetSentence);
    if (found) {
      priorityItems.push(found);
    }
  });

  // Remove priority sentences from main list to avoid duplicates
  const remainingSentences = sentences.filter((s: Sentence) => !prioritySet.has(s.sentence));

  const result = [...priorityItems, ...remainingSentences];
  // END TEMP BLOCK

  // Store in cache before returning
  cachedSentences = result;
  if (isDebugMode()) {
    console.log(`✓ Cached ${result.length} sentences in memory`);
  }

  return result;
}
