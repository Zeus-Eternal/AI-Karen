# Error Response Service AI Integration

This document describes the AI integration implemented in the Error Response Service as part of task 7 of the session-persistence-premium-response specification.

## Overview

The Error Response Service has been enhanced with AI orchestrator integration to provide intelligent error analysis and guidance generation. This integration leverages Karen's core LLM capabilities to analyze complex errors and provide actionable responses.

## Key Features

### 1. AI-Powered Error Analysis

The service can now analyze unclassified errors using AI when rule-based classification fails:

```python
# AI analysis for complex errors
response = service.analyze_error(
    error_message="Complex multi-service authentication chain failure",
    use_ai_analysis=True
)
```

### 2. Response Enhancement

Rule-based responses can be enhanced with AI-generated insights:

```python
# Enhanced response with AI insights
enhanced_response = service._enhance_response_with_ai(base_response, context)
```

### 3. Intelligent Prompt Templates

The service generates structured prompts for LLM analysis:

```python
# Generate analysis prompt with context
prompt = service._build_error_analysis_prompt(context, analysis_context)
```

## Implementation Details

### AI Component Integration

The service integrates with three key AI components:

1. **AI Orchestrator**: Coordinates AI processing workflows
2. **LLM Router**: Routes requests to appropriate LLM providers
3. **LLM Utils**: Provides utilities for LLM interaction

All components are lazily initialized to avoid circular dependencies:

```python
def _get_ai_orchestrator(self):
    """Lazily initialize AI orchestrator to avoid circular imports."""
    if self._ai_orchestrator is None:
        try:
            from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
            from ai_karen_engine.core.services.base import ServiceConfig
            config = ServiceConfig(name="error_response_ai_orchestrator")
            self._ai_orchestrator = AIOrchestrator(config)
            self._ai_orchestrator._initialized = True
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI orchestrator: {e}")
            self._ai_orchestrator = None
    return self._ai_orchestrator
```

### Context Enrichment

The service enriches error context with provider health and system status:

```python
def _build_error_analysis_context(self, context: ErrorContext) -> Dict[str, Any]:
    """Build comprehensive context for AI error analysis"""
    analysis_context = {
        "timestamp": context.timestamp.isoformat() if context.timestamp else None,
        "provider_health": {},
        "system_status": "operational",
        "alternative_providers": []
    }
    
    # Add provider health information
    if context.provider_name:
        provider_health = self._get_provider_health(context.provider_name)
        if provider_health:
            analysis_context["provider_health"] = {
                "name": provider_health.name,
                "status": provider_health.status.value,
                "success_rate": provider_health.success_rate,
                "response_time": provider_health.response_time,
                "error_message": provider_health.error_message,
                "last_check": provider_health.last_check.isoformat() if provider_health.last_check else None
            }
    
    return analysis_context
```

### Prompt Template Design

The AI analysis prompt follows a structured format:

```python
def _build_error_analysis_prompt(self, context: ErrorContext, analysis_context: Dict[str, Any]) -> str:
    """Build prompt for AI error analysis"""
    return f"""You are Karen's intelligent error analysis system. Analyze the following error and provide actionable guidance.

Error Details:
- Message: {context.error_message}
- Type: {context.error_type or 'Unknown'}
- Status Code: {context.status_code or 'N/A'}
- Provider: {context.provider_name or 'N/A'}

Provider Information:
- Status: {provider_health.get('status', 'unknown')}
- Success Rate: {provider_health.get('success_rate', 'unknown')}%
- Alternative Providers: {', '.join(analysis_context.get('alternative_providers', []))}

Your task is to provide a helpful, actionable response in JSON format:
{{
    "title": "Brief, user-friendly error title",
    "summary": "Clear explanation of what went wrong",
    "category": "error category",
    "severity": "error severity",
    "next_steps": ["2-4 specific, actionable steps"],
    "contact_admin": false,
    "retry_after": null,
    "technical_details": "Brief technical context"
}}

Guidelines:
- Be specific and actionable
- Limit next_steps to 2-4 concrete actions
- Use helpful, direct tone without jargon
- If provider is down, suggest alternatives
- Set contact_admin to true only for critical system issues
"""
```

### Response Validation

AI-generated responses are validated for quality:

```python
def validate_response_quality(self, response: IntelligentErrorResponse) -> bool:
    """Validate that an error response meets quality standards"""
    # Check title quality
    if not response.title or len(response.title.strip()) < 5:
        return False
    
    # Check summary quality
    if not response.summary or len(response.summary.strip()) < 10:
        return False
    
    # Ensure next steps are actionable
    action_words = ["add", "check", "verify", "try", "contact", "update", "restart", "wait", "use", "configure"]
    actionable_steps = sum(1 for step in response.next_steps 
                          if any(word in step.lower() for word in action_words))
    
    return actionable_steps > 0
```

## Usage Examples

### Basic AI Analysis

