# CoPilot Developer Guide

## Table of Contents
- [Introduction](#introduction)
- [Architecture Overview](#architecture-overview)
- [Development Environment Setup](#development-environment-setup)
- [Core Components](#core-components)
- [Extension Development](#extension-development)
- [Customization](#customization)
- [Testing](#testing)
- [Performance Optimization](#performance-optimization)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive information for developers working with CoPilot. It covers the architecture, development environment setup, core components, extension development, and best practices.

### Target Audience

This guide is intended for:

- Software developers integrating with CoPilot
- Extension developers creating new functionality
- System administrators deploying CoPilot
- DevOps engineers managing CoPilot infrastructure

### Prerequisites

Before starting, you should have:

- Experience with TypeScript and JavaScript
- Knowledge of React and modern web development
- Understanding of REST APIs and WebSocket connections
- Familiarity with Git and version control
- Basic understanding of AI/ML concepts

### Documentation Structure

This guide is organized into sections that build upon each other:

1. **Architecture Overview**: High-level understanding of CoPilot architecture
2. **Development Environment Setup**: Setting up your development environment
3. **Core Components**: Detailed explanation of core components
4. **Extension Development**: Creating extensions for CoPilot
5. **Customization**: Customizing CoPilot behavior and appearance
6. **Testing**: Testing strategies and tools
7. **Performance Optimization**: Optimizing CoPilot performance
8. **Deployment**: Deploying CoPilot to production
9. **Best Practices**: Recommended practices for CoPilot development
10. **Troubleshooting**: Common issues and solutions

## Architecture Overview

### High-Level Architecture

CoPilot follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    CoPilot (UI/UX Layer)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────┐    │
│  │   Chat UI      │  │   Task UI      │  │ Memory│    │
│  │   Component     │  │   Component     │  │ UI    │    │
│  └─────────────────┘  └─────────────────┘  └───────┘    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Agent UI Service                          │   │
│  │  • Translates UI interactions to AgentTask objects   │   │
│  │  • Maintains session state                          │   │
│  │  • Routes requests to appropriate agent components   │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────┐    │
│  │ Thread Manager  │  │Session State   │  │Safety │    │
│  │                 │  │Manager         │  │Middleware│    │
│  └─────────────────┘  └─────────────────┘  └───────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Architecture (Backend Engine)           │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────┐    │
│  │Agent Orchestrator│  │   Task Router  │  │Agent  │    │
│  │                 │  │                 │  │Executor│    │
│  └─────────────────┘  └─────────────────┘  └───────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Supporting Systems                     │   │
│  │  • AI Orchestrator • Memory • Tools • Safety  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

CoPilot's architecture is guided by several key principles:

#### Separation of Concerns

- **UI/UX Layer**: CoPilot handles all user interface and user experience aspects
- **Business Logic**: Agent architecture handles all business logic and processing
- **Clear Boundaries**: Well-defined interfaces between components

#### Headless-First Design

- **Headless Backend**: Agent architecture is designed to be headless
- **Multiple UIs**: CoPilot is one of many possible UI layers
- **API-First**: All functionality is accessible through APIs

#### Component-Based Architecture

- **Reusable Components**: UI components are reusable and composable
- **Loose Coupling**: Components are loosely coupled and independently deployable
- **High Cohesion**: Components have high internal cohesion

#### Extensibility

- **Extension System**: Comprehensive extension system for adding functionality
- **Plugin Architecture**: Plugin architecture for customizing behavior
- **Hook System**: Hook system for extending core functionality

### Component Relationships

The following diagram shows the relationships between key components:

```mermaid
classDiagram
    class CoPilotUI {
        +ChatComponent
        +TaskComponent
        +MemoryComponent
        +AgentSelectionComponent
    }
    
    class AgentUIService {
        +sendMessage()
        +createDeepTask()
        +getTaskProgress()
    }
    
    class ThreadManager {
        +createThread()
        +getLanggraphThread()
        +getCopilotSession()
    }
    
    class SessionStateManager {
        +saveSessionState()
        +loadSessionState()
    }
    
    class SafetyMiddleware {
        +validateRequest()
        +checkContentSafety()
        +checkAuthorization()
    }
    
    class AgentOrchestrator {
        +executeTask()
        +routeTask()
        +selectExecutionMode()
    }
    
    class AgentExecutor {
        +executeNativeMode()
        +executeDeepAgentsMode()
        +executeLangGraphMode()
    }
    
    class SupportingSystems {
        +AIOrchestrator
        +Memory
        +Tools
        +Safety
    }
    
    CoPilotUI --> AgentUIService
    AgentUIService --> ThreadManager
    AgentUIService --> SessionStateManager
    AgentUIService --> SafetyMiddleware
    AgentUIService --> AgentOrchestrator
    AgentOrchestrator --> AgentExecutor
    AgentExecutor --> SupportingSystems
```

### Data Flow

The following diagram shows the data flow through the system:

```mermaid
sequenceDiagram
    participant C as CoPilot UI
    participant AUI as Agent UI Service
    participant TM as Thread Manager
    participant SSM as Session State Manager
    participant SM as Safety Middleware
    participant AO as Agent Orchestrator
    participant AE as Agent Executor
    participant SS as Supporting Systems
    
    C->>AUI: User interaction (message, task, etc.)
    AUI->>TM: Get or create thread
    AUI->>SSM: Get or create session state
    AUI->>SM: Validate request
    SM-->>AUI: Validation result
    AUI->>AO: Forward validated request
    AO->>AE: Execute task
    AE->>SS: Access supporting systems
    SS-->>AE: System response
    AE-->>AO: Execution result
    AO-->>AUI: Formatted response
    AUI->>SSM: Update session state
    AUI-->>C: UI response
```

## Development Environment Setup

### Prerequisites

Before setting up your development environment, ensure you have:

- **Node.js**: Version 16.x or later
- **npm**: Version 8.x or later
- **Git**: Version 2.x or later
- **Python**: Version 3.8 or later (for backend components)
- **Docker**: Version 20.x or later (for containerized deployment)
- **VS Code**: Latest version with recommended extensions

### Repository Setup

1. **Clone the Repository**:

```bash
git clone https://github.com/your-org/copilot.git
cd copilot
```

2. **Install Dependencies**:

```bash
# Frontend dependencies
npm install

# Backend dependencies (if working on backend components)
cd server
pip install -r requirements.txt
```

3. **Set Up Environment Variables**:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file with your settings
nano .env
```

### IDE Configuration

For the best development experience, configure your IDE with the following:

#### VS Code Extensions

Install these recommended VS Code extensions:

- **ESLint**: For code linting
- **Prettier**: For code formatting
- **GitLens**: For enhanced Git integration
- **Path Intellisense**: For path autocompletion
- **Auto Rename Tag**: For HTML/XML tag renaming
- **Bracket Pair Colorizer**: For visual bracket matching
- **Material Icon Theme**: For better file icons

#### VS Code Settings

Add these settings to your VS Code settings:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "files.associations": {
    "*.css": "postcss"
  }
}
```

### Local Development

#### Starting the Development Server

```bash
# Start the frontend development server
npm run dev

# In another terminal, start the backend server (if needed)
cd server
npm run dev
```

#### Accessing the Development Environment

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Testing Setup

#### Running Tests

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e

# Run all tests
npm run test:all
```

#### Test Coverage

```bash
# Generate test coverage report
npm run test:coverage
```

### Debugging Setup

#### Frontend Debugging

1. Open Chrome DevTools (F12)
2. Go to the "Sources" tab
3. Find your source files under `webpack://`
4. Set breakpoints and debug as needed

#### Backend Debugging

```bash
# Start the backend in debug mode
cd server
npm run debug
```

Then attach your debugger to the process (usually on port 9229).

## Core Components

### Agent UI Service

The Agent UI Service acts as a bridge between CoPilot UI and the agent architecture.

#### Interface

```typescript
interface AgentUIService {
  sendMessage(request: SendMessageRequest): Promise<SendMessageResponse>;
  createDeepTask(request: CreateDeepTaskRequest): Promise<CreateDeepTaskResponse>;
  getTaskProgress(request: GetTaskProgressRequest): Promise<GetTaskProgressResponse>;
}
```

#### Implementation

```typescript
class AgentUIServiceImpl implements AgentUIService {
  private threadManager: ThreadManager;
  private sessionStateManager: SessionStateManager;
  private safetyMiddleware: SafetyMiddleware;
  private agentOrchestrator: AgentOrchestrator;

  constructor(
    threadManager: ThreadManager,
    sessionStateManager: SessionStateManager,
    safetyMiddleware: SafetyMiddleware,
    agentOrchestrator: AgentOrchestrator
  ) {
    this.threadManager = threadManager;
    this.sessionStateManager = sessionStateManager;
    this.safetyMiddleware = safetyMiddleware;
    this.agentOrchestrator = agentOrchestrator;
  }

  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    // Get or create thread for session
    const threadId = await this.threadManager.getLanggraphThread(request.sessionId);
    
    // Get session state
    const sessionState = await this.sessionStateManager.loadSessionState(request.sessionId);
    
    // Validate request
    const validationResult = await this.safetyMiddleware.validateRequest(request);
    if (!validationResult.isValid) {
      throw new Error(`Request validation failed: ${validationResult.reason}`);
    }
    
    // Forward to agent orchestrator
    const agentRequest = {
      ...request,
      threadId,
      sessionState
    };
    
    const response = await this.agentOrchestrator.executeTask(agentRequest);
    
    // Update session state
    await this.sessionStateManager.saveSessionState(request.sessionId, response.sessionState);
    
    return response;
  }

  async createDeepTask(request: CreateDeepTaskRequest): Promise<CreateDeepTaskResponse> {
    // Similar implementation for deep task creation
  }

  async getTaskProgress(request: GetTaskProgressRequest): Promise<GetTaskProgressResponse> {
    // Implementation for getting task progress
  }
}
```

### Thread Manager

The Thread Manager manages the mapping between CoPilot sessions and LangGraph threads.

#### Interface

```typescript
interface ThreadManager {
  createThread(copilotSessionId: string): Promise<string>;
  getLanggraphThread(copilotSessionId: string): Promise<string>;
  getCopilotSession(langgraphThreadId: string): Promise<string>;
}
```

#### Implementation

```typescript
class ThreadManagerImpl implements ThreadManager {
  private sessionToThreadMap: Map<string, string> = new Map();
  private threadToSessionMap: Map<string, string> = new Map();
  private persistence: PersistenceService;

  constructor(persistence: PersistenceService) {
    this.persistence = persistence;
    this.loadMappings();
  }

  async createThread(copilotSessionId: string): Promise<string> {
    const threadId = await this.createLanggraphThread();
    
    this.sessionToThreadMap.set(copilotSessionId, threadId);
    this.threadToSessionMap.set(threadId, copilotSessionId);
    
    await this.saveMappings();
    
    return threadId;
  }

  async getLanggraphThread(copilotSessionId: string): Promise<string> {
    let threadId = this.sessionToThreadMap.get(copilotSessionId);
    
    if (!threadId) {
      threadId = await this.createThread(copilotSessionId);
    }
    
    return threadId;
  }

  async getCopilotSession(langgraphThreadId: string): Promise<string> {
    const sessionId = this.threadToSessionMap.get(langgraphThreadId);
    
    if (!sessionId) {
      throw new Error(`No session found for thread: ${langgraphThreadId}`);
    }
    
    return sessionId;
  }

  private async createLanggraphThread(): Promise<string> {
    // Call LangGraph API to create a new thread
    const response = await fetch(`${LANGGRAPH_API_URL}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${LANGGRAPH_API_KEY}`
      }
    });
    
    const data = await response.json();
    return data.threadId;
  }

  private async loadMappings(): Promise<void> {
    // Load mappings from persistence
  }

  private async saveMappings(): Promise<void> {
    // Save mappings to persistence
  }
}
```

### Session State Manager

The Session State Manager handles persistence and retrieval of session state.

#### Interface

```typescript
interface SessionStateManager {
  saveSessionState(copilotSessionId: string, state: SessionState): Promise<void>;
  loadSessionState(copilotSessionId: string): Promise<SessionState>;
}
```

#### Implementation

```typescript
class SessionStateManagerImpl implements SessionStateManager {
  private langGraphCheckpointService: LangGraphCheckpointService;
  private unifiedMemoryService: UnifiedMemoryService;

  constructor(
    langGraphCheckpointService: LangGraphCheckpointService,
    unifiedMemoryService: UnifiedMemoryService
  ) {
    this.langGraphCheckpointService = langGraphCheckpointService;
    this.unifiedMemoryService = unifiedMemoryService;
  }

  async saveSessionState(copilotSessionId: string, state: SessionState): Promise<void> {
    // Save to LangGraph checkpoints
    await this.langGraphCheckpointService.saveCheckpoint(copilotSessionId, state);
    
    // Save to Unified Memory Service
    await this.unifiedMemoryService.saveMemory(copilotSessionId, {
      type: 'session_state',
      data: state,
      timestamp: new Date().toISOString()
    });
  }

  async loadSessionState(copilotSessionId: string): Promise<SessionState> {
    // Try to load from LangGraph checkpoints first
    try {
      const checkpoint = await this.langGraphCheckpointService.loadCheckpoint(copilotSessionId);
      if (checkpoint) {
        return checkpoint.state;
      }
    } catch (error) {
      console.error('Error loading from LangGraph checkpoints:', error);
    }
    
    // Fallback to Unified Memory Service
    try {
      const memory = await this.unifiedMemoryService.loadMemory(copilotSessionId);
      if (memory && memory.type === 'session_state') {
        return memory.data;
      }
    } catch (error) {
      console.error('Error loading from Unified Memory Service:', error);
    }
    
    // Return default state if no state found
    return this.getDefaultSessionState();
  }

  private getDefaultSessionState(): SessionState {
    return {
      messages: [],
      context: {},
      preferences: {},
      lastActivity: new Date().toISOString()
    };
  }
}
```

### Safety Middleware

The Safety Middleware validates all CoPilot requests for security and safety.

#### Interface

```typescript
interface SafetyMiddleware {
  validateRequest(request: AgentTask): Promise<SafetyValidationResult>;
}
```

#### Implementation

```typescript
class SafetyMiddlewareImpl implements SafetyMiddleware {
  private contentSafetyService: ContentSafetyService;
  private authorizationService: AuthorizationService;

  constructor(
    contentSafetyService: ContentSafetyService,
    authorizationService: AuthorizationService
  ) {
    this.contentSafetyService = contentSafetyService;
    this.authorizationService = authorizationService;
  }

  async validateRequest(request: AgentTask): Promise<SafetyValidationResult> {
    // Check content safety
    const contentSafetyResult = await this.contentSafetyService.checkContent(request);
    if (!contentSafetyResult.isSafe) {
      return {
        isValid: false,
        reason: `Content safety check failed: ${contentSafetyResult.reason}`
      };
    }
    
    // Check authorization
    const authorizationResult = await this.authorizationService.checkAuthorization(request);
    if (!authorizationResult.isAuthorized) {
      return {
        isValid: false,
        reason: `Authorization check failed: ${authorizationResult.reason}`
      };
    }
    
    return {
      isValid: true
    };
  }
}
```

## Extension Development

### Extension Architecture

CoPilot extensions are modular components that extend the functionality of CoPilot. They follow a well-defined architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Extension                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────┐    │
│  │Extension Manifest│  │Extension Code  │  │Assets │    │
│  │                 │  │                 │  │       │    │
│  │• ID            │  │• Main Module   │  │• Icons│    │
│  │• Name          │  │• UI Components │  │• CSS  │    │
│  │• Version       │  │• API Handlers  │  │• HTML │    │
│  │• Dependencies  │  │• Hooks         │  │       │    │
│  └─────────────────┘  └─────────────────┘  └───────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Extension Manifest

Every extension must include a manifest file (`extension.json`) that describes the extension:

```json
{
  "id": "com.example.my-extension",
  "name": "My Extension",
  "version": "1.0.0",
  "description": "A brief description of my extension",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "license": "MIT",
  "main": "dist/index.js",
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2"
  },
  "devDependencies": {
    "@types/react": "^17.0.0",
    "@types/react-dom": "^17.0.0",
    "typescript": "^4.2.0"
  },
  "contributes": {
    "commands": [
      {
        "command": "my-extension.helloWorld",
        "title": "Hello World",
        "category": "My Extension"
      }
    ],
    "menus": {
      "editor/context": [
        {
          "command": "my-extension.helloWorld",
          "when": "editorHasSelection"
        }
      ]
    },
    "ui": {
      "components": [
        {
          "id": "my-component",
          "name": "My Component",
          "path": "components/MyComponent",
          "location": "sidebar"
        }
      ]
    }
  }
}
```

### Extension API

CoPilot provides a comprehensive API for extensions:

#### Core API

```typescript
// Core API for basic extension functionality
interface CoPilotAPI {
  // Extension lifecycle
  activate(context: ExtensionContext): Promise<void>;
  deactivate(): Promise<void>;
  
  // UI registration
  registerComponent(component: UIComponent): void;
  registerCommand(command: Command): void;
  
  // Event handling
  onEvent(event: string, callback: Function): Disposable;
  emitEvent(event: string, data: any): void;
  
  // Configuration
  getConfiguration(key: string): any;
  updateConfiguration(key: string, value: any): void;
}
```

#### UI API

```typescript
// UI API for creating user interface components
interface UIAPI {
  // Component registration
  registerComponent(component: UIComponent): void;
  registerView(view: View): void;
  
  // UI manipulation
  showView(viewId: string): void;
  hideView(viewId: string): void;
  
  // Dialogs and notifications
  showInformationMessage(message: string): void;
  showWarningMessage(message: string): void;
  showErrorMessage(message: string): void;
  showQuickPick(items: string[], options: QuickPickOptions): Promise<string>;
  showInputBox(options: InputBoxOptions): Promise<string>;
}
```

#### Agent API

```typescript
// Agent API for interacting with agents
interface AgentAPI {
  // Agent interaction
  sendMessage(agentId: string, message: string): Promise<string>;
  createTask(agentId: string, task: Task): Promise<string>;
  getTaskStatus(taskId: string): Promise<TaskStatus>;
  
  // Agent management
  listAgents(): Promise<Agent[]>;
  getAgent(agentId: string): Promise<Agent>;
  registerAgent(agent: Agent): Promise<void>;
}
```

### Creating a Simple Extension

Here's how to create a simple "Hello World" extension:

#### Project Structure

```
my-extension/
├── src/
│   ├── extension.ts          # Main extension file
│   ├── components/
│   │   └── HelloComponent.tsx  # UI component
│   └── commands/
│       └── helloCommand.ts   # Command handler
├── extension.json            # Extension manifest
├── package.json             # Node.js package file
├── tsconfig.json            # TypeScript configuration
└── README.md               # Extension documentation
```

#### Main Extension File

```typescript
// src/extension.ts
import * as copilot from '@copilot/api';
import { HelloComponent } from './components/HelloComponent';
import { helloCommand } from './commands/helloCommand';

export async function activate(context: copilot.ExtensionContext) {
  console.log('Hello World extension is now active!');
  
  // Register UI component
  copilot.ui.registerComponent({
    id: 'hello-component',
    name: 'Hello Component',
    component: HelloComponent,
    location: 'sidebar'
  });
  
  // Register command
  copilot.registerCommand({
    id: 'hello-command',
    name: 'Say Hello',
    callback: helloCommand
  });
}

export function deactivate() {
  console.log('Hello World extension is now deactivated');
}
```

#### UI Component

```typescript
// src/components/HelloComponent.tsx
import * as React from 'react';
import { useCopilot } from '@copilot/react';

export const HelloComponent: React.FC = () => {
  const [message, setMessage] = React.useState('Hello, World!');
  const copilot = useCopilot();
  
  const handleClick = () => {
    copilot.ui.showInformationMessage('Button clicked!');
    setMessage('Hello, CoPilot!');
  };
  
  return (
    <div className="hello-component">
      <h1>{message}</h1>
      <button onClick={handleClick}>Click Me</button>
    </div>
  );
};
```

#### Command Handler

```typescript
// src/commands/helloCommand.ts
import * as copilot from '@copilot/api';

export const helloCommand = async () => {
  const name = await copilot.ui.showInputBox({
    prompt: 'Enter your name',
    placeHolder: 'John Doe'
  });
  
  if (name) {
    copilot.ui.showInformationMessage(`Hello, ${name}!`);
  }
};
```

#### Extension Manifest

```json
{
  "id": "com.example.hello-world",
  "name": "Hello World",
  "version": "1.0.0",
  "description": "A simple Hello World extension for CoPilot",
  "main": "dist/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "hello-command",
        "title": "Say Hello",
        "category": "Hello World"
      }
    ],
    "ui": {
      "components": [
        {
          "id": "hello-component",
          "name": "Hello Component",
          "path": "components/HelloComponent",
          "location": "sidebar"
        }
      ]
    }
  }
}
```

#### Package.json

```json
{
  "name": "hello-world-extension",
  "version": "1.0.0",
  "description": "A simple Hello World extension for CoPilot",
  "main": "dist/extension.js",
  "scripts": {
    "build": "tsc",
    "watch": "tsc --watch"
  },
  "devDependencies": {
    "@copilot/api": "^1.0.0",
    "@copilot/react": "^1.0.0",
    "@types/react": "^17.0.0",
    "@types/react-dom": "^17.0.0",
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "typescript": "^4.2.0"
  }
}
```

#### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["es6", "dom"],
    "module": "commonjs",
    "moduleResolution": "node",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### Extension Testing

Testing is an important part of extension development. Here's how to set up tests for your extension:

#### Unit Testing

```typescript
// src/extension.test.ts
import { activate, deactivate } from './extension';
import * as copilot from '@copilot/api';

// Mock the CoPilot API
jest.mock('@copilot/api', () => ({
  ui: {
    registerComponent: jest.fn(),
    registerCommand: jest.fn()
  },
  registerCommand: jest.fn()
}));

describe('Hello World Extension', () => {
  let mockContext: any;

  beforeEach(() => {
    mockContext = {
      subscriptions: []
    };
    
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  it('should register a UI component on activation', async () => {
    await activate(mockContext);
    
    expect(copilot.ui.registerComponent).toHaveBeenCalledWith({
      id: 'hello-component',
      name: 'Hello Component',
      component: expect.any(Function),
      location: 'sidebar'
    });
  });

  it('should register a command on activation', async () => {
    await activate(mockContext);
    
    expect(copilot.registerCommand).toHaveBeenCalledWith({
      id: 'hello-command',
      name: 'Say Hello',
      callback: expect.any(Function)
    });
  });

  it('should log activation message', async () => {
    const consoleSpy = jest.spyOn(console, 'log');
    
    await activate(mockContext);
    
    expect(consoleSpy).toHaveBeenCalledWith('Hello World extension is now active!');
    
    consoleSpy.mockRestore();
  });

  it('should log deactivation message', () => {
    const consoleSpy = jest.spyOn(console, 'log');
    
    deactivate();
    
    expect(consoleSpy).toHaveBeenCalledWith('Hello World extension is now deactivated');
    
    consoleSpy.mockRestore();
  });
});
```

#### Component Testing

```typescript
// src/components/HelloComponent.test.tsx
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { HelloComponent } from './HelloComponent';

// Mock the useCopilot hook
jest.mock('@copilot/react', () => ({
  useCopilot: () => ({
    ui: {
      showInformationMessage: jest.fn()
    }
  })
}));

describe('HelloComponent', () => {
  it('should render with default message', () => {
    render(<HelloComponent />);
    
    expect(screen.getByText('Hello, World!')).toBeInTheDocument();
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('should change message when button is clicked', () => {
    const { useCopilot } = require('@copilot/react');
    const mockShowInformationMessage = jest.fn();
    
    useCopilot.mockReturnValue({
      ui: {
        showInformationMessage: mockShowInformationMessage
      }
    });
    
    render(<HelloComponent />);
    
    fireEvent.click(screen.getByText('Click Me'));
    
    expect(screen.getByText('Hello, CoPilot!')).toBeInTheDocument();
    expect(mockShowInformationMessage).toHaveBeenCalledWith('Button clicked!');
  });
});
```

#### Command Testing

```typescript
// src/commands/helloCommand.test.ts
import { helloCommand } from './helloCommand';
import * as copilot from '@copilot/api';

// Mock the CoPilot API
jest.mock('@copilot/api', () => ({
  ui: {
    showInputBox: jest.fn(),
    showInformationMessage: jest.fn()
  }
}));

describe('helloCommand', () => {
  it('should show input box', async () => {
    await helloCommand();
    
    expect(copilot.ui.showInputBox).toHaveBeenCalledWith({
      prompt: 'Enter your name',
      placeHolder: 'John Doe'
    });
  });

  it('should show information message with name', async () => {
    const mockName = 'Test User';
    
    (copilot.ui.showInputBox as jest.Mock).mockResolvedValue(mockName);
    
    await helloCommand();
    
    expect(copilot.ui.showInformationMessage).toHaveBeenCalledWith(`Hello, ${mockName}!`);
  });

  it('should not show information message if name is empty', async () => {
    (copilot.ui.showInputBox as jest.Mock).mockResolvedValue('');
    
    await helloCommand();
    
    expect(copilot.ui.showInformationMessage).not.toHaveBeenCalled();
  });
});
```

### Extension Packaging and Distribution

Once your extension is complete, you'll want to package and distribute it:

#### Building the Extension

```bash
# Install dependencies
npm install

# Build the extension
npm run build
```

#### Packaging the Extension

```bash
# Package the extension
npx @copilot/extension-package
```

This will create a `.vsix` file in the `dist` directory.

#### Publishing the Extension

```bash
# Publish to the CoPilot Extension Marketplace
npx @copilot/extension-publish --package-path dist/my-extension-1.0.0.vsix
```

## Customization

### Theme Customization

CoPilot allows extensive customization of themes and appearance.

#### Creating a Custom Theme

```typescript
// themes/my-theme.ts
import { Theme } from '@copilot/theme';

export const myTheme: Theme = {
  id: 'my-theme',
  name: 'My Custom Theme',
  colors: {
    primary: '#3f51b5',
    secondary: '#f50057',
    background: '#ffffff',
    surface: '#f5f5f5',
    text: '#212121',
    textSecondary: '#757575',
    divider: '#bdbdbd',
    error: '#f44336',
    warning: '#ff9800',
    success: '#4caf50',
    info: '#2196f3'
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      bold: 700,
      black: 900
    }
  },
  spacing: {
    unit: 8,
    px: '1px',
    0: '0',
    1: '0.25rem',
    2: '0.5rem',
    3: '0.75rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    8: '2rem',
    10: '2.5rem',
    12: '3rem',
    16: '4rem',
    20: '5rem',
    24: '6rem'
  },
  borderRadius: {
    none: '0',
    sm: '0.125rem',
    base: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    none: 'none'
  }
};
```

#### Registering a Custom Theme

```typescript
// src/extension.ts
import * as copilot from '@copilot/api';
import { myTheme } from '../themes/my-theme';

export async function activate(context: copilot.ExtensionContext) {
  // Register the custom theme
  copilot.theme.registerTheme(myTheme);
}
```

### UI Component Customization

You can customize existing UI components or create new ones:

#### Customizing Existing Components

```typescript
// src/components/CustomChatComponent.tsx
import * as React from 'react';
import { ChatComponent, ChatComponentProps } from '@copilot/components';
import { styled } from '@copilot/styled';

// Create a styled version of the ChatComponent
const CustomChatComponent = styled(ChatComponent)`
  background-color: ${props => props.theme.colors.background};
  border-radius: ${props => props.theme.borderRadius.lg};
  box-shadow: ${props => props.theme.shadows.lg};
  padding: ${props => props.theme.spacing[4]};
  
  .message {
    margin-bottom: ${props => props.theme.spacing[3]};
    
    &.user {
      background-color: ${props => props.theme.colors.primary};
      color: white;
      border-radius: ${props => props.theme.borderRadius.lg};
      padding: ${props => props.theme.spacing[3]};
      margin-left: auto;
      max-width: 70%;
    }
    
    &.agent {
      background-color: ${props => props.theme.colors.surface};
      color: ${props => props.theme.colors.text};
      border-radius: ${props => props.theme.borderRadius.lg};
      padding: ${props => props.theme.spacing[3]};
      max-width: 70%;
    }
  }
`;

export default CustomChatComponent;
```

#### Creating Custom Components

```typescript
// src/components/CustomDashboard.tsx
import * as React from 'react';
import { useCopilot, styled } from '@copilot/react';

const DashboardContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing[4]};
  padding: ${props => props.theme.spacing[4]};
`;

const DashboardCard = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border-radius: ${props => props.theme.borderRadius.lg};
  box-shadow: ${props => props.theme.shadows.base};
  padding: ${props => props.theme.spacing[4]};
  
  h2 {
    color: ${props => props.theme.colors.primary};
    margin-top: 0;
    margin-bottom: ${props => props.theme.spacing[3]};
  }
`;

export const CustomDashboard: React.FC = () => {
  const copilot = useCopilot();
  
  return (
    <DashboardContainer>
      <DashboardCard>
        <h2>Active Conversations</h2>
        <p>You have 3 active conversations.</p>
      </DashboardCard>
      
      <DashboardCard>
        <h2>Pending Tasks</h2>
        <p>You have 5 pending tasks.</p>
      </DashboardCard>
      
      <DashboardCard>
        <h2>Memory Usage</h2>
        <p>You're using 45% of your memory quota.</p>
      </DashboardCard>
    </DashboardContainer>
  );
};
```

### Behavior Customization

You can customize CoPilot's behavior through configuration:

#### Custom Configuration

```typescript
// src/configuration.ts
import { Configuration } from '@copilot/api';

export const customConfiguration: Configuration = {
  // General settings
  general: {
    autoSave: true,
    autoSaveInterval: 30000, // 30 seconds
    telemetryEnabled: false,
    updateCheckEnabled: true,
    updateCheckInterval: 86400000 // 24 hours
  },
  
  // UI settings
  ui: {
    theme: 'my-theme',
    fontSize: 'base',
    fontFamily: 'Roboto, sans-serif',
    sidebar: {
      position: 'left',
      width: 300,
      collapsible: true,
      collapsed: false
    },
    editor: {
      wordWrap: true,
      minimap: false,
      lineNumbers: true,
      renderWhitespace: 'boundary'
    }
  },
  
  // Agent settings
  agents: {
    defaultAgent: 'general-purpose',
    autoSelect: true,
    responseLength: 'medium',
    responseStyle: 'balanced'
  },
  
  // Memory settings
  memory: {
    retentionPeriod: 2592000000, // 30 days
    maxSize: 104857600, // 100MB
    autoCleanup: true,
    cleanupInterval: 604800000 // 7 days
  },
  
  // Security settings
  security: {
    contentFiltering: true,
    encryptionEnabled: true,
    anonymizeData: true,
    logLevel: 'error'
  }
};
```

#### Registering Custom Configuration

```typescript
// src/extension.ts
import * as copilot from '@copilot/api';
import { customConfiguration } from './configuration';

export async function activate(context: copilot.ExtensionContext) {
  // Register the custom configuration
  copilot.configuration.registerConfiguration(customConfiguration);
}
```

## Testing

### Testing Strategies

CoPilot supports several testing strategies to ensure code quality and reliability:

#### Unit Testing

Unit tests focus on individual components in isolation:

```typescript
// src/components/ChatComponent.test.tsx
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatComponent } from './ChatComponent';

describe('ChatComponent', () => {
  const mockSendMessage = jest.fn();
  const mockMessages = [
    { id: '1', content: 'Hello', sender: 'user', timestamp: new Date() },
    { id: '2', content: 'Hi there!', sender: 'agent', timestamp: new Date() }
  ];

  beforeEach(() => {
    mockSendMessage.mockClear();
  });

  it('should render messages correctly', () => {
    render(
      <ChatComponent 
        messages={mockMessages} 
        onSendMessage={mockSendMessage} 
      />
    );

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('should call onSendMessage when form is submitted', () => {
    render(
      <ChatComponent 
        messages={mockMessages} 
        onSendMessage={mockSendMessage} 
      />
    );

    const input = screen.getByRole('textbox');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'New message' } });
    fireEvent.submit(form);

    expect(mockSendMessage).toHaveBeenCalledWith('New message');
  });

  it('should clear input after sending message', () => {
    render(
      <ChatComponent 
        messages={mockMessages} 
        onSendMessage={mockSendMessage} 
      />
    );

    const input = screen.getByRole('textbox');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'New message' } });
    fireEvent.submit(form);

    expect(input).toHaveValue('');
  });
});
```

#### Integration Testing

Integration tests verify that components work together correctly:

```typescript
// src/integration/ChatIntegration.test.tsx
import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from '../components/ChatInterface';
import { AgentUIService } from '../services/AgentUIService';

// Mock the AgentUIService
jest.mock('../services/AgentUIService');

describe('ChatInterface Integration', () => {
  const mockAgentUIService = new AgentUIService() as jest.Mocked<AgentUIService>;
  
  beforeEach(() => {
    mockAgentUIService.sendMessage.mockClear();
  });

  it('should send message and display response', async () => {
    // Mock the service response
    mockAgentUIService.sendMessage.mockResolvedValue({
      content: 'Mock response',
      timestamp: new Date()
    });

    render(<ChatInterface agentUIService={mockAgentUIService} />);

    // Send a message
    const input = screen.getByRole('textbox');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.submit(form);

    // Verify the service was called
    expect(mockAgentUIService.sendMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        content: 'Hello'
      })
    );

    // Wait for and verify the response is displayed
    await waitFor(() => {
      expect(screen.getByText('Mock response')).toBeInTheDocument();
    });
  });

  it('should handle service errors gracefully', async () => {
    // Mock the service to throw an error
    mockAgentUIService.sendMessage.mockRejectedValue(new Error('Service error'));

    render(<ChatInterface agentUIService={mockAgentUIService} />);

    // Send a message
    const input = screen.getByRole('textbox');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.submit(form);

    // Wait for and verify the error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Failed to send message/)).toBeInTheDocument();
    });
  });
});
```

#### End-to-End Testing

End-to-end tests simulate real user scenarios:

```typescript
// e2e/chat.spec.ts
import { test, expect } from '@playwright/test';

test('user can have a conversation with an agent', async ({ page }) => {
  // Navigate to the chat page
  await page.goto('/chat');

  // Wait for the chat interface to load
  await page.waitForSelector('.chat-interface');

  // Send a message
  await page.fill('.chat-input', 'Hello, agent!');
  await page.click('.send-button');

  // Wait for the response
  await page.waitForSelector('.agent-message');

  // Verify the response is displayed
  const agentMessage = await page.textContent('.agent-message');
  expect(agentMessage).toBeTruthy();
});

test('user can create and monitor a task', async ({ page }) => {
  // Navigate to the tasks page
  await page.goto('/tasks');

  // Wait for the tasks interface to load
  await page.waitForSelector('.tasks-interface');

  // Create a new task
  await page.click('.new-task-button');
  await page.fill('.task-title-input', 'Test Task');
  await page.fill('.task-description-input', 'This is a test task');
  await page.click('.create-task-button');

  // Wait for the task to be created
  await page.waitForSelector('.task-card');

  // Verify the task is displayed
  const taskTitle = await page.textContent('.task-title');
  expect(taskTitle).toBe('Test Task');

  // Monitor the task progress
  await page.click('.task-card');
  
  // Wait for the task details to load
  await page.waitForSelector('.task-details');
  
  // Verify the task progress is displayed
  const progressIndicator = await page.$('.progress-indicator');
  expect(progressIndicator).toBeTruthy();
});
```

### Testing Tools

CoPilot uses several testing tools:

#### Jest

Jest is used for unit and integration tests:

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.11.0",
    "@testing-library/react": "^11.2.0",
    "@testing-library/user-event": "^12.8.0",
    "@types/jest": "^26.0.20",
    "jest": "^26.6.0",
    "ts-jest": "^26.5.0"
  }
}
```

#### Jest Configuration

```json
// jest.config.json
{
  "preset": "ts-jest",
  "testEnvironment": "jsdom",
  "roots": ["<rootDir>/src"],
  "testMatch": [
    "**/__tests__/**/*.ts?(x)",
    "**/?(*.)+(spec|test).ts?(x)"
  ],
  "transform": {
    "^.+\\.tsx?$": "ts-jest"
  },
  "moduleNameMapping": {
    "^@copilot/(.*)$": "<rootDir>/src/$1"
  },
  "collectCoverageFrom": [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/index.ts"
  ],
  "coverageReporters": ["text", "lcov", "html"],
  "setupFilesAfterEnv": ["<rootDir>/src/setupTests.ts"]
}
```

#### React Testing Library

React Testing Library is used for testing React components:

```typescript
// src/setupTests.ts
import '@testing-library/jest-dom';
```

#### Playwright

Playwright is used for end-to-end testing:

```json
// package.json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug"
  },
  "devDependencies": {
    "@playwright/test": "^1.10.0"
  }
}
```

#### Playwright Configuration

```typescript
// playwright.config.ts
import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './e2e',
  timeout: 30000,
  expect: {
    timeout: 5000
  },
  use: {
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 720 },
    video: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  reporter: [['html'], ['list']],
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' }
    },
    {
      name: 'firefox',
      use: { browserName: 'firefox' }
    },
    {
      name: 'webkit',
      use: { browserName: 'webkit' }
    }
  ]
};

export default config;
```

### Test Coverage

CoPilot aims for high test coverage:

#### Coverage Goals

- **Unit Tests**: 80% coverage minimum
- **Integration Tests**: 70% coverage minimum
- **End-to-End Tests**: Cover all critical user flows

#### Coverage Reports

Coverage reports are generated in HTML format and can be found in the `coverage` directory after running:

```bash
npm run test:coverage
```

## Performance Optimization

### Frontend Optimization

Optimizing the frontend is crucial for a smooth user experience:

#### Code Splitting

Code splitting allows loading only the code that's needed:

```typescript
// src/App.tsx
import * as React from 'react';
import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load components
const ChatInterface = lazy(() => import('./components/ChatInterface'));
const TaskInterface = lazy(() => import('./components/TaskInterface'));
const MemoryInterface = lazy(() => import('./components/MemoryInterface'));
const AgentInterface = lazy(() => import('./components/AgentInterface'));

const App: React.FC = () => {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/chat" element={<ChatInterface />} />
          <Route path="/tasks" element={<TaskInterface />} />
          <Route path="/memory" element={<MemoryInterface />} />
          <Route path="/agents" element={<AgentInterface />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default App;
```

#### Memoization

Memoization prevents unnecessary re-renders:

```typescript
// src/components/MessageComponent.tsx
import * as React from 'react';
import { memo } from 'react';

interface MessageComponentProps {
  message: {
    id: string;
    content: string;
    sender: 'user' | 'agent';
    timestamp: Date;
  };
}

const MessageComponent: React.FC<MessageComponentProps> = ({ message }) => {
  return (
    <div className={`message ${message.sender}`}>
      <div className="message-content">{message.content}</div>
      <div className="message-timestamp">
        {message.timestamp.toLocaleTimeString()}
      </div>
    </div>
  );
};

// Memoize the component to prevent unnecessary re-renders
export default memo(MessageComponent);
```

#### Virtualization

Virtualization improves performance for long lists:

```typescript
// src/components/MessageList.tsx
import * as React from 'react';
import { FixedSizeList as List } from 'react-window';
import MessageComponent from './MessageComponent';

interface MessageListProps {
  messages: Array<{
    id: string;
    content: string;
    sender: 'user' | 'agent';
    timestamp: Date;
  }>;
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  // Row renderer for virtualized list
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <MessageComponent message={messages[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={messages.length}
      itemSize={80}
      width="100%"
    >
      {Row}
    </List>
  );
};

export default MessageList;
```

#### Image Optimization

Optimize images to reduce load times:

```typescript
// src/components/OptimizedImage.tsx
import * as React from 'react';
import { lazy, Suspense } from 'react';

// Lazy load the image component
const LazyImage = lazy(() => import('react-lazy-load-image-component'));

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({ src, alt, width, height }) => {
  return (
    <Suspense fallback={<div>Loading image...</div>}>
      <LazyImage
        src={src}
        alt={alt}
        width={width}
        height={height}
        effect="blur"
        placeholderSrc="/placeholder.jpg"
      />
    </Suspense>
  );
};

export default OptimizedImage;
```

### Backend Optimization

Optimizing the backend ensures fast and reliable service:

#### Caching

Caching reduces database load and improves response times:

```typescript
// src/services/CacheService.ts
import NodeCache from 'node-cache';

export class CacheService {
  private cache: NodeCache;

  constructor(ttlSeconds: number = 300) {
    this.cache = new NodeCache({
      stdTTL: ttlSeconds,
      checkperiod: ttlSeconds * 0.2,
      useClones: false
    });
  }

  get<T>(key: string): T | undefined {
    return this.cache.get<T>(key);
  }

  set<T>(key: string, value: T, ttl?: number): boolean {
    return this.cache.set<T>(key, value, ttl);
  }

  del(key: string): number {
    return this.cache.del(key);
  }

  flush(): void {
    this.cache.flushAll();
  }

  getStats(): NodeCache.Stats {
    return this.cache.getStats();
  }
}

// Usage example
const cacheService = new CacheService();

export const getCachedData = async (key: string, fetchFunction: () => Promise<any>) => {
  // Try to get from cache first
  const cachedData = cacheService.get(key);
  if (cachedData) {
    return cachedData;
  }

  // If not in cache, fetch and cache the data
  const data = await fetchFunction();
  cacheService.set(key, data);
  
  return data;
};
```

#### Database Optimization

Optimize database queries for better performance:

```typescript
// src/repositories/MessageRepository.ts
import { Database } from '../database/Database';
import { Message } from '../models/Message';

export class MessageRepository {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  async getMessagesBySessionId(sessionId: string, limit: number = 50, offset: number = 0): Promise<Message[]> {
    // Use parameterized query to prevent SQL injection
    const query = `
      SELECT * FROM messages
      WHERE session_id = ?
      ORDER BY timestamp DESC
      LIMIT ? OFFSET ?
    `;
    
    return this.db.all(query, [sessionId, limit, offset]);
  }

  async getMessageCountBySessionId(sessionId: string): Promise<number> {
    const query = `
      SELECT COUNT(*) as count
      FROM messages
      WHERE session_id = ?
    `;
    
    const result = await this.db.get(query, [sessionId]);
    return result.count;
  }

  async createMessage(message: Omit<Message, 'id' | 'timestamp'>): Promise<Message> {
    const query = `
      INSERT INTO messages (session_id, content, sender, timestamp)
      VALUES (?, ?, ?, ?)
      RETURNING *
    `;
    
    const timestamp = new Date().toISOString();
    const result = await this.db.run(query, [
      message.sessionId,
      message.content,
      message.sender,
      timestamp
    ]);
    
    return {
      id: result.lastID,
      sessionId: message.sessionId,
      content: message.content,
      sender: message.sender,
      timestamp
    };
  }
}
```

#### Connection Pooling

Connection pooling improves database performance:

```typescript
// src/database/ConnectionPool.ts
import { createPool, Pool } from 'mysql2/promise';

export class ConnectionPool {
  private pool: Pool;

  constructor(config: {
    host: string;
    user: string;
    password: string;
    database: string;
    port: number;
    connectionLimit: number;
  }) {
    this.pool = createPool({
      host: config.host,
      user: config.user,
      password: config.password,
      database: config.database,
      port: config.port,
      connectionLimit: config.connectionLimit,
      queueLimit: 0,
      multipleStatements: false
    });
  }

  async getConnection() {
    return this.pool.getConnection();
  }

  async query(sql: string, params: any[] = []) {
    const connection = await this.getConnection();
    try {
      const [rows] = await connection.execute(sql, params);
      return rows;
    } finally {
      connection.release();
    }
  }

  async end() {
    return this.pool.end();
  }
}
```

### Performance Monitoring

Monitor performance to identify and fix issues:

#### Frontend Monitoring

```typescript
// src/services/PerformanceService.ts
export class PerformanceService {
  private metrics: Map<string, number[]> = new Map();

  measureTime(name: string, fn: () => Promise<any> | any): any {
    const start = performance.now();
    const result = fn();
    
    const end = () => {
      const duration = performance.now() - start;
      this.recordMetric(name, duration);
    };

    if (result instanceof Promise) {
      return result.then((value) => {
        end();
        return value;
      });
    } else {
      end();
      return result;
    }
  }

  recordMetric(name: string, value: number): void {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    const values = this.metrics.get(name)!;
    values.push(value);
    
    // Keep only the last 100 values
    if (values.length > 100) {
      values.shift();
    }
  }

  getMetricStats(name: string) {
    const values = this.metrics.get(name) || [];
    
    if (values.length === 0) {
      return null;
    }
    
    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((acc, val) => acc + val, 0);
    
    return {
      count: values.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      mean: sum / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)]
    };
  }

  getAllMetrics() {
    const result: Record<string, any> = {};
    
    for (const [name, _] of this.metrics) {
      result[name] = this.getMetricStats(name);
    }
    
    return result;
  }
}

// Usage example
const performanceService = new PerformanceService();

export const withPerformance = (name: string, fn: () => any) => {
  return performanceService.measureTime(name, fn);
};
```

#### Backend Monitoring

```typescript
// src/services/MonitoringService.ts
import { performance } from 'perf_hooks';

export class MonitoringService {
  private metrics: Map<string, number[]> = new Map();
  private timers: Map<string, number> = new Map();

  startTimer(name: string): void {
    this.timers.set(name, performance.now());
  }

  endTimer(name: string): number {
    const start = this.timers.get(name);
    
    if (!start) {
      throw new Error(`No timer found for ${name}`);
    }
    
    const duration = performance.now() - start;
    this.recordMetric(name, duration);
    this.timers.delete(name);
    
    return duration;
  }

  recordMetric(name: string, value: number): void {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    const values = this.metrics.get(name)!;
    values.push(value);
    
    // Keep only the last 1000 values
    if (values.length > 1000) {
      values.shift();
    }
  }

  incrementCounter(name: string, value: number = 1): void {
    this.recordMetric(name, value);
  }

  getMetricStats(name: string) {
    const values = this.metrics.get(name) || [];
    
    if (values.length === 0) {
      return null;
    }
    
    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((acc, val) => acc + val, 0);
    
    return {
      count: values.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      mean: sum / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)]
    };
  }

  getAllMetrics() {
    const result: Record<string, any> = {};
    
    for (const [name, _] of this.metrics) {
      result[name] = this.getMetricStats(name);
    }
    
    return result;
  }

  reset(): void {
    this.metrics.clear();
    this.timers.clear();
  }
}

