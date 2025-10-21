'use client';

import Navigation from '@/components/Navigation';
import UserStats from '@/components/UserStats';
import DevStats from '@/components/DevStats';

export default function StatsPage() {
  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation currentPage="stats" />

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Your Progress</h1>

          {/* Production: User-facing stats */}
          <UserStats />

          {/* Development: Additional debugging stats */}
          {isDev && (
            <div className="mt-12 pt-12 border-t border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold mb-6 text-gray-500">
                Development Stats
              </h2>
              <DevStats />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
