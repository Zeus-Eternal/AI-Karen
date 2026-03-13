# KAREN AI - Default Theme UI

Production-ready React + TypeScript UI for KAREN AI powered by Vite.

## 🚀 Features

- ⚡ Lightning-fast development with Vite + SWC
- 🎨 Modern UI with Tailwind CSS
- 🔷 TypeScript for type safety
- 🎯 React Router for navigation
- 🔄 TanStack Query for data fetching
- 🎭 Zustand for state management
- 🌙 Dark mode support
- 📱 Fully responsive design
- 🎨 Beautiful animations with Framer Motion
- 📝 Markdown support for AI responses

## 🛠️ Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Router**: React Router DOM
- **UI Components**: Lucide Icons
- **Notifications**: Sonner

## 📦 Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

## 🎯 Available Scripts

- `npm run dev` - Start development server (port 9002)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking
- `npm run format` - Format code with Prettier
- `npm test` - Run tests

## 🌐 API Configuration

Update `.env` to point to your KAREN AI backend:

```env
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
src/
├── components/      # Reusable UI components
├── pages/          # Page components
├── stores/         # Zustand state stores
├── lib/            # Utilities and API client
├── App.tsx         # Main app component
├── main.tsx        # Entry point
└── index.css       # Global styles
```

## 🎨 Theming

The UI supports light and dark modes with automatic system theme detection. Toggle between themes using the button in the sidebar.

## 🔌 API Integration

The UI connects to the KAREN AI backend via RESTful APIs:

- `/api/chat/*` - Chat and conversation management
- `/api/plugins/*` - Plugin management
- `/api/system/*` - System settings and health
- `/api/analytics/*` - Usage analytics

## 🏗️ Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## 📄 License

Part of the KAREN AI project.
