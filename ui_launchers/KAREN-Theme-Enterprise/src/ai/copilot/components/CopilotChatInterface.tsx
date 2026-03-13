import React, { useState, useEffect } from 'react';
import { CopilotState, UserExpertiseLevel } from '../types/copilot';
import { CopilotProvider } from '../hooks/useCopilot';
import { IntelligentAssistant } from './IntelligentAssistant';
import { MemoryManagement } from './MemoryManagement';
import { WorkflowAutomation } from './WorkflowAutomation';
import { ArtifactSystem } from './ArtifactSystem';
import { PluginDiscovery } from './PluginDiscovery';
import { AdaptiveInterface } from './AdaptiveInterface';
import { MultiModalInput } from '../../../components/copilot-chat/components/MultiModalInput';
import { CopilotErrorBoundary } from '../../../components/ui/error-handling/CopilotErrorBoundary';
import { useCopilot } from '../../../hooks/useCopilot';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Cpu, HardDrive, Puzzle, MessageSquare, Loader2, Bot, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CopilotChatInterface component
 * Main shell component for the Copilot Chat Interface
 * Serves as the entry point for the unified chat system
 */
interface CopilotChatInterfaceProps {
  initialState?: Partial<CopilotState>;
  backendConfig: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
  expertiseLevel?: UserExpertiseLevel;
  className?: string;
}

