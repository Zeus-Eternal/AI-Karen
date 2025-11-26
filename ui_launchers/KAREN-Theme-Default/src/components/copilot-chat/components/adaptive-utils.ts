import { ExpertiseLevel } from '../types/copilot';

interface UIAdaptationPolicy {
  simplifiedUI: boolean;
  guidedMode: boolean;
  showAdvancedFeatures: boolean;
  showDebugInfo: boolean;
  showMemoryOps: boolean;
  showTimestamps: boolean;
  maxMessageHistory: number;
  enableAnimations: boolean;
  enableSoundEffects: boolean;
  enableKeyboardShortcuts: boolean;
  autoScroll: boolean;
  markdownSupport: boolean;
  codeHighlighting: boolean;
  imagePreview: boolean;
}

// Helper function to get default policy based on expertise level
export function getDefaultPolicy(level: ExpertiseLevel): UIAdaptationPolicy {
  switch (level) {
    case 'beginner':
      return {
        simplifiedUI: true,
        guidedMode: true,
        showAdvancedFeatures: false,
        showDebugInfo: false,
        showMemoryOps: false,
        showTimestamps: true,
        maxMessageHistory: 20,
        enableAnimations: true,
        enableSoundEffects: true,
        enableKeyboardShortcuts: false,
        autoScroll: true,
        markdownSupport: true,
        codeHighlighting: true,
        imagePreview: true
      };
    case 'intermediate':
      return {
        simplifiedUI: false,
        guidedMode: true,
        showAdvancedFeatures: true,
        showDebugInfo: false,
        showMemoryOps: false,
        showTimestamps: true,
        maxMessageHistory: 50,
        enableAnimations: true,
        enableSoundEffects: false,
        enableKeyboardShortcuts: true,
        autoScroll: true,
        markdownSupport: true,
        codeHighlighting: true,
        imagePreview: true
      };
    case 'advanced':
      return {
        simplifiedUI: false,
        guidedMode: false,
        showAdvancedFeatures: true,
        showDebugInfo: true,
        showMemoryOps: true,
        showTimestamps: true,
        maxMessageHistory: 100,
        enableAnimations: true,
        enableSoundEffects: false,
        enableKeyboardShortcuts: true,
        autoScroll: true,
        markdownSupport: true,
        codeHighlighting: true,
        imagePreview: true
      };
    case 'expert':
      return {
        simplifiedUI: false,
        guidedMode: false,
        showAdvancedFeatures: true,
        showDebugInfo: true,
        showMemoryOps: true,
        showTimestamps: true,
        maxMessageHistory: 200,
        enableAnimations: false,
        enableSoundEffects: false,
        enableKeyboardShortcuts: true,
        autoScroll: false,
        markdownSupport: true,
        codeHighlighting: true,
        imagePreview: true
      };
    default:
      return getDefaultPolicy('intermediate' as ExpertiseLevel);
  }
}

export type { UIAdaptationPolicy };