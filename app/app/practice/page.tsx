'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import type { Sentence, PracticeState } from '@/lib/types';
import { loadSentences } from '@/lib/sentences';
import { checkPinyin, calculateScore } from '@/lib/scoring';
import { convertToneNumbers } from '@/lib/pinyin';
import { getCharType } from '@/lib/characters';
import { playPinyinAudio } from '@/lib/audio';
import { recordSentenceAttempt, recordSentenceProgress } from '@/lib/mastery';

type ScriptFilter = 'simplified' | 'traditional' | 'mixed';

export default function PracticePage() {
  const searchParams = useSearchParams();
  const scriptParam = searchParams.get('script') as ScriptFilter | null;
  const scriptFilter = scriptParam && ['simplified', 'traditional', 'mixed'].includes(scriptParam)
    ? scriptParam
    : 'mixed';

  const [allSentences, setAllSentences] = useState<Sentence[]>([]);
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
  const [isFirstAttempt, setIsFirstAttempt] = useState(true);
  const [currentCharWasWrong, setCurrentCharWasWrong] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load sentences on mount
  useEffect(() => {
    loadSentences()
      .then((data) => {
        setAllSentences(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load sentences:', error);
        setLoading(false);
      });
  }, []);

  // Filter sentences based on script type
  useEffect(() => {
    if (allSentences.length === 0) return;

    let filtered: Sentence[];

    if (scriptFilter === 'simplified') {
      // Simplified: include simplified and neutral, exclude ambiguous
      filtered = allSentences.filter(
        s => s.script_type === 'simplified' || s.script_type === 'neutral'
      );
    } else if (scriptFilter === 'traditional') {
      // Traditional: include traditional and neutral, exclude ambiguous
      filtered = allSentences.filter(
        s => s.script_type === 'traditional' || s.script_type === 'neutral'
      );
    } else {
      // Mixed: include all except ambiguous
      filtered = allSentences.filter(s => s.script_type !== 'ambiguous');
    }

    setSentences(filtered);

    // Reset practice state when filter changes
    setState({
      currentSentenceIndex: 0,
      currentCharIndex: 0,
      userInputs: [],
      results: [],
      score: { correct: 0, total: 0 },
    });
    setCurrentInput('');
    setIsFirstAttempt(true);
    setCurrentCharWasWrong(false);
  }, [allSentences, scriptFilter]);

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

  // Record mastery data when sentence is completed
  useEffect(() => {
    if (!finishedCurrentSentence || !currentSentence) return;

    // Build attempts array: only Chinese characters with char_id
    const attempts = currentSentence.chars
      .map((char, idx) => {
        // Only process Chinese characters (those with char_id)
        if (char.char_id === null) return null;

        // Find the index of this character in the results array
        // Results array only contains results for Chinese characters
        const chineseCharsBeforeThis = currentSentence.chars
          .slice(0, idx)
          .filter((c) => c.char_id !== null).length;

        return {
          char_id: char.char_id,
          correct: state.results[chineseCharsBeforeThis] ?? false,
        };
      })
      .filter((attempt): attempt is { char_id: number; correct: boolean } =>
        attempt !== null
      );

    // Determine if sentence passed: all Chinese characters correct on first attempt
    const passed = state.results.every((result) => result === true);

    // Record both word-level and sentence-level progress to IndexedDB (async but don't block UI)
    recordSentenceAttempt(attempts);
    recordSentenceProgress(currentSentence.id, passed);
  }, [finishedCurrentSentence, currentSentence, state.results]);

  const handleSubmit = () => {
    if (!currentChar) return;

    // Handle based on character type
    if (currentCharType === 'chinese') {
      // Chinese character - validate pinyin
      if (!currentInput.trim()) return;

      const isCorrect = checkPinyin(currentInput, currentChar.pinyin);

      if (isCorrect) {
        // Correct answer - advance to next character
        setState((prev) => ({
          ...prev,
          userInputs: [...prev.userInputs, currentInput],
          results: [...prev.results, currentCharWasWrong ? false : true], // Keep result from first attempt
          currentCharIndex: prev.currentCharIndex + 1,
          score: {
            correct: prev.score.correct + (isFirstAttempt ? 1 : 0), // Only count first attempt
            total: prev.score.total + (isFirstAttempt ? 1 : 0),
          },
        }));

        setCurrentInput('');
        setIsFirstAttempt(true); // Reset for next character
        setCurrentCharWasWrong(false); // Reset for next character
      } else {
        // Wrong answer - don't advance, let user retry
        if (isFirstAttempt) {
          // Only record score on first attempt
          setState((prev) => ({
            ...prev,
            userInputs: [...prev.userInputs, currentInput],
            score: {
              correct: prev.score.correct,
              total: prev.score.total + 1,
            },
          }));
          setIsFirstAttempt(false); // Mark that first attempt was made
          setCurrentCharWasWrong(true); // Mark for visual feedback
        }

        // Play audio for correct pronunciation on every wrong attempt
        if (currentChar.pinyin) {
          playPinyinAudio(currentChar.pinyin).catch((error) => {
            // Silently handle audio errors - don't block user progress
            console.warn('Audio playback failed:', error);
          });
        }

        // Clear input but stay on same character
        setCurrentInput('');
      }
    } else {
      // Alphanumeric or punctuation - just advance (no validation)
      setState((prev) => ({
        ...prev,
        currentCharIndex: prev.currentCharIndex + 1,
      }));
      setIsFirstAttempt(true); // Reset for next character
      setCurrentCharWasWrong(false); // Reset for next character
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
    // Advance to next sentence (recording happens in useEffect when sentence completes)
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
      setIsFirstAttempt(true); // Reset for new sentence
      setCurrentCharWasWrong(false); // Reset for new sentence
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
          <div className="flex items-center gap-4">
            <p className="text-gray-600 dark:text-gray-400">
              Score: {state.score.correct} / {state.score.total}
              {state.score.total > 0 &&
                ` (${calculateScore(state.score.correct, state.score.total)}%)`}
            </p>
            <Link
              href="/stats"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Stats
            </Link>
          </div>
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
                        isCurrent && currentCharWasWrong
                          ? 'text-red-600'              // Current character but wrong - red
                          : isCurrent
                          ? 'text-blue-600'             // Current character - blue
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
