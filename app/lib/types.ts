export interface CharPinyin {
  char: string;
  pinyin: string;
  char_id: number | null;  // Character ID from chinese_characters.csv (null for non-Chinese)
}

export interface Sentence {
  id: number;
  sentence: string;
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
