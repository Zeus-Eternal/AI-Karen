# Kari Developer Tools with AG-UI Integration

This document describes the enhanced developer tools for Kari, featuring AG-UI components and CopilotKit integration for a modern development experience.

## Overview

The Kari Developer Tools provide a comprehensive development environment with:

- **AG-UI Components**: Modern data grids, charts, and visualizations
- **CopilotKit Integration**: AI-powered development assistance
- **Real-time Monitoring**: Live system metrics and component health
- **Interactive Management**: Component control and configuration
- **Code Generation**: AI-assisted boilerplate generation

## Components

### 1. Kari Dev Studio (Web UI)

The main web interface for developer tools, accessible at `/developer`.

#### Features:
- **Component Management**: View and manage all Kari components (plugins, extensions, hooks, LLM providers)
- **Real-time Metrics**: Live performance data with AG Charts visualization
- **Health Monitoring**: Component health status with visual indicators
- **AI Assistant**: CopilotKit-powered development assistance
- **Interactive Actions**: Start, stop, restart, and configure components

#### Usage:
```typescript
// Access through the web UI at /developer
// Or integrate into your own components:
import KariDevStudio from "@/src/components/developer/KariDevStudio";

<KariDevStudio />
```

### 2. Enhanced CLI Tool

A rich command-line interface for developer operations.

#### Installation:
```bash
# Make the CLI executable
chmod +x scripts/kari_dev_cli.py

# Install dependencies
pip install rich requests
```

#### Usage:
```bash
# List all components
python scripts/kari_dev_cli.py list

# Filter by component type
python scripts/kari_dev_cli.py list --type plugin

# Show component details
python scripts/kari_dev_cli.py show weather_plugin

# Execute component actions
python scripts/kari_dev_cli.py action plugin_weather_plugin restart

# View chat metrics
python scripts/kari_dev_cli.py metrics --hours 24

# Generate component boilerplate
python scripts/kari_dev_cli.py generate plugin my_new_plugin --features chat_integration ai_assistance
```

### 3. Developer API

RESTful API endpoints for programmatic access to developer tools.

#### Endpoints:

##### Get System Components
```http
GET /api/developer/components
```

Response:
```json
{
  "components": [
    {
      "id": "plugin_weather",
      "name": "weather",
      "type": "plugin",
      "status": "active",
      "health": "healthy",
      "metrics": {
        "executions": 150,
        "success_rate": 0.96,
        "avg_response_time": 450,
        "memory_usage": 25.5,
        "cpu_usage": 3.2
      },
      "capabilities": ["chat_integration", "tool_calling"],
      "last_activity": "2024-01-15T10:30:00Z",
      "chat_integration": true,
      "copilot_enabled": true
    }
  ],
  "total_count": 12,
  "active_count": 10,
  "healthy_count": 9,
  "chat_integrated_count": 8,
  "ai_enabled_count": 6
}
```

##### Get Chat Metrics
```http
GET /api/developer/chat-metrics?hours=24
```

Response:
```json
{
  "metrics": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "total_messages": 45,
      "ai_suggestions": 12,
      "tool_calls": 8,
      "memory_operations": 5,
      "response_time_ms": 850,
      "user_satisfaction": 0.92
    }
  ],
  "summary": {
    "total_messages": 1080,
    "avg_response_time": 750,
    "avg_satisfaction": 0.89,
    "total_ai_suggestions": 320,
    "total_tool_calls": 180
  }
}
```

##### Execute Component Action
```http
POST /api/developer/components/{component_id}/{action}
```

Example:
```http
POST /api/developer/components/plugin_weather/restart
```

Response:
```json
{
  "success": true,
  "message": "Plugin weather restarted successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## AG-UI Integration

### Data Grids

The developer tools use AG-Grid for displaying component data with advanced features:

- **Sorting and Filtering**: Multi-column sorting and filtering
- **Custom Cell Renderers**: Rich visual components for status, health, and metrics
- **Real-time Updates**: Live data refresh with smooth animations
- **Export Capabilities**: Export data to CSV, Excel, and PDF formats

### Charts and Visualizations

AG Charts provide real-time visualizations:

- **Performance Metrics**: Response time, success rate, and resource usage
- **System Health**: Component health trends over time
- **Chat Analytics**: Message volume, AI suggestions, and user satisfaction

### Theming

The interface supports both light and dark themes with consistent styling across all AG-UI components.

## CopilotKit Integration

### AI Assistant Features

The developer tools include CopilotKit-powered AI assistance:

#### Component Analysis
```typescript
// Ask the AI to analyze component health
"Analyze my component health and suggest improvements"
```

#### Code Generation
```typescript
// Generate boilerplate code
"Generate a new plugin for weather data with chat integration"
```

#### Optimization Suggestions
```typescript
// Get optimization recommendations
"How can I optimize the performance of my weather plugin?"
```

### Available Actions

The AI assistant can help with:

1. **analyzeComponentHealth**: Analyze system component health
2. **optimizeComponent**: Get optimization suggestions for specific components
3. **generateComponentCode**: Generate boilerplate code for new components

### Usage Examples

```typescript
// In the web UI, you can ask:
"Show me all components with low success rates"
"Generate a new extension for email integration"
"What's causing the high response times in my chat system?"
```

## Component Types

### Plugins
- **Status**: Active, Inactive, Error
- **Metrics**: Execution count, success rate, response time
- **Actions**: Restart, Configure, Enable/Disable

### Extensions
- **Status**: Active, Inactive, Loading, Error
- **Health**: Green, Yellow, Red
- **Resources**: Memory usage, CPU usage, uptime
- **Actions**: Reload, Enable, Disable, Remove

### Hooks
- **Execution**: Count, failures, duration
- **Status**: Enabled, Disabled
- **Actions**: Toggle, Configure

### LLM Providers
- **Integration**: OpenAI, Anthropic, LlamaCpp, Gemini
- **Metrics**: Response time, token usage, success rate
- **Actions**: Test, Configure, Switch

## Development Workflow

### 1. Component Development

```bash
# Generate boilerplate
python scripts/kari_dev_cli.py generate plugin my_plugin --features chat_integration

