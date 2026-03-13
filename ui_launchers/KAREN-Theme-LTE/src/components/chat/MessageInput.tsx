/**
 * Production-Ready Message Input Component
 * Enhanced input area with keyboard shortcuts, file upload, and voice recording
 */

import React, { useState, useRef, useCallback, useEffect, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Send,
  Paperclip,
  Mic,
  Square,
  Image as ImageIcon,
  FileText,
  X,
  Upload,
  File,
  Camera,
  Code,
  Link,
  Bold,
  Italic,
  List,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Sparkles
} from 'lucide-react';

export interface MessageInputProps {
  onSendMessage: (content: string, files?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  allowFileUpload?: boolean;
  allowVoiceRecording?: boolean;
  allowCodeBlock?: boolean;
  allowFormatting?: boolean;
  maxFileSize?: number;
  acceptedFileTypes?: string[];
  onTypingStart?: () => void;
  onTypingEnd?: () => void;
}

export interface FileAttachment {
  file: File;
  id: string;
  preview?: string;
  size: number;
  type: string;
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  placeholder = "Type your message...",
  className,
  allowFileUpload = true,
  allowVoiceRecording = true,
  allowCodeBlock = true,
  allowFormatting = true,
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedFileTypes = ['image/*', 'text/*', 'application/pdf', '.doc,.docx', '.txt,.md'],
  onTypingStart,
  onTypingEnd,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [showFormattingToolbar, setShowFormattingToolbar] = useState(false);
  const [showCodeBlock, setShowCodeBlock] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isCodeMode, setIsCodeMode] = useState(false);
  
