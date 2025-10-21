'use client';

import { useState, useEffect } from 'react';
import { resetDatabase } from '@/lib/db';
import Navigation from '@/components/Navigation';

type ScriptType = 'simplified' | 'traditional' | 'mixed';

const SCRIPT_PREFERENCE_KEY = 'hanzi-flow-script-preference';

export default function SettingsPage() {
  const [selectedScript, setSelectedScript] = useState<ScriptType>('mixed');
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  // Load preference on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(SCRIPT_PREFERENCE_KEY) as ScriptType | null;
      if (saved) {
        setSelectedScript(saved);
      }
    }
  }, []);

  const handleScriptChange = (script: ScriptType) => {
    setSelectedScript(script);
    localStorage.setItem(SCRIPT_PREFERENCE_KEY, script);
  };

  const handleReset = async () => {
    await resetDatabase();
    localStorage.removeItem(SCRIPT_PREFERENCE_KEY);
    setShowResetConfirm(false);
    setResetSuccess(true);
    setTimeout(() => setResetSuccess(false), 3000);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation currentPage="settings" />

      {/* Content */}
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto space-y-12">
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
          </section>
        </div>
      </div>
    </div>
  );
}
