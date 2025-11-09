/**
 * Common Utility Functions
 *
 * Centralized collection of frequently-used utility functions for
 * string manipulation, array/object operations, validation, and formatting.
 *
 * @module utils/common
 */

// ─────────────────────────────────────────────────────────────────────
// String Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Truncates a string to a maximum length and adds an ellipsis
 *
 * @param str - The string to truncate
 * @param maxLength - Maximum length before truncation
 * @param suffix - Suffix to add when truncated (default: '...')
 * @returns Truncated string
 *
 * @example
 * truncate('Hello World', 8) // => 'Hello...'
 * truncate('Short', 10) // => 'Short'
 */
export function truncate(str: string, maxLength: number, suffix = '...'): string {
  if (!str || str.length <= maxLength) return str;
  return str.slice(0, Math.max(0, maxLength - suffix.length)) + suffix;
}

/**
 * Converts a string to URL-friendly slug format
 *
 * @param str - The string to slugify
 * @returns URL-safe slug
 *
 * @example
 * slugify('Hello World!') // => 'hello-world'
 * slugify('  Foo & Bar  ') // => 'foo-and-bar'
 */
export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special chars
    .replace(/[\s_-]+/g, '-') // Replace spaces/underscores with single dash
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing dashes
}

/**
 * Converts a string to camelCase
 *
 * @param str - The string to convert
 * @returns camelCase string
 *
 * @example
 * camelCase('hello-world') // => 'helloWorld'
 * camelCase('user_name') // => 'userName'
 */
export function camelCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/[_-\s](.)/g, (_, char) => char.toUpperCase());
}

/**
 * Converts a string to PascalCase
 *
 * @param str - The string to convert
 * @returns PascalCase string
 *
 * @example
 * pascalCase('hello-world') // => 'HelloWorld'
 */
export function pascalCase(str: string): string {
  const camel = camelCase(str);
  return camel.charAt(0).toUpperCase() + camel.slice(1);
}

/**
 * Converts a string to snake_case
 *
 * @param str - The string to convert
 * @returns snake_case string
 *
 * @example
 * snakeCase('helloWorld') // => 'hello_world'
 * snakeCase('HelloWorld') // => 'hello_world'
 */
export function snakeCase(str: string): string {
  return str
    .replace(/([A-Z])/g, '_$1')
    .toLowerCase()
    .replace(/^_/, '');
}

/**
 * Formats bytes to human-readable string
 *
 * @param bytes - Number of bytes
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string (e.g., '1.5 MB')
 *
 * @example
 * formatBytes(1024) // => '1.00 KB'
 * formatBytes(1536000) // => '1.46 MB'
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';
  if (!Number.isFinite(bytes) || bytes < 0) return 'Invalid';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

// ─────────────────────────────────────────────────────────────────────
// Array/Object Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Groups array elements by a key function
 *
 * @param array - Array to group
 * @param keyFn - Function to extract grouping key
 * @returns Object with grouped elements
 *
 * @example
 * const users = [{ age: 20 }, { age: 30 }, { age: 20 }];
 * groupBy(users, u => u.age) // => { '20': [{age:20}, {age:20}], '30': [{age:30}] }
 */
export function groupBy<T, K extends string | number>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return array.reduce((groups, item) => {
    const key = keyFn(item);
    (groups[key] = groups[key] || []).push(item);
    return groups;
  }, {} as Record<K, T[]>);
}

/**
 * Returns unique array elements
 *
 * @param array - Array with potential duplicates
 * @param keyFn - Optional function to extract comparison key
 * @returns Array with unique elements
 *
 * @example
 * unique([1, 2, 2, 3]) // => [1, 2, 3]
 * unique([{id:1}, {id:1}, {id:2}], x => x.id) // => [{id:1}, {id:2}]
 */
