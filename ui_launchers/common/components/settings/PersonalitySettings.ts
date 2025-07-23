// Shared Personality Settings Component
// Framework-agnostic personality configuration interface

import { 
  KarenSettings, 
  PersonalityTone, 
  PersonalityVerbosity, 
  Theme 
} from '../../abstractions/types';
import { validator, errorHandler } from '../../abstractions/utils';

export interface PersonalitySettingsOptions {
  showPresets?: boolean;
  enableCustomInstructions?: boolean;
  maxCustomInstructionsLength?: number;
  showExamples?: boolean;
}

export interface PersonalityPreset {
  id: string;
  name: string;
  description: string;
  tone: PersonalityTone;
  verbosity: PersonalityVerbosity;
  customInstructions: string;
  example: string;
}

export interface PersonalitySettingsState {
  selectedTone: PersonalityTone;
  selectedVerbosity: PersonalityVerbosity;
  customInstructions: string;
  selectedPreset: string | null;
  isCustom: boolean;
  errors: Record<string, string>;
}

export interface PersonalitySettingsCallbacks {
  onToneChange?: (tone: PersonalityTone) => void;
  onVerbosityChange?: (verbosity: PersonalityVerbosity) => void;
  onCustomInstructionsChange?: (instructions: string) => void;
  onPresetSelect?: (preset: PersonalityPreset) => void;
}

export class SharedPersonalitySettings {
  private state: PersonalitySettingsState;
  private options: PersonalitySettingsOptions;
  private callbacks: PersonalitySettingsCallbacks;
  private theme: Theme;

