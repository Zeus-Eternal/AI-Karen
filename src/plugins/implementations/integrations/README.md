# Third-Party Integration Plugins

This directory contains plugins that integrate with external services and APIs.

## Available Integration Plugins

### `gmail/`
Gmail integration for email functionality.

### `weather/`
Weather service integration for weather queries.

### `search/`
Search provider integrations for web search capabilities.

### `yelp/`
Yelp API integration for business and location information.

## Plugin Categories

Integration plugins typically:
- Connect to external APIs
- Handle authentication with third-party services
- Transform data between system and external formats
- Provide caching for external data
- Handle rate limiting and quotas

## Development Guidelines

Integration plugins should:
- Implement robust error handling for network issues
- Use secure authentication methods
- Respect API rate limits and quotas
- Cache data appropriately to reduce API calls
- Provide clear error messages for users
- Handle service outages gracefully
- Follow each service's terms of use