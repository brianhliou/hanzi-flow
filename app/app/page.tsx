'use client';

import { useEffect } from 'react';
import Link from "next/link";
import { loadSentences } from '@/lib/sentences';
import { loadCharacterMapping } from '@/lib/characters';

export default function Home() {
  // Preload data in background while user reads homepage
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🏠 Homepage: Starting background preload...');
    }

    Promise.all([
      loadSentences(),
      loadCharacterMapping()
    ])
      .then(() => {
        if (process.env.NODE_ENV === 'development') {
          console.log('✓ Preload complete - data cached for instant practice page load');
        }
      })
      .catch((error) => {
        console.error('Preload failed (non-critical):', error);
      });
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full space-y-12">
        {/* Hero Section */}
        <div className="text-center space-y-6">
          <h1 className="text-6xl font-bold">Hanzi Flow</h1>
          <p className="text-2xl text-gray-600 dark:text-gray-400">
            Master Chinese Characters Through Practice
          </p>

          {/* Value Props */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
            <div className="text-center">
              <div className="text-2xl mb-1">✨</div>
              <div className="text-sm font-medium">Adaptive Learning</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">🎯</div>
              <div className="text-sm font-medium">Spaced Repetition</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">📊</div>
              <div className="text-sm font-medium">Track Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">🆓</div>
              <div className="text-sm font-medium">Free, No Signup</div>
            </div>
          </div>
        </div>

        {/* How It Works */}
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="text-center space-y-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-2 h-32 flex items-center justify-center">
                <div className="text-6xl">你</div>
              </div>
              <div className="font-semibold">1. See a Character</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Practice with real Chinese sentences
              </div>
            </div>

            {/* Step 2 */}
            <div className="text-center space-y-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-2 h-32 flex items-center justify-center">
                <div className="text-2xl font-mono text-gray-600">ni3</div>
              </div>
              <div className="font-semibold">2. Type Pinyin</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Enter the pronunciation
              </div>
            </div>

            {/* Step 3 */}
            <div className="text-center space-y-3">
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-6 mb-2 h-32 flex items-center justify-center">
                <div className="text-5xl text-green-600">✓</div>
              </div>
              <div className="font-semibold">3. Get Feedback</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Learn from instant corrections
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link
            href="/practice"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xl px-12 py-5 rounded-lg transition-colors shadow-lg hover:shadow-xl"
          >
            Start Practicing
          </Link>
        </div>
      </div>
    </div>
  );
}
