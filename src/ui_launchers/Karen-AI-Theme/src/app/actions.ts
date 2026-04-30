
'use server';
/**
 * @fileoverview Server Actions for tasks that don't involve a complex backend.
 * These are simple placeholders.
 */

// Starter suggestions API pending backend hookup
export async function getSuggestedStarter(): Promise<string> {
  // In a real scenario, this might call a simple API or have a static list.
  return "Tell me a fun fact about space.";
}

// Premium TTS endpoint pending backend availability.
export async function getPremiumTts(): Promise<string | null> {
  console.warn("getPremiumTts called, but backend is removed. Returning null.");
  return null;
}
