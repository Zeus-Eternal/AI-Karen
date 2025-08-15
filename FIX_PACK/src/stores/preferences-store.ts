import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// User Preferences Types
export interface UserPreferences {
  // AI Provider preferences
  preferredProvider: string | null;
  preferredModel: string | null;
  temperature: number;
  maxTokens: number;
  
  // Chat behavior
  autoSave: boolean;
  autoTitle: boolean;
  streamingEnabled: boolean;
  soundEnabled: boolean;
  
  // Voice preferences
  voiceInputEnabled: boolean;
  voiceOutputEnabled: boolean;
  voiceLanguage: string;
  voiceSpeed: number;
  
  // Privacy and security
  dataRetention: 'session' | '7days' | '30days' | 'forever';
  analyticsEnabled: boolean;
  crashReportingEnabled: boolean;
  
  // Accessibility
  highContrast: boolean;
  reducedMotion: boolean;
  screenReaderOptimized: boolean;
  keyboardNavigation: boolean;
  
  // Experimental features
  experimentalFeatures: string[];
  betaFeatures: string[];
}

// Preferences Actions
export interface PreferencesActions {
  // AI Provider actions
  setPreferredProvider: (provider: string | null) => void;
  setPreferredModel: (model: string | null) => void;
  setTemperature: (temperature: number) => void;
  setMaxTokens: (maxTokens: number) => void;
  
  // Chat behavior actions
  toggleAutoSave: () => void;
  toggleAutoTitle: () => void;
  toggleStreaming: () => void;
  toggleSound: () => void;
  
  // Voice actions
  toggleVoiceInput: () => void;
  toggleVoiceOutput: () => void;
  setVoiceLanguage: (language: string) => void;
  setVoiceSpeed: (speed: number) => void;
  
  // Privacy actions
  setDataRetention: (retention: UserPreferences['dataRetention']) => void;
  toggleAnalytics: () => void;
  toggleCrashReporting: () => void;
  
  // Accessibility actions
  toggleHighContrast: () => void;
  toggleReducedMotion: () => void;
  toggleScreenReaderOptimized: () => void;
  toggleKeyboardNavigation: () => void;
  
  // Feature flags
  enableExperimentalFeature: (feature: string) => void;
  disableExperimentalFeature: (feature: string) => void;
  enableBetaFeature: (feature: string) => void;
  disableBetaFeature: (feature: string) => void;
  
  // Bulk actions
  resetPreferences: () => void;
  importPreferences: (preferences: Partial<UserPreferences>) => void;
  exportPreferences: () => UserPreferences;
}/
/ Default preferences
const defaultPreferences: UserPreferences = {
  // AI Provider defaults
  preferredProvider: null,
  preferredModel: null,
  temperature: 0.7,
  maxTokens: 2048,
  
  // Chat behavior defaults
  autoSave: true,
  autoTitle: true,
  streamingEnabled: true,
  soundEnabled: false,
  
  // Voice defaults
  voiceInputEnabled: false,
  voiceOutputEnabled: false,
  voiceLanguage: 'en-US',
  voiceSpeed: 1.0,
  
  // Privacy defaults
  dataRetention: '30days',
  analyticsEnabled: true,
  crashReportingEnabled: true,
  
  // Accessibility defaults
  highContrast: false,
  reducedMotion: false,
  screenReaderOptimized: false,
  keyboardNavigation: true,
  
  // Feature flags
  experimentalFeatures: [],
  betaFeatures: [],
};