// Usage example
const monitoringService = new MonitoringService();

// Middleware for Express
export const monitoringMiddleware = (req: any, res: any, next: any) => {
  const start = performance.now();
  
  res.on('finish', () => {
    const duration = performance.now() - start;
    monitoringService.recordMetric(`request.${req.route.path}`, duration);
    monitoringService.incrementCounter(`request.${req.method}.${req.route.path}`);
  });
  
  next();
};
```

## Deployment

### Containerization

Docker containers provide a consistent deployment environment:

#### Dockerfile

```dockerfile
# Dockerfile
FROM node:16-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  copilot-frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - API_URL=http://copilot-backend:8000
    depends_on:
      - copilot-backend
    networks:
      - copilot-network

  copilot-backend:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:password@postgres:5432/copilot
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - copilot-network

  postgres:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=copilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - copilot-network

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    networks:
      - copilot-network

volumes:
  postgres_data:
  redis_data:

networks:
  copilot-network:
    driver: bridge
```

### CI/CD Pipeline

GitHub Actions provides a CI/CD pipeline:

```yaml
# .github/workflows/deploy.yml
name: Deploy CoPilot

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v2
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linting
        run: npm run lint
      
      - name: Run tests
        run: npm run test:all
      
      - name: Build application
        run: npm run build
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1
      
      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push frontend
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: yourorg/copilot-frontend:latest
          cache-from: type=registry,ref=yourorg/copilot-frontend:buildcache
          cache-to: type=registry,ref=yourorg/copilot-frontend:buildcache,mode=max
      
      - name: Build and push backend
        uses: docker/build-push-action@v2
        with:
          context: ./server
          push: true
          tags: yourorg/copilot-backend:latest
          cache-from: type=registry,ref=yourorg/copilot-backend:buildcache
          cache-to: type=registry,ref=yourorg/copilot-backend:buildcache,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_KEY }}
          script: |
            cd /opt/copilot
            docker-compose pull
            docker-compose up -d
