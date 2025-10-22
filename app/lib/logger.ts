/**
 * Simple logging utility for NSS and other debug output
 *
 * Logs to both console and localStorage for persistence across sessions.
 * Can be viewed/cleared via browser DevTools.
 */

interface LogEntry {
  timestamp: number;
  level: 'log' | 'warn' | 'error';
  tag: string;
  message: string;
  data?: any;
}

const MAX_LOGS = 1000;  // Keep last 1000 entries
const STORAGE_KEY = 'hanzi-flow-logs';
const AUTO_SAVE_INTERVAL_MS = 30000;  // Auto-save to file every 30 seconds in dev mode
const LAST_SAVE_KEY = 'hanzi-flow-logs-last-save';

/**
 * Get all stored logs
 */
export function getLogs(): LogEntry[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to read logs from localStorage:', error);
    return [];
  }
}

/**
 * Add a log entry
 */
function addLog(entry: LogEntry): void {
  if (typeof window === 'undefined') return;

  try {
    const logs = getLogs();
    logs.push(entry);

    // Keep only last MAX_LOGS entries
    const trimmed = logs.slice(-MAX_LOGS);

    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));

    // Trigger auto-save in development mode
    scheduleAutoSave();
  } catch (error) {
    console.error('Failed to write log to localStorage:', error);
  }
}

/**
 * Clear all logs
 */
export function clearLogs(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem(STORAGE_KEY);
    console.log('[Logger] Logs cleared');
  } catch (error) {
    console.error('Failed to clear logs:', error);
  }
}

/**
 * Export logs as downloadable text file
 */
export function exportLogs(): void {
  const logs = getLogs();

  const text = logs.map(entry => {
    const date = new Date(entry.timestamp).toISOString();
    const dataStr = entry.data ? `\n  ${JSON.stringify(entry.data, null, 2)}` : '';
    return `[${date}] [${entry.level.toUpperCase()}] [${entry.tag}] ${entry.message}${dataStr}`;
  }).join('\n\n');

  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `hanzi-flow-logs-${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Log a message (info level)
 */
export function log(tag: string, message: string, data?: any): void {
  console.log(`[${tag}] ${message}`, data ?? '');

  addLog({
    timestamp: Date.now(),
    level: 'log',
    tag,
    message,
    data
  });
}

/**
 * Log a warning
 */
export function warn(tag: string, message: string, data?: any): void {
  console.warn(`[${tag}] ${message}`, data ?? '');

  addLog({
    timestamp: Date.now(),
    level: 'warn',
    tag,
    message,
    data
  });
}

/**
 * Log an error
 */
export function error(tag: string, message: string, data?: any): void {
  console.error(`[${tag}] ${message}`, data ?? '');

  addLog({
    timestamp: Date.now(),
    level: 'error',
    tag,
    message,
    data
  });
}

// Convenience exports for NSS logging (disabled)
export const nssLog = (message: string, data?: any) => {
  // NSS logging disabled
  return;
};

export const nssWarn = (message: string, data?: any) => {
  // NSS logging disabled
  return;
};

export const nssError = (message: string, data?: any) => {
  // NSS logging disabled
  return;
};

// ============================================================================
// AUTO-SAVE TO FILE (Development only)
// ============================================================================

let autoSaveTimeout: NodeJS.Timeout | null = null;

/**
 * Schedule auto-save to file system (development only)
 * Debounced - only saves if no new logs for 30 seconds
 */
function scheduleAutoSave(): void {
  if (typeof window === 'undefined') return;
  if (process.env.NODE_ENV !== 'development') return;

  // Clear existing timeout
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
  }

  // Schedule new save
  autoSaveTimeout = setTimeout(() => {
    saveLogsToFile();
  }, AUTO_SAVE_INTERVAL_MS);
}

/**
 * Save logs to file system via API endpoint
 */
async function saveLogsToFile(): Promise<void> {
  if (typeof window === 'undefined') return;

  try {
    const logs = getLogs();
    if (logs.length === 0) return;

    // Check last save timestamp to avoid duplicate saves
    const lastSave = localStorage.getItem(LAST_SAVE_KEY);
    const lastSaveTime = lastSave ? parseInt(lastSave, 10) : 0;
    const now = Date.now();

    // Only save if at least 30 seconds since last save
    if (now - lastSaveTime < AUTO_SAVE_INTERVAL_MS) {
      return;
    }

    const response = await fetch('/api/save-logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ logs }),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Logger] Auto-saved ${result.count} logs to ${result.filename}`);
      localStorage.setItem(LAST_SAVE_KEY, now.toString());
    } else {
      console.warn('[Logger] Failed to auto-save logs:', response.statusText);
    }
  } catch (error) {
    // Silently fail - auto-save is a convenience feature
    console.warn('[Logger] Auto-save failed:', error);
  }
}

/**
 * Manually trigger save to file
 */
export async function saveLogsNow(): Promise<void> {
  await saveLogsToFile();
}
