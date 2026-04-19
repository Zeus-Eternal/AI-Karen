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

  // UI state
  streamingStatus: string;
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
  streamingStatus,
}: ChatInputProps) {
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  return (
    <div id="chat-input-area">
      <div className="chat-input-container border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        <div className="mb-2 flex w-full flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex gap-2">
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
          <div className="flex self-center md:self-auto">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onSuggestStarter}
              disabled={isLoading || isSuggestingStarter || isRecording}
              className="h-9 px-3"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              {isSuggestingStarter ? "Getting idea..." : "Need an idea?"}
            </Button>
          </div>
        </div>
        <form onSubmit={onSubmit} className="w-full flex gap-2 md:gap-3 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`${isRecording ? 'text-destructive animate-pulse' : ''}`}
            onClick={onMicClick}
            disabled={isLoading || isAuthLoading || !speechRecognitionSupported}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
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
            className="flex-1 bg-[#292929]"
            disabled={isAuthLoading}
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
            className={`${isLoading ? 'bg-destructive hover:bg-destructive/90' : ''}`}
          >
            {showStopButton ? '⏹️' : '🚀'}
          </Button>
        </form>
      </div>
    </div>
  );
}
