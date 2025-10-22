export interface CharPinyin {
  char: string;
  pinyin: string | null;  // null for non-Chinese characters (punctuation, etc.)
}

export interface Sentence {
  id: number;
  sentence: string;
  english_translation: string;
  script_type: 'simplified' | 'traditional' | 'neutral' | 'ambiguous';
  chars: CharPinyin[];
  hskLevel?: string;  // HSK level: "1"-"6", "7-9", or undefined for unclassified sentences
}

export interface PracticeState {
  currentSentenceIndex: number;
  currentCharIndex: number;
  userInputs: string[];
  results: boolean[];
  score: {
    correct: number;
    total: number;
  };
}

// HSK filter preference - cumulative (e.g., "1-3" includes levels 1, 2, and 3)
// "1-beyond" includes all HSK levels 1-9 plus beyond-hsk category
export type HskFilter = '1' | '1-2' | '1-3' | '1-4' | '1-5' | '1-6' | '1-9' | '1-beyond';
