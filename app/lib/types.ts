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
