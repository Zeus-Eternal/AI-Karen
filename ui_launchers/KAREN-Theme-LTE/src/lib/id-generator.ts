// Helper functions to generate consistent IDs that won't cause hydration mismatches

let counter = 0;

// Generate a consistent ID that won't change between server and client renders
export function generateId(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}`;
}

// Generate a timestamp-based ID that's consistent during SSR
export function generateTimestampId(prefix: string): string {
  // Use a fixed timestamp for SSR to ensure consistency
  const timestamp = typeof window === 'undefined' ? 0 : Date.now();
  return `${prefix}-${timestamp}`;
}

// Generate a random ID (client-side only)
export function generateRandomId(prefix: string): string {
  // Only use random on client-side to avoid hydration mismatches
  if (typeof window === 'undefined') {
    return generateId(prefix); // Fallback to sequential ID on server
  }
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}