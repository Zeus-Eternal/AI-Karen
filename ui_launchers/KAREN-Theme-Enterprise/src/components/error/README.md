# Intelligent Error Panel Component

This directory contains the implementation of the Intelligent Error Panel component system, which provides automatic error detection and intelligent response generation for the Karen AI system.

## Components

### IntelligentErrorPanel
The main component that displays intelligent error analysis and actionable guidance to users.

**Features:**
- Automatic error analysis using Karen's AI backend
- User-friendly error messages with specific next steps
- Provider health status integration
- Loading states and fallback messaging
- Retry logic with exponential backoff
- Technical details toggle
- Contact admin functionality
- Caching indicators

**Usage:**
```tsx
import { IntelligentErrorPanel } from '@/components/error';

<IntelligentErrorPanel
  error="OpenAI API key not found"
  errorType="AuthenticationError"
  statusCode={401}
  providerName="openai"
  onRetry={() => console.log('Retry clicked')}
  onDismiss={() => console.log('Dismissed')}
/>
```

### useIntelligentError Hook
A React hook for intelligent error analysis and state management.

**Features:**
- Automatic error detection and analysis
- Debounced API calls to prevent spam
- Retry logic with configurable limits
- Loading and error states
- Cleanup on unmount

**Usage:**
```tsx
import { useIntelligentError } from '@/hooks/use-intelligent-error';

const MyComponent = () => {
  const { analysis, isAnalyzing, analyzeError } = useIntelligentError();
  
  const handleError = (error: Error) => {
    analyzeError(error, {
      provider_name: 'openai',
      request_path: '/api/chat'
    });
  };
  
  return (
    <div>
      {isAnalyzing && <div>Analyzing error...</div>}
      {analysis && <div>{analysis.title}: {analysis.summary}</div>}
    </div>
  );
};
```

### withIntelligentError HOC
A higher-order component that adds automatic error detection to existing components.

**Usage:**
```tsx
import { withIntelligentError } from '@/components/error';

const MyComponent = ({ data, error }) => {
  if (error) throw error;
  return <div>{data}</div>;
};

const EnhancedComponent = withIntelligentError(MyComponent, {
  position: 'top',
  autoShow: true
});
```

## API Integration

The components integrate with the backend error response service at `/api/error-response/analyze` to provide intelligent analysis using Karen's core LLM capabilities.

**Request Format:**
```typescript
{
  error_message: string;
  error_type?: string;
  status_code?: number;
  provider_name?: string;
  request_path?: string;
  user_context?: Record<string, any>;
  use_ai_analysis?: boolean;
}
```

**Response Format:**
```typescript
{
  title: string;
  summary: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  next_steps: string[];
  provider_health?: ProviderHealth;
  contact_admin: boolean;
  retry_after?: number;
  help_url?: string;
  technical_details?: string;
  cached: boolean;
  response_time_ms: number;
}
```

## Error Categories

The system classifies errors into the following categories:
- `authentication` - Login/session issues
- `authorization` - Permission issues
- `api_key_missing` - Missing API keys
- `api_key_invalid` - Invalid API keys
- `rate_limit` - Rate limiting issues
- `provider_down` - Service unavailability
- `network_error` - Connectivity issues
- `validation_error` - Input validation issues
- `database_error` - Database issues
- `system_error` - General system errors
- `unknown` - Unclassified errors

## Examples

See `IntelligentErrorExample.tsx` for comprehensive usage examples including:
- Basic error panel usage
- Hook integration
- API error handling
- Higher-order component usage

## Testing

The components include comprehensive test suites covering:
- Error display and formatting
- User interactions (retry, dismiss, etc.)
- Loading states and error handling
- API integration
- Accessibility features
- Hook functionality and state management

Run tests with:
```bash
npm test -- src/components/error/__tests__/
npm test -- src/hooks/__tests__/use-intelligent-error.test.ts
```

## Requirements Fulfilled

This implementation fulfills the following requirements:

**3.2**: Premium Response System with Core LLM Integration
- ✅ Analyzes errors using Karen's core LLM brain
- ✅ Provides specific next steps and actionable guidance
- ✅ Integrates with provider health monitoring

**3.3**: Error Context and Provider Health Integration
- ✅ Includes current provider health status
- ✅ Suggests alternative providers when needed
- ✅ Differentiates between error types

**3.7**: Intelligent Response Generation
- ✅ Uses helpful, direct tone without technical jargon
- ✅ Limits suggestions to 2-4 concrete next steps
- ✅ Provides specific guidance (e.g., "Add OPENAI_API_KEY to your .env file")

**4.4**: User-Friendly Error Display
- ✅ Automatic error detection and response fetching
- ✅ User-friendly formatting for error messages
- ✅ Loading states and fallback messaging
- ✅ Interactive components for user actions