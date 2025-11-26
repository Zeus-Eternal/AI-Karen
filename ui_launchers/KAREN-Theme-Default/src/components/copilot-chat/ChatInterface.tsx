import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useCopilotEngine } from './core/CopilotEngine';
import { ContextBridgeProvider } from './core/ContextBridge';
import { useContextBridge } from './core/context-bridge-hooks';
import { WorkflowEngineProvider } from './core/WorkflowEngine';
import { useWorkflowEngine } from './core/workflow-engine-hooks';
import { ArtifactSystemProvider } from './core/ArtifactSystem';
import { useArtifactSystem } from './core/artifact-hooks';
import { AdaptiveInterface } from './components/AdaptiveInterface';
import { AdaptiveLayout } from './components/AdaptiveLayout';
import { useAdaptiveLayout } from './components/adaptive-layout-hooks';
import { ContextualSuggestions } from './components/ContextualSuggestions';
import { SmartMessageBubble } from './components/SmartMessageBubble';
import { MultiModalInput } from './components/MultiModalInput';
import { WorkflowAutomation } from './components/WorkflowAutomation';
import { ArtifactSystem } from './components/ArtifactSystem';
import { CopilotMessage, CopilotSuggestion } from './types/copilot';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import Image from 'next/image';
import {
  MessageSquare,
  Workflow,
  FileText,
  Settings,
  History,
  Bot,
  Loader2
} from 'lucide-react';
import {
  debounce,
  throttle,
  VirtualListUtils,
  PerformanceMonitor,
  LazyLoader,
  ImageOptimizer,
  CodeHighlighter,
  ComponentOptimizer
} from './utils/performance';

/**
 * Optimized version of the ChatInterface with performance enhancements
 * Implements performance optimizations for the innovative Copilot-first approach
 */
