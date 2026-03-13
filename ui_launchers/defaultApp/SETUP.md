# AI-Karen New UI - Setup Guide

## Quick Start

### 1. Environment Configuration

Create a `.env.local` file in the project root:

```bash
# AI-Karen Backend Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# WebSocket Configuration  
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# API Configuration
NEXT_PUBLIC_API_TIMEOUT=30000

# Feature Flags
NEXT_PUBLIC_ENABLE_STREAMING=true
NEXT_PUBLIC_ENABLE_MARKDOWN=true
NEXT_PUBLIC_ENABLE_SYNTAX_HIGHLIGHTING=true

# Development Mode
NODE_ENV=development
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Start Backend Server

In a separate terminal, start the AI-Karen backend:

```bash
cd /mnt/development/KIRO/AI-Karen
python -m src.ai_karen_engine
```

## Project Structure

```
ui_launchers/defaultApp/
├── app/                    # Next.js App Router pages
├── components/             # React components
│   ├── chat/              # Chat interface components
│   ├── conversations/     # Conversation management
│   └── ui/                # Shared UI components
├── lib/                   # Core utilities
│   ├── api/              # API client
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # State management (Zustand)
│   └── utils/            # Utility functions
├── types/                 # TypeScript type definitions
└── public/                # Static assets
```

## Features Implemented (Stage 1)

### Core Chat Experience
- ✅ Clean, modern chat interface
- ✅ Real-time message streaming
- ✅ Markdown rendering
- ✅ Code syntax highlighting
- ✅ Auto-expanding message input
- ✅ Conversation management
- ✅ Dark/light mode support
- ✅ Responsive design

### State Management
- ✅ Zustand store for client state
- ✅ Conversation persistence
- ✅ Message history
- ✅ Streaming state management

### API Integration
- ✅ Base API client with authentication
- ✅ Streaming support (Server-Sent Events)
- ✅ Error handling and timeout management
- ✅ Type-safe API calls

## Available Scripts

```bash
# Development
npm run dev          # Start development server

# Build
npm run build        # Build for production
npm start           # Start production server

# Code Quality
npm run lint        # Run ESLint
npm run type-check  # Run TypeScript compiler

# Testing
npm run test        # Run tests (when configured)
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Markdown**: react-markdown + remark-gfm
- **Code Highlighting**: react-syntax-highlighter
- **Icons**: lucide-react
- **Utilities**: uuid

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse Score: > 90
- Streaming latency: < 100ms to first token

## Development Tips

### Hot Reload
The development server supports hot module replacement. Changes to components will reflect immediately without a full page refresh.

### TypeScript
All code is written in TypeScript with strict mode enabled. Take advantage of type checking for safer code.

### TailwindCSS
Use utility classes for styling. The theme is configured for both light and dark modes.

### API Mocking (For Development)
If the backend is not available, you can mock API responses in the `lib/api/client.ts` file.

## Troubleshooting

### Backend Connection Issues
If you see connection errors:
1. Ensure the backend is running on port 8000
2. Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
3. Verify CORS settings on the backend

### Streaming Not Working
1. Check if streaming is enabled: `NEXT_PUBLIC_ENABLE_STREAMING=true`
2. Verify backend supports Server-Sent Events
3. Check browser console for errors

### Build Errors
1. Clear Next.js cache: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check TypeScript errors: `npm run type-check`

## Next Steps

### Stage 1 Completion
- [ ] Test with backend API
- [ ] Implement conversation list sidebar
- [ ] Add conversation rename/delete
- [ ] Add search functionality
- [ ] Performance optimization
- [ ] Accessibility audit

### Future Stages
- Stage 2: Memory & Intelligence
- Stage 3: Agents & Orchestration
- Stage 4: Model Management
- Stage 5: Advanced Features

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for details.

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Commit with descriptive messages
4. Push and create a pull request

## License

Part of the AI-Karen project. See main project LICENSE.
