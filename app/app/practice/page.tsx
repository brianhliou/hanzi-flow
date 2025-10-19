'use client';

import { useState, useEffect, useRef } from 'react';
import type { Sentence, PracticeState } from '@/lib/types';
import { loadSentences } from '@/lib/sentences';
import { checkPinyin, calculateScore } from '@/lib/scoring';
import { convertToneNumbers } from '@/lib/pinyin';
import { getCharType } from '@/lib/characters';

export default function PracticePage() {
  const [sentences, setSentences] = useState<Sentence[]>([]);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<PracticeState>({
    currentSentenceIndex: 0,
    currentCharIndex: 0,
    userInputs: [],
    results: [],
    score: { correct: 0, total: 0 },
  });
  const [currentInput, setCurrentInput] = useState('');
  const [showResult, setShowResult] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load sentences on mount
  useEffect(() => {
    loadSentences()
      .then((data) => {
        setSentences(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load sentences:', error);
        setLoading(false);
      });
  }, []);

  const currentSentence = sentences[state.currentSentenceIndex];
  const currentChar = currentSentence?.chars[state.currentCharIndex];
  const finishedCurrentSentence =
    currentSentence && state.currentCharIndex >= currentSentence.chars.length;

  // Determine current character type
  const currentCharType = currentChar
    ? getCharType(currentChar.char, currentChar.pinyin)
    : 'chinese';

  // Auto-skip non-Chinese characters (alphanumeric and punctuation)
  useEffect(() => {
    if (!currentChar || finishedCurrentSentence) return;

    if (currentCharType !== 'chinese') {
      // Auto-skip after brief delay so user sees the character
      setTimeout(() => {
        setState((prev) => ({
          ...prev,
          currentCharIndex: prev.currentCharIndex + 1,
        }));
        // Restore focus after auto-skip
        setTimeout(() => inputRef.current?.focus(), 0);
      }, 200);
    }
  }, [state.currentCharIndex, currentChar, currentCharType, finishedCurrentSentence]);

  const handleSubmit = () => {
    if (!currentChar) return;

    // Handle based on character type
    if (currentCharType === 'chinese') {
      // Chinese character - validate pinyin
      if (!currentInput.trim()) return;

      const isCorrect = checkPinyin(currentInput, currentChar.pinyin);

      setState((prev) => ({
        ...prev,
        userInputs: [...prev.userInputs, currentInput],
        results: [...prev.results, isCorrect],
        currentCharIndex: prev.currentCharIndex + 1,
        score: {
          correct: prev.score.correct + (isCorrect ? 1 : 0),
          total: prev.score.total + 1,
        },
      }));

      setCurrentInput('');
    } else {
      // Alphanumeric or punctuation - just advance (no validation)
      setState((prev) => ({
        ...prev,
        currentCharIndex: prev.currentCharIndex + 1,
      }));
    }

    setShowResult(false);

    // Focus input for next character
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const nextSentence = () => {
    if (state.currentSentenceIndex < sentences.length - 1) {
      setState({
        currentSentenceIndex: state.currentSentenceIndex + 1,
        currentCharIndex: 0,
        userInputs: [],
        results: [],
        score: state.score, // Keep cumulative score
      });
      setCurrentInput('');
      setShowResult(false);
    }
  };

  // Add global key listener for advancing to next sentence
  useEffect(() => {
    const handleGlobalKeyPress = (e: KeyboardEvent) => {
      // Only handle Space/Enter when sentence is complete
      if (finishedCurrentSentence && (e.key === ' ' || e.key === 'Enter')) {
        e.preventDefault();
        nextSentence();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyPress);
    return () => window.removeEventListener('keydown', handleGlobalKeyPress);
  }, [finishedCurrentSentence, state.currentSentenceIndex, sentences.length]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl">Loading sentences...</p>
      </div>
    );
  }

  if (!currentSentence) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8">
        <h2 className="text-2xl font-bold mb-4">All Done!</h2>
        <p className="text-xl mb-2">
          Final Score: {state.score.correct} / {state.score.total}
        </p>
        <p className="text-lg text-gray-600">
          {calculateScore(state.score.correct, state.score.total)}% accuracy
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Sticky Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-8 py-4 z-10">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <p className="text-gray-600 dark:text-gray-400">
            Sentence {state.currentSentenceIndex + 1} of {sentences.length}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            Score: {state.score.correct} / {state.score.total}
            {state.score.total > 0 &&
              ` (${calculateScore(state.score.correct, state.score.total)}%)`}
          </p>
        </div>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-8">
        <div className="w-full max-w-4xl">
          {/* Sentence Display with inline feedback */}
          <div className="text-center">
            <div style={{ fontSize: '72px', lineHeight: '1.3' }}>
              {currentSentence.chars.map((char, index) => {
                // Show feedback for completed characters (index < currentCharIndex)
                const hasBeenAnswered = index < state.currentCharIndex;
                const isCurrent = index === state.currentCharIndex;
                const charType = getCharType(char.char, char.pinyin);

                // Calculate result index: count Chinese characters before this one
                const chineseCharsBeforeThis = currentSentence.chars
                  .slice(0, index)
                  .filter(c => getCharType(c.char, c.pinyin) === 'chinese').length;

                const isCorrect = hasBeenAnswered && charType === 'chinese'
                  ? state.results[chineseCharsBeforeThis]
                  : null;

                return (
                  <span
                    key={index}
                    className="inline-block transition-all"
                    style={{
                      marginRight: '10px',
                      marginBottom: '6px',
                      verticalAlign: 'top',
                    }}
                  >
                    <span
                      className={`block ${
                        isCurrent
                          ? 'text-blue-600'             // Current character - always blue
                          : hasBeenAnswered && charType === 'chinese'
                          ? isCorrect
                            ? 'text-green-600'          // Correct answer - green
                            : 'text-red-600'            // Wrong answer - red
                          : hasBeenAnswered && charType === 'alphanumeric'
                          ? 'text-gray-600'             // Completed alphanumeric - gray
                          : hasBeenAnswered && charType === 'punctuation'
                          ? 'text-gray-400'             // Completed punctuation - light gray
                          : 'text-gray-900'             // Not reached yet - dark
                      }`}
                      style={{
                        transform: isCurrent ? 'scale(1.05)' : 'scale(1)',
                      }}
                    >
                      {char.char}
                    </span>
                    {/* Always reserve space for feedback to prevent layout shift */}
                    <span
                      className="block text-center mt-1"
                      style={{ fontSize: '16px', height: '20px', lineHeight: '20px' }}
                    >
                      {hasBeenAnswered && (
                        <span className="text-gray-600">{convertToneNumbers(char.pinyin)}</span>
                      )}
                    </span>
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Sticky Footer - Input/Button */}
      <div className="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-8 py-6">
        <div className="max-w-lg mx-auto" style={{ height: '68px' }}>
          {!finishedCurrentSentence ? (
            <input
              ref={inputRef}
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full h-full text-2xl text-center border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
              placeholder={state.currentCharIndex === 0 ? "Type pinyin" : ""}
              autoFocus
              style={{ padding: '0 24px' }}
            />
          ) : (
            <button
              onClick={nextSentence}
              className="w-full h-full text-2xl text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ padding: '0 24px' }}
            >
              Next Sentence
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