// Create the preferences store
export const usePreferencesStore = create<UserPreferences & PreferencesActions>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...defaultPreferences,

        // AI Provider actions
        setPreferredProvider: (provider: string | null) =>
          set((state) => {
            state.preferredProvider = provider;
          }),

        setPreferredModel: (model: string | null) =>
          set((state) => {
            state.preferredModel = model;
          }),

        setTemperature: (temperature: number) =>
          set((state) => {
            state.temperature = Math.max(0, Math.min(2, temperature));
          }),

        setMaxTokens: (maxTokens: number) =>
          set((state) => {
            state.maxTokens = Math.max(1, Math.min(8192, maxTokens));
          }),

        // Chat behavior actions
        toggleAutoSave: () =>
          set((state) => {
            state.autoSave = !state.autoSave;
          }),

        toggleAutoTitle: () =>
          set((state) => {
            state.autoTitle = !state.autoTitle;
          }),

        toggleStreaming: () =>
          set((state) => {
            state.streamingEnabled = !state.streamingEnabled;
          }),

        toggleSound: () =>
          set((state) => {
            state.soundEnabled = !state.soundEnabled;
          }),

        // Voice actions
        toggleVoiceInput: () =>
          set((state) => {
            state.voiceInputEnabled = !state.voiceInputEnabled;
          }),

        toggleVoiceOutput: () =>
          set((state) => {
            state.voiceOutputEnabled = !state.voiceOutputEnabled;
          }),

        setVoiceLanguage: (language: string) =>
          set((state) => {
            state.voiceLanguage = language;
          }),

        setVoiceSpeed: (speed: number) =>
          set((state) => {
            state.voiceSpeed = Math.max(0.5, Math.min(2.0, speed));
          }),

        // Privacy actions
        setDataRetention: (retention: UserPreferences['dataRetention']) =>
          set((state) => {
            state.dataRetention = retention;
          }),

        toggleAnalytics: () =>
          set((state) => {
            state.analyticsEnabled = !state.analyticsEnabled;
          }),

        toggleCrashReporting: () =>
          set((state) => {
            state.crashReportingEnabled = !state.crashReportingEnabled;
          }),

        // Accessibility actions
        toggleHighContrast: () =>
          set((state) => {
            state.highContrast = !state.highContrast;
          }),

        toggleReducedMotion: () =>
          set((state) => {
            state.reducedMotion = !state.reducedMotion;
          }),

        toggleScreenReaderOptimized: () =>
          set((state) => {
            state.screenReaderOptimized = !state.screenReaderOptimized;
          }),

        toggleKeyboardNavigation: () =>
          set((state) => {
            state.keyboardNavigation = !state.keyboardNavigation;
          }),

        // Feature flag actions
        enableExperimentalFeature: (feature: string) =>
          set((state) => {
            if (!state.experimentalFeatures.includes(feature)) {
              state.experimentalFeatures.push(feature);
            }
          }),

        disableExperimentalFeature: (feature: string) =>
          set((state) => {
            state.experimentalFeatures = state.experimentalFeatures.filter(
              (f) => f !== feature
            );
          }),

        enableBetaFeature: (feature: string) =>
          set((state) => {
            if (!state.betaFeatures.includes(feature)) {
              state.betaFeatures.push(feature);
            }
          }),

        disableBetaFeature: (feature: string) =>
          set((state) => {
            state.betaFeatures = state.betaFeatures.filter((f) => f !== feature);
          }),

        // Bulk actions
        resetPreferences: () =>
          set((state) => {
            Object.assign(state, defaultPreferences);
          }),

        importPreferences: (preferences: Partial<UserPreferences>) =>
          set((state) => {
            Object.assign(state, preferences);
          }),

        exportPreferences: () => {
          const state = get();
          const {
            setPreferredProvider,
            setPreferredModel,
            setTemperature,
            setMaxTokens,
            toggleAutoSave,
            toggleAutoTitle,
            toggleStreaming,
            toggleSound,
            toggleVoiceInput,
            toggleVoiceOutput,
            setVoiceLanguage,
            setVoiceSpeed,
            setDataRetention,
            toggleAnalytics,
            toggleCrashReporting,
            toggleHighContrast,
            toggleReducedMotion,
            toggleScreenReaderOptimized,
            toggleKeyboardNavigation,
            enableExperimentalFeature,
            disableExperimentalFeature,
            enableBetaFeature,
            disableBetaFeature,
            resetPreferences,
            importPreferences,
            exportPreferences,
            ...preferences
          } = state;
          return preferences;
        },
      })),
      {
        name: 'user-preferences',
        // Persist all preferences
        partialize: (state) => {
          const {
            setPreferredProvider,
            setPreferredModel,
            setTemperature,
            setMaxTokens,
            toggleAutoSave,
            toggleAutoTitle,
            toggleStreaming,
            toggleSound,
            toggleVoiceInput,
            toggleVoiceOutput,
            setVoiceLanguage,
            setVoiceSpeed,
            setDataRetention,
            toggleAnalytics,
            toggleCrashReporting,
            toggleHighContrast,
            toggleReducedMotion,
            toggleScreenReaderOptimized,
            toggleKeyboardNavigation,
            enableExperimentalFeature,
            disableExperimentalFeature,
            enableBetaFeature,
            disableBetaFeature,
            resetPreferences,
            importPreferences,
            exportPreferences,
            ...preferences
          } = state;
          return preferences;
        },
      }
    ),
    {
      name: 'Preferences Store',
    }
  )
);

// Selectors for optimized subscriptions
export const preferencesSelectors = {
  aiProvider: (state: UserPreferences & PreferencesActions) => ({
    provider: state.preferredProvider,
    model: state.preferredModel,
    temperature: state.temperature,
    maxTokens: state.maxTokens,
    setProvider: state.setPreferredProvider,
    setModel: state.setPreferredModel,
    setTemperature: state.setTemperature,
    setMaxTokens: state.setMaxTokens,
  }),
  
  chatBehavior: (state: UserPreferences & PreferencesActions) => ({
    autoSave: state.autoSave,
    autoTitle: state.autoTitle,
    streamingEnabled: state.streamingEnabled,
    soundEnabled: state.soundEnabled,
    toggleAutoSave: state.toggleAutoSave,
    toggleAutoTitle: state.toggleAutoTitle,
    toggleStreaming: state.toggleStreaming,
    toggleSound: state.toggleSound,
  }),
  
  voice: (state: UserPreferences & PreferencesActions) => ({
    inputEnabled: state.voiceInputEnabled,
    outputEnabled: state.voiceOutputEnabled,
    language: state.voiceLanguage,
    speed: state.voiceSpeed,
    toggleInput: state.toggleVoiceInput,
    toggleOutput: state.toggleVoiceOutput,
    setLanguage: state.setVoiceLanguage,
    setSpeed: state.setVoiceSpeed,
  }),
  
  accessibility: (state: UserPreferences & PreferencesActions) => ({
    highContrast: state.highContrast,
    reducedMotion: state.reducedMotion,
    screenReaderOptimized: state.screenReaderOptimized,
    keyboardNavigation: state.keyboardNavigation,
    toggleHighContrast: state.toggleHighContrast,
    toggleReducedMotion: state.toggleReducedMotion,
    toggleScreenReaderOptimized: state.toggleScreenReaderOptimized,
    toggleKeyboardNavigation: state.toggleKeyboardNavigation,
  }),
};