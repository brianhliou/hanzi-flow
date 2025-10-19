import type { Sentence } from './types';

export async function loadSentences(): Promise<Sentence[]> {
  const response = await fetch('/data/sentences.json');
  if (!response.ok) {
    throw new Error('Failed to load sentences');
  }
  const sentences = await response.json();

  // TEMP: Prioritize test sentences with alphanumeric/punctuation - REMOVE THIS BLOCK LATER
  // Sentences to load first (in order)
  const prioritySentences = [
    "今天是６月１８号，也是Muiriel的生日！",
    "生日快乐，Muiriel！",
    "Muiriel现在20岁了。",
    "\"密码是\"\"Muiriel\"\"。\""
  ];

  // Extract priority sentences from the full list
  const priorityItems: Sentence[] = [];
  const prioritySet = new Set(prioritySentences);

  prioritySentences.forEach(targetSentence => {
    const found = sentences.find((s: Sentence) => s.sentence === targetSentence);
    if (found) {
      priorityItems.push(found);
    }
  });

  // Remove priority sentences from main list to avoid duplicates
  const remainingSentences = sentences.filter((s: Sentence) => !prioritySet.has(s.sentence));

  return [...priorityItems, ...remainingSentences];
  // END TEMP BLOCK
}