  const textareaRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, []);

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  // Get file icon based on type
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="h-4 w-4" />;
    } else if (file.type.startsWith('text/') || file.type.includes('document') || file.type.includes('pdf')) {
      return <FileText className="h-4 w-4" />;
    } else if (file.type.startsWith('audio/')) {
      return <Mic className="h-4 w-4" />;
    } else {
      return <Paperclip className="h-4 w-4" />;
    }
  };

  // Handle typing state
  const handleTypingStart = useCallback(() => {
    if (!isTyping) {
      setIsTyping(true);
      onTypingStart?.();
    }
    
    // Clear existing timer
    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
    }
    
    // Set new timer to detect typing end
    typingTimerRef.current = setTimeout(() => {
      setIsTyping(false);
      onTypingEnd?.();
    }, 1000);
  }, [isTyping, onTypingStart, onTypingEnd]);

  // Handle text input changes
  const handleMessageChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    adjustTextareaHeight();
    handleTypingStart();
  }, [adjustTextareaHeight, handleTypingStart]);

  // Handle sending message
  const handleSend = useCallback(() => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage && attachedFiles.length === 0) return;
    if (disabled) return;

    const filesToSend = attachedFiles.map(f => f.file);
    onSendMessage(trimmedMessage, filesToSend.length > 0 ? filesToSend : undefined);
    setMessage('');
    setAttachedFiles([]);
    setIsCodeMode(false);
    adjustTextareaHeight();
  }, [message, attachedFiles, disabled, onSendMessage, adjustTextareaHeight]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
      return;
    }

    // Ctrl/Cmd + Enter to send (with Shift for newline)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
      return;
    }

    // Escape to cancel recording
    if (e.key === 'Escape') {
      if (isRecording) {
        handleRecordingCancel();
      }
      if (showFileUpload) {
        setShowFileUpload(false);
      }
      if (showFormattingToolbar) {
        setShowFormattingToolbar(false);
      }
      if (showCodeBlock) {
        setShowCodeBlock(false);
      }
      return;
    }

    // Ctrl/Cmd + K for code block
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      setIsCodeMode(!isCodeMode);
      return;
    }

    // Ctrl/Cmd + B for bold
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
      e.preventDefault();
      insertFormatting('**', '**');
      return;
    }

    // Ctrl/Cmd + I for italic
    if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
      e.preventDefault();
      insertFormatting('*', '*');
      return;
    }

    // Ctrl/Cmd + U for upload
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
      e.preventDefault();
      fileInputRef.current?.click();
      return;
    }

    // Ctrl/Cmd + V for voice recording
    if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
      e.preventDefault();
      if (isRecording) {
        handleRecordingStop();
      } else {
        handleRecordingStart();
      }
      return;
    }

    // Ctrl/Cmd + F for formatting toolbar
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
      e.preventDefault();
      setShowFormattingToolbar(!showFormattingToolbar);
      return;
    }

    // Tab for autocomplete or indent
    if (e.key === 'Tab') {
      e.preventDefault();
      if (isCodeMode) {
        // Insert 2 spaces in code mode
        const start = textareaRef.current?.selectionStart || message.length;
        const end = textareaRef.current?.selectionEnd || message.length;
        const newText = message.substring(0, start) + '  ' + message.substring(end);
        setMessage(newText);
        // Restore cursor position
        setTimeout(() => {
          textareaRef.current?.setSelectionRange(start + 2, start + 2);
        }, 0);
      } else {
        // Move focus to next element in normal mode
        (e.target as HTMLElement).blur();
      }
      return;
    }

    // Arrow keys for history navigation (placeholder)
    if (e.key === 'ArrowUp' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      // Navigate to previous message
      console.log('Navigate to previous message');
      return;
    }

    if (e.key === 'ArrowDown' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      // Navigate to next message
      console.log('Navigate to next message');
      return;
    }
  }, [message, isRecording, showFileUpload, showFormattingToolbar, showCodeBlock, isCodeMode, handleSend]);

  // Insert formatting
  const insertFormatting = useCallback((before: string, after: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart ?? 0;
    const end = textarea.selectionEnd ?? 0;
    const text = message;

    const newText = text.substring(0, start) + before + text.substring(start, end) + after + text.substring(end);
    setMessage(newText);

    // Restore cursor position
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(start + before.length, start + before.length + text.substring(start, end).length + after.length);
      }
    }, 0);
  }, [message]);

  // Handle file selection
  const handleFileSelect = useCallback((files: FileList) => {
    const validFiles: FileAttachment[] = [];
    
    Array.from(files).forEach(file => {
      // Validate file size
      if (file.size > maxFileSize) {
        console.error(`File ${file.name} exceeds size limit of ${formatFileSize(maxFileSize)}`);
        return;
      }

      // Validate file type
      const isValidType = acceptedFileTypes.some(type => {
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.slice(0, -1));
        }
        return file.name.endsWith(type);
      });

      if (!isValidType) {
        console.error(`File ${file.name} has invalid type`);
        return;
      }

      // Create preview for images
      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      validFiles.push({
        file,
        id: `${Date.now()}-${Math.random().toString(36).substring(7)}`,
        preview,
        size: file.size,
        type: file.type
      });
    });

    setAttachedFiles(prev => [...prev, ...validFiles]);
    setShowFileUpload(false);
  }, [maxFileSize, acceptedFileTypes]);

  // Handle file removal
  const handleFileRemove = useCallback((id: string) => {
    setAttachedFiles(prev => {
      const fileToRemove = prev.find(f => f.id === id);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return prev.filter(f => f.id !== id);
    });
  }, []);

  // Handle voice recording
  const handleRecordingStart = useCallback(() => {
    setIsRecording(true);
    setShowVoiceRecorder(true);
    setRecordingTime(0);
    
    // Start recording timer
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    
    recordingTimerRef.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
  }, []);

  const handleRecordingStop = useCallback(() => {
    setIsRecording(false);
    setShowVoiceRecorder(false);
    
    // Stop recording timer
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    // In production, this would convert audio blob to file
    console.log('Recording stopped, duration:', recordingTime, 'seconds');
  }, [recordingTime]);

  const handleRecordingCancel = useCallback(() => {
    setIsRecording(false);
    setShowVoiceRecorder(false);
    setRecordingTime(0);
    
    // Stop recording timer
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  }, []);

  // Format recording time
  const formatRecordingTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Format code block
  const formatCodeBlock = (text: string) => {
    return `\`\`\`\n${text}\n\`\`\``;
  };

  // Handle code block toggle
  const handleCodeBlockToggle = useCallback(() => {
    if (isCodeMode) {
      setMessage(formatCodeBlock(message));
    }
    setIsCodeMode(!isCodeMode);
  }, [message, isCodeMode]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) {
        clearTimeout(typingTimerRef.current);
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      
      // Revoke object URLs
      attachedFiles.forEach(f => {
        if (f.preview) {
          URL.revokeObjectURL(f.preview);
        }
      });
    };
  }, [attachedFiles]);

  const canSend = (message.trim().length > 0 || attachedFiles.length > 0) && !disabled;

  return (
    <div className={cn('border-t border-purple-500/20 bg-black/40 backdrop-blur-md p-4', className)}>
      {/* File attachments preview */}
      {attachedFiles.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachedFiles.map((attachment) => (
            <div
              key={attachment.id}
              className="bg-purple-500/20 border border-purple-500/30 rounded-lg p-2 flex items-center gap-2 max-w-xs group hover:bg-purple-500/30 transition-colors"
            >
              <div className="text-purple-300">
                {getFileIcon(attachment.file)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate" title={attachment.file.name}>
                  {attachment.file.name}
                </p>
                <p className="text-xs text-purple-300">
                  {formatFileSize(attachment.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFileRemove(attachment.id)}
                className="text-purple-400 hover:text-purple-300 p-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Remove file"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Voice recorder */}
      {showVoiceRecorder && (
        <div className="mb-4 p-4 bg-purple-500/20 border border-purple-500/30 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-3 h-3 rounded-full flex items-center justify-center",
                isRecording ? 'bg-red-500 animate-pulse' : 'bg-purple-500'
              )}>
                {isRecording ? (
                  <Square className="h-4 w-4 text-white" />
                ) : (
                  <Mic className="h-4 w-4 text-white" />
                )}
              </div>
              <div>
                <p className="text-white font-semibold">
                  {isRecording ? 'Recording...' : 'Voice Recording'}
                </p>
                <p className="text-purple-300 text-sm">
                  {isRecording ? formatRecordingTime(recordingTime) : 'Click to start recording'}
                </p>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={isRecording ? handleRecordingStop : handleRecordingStart}
              variant={isRecording ? "destructive" : "default"}
              size="sm"
              className="flex-1"
            >
              {isRecording ? 'Stop' : 'Start'}
            </Button>
            <Button
              onClick={handleRecordingCancel}
              variant="outline"
              size="sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Formatting toolbar */}
      {showFormattingToolbar && allowFormatting && (
        <div className="mb-4 p-4 bg-purple-500/20 border border-purple-500/30 rounded-lg">
          <div className="flex flex-wrap gap-2 mb-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('**', '**')}
              className="text-purple-300 hover:text-purple-200"
              title="Bold (Ctrl+B)"
            >
              <Bold className="h-4 w-4 mr-1" />
              Bold
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('*', '*')}
              className="text-purple-300 hover:text-purple-200"
              title="Italic (Ctrl+I)"
            >
              <Italic className="h-4 w-4 mr-1" />
              Italic
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('`', '`')}
              className="text-purple-300 hover:text-purple-200"
              title="Code (Ctrl+K)"
            >
              <Code className="h-4 w-4 mr-1" />
              Code
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('- ', '- ')}
              className="text-purple-300 hover:text-purple-200"
              title="List"
            >
              <List className="h-4 w-4 mr-1" />
              List
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('> ', '> ')}
              className="text-purple-300 hover:text-purple-200"
              title="Quote"
            >
              <ChevronDown className="h-4 w-4 mr-1" />
              Quote
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('`', '`')}
              className="text-purple-300 hover:text-purple-200"
              title="Code Block"
            >
              <FileText className="h-4 w-4 mr-1" />
              Code Block
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => insertFormatting('[', ']')}
              className="text-purple-300 hover:text-purple-200"
              title="Link"
            >
              <Link className="h-4 w-4 mr-1" />
              Link
            </Button>
          </div>
          <Button
            onClick={() => setShowFormattingToolbar(false)}
            variant="outline"
            size="sm"
            className="w-full"
          >
            Close
          </Button>
        </div>
      )}

      {/* Code block indicator */}
      {isCodeMode && (
        <div className="mb-3 p-2 bg-purple-500/20 border border-purple-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code className="h-4 w-4 text-purple-300" />
            <span className="text-purple-300 text-sm">Code Mode</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCodeBlockToggle}
          >
            <Sparkles className="h-4 w-4 mr-1" />
            Convert to Code Block
          </Button>
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef as any}
            value={message}
            onChange={handleMessageChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'w-full bg-black/40 border-purple-500/30 text-white placeholder-purple-400 focus:border-purple-400 focus:ring-2 focus:ring-purple-500 min-h-[44px] resize-none',
              isCodeMode && 'font-mono text-sm',
              isRecording && 'opacity-50'
            )}
            style={{
              paddingRight: allowFileUpload || allowVoiceRecording ? '100px' : '12px',
              maxHeight: '200px'
            }}
            rows={1}
            aria-label="Message input"
            aria-describedby={isTyping ? 'typing-indicator' : undefined}
          />
          
          {/* Typing indicator */}
          {isTyping && (
            <div id="typing-indicator" className="absolute right-2 bottom-2">
              <div className="flex items-center gap-1">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                </div>
                <span className="text-xs text-purple-300">Typing...</span>
              </div>
            </div>
          )}
          
          {/* Attachment buttons */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            {allowFileUpload && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="text-purple-400 hover:text-purple-300 p-1 h-6 w-6"
                title="Upload file (Ctrl+U)"
              >
                <Upload className="h-4 w-4" />
              </Button>
            )}
            
            {allowVoiceRecording && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={isRecording ? handleRecordingStop : handleRecordingStart}
                disabled={disabled}
                className={cn(
                  'p-1 h-6 w-6',
                  isRecording ? 'text-red-400 hover:text-red-300 animate-pulse' : 'text-purple-400 hover:text-purple-300'
                )}
                title={isRecording ? 'Stop recording (Ctrl+V)' : 'Start voice recording (Ctrl+V)'}
              >
                {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
            )}
            
            {allowFormatting && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setShowFormattingToolbar(!showFormattingToolbar)}
                disabled={disabled}
                className="text-purple-400 hover:text-purple-300 p-1 h-6 w-6"
                title="Formatting tools (Ctrl+F)"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        
        {/* Send button */}
        <Button
          onClick={handleSend}
          disabled={!canSend}
          className={cn(
            'px-4 py-2 rounded-lg transition-all duration-200',
            canSend
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : 'bg-purple-500/20 text-purple-400 cursor-not-allowed'
          )}
          title="Send message (Enter or Ctrl+Enter)"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedFileTypes.join(',')}
        onChange={(e) => {
          const files = e.target.files;
          if (files && files.length > 0) {
            handleFileSelect(files);
          }
          e.target.value = ''; // Reset input
        }}
        className="hidden"
        aria-label="Upload file"
      />
      
      {/* Keyboard shortcuts help */}
      <div className="mt-2 text-xs text-purple-400">
        <span className="font-semibold">Shortcuts:</span>
        <span className="ml-2">Enter/Ctrl+Enter: Send</span>
        <span className="ml-2">Shift+Enter: New line</span>
        {allowFileUpload && <span className="ml-2">Ctrl+U: Upload</span>}
        {allowVoiceRecording && <span className="ml-2">Ctrl+V: Voice</span>}
        {allowFormatting && <span className="ml-2">Ctrl+F: Format</span>}
        {allowCodeBlock && <span className="ml-2">Ctrl+K: Code</span>}
        <span className="ml-2">Esc: Cancel</span>
      </div>
    </div>
  );
}
