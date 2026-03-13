# AI-Karen New UI Implementation Plan

**Project**: `ui_launchers/defaultApp`  
**Date**: 2025-01-22  
**Approach**: Progressive Stages with Working Deliverables

---

## Architecture Overview

### Tech Stack

```yaml
Frontend Framework: Next.js 14 (App Router)
Language: TypeScript
React Version: 18+
AI Copilot Toolkit: CopilotKit (@copilotkit/react-core ^0.28)
Styling: TailwindCSS
State Management: React Context + SWR
Real-time: WebSocket + Server-Sent Events
Build Tool: Turbopack (Next.js default)
Testing: Vitest + Testing Library
```

### Project Structure

```
ui_launchers/defaultApp/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (chat)/                   # Chat route group
│   │   │   ├── chat/                 # Main chat interface
│   │   │   └── layout.tsx            # Chat layout
│   │   ├── (dashboard)/              # Dashboard route group
│   │   │   ├── memory/               # Memory dashboard
│   │   │   ├── agents/               # Agent management
│   │   │   └── models/               # Model management
│   │   ├── api/                      # API routes (backend proxy)
│   │   │   ├── chat/
│   │   │   ├── conversations/
│   │   │   ├── memory/
│   │   │   └── agents/
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Home page
│   ├── components/
│   │   ├── chat/                     # Chat components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── StreamingMessage.tsx
│   │   ├── conversations/            # Conversation components
│   │   │   ├── ConversationList.tsx
│   │   │   ├── ConversationCard.tsx
│   │   │   └── NewConversationDialog.tsx
│   │   ├── memory/                   # Memory components
│   │   │   ├── MemorySearch.tsx
│   │   │   ├── MemoryStats.tsx
│   │   │   └── KnowledgeGraph.tsx
│   │   ├── agents/                   # Agent components
│   │   │   ├── AgentSelector.tsx
│   │   │   ├── TaskMonitor.tsx
│   │   │   └── AgentConfig.tsx
│   │   └── ui/                       # Shared UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       └── Toast.tsx
│   ├── lib/
│   │   ├── api/                      # API client
│   │   │   ├── client.ts             # Base API client
│   │   │   ├── chat.ts               # Chat API
│   │   │   ├── conversations.ts      # Conversations API
│   │   │   ├── memory.ts             # Memory API
│   │   │   └── agents.ts             # Agents API
│   │   ├── hooks/                    # Custom hooks
│   │   │   ├── useChat.ts            # Chat hook
│   │   │   ├── useConversations.ts   # Conversations hook
│   │   │   ├── useMemory.ts          # Memory hook
│   │   │   └── useAgent.ts           # Agent hook
│   │   ├── stores/                   # State stores
│   │   │   ├── chatStore.ts
│   │   │   └── userStore.ts
│   │   └── utils/
│   │       ├── streaming.ts          # Streaming utilities
│   │       └── formatting.ts         # Text formatting
│   └── types/
│       ├── chat.ts                   # Chat types
│       ├── conversation.ts           # Conversation types
│       ├── memory.ts                 # Memory types
│       └── agent.ts                  # Agent types
├── public/
├── .env.local                        # Local environment
├── .env.production                   # Production environment
├── next.config.js
├── tailwind.config.js
└── package.json
```

---

## Stage 1: Core Chat Experience 🎯

**Duration**: 1-2 weeks  
**Status**: Foundation - Must be rock solid

### Features

#### 1.1 Chat Interface
- [ ] Clean, modern chat UI (similar to ChatGPT/Claude)
- [ ] Message input with auto-expanding textarea
- [ ] Streaming response display (typewriter effect)
- [ ] Message history with auto-scroll
- [ ] Syntax highlighting for code blocks
- [ ] Markdown rendering (using react-markdown)
- [ ] Copy code button
- [ ] Message timestamps
- [ ] Loading indicators

#### 1.2 Conversation Management
- [ ] Sidebar with conversation list
- [ ] Create new conversation
- [ ] Rename conversation
- [ ] Delete conversation
- [ ] Search conversations
- [ ] Conversation tags
- [ ] Active conversation highlighting

#### 1.3 Real-time Communication
- [ ] WebSocket connection for streaming
- [ ] Automatic reconnection on disconnect
- [ ] Connection status indicator
- [ ] Server-Sent Events fallback
- [ ] Message queuing when offline

#### 1.4 Responsive Design
- [ ] Mobile-first approach
- [ ] Collapsible sidebar
- [ ] Touch-friendly controls
- [ ] Dark/light mode toggle

### API Endpoints Needed

