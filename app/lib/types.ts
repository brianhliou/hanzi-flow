export interface CharPinyin {
  char: string;
  pinyin: string;
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
