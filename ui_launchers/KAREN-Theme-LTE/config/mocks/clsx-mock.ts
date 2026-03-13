/**
 * Mock for clsx module to resolve module resolution issues
 */

export type ClassValue =
  | string
  | number
  | boolean
  | undefined
  | null
  | ClassValue[]
  | { [key: string]: any };

function clsx(...inputs: ClassValue[]): string {
  return inputs
    .filter(Boolean)
    .map(input => {
      if (typeof input === 'string' || typeof input === 'number') {
        return String(input);
      }
      if (Array.isArray(input)) {
        return clsx(...input);
      }
      if (typeof input === 'object' && input !== null) {
        return Object.keys(input)
          .filter(key => input[key])
          .join(' ');
      }
      return '';
    })
    .join(' ');
}

// Add displayName to the function for better compatibility
clsx.displayName = 'clsx';

export default clsx;
export { clsx };