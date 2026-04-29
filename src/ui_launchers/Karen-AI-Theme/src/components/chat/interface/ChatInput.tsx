import { FormEvent, KeyboardEvent, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sparkles, Mic, MicOff } from 'lucide-react';
import { ProviderSettingsModal } from '../const/ProviderSettingsModal';
import { SessionHistory } from '../const/SessionHistory';
import { ChatActionsMenu } from '../const/ChatActionsMenu';
import type { Session, ProviderDetails } from '../types';

interface ChatInputProps {
  // Form handling
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  displayedInputValue: string;
  onInputChange: (value: string) => void;
  onKeyDown: (e: KeyboardEvent<HTMLInputElement>) => void;
  onPaste: (e: React.ClipboardEvent<HTMLInputElement>) => void;

  // Button states
  isLoading: boolean;
  isAuthLoading: boolean;
  isRecording: boolean;
  isSuggestingStarter: boolean;
  isEditingDuringProcessing: boolean;
  isBackendOffline: boolean;
  speechRecognitionSupported: boolean;
  showStopButton: boolean;

  // Streaming status
  streamingStatus: string;

  // Button handlers
  onMicClick: () => void;
  onSuggestStarter: () => void;
  onStopRequest: () => void;

  // Provider settings
  selectableProviders: ProviderDetails[];
  selectedProvider: string;
  selectedModel: string;
  applyModelSelection: (providerId: string, modelId: string) => Promise<void>;
  isUpdatingModelSelection: boolean;

  // Session management
  sessions: Session[];
  currentSession: Session | null;
  isLoadingSessions: boolean;
  error: string | null;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<boolean | void>;
  deleteSessions: (sessionIds: string[]) => Promise<boolean>;
  updateSessionTitle: (sessionId: string, newTitle: string) => Promise<boolean>;
  refreshSessions: () => Promise<void>;
  createNewSession: () => Promise<void>;
  onExportChat: () => Promise<void> | void;
  onCopyChat?: () => Promise<void> | void;
  onShareChat?: () => Promise<void> | void;
  onClearChat?: () => Promise<void> | void;
  onSearchInChat?: () => void;
}

