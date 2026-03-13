
import type { KarenSettings } from './types';

export const KAREN_SETTINGS_LS_KEY = 'karenAiSettings';
export const KAREN_SUGGESTED_FACTS_LS_KEY = 'karenAiSuggestedFacts';

export const DEFAULT_KAREN_SETTINGS: KarenSettings = {
  memoryDepth: 'medium',
  personalityTone: 'friendly',
  personalityVerbosity: 'balanced',
  personalFacts: [],
  notifications: {
    enabled: true,
    alertOnNewInsights: true,
    alertOnSummaryReady: false,
  },
  ttsVoiceURI: null,
  customPersonaInstructions: '',
  temperatureUnit: 'C',
  weatherService: 'wttr_in',
  weatherApiKey: null,
  defaultWeatherLocation: null,
  activeListenMode: false, // Added active listen mode default
};
