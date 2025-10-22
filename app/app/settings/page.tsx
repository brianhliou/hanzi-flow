'use client';

import { useState, useEffect } from 'react';
import { resetDatabase } from '@/lib/db';
import Navigation from '@/components/Navigation';
import type { HskFilter } from '@/lib/types';

type ScriptType = 'simplified' | 'traditional' | 'mixed';

const SCRIPT_PREFERENCE_KEY = 'hanzi-flow-script-preference';
const HSK_PREFERENCE_KEY = 'hanzi-flow-hsk-preference';
const AUDIO_ENABLED_KEY = 'hanzi-flow-audio-enabled';

export default function SettingsPage() {
  const [selectedScript, setSelectedScript] = useState<ScriptType | null>(null);
  const [selectedHsk, setSelectedHsk] = useState<HskFilter | null>(null);
  const [audioEnabled, setAudioEnabled] = useState<boolean>(true);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Load preferences on mount (client-side only to avoid hydration mismatch)
  useEffect(() => {
    const savedScript = localStorage.getItem(SCRIPT_PREFERENCE_KEY) as ScriptType | null;
    setSelectedScript(savedScript); // Keep as null if no preference saved

    const savedHsk = localStorage.getItem(HSK_PREFERENCE_KEY) as HskFilter | null;
    setSelectedHsk(savedHsk); // Keep as null if no preference saved

    const savedAudio = localStorage.getItem(AUDIO_ENABLED_KEY);
    setAudioEnabled(savedAudio === null ? true : savedAudio === 'true'); // Default to enabled

    setIsHydrated(true); // Mark as hydrated
  }, []);

  const handleScriptChange = (script: ScriptType) => {
    setSelectedScript(script);
    localStorage.setItem(SCRIPT_PREFERENCE_KEY, script);
  };

  const handleHskChange = (hsk: HskFilter) => {
    setSelectedHsk(hsk);
    localStorage.setItem(HSK_PREFERENCE_KEY, hsk);
  };

  const handleAudioToggle = () => {
    const newValue = !audioEnabled;
    setAudioEnabled(newValue);
    localStorage.setItem(AUDIO_ENABLED_KEY, String(newValue));
  };

  const handleReset = async () => {
    await resetDatabase();
    localStorage.removeItem(SCRIPT_PREFERENCE_KEY);
    localStorage.removeItem(HSK_PREFERENCE_KEY);
    setShowResetConfirm(false);
    setResetSuccess(true);
    setTimeout(() => setResetSuccess(false), 3000);
  };

  // DEV MODE ONLY: Reset both preferences to trigger modal (without losing progress data)
  const handleResetPreferences = () => {
    localStorage.removeItem(SCRIPT_PREFERENCE_KEY);
    localStorage.removeItem(HSK_PREFERENCE_KEY);
    setSelectedScript(null);
    setSelectedHsk(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation currentPage="settings" />

      {/* Content */}
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Settings</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Customize your learning experience
            </p>
          </div>

          {/* Script Preference */}
          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold mb-1">Script Preference</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Choose which Chinese character style you want to practice
              </p>
            </div>

            {!isHydrated ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Hydration placeholder - show neutral non-interactive cards */}
                <div className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 text-center opacity-50">
                  <div className="text-5xl mb-3">简体</div>
                  <div className="font-semibold text-lg">Simplified</div>
                </div>
                <div className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 text-center opacity-50">
                  <div className="text-5xl mb-3">繁體</div>
                  <div className="font-semibold text-lg">Traditional</div>
                </div>
                <div className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 text-center opacity-50">
                  <div className="text-4xl mb-3 whitespace-nowrap">简体 + 繁體</div>
                  <div className="font-semibold text-lg">Mixed</div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Simplified */}
                <button
                  onClick={() => handleScriptChange('simplified')}
                  className={`p-6 rounded-lg border-2 transition-all text-center ${
                    selectedScript === 'simplified'
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="text-5xl mb-3">简体</div>
                  <div className="font-semibold text-lg">Simplified</div>
                </button>

                {/* Traditional */}
                <button
                  onClick={() => handleScriptChange('traditional')}
                  className={`p-6 rounded-lg border-2 transition-all text-center ${
                    selectedScript === 'traditional'
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="text-5xl mb-3">繁體</div>
                  <div className="font-semibold text-lg">Traditional</div>
                </button>

                {/* Mixed */}
                <button
                  onClick={() => handleScriptChange('mixed')}
                  className={`p-6 rounded-lg border-2 transition-all text-center ${
                    selectedScript === 'mixed'
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="text-4xl mb-3 whitespace-nowrap">
                    简体 + 繁體
                  </div>
                  <div className="font-semibold text-lg">Mixed</div>
                </button>
              </div>
            )}
          </section>

          {/* HSK Level Preference */}
          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold mb-1">Max HSK Level</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Includes all levels up to and including the selected level
              </p>
            </div>

            {!isHydrated ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Hydration placeholder */}
                {['1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-9', '1-beyond'].map((level) => (
                  <div key={level} className="p-4 rounded-lg border-2 border-gray-200 dark:border-gray-700 text-center opacity-50">
                    <div className="font-semibold mb-1">HSK {level}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: '1' as HskFilter, label: 'HSK 1', subtitle: '300 chars' },
                  { value: '1-2' as HskFilter, label: 'HSK 2', subtitle: '300 chars (600 total)' },
                  { value: '1-3' as HskFilter, label: 'HSK 3', subtitle: '300 chars (900 total)' },
                  { value: '1-4' as HskFilter, label: 'HSK 4', subtitle: '300 chars (1,200 total)' },
                  { value: '1-5' as HskFilter, label: 'HSK 5', subtitle: '300 chars (1,500 total)' },
                  { value: '1-6' as HskFilter, label: 'HSK 6', subtitle: '300 chars (1,800 total)' },
                  { value: '1-9' as HskFilter, label: 'HSK 7-9', subtitle: '1,200 chars (3,000 total)' },
                  { value: '1-beyond' as HskFilter, label: 'Beyond HSK', subtitle: '~4,000 chars total' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleHskChange(option.value)}
                    className={`p-4 rounded-lg border-2 transition-all text-center ${
                      selectedHsk === option.value
                        ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="font-semibold mb-1">{option.label}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">{option.subtitle}</div>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Audio Settings */}
          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold mb-1">Audio Settings</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Control audio feedback during practice
              </p>
            </div>

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold mb-1">Pronunciation Audio</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Play audio when you answer incorrectly
                  </p>
                </div>
                <button
                  onClick={handleAudioToggle}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    audioEnabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                  aria-label="Toggle audio"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      audioEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </section>

          {/* Data Management */}
          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold mb-1">Data Management</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage your learning progress and data
              </p>
            </div>

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="font-semibold mb-2">Reset All Progress</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                This will delete all your learning data, progress, and preferences. This action cannot be undone.
              </p>

              {!showResetConfirm ? (
                <button
                  onClick={() => setShowResetConfirm(true)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  Reset All Data
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm font-semibold text-red-600 dark:text-red-400">
                    Are you sure? This will delete everything.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleReset}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    >
                      Yes, Reset Everything
                    </button>
                    <button
                      onClick={() => setShowResetConfirm(false)}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {resetSuccess && (
                <div className="mt-3 text-sm text-green-600 dark:text-green-400">
                  ✓ All data has been reset successfully
                </div>
              )}
            </div>

            {/* DEV MODE ONLY: Reset preferences button */}
            {process.env.NODE_ENV === 'development' && (
              <div className="border border-orange-300 dark:border-orange-700 bg-orange-50 dark:bg-orange-900/20 rounded-lg p-6">
                <h3 className="font-semibold mb-2 text-orange-800 dark:text-orange-300">
                  [DEV] Reset Preferences
                </h3>
                <p className="text-sm text-orange-700 dark:text-orange-400 mb-4">
                  Development only: Clear both script and HSK preferences to test the modal flow. Does NOT delete progress data.
                </p>
                <button
                  onClick={handleResetPreferences}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
                >
                  [DEV] Clear All Preferences
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