export function ChatInput({
  onSubmit,
  displayedInputValue,
  onInputChange,
  onKeyDown,
  onPaste,
  isLoading,
  isAuthLoading,
  isRecording,
  isSuggestingStarter,
  isEditingDuringProcessing,
  isBackendOffline,
  speechRecognitionSupported,
  showStopButton,
  streamingStatus,
  onMicClick,
  onSuggestStarter,
  onStopRequest,
  selectableProviders,
  selectedProvider,
  selectedModel,
  applyModelSelection,
  isUpdatingModelSelection,
  sessions,
  currentSession,
  isLoadingSessions,
  error,
  loadSession,
  deleteSession,
  deleteSessions,
  updateSessionTitle,
  refreshSessions,
  createNewSession,
  onExportChat,
  onCopyChat,
  onShareChat,
  onClearChat,
  onSearchInChat,
}: ChatInputProps) {
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  return (
    <div id="chat-input-area">


      <div className="chat-input-container border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        <div className="mb-2 flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            <ProviderSettingsModal
              selectableProviders={selectableProviders}
              selectedProvider={selectedProvider}
              selectedModel={selectedModel}
              applyModelSelection={applyModelSelection}
              isUpdatingModelSelection={isUpdatingModelSelection}
            />
            <ChatActionsMenu
              currentSession={currentSession}
              isLoadingSessions={isLoadingSessions}
              createNewSession={createNewSession}
              refreshSessions={refreshSessions}
              updateSessionTitle={updateSessionTitle}
              deleteSession={deleteSession}
              onOpenHistory={() => setIsHistoryOpen(true)}
              onExportChat={onExportChat}
              onCopyChat={onCopyChat}
              onShareChat={onShareChat}
              onClearChat={onClearChat}
              onSearchInChat={onSearchInChat}
            />
            <SessionHistory
              sessions={sessions}
              currentSession={currentSession}
              isLoadingSessions={isLoadingSessions}
              error={error}
              loadSession={loadSession}
              deleteSession={deleteSession}
              deleteSessions={deleteSessions}
              updateSessionTitle={updateSessionTitle}
              refreshSessions={refreshSessions}
              createNewSession={createNewSession}
              open={isHistoryOpen}
              onOpenChange={setIsHistoryOpen}
              hideTrigger={true}
            />
          </div>
          <div className="flex self-center sm:self-auto">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onSuggestStarter}
              disabled={isLoading || isSuggestingStarter || isRecording}
              className="h-9 px-3 text-xs sm:text-sm"
              aria-label={isSuggestingStarter ? "Generating conversation starter suggestion" : "Generate a conversation starter suggestion"}
              aria-describedby="starter-help"
            >
              <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">
                {isSuggestingStarter ? "Getting idea..." : "Need an idea?"}
              </span>
              <span className="sm:hidden">
                {isSuggestingStarter ? "Idea..." : "Idea"}
              </span>
            </Button>
          </div>
        </div>
        <form onSubmit={onSubmit} className="w-full flex gap-2 sm:gap-3 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`h-10 w-10 sm:h-11 sm:w-11 ${isRecording ? 'text-destructive animate-pulse' : ''}`}
            onClick={onMicClick}
            disabled={isLoading || isAuthLoading || !speechRecognitionSupported}
            aria-label={isRecording ? "Stop voice recording" : "Start voice recording"}
            aria-pressed={isRecording}
            aria-describedby="mic-help"
          >
            {isRecording ? <MicOff className="h-5 w-5" aria-hidden="true" /> : <Mic className="h-5 w-5" aria-hidden="true" />}
          </Button>
          <Input
            type="text"
            value={displayedInputValue}
            onChange={(e) => {
              if (showStopButton && !isEditingDuringProcessing) {
                return;
              }
              onInputChange(e.target.value);
            }}
            onKeyDown={onKeyDown}
            onPaste={onPaste}
            placeholder={
              isAuthLoading
                ? "Loading your profile..."
                : isLoading && isEditingDuringProcessing
                  ? "Type while Karen is still processing..."
                  : isBackendOffline
                    ? "Offline mode - limited functionality"
                    : streamingStatus || "Ask Karen anything..."
            }
            className="flex-1 bg-[#292929] h-10 sm:h-11 text-sm sm:text-base"
            disabled={isAuthLoading}
            aria-label="Chat message input"
            aria-describedby="input-help"
            aria-invalid={isBackendOffline}
            autoComplete="off"
            spellCheck="true"
            role="textbox"
            aria-multiline="false"
          />
          <Button
            type={isLoading ? 'button' : 'submit'}
            size="icon"
            onClick={isLoading ? onStopRequest : undefined}
            disabled={
              isAuthLoading ||
              isRecording ||
              isBackendOffline ||
              (!isLoading && !displayedInputValue.trim())
            }
            className={`${isLoading ? 'bg-destructive hover:bg-destructive/90' : ''} h-10 w-10 sm:h-11 sm:w-11`}
            aria-label={showStopButton ? "Stop current response generation" : "Send message"}
            aria-describedby="submit-help"
          >
            <span aria-hidden="true" className="text-lg sm:text-xl">{showStopButton ? '⏹️' : '🚀'}</span>
          </Button>
        </form>
      </div>

      {/* Hidden help text for screen readers */}
      <div className="sr-only">
        <div id="starter-help">Get a suggested conversation starter from Karen AI</div>
        <div id="mic-help">
          {speechRecognitionSupported
            ? "Voice input for chat messages"
            : "Voice input not supported in this browser"}
        </div>
        <div id="input-help">Type your message to Karen AI. Press Enter to send, Shift+Enter for new line</div>
        <div id="submit-help">
          {showStopButton
            ? "Stop the current AI response generation"
            : "Send your message to Karen AI"}
        </div>
      </div>
    </div>
  );
}