export const OptimizedChatInterface: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Debounced resize handler
  const handleResize = useMemo(
    () => debounce(() => {
      // Handle resize logic here
      console.log('Window resized (debounced)');
    }, 200),
    []
  );
  
  // Throttled scroll handler
  const handleScroll = useMemo(
    () => throttle(() => {
      // Handle scroll logic here
      console.log('Scrolled (throttled)');
    }, 100),
    []
  );
  
  
  // Optimized event listeners
  useEffect(() => {
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [handleResize]);
  
  // Performance monitoring
  useEffect(() => {
    const endMeasure = PerformanceMonitor.startMeasure('ChatInterface-mount');
    
    // Simulate loading
    const timer = setTimeout(() => {
      setIsLoading(false);
      endMeasure();
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Lazy loading for components
  useEffect(() => {
    const currentContainer = containerRef.current;
    if (currentContainer) {
      // In a real implementation, we would register elements for lazy loading
      // LazyLoader.register(currentContainer, () => {
      //   // Load additional content when visible
      // });
    }
    
    return () => {
      if (currentContainer) {
        // LazyLoader.unregister(currentContainer);
      }
    };
  }, []);
  
  // Optimized click handler
  const handleClick = useCallback((_event: React.MouseEvent) => {
    // Handle click logic here
    console.log('Clicked (optimized)');
  }, []);
  
  // Optimized render using shouldComponentUpdate logic
  const shouldRender = useMemo(() => {
    const prevProps = {}; // Previous props would be stored in state or ref
    const nextProps = { isLoading }; // Current props
    
    return ComponentOptimizer.shouldComponentUpdate(
      prevProps,
      nextProps,
      ['isLoading']
    );
  }, [isLoading]);
  
  if (!shouldRender && !isLoading) {
    return null; // Skip rendering if props haven't changed
  }
  
  return (
    <div 
      ref={containerRef}
      className="optimized-unified-chat-interface"
      onClick={handleClick}
      onScroll={handleScroll}
    >
      {isLoading ? (
        <div className="loading-indicator">Loading optimized interface...</div>
      ) : (
        <div>Optimized Interface Loaded</div>
      )}
    </div>
  );
};

/**
 * Virtualized message list component for handling large message histories efficiently
 */
export const VirtualizedMessageList: React.FC<{ messages: CopilotMessage[] }> = ({ messages }) => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const itemHeight = 80; // Approximate height of each message item
  
  // Calculate visible items
  const { startIndex, endIndex } = useMemo(() => {
    if (!containerRef.current) {
      return { startIndex: 0, endIndex: 10 };
    }
    
    const containerHeight = containerRef.current.clientHeight;
    return VirtualListUtils.calculateVisibleItems(
      messages.length,
      itemHeight,
      containerHeight,
      scrollTop
    );
  }, [messages.length, scrollTop]);
  
  // Handle scroll with throttling
  const handleScroll = useMemo(
    () => throttle((event: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(event.currentTarget.scrollTop);
    }, 16), // ~60fps
    []
  );
  
  // Calculate total height
  const totalHeight = useMemo(
    () => VirtualListUtils.calculateTotalHeight(messages.length, itemHeight),
    [messages.length, itemHeight]
  );
  
  // Visible items
  const visibleItems = useMemo(
    () => messages.slice(startIndex, endIndex + 1),
    [messages, startIndex, endIndex]
  );
  
  return (
    <div
      ref={containerRef}
      className="virtualized-message-list"
      onScroll={handleScroll}
      style={{ height: '100%', overflowY: 'auto' }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((message, index) => {
          const actualIndex = startIndex + index;
          const offset = VirtualListUtils.calculateItemOffset(actualIndex, itemHeight);
          
          return (
            <div
              key={message.id}
              className="message-item"
              style={{
                position: 'absolute',
                top: offset,
                width: '100%',
                height: itemHeight
              }}
            >
              {/* Message content would go here */}
              <div className="message-preview">
                Message {actualIndex}: {message.content?.substring(0, 50)}...
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Optimized image component with lazy loading and responsive sizing
 */
export const OptimizedImage: React.FC<{
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
}> = ({ src, alt, width = 400, height, className }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [imageSrc, setImageSrc] = useState<string>('');
  const imgRef = useRef<HTMLImageElement>(null);
  
  // Generate optimized image URL
  const optimizedSrc = useMemo(() => {
    return ImageOptimizer.getOptimizedImageUrl(src, width, height);
  }, [src, width, height]);
  
  // Generate srcset for responsive images
  // const _srcset = useMemo(() => {
  //   return ImageOptimizer.generateSrcset(src, [200, 400, 800, 1200]);
  // }, [src]);
  
  // Generate sizes attribute
  // const _sizes = useMemo(() => {
  //   return ImageOptimizer.generateSizes([
  //     { maxWidth: 600, size: '100vw' },
  //     { maxWidth: 1200, size: '50vw' },
  //     { maxWidth: 1800, size: '33vw' }
  //   ]);
  // }, []);
  
  // Lazy loading with intersection observer
  useEffect(() => {
    if (imgRef.current) {
      const currentImgRef = imgRef.current;
      LazyLoader.register(currentImgRef, () => {
        setImageSrc(optimizedSrc);
      });
      
      return () => {
        LazyLoader.unregister(currentImgRef);
      };
    }
  }, [optimizedSrc]);
  
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
  }, []);
  
  return (
    <div className={`optimized-image-container ${className || ''}`}>
      {!isLoaded && (
        <div className="image-placeholder">
          <div className="loading-spinner"></div>
        </div>
      )}
      <Image
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        width={width}
        height={height || width} // Use width as fallback if height is not provided
        onLoad={handleLoad}
        className={`optimized-image ${isLoaded ? 'loaded' : 'loading'} ${className || ''}`}
        loading="lazy"
      />
    </div>
  );
};

/**
 * Optimized code block with syntax highlighting and caching
 */
export const OptimizedCodeBlock: React.FC<{
  code: string;
  language: string;
  className?: string;
}> = ({ code, language, className }) => {
  const [highlightedCode, setHighlightedCode] = useState<string>('');
  const [isHighlighting, setIsHighlighting] = useState(true);
  
  // Mock highlight function (in a real implementation, this would use a library like Prism or highlight.js)
  const highlightCode = useCallback(async (code: string, lang: string): Promise<string> => {
    // Simulate async highlighting
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Simple mock highlighting - in a real implementation, this would use a proper highlighter
    return `<pre><code class="language-${lang}">${code.replace(/</g, '<').replace(/>/g, '>')}</code></pre>`;
  }, []);
  
  // Highlight code with caching
  useEffect(() => {
    const highlight = async () => {
      const endMeasure = PerformanceMonitor.startMeasure('code-highlight');
      
      try {
        const highlighted = await CodeHighlighter.highlightCode(code, language, highlightCode);
        setHighlightedCode(highlighted);
      } catch (error) {
        console.error('Failed to highlight code:', error);
        setHighlightedCode(`<pre><code>${code}</code></pre>`);
      } finally {
        setIsHighlighting(false);
        endMeasure();
      }
    };
    
    highlight();
  }, [code, language, highlightCode]);
  
  if (isHighlighting) {
    return (
      <div className={`code-block-loading ${className || ''}`}>
        <div className="loading-spinner"></div>
        <div>Highlighting code...</div>
      </div>
    );
  }
  
  return (
    <div 
      className={`optimized-code-block ${className || ''}`}
      dangerouslySetInnerHTML={{ __html: highlightedCode }}
    />
  );
};

/**
 * ChatInterface - Main interface that integrates all components
 * Implements Phase 6 of the INNOVATIVE_COPILOT_PLAN.md
 */

interface ChatInterfaceProps {
  className?: string;
  backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
}

/**
 * Main ChatInterface component with all providers
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  className,
  backendConfig
}) => {
  return (
    <ContextBridgeProvider>
      <WorkflowEngineProvider>
        <ArtifactSystemProvider>
          <AdaptiveInterface expertiseLevel="intermediate">
            <AdaptiveLayout>
              <ChatInterfaceContent
                className={className}
                backendConfig={backendConfig}
              />
            </AdaptiveLayout>
          </AdaptiveInterface>
        </ArtifactSystemProvider>
      </WorkflowEngineProvider>
    </ContextBridgeProvider>
  );
};

/**
 * ChatInterfaceContent - The actual content component
 */
const ChatInterfaceContent: React.FC<ChatInterfaceProps> = ({
  className,
  backendConfig
}) => {
  const {
    state,
    sendMessage,
    executeAction,
    executeWorkflow,
    openArtifact,
    isInitialized
  } = useCopilotEngine(undefined, backendConfig);

  const {
    createBackendRequest,
    activePanel,
    updateUIContext
  } = useContextBridge();

  const {
    activeWorkflows
  } = useWorkflowEngine();

  const {
    artifacts
  } = useArtifactSystem();

  const {
    sidebarOpen,
    toggleSidebar
  } = useAdaptiveLayout();

  const [inputModality, setInputModality] = useState<'text' | 'code' | 'image' | 'audio'>('text');
  const [suggestions] = useState<CopilotSuggestion[]>([
    {
      id: 'suggestion-1',
      type: 'response',
      title: 'Help me write code',
      description: 'Get assistance with writing, debugging, or optimizing code',
      confidence: 0.9,
      priority: 'high',
    },
    {
      id: 'suggestion-2',
      type: 'workflow',
      title: 'Analyze my project',
      description: 'Run a comprehensive analysis workflow on your project',
      confidence: 0.8,
      priority: 'medium',
    },
    {
      id: 'suggestion-3',
      type: 'artifact',
      title: 'Generate documentation',
      description: 'Create documentation for your code or project',
      confidence: 0.7,
      priority: 'medium',
    },
  ]);

  // Initialize with welcome message
  useEffect(() => {
    if (isInitialized && state.messages.length === 0) {
      // The welcome message will be added by the CopilotEngine
    }
  }, [isInitialized, state.messages.length]);

  // Handle sending a message
  const handleSendMessage = useCallback(async (message: string, modality?: 'text' | 'code' | 'image' | 'audio', file?: File) => {
    if ((!message.trim() && !file) || state.isLoading) return;

    try {
      // Create backend request
      createBackendRequest(message, modality);
      
      // Send message to backend
      await sendMessage(message, modality);
      
      // The actual response will be handled by the CopilotEngine through its state update
      // No need to manually add a placeholder response here
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }, [state.isLoading, createBackendRequest, sendMessage]);

  // Handle executing an action
  const handleExecuteAction = useCallback(async (actionId: string) => {
    try {
      // Execute the action using CopilotEngine
      await executeAction({ id: actionId, title: actionId });
    } catch (error) {
      console.error('Error executing action:', error);
    }
  }, [executeAction]);

  // Handle executing a workflow
  const handleExecuteWorkflow = useCallback(async (workflowId: string) => {
    try {
      // Start the workflow using CopilotEngine
      await executeWorkflow({ id: workflowId, name: workflowId });
    } catch (error) {
      console.error('Error executing workflow:', error);
    }
  }, [executeWorkflow]);

  // Handle generating an artifact
  const handleGenerateArtifact = useCallback(async (type: 'code' | 'documentation' | 'analysis' | 'test', prompt: string) => {
    try {
      // Generate the artifact using CopilotEngine
      await openArtifact({ id: type, title: prompt });
    } catch (error) {
      console.error('Error generating artifact:', error);
    }
  }, [openArtifact]);

  // Handle selecting a suggestion
  const handleSelectSuggestion = useCallback((suggestion: CopilotSuggestion) => {
    switch (suggestion.type) {
      case 'response':
        // Response suggestions would be handled directly by the input component
        break;
      case 'action':
        // Actions would be executed directly
        break;
      case 'workflow':
        handleExecuteWorkflow(suggestion.data?.id || '');
        break;
      case 'artifact':
        handleGenerateArtifact(
          suggestion.data?.type || 'code',
          suggestion.title
        );
        break;
      case 'setting':
        // Settings would be applied directly
        break;
    }
  }, [handleExecuteWorkflow, handleGenerateArtifact]);

  // Handle changing the active panel
  const handleChangePanel = useCallback((panel: 'chat' | 'memory' | 'workflows' | 'artifacts') => {
    updateUIContext({ activePanel: panel });
  }, [updateUIContext]);

  return (
    <div className={`flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 ${className}`}>
      <div className="flex flex-col h-full max-w-4xl mx-auto w-full px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">KAREN AI Assistant</h1>
              <p className="text-sm text-muted-foreground">Your intelligent development companion</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="hidden sm:flex">
              {activeWorkflows.length} active workflows
            </Badge>
            <Badge variant="outline" className="hidden sm:flex">
              {artifacts.length} artifacts
            </Badge>
            <Button variant="ghost" size="sm" onClick={toggleSidebar}>
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden gap-4">
          {/* Sidebar */}
          {sidebarOpen && (
            <div className="hidden md:flex w-64 flex-col rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="font-semibold mb-3">Navigation</h2>
                <div className="space-y-1">
                  <Button
                    variant={activePanel === 'chat' ? 'default' : 'ghost'}
                    className="w-full justify-start rounded-lg"
                    onClick={() => handleChangePanel('chat')}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Chat
                  </Button>
                  <Button
                    variant={activePanel === 'memory' ? 'default' : 'ghost'}
                    className="w-full justify-start rounded-lg"
                    onClick={() => handleChangePanel('memory')}
                  >
                    <History className="h-4 w-4 mr-2" />
                    Memory
                  </Button>
                  <Button
                    variant={activePanel === 'workflows' ? 'default' : 'ghost'}
                    className="w-full justify-start rounded-lg"
                    onClick={() => handleChangePanel('workflows')}
                  >
                    <Workflow className="h-4 w-4 mr-2" />
                    Workflows
                  </Button>
                  <Button
                    variant={activePanel === 'artifacts' ? 'default' : 'ghost'}
                    className="w-full justify-start rounded-lg"
                    onClick={() => handleChangePanel('artifacts')}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    Artifacts
                  </Button>
                  <Button
                    variant={activePanel === 'artifacts' ? 'default' : 'ghost'}
                    className="w-full justify-start rounded-lg"
                    onClick={() => handleChangePanel('artifacts')}
                  >
                    <Bot className="h-4 w-4 mr-2" />
                    Plugins
                  </Button>
                </div>
              </div>
              
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="font-semibold mb-3">Suggestions</h2>
                <ContextualSuggestions
                  suggestions={suggestions}
                  onSelectSuggestion={handleSelectSuggestion}
                />
              </div>
              
              <div className="p-4 flex-1 overflow-y-auto">
                <h2 className="font-semibold mb-3">Active Workflows</h2>
                <div className="space-y-2">
                  {activeWorkflows.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No active workflows</p>
                  ) : (
                    activeWorkflows.map(id => (
                      <div key={id} className="text-sm p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Workflow {id}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Main panel */}
          <div className="flex-1 flex flex-col">
            <Tabs value={activePanel} className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-5 mb-4 bg-white dark:bg-gray-800 p-1 rounded-xl shadow-sm">
                <TabsTrigger value="chat" className="flex items-center gap-1 rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">
                  <MessageSquare className="h-4 w-4" />
                  <span className="hidden sm:inline">Chat</span>
                </TabsTrigger>
                <TabsTrigger value="memory" className="flex items-center gap-1 rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">
                  <History className="h-4 w-4" />
                  <span className="hidden sm:inline">Memory</span>
                </TabsTrigger>
                <TabsTrigger value="workflows" className="flex items-center gap-1 rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">
                  <Workflow className="h-4 w-4" />
                  <span className="hidden sm:inline">Workflows</span>
                </TabsTrigger>
                <TabsTrigger value="artifacts" className="flex items-center gap-1 rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">
                  <FileText className="h-4 w-4" />
                  <span className="hidden sm:inline">Artifacts</span>
                </TabsTrigger>
                <TabsTrigger value="plugins" className="flex items-center gap-1 rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">
                  <Bot className="h-4 w-4" />
                  <span className="hidden sm:inline">Plugins</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0 data-[state=active]:flex">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto pb-4">
                  <div className="space-y-4 max-w-3xl mx-auto">
                    {state.messages.map(message => (
                      <SmartMessageBubble
                        key={message.id}
                        id={message.id}
                        content={message.content}
                        role={message.role}
                        timestamp={message.timestamp}
                        metadata={{
                          ...message.metadata,
                          suggestions: message.metadata?.suggestions?.map(s => s.title) || []
                        }}
                        onExecuteAction={handleExecuteAction}
                      />
                    ))}
                    {state.isLoading && (
                      <div className="flex items-center justify-center py-4">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>KAREN is thinking...</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Input */}
                <div className="mt-auto pt-4">
                  <MultiModalInput
                    onSendMessage={handleSendMessage}
                    isLoading={state.isLoading}
                    inputModality={inputModality}
                    onModalityChange={setInputModality}
                  />
                </div>
              </TabsContent>

              <TabsContent value="memory" className="flex-1 p-4 data-[state=active]:flex">
                <div className="max-w-3xl mx-auto">
                  <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
                    <CardHeader>
                      <CardTitle>Memory Management</CardTitle>
                      <CardDescription>
                        View and manage your conversation history and context
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground">Memory management features will be implemented here.</p>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="workflows" className="flex-1 p-0 m-0 data-[state=active]:flex">
                <WorkflowAutomation />
              </TabsContent>

              <TabsContent value="artifacts" className="flex-1 p-0 m-0 data-[state=active]:flex">
                <ArtifactSystem />
              </TabsContent>

              <TabsContent value="plugins" className="flex-1 p-4 data-[state=active]:flex">
                <div className="max-w-3xl mx-auto">
                  <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
                    <CardHeader>
                      <CardTitle>Plugin Management</CardTitle>
                      <CardDescription>
                        Manage your plugins and extensions
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground">Plugin management features will be implemented here.</p>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
