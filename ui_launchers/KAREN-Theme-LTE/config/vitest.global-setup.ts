import { vi } from 'vitest';

// Global setup for problematic modules
export async function setup() {
  // Mock clsx globally to prevent module resolution issues
  vi.mock('clsx', () => ({
    default: (...classes: any[]) => classes.filter(Boolean).join(' '),
    clsx: (...classes: any[]) => classes.filter(Boolean).join(' '),
  }));

  // Mock tailwind-merge as well since it's used with clsx
  vi.mock('tailwind-merge', () => ({
    twMerge: (...classes: any[]) => classes.filter(Boolean).join(' '),
    default: (...classes: any[]) => classes.filter(Boolean).join(' '),
  }));
}

export async function teardown() {
  // Cleanup if needed
}