// Inner component that uses the Copilot context
function CopilotChatInterfaceContent({
  expertiseLevel = 'intermediate',
  className = '',
  backendConfig
}: {
  expertiseLevel?: UserExpertiseLevel;
  className?: string;
  backendConfig: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
}) {
  const { state, sendMessage, executeWorkflow, openArtifact, changePanel, changeModality, togglePlugin, clearError, retry, dismissWorkflow, dismissArtifact } = useCopilot({ backendConfig });
  const [activePanel, setActivePanel] = useState<'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins'>(state.activePanel);
  const [inputModality, setInputModality] = useState<'text' | 'code' | 'image' | 'audio'>(state.inputModality);
  
  // Sync local state with global state
  useEffect(() => {
    setActivePanel(state.activePanel);
    setInputModality(state.inputModality);
  }, [state.activePanel, state.inputModality]);

  // Handle panel change
  const handlePanelChange = (panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') => {
    setActivePanel(panel);
    changePanel(panel);
  };

  // Handle modality change
  const handleModalityChange = (modality: 'text' | 'code' | 'image' | 'audio') => {
    setInputModality(modality);
    changeModality(modality);
  };

  // Handle send message
  const handleSendMessage = (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => {
    if (message.trim()) {
      sendMessage(message, modality || inputModality);
    }
  };


  // Render active panel
  const renderActivePanel = () => {
    switch (activePanel) {
      case 'memory':
        return (
          <MemoryManagement
            messages={state.messages}
            memoryOps={state.memoryOps}
            onQueryMemory={(query) => sendMessage(query)}
            onPinMemory={(messageId) => console.log('Pin memory:', messageId)}
            onForgetMemory={(messageId) => console.log('Forget memory:', messageId)}
            securityContext={state.securityContext}
          />
        );
      case 'workflows':
        return (
          <WorkflowAutomation
            workflows={state.workflows}
            _onExecuteWorkflow={(workflow) => executeWorkflow(workflow)}
            _onDismissWorkflow={(workflowId) => dismissWorkflow(workflowId)}
            securityContext={state.securityContext}
          />
        );
      case 'artifacts':
        return (
          <ArtifactSystem
            artifacts={state.artifacts}
            _onOpenArtifact={(artifact) => openArtifact(artifact)}
            _onDismissArtifact={(artifactId) => dismissArtifact(artifactId)}
            securityContext={state.securityContext}
          />
        );
      case 'plugins':
        return (
          <PluginDiscovery
            availablePlugins={state.availablePlugins}
            _onTogglePlugin={(plugin, enabled) => togglePlugin(plugin, enabled)}
            securityContext={state.securityContext}
          />
        );
      case 'chat':
      default:
        return (
          <IntelligentAssistant
            actions={state.actions}
            suggestions={[]}
            securityContext={state.securityContext}
          />
        );
    }
  };

  return (
    <AdaptiveInterface
      expertiseLevel={expertiseLevel}
      className={cn("copilot-chat-interface", className)}
    >
      <div className="flex flex-col h-full bg-background">
        {/* Header */}
        <Card className="rounded-none border-b">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-6 w-6 text-primary" />
                <CardTitle className="text-xl">KAREN Copilot</CardTitle>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className={cn(
                    "relative flex h-2 w-2",
                    state.isLoading ? "animate-pulse" : ""
                  )}>
                    <span className={cn(
                      "absolute inline-flex h-full w-full rounded-full opacity-75",
                      state.isLoading ? "bg-green-500" : "bg-green-400"
                    )} />
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {state.isLoading ? 'Processing...' : 'Ready'}
                  </span>
                </div>
                {state.activeLNM && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    {state.activeLNM.name}
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Panel Navigation */}
        <div className="border-b bg-background/95 backdrop-sm">
          <div className="flex overflow-x-auto py-1 px-2 gap-1">
            <Button
              variant={activePanel === 'chat' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handlePanelChange('chat')}
              className="flex items-center gap-1.5"
            >
              <Bot className="h-4 w-4" />
              <span>Assistant</span>
            </Button>
            <Button
              variant={activePanel === 'memory' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handlePanelChange('memory')}
              className="flex items-center gap-1.5"
            >
              <Brain className="h-4 w-4" />
              <span>Memory</span>
            </Button>
            <Button
              variant={activePanel === 'workflows' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handlePanelChange('workflows')}
              className="flex items-center gap-1.5"
            >
              <Cpu className="h-4 w-4" />
              <span>Workflows</span>
            </Button>
            <Button
              variant={activePanel === 'artifacts' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handlePanelChange('artifacts')}
              className="flex items-center gap-1.5"
            >
              <HardDrive className="h-4 w-4" />
              <span>Artifacts</span>
            </Button>
            <Button
              variant={activePanel === 'plugins' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handlePanelChange('plugins')}
              className="flex items-center gap-1.5"
            >
              <Puzzle className="h-4 w-4" />
              <span>Plugins</span>
            </Button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Messages Panel */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4 max-w-3xl mx-auto">
                {state.messages.map((message) => (
                  <Card
                    key={message.id}
                    className={cn(
                      "overflow-hidden",
                      message.role === 'user' ? "ml-auto max-w-[85%]" : "mr-auto max-w-[85%]"
                    )}
                  >
                    <CardHeader className="pb-2 pt-3 px-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {message.role === 'user' ? (
                            <div className="bg-primary text-primary-foreground rounded-full p-1">
                              <MessageSquare className="h-4 w-4" />
                            </div>
                          ) : (
                            <div className="bg-secondary text-secondary-foreground rounded-full p-1">
                              <Bot className="h-4 w-4" />
                            </div>
                          )}
                          <span className="font-medium text-sm">
                            {message.role === 'user' ? 'You' : 'KAREN'}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="px-4 pb-3 pt-0">
                      <div className="text-sm">
                        {message.content}
                      </div>
                      {message.metadata && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {message.metadata.modality && (
                            <Badge variant="outline" className="text-xs">
                              {message.metadata.modality}
                            </Badge>
                          )}
                          {message.metadata.pluginId && (
                            <Badge variant="outline" className="text-xs">
                              Plugin: {message.metadata.pluginId}
                            </Badge>
                          )}
                          {message.metadata.intent && (
                            <Badge variant="outline" className="text-xs">
                              Intent: {message.metadata.intent}
                            </Badge>
                          )}
                          {message.metadata.confidence && (
                            <Badge variant="outline" className="text-xs">
                              Confidence: {Math.round(message.metadata.confidence * 100)}%
                            </Badge>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
                {state.isLoading && (
                  <Card className="mr-auto max-w-[85%]">
                    <CardContent className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm text-muted-foreground">KAREN is thinking...</span>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Active Panel */}
            <div className="border-t p-4 bg-background/50">
              {renderActivePanel()}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {state.error && (
          <Card className="mx-4 mb-4 border-destructive/50 bg-destructive/5">
            <CardContent className="p-3">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <div className="bg-destructive/10 p-1 rounded-full">
                    <Zap className="h-4 w-4 text-destructive" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-destructive">
                      {state.error.message}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  {state.error.retryable && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => retry(state.messages[state.messages.length - 1]?.id || '')}
                      className="h-8"
                    >
                      Retry
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => state.error && clearError(state.error.id)}
                    className="h-8"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Multi-Modal Input Area */}
        <div className="border-t p-4 bg-background">
          <MultiModalInput
            onSendMessage={handleSendMessage}
            isLoading={state.isLoading}
            inputModality={inputModality}
            onModalityChange={handleModalityChange}
            backendConfig={backendConfig}
          />
        </div>
      </div>
    </AdaptiveInterface>
  );
}

export function CopilotChatInterface({
  initialState,
  backendConfig,
  expertiseLevel = 'intermediate',
  className = ''
}: CopilotChatInterfaceProps) {
  return (
    <CopilotErrorBoundary isRetryable={true}>
      <CopilotProvider
        backendConfig={backendConfig}
        initialState={initialState}
      >
        <CopilotChatInterfaceContent
          expertiseLevel={expertiseLevel}
          className={className}
          backendConfig={backendConfig}
        />
      </CopilotProvider>
    </CopilotErrorBoundary>
  );
}
