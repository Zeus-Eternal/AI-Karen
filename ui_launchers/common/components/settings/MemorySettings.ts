// Shared Memory Settings Component
// Framework-agnostic memory configuration interface

import { 
  KarenSettings, 
  MemoryDepth, 
  Theme 
} from '../../abstractions/types';
import { validator, errorHandler, debounce } from '../../abstractions/utils';

export interface MemorySettingsOptions {
  enablePersonalFacts?: boolean;
  maxPersonalFacts?: number;
  enableFactSuggestions?: boolean;
  showMemoryStats?: boolean;
  enableFactValidation?: boolean;
}

export interface PersonalFact {
  id: string;
  text: string;
  category?: string;
  dateAdded: Date;
  isVerified: boolean;
  source: 'user' | 'ai_suggested' | 'conversation';
}

export interface MemorySettingsState {
  selectedDepth: MemoryDepth;
  personalFacts: PersonalFact[];
  newFactText: string;
  suggestedFacts: string[];
  showSuggestions: boolean;
  errors: Record<string, string>;
  isAddingFact: boolean;
}

export interface MemorySettingsCallbacks {
  onDepthChange?: (depth: MemoryDepth) => void;
  onFactAdd?: (fact: string) => void;
  onFactRemove?: (factId: string) => void;
  onFactEdit?: (factId: string, newText: string) => void;
  onSuggestedFactAccept?: (fact: string) => void;
  onSuggestedFactReject?: (fact: string) => void;
}

export class SharedMemorySettings {
  private state: MemorySettingsState;
  private options: MemorySettingsOptions;
  private callbacks: MemorySettingsCallbacks;
  private theme: Theme;
  private debouncedValidation: (text: string) => void;

  constructor(
    settings: KarenSettings,
    theme: Theme,
    options: MemorySettingsOptions = {},
    callbacks: MemorySettingsCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      enablePersonalFacts: true,
      maxPersonalFacts: 50,
      enableFactSuggestions: true,
      showMemoryStats: true,
      enableFactValidation: true,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      selectedDepth: settings.memoryDepth,
      personalFacts: this.convertFactsToObjects(settings.personalFacts),
      newFactText: '',
      suggestedFacts: [],
      showSuggestions: false,
      errors: {},
      isAddingFact: false
    };

    // Create debounced validation
    this.debouncedValidation = debounce((text: string) => {
      this.validateNewFact(text);
    }, 300);