```

### Environment Configuration

Configure different environments:

#### Development Environment

```bash
# .env.development
NODE_ENV=development
API_URL=http://localhost:8000
DATABASE_URL=postgresql://user:password@localhost:5432/copilot_dev
REDIS_URL=redis://localhost:6379
LOG_LEVEL=debug
```

#### Production Environment

```bash
# .env.production
NODE_ENV=production
API_URL=https://api.copilot.example.com
DATABASE_URL=postgresql://user:${{DATABASE_PASSWORD}}@postgres:5432/copilot_prod
REDIS_URL=redis://redis:6379
LOG_LEVEL=info
```

#### Staging Environment

```bash
# .env.staging
NODE_ENV=staging
API_URL=https://staging-api.copilot.example.com
DATABASE_URL=postgresql://user:${{DATABASE_PASSWORD}}@postgres:5432/copilot_staging
REDIS_URL=redis://redis:6379
LOG_LEVEL=debug
```

### Monitoring and Logging

Monitor and log your deployed application:

#### Logging Configuration

```typescript
// src/logger.ts
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'copilot' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// If we're not in production, log to the console as well
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

export default logger;
```

#### Health Checks

```typescript
// src/health.ts
import express from 'express';
import { Database } from './database/Database';
import { Redis } from './redis/Redis';

