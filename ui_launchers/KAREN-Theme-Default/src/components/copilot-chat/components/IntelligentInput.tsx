import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import NextImage from 'next/image';
import {
  Send,
  Mic,
  Paperclip,
  Image as ImageIcon,
  Code,
  X,
  Loader2,
  Sparkles,
  Lightbulb,
  Zap,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useAdaptiveInterface } from './adaptive-interface-hooks';

interface IntelligentInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string, modality?: 'text' | 'code' | 'image' | 'audio') => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  modality?: 'text' | 'code' | 'image' | 'audio';
  onModalityChange?: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  onAttachFile?: (file: File) => void;
  onRecordAudio?: () => void;
  onCaptureImage?: () => void;
  suggestions?: string[];
  className?: string;
}

interface FileAttachment {
  id: string;
  file: File;
  preview?: string;
}

/**
 * IntelligentInput component that provides AI-enhanced input capabilities
 * with contextual suggestions, multi-modal input, and adaptive behavior.
 * Implements the Copilot-first intelligent input system.
 */
export const IntelligentInput: React.FC<IntelligentInputProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = 'Type your message...',
  disabled = false,
  isLoading = false,
  modality = 'text',
  onModalityChange,
  onAttachFile,
  onRecordAudio,
  onCaptureImage,
  suggestions = [],
  className
}) => {
  const { adaptationPolicy, expertiseLevel } = useAdaptiveInterface();
  const [isFocused, setIsFocused] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Handle form submission
  const handleSubmit = useCallback(() => {
    if (value.trim() || attachments.length > 0) {
      onSubmit(value, modality);
      onChange('');
      setAttachments([]);
    }
  }, [value, modality, onSubmit, onChange, attachments]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [value]);

  // Focus textarea when suggestions are shown
  useEffect(() => {
    if (showSuggestions && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [showSuggestions]);

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!adaptationPolicy.enableKeyboardShortcuts) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Enter to submit
      if (e.ctrlKey && e.key === 'Enter' && !disabled && !isLoading) {
        e.preventDefault();
        handleSubmit();
      }
      
      // Escape to cancel recording or close suggestions
      if (e.key === 'Escape') {
        if (isRecording) {
          setIsRecording(false);
        } else if (showSuggestions) {
          setShowSuggestions(false);
        }
      }
      
      // Tab to accept suggestion
      if (e.key === 'Tab' && showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        onChange(suggestions[0]);
        setShowSuggestions(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [disabled, isLoading, isRecording, showSuggestions, suggestions, onChange, adaptationPolicy.enableKeyboardShortcuts, handleSubmit]);

  // Handle file attachment
  const handleAttachFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const newAttachments: FileAttachment[] = Array.from(files).map(file => ({
        id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        file,
        preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
      }));
      
      setAttachments(prev => [...prev, ...newAttachments]);
      onAttachFile?.(files[0]);
    }
  }, [onAttachFile]);

  // Remove attachment
  const handleRemoveAttachment = useCallback((id: string) => {
    setAttachments(prev => {
      const attachment = prev.find(a => a.id === id);
      if (attachment?.preview) {
        URL.revokeObjectURL(attachment.preview);
      }
      return prev.filter(a => a.id !== id);
    });
  }, []);

  // Handle suggestion click
  const handleSuggestionClick = useCallback((suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
  }, [onChange]);

  // Handle modality change
  const handleModalityChange = useCallback((newModality: 'text' | 'code' | 'image' | 'audio') => {
    onModalityChange?.(newModality);
    
    // Special handling for image and audio modalities
    if (newModality === 'image') {
      onCaptureImage?.();
    } else if (newModality === 'audio') {
      onRecordAudio?.();
      setIsRecording(true);
    }
  }, [onModalityChange, onCaptureImage, onRecordAudio]);

  // Trigger file input click
  const triggerFileInput = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Get placeholder based on modality and expertise level
  const getPlaceholder = () => {
    if (adaptationPolicy.guidedMode) {
      switch (modality) {
        case 'text':
          return 'Type your message here...';
        case 'code':
          return 'Enter your code snippet...';
        case 'image':
          return 'Describe the image you want to upload...';
        case 'audio':
          return isRecording ? 'Recording... Click to stop' : 'Click to start recording...';
        default:
          return placeholder;
      }
    }
    
    return placeholder;
  };

  // Determine if advanced options should be shown
  const shouldShowAdvancedOptions = adaptationPolicy.showAdvancedFeatures && 
                                    expertiseLevel !== 'beginner';

  return (
    <div className={cn('intelligent-input-container', className)}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleAttachFile}
        multiple
        accept="image/*,audio/*,.pdf,.doc,.docx,.txt,.json,.xml,.html,.css,.js,.ts,.tsx,.jsx"
      />
      
      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div ref={suggestionsRef} className="suggestions-dropdown">
          <div className="suggestions-header">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium">Suggestions</span>
          </div>
          <div className="suggestions-list">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-item"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Main input container */}
      <div
        className={cn(
          'intelligent-input overflow-hidden transition-all duration-200',
          {
            'intelligent-input--focused': isFocused,
            'intelligent-input--disabled': disabled,
            'guided-mode': adaptationPolicy.guidedMode
          }
        )}
      >
        <div className="p-3">
          {/* Attachments */}
          {attachments.length > 0 && (
            <div className="input-attachments">
              {attachments.map(attachment => (
                <div
                  key={attachment.id}
                  className="attachment-item"
                >
                  <div className="attachment-badge">
                    {attachment.file.type.startsWith('image/') ? (
                      <ImageIcon className="h-3 w-3" />
                    ) : attachment.file.type.startsWith('audio/') ? (
                      <Mic className="h-3 w-3" />
                    ) : (
                      <Paperclip className="h-3 w-3" />
                    )}
                    <span className="attachment-name">
                      {attachment.file.name}
                    </span>
                    <button
                      className="attachment-remove"
                      onClick={() => handleRemoveAttachment(attachment.id)}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                  
                  {/* Image preview */}
                  {attachment.preview && (
                    <div className="attachment-preview">
                      <NextImage
                        src={attachment.preview}
                        alt={`Preview of ${attachment.file.name}`}
                        width={100}
                        height={100}
                        className="object-contain"
                        unoptimized
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Textarea input */}
          <div className="input-textarea-container">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={getPlaceholder()}
              disabled={disabled || isLoading}
              className={cn(
                'input-textarea',
                {
                  'input-textarea--large': adaptationPolicy.simplifiedUI,
                  'input-textarea--normal': !adaptationPolicy.simplifiedUI
                }
              )}
              rows={1}
            />
            
            {/* Submit button */}
            <button
              className={cn(
                'input-submit',
                {
                  'input-submit--disabled': (!value.trim() && attachments.length === 0) || disabled || isLoading,
                  'input-submit--loading': isLoading
                }
              )}
              onClick={handleSubmit}
              disabled={(!value.trim() && attachments.length === 0) || disabled || isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
          
          {/* Input options */}
          <div className="input-options">
            {/* Left side - Modality and attachment options */}
            <div className="input-options-left">
              {/* Modality selector */}
              {shouldShowAdvancedOptions && (
                <div className="modality-selector">
                  <button
                    className={cn(
                      'modality-button',
                      { 'modality-button--active': modality === 'text' }
                    )}
                    onClick={() => handleModalityChange('text')}
                    title="Text input"
                  >
                    Text
                  </button>
                  <button
                    className={cn(
                      'modality-button',
                      { 'modality-button--active': modality === 'code' }
                    )}
                    onClick={() => handleModalityChange('code')}
                    title="Code input"
                  >
                    <Code className="h-3 w-3" />
                  </button>
                  <button
                    className={cn(
                      'modality-button',
                      { 'modality-button--active': modality === 'image' }
                    )}
                    onClick={() => handleModalityChange('image')}
                    title="Image input"
                  >
                    <ImageIcon className="h-3 w-3" />
                  </button>
                  <button
                    className={cn(
                      'modality-button',
                      {
                        'modality-button--active': modality === 'audio',
                        'modality-button--recording': isRecording
                      }
                    )}
                    onClick={() => handleModalityChange('audio')}
                    title={isRecording ? 'Stop recording' : 'Audio input'}
                  >
                    <Mic className="h-3 w-3" />
                  </button>
                </div>
              )}
              
              {/* Attachment button */}
              <button
                className="input-option-button"
                onClick={triggerFileInput}
                title="Attach file"
                disabled={disabled || isLoading}
              >
                <Paperclip className="h-4 w-4" />
              </button>
              
              {/* Suggestions button */}
              {suggestions.length > 0 && (
                <button
                  className="input-option-button"
                  onClick={() => setShowSuggestions(!showSuggestions)}
                  title={showSuggestions ? 'Hide suggestions' : 'Show suggestions'}
                  disabled={disabled || isLoading}
                >
                  <Lightbulb className="h-4 w-4" />
                </button>
              )}
            </div>
            
            {/* Right side - Advanced options toggle */}
            {shouldShowAdvancedOptions && (
              <button
                className="input-option-button"
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                title={showAdvancedOptions ? 'Hide advanced options' : 'Show advanced options'}
              >
                {showAdvancedOptions ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
            )}
          </div>
          
          {/* Advanced options panel */}
          {showAdvancedOptions && shouldShowAdvancedOptions && (
            <div className="advanced-options">
              <div className="advanced-options-header">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">AI Enhancement Options</span>
              </div>
              
              <div className="advanced-options-grid">
                <button
                  className="ai-enhancement-button"
                  onClick={() => onChange(value + '\\n\\nPlease explain this in detail.')}
                >
                  Explain in detail
                </button>
                <button
                  className="ai-enhancement-button"
                  onClick={() => onChange(value + '\\n\\nProvide a code example.')}
                >
                  Code example
                </button>
                <button
                  className="ai-enhancement-button"
                  onClick={() => onChange(value + '\\n\\nSimplify this explanation.')}
                >
                  Simplify
                </button>
                <button
                  className="ai-enhancement-button"
                  onClick={() => onChange(value + '\\n\\nWhat are the alternatives?')}
                >
                  Alternatives
                </button>
              </div>
              
              {/* AI power indicator */}
              <div className="ai-power-indicator">
                <div className="ai-power-label">
                  <Zap className="h-3 w-3 text-yellow-500" />
                  <span className="text-xs">
                    AI-powered suggestions
                  </span>
                </div>
                <div className="expertise-badge">
                  {expertiseLevel === 'expert' ? 'Expert Mode' :
                   expertiseLevel === 'advanced' ? 'Advanced' :
                   expertiseLevel === 'intermediate' ? 'Standard' : 'Beginner'}
                </div>
              </div>
            </div>
          )}
          
          {/* Guided mode tooltip */}
          {adaptationPolicy.guidedMode && (
            <div className="guided-mode-tooltip">
              💡 Type your message and press Enter to send. Use the buttons above for different input types.
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
};