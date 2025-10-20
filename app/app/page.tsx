'use client';

import Link from "next/link";
import { useState } from "react";

type ScriptType = 'simplified' | 'traditional' | 'mixed';

export default function Home() {
  const [selectedScript, setSelectedScript] = useState<ScriptType>('mixed');

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-5xl font-bold">Hanzi Flow</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Master Chinese character pronunciation through interactive typing practice
        </p>

        {/* Script Type Selection */}
        <div className="space-y-4">
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
            Choose your script type:
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setSelectedScript('simplified')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                selectedScript === 'simplified'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Simplified
            </button>
            <button
              onClick={() => setSelectedScript('traditional')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                selectedScript === 'traditional'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Traditional
            </button>
            <button
              onClick={() => setSelectedScript('mixed')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                selectedScript === 'mixed'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Mixed
            </button>
          </div>
        </div>

        <Link
          href={`/practice?script=${selectedScript}`}
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
        >
          Start Practicing
        </Link>

        {/* Dev Link to Stats */}
        <Link
          href="/stats"
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          View Stats (Dev)
        </Link>
      </div>
    </div>
  );
}