export const createHealthRouter = (db: Database, redis: Redis) => {
  const router = express.Router();
  
  router.get('/health', async (req, res) => {
    try {
      // Check database connection
      await db.query('SELECT 1');
      
      // Check Redis connection
      await redis.ping();
      
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        checks: {
          database: 'healthy',
          redis: 'healthy'
        }
      });
    } catch (error) {
      res.status(503).json({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        error: error.message,
        checks: {
          database: error.message.includes('database') ? 'unhealthy' : 'healthy',
          redis: error.message.includes('redis') ? 'unhealthy' : 'healthy'
        }
      });
    }
  });
  
  router.get('/ready', async (req, res) => {
    // More comprehensive check for readiness
    try {
      // Check database with a more complex query
      await db.query('SELECT COUNT(*) FROM users');
      
      // Check Redis with a more complex operation
      await redis.set('health-check', 'ok', 'EX', 5);
      await redis.get('health-check');
      
      res.status(200).json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      });
    } catch (error) {
      res.status(503).json({
        status: 'not ready',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        error: error.message
      });
    }
  });
  
  return router;
};
```

## Best Practices

### Code Quality

Maintain high code quality with these practices:

#### Code Style

Use a consistent code style:

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "react", "react-hooks"],
  "rules": {
    "react/prop-types": "off",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

#### Code Reviews

Conduct thorough code reviews:

1. **Automated Checks**: All code must pass automated checks (linting, tests)
2. **Small Changes**: Keep pull requests small and focused
3. **Clear Description**: Provide a clear description of changes
4. **Test Coverage**: Ensure adequate test coverage for new code
5. **Documentation**: Update documentation for any user-facing changes

#### Error Handling

Handle errors gracefully:

```typescript
// src/utils/errors.ts
export class CoPilotError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'CoPilotError';
  }
}

