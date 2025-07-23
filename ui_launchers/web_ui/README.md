# Karen AI Web UI

A modern, responsive web interface for the AI-Karen system built with Next.js 15.2.3, React 18, and a comprehensive UI component library.

## Overview

The Karen AI Web UI provides a sophisticated chat interface with plugin management, real-time communication, and seamless integration with the AI-Karen backend services. Built with modern web technologies and designed for both desktop and mobile experiences.

## Features

### Core Features
- **Interactive Chat Interface**: Real-time conversation with AI Karen
- **Plugin Management**: Comprehensive plugin system with dedicated interfaces for:
  - Database Connector
  - Facebook Integration
  - Gmail Integration
  - Date/Time Services
  - Weather Services
- **Settings Management**: Customizable AI personality, memory depth, and user preferences
- **Communications Center**: Notifications, alerts, and system updates
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Dark Mode**: Built-in dark theme with CSS custom properties

### Technical Features
- **Modern React Architecture**: Built with React 18 and Next.js 15.2.3
- **Component Library**: Comprehensive UI components based on Radix UI primitives
- **Type Safety**: Full TypeScript implementation with strict type checking
- **Real-time Updates**: Live chat interface with backend integration
- **Memory Integration**: Persistent conversation history and context awareness
- **Plugin Architecture**: Extensible plugin system with dedicated management interfaces

## Technology Stack

### Core Framework
- **Next.js**: 15.2.3 (React framework with App Router)
- **React**: 18.3.1 (UI library)
- **TypeScript**: 5.x (Type safety and development experience)

### UI Components & Styling
- **Radix UI**: Comprehensive set of accessible, unstyled UI primitives
  - Accordion, Alert Dialog, Avatar, Checkbox, Dialog, Dropdown Menu
  - Label, Menubar, Popover, Progress, Radio Group, Scroll Area
  - Select, Separator, Slider, Switch, Tabs, Toast, Tooltip
- **Tailwind CSS**: 3.4.1 (Utility-first CSS framework)
- **Tailwind Animate**: Animation utilities
- **Lucide React**: Modern icon library
- **Class Variance Authority**: Component variant management
- **Tailwind Merge**: Intelligent Tailwind class merging

### State Management & Data
- **TanStack Query**: 5.66.0 (Server state management)
- **React Hook Form**: 7.54.2 (Form state management)
- **Zod**: 3.24.2 (Schema validation)

### AI & Backend Integration
- **Google Genkit**: 1.8.0 (AI development framework)
- **Firebase**: 11.7.3 (Authentication and real-time features)
- **Custom Backend Service**: Integration with AI-Karen Python backend

### Development Tools
- **ESLint**: Code linting and quality
- **PostCSS**: CSS processing
- **Patch Package**: Dependency patching

## Prerequisites

### System Requirements
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (or yarn/pnpm equivalent)
- **AI-Karen Backend**: Running backend services (see main project README)

### Environment Setup
1. Ensure the AI-Karen backend is running and accessible
2. Configure environment variables (see Configuration section)
3. Install dependencies and start development server

## Quick Start

### Installation

```bash
# Navigate to the web UI directory
cd ui_launchers/web_ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:9002`

### Development Commands

```bash
# Development server with Turbopack (faster builds)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type checking
npm run typecheck

# AI development with Genkit
npm run genkit:dev
npm run genkit:watch
```

## Configuration

### Environment Variables

Create a `.env.local` file in the web UI directory:

```env
# Backend Configuration
KAREN_BACKEND_URL=http://localhost:8000
KAREN_API_KEY=your_api_key_here

# Firebase Configuration (if using Firebase features)
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id

# Genkit Configuration
GOOGLE_GENKIT_ENV=dev
```

### Next.js Configuration

The `next.config.ts` file includes:
- TypeScript build error handling for development
- ESLint configuration for builds
- Image optimization for external sources
- Remote pattern configuration for placeholder images

### Tailwind Configuration

Custom theme configuration includes:
- CSS custom properties for theming
- Extended color palette with semantic naming
- Custom animations and keyframes
- Responsive design utilities
- Dark mode support

## Component Architecture

### Directory Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Main application page
│   ├── globals.css        # Global styles and CSS variables
│   └── actions.ts         # Server actions
├── components/            # React components
│   ├── ui/               # Base UI components (Radix UI based)
│   ├── chat/             # Chat interface components
│   ├── plugins/          # Plugin-specific components
│   ├── settings/         # Settings and configuration
│   └── sidebar/          # Navigation and sidebar components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and configurations
│   ├── karen-backend.ts  # Backend integration service
│   ├── types.ts          # TypeScript type definitions
│   ├── utils.ts          # Utility functions
│   └── constants.ts      # Application constants
├── services/             # Business logic services
│   ├── chatService.ts    # Chat and conversation management
│   ├── memoryService.ts  # Memory and context management
│   └── pluginService.ts  # Plugin management
└── ai/                   # AI and Genkit integration
    ├── genkit.ts         # Genkit configuration
    └── tools/            # AI tools and functions
