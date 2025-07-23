# AI Karen - Modern Streamlit Interface

A sophisticated, responsive web interface for AI Karen built with Streamlit, featuring modern design patterns, real-time backend integration, and comprehensive system management capabilities.

## Overview

The AI Karen Streamlit interface provides a production-ready web application with advanced features including real-time chat, memory management, plugin orchestration, and comprehensive system monitoring. Built with a modular architecture and modern design principles, it offers both user-friendly operation and powerful administrative capabilities.

## Features

### Core Interface Features
- **Modern Pill Navigation**: Horizontal navigation with smooth transitions and hover effects
- **Interactive Dashboard**: Real-time metrics, activity charts, and system health monitoring
- **Responsive Design**: Mobile-first approach with adaptive layouts for all screen sizes
- **Dark/Light Themes**: Multiple theme options with CSS custom properties
- **Real-time Updates**: Live system monitoring with auto-refresh capabilities
- **Modal Dialogs**: Advanced modal system with drag-and-drop interfaces

### AI & Chat Features
- **Enhanced Chat Interface**: Real-time conversation with AI Karen
- **Memory Explorer**: Visual memory management with search and filtering
- **Context Awareness**: Persistent conversation history and context management
- **Voice Integration**: Text-to-speech and speech recognition capabilities
- **Message Threading**: Organized conversation threads with metadata

### System Management
- **Plugin Manager**: Comprehensive plugin system with lifecycle management
- **System Health Monitoring**: Real-time service status and performance metrics
- **Analytics Dashboard**: Usage insights, performance metrics, and trend analysis
- **User Management**: Role-based access control and user administration
- **Configuration Management**: Dynamic settings with validation and persistence

### Backend Integration
- **AI Karen Engine**: Full integration with the AI Karen backend services
- **Memory Services**: Long-term and short-term memory management
- **Plugin Orchestration**: Dynamic plugin loading and execution
- **Database Integration**: Multi-database support (PostgreSQL, Redis, DuckDB, Milvus)
- **API Gateway**: Unified API access with error handling and retry logic

## Technology Stack

### Core Framework
- **Streamlit**: Latest version with modern components and features
- **Python**: 3.8+ with async/await support
- **Pydantic**: Data validation and settings management

### Backend Integration
- **HTTPX**: Async HTTP client for backend communication
- **WebSockets**: Real-time communication with backend services
- **Cryptography**: Secure data handling and encryption
- **Watchdog**: File system monitoring for configuration changes

### Data & AI
- **PyMilvus**: Vector database integration for embeddings
- **DuckDB**: Local analytics and data processing
- **Llama-cpp-python**: Local LLM integration and inference

### UI & Visualization
- **Plotly**: Interactive charts and data visualization
- **Custom CSS**: Modern styling with CSS variables and animations
- **Responsive Components**: Mobile-optimized UI components

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **AI Karen Backend**: Running backend services (FastAPI server)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for models and data

### Dependencies
All dependencies are managed through `requirements.txt`:
```bash
streamlit
streamlit-autorefresh
httpx
websockets
pymilvus
duckdb
pydantic
watchdog
aiofiles
cryptography
llama-cpp-python
```

## Quick Start

### Installation and Setup

```bash
# Navigate to the Streamlit UI directory
cd ui_launchers/streamlit_ui

# Install dependencies
pip install -r requirements.txt

# Ensure AI Karen backend is running
# (See main project README for backend setup)

# Start the Streamlit interface
streamlit run app.py
```

The interface will be available at `http://localhost:8501`

### Development Mode

```bash
# Start with auto-reload for development
streamlit run app.py --server.runOnSave true

# Start with custom port
streamlit run app.py --server.port 8502

# Start with debug logging
STREAMLIT_LOGGER_LEVEL=debug streamlit run app.py
```

## Configuration

### Environment Variables

Create a `.env` file in the Streamlit UI directory:

