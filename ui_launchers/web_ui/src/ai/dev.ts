
import { config } from 'dotenv';
config(); // This loads .env variables into process.env

// Explicit check for the GOOGLE_API_KEY after dotenv has run
if (!process.env.GOOGLE_API_KEY || process.env.GOOGLE_API_KEY.trim() === "") {
  console.error("\n***********************************************************************************");
  console.error("**********            ! ! !   FATAL ERROR   ! ! !            **********");
  console.error("***********************************************************************************");
  console.error("*                                                                                 *");
  console.error("*  GOOGLE_API_KEY is NOT DEFINED or is EMPTY in the Genkit server's environment.  *");
  console.error("*                                                                                 *");
  console.error("*  Please ensure:                                                                 *");
  console.error("*  1. You have a file named exactly `.env` (starting with a dot) in your          *");
  console.error("*     PROJECT ROOT directory (the same directory that contains package.json).     *");
  console.error("*  2. This `.env` file contains the line:                                         *");
  console.error("*     GOOGLE_API_KEY=your_actual_api_key_here                                     *");
  console.error("*  3. You have RESTARTED this Genkit server process after creating/modifying      *");
  console.error("*     the `.env` file.                                                            *");
  console.error("*                                                                                 *");
  console.error("*  The Karen AI application will NOT function correctly without this key.         *");
  console.error("*                                                                                 *");
  console.error("***********************************************************************************\n");
} else {
  console.log("\n✅ GOOGLE_API_KEY environment variable found. Initializing Genkit plugins and flows...\n");
}

// Import new flows
import '@/ai/flows/decide-action-flow';
import '@/ai/flows/generate-final-response-flow';
import '@/ai/flows/summarize-conversation'; 
import '@/ai/flows/explore-concept-flow'; // Added new concept exploration flow

// Original flows (some might be deprecated or less used now)
import '@/ai/flows/generate-initial-prompt.ts';
import '@/ai/flows/local-ai-response.ts';

// The old process-user-prompt.ts is no longer needed as its logic is split
// into decide-action-flow.ts and generate-final-response-flow.ts
// No need to import '@/ai/flows/process-user-prompt.ts';
