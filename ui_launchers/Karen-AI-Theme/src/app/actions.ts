
'use server';
/**
 * @fileoverview Server Actions for tasks that don't involve a complex backend.
 * These are simple placeholders.
 */

// Placeholder for suggested starters
export async function getSuggestedStarter(): Promise<string> {
  // In a real scenario, this might call a simple API or have a static list.
  return "Tell me a fun fact about space.";
}

// Placeholder for premium TTS - backend is removed.
export async function getPremiumTts(): Promise<string | null> {
  console.warn("getPremiumTts called, but backend is removed. Returning null.");
  return null;
}