```python
service = ErrorResponseService()

# Analyze complex error with AI
response = service.analyze_error(
    error_message="Authentication chain failure: OAuth token validation failed with service unavailable",
    error_type="AuthenticationChainError",
    status_code=503,
    use_ai_analysis=True
)

print(f"AI Analysis: {response.title}")
print(f"Category: {response.category.value}")
print(f"Next Steps: {response.next_steps}")
```

### Response Enhancement

```python
# Get rule-based response
base_response = service.analyze_error(
    error_message="Rate limit exceeded",
    provider_name="OpenAI",
    use_ai_analysis=False
)

# Enhance with AI insights
enhanced_response = service.analyze_error(
    error_message="Rate limit exceeded",
    provider_name="OpenAI",
    use_ai_analysis=True
)

print(f"Enhanced: {enhanced_response.title}")
print(f"AI Insights: {enhanced_response.technical_details}")
```

## Error Handling and Fallbacks

The integration includes robust error handling:

1. **Graceful Degradation**: If AI components fail, falls back to rule-based classification
2. **Timeout Handling**: LLM requests have appropriate timeouts
3. **JSON Parsing**: Robust parsing of AI responses with validation
4. **Quality Validation**: Ensures AI responses meet quality standards

```python
def _generate_ai_error_response(self, context: ErrorContext) -> Optional[IntelligentErrorResponse]:
    """Generate an AI-powered error response for unclassified errors"""
    try:
        llm_router = self._get_llm_router()
        llm_utils = self._get_llm_utils()
        
        if not llm_router or not llm_utils:
            self.logger.warning("LLM components not available for AI error analysis")
            return None
        
        # Generate AI analysis
        ai_response = llm_router.invoke(
            llm_utils,
            analysis_prompt,
            task_intent="analysis",
            preferred_provider="openai",
            preferred_model="gpt-3.5-turbo"
        )
        
        if ai_response and ai_response.strip():
            parsed_response = self._parse_ai_error_response(ai_response, context)
            if parsed_response and self.validate_response_quality(parsed_response):
                return parsed_response
        
        return None
        
    except Exception as e:
        self.logger.error(f"AI error analysis failed: {e}")
        return None
```

## Testing

Comprehensive tests cover all AI integration features:

### Unit Tests (`tests/test_error_response_ai_integration.py`)

- AI component lazy initialization
- AI error analysis with valid/invalid responses
- Response enhancement
- JSON parsing with code blocks
- Quality validation
- Error handling and fallbacks

### Integration Tests (`tests/test_error_response_ai_orchestrator_integration.py`)

- AI orchestrator integration
- Prompt template generation
- Context enrichment
- Provider health integration
- Metrics collection

### Test Coverage

```bash
# Run AI integration tests
python -m pytest tests/test_error_response_ai_integration.py -v

# Run AI orchestrator integration tests  
python -m pytest tests/test_error_response_ai_orchestrator_integration.py -v

# Run existing error response tests
python -m pytest tests/test_error_response_service.py -v
```

## Metrics and Monitoring

The service provides metrics for AI integration:

```python
def get_ai_analysis_metrics(self) -> Dict[str, Any]:
    """Get metrics about AI analysis usage and quality"""
    return {
        "ai_analysis_enabled": self._get_llm_router() is not None,
        "ai_orchestrator_available": self._get_ai_orchestrator() is not None,
        "llm_utils_available": self._get_llm_utils() is not None,
        "total_classification_rules": len(self.classification_rules)
    }
```

## Configuration

AI analysis can be enabled/disabled per request:

```python
# Enable AI analysis (default)
response = service.analyze_error(error_message, use_ai_analysis=True)

# Disable AI analysis (rule-based only)
response = service.analyze_error(error_message, use_ai_analysis=False)
```

## Performance Considerations

1. **Lazy Loading**: AI components are only loaded when needed
2. **Caching**: Provider health information is cached
3. **Timeouts**: LLM requests have appropriate timeouts
4. **Fallback**: Quick fallback to rule-based responses if AI fails
5. **Validation**: Response quality validation prevents poor AI outputs

## Security Considerations

1. **Input Sanitization**: Error messages are sanitized before sending to LLM
2. **Output Validation**: AI responses are validated and sanitized
3. **Provider Selection**: Uses trusted LLM providers (OpenAI by default)
4. **Error Handling**: No sensitive information leaked in error messages

## Future Enhancements

1. **Response Caching**: Cache AI responses for common error patterns
2. **Learning**: Learn from user feedback to improve responses
3. **Multi-language**: Support for error analysis in multiple languages
4. **Custom Models**: Support for fine-tuned models for specific error types
5. **Batch Processing**: Batch multiple errors for efficient processing

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **3.1**: AI analysis using Karen's core LLM brain
- **3.3**: LLM prompt templates for error analysis and guidance generation  
- **3.7**: Context enrichment with provider status and error metadata
- **4.3**: Response validation to ensure actionable guidance format

The integration provides intelligent, context-aware error responses that help users understand and resolve issues more effectively.