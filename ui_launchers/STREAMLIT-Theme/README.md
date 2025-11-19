# Kari AI - Lite Streamlit Console

## Overview

The Kari AI Lite Streamlit Console is a personal-DB-aware chat interface that provides a sleek, dark neon-themed UI for interacting with AI models. This implementation features a three-panel layout with enhanced message styling, conversation persistence, and comprehensive system status indicators.

## Features

### User Interface
- **Dark Neon Theme**: A visually appealing dark theme with cyan and magenta neon accents
- **Three-Panel Layout**: 
  - Left sidebar for navigation and conversation history
  - Main chat area with enhanced message display
  - Right sidebar for configuration and system status
- **Enhanced Message Styling**: Messages with avatars, timestamps, and metadata badges
- **Streaming Response Support**: Real-time response streaming with playback controls
- **Responsive Design**: Adapts to different screen sizes

### Functionality
- **Conversation Persistence**: Save and load chat histories
- **Model Selection**: Choose between local (llama-cpp) and cloud models (GPT, Claude)
- **Plugin System**: Toggle and monitor search, memory, and tools plugins
- **Reasoning Modes**: Configure AI reasoning with Off, Standard, or Detailed modes
- **User Profile Integration**: Fetch and display user context from personal database
- **Keyboard Shortcuts**: 
  - Ctrl/Cmd + K: Focus on input
  - Ctrl/Cmd + N: New chat
  - Escape: Clear input

### System Features
- **Status Indicators**: Real-time monitoring of model, database, and plugin status
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Performance Optimizations**: Lazy loading, session caching, and efficient rendering
- **Debug Mode**: Detailed diagnostics and system information for troubleshooting

## Installation

### Prerequisites
- Python 3.8 or higher
- Streamlit
- Required Python packages (see requirements.txt)

### Setup
1. Clone the repository
   ```bash
   git clone <repository-url>
   cd ui_launchers/STREAMLIT-Theme
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create necessary services
   - Ensure the conversation and user services are available
   - Configure database connections as needed

4. Run the application
   ```bash
   streamlit run index.py
   ```

## Configuration

### Environment Variables
The application can be configured through environment variables:

- `USER_ID`: Default user ID (defaults to "dev_user")
- `DEFAULT_MODEL`: Default AI model (defaults to "llama-cpp")
- `DEBUG_MODE`: Enable debug features (defaults to False)

### Service Configuration
The application integrates with two main services:

1. **Conversation Service**: Handles conversation persistence and management
2. **User Service**: Manages user profiles and personal context

These services should be implemented according to the interfaces defined in the `services/` directory.

## Architecture

### Directory Structure
```
ui_launchers/STREAMLIT-Theme/
├── index.py                 # Main application file
├── services/
│   ├── conversation_service.py  # Conversation management
│   └── user_service.py        # User profile management
├── README.md                # This documentation
└── requirements.txt          # Python dependencies
```

### Key Components

1. **Session Management**: Handles user sessions and state persistence
2. **UI Components**: Modular UI rendering functions for different interface elements
3. **Service Integration**: Clean separation between UI and backend services
4. **Status Monitoring**: Real-time system health and performance monitoring

### Data Flow
1. User interacts with the UI through the Streamlit interface
2. User actions trigger events that update the session state
3. Service functions are called to persist data or fetch information
4. Results are displayed back to the user with appropriate status indicators

## Customization

### Theme Customization
The neon theme can be customized by modifying the CSS variables in the `load_neon_theme()` function:

```python
:root {
    --primary-neon: #00FFFF;     /* Primary accent color */
    --secondary-neon: #FF00FF;   /* Secondary accent color */
    --background-dark: #0F0F1B;   /* Main background */
    --background-panel: #1A1A2E;  /* Panel background */
    --text-primary: #FFFFFF;       /* Main text color */
    --text-secondary: #00FFFF;     /* Secondary text color */
}
```

### Plugin Development
New plugins can be added by:
1. Adding the plugin to the `active_plugins` session state
2. Implementing plugin functionality in the backend
3. Adding plugin status indicators to the UI

## Deployment

### Local Development
For local development, run the application with:
```bash
streamlit run index.py
```

### Production Deployment
For production deployment:

1. **Server Requirements**:
   - Python 3.8+ environment
   - Sufficient memory for model loading
   - Database connections for services

2. **Configuration**:
   - Set production environment variables
   - Configure secure database connections
   - Set up proper logging

3. **Deployment Options**:
   - **Streamlit Sharing**: Use Streamlit's sharing feature
   - **Docker**: Containerize the application
   - **Cloud Services**: Deploy to AWS, GCP, or Azure

### Docker Deployment
Create a Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "index.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t kari-ai-console .
docker run -p 8501:8501 kari-ai-console
```

## Troubleshooting

### Common Issues

1. **Service Connection Errors**
   - Verify service endpoints are accessible
   - Check network connectivity
   - Review service logs

2. **Performance Issues**
   - Enable debug mode to see diagnostics
   - Check memory usage
   - Monitor response times

3. **UI Rendering Problems**
   - Verify CSS is loading correctly
   - Check browser console for errors
   - Try clearing browser cache

### Debug Mode
Enable debug mode in the sidebar to access:
- Detailed system information
- Response metadata
- Performance metrics
- Error details

## Future Enhancements

### Planned Features
- Real-time collaboration
- Voice input/output
- File upload and processing
- Advanced plugin marketplace
- Multi-language support

### Contribution Guidelines
1. Follow the existing code style
2. Add appropriate error handling
3. Update documentation for new features
4. Test thoroughly before submitting

## Support

For support and questions:
- Create an issue in the project repository
- Check the troubleshooting section
- Review debug information in debug mode

## License

This project is licensed under the MIT License. See LICENSE file for details.