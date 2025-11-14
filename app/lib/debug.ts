/**
 * Debug mode utility - enables debug features in both dev and production
 *
 * Debug features are enabled when:
 * 1. Running in development environment (NODE_ENV === 'development'), OR
 * 2. User has enabled debug mode via URL parameter (?debug=true)
 *
 * Usage:
 *   - Enable in production: Visit yourapp.com?debug=true
 *   - Disable in production: Visit yourapp.com?debug=false
 *   - Check if debug is enabled: isDebugMode()
 */

const DEBUG_STORAGE_KEY = 'hanzi-debug';

/**
 * Check if debug mode is currently enabled
 * Returns true if in dev environment OR debug toggle is on
 */
export function isDebugMode(): boolean {
  // Always true in development environment
  if (process.env.NODE_ENV === 'development') return true;

  // Check localStorage for production debug toggle
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(DEBUG_STORAGE_KEY) === 'true';
}

/**
 * Check URL parameters and update debug mode accordingly
 * Should be called on page load (e.g., in root layout useEffect)
 */
export function checkAndApplyDebugParam(): void {
  if (typeof window === 'undefined') return;

  const params = new URLSearchParams(window.location.search);
  const debug = params.get('debug');

  if (debug === 'true' || debug === 'false') {
    // Update localStorage
    if (debug === 'true') {
      localStorage.setItem(DEBUG_STORAGE_KEY, 'true');
      console.log('✅ Debug mode enabled');
    } else {
      localStorage.removeItem(DEBUG_STORAGE_KEY);
      console.log('❌ Debug mode disabled');
    }

    // Remove ?debug param from URL and reload
    params.delete('debug');
    const newUrl = params.toString()
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;
    window.location.href = newUrl;
  }
}

/**
 * Manually enable debug mode
 * Useful for programmatic control
 */
export function enableDebugMode(): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(DEBUG_STORAGE_KEY, 'true');
}

/**
 * Manually disable debug mode
 * Useful for programmatic control
 */
export function disableDebugMode(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(DEBUG_STORAGE_KEY);
}
