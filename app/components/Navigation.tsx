import Link from 'next/link';

type NavigationProps = {
  currentPage?: 'practice' | 'settings' | 'stats';
};

export default function Navigation({ currentPage }: NavigationProps) {
  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-8 py-4">
      <div className="max-w-4xl mx-auto flex justify-between items-center">
        <Link
          href="/"
          className="text-xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          Hanzi Flow
        </Link>
        <div className="flex gap-6">
          <Link
            href="/practice"
            className={`transition-colors ${
              currentPage === 'practice'
                ? 'text-blue-600 dark:text-blue-400 font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Practice
          </Link>
          <Link
            href="/settings"
            className={`transition-colors ${
              currentPage === 'settings'
                ? 'text-blue-600 dark:text-blue-400 font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Settings
          </Link>
          <Link
            href="/stats"
            className={`transition-colors ${
              currentPage === 'stats'
                ? 'text-blue-600 dark:text-blue-400 font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Stats
          </Link>
        </div>
      </div>
    </nav>
  );
}
