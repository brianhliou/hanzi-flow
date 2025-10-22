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
      <div className="max-w-4xl w-full space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="text-6xl font-bold">Hanzi Flow</h1>
          <p className="text-2xl text-gray-600 dark:text-gray-400">
            Master Chinese Reading with HSK 3.0-Aligned Adaptive Practice
          </p>

          {/* Stats Teaser */}
          <div className="text-sm text-gray-500 dark:text-gray-500">
            3,000+ characters • 75,000+ sentences • 9 HSK levels
          </div>

          {/* Primary CTA */}
          <div className="pt-4">
            <Link
              href="/practice"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xl px-12 py-4 rounded-lg transition-colors shadow-lg hover:shadow-xl"
            >
              Start Practicing
            </Link>
          </div>
        </div>

        {/* How It Works */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Step 1 */}
            <div className="text-center space-y-2">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-2 h-28 flex items-center justify-center relative">
                <div className="text-6xl">你</div>
                <div className="absolute top-2 right-2 text-xs bg-blue-600 text-white px-2 py-1 rounded">
                  HSK 1
                </div>
              </div>
              <div className="font-semibold">1. Get a Sentence at Your Level</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                AI selects sentences matching your HSK level and progress
              </div>
            </div>

            {/* Step 2 */}
            <div className="text-center space-y-2">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-2 h-28 flex items-center justify-center">
                <div className="text-2xl font-mono text-gray-600">ni3</div>
              </div>
              <div className="font-semibold">2. Type Each Character's Pinyin</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Practice pronunciation with real-time validation
              </div>
            </div>

            {/* Step 3 */}
            <div className="text-center space-y-2">
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 mb-2 h-28 flex items-center justify-center">
                <div className="text-5xl text-green-600">✓</div>
              </div>
              <div className="font-semibold">3. System Adapts to You</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Spaced repetition ensures you remember what you learn
              </div>
            </div>
          </div>
        </div>

        {/* Simple Footer */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-500 pt-8">
          <p>
            Made by{' '}
            <a
              href="https://brianhliou.github.io/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              Brian Lou
            </a>
          </p>
        </div>

      </div>
    </div>
  );
}