export class ValidationError extends CoPilotError {
  constructor(message: string, details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
  }
}

export class NotFoundError extends CoPilotError {
  constructor(message: string, details?: any) {
    super(message, 'NOT_FOUND', 404, details);
  }
}

export class UnauthorizedError extends CoPilotError {
  constructor(message: string, details?: any) {
    super(message, 'UNAUTHORIZED', 401, details);
  }
}

// Error handling middleware
export const errorHandler = (err: any, req: any, res: any, next: any) => {
  logger.error('Error occurred', { error: err });
  
  if (err instanceof CoPilotError) {
    return res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }
  
  // Default error
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
};
```

### Security

Follow security best practices:

#### Input Validation

Validate all user input:

```typescript
// src/utils/validation.ts
import { z } from 'zod';

export const MessageSchema = z.object({
  content: z.string().min(1).max(10000),
  sessionId: z.string().uuid(),
  sender: z.enum(['user', 'agent'])
});

export const TaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(5000),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  dueDate: z.date().optional(),
  sessionId: z.string().uuid()
});

export const validate = <T>(schema: z.ZodSchema<T>, data: any): T => {
  const result = schema.safeParse(data);
  
  if (!result.success) {
    throw new ValidationError('Invalid input', result.error);
  }
  
  return result.data;
};
```

#### Authentication and Authorization

Implement proper authentication and authorization:

```typescript
// src/auth/AuthService.ts
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import { Database } from '../database/Database';