# Edit the generated code
# Test the component
# Deploy and monitor
```

### 2. Monitoring and Debugging

```bash
# Check system health
python scripts/kari_dev_cli.py list

# View detailed metrics
python scripts/kari_dev_cli.py metrics

# Debug specific component
python scripts/kari_dev_cli.py show my_plugin
```

### 3. Performance Optimization

1. Use the web UI to identify performance bottlenecks
2. Ask the AI assistant for optimization suggestions
3. Apply improvements and monitor results
4. Use A/B testing for performance comparisons

## Configuration

### Environment Variables

```bash
# API Configuration
KARI_API_URL=http://localhost:8000
KARI_DEV_TOKEN=your_api_token

# Feature Flags
ENABLE_DEVELOPER_TOOLS=true
ENABLE_AI_ASSISTANT=true
ENABLE_METRICS_COLLECTION=true
```

### Settings

```json
{
  "developer_tools": {
    "enabled": true,
    "refresh_interval": 30,
    "max_metrics_history": 1000,
    "ai_assistant": {
      "enabled": true,
      "model": "gpt-4",
      "max_suggestions": 5
    },
    "ui": {
      "theme": "auto",
      "grid_page_size": 50,
      "chart_animation": true
    }
  }
}
```

## Security

### Authentication

All developer API endpoints require authentication:

```http
Authorization: Bearer your_jwt_token
```

### Authorization

Component actions require admin role:

```json
{
  "user_id": "developer_user",
  "roles": ["admin"],
  "permissions": ["component_management", "system_monitoring"]
}
```

### Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Component List**: 60 requests/minute
- **Metrics**: 30 requests/minute  
- **Actions**: 10 requests/minute

## Troubleshooting

### Common Issues

#### 1. Components Not Loading
```bash
# Check API connectivity
curl http://localhost:8000/api/developer/components

# Verify authentication
python scripts/kari_dev_cli.py list --token your_token
```

#### 2. Metrics Not Updating
- Ensure metrics collection is enabled
- Check system resources
- Verify database connectivity

#### 3. AI Assistant Not Responding
- Check CopilotKit configuration
- Verify API keys
- Review rate limits

### Debug Mode

Enable debug mode for detailed logging:

```bash
export KARI_DEBUG=true
export LOG_LEVEL=DEBUG
```

## Contributing

### Adding New Component Types

1. Update the `KariDevStudioAPI` class
2. Add new column definitions for AG-Grid
3. Implement action handlers
4. Add tests
5. Update documentation

### Extending AI Capabilities

1. Add new CopilotKit actions
2. Update the AI context
3. Test with various prompts
4. Document new capabilities

## Best Practices

### Performance
- Use pagination for large datasets
- Implement efficient filtering
- Cache frequently accessed data
- Monitor resource usage

### User Experience
- Provide clear visual feedback
- Use consistent terminology
- Implement progressive disclosure
- Support keyboard navigation

### Monitoring
- Track component health continuously
- Set up alerts for critical issues
- Monitor performance trends
- Regular health checks

## Future Enhancements

### Planned Features
- **Visual Component Editor**: Drag-and-drop component configuration
- **Advanced Analytics**: Machine learning-powered insights
- **Collaborative Development**: Multi-user development environment
- **Integration Testing**: Automated component testing framework

### Roadmap
- Q1 2024: Visual editor and advanced analytics
- Q2 2024: Collaborative features and testing framework
- Q3 2024: Mobile developer app
- Q4 2024: Enterprise features and advanced security

## Support

For support with the developer tools:

1. Check the troubleshooting section
2. Review the API documentation
3. Ask the AI assistant for help
4. Contact the development team

## License

The Kari Developer Tools are part of the Kari AI platform and are subject to the same licensing terms.