  constructor(
    settings: KarenSettings,
    theme: Theme,
    options: PersonalitySettingsOptions = {},
    callbacks: PersonalitySettingsCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      showPresets: true,
      enableCustomInstructions: true,
      maxCustomInstructionsLength: 1000,
      showExamples: true,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      selectedTone: settings.personalityTone,
      selectedVerbosity: settings.personalityVerbosity,
      customInstructions: settings.customPersonaInstructions,
      selectedPreset: this.findMatchingPreset(settings),
      isCustom: this.isCustomConfiguration(settings),
      errors: {}
    };
  }

  // Get current state
  getState(): PersonalitySettingsState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<PersonalitySettingsState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Update personality tone
  updateTone(tone: PersonalityTone): void {
    this.updateState({ 
      selectedTone: tone,
      selectedPreset: null,
      isCustom: true
    });

    if (this.callbacks.onToneChange) {
      this.callbacks.onToneChange(tone);
    }
  }

  // Update personality verbosity
  updateVerbosity(verbosity: PersonalityVerbosity): void {
    this.updateState({ 
      selectedVerbosity: verbosity,
      selectedPreset: null,
      isCustom: true
    });

    if (this.callbacks.onVerbosityChange) {
      this.callbacks.onVerbosityChange(verbosity);
    }
  }

  // Update custom instructions
  updateCustomInstructions(instructions: string): void {
    // Validate length
    const errors: Record<string, string> = {};
    
    if (this.options.maxCustomInstructionsLength && 
        instructions.length > this.options.maxCustomInstructionsLength) {
      errors.customInstructions = `Instructions too long (${instructions.length}/${this.options.maxCustomInstructionsLength} characters)`;
    }

    this.updateState({ 
      customInstructions: instructions,
      selectedPreset: null,
      isCustom: true,
      errors
    });

    if (Object.keys(errors).length === 0 && this.callbacks.onCustomInstructionsChange) {
      this.callbacks.onCustomInstructionsChange(instructions);
    }
  }

  // Select a personality preset
  selectPreset(presetId: string): void {
    const preset = this.getPresets().find(p => p.id === presetId);
    
    if (preset) {
      this.updateState({
        selectedTone: preset.tone,
        selectedVerbosity: preset.verbosity,
        customInstructions: preset.customInstructions,
        selectedPreset: presetId,
        isCustom: false,
        errors: {}
      });

      if (this.callbacks.onPresetSelect) {
        this.callbacks.onPresetSelect(preset);
      }

      // Trigger individual callbacks
      if (this.callbacks.onToneChange) {
        this.callbacks.onToneChange(preset.tone);
      }
      if (this.callbacks.onVerbosityChange) {
        this.callbacks.onVerbosityChange(preset.verbosity);
      }
      if (this.callbacks.onCustomInstructionsChange) {
        this.callbacks.onCustomInstructionsChange(preset.customInstructions);
      }
    }
  }

  // Get available personality presets
  getPresets(): PersonalityPreset[] {
    return [
      {
        id: 'professional',
        name: 'Professional Assistant',
        description: 'Formal, concise, and business-focused',
        tone: 'formal',
        verbosity: 'concise',
        customInstructions: 'Be professional and direct. Focus on providing clear, actionable information.',
        example: 'I can help you with that task. Here are the key steps you need to follow...'
      },
      {
        id: 'friendly',
        name: 'Friendly Companion',
        description: 'Warm, conversational, and supportive',
        tone: 'friendly',
        verbosity: 'balanced',
        customInstructions: 'Be warm and supportive. Show genuine interest in helping and use a conversational tone.',
        example: 'I\'d be happy to help you with that! Let me walk you through this step by step...'
      },
      {
        id: 'expert',
        name: 'Technical Expert',
        description: 'Detailed, thorough, and knowledgeable',
        tone: 'neutral',
        verbosity: 'detailed',
        customInstructions: 'Provide comprehensive explanations with technical details. Include context and reasoning.',
        example: 'This is an interesting question that involves several concepts. Let me explain the underlying principles and then provide a detailed solution...'
      },
      {
        id: 'casual',
        name: 'Casual Friend',
        description: 'Relaxed, humorous, and easy-going',
        tone: 'humorous',
        verbosity: 'balanced',
        customInstructions: 'Keep things light and fun. Use humor when appropriate and maintain a relaxed tone.',
        example: 'Oh, that\'s a fun one! Let me help you figure this out - it\'s actually pretty straightforward once you know the trick...'
      },
      {
        id: 'tutor',
        name: 'Patient Tutor',
        description: 'Educational, encouraging, and thorough',
        tone: 'friendly',
        verbosity: 'detailed',
        customInstructions: 'Focus on teaching and explaining concepts clearly. Be patient and encouraging.',
        example: 'Great question! This is a perfect opportunity to learn something new. Let me break this down into manageable pieces...'
      }
    ];
  }

  // Get tone options with descriptions
  getToneOptions(): Array<{ value: PersonalityTone; label: string; description: string }> {
    return [
      {
        value: 'neutral',
        label: 'Neutral',
        description: 'Balanced and professional tone'
      },
      {
        value: 'friendly',
        label: 'Friendly',
        description: 'Warm and conversational tone'
      },
      {
        value: 'formal',
        label: 'Formal',
        description: 'Professional and business-like tone'
      },
      {
        value: 'humorous',
        label: 'Humorous',
        description: 'Light-hearted with occasional humor'
      }
    ];
  }

  // Get verbosity options with descriptions
  getVerbosityOptions(): Array<{ value: PersonalityVerbosity; label: string; description: string }> {
    return [
      {
        value: 'concise',
        label: 'Concise',
        description: 'Brief and to-the-point responses'
      },
      {
        value: 'balanced',
        label: 'Balanced',
        description: 'Moderate detail level'
      },
      {
        value: 'detailed',
        label: 'Detailed',
        description: 'Comprehensive and thorough responses'
      }
    ];
  }

  // Get example response for current settings
  getExampleResponse(): string {
    const { selectedTone, selectedVerbosity } = this.state;
    
    const examples: Record<PersonalityTone, Record<PersonalityVerbosity, string>> = {
      neutral: {
        concise: 'I can help you with that. Here\'s what you need to do.',
        balanced: 'I can help you with that task. Let me provide you with the necessary steps and some context.',
        detailed: 'I can certainly help you with that task. Let me provide you with a comprehensive explanation of the process, including the reasoning behind each step and potential alternatives you might consider.'
      },
      friendly: {
        concise: 'I\'d love to help! Here\'s what you need to do.',
        balanced: 'I\'d be happy to help you with that! Let me walk you through the process step by step.',
        detailed: 'I\'d absolutely love to help you with that! This is actually a really interesting question, and I\'m excited to walk you through the entire process. Let me give you a comprehensive explanation with all the details you might need.'
      },
      formal: {
        concise: 'I shall assist you with this matter. Please proceed as follows.',
        balanced: 'I shall be pleased to assist you with this matter. Allow me to provide you with the appropriate guidance and necessary steps.',
        detailed: 'I shall be pleased to provide you with comprehensive assistance regarding this matter. Please allow me to present you with a detailed explanation of the process, including all relevant considerations and methodological approaches.'
      },
      humorous: {
        concise: 'Sure thing! Here\'s the scoop.',
        balanced: 'Absolutely! This is actually pretty fun to explain. Let me break it down for you in a way that won\'t put you to sleep.',
        detailed: 'Oh, this is a great question! You know what? This reminds me of that time when... well, never mind that story for now. Let me give you the full rundown with all the juicy details and maybe a few fun facts along the way!'
      }
    };

    return examples[selectedTone][selectedVerbosity];
  }

  // Validate current settings
  validate(): Record<string, string> {
    const errors: Record<string, string> = {};
    
    if (this.options.maxCustomInstructionsLength && 
        this.state.customInstructions.length > this.options.maxCustomInstructionsLength) {
      errors.customInstructions = `Instructions too long (${this.state.customInstructions.length}/${this.options.maxCustomInstructionsLength} characters)`;
    }

    return errors;
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-personality-settings'];
    
    if (this.state.isCustom) {
      classes.push('karen-personality-settings-custom');
    }
    
    if (Object.keys(this.state.errors).length > 0) {
      classes.push('karen-personality-settings-errors');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.theme.colors.surface,
      color: this.theme.colors.text,
      padding: this.theme.spacing.md,
      borderRadius: this.theme.borderRadius,
      border: `1px solid ${this.theme.colors.border}`,
      fontFamily: this.theme.typography.fontFamily
    };
  }

  // Get render data
  getRenderData(): PersonalitySettingsRenderData {
    return {
      state: this.getState(),
      options: this.options,
      presets: this.options.showPresets ? this.getPresets() : [],
      toneOptions: this.getToneOptions(),
      verbosityOptions: this.getVerbosityOptions(),
      exampleResponse: this.options.showExamples ? this.getExampleResponse() : '',
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onToneChange: (tone: PersonalityTone) => this.updateTone(tone),
        onVerbosityChange: (verbosity: PersonalityVerbosity) => this.updateVerbosity(verbosity),
        onCustomInstructionsChange: (instructions: string) => this.updateCustomInstructions(instructions),
        onPresetSelect: (presetId: string) => this.selectPreset(presetId)
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Update from settings
  updateFromSettings(settings: KarenSettings): void {
    this.updateState({
      selectedTone: settings.personalityTone,
      selectedVerbosity: settings.personalityVerbosity,
      customInstructions: settings.customPersonaInstructions,
      selectedPreset: this.findMatchingPreset(settings),
      isCustom: this.isCustomConfiguration(settings),
      errors: {}
    });
  }

  // Private helper methods
  private findMatchingPreset(settings: KarenSettings): string | null {
    const presets = this.getPresets();
    
    for (const preset of presets) {
      if (preset.tone === settings.personalityTone &&
          preset.verbosity === settings.personalityVerbosity &&
          preset.customInstructions === settings.customPersonaInstructions) {
        return preset.id;
      }
    }
    
    return null;
  }

  private isCustomConfiguration(settings: KarenSettings): boolean {
    return this.findMatchingPreset(settings) === null;
  }
}

// Supporting interfaces
export interface PersonalitySettingsRenderData {
  state: PersonalitySettingsState;
  options: PersonalitySettingsOptions;
  presets: PersonalityPreset[];
  toneOptions: Array<{ value: PersonalityTone; label: string; description: string }>;
  verbosityOptions: Array<{ value: PersonalityVerbosity; label: string; description: string }>;
  exampleResponse: string;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onToneChange: (tone: PersonalityTone) => void;
    onVerbosityChange: (verbosity: PersonalityVerbosity) => void;
    onCustomInstructionsChange: (instructions: string) => void;
    onPresetSelect: (presetId: string) => void;
  };
}