    // Load suggested facts if enabled
    if (this.options.enableFactSuggestions) {
      this.loadSuggestedFacts();
    }
  }

  // Get current state
  getState(): MemorySettingsState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<MemorySettingsState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Update memory depth
  updateDepth(depth: MemoryDepth): void {
    this.updateState({ selectedDepth: depth });

    if (this.callbacks.onDepthChange) {
      this.callbacks.onDepthChange(depth);
    }
  }

  // Update new fact text
  updateNewFactText(text: string): void {
    this.updateState({ 
      newFactText: text,
      errors: { ...this.state.errors, newFact: '' }
    });

    if (this.options.enableFactValidation) {
      this.debouncedValidation(text);
    }
  }

  // Add a new personal fact
  addPersonalFact(): void {
    const text = this.state.newFactText.trim();
    
    if (!text) {
      this.updateState({
        errors: { ...this.state.errors, newFact: 'Please enter a fact' }
      });
      return;
    }

    // Validate fact
    const validationError = this.validateFact(text);
    if (validationError) {
      this.updateState({
        errors: { ...this.state.errors, newFact: validationError }
      });
      return;
    }

    // Check for duplicates
    if (this.isDuplicateFact(text)) {
      this.updateState({
        errors: { ...this.state.errors, newFact: 'This fact already exists' }
      });
      return;
    }

    // Check max limit
    if (this.options.maxPersonalFacts && 
        this.state.personalFacts.length >= this.options.maxPersonalFacts) {
      this.updateState({
        errors: { ...this.state.errors, newFact: `Maximum ${this.options.maxPersonalFacts} facts allowed` }
      });
      return;
    }

    const newFact: PersonalFact = {
      id: this.generateFactId(),
      text,
      dateAdded: new Date(),
      isVerified: true,
      source: 'user'
    };

    this.updateState({
      personalFacts: [...this.state.personalFacts, newFact],
      newFactText: '',
      errors: { ...this.state.errors, newFact: '' },
      isAddingFact: false
    });

    if (this.callbacks.onFactAdd) {
      this.callbacks.onFactAdd(text);
    }
  }

  // Remove a personal fact
  removePersonalFact(factId: string): void {
    const updatedFacts = this.state.personalFacts.filter(fact => fact.id !== factId);
    this.updateState({ personalFacts: updatedFacts });

    if (this.callbacks.onFactRemove) {
      this.callbacks.onFactRemove(factId);
    }
  }

  // Edit a personal fact
  editPersonalFact(factId: string, newText: string): void {
    const validationError = this.validateFact(newText);
    if (validationError) {
      this.updateState({
        errors: { ...this.state.errors, [factId]: validationError }
      });
      return;
    }

    const updatedFacts = this.state.personalFacts.map(fact =>
      fact.id === factId 
        ? { ...fact, text: newText.trim() }
        : fact
    );

    this.updateState({ 
      personalFacts: updatedFacts,
      errors: { ...this.state.errors, [factId]: '' }
    });

    if (this.callbacks.onFactEdit) {
      this.callbacks.onFactEdit(factId, newText.trim());
    }
  }

  // Accept a suggested fact
  acceptSuggestedFact(fact: string): void {
    // Add as a new fact
    const newFact: PersonalFact = {
      id: this.generateFactId(),
      text: fact,
      dateAdded: new Date(),
      isVerified: false,
      source: 'ai_suggested'
    };

    this.updateState({
      personalFacts: [...this.state.personalFacts, newFact],
      suggestedFacts: this.state.suggestedFacts.filter(f => f !== fact)
    });

    if (this.callbacks.onSuggestedFactAccept) {
      this.callbacks.onSuggestedFactAccept(fact);
    }
  }

  // Reject a suggested fact
  rejectSuggestedFact(fact: string): void {
    this.updateState({
      suggestedFacts: this.state.suggestedFacts.filter(f => f !== fact)
    });

    if (this.callbacks.onSuggestedFactReject) {
      this.callbacks.onSuggestedFactReject(fact);
    }
  }

  // Toggle suggestions visibility
  toggleSuggestions(): void {
    this.updateState({ showSuggestions: !this.state.showSuggestions });
  }

  // Get memory depth options
  getDepthOptions(): Array<{ value: MemoryDepth; label: string; description: string }> {
    return [
      {
        value: 'short',
        label: 'Short',
        description: 'Remember recent conversation context (last 5-10 messages)'
      },
      {
        value: 'medium',
        label: 'Medium',
        description: 'Remember moderate conversation history (last 20-30 messages)'
      },
      {
        value: 'long',
        label: 'Long',
        description: 'Remember extensive conversation history (last 50+ messages)'
      }
    ];
  }

  // Get memory statistics
  getMemoryStats(): MemoryStats {
    const facts = this.state.personalFacts;
    const totalFacts = facts.length;
    const verifiedFacts = facts.filter(f => f.isVerified).length;
    const suggestedFacts = facts.filter(f => f.source === 'ai_suggested').length;
    const userFacts = facts.filter(f => f.source === 'user').length;
    
    const categories = facts.reduce((acc, fact) => {
      const category = fact.category || 'General';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const averageFactLength = totalFacts > 0 
      ? Math.round(facts.reduce((sum, fact) => sum + fact.text.length, 0) / totalFacts)
      : 0;

    return {
      totalFacts,
      verifiedFacts,
      suggestedFacts,
      userFacts,
      categories,
      averageFactLength,
      maxFacts: this.options.maxPersonalFacts || 0,
      remainingSlots: Math.max(0, (this.options.maxPersonalFacts || 0) - totalFacts)
    };
  }

  // Get fact categories
  getFactCategories(): string[] {
    const categories = new Set<string>();
    this.state.personalFacts.forEach(fact => {
      if (fact.category) {
        categories.add(fact.category);
      }
    });
    return Array.from(categories).sort();
  }

  // Validate a fact
  private validateFact(text: string): string | null {
    if (!text.trim()) {
      return 'Fact cannot be empty';
    }

    if (text.length < 3) {
      return 'Fact must be at least 3 characters long';
    }

    if (text.length > 200) {
      return 'Fact must be less than 200 characters';
    }

    // Check for inappropriate content (basic check)
    const inappropriateWords = ['password', 'ssn', 'social security'];
    const lowerText = text.toLowerCase();
    
    for (const word of inappropriateWords) {
      if (lowerText.includes(word)) {
        return 'Please avoid including sensitive information';
      }
    }

    return null;
  }

  // Validate new fact input
  private validateNewFact(text: string): void {
    const error = this.validateFact(text);
    this.updateState({
      errors: { ...this.state.errors, newFact: error || '' }
    });
  }

  // Check if fact is duplicate
  private isDuplicateFact(text: string): boolean {
    const normalizedText = text.toLowerCase().trim();
    return this.state.personalFacts.some(fact => 
      fact.text.toLowerCase().trim() === normalizedText
    );
  }

  // Generate unique fact ID
  private generateFactId(): string {
    return `fact-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Convert string facts to fact objects
  private convertFactsToObjects(facts: string[]): PersonalFact[] {
    return facts.map((fact, index) => ({
      id: `fact-${index}-${Date.now()}`,
      text: fact,
      dateAdded: new Date(),
      isVerified: true,
      source: 'user' as const
    }));
  }

  // Load suggested facts (would typically come from API)
  private loadSuggestedFacts(): void {
    // This would typically load from an API or storage
    // For now, we'll use some example suggestions
    const suggestions = [
      'I prefer morning meetings over afternoon ones',
      'I work in the technology industry',
      'I enjoy learning about new programming languages',
      'I prefer detailed explanations over brief summaries'
    ];

    this.updateState({ suggestedFacts: suggestions });
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-memory-settings'];
    
    if (this.state.isAddingFact) {
      classes.push('karen-memory-settings-adding');
    }
    
    if (Object.keys(this.state.errors).length > 0) {
      classes.push('karen-memory-settings-errors');
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
  getRenderData(): MemorySettingsRenderData {
    return {
      state: this.getState(),
      options: this.options,
      depthOptions: this.getDepthOptions(),
      stats: this.options.showMemoryStats ? this.getMemoryStats() : null,
      categories: this.getFactCategories(),
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onDepthChange: (depth: MemoryDepth) => this.updateDepth(depth),
        onNewFactTextChange: (text: string) => this.updateNewFactText(text),
        onFactAdd: () => this.addPersonalFact(),
        onFactRemove: (factId: string) => this.removePersonalFact(factId),
        onFactEdit: (factId: string, text: string) => this.editPersonalFact(factId, text),
        onSuggestedFactAccept: (fact: string) => this.acceptSuggestedFact(fact),
        onSuggestedFactReject: (fact: string) => this.rejectSuggestedFact(fact),
        onToggleSuggestions: () => this.toggleSuggestions()
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
      selectedDepth: settings.memoryDepth,
      personalFacts: this.convertFactsToObjects(settings.personalFacts)
    });
  }

  // Export facts to array format
  exportFacts(): string[] {
    return this.state.personalFacts.map(fact => fact.text);
  }
}

// Supporting interfaces
export interface MemoryStats {
  totalFacts: number;
  verifiedFacts: number;
  suggestedFacts: number;
  userFacts: number;
  categories: Record<string, number>;
  averageFactLength: number;
  maxFacts: number;
  remainingSlots: number;
}

export interface MemorySettingsRenderData {
  state: MemorySettingsState;
  options: MemorySettingsOptions;
  depthOptions: Array<{ value: MemoryDepth; label: string; description: string }>;
  stats: MemoryStats | null;
  categories: string[];
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onDepthChange: (depth: MemoryDepth) => void;
    onNewFactTextChange: (text: string) => void;
    onFactAdd: () => void;
    onFactRemove: (factId: string) => void;
    onFactEdit: (factId: string, text: string) => void;
    onSuggestedFactAccept: (fact: string) => void;
    onSuggestedFactReject: (fact: string) => void;
    onToggleSuggestions: () => void;
  };
}

// Utility functions
export function createMemorySettings(
  settings: KarenSettings,
  theme: Theme,
  options: MemorySettingsOptions = {},
  callbacks: MemorySettingsCallbacks = {}
): SharedMemorySettings {
  return new SharedMemorySettings(settings, theme, options, callbacks);
}

export function categorizePersonalFact(fact: string): string {
  const categories = {
    work: ['job', 'work', 'career', 'office', 'company', 'colleague', 'boss', 'project'],
    personal: ['family', 'spouse', 'child', 'parent', 'sibling', 'friend', 'relationship'],
    hobbies: ['hobby', 'interest', 'enjoy', 'like', 'love', 'passion', 'sport', 'game'],
    preferences: ['prefer', 'favorite', 'dislike', 'hate', 'always', 'never', 'usually'],
    health: ['health', 'medical', 'doctor', 'medication', 'allergy', 'diet', 'exercise'],
    location: ['live', 'home', 'address', 'city', 'country', 'location', 'travel']
  };

  const lowerFact = fact.toLowerCase();
  
  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.some(keyword => lowerFact.includes(keyword))) {
      return category.charAt(0).toUpperCase() + category.slice(1);
    }
  }
  
  return 'General';
}

export function generateFactSuggestions(conversationHistory: string[]): string[] {
  // This would typically use AI to analyze conversation history
  // For now, return some common suggestions
  return [
    'I prefer morning meetings',
    'I work remotely',
    'I have a pet',
    'I enjoy coffee',
    'I prefer detailed explanations'
  ];
}

export function validatePersonalFacts(facts: string[]): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  facts.forEach((fact, index) => {
    if (!fact.trim()) {
      errors.push(`Fact ${index + 1} is empty`);
    } else if (fact.length > 200) {
      errors.push(`Fact ${index + 1} is too long (${fact.length}/200 characters)`);
    }
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}