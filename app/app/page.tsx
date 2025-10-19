import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-5xl font-bold">Hanzi Flow</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Master Chinese character pronunciation through interactive typing practice
        </p>
        <Link
          href="/practice"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
        >
          Start Practicing
        </Link>
      </div>
    </div>
  );
}