```typescript
POST /api/chat/send              // Send message
GET  /api/conversations          // List conversations
POST /api/conversations          // Create conversation
GET  /api/conversations/{id}     // Get conversation
PUT  /api/conversations/{id}     // Update conversation
DELETE /api/conversations/{id}   // Delete conversation
```

### Success Criteria

- ✅ Can send and receive messages
- ✅ Streaming works smoothly
- ✅ Conversations persist across refreshes
- ✅ Mobile responsive
- ✅ No console errors
- ✅ Lighthouse score > 90

---

## Stage 2: Memory & Intelligence 🧠

**Duration**: 1-2 weeks  
**Prerequisites**: Stage 1 complete

### Features

#### 2.1 Semantic Search
- [ ] Search bar across all conversations
- [ ] Real-time search results as you type
- [ ] Highlight matching text
- [ ] Search filters (date range, tags)
- [ ] Search result preview
- [ ] Click to jump to conversation

#### 2.2 Memory Dashboard
- [ ] Memory statistics (total vectors, storage size)
- [ ] Memory usage charts
- [ ] Search latency metrics
- [ ] Collection overview
- [ ] Memory optimization suggestions

#### 2.3 Context Awareness
- [ ] Display active context in sidebar
- [ ] Show relevant past conversations
- [ ] Suggested follow-up questions
- [ ] Context window indicator

#### 2.4 File Attachments
- [ ] Drag & drop file upload
- [ ] File type preview
- [ ] Attachment list in messages
- [ ] File size limits

### API Endpoints Needed

```typescript
POST /api/memory/search          // Semantic search
GET  /api/memory/stats           // Memory statistics
POST /api/memory/store           // Store memory
GET  /api/knowledge/query        // Query knowledge base
POST /api/file/attach            // Attach file
```

### Success Criteria

- ✅ Search returns relevant results
- ✅ Memory stats display correctly
- ✅ File uploads work
- ✅ Context awareness improves responses

---

## Stage 3: Agents & Orchestration 🤖

**Duration**: 2 weeks  
**Prerequisites**: Stage 2 complete

### Features

#### 3.1 Agent Selection
- [ ] Agent selector in chat interface
- [ ] Agent descriptions and capabilities
- [ ] Agent performance metrics
- [ ] Switch agents mid-conversation
- [ ] Agent-specific settings

#### 3.2 Task Management
- [ ] Task creation dialog
- [ ] Task progress tracking
- [ ] Task history
- [ ] Task cancellation
- [ ] Task retry on failure

#### 3.3 Execution Modes
- [ ] Mode selector (Native, LangGraph, DeepAgents, Auto)
- [ ] Mode explanations
- [ ] Performance comparison
- [ ] Per-mode settings

#### 3.4 Multi-Agent Workflows
- [ ] Visual workflow builder
- [ ] Agent chaining
- [ ] Parallel task execution
- [ ] Workflow templates

### API Endpoints Needed

```typescript
GET  /api/agents                    // List agents
POST /api/agent/ui/send-message     // Send to agent
POST /api/agent/ui/create-task      // Create task
GET  /api/agent/ui/task-progress    // Task progress
POST /api/agent/ui/cancel-task      // Cancel task
```

### Success Criteria

- ✅ Can select and switch agents
- ✅ Tasks execute correctly
- ✅ Progress tracking works
- ✅ Multi-agent workflows function

---

## Stage 4: Model Management 🎛️

**Duration**: 1 week  
**Prerequisites**: Stage 3 complete

### Features

#### 4.1 Model Selection
- [ ] Model picker with search
- [ ] Model details and specs
- [ ] Provider information
- [ ] Model comparison

#### 4.2 Provider Configuration
- [ ] Provider settings page
- [ ] API key management
- [ ] Provider health status
- [ ] Cost tracking

#### 4.3 Model Library
- [ ] Browse available models
- [ ] Model categories
- [ ] Model ratings
- [ ] Download manager (for local models)

#### 4.4 Performance Analytics
- [ ] Response time charts
- [ ] Token usage tracking
- [ ] Cost estimation
- [ ] Quality metrics

### API Endpoints Needed

```typescript
GET  /api/models                   // List models
POST /api/models/select            // Select model
GET  /api/models/providers         // List providers
GET  /api/models/library           // Model library
POST /api/models/download          // Download model
```

### Success Criteria

- ✅ Can switch models
- ✅ Provider configuration works
- ✅ Performance metrics accurate

---

## Stage 5: Advanced Features 🚀

**Duration**: 2+ weeks  
**Prerequisites**: Stage 4 complete

### Features

#### 5.1 Code Execution
- [ ] Code editor with syntax highlighting
- [ ] Execution button
- [ ] Output display
- [ ] Error handling
- [ ] Sandbox indicator

