import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import { CopilotState } from '../types/copilot';
import { CopilotGateway } from '../services/copilotGateway';
import { cn } from '@/lib/utils';
import {
  Send,
  Paperclip,
  Image as ImageIcon,
  Code,
  Mic,
  X,
  Loader2,
  FileText,
  Keyboard,
  AlertCircle
} from 'lucide-react';

interface MultiModalInputProps {
  onSendMessage: (message: string, modality: 'text' | 'code' | 'image' | 'audio', file?: File) => void;
  isLoading: boolean;
  inputModality: CopilotState['inputModality'];
  onModalityChange: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
  className?: string;
}

/**
 * MultiModalInput - Modern, sleek input component supporting multiple modalities
 * Inspired by ChatGPT's clean design with enhanced user experience
 */
export const MultiModalInput: React.FC<MultiModalInputProps> = ({
  onSendMessage,
  isLoading,
  inputModality,
  onModalityChange,
  backendConfig,
  className = ''
}) => {
  const [message, setMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showModalityOptions, setShowModalityOptions] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copilotGateway = backendConfig ? new CopilotGateway(backendConfig) : null;
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Focus textarea on modality change to text
  useEffect(() => {
    if (inputModality === 'text' && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [inputModality]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  // Handle recording timer
  useEffect(() => {
    if (isRecording) {
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current);
      setRecordingTime(0);
    }

    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    };
  }, [isRecording]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!message.trim() && !selectedFile) {
      setError('Please enter a message or attach a file');
      return;
    }
    
    try {
      // If we have a file and backend config, upload it first
      if (selectedFile && copilotGateway) {
        setIsUploading(true);
        setUploadProgress(0);
        
        try {
          // Check if file size is reasonable (limit to 50MB)
          if (selectedFile.size > 50 * 1024 * 1024) {
            throw new Error('File size exceeds 50MB limit. Please choose a smaller file.');
          }
          
          // Upload file using CopilotGateway
          if (copilotGateway) {
            // Create a FormData object for file upload
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('userId', copilotGateway['config'].userId);
            formData.append('sessionId', copilotGateway['config'].sessionId);
            
            // Get upload URL
            const uploadUrl = `${copilotGateway['config'].baseUrl}/api/copilot/upload`;
            
            // Get headers
            const headers: Record<string, string> = {
              'X-Kari-User-ID': copilotGateway['config'].userId,
              'X-Kari-Session-ID': copilotGateway['config'].sessionId,
              'X-Correlation-ID': copilotGateway.getCorrelationId(),
            };
            
            if (copilotGateway['config'].apiKey) {
              headers['Authorization'] = `Bearer ${copilotGateway['config'].apiKey}`;
            }
            
            // Upload file with progress tracking
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
              if (event.lengthComputable) {
                const progress = Math.round((event.loaded / event.total) * 100);
                setUploadProgress(progress);
              }
            });
            
            // Handle upload completion
            const uploadPromise = new Promise<void>((resolve, reject) => {
              xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                      resolve();
                    } else {
                      reject(new Error(response.message || 'Upload failed'));
                    }
                  } catch {
                    reject(new Error('Invalid response from server'));
                  }
                } else {
                  reject(new Error(`Upload failed with status ${xhr.status}`));
                }
              });
              
              xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
              });
              
              xhr.addEventListener('timeout', () => {
                reject(new Error('Upload request timed out'));
              });
              
              xhr.timeout = 60000; // 60 seconds timeout
            });
            
            // Send the request
            xhr.open('POST', uploadUrl, true);
            Object.entries(headers).forEach(([key, value]) => {
              xhr.setRequestHeader(key, value);
            });
            xhr.send(formData);
            
            await uploadPromise;
          }
          
          // Call the onSendMessage with both message and file
          onSendMessage(message.trim() || 'File attached', inputModality, selectedFile);
        } catch (uploadError) {
          console.error('Upload error:', uploadError);
          setError(`Failed to upload file: ${uploadError instanceof Error ? uploadError.message : 'Unknown error'}`);
          return;
        } finally {
          setIsUploading(false);
          setUploadProgress(0);
        }
      } else {
        // No file or no backend config, just send the message
        onSendMessage(message.trim(), inputModality, selectedFile || undefined);
      }
      
      // Reset form
      setMessage('');
      setFilePreview(null);
      setSelectedFile(null);
    } catch (err) {
      console.error('Submit error:', err);
      setError(`Failed to send message: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = (file: File) => {
    try {
      // Validate file
      if (!file) {
        setError('No file selected');
        return;
      }
      
      // Check file size (limit to 50MB)
      if (file.size > 50 * 1024 * 1024) {
        setError(`File size exceeds 50MB limit. Selected file is ${(file.size / (1024 * 1024)).toFixed(2)}MB.`);
        return;
      }
      
      // Check file type
      const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'audio/wav', 'audio/mp3', 'audio/webm', 'audio/ogg',
        'application/pdf',
        'text/plain', 'application/json',
        'text/html', 'text/css',
        'application/javascript', 'text/javascript',
        'application/typescript', 'text/typescript',
        'application/x-tex', 'text/x-tex',
        'application/xml', 'text/xml'
      ];
      
      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(js|ts|tsx|jsx|html|css|json|md|txt)$/i)) {
        setError(`Unsupported file type: ${file.type}. Please select an image, audio, or document file.`);
        return;
      }
      
      setSelectedFile(file);
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setFilePreview(e.target?.result as string);
        };
        reader.onerror = () => {
          setError('Failed to preview image. The file may be corrupted.');
          setFilePreview(null);
        };
        reader.readAsDataURL(file);
      } else {
        setFilePreview(null);
      }
    } catch (error) {
      console.error('File selection error:', error);
      setError(`Error selecting file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    try {
      if (!e.dataTransfer.files || e.dataTransfer.files.length === 0) {
        setError('No files were dropped. Please try again.');
        return;
      }
      
      // Check if too many files were dropped
      if (e.dataTransfer.files.length > 1) {
        setError('Please drop only one file at a time.');
        return;
      }
      
      const file = e.dataTransfer.files[0];
      
      // Check if file is valid
      if (!file || !file.name) {
        setError('Invalid file dropped. Please try again.');
        return;
      }
      
      // Check file size
      if (file.size === 0) {
        setError('The dropped file is empty. Please select a valid file.');
        return;
      }
      
      // Check if file is too large
      if (file.size > 50 * 1024 * 1024) {
        setError(`File size exceeds 50MB limit. Selected file is ${(file.size / (1024 * 1024)).toFixed(2)}MB.`);
        return;
      }
      
      handleFileSelect(file);
      onModalityChange(file.type.startsWith('image/') ? 'image' : 'code');
    } catch (error) {
      console.error('Drop error:', error);
      setError(`Error handling dropped file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    try {
      if (!e.target.files || e.target.files.length === 0) {
        setError('No file selected. Please try again.');
        return;
      }
      
      // Check if too many files were selected
      if (e.target.files.length > 1) {
        setError('Please select only one file at a time.');
        return;
      }
      
      const file = e.target.files[0];
      
      // Check if file is valid
      if (!file || !file.name) {
        setError('Invalid file selected. Please try again.');
        return;
      }
      
      // Reset the file input to allow selecting the same file again
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      handleFileSelect(file);
    } catch (error) {
      console.error('File input change error:', error);
      setError(`Error selecting file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const startRecording = async () => {
    try {
      setError(null);
      
      // Check if browser supports MediaRecorder
      if (!window.MediaRecorder) {
        setError('Your browser does not support audio recording. Please try a different browser.');
        return;
      }
      
      // Check if getUserMedia is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('Your browser does not support microphone access. Please check your permissions.');
        return;
      }
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 44100
          }
        });
        
        // Check if we got any audio tracks
        if (!stream.getAudioTracks().length) {
          throw new Error('No audio tracks found in the stream');
        }
        
        // Check if the audio track is enabled
        const audioTrack = stream.getAudioTracks()[0];
        if (!audioTrack.enabled) {
          throw new Error('Audio track is disabled');
        }
        
        mediaRecorderRef.current = new MediaRecorder(stream, {
          mimeType: 'audio/webm'
        });
        
        const audioChunks: Blob[] = [];
        mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        });
        
        mediaRecorderRef.current.addEventListener('stop', () => {
          try {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            if (audioBlob.size === 0) {
              setError('Recording failed: No audio data captured. Please try again.');
              return;
            }
            
            // Check if recording is too short (less than 1 second)
            if (audioBlob.size < 1000) {
              setError('Recording is too short. Please record for at least 1 second.');
              return;
            }
            
            const audioFile = new File([audioBlob], `recording-${Date.now()}.webm`, { type: 'audio/webm' });
            handleFileSelect(audioFile);
            stream.getTracks().forEach(track => track.stop());
            
            // If we have a backend config, upload the audio file
            if (copilotGateway) {
              try {
                const formData = new FormData();
                formData.append('file', audioFile);
                formData.append('userId', copilotGateway['config'].userId);
                formData.append('sessionId', copilotGateway['config'].sessionId);
                
                // Get upload URL
                const uploadUrl = `${copilotGateway['config'].baseUrl}/api/copilot/upload`;
                
                // Get headers
                const headers: Record<string, string> = {
                  'X-Kari-User-ID': copilotGateway['config'].userId,
                  'X-Kari-Session-ID': copilotGateway['config'].sessionId,
                  'X-Correlation-ID': copilotGateway.getCorrelationId(),
                };
                
                if (copilotGateway['config'].apiKey) {
                  headers['Authorization'] = `Bearer ${copilotGateway['config'].apiKey}`;
                }
                
                // Upload file with progress tracking
                const xhr = new XMLHttpRequest();
                
                // Track upload progress
                xhr.upload.addEventListener('progress', (event) => {
                  if (event.lengthComputable) {
                    const progress = Math.round((event.loaded / event.total) * 100);
                    setUploadProgress(progress);
                  }
                });
                
                // Handle upload completion
                xhr.addEventListener('load', () => {
                  if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                      const response = JSON.parse(xhr.responseText);
                      if (!response.success) {
                        setError(`Upload failed: ${response.message || 'Unknown error'}`);
                      }
                    } catch {
                      setError('Invalid response from server');
                    }
                  } else {
                    setError(`Upload failed with status ${xhr.status}`);
                  }
                });
                
                xhr.addEventListener('error', () => {
                  setError('Network error during audio upload');
                });
                
                xhr.addEventListener('timeout', () => {
                  setError('Audio upload request timed out');
                });
                
                xhr.timeout = 60000; // 60 seconds timeout
                xhr.open('POST', uploadUrl, true);
                Object.entries(headers).forEach(([key, value]) => {
                  xhr.setRequestHeader(key, value);
                });
                xhr.send(formData);
              } catch (uploadError) {
                console.error('Audio upload error:', uploadError);
                setError(`Failed to upload audio: ${uploadError instanceof Error ? uploadError.message : 'Unknown error'}`);
              }
            }
          } catch (blobError) {
            console.error('Blob processing error:', blobError);
            setError(`Failed to process recording: ${blobError instanceof Error ? blobError.message : 'Unknown error'}`);
          }
        });
        
        mediaRecorderRef.current.start();
        setIsRecording(true);
        onModalityChange('audio');
      } catch (mediaError) {
        console.error('Media access error:', mediaError);
        if (mediaError instanceof Error) {
          if (mediaError.name === 'NotAllowedError' || mediaError.message.includes('denied')) {
            setError('Microphone access was denied. Please allow microphone access and try again.');
          } else if (mediaError.name === 'NotFoundError' || mediaError.message.includes('not found')) {
            setError('No microphone was found. Please connect a microphone and try again.');
          } else if (mediaError.name === 'NotReadableError' || mediaError.message.includes('readable')) {
            setError('Microphone is being used by another application. Please close other applications using the microphone.');
          } else {
            setError(`Error accessing microphone: ${mediaError.message}`);
          }
        } else {
          setError('An unknown error occurred while accessing the microphone.');
        }
      }
    } catch (err) {
      console.error('Recording error:', err);
      setError(`Failed to start recording: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const getModalityIcon = (modality: 'text' | 'code' | 'image' | 'audio') => {
    switch (modality) {
      case 'text':
        return <FileText className="w-4 h-4" />;
      case 'code':
        return <Code className="w-4 h-4" />;
      case 'image':
        return <ImageIcon className="w-4 h-4" />;
      case 'audio':
        return <Mic className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getModalityLabel = (modality: 'text' | 'code' | 'image' | 'audio') => {
    switch (modality) {
      case 'text':
        return 'Text';
      case 'code':
        return 'Code';
      case 'image':
        return 'Image';
      case 'audio':
        return 'Audio';
      default:
        return '';
    }
  };

  return (
    <div className={cn("modern-multi-modal-input", className)}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileInputChange}
        accept="image/*,audio/*,.pdf,.doc,.docx,.txt,.json,.xml,.html,.css,.js,.ts,.tsx,.jsx"
      />
      
      {/* Error display */}
      {error && (
        <div className="modern-input-error">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            className="modern-error-dismiss"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {/* Upload progress */}
      {isUploading && (
        <div className="modern-upload-progress">
          <div className="modern-progress-bar">
            <div
              className="modern-progress-fill"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <span className="modern-progress-text">Uploading... {uploadProgress}%</span>
        </div>
      )}
      
      {/* Main input container */}
      <div className="modern-input-container">
        <form onSubmit={handleSubmit} className="modern-input-form">
          {/* File preview */}
          {filePreview && (
            <div className="modern-file-preview">
              {selectedFile?.type.startsWith('image/') ? (
                <>
                  <div className="modern-image-preview">
                    <Image
                      src={filePreview || ''}
                      alt={`Preview of ${selectedFile?.name || 'uploaded file'}`}
                      className="modern-preview-image"
                      width={100}
                      height={100}
                    />
                  </div>
                  <div className="modern-file-info">
                    <span className="modern-file-name">{selectedFile.name}</span>
                    <span className="modern-file-size">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </>
              ) : (
                <div className="modern-generic-file-preview">
                  <FileText className="w-8 h-8 text-gray-400" />
                  <div className="modern-file-info">
                    <span className="modern-file-name">{selectedFile?.name}</span>
                    <span className="modern-file-size">
                      {selectedFile && (selectedFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
              )}
              <button
                type="button"
                onClick={() => {
                  setFilePreview(null);
                  setSelectedFile(null);
                }}
                className="modern-remove-file"
                aria-label="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Input area */}
          <div
            className={cn(
              "modern-input-area",
              {
                "modern-input-area--focused": !!message || isDragging,
                "modern-input-area--dragging": isDragging,
                "modern-input-area--disabled": isLoading
              }
            )}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleFileDrop}
          >
            {inputModality === 'audio' ? (
              <div className="modern-audio-input">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={cn(
                    "modern-record-button",
                    {
                      "modern-record-button--recording": isRecording
                    }
                  )}
                  aria-label={isRecording ? 'Stop recording' : 'Start recording'}
                >
                  {isRecording ? (
                    <div className="modern-recording-indicator">
                      <span className="modern-recording-pulse"></span>
                      <Mic className="w-5 h-5" />
                    </div>
                  ) : (
                    <Mic className="w-5 h-5" />
                  )}
                </button>
                <div className="modern-recording-info">
                  <span className="modern-recording-status">
                    {isRecording ? `Recording: ${formatTime(recordingTime)}` : 'Click to start recording'}
                  </span>
                  <span className="modern-recording-hint">
                    {isRecording ? 'Click to stop' : 'Hold to record'}
                  </span>
                </div>
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  inputModality === 'text'
                    ? 'Message...'
                    : inputModality === 'code'
                    ? 'Code...'
                    : 'Describe image...'
                }
                className="modern-textarea"
                disabled={isLoading}
                aria-label={
                  inputModality === 'text'
                    ? 'Message input'
                    : inputModality === 'code'
                    ? 'Code input'
                    : 'Image description input'
                }
                rows={1}
              />
            )}
          </div>

          {/* Action buttons */}
          <div className="modern-input-actions">
            <div className="modern-input-left-actions">
              {/* Modality selector */}
              <div className="modern-modality-container">
                <button
                  type="button"
                  onClick={() => setShowModalityOptions(!showModalityOptions)}
                  className="modern-modality-toggle"
                  aria-label="Select input modality"
                >
                  {getModalityIcon(inputModality)}
                  <span>{getModalityLabel(inputModality)}</span>
                  <Keyboard className="w-3 h-3 opacity-60" />
                </button>
                
                {showModalityOptions && (
                  <div className="modern-modality-options">
                    {(['text', 'code', 'image', 'audio'] as const).map((modality) => (
                      <button
                        key={modality}
                        type="button"
                        onClick={() => {
                          onModalityChange(modality);
                          setShowModalityOptions(false);
                        }}
                        className={cn(
                          "modern-modality-option",
                          {
                            "modern-modality-option--active": inputModality === modality
                          }
                        )}
                      >
                        {getModalityIcon(modality)}
                        <span>{getModalityLabel(modality)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Attachment button */}
              <button
                type="button"
                onClick={triggerFileInput}
                className="modern-action-button"
                aria-label="Attach file"
                disabled={isLoading}
              >
                <Paperclip className="w-4 h-4" />
              </button>
            </div>

            {/* Send button */}
            <button
              type="submit"
              disabled={isLoading || (!message.trim() && !selectedFile)}
              className={cn(
                "modern-send-button",
                {
                  "modern-send-button--disabled": isLoading || (!message.trim() && !selectedFile),
                  "modern-send-button--active": !isLoading && (message.trim() || selectedFile)
                }
              )}
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </form>

        {/* Keyboard hint */}
        <div className="modern-input-hint">
          <span>Press</span>
          <kbd className="modern-key">Enter</kbd>
          <span>to send</span>
          <kbd className="modern-key">Shift</kbd>
          <span>+</span>
          <kbd className="modern-key">Enter</kbd>
          <span>for new line</span>
        </div>
      </div>
    </div>
  );
};
