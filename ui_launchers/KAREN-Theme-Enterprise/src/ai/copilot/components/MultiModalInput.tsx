import React, { useState, useRef, useEffect } from 'react';
import { LNMInfo } from '../types/backend';
import Image from 'next/image';

/**
 * MultiModalInput component
 * Creates an input component that supports multiple modalities
 */
interface MultiModalInputProps {
  activeModality: 'text' | 'code' | 'image' | 'audio';
  availableLNMs: LNMInfo[];
  activeLNM: LNMInfo | null;
  onSendMessage: (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => void;
  onChangeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  onSelectLNM: (lnm: LNMInfo) => void;
  onAttachFile?: (file: File) => void;
  onRecordAudio?: () => void;
  onCaptureImage?: () => void;
  className?: string;
}

export function MultiModalInput({
  activeModality,
  availableLNMs,
  activeLNM,
  onSendMessage,
  onChangeModality,
  onSelectLNM,
  onAttachFile,
  onRecordAudio,
  onCaptureImage,
  className = ''
}: MultiModalInputProps) {
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [codeLanguage, setCodeLanguage] = useState('javascript');
  
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Focus input when modality changes to text or code
  useEffect(() => {
    if ((activeModality === 'text' || activeModality === 'code') && inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeModality]);

  // Clean up recording interval
  useEffect(() => {
    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    };
  }, []);

  // Handle text/code input
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  // Handle send message
  const handleSendMessage = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue, activeModality);
      setInputValue('');
    }
  };

  // Handle key press (Ctrl+Enter or Cmd+Enter to send)
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSendMessage();
    }
  };

  // Handle file drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  // Handle file upload
  const handleFileUpload = (file: File) => {
    if (onAttachFile) {
      onAttachFile(file);
    }
    
    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle file input click
  const handleFileInputClick = () => {
    fileInputRef.current?.click();
  };

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  // Handle audio recording
  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      audioRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      audioRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        if (onAttachFile) {
          onAttachFile(audioFile);
        }
      };
      
      audioRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start recording timer
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      if (onRecordAudio) {
        onRecordAudio();
      }
    } catch (error) {
      console.error('Error starting audio recording:', error);
    }
  };

  const handleStopRecording = () => {
    if (audioRecorderRef.current && isRecording) {
      audioRecorderRef.current.stop();
      audioRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    }
  };

  // Handle image capture
  const handleCaptureImage = () => {
    if (onCaptureImage) {
      onCaptureImage();
    }
  };

  // Format recording time
  const formatRecordingTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Render input based on active modality
  const renderInput = () => {
    switch (activeModality) {
      case 'text':
        return (
          <textarea
            ref={inputRef}
            className="multi-modal-input__text-input"
            placeholder="Type your message..."
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            rows={3}
          />
        );
        
      case 'code':
        return (
          <div className="multi-modal-input__code-container">
            <div className="multi-modal-input__code-header">
              <select
                className="multi-modal-input__code-language"
                value={codeLanguage}
                onChange={(e) => setCodeLanguage(e.target.value)}
              >
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="csharp">C#</option>
                <option value="cpp">C++</option>
                <option value="html">HTML</option>
                <option value="css">CSS</option>
                <option value="json">JSON</option>
                <option value="xml">XML</option>
                <option value="sql">SQL</option>
                <option value="markdown">Markdown</option>
              </select>
            </div>
            <textarea
              ref={inputRef}
              className="multi-modal-input__code-input"
              placeholder={`Enter your ${codeLanguage} code...`}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              rows={8}
              style={{ fontFamily: 'monospace' }}
            />
          </div>
        );
        
      case 'image':
        return (
          <div
            className={`multi-modal-input__image-area ${isDragging ? 'multi-modal-input__image-area--dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleFileInputClick}
          >
            {previewUrl ? (
              <div className="multi-modal-input__image-preview">
                <Image
                  src={previewUrl}
                  alt="Preview"
                  className="multi-modal-input__image-preview-img"
                  width={100}
                  height={100}
                />
                <button
                  className="multi-modal-input__image-preview-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPreviewUrl(null);
                  }}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="multi-modal-input__image-placeholder">
                <div className="multi-modal-input__image-placeholder-icon">📷</div>
                <div className="multi-modal-input__image-placeholder-text">
                  Drag & drop an image here, or click to browse
                </div>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              className="multi-modal-input__file-input"
              accept="image/*"
              onChange={handleFileInputChange}
            />
          </div>
        );
        
      case 'audio':
        return (
          <div className="multi-modal-input__audio-container">
            {isRecording ? (
              <div className="multi-modal-input__audio-recording">
                <div className="multi-modal-input__audio-recording-indicator"></div>
                <div className="multi-modal-input__audio-recording-time">
                  {formatRecordingTime(recordingTime)}
                </div>
                <button
                  className="multi-modal-input__audio-stop"
                  onClick={handleStopRecording}
                >
                  Stop Recording
                </button>
              </div>
            ) : (
              <div className="multi-modal-input__audio-controls">
                <button
                  className="multi-modal-input__audio-record"
                  onClick={handleStartRecording}
                >
                  Start Recording
                </button>
                <div className="multi-modal-input__audio-or">or</div>
                <div
                  className="multi-modal-input__audio-upload"
                  onClick={handleFileInputClick}
                >
                  Upload Audio File
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="multi-modal-input__file-input"
                  accept="audio/*"
                  onChange={handleFileInputChange}
                />
              </div>
            )}
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className={`multi-modal-input ${className}`}>
      {/* Modality Selector */}
      <div className="multi-modal-input__modalities">
        <button
          className={`multi-modal-input__modality ${activeModality === 'text' ? 'multi-modal-input__modality--active' : ''}`}
          onClick={() => onChangeModality('text')}
          title="Text Input"
        >
          <span className="multi-modal-input__modality-icon">T</span>
          <span className="multi-modal-input__modality-label">Text</span>
        </button>
        
        <button
          className={`multi-modal-input__modality ${activeModality === 'code' ? 'multi-modal-input__modality--active' : ''}`}
          onClick={() => onChangeModality('code')}
          title="Code Input"
        >
          <span className="multi-modal-input__modality-icon">{`</>`}</span>
          <span className="multi-modal-input__modality-label">Code</span>
        </button>
        
        <button
          className={`multi-modal-input__modality ${activeModality === 'image' ? 'multi-modal-input__modality--active' : ''}`}
          onClick={() => onChangeModality('image')}
          title="Image Input"
        >
          <span className="multi-modal-input__modality-icon">🖼️</span>
          <span className="multi-modal-input__modality-label">Image</span>
        </button>
        
        <button
          className={`multi-modal-input__modality ${activeModality === 'audio' ? 'multi-modal-input__modality--active' : ''}`}
          onClick={() => onChangeModality('audio')}
          title="Audio Input"
        >
          <span className="multi-modal-input__modality-icon">🎤</span>
          <span className="multi-modal-input__modality-label">Audio</span>
        </button>
      </div>

      {/* Input Area */}
      <div className="multi-modal-input__input-area">
        {renderInput()}
      </div>

      {/* Action Buttons */}
      <div className="multi-modal-input__actions">
        {/* LNM Selector */}
        <div className="multi-modal-input__lnm-selector">
          <select
            className="multi-modal-input__lnm-select"
            value={activeLNM?.id || ''}
            onChange={(e) => {
              const lnm = availableLNMs.find(l => l.id === e.target.value);
              if (lnm) onSelectLNM(lnm);
            }}
          >
            {availableLNMs.map(lnm => (
              <option key={lnm.id} value={lnm.id}>
                {lnm.name}
              </option>
            ))}
          </select>
        </div>

        {/* Send Button */}
        {(activeModality === 'text' || activeModality === 'code') && (
          <button
            className="multi-modal-input__send"
            onClick={handleSendMessage}
            disabled={!inputValue.trim()}
          >
            Send
          </button>
        )}

        {/* Image Capture Button */}
        {activeModality === 'image' && (
          <button
            className="multi-modal-input__capture"
            onClick={handleCaptureImage}
          >
            Capture Image
          </button>
        )}
      </div>

      {/* Help Text */}
      <div className="multi-modal-input__help">
        {activeModality === 'text' && (
          <div>Press Ctrl+Enter or Cmd+Enter to send</div>
        )}
        {activeModality === 'code' && (
          <div>Code will be syntax-highlighted and formatted</div>
        )}
        {activeModality === 'image' && (
          <div>Images will be analyzed and described</div>
        )}
        {activeModality === 'audio' && (
          <div>Audio will be transcribed to text</div>
        )}
      </div>
    </div>
  );
}