#### 5.2 Multimodal Processing
- [ ] Image upload
- [ ] Image preview in chat
- [ ] Video/audio support
- [ ] Multimodal model selection

#### 5.3 Extensions
- [ ] Extension marketplace
- [ ] Install/uninstall extensions
- [ ] Extension configuration
- [ ] Extension permissions

#### 5.4 Admin Panel
- [ ] User management
- [ ] System settings
- [ ] Audit logs
- [ ] Performance monitoring
- [ ] Health dashboard

#### 5.5 Monitoring & Observability
- [ ] Real-time metrics dashboard
- [ ] Error tracking
- [ ] SLO compliance
- [ ] Alerts and notifications

### Success Criteria

- ✅ All features work end-to-end
- ✅ Admin features functional
- ✅ Monitoring accurate

---

## Technical Implementation Details

### CopilotKit Integration

```typescript
// app/providers.tsx
import { CopilotKit } from '@copilotkit/react-core'

export function Providers({ children }) {
  return (
    <CopilotKit runtimeUrl="/api/copilot">
      {children}
    </CopilotKit>
  )
}
```

### Streaming Implementation

```typescript
// lib/hooks/useChat.ts
export function useChat(conversationId: string) {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (content: string) => {
    setIsStreaming(true)
    
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      body: JSON.stringify({ conversationId, message: content })
    })
    
    // Handle streaming response
    const reader = response.body.getReader()
    // ... streaming logic
  }

  return { messages, isStreaming, sendMessage }
}
```

### API Proxy Pattern

```typescript
// app/api/chat/send/route.ts
export async function POST(request: Request) {
  const body = await request.json()
  
  // Proxy to backend
  const response = await fetch(`${BACKEND_URL}/api/chat/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(body)
  })
  
  // Handle streaming
  if (response.body) {
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache'
      }
    })
  }
}
```

---

## Development Workflow

### Initial Setup

```bash
# 1. Create Next.js project
npx create-next-app@latest ui_launchers/defaultApp \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir

# 2. Install dependencies
cd ui_launchers/defaultApp
npm install @copilotkit/react-core @copilotkit/react-ui
npm install swr zustand
npm install react-markdown remark-gfm
npm install @tanstack/react-query

# 3. Set up environment
cp .env.local.example .env.local
# Edit BACKEND_URL and other vars
```

### Stage Development Pattern

```bash
# For each stage:
git checkout -b stage-N-feature-name

# Develop
npm run dev

# Test
npm run test
npm run lint

# Commit when stage is complete
git add .
git commit -m "Complete stage N: feature-name"
```

---

## Quality Standards

### Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 200KB (initial)

### Code Quality

- **TypeScript**: Strict mode, no `any`
- **Linting**: ESLint with no errors
- **Formatting**: Prettier
- **Testing**: > 80% coverage
- **Accessibility**: WCAG 2.1 AA

### Security

- **XSS Protection**: All user input sanitized
- **CSRF Protection**: Token-based
- **Auth**: JWT with httpOnly cookies
- **API Security**: Rate limiting, CORS

---

## Risk Mitigation

### Potential Issues

1. **CopilotKit Compatibility**
   - Risk: Version conflicts with existing backend
   - Mitigation: Test API compatibility early in Stage 1

2. **Streaming Complexity**
   - Risk: Streaming implementation difficult
   - Mitigation: Use proven libraries (fetch, eventsource)

3. **Performance at Scale**
   - Risk: Slow with many messages
   - Mitigation: Virtualization for long lists, pagination

4. **Backend API Changes**
   - Risk: Backend APIs change during development
   - Mitigation: Version API routes, use API client abstraction

---

## Success Metrics

### Stage 1 Success
- ✅ 100+ messages sent successfully
- ✅ < 100ms time to first token
- ✅ Zero crashes in 1-hour session
- ✅ Mobile and desktop working

### Stage 2 Success
- ✅ Search returns results in < 200ms
- ✅ Memory stats accurate
- ✅ 95%+ search relevance

### Stage 3 Success
- ✅ All agents functional
- ✅ Tasks complete successfully
- ✅ Multi-agent workflows work

### Overall Success
- ✅ All 5 stages complete
- ✅ Production deployed
- ✅ User satisfaction > 4.5/5
- ✅ Performance targets met

---

## Next Steps

1. **Initialize project** (Next.js setup)
2. **Set up CopilotKit** (configure provider)
3. **Build Stage 1** (Core chat)
4. **Test and refine** (user feedback)
5. **Proceed to Stage 2** (Memory)

**Let's start building! 🚀**