```env
# Backend Configuration
KAREN_BACKEND_URL=http://localhost:8000
KAREN_API_KEY=your_api_key_here

# Database Configuration
POSTGRES_URL=postgresql://user:pass@localhost:5432/karen
REDIS_URL=redis://localhost:6379
MILVUS_HOST=localhost
MILVUS_PORT=19530

# UI Configuration
STREAMLIT_THEME=dark
STREAMLIT_AUTO_REFRESH=true
STREAMLIT_DEBUG=false

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

### Streamlit Configuration

The interface includes a `.streamlit/config.toml` file with optimized settings:

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## Architecture

### Directory Structure

```
ui_launchers/streamlit_ui/
├── app.py                     # Main application entry point
├── requirements.txt           # Python dependencies
├── README.md                 # This documentation
├── test_integration.py       # Integration tests
├── components/               # Reusable UI components
│   ├── backend_components.py # Backend-integrated components
│   ├── navigation.py         # Navigation and routing
│   ├── sidebar.py           # Global sidebar components
│   ├── styling.py           # CSS injection and theming
│   ├── modals.py            # Modal dialogs and overlays
│   └── data_utils.py        # Data processing utilities
├── pages/                   # Individual page implementations
│   ├── dashboard.py         # Interactive dashboard
│   ├── chat.py              # Enhanced chat interface
│   ├── plugins.py           # Plugin management
│   ├── settings.py          # Configuration management
│   ├── monitoring.py        # System monitoring
│   └── user_management.py   # User administration
├── services/                # Business logic services
│   ├── backend_integration.py # AI Karen backend client
│   ├── chat_service.py      # Chat and conversation logic
│   ├── memory_service.py    # Memory management
│   ├── plugin_service.py    # Plugin orchestration
│   ├── user_service.py      # User management
│   └── data_flow_manager.py # Data flow coordination
├── helpers/                 # Utility functions
│   ├── session.py           # Session management
│   ├── auth.py              # Authentication helpers
│   ├── icons.py             # Icon definitions
│   ├── context.py           # Context management
│   └── api_handler.py       # API communication
├── config/                  # Configuration management
│   ├── env.py               # Environment configuration
│   ├── theme.py             # Theme definitions
│   └── routing.py           # Route configuration
└── styles/                  # CSS stylesheets
    ├── dark.css             # Dark theme styles
    ├── light.css            # Light theme styles
    └── enterprise.css       # Enterprise theme styles
```

### Component Architecture

#### Main Application (`app.py`)
- **Navigation System**: Pill-based horizontal navigation with state management
- **Theme Management**: Dynamic theme switching with CSS injection
- **Backend Integration**: Centralized backend service initialization
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Session Management**: User context and state persistence

#### Backend Integration (`services/backend_integration.py`)
- **API Client**: Async HTTP client with retry logic and error handling
- **WebSocket Manager**: Real-time communication with backend services
- **Cache Layer**: Intelligent caching for performance optimization
- **Health Monitoring**: Service health checks and status reporting

#### UI Components (`components/`)
- **Modular Design**: Reusable components with consistent interfaces
- **State Management**: Component-level state with global context
- **Responsive Layout**: Mobile-first design with adaptive breakpoints
- **Accessibility**: ARIA labels and keyboard navigation support

## Navigation & Pages

### Main Navigation Sections

- **🏠 Dashboard**: System overview with real-time metrics and quick actions
- **💬 Chat**: Enhanced AI conversation interface with memory integration
- **🧠 Memory**: Visual memory explorer with search and management tools
- **📊 Analytics**: Comprehensive usage analytics and performance insights
- **🧩 Plugins**: Plugin marketplace and management interface
- **⚙️ Settings**: System configuration and user preferences
- **🛡️ Admin**: Administrative tools and user management
- **📈 Monitoring**: Real-time system health and performance monitoring

### Page Features

#### Dashboard Page
- **Live Metrics**: Real-time system statistics and performance indicators
- **Activity Timeline**: Recent system activity with filtering and search
- **Quick Actions**: One-click access to frequently used features
- **System Status**: Health monitoring for all connected services
- **Usage Analytics**: Charts and graphs showing system utilization

#### Chat Page
- **Real-time Messaging**: Instant communication with AI Karen
- **Message History**: Persistent conversation history with search
- **Context Awareness**: Automatic context injection from memory
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **File Sharing**: Drag-and-drop file upload and processing

#### Memory Page
- **Memory Explorer**: Visual interface for browsing stored memories
- **Search & Filter**: Advanced search with metadata filtering
- **Memory Management**: Create, edit, and delete memory entries
- **Context Visualization**: Graph view of memory relationships
- **Export/Import**: Backup and restore memory data

## Backend Integration

### AI Karen Engine Integration

The Streamlit interface provides comprehensive integration with the AI Karen backend:

#### Chat Processing
```python
# Process user messages with full context
response = await backend_service.process_message(
    message=user_input,
    user_id=session_state.user_id,
    conversation_id=session_state.conversation_id,
    context=memory_context
)
```

#### Memory Management
```python
# Store and retrieve memories
await backend_service.store_memory(
    content=message_content,
    metadata=message_metadata,
    user_id=session_state.user_id
)

