'use client';

import Navigation from '@/components/Navigation';
import DevStats from '@/components/DevStats';

export default function StatsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation currentPage="stats" />

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-6xl mx-auto">
          <DevStats />
        </div>
      </div>
    </div>
  );
}