export class AuthService {
  private db: Database;
  private jwtSecret: string;

  constructor(db: Database, jwtSecret: string) {
    this.db = db;
    this.jwtSecret = jwtSecret;
  }

  async authenticate(username: string, password: string): Promise<string> {
    // Get user from database
    const user = await this.db.get(
      'SELECT id, username, password_hash FROM users WHERE username = ?',
      [username]
    );

    if (!user) {
      throw new UnauthorizedError('Invalid username or password');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password_hash);

    if (!isPasswordValid) {
      throw new UnauthorizedError('Invalid username or password');
    }

    // Generate JWT
    const token = jwt.sign(
      { userId: user.id, username: user.username },
      this.jwtSecret,
      { expiresIn: '24h' }
    );

    return token;
  }

  verifyToken(token: string): { userId: string; username: string } {
    try {
      const decoded = jwt.verify(token, this.jwtSecret) as any;
      return {
        userId: decoded.userId,
        username: decoded.username
      };
    } catch (error) {
      throw new UnauthorizedError('Invalid token');
    }
  }
}

// Authentication middleware
export const authenticate = (authService: AuthService) => {
  return async (req: any, res: any, next: any) => {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new UnauthorizedError('Missing or invalid authorization header');
    }

    const token = authHeader.substring(7);
    const user = authService.verifyToken(token);

    req.user = user;
    next();
  };
};