memories = await backend_service.query_memories(
    query=search_query,
    user_id=session_state.user_id,
    limit=10
)
```

#### Plugin Orchestration
```python
# Execute plugins with parameters
result = await backend_service.execute_plugin(
    plugin_name="database-connector",
    parameters={"query": sql_query},
    user_id=session_state.user_id
)
```

### Real-time Features

- **WebSocket Connection**: Persistent connection for real-time updates
- **Auto-refresh**: Configurable auto-refresh for live data
- **Event Streaming**: Real-time event notifications and updates
- **Status Monitoring**: Live system health and performance metrics

## Development

### Development Setup

```bash
# Clone and navigate to directory
cd ui_launchers/streamlit_ui

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8

# Start development server
streamlit run app.py --server.runOnSave true
```

### Code Style and Standards

- **Python Style**: Follow PEP 8 with Black formatting
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Google-style docstrings for all modules and functions
- **Error Handling**: Comprehensive exception handling with user feedback
- **Logging**: Structured logging with appropriate levels

### Testing

```bash
# Run integration tests
python test_integration.py

# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Performance Optimization

- **Caching**: Streamlit caching for expensive operations
- **Lazy Loading**: Dynamic component loading for better performance
- **Memory Management**: Efficient memory usage with cleanup
- **Database Optimization**: Connection pooling and query optimization

## Deployment

### Production Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment variables
export STREAMLIT_ENV=production
export KAREN_BACKEND_URL=https://your-backend-url.com

# Start with production settings
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Environment Configuration

- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Optimized for performance and security

## Troubleshooting

### Common Issues

#### Backend Connection Issues
```bash
# Check backend status
curl http://localhost:8000/health

# Verify environment variables
echo $KAREN_BACKEND_URL

# Check network connectivity
ping localhost
```

#### Performance Issues
- **Slow Loading**: Check backend response times and database performance
- **Memory Usage**: Monitor Python memory usage and optimize caching
- **UI Responsiveness**: Profile component rendering and optimize updates

#### Configuration Issues
- **Theme Problems**: Verify CSS injection and theme configuration
- **Navigation Issues**: Check routing configuration and state management
- **Plugin Errors**: Verify plugin registration and backend connectivity

### Debug Mode

```bash
# Enable debug logging
STREAMLIT_LOGGER_LEVEL=debug streamlit run app.py

# Enable development mode
STREAMLIT_ENV=development streamlit run app.py

# Profile performance
streamlit run app.py --server.enableStaticServing=false
```

### Support and Monitoring

- **Health Checks**: Built-in health monitoring for all services
- **Error Reporting**: Comprehensive error logging and user feedback
- **Performance Metrics**: Real-time performance monitoring and alerts
- **User Analytics**: Usage tracking and behavior analysis

## Contributing

### Development Guidelines

1. **Fork the Repository**: Create a personal fork for development
2. **Feature Branches**: Create feature branches for new functionality
3. **Code Quality**: Ensure code passes linting and testing
4. **Documentation**: Update documentation for new features
5. **Testing**: Add tests for new functionality
6. **Pull Requests**: Submit well-documented pull requests

### Code Standards

- **Python**: Follow PEP 8 and use Black for formatting
- **TypeScript**: Use strict typing for all interfaces
- **Documentation**: Maintain comprehensive documentation
- **Testing**: Achieve >80% test coverage for new code

## License

This project is part of the AI-Karen system. See the main project LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the main AI-Karen project documentation
3. Submit issues through the project's issue tracker
4. Join the community discussions for support and feature requests