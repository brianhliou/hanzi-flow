'use client';

import { useState, useEffect, useRef } from 'react';
import type { Sentence, PracticeState } from '@/lib/types';
import { loadSentences } from '@/lib/sentences';
import { checkPinyin, calculateScore } from '@/lib/scoring';
import { convertToneNumbers } from '@/lib/pinyin';
import { getCharType, loadCharacterMapping, getCharId } from '@/lib/characters';
import { playPinyinAudio } from '@/lib/audio';
import { recordSentenceAttempt, recordSentenceProgress } from '@/lib/mastery';
import { getNextSentence } from '@/lib/sentence-selection';
import Navigation from '@/components/Navigation';

type ScriptFilter = 'simplified' | 'traditional' | 'mixed';

const SCRIPT_PREFERENCE_KEY = 'hanzi-flow-script-preference';
const AUDIO_ENABLED_KEY = 'hanzi-flow-audio-enabled';

export default function PracticePage() {
  const [scriptFilter, setScriptFilter] = useState<ScriptFilter | null>(null);
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [allSentences, setAllSentences] = useState<Sentence[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentSentence, setCurrentSentence] = useState<Sentence | null>(null);
  const [state, setState] = useState<PracticeState>({
    currentSentenceIndex: 0,  // Kept for compatibility but unused
    currentCharIndex: 0,
    userInputs: [],
    results: [],
    score: { correct: 0, total: 0 },
  });
  const [currentInput, setCurrentInput] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [isFirstAttempt, setIsFirstAttempt] = useState(true);
  const [currentCharWasWrong, setCurrentCharWasWrong] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [showTranslation, setShowTranslation] = useState(false);
  const [exceededRetryIndices, setExceededRetryIndices] = useState<Set<number>>(new Set());
  const [audioEnabled, setAudioEnabled] = useState<boolean>(true);
  const inputRef = useRef<HTMLInputElement>(null);

  const MAX_RETRIES = 5;

  // Helper function to detect ending punctuation that shouldn't start a line
  const isEndingPunctuation = (char: string): boolean => {
    const endingPunctuationSet = new Set([
      '。', '，', '！', '？', '；', '：',  // Chinese punctuation
      '」', '』', '）', '】', '》', '〉',  // Closing brackets/quotes
      '\u201D', '\u2019',                // Chinese closing quotes (" ')
      '、', '…', '·',                    // Other punctuation
      '.', ',', '!', '?', ';', ':',      // English punctuation
      ')', ']', '}', '"', '\'',          // English closing
    ]);
    return endingPunctuationSet.has(char);
  };

  // Step 1: Load sentences immediately (ignore preference)
  useEffect(() => {
    Promise.all([
      loadSentences(),
      loadCharacterMapping()
    ])
      .then(([sentences]) => {
        setAllSentences(sentences);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load data:', error);
        setLoading(false);
      });
  }, []);

  // Step 2: Check script preference and audio setting after mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const saved = localStorage.getItem(SCRIPT_PREFERENCE_KEY) as ScriptFilter | null;
    if (saved) {
      setScriptFilter(saved);
    } else {
      // No preference set - show modal
      setShowScriptModal(true);
    }

    // Load audio preference (defaults to enabled)
    const savedAudio = localStorage.getItem(AUDIO_ENABLED_KEY);
    setAudioEnabled(savedAudio === null ? true : savedAudio === 'true');
  }, []);

  // Step 3: Get first sentence when both sentences and preference are ready
  useEffect(() => {
    if (allSentences.length === 0) return;  // Wait for sentences
    if (!scriptFilter) return;  // Wait for preference
    if (currentSentence) return;  // Already have a sentence

    // Get first sentence using NSS
    getNextSentence(allSentences, scriptFilter)
      .then((sid) => {
        const sentence = allSentences.find(s => s.id === sid);
        setCurrentSentence(sentence || null);
      })
      .catch((error) => {
        console.error('Failed to get next sentence:', error);
      });
  }, [allSentences, scriptFilter, currentSentence]);
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
        // Only process Chinese characters (those with pinyin)
        if (!char.pinyin) return null;

        // Look up character ID
        const char_id = getCharId(char.char);
        if (char_id === null) return null;

        // Find the index of this character in the results array
        // Results array only contains results for Chinese characters
        const chineseCharsBeforeThis = currentSentence.chars
          .slice(0, idx)
          .filter((c) => c.pinyin !== null).length;

        return {
          char_id,
          correct: state.results[chineseCharsBeforeThis] ?? false,
        };
      })
      .filter((attempt): attempt is { char_id: number; correct: boolean } =>
        attempt !== null
      );

    // Calculate sentence score as average of unique character scores
    // For duplicate characters, use worst outcome (minimum score)
    const charScores = new Map<number, number>();

    for (const attempt of attempts) {
      const existingScore = charScores.get(attempt.char_id);
      const currentScore = attempt.correct ? 1 : 0;

      // For duplicates, keep the minimum (worst outcome)
      if (existingScore === undefined) {
        charScores.set(attempt.char_id, currentScore);
      } else {
        charScores.set(attempt.char_id, Math.min(existingScore, currentScore));
      }
    }

    // Calculate average score across unique characters
    const sentenceScore = charScores.size > 0
      ? Array.from(charScores.values()).reduce((sum, score) => sum + score, 0) / charScores.size
      : 0;

    // Record both word-level and sentence-level progress to IndexedDB (async but don't block UI)
    recordSentenceAttempt(attempts);
    recordSentenceProgress(currentSentence.id, sentenceScore);
  }, [finishedCurrentSentence, currentSentence, state.results]);

  // Auto-reveal translation when sentence is finished
  useEffect(() => {
    if (finishedCurrentSentence) {
      setShowTranslation(true);
    }
  }, [finishedCurrentSentence]);

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
        setRetryCount(0); // Reset retry count for next character
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

        // Increment retry count
        const newRetryCount = retryCount + 1;
        setRetryCount(newRetryCount);

        // Check if max retries reached - auto-advance to next character
        if (newRetryCount >= MAX_RETRIES) {
          // Mark this character as exceeded retry limit (for purple color)
          setExceededRetryIndices((prev) => new Set(prev).add(state.currentCharIndex));

          setState((prev) => ({
            ...prev,
            results: [...prev.results, false], // Mark as wrong
            currentCharIndex: prev.currentCharIndex + 1,
          }));
          setCurrentInput('');
          setRetryCount(0); // Reset for next character
          setIsFirstAttempt(true);
          setCurrentCharWasWrong(false);
          return;
        }

        // Play audio for correct pronunciation on every wrong attempt (if enabled)
        if (audioEnabled && currentChar.pinyin) {
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
      setRetryCount(0); // Reset retry count for next character
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

  const nextSentence = async () => {
    // Get next sentence using NSS (recording happens in useEffect when sentence completes)
    if (!scriptFilter) return;  // Wait for preference to be set

    try {
      const sid = await getNextSentence(allSentences, scriptFilter);
      const sentence = allSentences.find(s => s.id === sid);

      if (sentence) {
        setCurrentSentence(sentence);
        setState({
          currentSentenceIndex: 0,  // Kept for compatibility but unused
          currentCharIndex: 0,
          userInputs: [],
          results: [],
          score: state.score, // Keep cumulative score
        });
        setCurrentInput('');
        setShowResult(false);
        setIsFirstAttempt(true);
        setCurrentCharWasWrong(false);
        setShowTranslation(false); // Reset translation visibility for new sentence
        setExceededRetryIndices(new Set()); // Reset exceeded retry tracking for new sentence
      }
    } catch (error) {
      console.error('Failed to get next sentence:', error);
    }
  };

  const handleScriptSelection = (script: ScriptType) => {
    setScriptFilter(script);
    localStorage.setItem(SCRIPT_PREFERENCE_KEY, script);
    setShowScriptModal(false);
  };

  // Add global key listener for advancing to next sentence
  useEffect(() => {
    const handleGlobalKeyPress = (e: KeyboardEvent) => {
      // Only handle Space/Enter when sentence is complete
      if (finishedCurrentSentence && (e.key === ' ' || e.key === 'Enter')) {
        e.preventDefault();
        nextSentence();  // Async but we don't need to await here
      }
    };

    window.addEventListener('keydown', handleGlobalKeyPress);
    return () => window.removeEventListener('keydown', handleGlobalKeyPress);
  }, [finishedCurrentSentence]);

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl">Loading sentences...</p>
      </div>
    );
  }

  // Show script selection modal if needed (even if no sentence yet)
  if (showScriptModal) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navigation currentPage="practice" />

        {/* First-Run Script Selection Modal */}
        <div className="fixed inset-0 bg-white dark:bg-black bg-opacity-90 dark:bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-lg p-8 max-w-4xl w-full">
            <h2 className="text-2xl font-bold mb-2">Welcome to Hanzi Flow!</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Choose your preferred Chinese script style to get started.
              <br />
              <span className="text-sm">You can change this anytime in Settings.</span>
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Simplified */}
              <button
                onClick={() => handleScriptSelection('simplified')}
                className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-600 dark:hover:border-blue-600 transition-all text-center"
              >
                <div className="text-5xl mb-3">简体</div>
                <div className="font-semibold text-lg">Simplified</div>
              </button>

              {/* Traditional */}
              <button
                onClick={() => handleScriptSelection('traditional')}
                className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-600 dark:hover:border-blue-600 transition-all text-center"
              >
                <div className="text-5xl mb-3">繁體</div>
                <div className="font-semibold text-lg">Traditional</div>
              </button>

              {/* Mixed */}
              <button
                onClick={() => handleScriptSelection('mixed')}
                className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-600 dark:hover:border-blue-600 transition-all text-center"
              >
                <div className="text-4xl mb-3 whitespace-nowrap">
                  简体 + 繁體
                </div>
                <div className="font-semibold text-lg">Mixed</div>
              </button>
            </div>
          </div>
        </div>

        {/* Loading message while waiting for sentence */}
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-600 dark:text-gray-400">Preparing your first sentence...</p>
        </div>
      </div>
    );
  }

  // If no current sentence and preference is set, show loading
  if (!currentSentence) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navigation currentPage="practice" />
        <div className="flex-1 flex items-center justify-center">
          <p className="text-xl text-gray-600 dark:text-gray-400">Loading your next sentence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation currentPage="practice" />

      {/* Score Display */}
      <div className="bg-gray-50 dark:bg-gray-800 px-8 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto">
          <p className="text-sm text-gray-600 dark:text-gray-400">
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
            <div style={{ fontSize: '72px', lineHeight: '1.3', lineBreak: 'strict', wordBreak: 'keep-all' }}>
              {currentSentence.chars.map((char, index) => {
                // Skip if this is ending punctuation (already rendered with previous character)
                const prevChar = currentSentence.chars[index - 1];
                if (isEndingPunctuation(char.char) && prevChar) {
                  return null; // Skip - will be rendered as part of previous character's group
                }

                // Look ahead to collect all consecutive ending punctuation
                const followingPunctuation: typeof currentSentence.chars = [];
                let lookAheadIndex = index + 1;
                while (lookAheadIndex < currentSentence.chars.length) {
                  const nextChar = currentSentence.chars[lookAheadIndex];
                  if (isEndingPunctuation(nextChar.char)) {
                    followingPunctuation.push(nextChar);
                    lookAheadIndex++;
                  } else {
                    break;
                  }
                }

                // Helper function to render a single character box
                const renderCharBox = (c: typeof char, idx: number) => {
                  const hasBeenAnswered = idx < state.currentCharIndex;
                  const isCurrent = idx === state.currentCharIndex;
                  const charType = getCharType(c.char, c.pinyin);

                  // Calculate result index: count Chinese characters before this one
                  const chineseCharsBeforeThis = currentSentence.chars
                    .slice(0, idx)
                    .filter(ch => getCharType(ch.char, ch.pinyin) === 'chinese').length;

                  const isCorrect = hasBeenAnswered && charType === 'chinese'
                    ? state.results[chineseCharsBeforeThis]
                    : null;

                  return (
                    <span
                      key={idx}
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
                            ? exceededRetryIndices.has(idx)
                              ? 'text-purple-600'         // Exceeded retry limit - purple
                              : isCorrect
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
                        {c.char}
                      </span>
                      {/* Always reserve space for feedback to prevent layout shift */}
                      <span
                        className="block text-center mt-1"
                        style={{ fontSize: '16px', height: '20px', lineHeight: '20px' }}
                      >
                        {hasBeenAnswered && (
                          <span className="text-gray-600">{convertToneNumbers(c.pinyin)}</span>
                        )}
                      </span>
                    </span>
                  );
                };

                // If we have following punctuation, wrap current + punctuation together
                if (followingPunctuation.length > 0) {
                  return (
                    <span
                      key={index}
                      style={{ display: 'inline-flex', whiteSpace: 'nowrap' }}
                    >
                      {renderCharBox(char, index)}
                      {followingPunctuation.map((pChar, pIndex) =>
                        renderCharBox(pChar, index + 1 + pIndex)
                      )}
                    </span>
                  );
                }

                // No following punctuation - render normally
                return renderCharBox(char, index);
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Translation Footer - Second footer above input */}
      <div className="sticky bottom-[100px] bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-8 py-4">
        <div className="max-w-4xl mx-auto text-center">
          {!showTranslation && !finishedCurrentSentence ? (
            <button
              onClick={() => setShowTranslation(true)}
              className="px-8 py-3 text-base bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
            >
              Show English Translation
            </button>
          ) : (
            <div className="text-2xl text-gray-600 dark:text-gray-400 italic py-2">
              "{currentSentence.english_translation}"
            </div>
          )}
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