// Authorization middleware
export const authorize = (roles: string[]) => {
  return (req: any, res: any, next: any) => {
    if (!req.user) {
      throw new UnauthorizedError('User not authenticated');
    }

    // Check if user has required role
    // This is a simplified example - in a real application, you would
    // check the user's roles against the required roles
    next();
  };
};
```

### Performance

Follow performance best practices:

#### Efficient Data Fetching

Fetch data efficiently:

```typescript
// src/services/DataService.ts
import { Database } from '../database/Database';

export class DataService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  async getMessagesWithPagination(sessionId: string, page: number, pageSize: number) {
    const offset = (page - 1) * pageSize;
    
    // Use a single query with LIMIT and OFFSET for pagination
    const messages = await this.db.all(
      `
        SELECT * FROM messages
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
      `,
      [sessionId, pageSize, offset]
    );
    
    // Get total count for pagination metadata
    const totalCountResult = await this.db.get(
      'SELECT COUNT(*) as count FROM messages WHERE session_id = ?',
      [sessionId]
    );
    
    const totalCount = totalCountResult.count;
    
    return {
      messages,
      pagination: {
        page,
        pageSize,
        totalCount,
        totalPages: Math.ceil(totalCount / pageSize)
      }
    };
  }

  async getMessagesWithUsers(sessionId: string) {
    // Use a JOIN to get messages with user information in a single query
    return await this.db.all(
      `
        SELECT 
          m.id,
          m.content,
          m.sender,
          m.timestamp,
          u.username,
          u.avatar_url
        FROM messages m
        LEFT JOIN users u ON m.sender_id = u.id
        WHERE m.session_id = ?
        ORDER BY m.timestamp DESC
      `,
      [sessionId]
    );
  }
}
```

#### Efficient State Management

Manage state efficiently:

```typescript
// src/stores/MessageStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Message } from '../types';

interface MessageState {
  messages: Message[];
  loading: boolean;
  error: string | null;
  fetchMessages: (sessionId: string) => Promise<void>;
  sendMessage: (content: string, sessionId: string) => Promise<void>;
  clearMessages: () => void;
}

export const useMessageStore = create<MessageState>()(
  devtools(
    persist(
      (set, get) => ({
        messages: [],
        loading: false,
        error: null,
        
        fetchMessages: async (sessionId: string) => {
          set({ loading: true, error: null });
          
          try {
            const response = await fetch(`/api/messages?sessionId=${sessionId}`);
            const messages = await response.json();
            
            set({ messages, loading: false });
          } catch (error) {
            set({ error: error.message, loading: false });
          }
        },
        
        sendMessage: async (content: string, sessionId: string) => {
          const { messages } = get();
          
          // Optimistically add the message to the state
          const optimisticMessage: Message = {
            id: `temp-${Date.now()}`,
            content,
            sender: 'user',
            timestamp: new Date().toISOString(),
            sessionId
          };
          
          set({ messages: [...messages, optimisticMessage] });
          
          try {
            const response = await fetch('/api/messages', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ content, sessionId })
            });
            
            if (!response.ok) {
              throw new Error('Failed to send message');
            }
            
            const savedMessage = await response.json();
            
            // Replace the optimistic message with the saved one
            set({
              messages: messages.map(msg => 
                msg.id === optimisticMessage.id ? savedMessage : msg
              )
            });
          } catch (error) {
            // Remove the optimistic message if sending failed
            set({
              messages: messages.filter(msg => msg.id !== optimisticMessage.id),
              error: error.message
            });
          }
        },
        
        clearMessages: () => set({ messages: [] })
      }),
      {
        name: 'message-storage',
        getStorage: () => sessionStorage
      }
    )
  )
);
```

### Documentation

Maintain comprehensive documentation:

#### Code Documentation

Document your code with JSDoc:

```typescript
// src/services/AgentService.ts
/**
 * Service for interacting with agents.
 * 
 * This service provides methods for sending messages to agents,
 * creating tasks, and monitoring task progress.
 */
export class AgentService {
  private agentUIService: AgentUIService;
  
  /**
   * Creates a new AgentService instance.
   * 
   * @param agentUIService - The Agent UI Service to use for agent interactions
   */
  constructor(agentUIService: AgentUIService) {
    this.agentUIService = agentUIService;
  }
  
  /**
   * Sends a message to an agent.
   * 
   * @param message - The message to send
   * @param sessionId - The session ID
   * @param agentId - The ID of the agent to send the message to
   * @returns A promise that resolves to the agent's response
   * @throws {ValidationError} If the message is invalid
   * @throws {UnauthorizedError} If the user is not authorized
   * @throws {NotFoundError} If the agent is not found
   */
  async sendMessage(
    message: string,
    sessionId: string,
    agentId?: string
  ): Promise<SendMessageResponse> {
    // Validate input
    if (!message || message.trim().length === 0) {
      throw new ValidationError('Message cannot be empty');
    }
    
    if (!sessionId) {
      throw new ValidationError('Session ID is required');
    }
    
    // Create request
    const request: SendMessageRequest = {
      content: message,
      sessionId,
      agentId
    };
    
    // Send message
    return this.agentUIService.sendMessage(request);
  }
  
