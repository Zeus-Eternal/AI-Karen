import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';

export const Documentation: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="documentation-container max-w-4xl mx-auto p-6">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Copilot-First Chat System Documentation</CardTitle>
          <p className="text-gray-600">
            Comprehensive guide to the innovative Copilot-first architecture and its components
          </p>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
          <TabsTrigger value="components">Components</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="testing">Testing</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>System Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The Copilot-First Chat System is an innovative approach to AI-powered chat interfaces 
                where Copilot serves as the central intelligence rather than an add-on feature. This system 
                provides proactive intelligence, enhanced context management, and adaptive interfaces.
              </p>
              
              <h3 className="text-lg font-semibold">Key Features</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Proactive Intelligence</strong>: Anticipates user needs rather than just reacting</li>
                <li><strong>Enhanced Context System</strong>: Multi-layered context combining user, conversation, system, external, and semantic contexts</li>
                <li><strong>Adaptive Interface</strong>: Dynamically adjusts UI based on user expertise level and screen size</li>
                <li><strong>Multi-Modal Input</strong>: Support for text, code, image, and audio inputs with advanced features</li>
                <li><strong>Workflow Automation</strong>: Copilot-powered workflow execution with templates and history</li>
                <li><strong>Artifact System</strong>: Intelligent artifact generation with version control and collaboration</li>
              </ul>

              <h3 className="text-lg font-semibold">Implementation Phases</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 1: Copilot Intelligence Core</h4>
                  <p className="text-sm text-gray-600">Foundation for Copilot-first architecture</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 2: Intelligent Assistant Features</h4>
                  <p className="text-sm text-gray-600">Proactive suggestions and multi-modal input</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 3: Adaptive Interface System</h4>
                  <p className="text-sm text-gray-600">Dynamic UI based on user expertise</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 4: Workflow Automation</h4>
                  <p className="text-sm text-gray-600">Copilot-powered workflow execution</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 5: Enhanced Artifact System</h4>
                  <p className="text-sm text-gray-600">Intelligent artifact generation</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Phase 6: Integration and Polish</h4>
                  <p className="text-sm text-gray-600">Complete system integration</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="architecture" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>System Architecture</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The Copilot-First architecture is designed around a central intelligence engine that 
                coordinates all AI features and provides a unified interface for users.
              </p>

              <h3 className="text-lg font-semibold">Core Components</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium flex items-center gap-2">
                    CopilotEngine <Badge variant="secondary">Core</Badge>
                  </h4>
                  <p className="text-sm text-gray-600 mt-2">
                    The central AI intelligence engine with proactive intelligence features. 
                    Integrates ContextManager and IntelligenceOrchestrator to provide a unified 
                    interface for React components.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/core/CopilotEngine.tsx</code>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium flex items-center gap-2">
                    ContextManager <Badge variant="secondary">Core</Badge>
                  </h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Implements multi-layered context management, handling user, conversation, 
                    system, external, and semantic contexts. Provides methods for updating 
                    context with new messages and managing external data.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/core/ContextManager.tsx</code>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium flex items-center gap-2">
                    IntelligenceOrchestrator <Badge variant="secondary">Core</Badge>
                  </h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Coordinates AI features and intelligence, generating suggestions, actions, 
                    workflows, and artifacts based on context. Manages feature enablement and 
                    plugin integration.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/core/IntelligenceOrchestrator.tsx</code>
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-semibold">Type System</h3>
              <p>
                The system uses comprehensive TypeScript type definitions to ensure type safety 
                and provide clear interfaces for all components.
              </p>
              <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                <code>src/components/copilot-chat/types/copilot.ts</code>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="components" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Component Library</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The system provides a comprehensive set of React components that implement the 
                Copilot-first architecture. These components are designed to be reusable and 
                composable, allowing for flexible implementation.
              </p>

              <h3 className="text-lg font-semibold">Interface Components</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">ChatInterface</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Main interface that integrates all components. Combines Copilot Intelligence 
                    Core, Intelligent Assistant Features, Adaptive Interface System, Workflow 
                    Automation, and Enhanced Artifact System.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/ChatInterface.tsx</code>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">ChatInterface</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Optimized version of the ChatInterface with performance enhancements. 
                    Implements debouncing, throttling, and other performance optimizations.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/ChatInterface.tsx</code>
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-semibold">Feature Components</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">IntelligentAssistant</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Enhanced assistant component with proactive suggestions and multi-modal input 
                    capabilities.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">AdaptiveInterface</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Dynamic interface that adjusts based on user expertise level and context.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">WorkflowAutomation</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Interface for interacting with Copilot-powered workflows.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">ArtifactSystem</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    System for managing intelligent artifact generation with version control.
                  </p>
                </div>
              </div>

              <h3 className="text-lg font-semibold">Performance Components</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">VirtualizedMessageList</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Optimized message list component that uses virtual scrolling for performance 
                    with large numbers of messages.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">OptimizedImage</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Image component with lazy loading and optimization features.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">OptimizedCodeBlock</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Code block component with syntax highlighting and performance optimizations.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Optimization</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The system includes comprehensive performance optimizations to ensure smooth 
                operation even with large amounts of data and complex interactions.
              </p>

              <h3 className="text-lg font-semibold">Performance Utilities</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Debounce and Throttle</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Utilities for debouncing and throttling function calls to improve performance 
                    during rapid events like typing or scrolling.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/utils/performance.ts</code>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Virtual Scrolling</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Implementation of virtual scrolling for efficiently rendering large lists 
                    by only rendering visible items.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Lazy Loading</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Lazy loading implementation for images and other resources to improve initial 
                    load times.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Memoization</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Utilities for memoizing function results and component rendering to avoid 
                    unnecessary computations.
                  </p>
                </div>
              </div>

              <h3 className="text-lg font-semibold">Performance Hooks</h3>
              <p>
                The system provides a collection of React hooks for performance optimization:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li><code>usePerformance</code> - Tracks component performance metrics</li>
                <li><code>useDebounce</code> - Debounces value changes</li>
                <li><code>useThrottle</code> - Throttles function calls</li>
                <li><code>useVirtualScroll</code> - Implements virtual scrolling</li>
                <li><code>useMemoize</code> - Memoizes function results</li>
                <li><code>useRenderTime</code> - Measures render time</li>
                <li><code>useShouldUpdate</code> - Determines if component should update</li>
                <li><code>useApiCall</code> - Optimizes API calls with caching and debouncing</li>
              </ul>
              <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                <code>src/components/copilot-chat/hooks/usePerformance.ts</code>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="testing" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Testing Strategy</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The system includes comprehensive testing to ensure reliability and correctness 
                of all components and utilities.
              </p>

              <h3 className="text-lg font-semibold">Test Coverage</h3>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Core Components</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Comprehensive tests for ContextManager, IntelligenceOrchestrator, and 
                    CopilotEngine to ensure correct behavior and error handling.
                  </p>
                  <div className="mt-2 text-xs bg-gray-100 p-2 rounded">
                    <code>src/components/copilot-chat/__tests__/</code>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Performance Utilities</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Tests for all performance utilities including debounce, throttle, virtual 
                    scrolling, and memoization functions.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Performance Hooks</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Tests for React hooks to ensure correct behavior and performance 
                    optimization.
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium">Interface Components</h4>
                  <p className="text-sm text-gray-600 mt-2">
                    Tests for interface components including ChatInterface and 
                    ChatInterface.
                  </p>
                </div>
              </div>

              <h3 className="text-lg font-semibold">Testing Approach</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Unit Testing</strong>: Individual component testing in isolation</li>
                <li><strong>Integration Testing</strong>: Testing component interactions</li>
                <li><strong>Performance Testing</strong>: Measuring and optimizing performance</li>
                <li><strong>Error Handling</strong>: Testing error scenarios and recovery</li>
                <li><strong>Accessibility Testing</strong>: Ensuring accessibility compliance</li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="examples" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Examples</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                Here are some examples of how to use the Copilot-First Chat System components 
                in your application.
              </p>

              <h3 className="text-lg font-semibold">Basic Usage</h3>
              <div className="bg-gray-100 p-4 rounded-lg">
                <pre>
{`import { ChatInterface } from './components/copilot-chat/ChatInterface';

function App() {
  return (
    <div className="App">
      <ChatInterface />
    </div>
  );
}`}
                </pre>
              </div>

              <h3 className="text-lg font-semibold">Optimized Usage</h3>
              <div className="bg-gray-100 p-4 rounded-lg">
                <pre>
{`import { ChatInterface } from './components/copilot-chat/ChatInterface';

function App() {
  return (
    <div className="App">
      <ChatInterface />
    </div>
  );
}`}
                </pre>
              </div>

              <h3 className="text-lg font-semibold">Using Performance Hooks</h3>
              <div className="bg-gray-100 p-4 rounded-lg">
                <pre>
{`import { usePerformance, useDebounce, useVirtualScroll } from './components/copilot-chat/hooks/usePerformance';

function ChatComponent() {
  const { renderCount } = usePerformance('ChatComponent');
  const [inputValue, setInputValue] = useState('');
  const debouncedValue = useDebounce(inputValue, 300);
  const { visibleItems } = useVirtualScroll(messages, 50, 400);
  
  return (
    <div>
      <div>Rendered {renderCount} times</div>
      <input 
        value={inputValue} 
        onChange={(e) => setInputValue(e.target.value)} 
      />
      <div>
        {visibleItems.map(item => (
          <MessageItem key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}`}
                </pre>
              </div>

              <h3 className="text-lg font-semibold">Using Performance Utilities</h3>
              <div className="bg-gray-100 p-4 rounded-lg">
                <pre>
{`import { 
  debounce, 
  throttle, 
  memoize, 
  VirtualListUtils 
} from './components/copilot-chat/utils/performance';

// Debounce a function
const debouncedSearch = debounce((query: string) => {
  // Perform search
}, 300);

// Throttle a function
const throttledScroll = throttle((event: Event) => {
  // Handle scroll
}, 100);

// Memoize a function
const expensiveCalculation = memoize((input: number) => {
  // Perform expensive calculation
  return result;
});

// Use virtual scrolling
const { startIndex, endIndex } = VirtualListUtils.calculateVisibleRange(
  scrollTop, 
  containerHeight, 
  itemHeight, 
  totalItems
);`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};