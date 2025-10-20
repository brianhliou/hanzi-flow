'use client';

import Link from 'next/link';
import DevStats from '@/components/DevStats';

export default function StatsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Sticky Header - matches practice page style */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-8 py-4 z-10">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <p className="text-gray-600 dark:text-gray-400">Mastery Statistics</p>
          <Link
            href="/practice"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Back to Practice
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-6xl mx-auto">
          <DevStats />
        </div>
      </div>
    </div>
  );
}