export function unique<T, K = T>(
  array: T[],
  keyFn?: (item: T) => K
): T[] {
  if (!keyFn) return [...new Set(array)];

  const seen = new Set<K>();
  return array.filter(item => {
    const key = keyFn(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Deep merges two objects
 *
 * @param target - Target object
 * @param source - Source object to merge
 * @returns Merged object
 *
 * @example
 * deepMerge({a: {b: 1}}, {a: {c: 2}}) // => {a: {b: 1, c: 2}}
 */
export function deepMerge<T extends Record<string, any>>(
  target: T,
  source: Partial<T>
): T {
  const result = { ...target };

  for (const key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      const sourceValue = source[key];
      const targetValue = result[key];

      if (
        sourceValue &&
        typeof sourceValue === 'object' &&
        !Array.isArray(sourceValue) &&
        targetValue &&
        typeof targetValue === 'object' &&
        !Array.isArray(targetValue)
      ) {
        result[key] = deepMerge(targetValue, sourceValue) as T[Extract<keyof T, string>];
      } else {
        result[key] = sourceValue as T[Extract<keyof T, string>];
      }
    }
  }

  return result;
}

/**
 * Picks specified keys from an object
 *
 * @param obj - Source object
 * @param keys - Keys to pick
 * @returns New object with only specified keys
 *
 * @example
 * pick({a: 1, b: 2, c: 3}, ['a', 'c']) // => {a: 1, c: 3}
 */
export function pick<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
}

/**
 * Omits specified keys from an object
 *
 * @param obj - Source object
 * @param keys - Keys to omit
 * @returns New object without specified keys
 *
 * @example
 * omit({a: 1, b: 2, c: 3}, ['b']) // => {a: 1, c: 3}
 */
export function omit<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
}

// ─────────────────────────────────────────────────────────────────────
// Validation Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Validates email address format
 *
 * @param email - Email string to validate
 * @returns true if valid email format
 *
 * @example
 * isEmail('[email protected]') // => true
 * isEmail('invalid@') // => false
 */
export function isEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validates URL format
 *
 * @param url - URL string to validate
 * @param allowedProtocols - Allowed protocols (default: ['http:', 'https:'])
 * @returns true if valid URL format
 *
 * @example
 * isURL('https://example.com') // => true
 * isURL('ftp://example.com', ['ftp:']) // => true
 * isURL('javascript:alert(1)') // => false
 */
export function isURL(url: string, allowedProtocols: string[] = ['http:', 'https:']): boolean {
  try {
    const parsed = new URL(url);
    return allowedProtocols.includes(parsed.protocol);
  } catch {
    return false;
  }
}

/**
 * Validates hexadecimal color code
 *
 * @param hex - Hex color string
 * @returns true if valid hex color
 *
 * @example
 * isValidHex('#FF5733') // => true
 * isValidHex('#FFF') // => true
 * isValidHex('FF5733') // => false
 */
export function isValidHex(hex: string): boolean {
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(hex);
}

/**
 * Checks if value is empty (null, undefined, '', [], {})
 *
 * @param value - Value to check
 * @returns true if empty
 *
 * @example
 * isEmpty(null) // => true
 * isEmpty('') // => true
 * isEmpty([]) // => true
 * isEmpty({}) // => true
 * isEmpty('hello') // => false
 */
export function isEmpty(value: any): boolean {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

// ─────────────────────────────────────────────────────────────────────
// Number/Math Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Clamps a number between min and max
 *
 * @param value - Number to clamp
 * @param min - Minimum value
 * @param max - Maximum value
 * @returns Clamped number
 *
 * @example
 * clamp(5, 0, 10) // => 5
 * clamp(-5, 0, 10) // => 0
 * clamp(15, 0, 10) // => 10
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Formats number with thousands separators
 *
 * @param num - Number to format
 * @param decimals - Number of decimal places
 * @returns Formatted string
 *
 * @example
 * formatNumber(1000) // => '1,000'
 * formatNumber(1234.567, 2) // => '1,234.57'
 */
export function formatNumber(num: number, decimals?: number): string {
  const fixed = decimals !== undefined ? num.toFixed(decimals) : num.toString();
  return fixed.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Calculates percentage
 *
 * @param value - Current value
 * @param total - Total value
 * @param decimals - Decimal places (default: 0)
 * @returns Percentage value
 *
 * @example
 * percentage(25, 100) // => 25
 * percentage(1, 3, 2) // => 33.33
 */
export function percentage(value: number, total: number, decimals = 0): number {
  if (total === 0) return 0;
  const pct = (value / total) * 100;
  return decimals > 0 ? parseFloat(pct.toFixed(decimals)) : Math.round(pct);
}

// ─────────────────────────────────────────────────────────────────────
// Date/Time Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Formats date to ISO string (YYYY-MM-DD)
 *
 * @param date - Date object or timestamp
 * @returns ISO date string
 *
 * @example
 * formatDate(new Date('2024-01-15')) // => '2024-01-15'
 */
export function formatDate(date: Date | number): string {
  const d = typeof date === 'number' ? new Date(date) : date;
  return d.toISOString().split('T')[0];
}

/**
 * Formats date and time to ISO string
 *
 * @param date - Date object or timestamp
 * @returns ISO datetime string
 *
 * @example
 * formatDateTime(new Date()) // => '2024-01-15T10:30:00.000Z'
 */
export function formatDateTime(date: Date | number): string {
  const d = typeof date === 'number' ? new Date(date) : date;
  return d.toISOString();
}

/**
 * Calculates days between two dates
 *
 * @param date1 - First date
 * @param date2 - Second date
 * @returns Number of days between dates
 *
 * @example
 * getDaysBetween(new Date('2024-01-01'), new Date('2024-01-10')) // => 9
 */
export function getDaysBetween(date1: Date | number, date2: Date | number): number {
  const d1 = typeof date1 === 'number' ? new Date(date1) : date1;
  const d2 = typeof date2 === 'number' ? new Date(date2) : date2;
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Adds days to a date
 *
 * @param date - Starting date
 * @param days - Number of days to add (can be negative)
 * @returns New date
 *
 * @example
 * addDays(new Date('2024-01-01'), 7) // => Date('2024-01-08')
 * addDays(new Date('2024-01-10'), -3) // => Date('2024-01-07')
 */
export function addDays(date: Date | number, days: number): Date {
  const d = new Date(typeof date === 'number' ? date : date.getTime());
  d.setDate(d.getDate() + days);
  return d;
}

/**
 * Formats a date relative to now (e.g., "2 days ago", "in 3 hours")
 *
 * @param date - Date to format
 * @returns Relative time string
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 3600000)) // => '1 hour ago'
 */
export function formatRelativeTime(date: Date | number): string {
  const d = typeof date === 'number' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (Math.abs(diffSec) < 60) return 'just now';
  if (Math.abs(diffMin) < 60) return `${Math.abs(diffMin)} minute${Math.abs(diffMin) === 1 ? '' : 's'} ${diffMs < 0 ? 'from now' : 'ago'}`;
  if (Math.abs(diffHour) < 24) return `${Math.abs(diffHour)} hour${Math.abs(diffHour) === 1 ? '' : 's'} ${diffMs < 0 ? 'from now' : 'ago'}`;
  return `${Math.abs(diffDay)} day${Math.abs(diffDay) === 1 ? '' : 's'} ${diffMs < 0 ? 'from now' : 'ago'}`;
}

// ─────────────────────────────────────────────────────────────────────
// Async Utilities
// ─────────────────────────────────────────────────────────────────────

/**
 * Creates a promise that resolves after specified delay
 *
 * @param ms - Milliseconds to wait
 * @returns Promise that resolves after delay
 *
 * @example
 * await sleep(1000); // Wait 1 second
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Debounces a function call
 *
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 *
 * @example
 * const debouncedSearch = debounce((query) => search(query), 300);
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Throttles a function call
 *
 * @param fn - Function to throttle
 * @param limit - Minimum time between calls in milliseconds
 * @returns Throttled function
 *
 * @example
 * const throttledScroll = throttle((e) => handleScroll(e), 100);
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