```

### Key Components

#### Main Application (`page.tsx`)
- **SidebarProvider**: Layout management with collapsible sidebar
- **Navigation**: Dynamic view switching between chat, settings, and plugins
- **Plugin Integration**: Dedicated interfaces for each plugin type
- **Responsive Design**: Mobile-first approach with adaptive layouts

#### UI Components (`components/ui/`)
All UI components are built on Radix UI primitives with custom styling:
- Fully accessible with keyboard navigation
- Consistent design system with CSS custom properties
- Dark mode support built-in
- TypeScript interfaces for all props

#### Chat Interface (`components/chat/`)
- Real-time message handling
- Message history and context management
- AI response processing and display
- Voice synthesis integration (TTS)

#### Backend Integration (`lib/karen-backend.ts`)
- RESTful API client for AI-Karen backend
- Memory service integration
- Plugin execution management
- Analytics and system metrics
- Caching layer for performance optimization

## API Integration

### Backend Service Integration

The web UI integrates with the AI-Karen backend through a comprehensive service layer:

#### Chat Processing
```typescript
// Process user messages with full context
const response = await karenBackend.processUserMessage(
  message,
  conversationHistory,
  settings,
  userId,
  sessionId
);
```

#### Memory Management
```typescript
// Store conversation in long-term memory
await karenBackend.storeMemory(
  content,
  metadata,
  tags,
  userId,
  sessionId
);

// Query relevant memories
const memories = await karenBackend.queryMemories({
  text: query,
  user_id: userId,
  top_k: 5
});
```

#### Plugin Execution
```typescript
// Execute plugins with parameters
const result = await karenBackend.executePlugin(
  'database-connector',
  { query: 'SELECT * FROM users' },
  userId
);
```

### Error Handling

- **Network Resilience**: Automatic retry logic with exponential backoff
- **Fallback Responses**: Graceful degradation when backend is unavailable
- **User Feedback**: Clear error messages and recovery suggestions
- **Logging**: Comprehensive error logging for debugging

## Development Guidelines

### Code Style
- **TypeScript**: Strict mode enabled with comprehensive type checking
- **ESLint**: Configured for React and Next.js best practices
- **Component Structure**: Functional components with hooks
- **File Naming**: kebab-case for files, PascalCase for components

### State Management
- **Local State**: React useState for component-specific state
- **Server State**: TanStack Query for API data management
- **Form State**: React Hook Form with Zod validation
- **Global State**: Context API for application-wide state

### Performance Optimization
- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: Next.js Image component with optimization
- **Bundle Analysis**: Built-in bundle analyzer
- **Caching**: Service worker caching for offline functionality

## Building and Deployment

### Development Build
```bash
npm run dev
```
- Runs on port 9002
- Hot module replacement enabled
- Turbopack for faster builds
- Source maps for debugging

### Production Build
```bash
npm run build
npm start
```
- Optimized bundle with tree shaking
- Static generation where possible
- Compressed assets
- Performance monitoring

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Troubleshooting

### Common Issues

#### Backend Connection Issues
```bash
# Check backend status
curl http://localhost:8000/api/health

# Verify environment variables
echo $KAREN_BACKEND_URL
```

#### Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Type check
npm run typecheck
```

#### Development Server Issues
```bash
# Check port availability
lsof -i :9002

# Start with different port
npm run dev -- -p 3001
```

### Performance Issues
- **Large Bundle Size**: Use bundle analyzer to identify large dependencies
- **Slow API Responses**: Check backend performance and network latency
- **Memory Leaks**: Use React DevTools Profiler to identify issues

### Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Mobile 90+
- **Feature Detection**: Graceful fallbacks for unsupported features

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install dependencies: `npm install`
4. Start development server: `npm run dev`
5. Make changes and test thoroughly
6. Submit a pull request

### Code Standards
- Follow existing code style and patterns
- Add TypeScript types for all new code
- Include unit tests for new functionality
- Update documentation for API changes
- Ensure accessibility compliance

### Testing
```bash
# Run type checking
npm run typecheck

# Run linting
npm run lint

# Build production bundle
npm run build
```

## License

This project is part of the AI-Karen system. See the main project LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the main AI-Karen project documentation
3. Submit issues through the project's issue tracker
4. Join the community discussions for support and feature requests