  /**
   * Creates a new task for an agent.
   * 
   * @param title - The title of the task
   * @param description - The description of the task
   * @param sessionId - The session ID
   * @param agentId - The ID of the agent to assign the task to
   * @param priority - The priority of the task
   * @param dueDate - The due date of the task
   * @returns A promise that resolves to the created task
   * @throws {ValidationError} If the task data is invalid
   * @throws {UnauthorizedError} If the user is not authorized
   */
  async createTask(
    title: string,
    description: string,
    sessionId: string,
    agentId?: string,
    priority?: 'low' | 'medium' | 'high' | 'critical',
    dueDate?: Date
  ): Promise<CreateDeepTaskResponse> {
    // Validate input
    if (!title || title.trim().length === 0) {
      throw new ValidationError('Title cannot be empty');
    }
    
    if (!sessionId) {
      throw new ValidationError('Session ID is required');
    }
    
    // Create request
    const request: CreateDeepTaskRequest = {
      title,
      description,
      sessionId,
      agentId,
      priority,
      dueDate
    };
    
    // Create task
    return this.agentUIService.createDeepTask(request);
  }
  
  /**
   * Gets the progress of a task.
   * 
   * @param taskId - The ID of the task
   * @returns A promise that resolves to the task progress
   * @throws {ValidationError} If the task ID is invalid
   * @throws {NotFoundError} If the task is not found
   */
  async getTaskProgress(taskId: string): Promise<GetTaskProgressResponse> {
    // Validate input
    if (!taskId) {
      throw new ValidationError('Task ID is required');
    }
    
    // Create request
    const request: GetTaskProgressRequest = {
      taskId
    };
    
    // Get task progress
    return this.agentUIService.getTaskProgress(request);
  }
}
```

#### API Documentation

Document your APIs with OpenAPI/Swagger:

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: CoPilot API
  description: API for CoPilot AI assistant
  version: 1.0.0
  contact:
    name: CoPilot Team
    email: support@copilot.example.com

servers:
  - url: https://api.copilot.example.com/v1
    description: Production server
  - url: https://staging-api.copilot.example.com/v1
    description: Staging server

paths:
  /messages:
    get:
      summary: Get messages for a session
      description: Retrieve all messages for a specific session
      parameters:
        - name: sessionId
          in: query
          description: ID of the session
          required: true
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          description: Maximum number of messages to return
          required: false
          schema:
            type: integer
            default: 50
        - name: offset
          in: query
          description: Number of messages to skip
          required: false
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: A list of messages
          content:
            application/json:
              schema:
                type: object
                properties:
                  messages:
                    type: array
                    items:
                      $ref: '#/components/schemas/Message'
                  pagination:
                    type: object
                    properties:
                      page:
                        type: integer
                      pageSize:
                        type: integer
                      totalCount:
                        type: integer
                      totalPages:
                        type: integer
        '400':
          description: Bad request
        '401':
          description: Unauthorized
        '404':
          description: Session not found
        '500':
          description: Internal server error
      security:
        - bearerAuth: []

    post:
      summary: Send a message
      description: Send a new message to an agent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - content
                - sessionId
              properties:
                content:
                  type: string
                  description: The message content
                sessionId:
                  type: string
                  format: uuid
                  description: The session ID
                agentId:
                  type: string
                  format: uuid
                  description: The ID of the agent to send the message to (optional)
      responses:
        '201':
          description: Message sent successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Message'
        '400':
          description: Bad request
        '401':
          description: Unauthorized
        '404':
          description: Session or agent not found
        '500':
          description: Internal server error
      security:
        - bearerAuth: []

components:
  schemas:
    Message:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: The message ID
        content:
          type: string
          description: The message content
        sender:
          type: string
          enum: [user, agent]
          description: The sender of the message
        timestamp:
          type: string
          format: date-time
          description: The timestamp of the message
        sessionId:
          type: string
          format: uuid
          description: The session ID
      required:
        - id
        - content
        - sender
        - timestamp
        - sessionId

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Troubleshooting

### Common Issues

Here are solutions to common issues developers encounter:

#### Build Issues

**Problem**: Build fails with TypeScript errors

**Solution**:
1. Check that all dependencies are installed: `npm install`
2. Verify TypeScript version compatibility
3. Check for syntax errors in your code
4. Ensure all type definitions are correct

**Problem**: Build fails with ESLint errors

**Solution**:
1. Run `npm run lint` to see all linting errors
2. Fix the reported errors or disable rules if necessary
3. Consider using `--fix` option for auto-fixable errors: `npm run lint -- --fix`

#### Runtime Issues

**Problem**: Application crashes on startup

**Solution**:
1. Check the error logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure all required services (database, Redis, etc.) are running
4. Check for port conflicts

**Problem**: API requests fail

**Solution**:
1. Verify the API URL is correct
2. Check network connectivity
3. Verify authentication tokens are valid
4. Check CORS settings if accessing from a different domain

#### Performance Issues

**Problem**: Application is slow

**Solution**:
1. Use browser DevTools to identify bottlenecks
2. Check for unnecessary re-renders in React components
3. Optimize database queries
4. Implement caching where appropriate

**Problem**: Memory usage is high

**Solution**:
1. Check for memory leaks using browser DevTools
2. Ensure large objects are properly cleaned up
3. Implement pagination for large data sets
4. Use virtualization for long lists

### Debugging Tools

Use these tools to debug issues:

#### Browser DevTools

Browser DevTools are essential for frontend debugging:

1. **Elements Tab**: Inspect and modify the DOM and CSS
2. **Console Tab**: View logs, errors, and run JavaScript
3. **Sources Tab**: Debug JavaScript and set breakpoints
4. **Network Tab**: Inspect network requests and responses
5. **Performance Tab**: Analyze runtime performance
6. **Memory Tab**: Analyze memory usage and identify leaks

#### Node.js Debugger

Debug Node.js code with the built-in debugger:

```bash
# Start the application in debug mode
node --inspect-brk=9229 server.js
```

Then connect to the debugger using Chrome DevTools or VS Code.

#### VS Code Debugger

Configure VS Code for debugging:

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Program",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/server.js",
      "outFiles": [
        "${workspaceFolder}/dist/**/*.js"
      ],
      "sourceMaps": true
    },
    {
      "name": "Attach to Process",
      "type": "node",
      "request": "attach",
      "port": 9229,
      "restart": true
    },
    {
      "name": "Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/src"
    }
  ]
}
```

### Logging

Implement comprehensive logging:

#### Structured Logging

Use structured logging for better analysis:

```typescript
// src/logger.ts
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'copilot' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

export default logger;

// Usage example
logger.info('User sent a message', {
  userId: '123',
  sessionId: '456',
  messageLength: 42
});

logger.error('Failed to send message', {
  userId: '123',
  sessionId: '456',
  error: error.message,
  stack: error.stack
});
```

#### Request Logging

Log all API requests:

```typescript
// src/middleware/requestLogger.ts
import { Request, Response, NextFunction } from 'express';
import logger from '../logger';

export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  
  // Log request
  logger.info('API request', {
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
    userId: req.user?.id
  });
  
  // Override end method to log response
  const originalEnd = res.end;
  res.end = function(chunk?: any, encoding?: any) {
    const duration = Date.now() - start;
    
    // Log response
    logger.info('API response', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration,
      userId: req.user?.id
    });
    
    originalEnd.call(this, chunk, encoding);
  };
  
  next();
};
```

### Error Tracking

Track errors to identify and fix issues:

#### Error Tracking Service

```typescript
// src/services/ErrorTrackingService.ts
export class ErrorTrackingService {
  private apiKey: string;
  private endpoint: string;

  constructor(apiKey: string, endpoint: string) {
    this.apiKey = apiKey;
    this.endpoint = endpoint;
  }

  async trackError(error: Error, context?: any) {
    const errorData = {
      message: error.message,
      stack: error.stack,
      type: error.name,
      context,
      timestamp: new Date().toISOString(),
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'server',
      url: typeof window !== 'undefined' ? window.location.href : 'server'
    };

    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify(errorData)
      });

      if (!response.ok) {
        console.error('Failed to track error', await response.text());
      }
    } catch (err) {
      console.error('Failed to track error', err);
    }
  }
}

// Global error handler
const errorTrackingService = new ErrorTrackingService(
  process.env.ERROR_TRACKING_API_KEY,
  process.env.ERROR_TRACKING_ENDPOINT
);

process.on('uncaughtException', (error) => {
  errorTrackingService.trackError(error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  errorTrackingService.trackError(new Error(String(reason)), { promise });
});
```

#### Error Boundary

Implement error boundaries in React:

```typescript
// src/components/ErrorBoundary.tsx
import * as React from 'react';
import * as Sentry from '@sentry/react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to error tracking service
    errorTrackingService.trackError(error, { errorInfo });
    
    // Log to Sentry if configured
    Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>We're sorry, but something went wrong. Please try refreshing the page.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

*This guide provides comprehensive information for developers working with CoPilot. For additional resources and support, please refer to the API documentation and community forums.*