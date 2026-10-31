/**
 * Timezone-safe date utilities to avoid UTC day shifts in the browser.
 */

/**
 * Returns today's date (or given date) as YYYY-MM-DD in local system time.
 * Avoids new Date().toISOString().split('T')[0] which converts to UTC midnight
 * and causes 1-day backward or forward shifts depending on the user's timezone.
 */
export function getLocalDateString(d: Date = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Safely displays a date string (YYYY-MM-DD or ISO timestamp) without
 * allowing timezone offsets to shift date-only strings by +/- 1 day.
 */
export function formatDateSafe(dateStr?: string | null): string {
  if (!dateStr) return 'N/A';
  // If it's already YYYY-MM-DD, keep as-is to preserve calendar date integrity
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    return dateStr;
  }
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return getLocalDateString(d);
  } catch {
    return dateStr;
  }
}