// Utility functions
export function createPersonalitySettings(
  settings: KarenSettings,
  theme: Theme,
  options: PersonalitySettingsOptions = {},
  callbacks: PersonalitySettingsCallbacks = {}
): SharedPersonalitySettings {
  return new SharedPersonalitySettings(settings, theme, options, callbacks);
}

export function getPersonalityPreview(
  tone: PersonalityTone,
  verbosity: PersonalityVerbosity,
  customInstructions: string
): string {
  const toneDescriptions = {
    neutral: 'balanced',
    friendly: 'warm',
    formal: 'professional',
    humorous: 'playful'
  };

  const verbosityDescriptions = {
    concise: 'brief',
    balanced: 'moderate',
    detailed: 'comprehensive'
  };

  let preview = `Karen will be ${toneDescriptions[tone]} and ${verbosityDescriptions[verbosity]}`;
  
  if (customInstructions.trim()) {
    preview += `, with custom behavior: "${customInstructions.substring(0, 50)}${customInstructions.length > 50 ? '...' : ''}"`;
  }

  return preview;
}

export function validatePersonalitySettings(
  tone: PersonalityTone,
  verbosity: PersonalityVerbosity,
  customInstructions: string,
  maxLength: number = 1000
): string[] {
  const errors: string[] = [];

  const validTones: PersonalityTone[] = ['neutral', 'friendly', 'formal', 'humorous'];
  if (!validTones.includes(tone)) {
    errors.push('Invalid personality tone');
  }

  const validVerbosity: PersonalityVerbosity[] = ['concise', 'balanced', 'detailed'];
  if (!validVerbosity.includes(verbosity)) {
    errors.push('Invalid verbosity level');
  }

  if (customInstructions.length > maxLength) {
    errors.push(`Custom instructions too long (${customInstructions.length}/${maxLength} characters)`);
  }

  return errors;
}