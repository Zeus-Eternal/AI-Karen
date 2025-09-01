# LLM Fallback Hierarchy Implementation

## Overview

This document describes the implementation of a proper LLM response fallback hierarchy in the AI Karen system. The system now follows the correct order:

1. **User's chosen LLM** (e.g., Llama)
2. **System default LLMs** if user choice fails
3. **Hardcoded responses** as final fallback

## Problem Statement

The original system was missing the proper LLM provider selection based on user preferences. Users expected their chosen LLM (like Llama) to be used first, with fallbacks to system defaults and finally hardcoded responses.

## Solution Architecture

### Frontend Changes

#### 1. ChatInterface Component (`ui_launchers/web_ui/src/components/chat/ChatInterface.tsx`)
- Updated to pass user's LLM preferences to the backend
- Extracts `preferredLLMProvider` and `preferredModel` from user preferences
- Passes these preferences in the `processUserMessage` options

```typescript
const result = await chatService.processUserMessage(
  content,
  messages.filter((m) => m.role !== 'system'),
  settings,
  {
    userId: user?.user_id,
    sessionId: sessionId || undefined,
    storeInMemory: true,
    generateSummary: messages.length > 10,
    // Pass user's LLM preferences for proper fallback hierarchy
    preferredLLMProvider: user?.preferences?.preferredLLMProvider || 'llamacpp',
    preferredModel: user?.preferences?.preferredModel || 'llama3.2:latest',
  },
);
```

#### 2. Chat Service (`ui_launchers/web_ui/src/services/chatService.ts`)
- Updated `ProcessMessageOptions` interface to include LLM preferences
- Modified `processUserMessage` to pass LLM preferences to backend

```typescript
export interface ProcessMessageOptions {
  userId?: string;
  sessionId?: string;
  storeInMemory?: boolean;
  generateSummary?: boolean;
  preferredLLMProvider?: string;
  preferredModel?: string;
}
```

#### 3. Karen Backend (`ui_launchers/web_ui/src/lib/karen-backend.ts`)
- Updated `processUserMessage` method to accept LLM preferences
- Passes LLM preferences to the backend API call

```typescript
async processUserMessage(
  message: string,
  conversationHistory: ChatMessage[],
  settings: KarenSettings,
  userId?: string,
  sessionId?: string,
  llmPreferences?: {
    preferredLLMProvider?: string;
    preferredModel?: string;
  }
): Promise<HandleUserMessageResult>
```

### Backend Changes

#### 1. API Routes (`src/ai_karen_engine/api_routes/ai_orchestrator_routes.py`)
- Updated `ConversationProcessingRequest` model to include LLM preferences
- Modified conversation processing endpoint to pass LLM preferences to context

```python
class ConversationProcessingRequest(BaseModel):
    # ... existing fields ...
    llm_preferences: Optional[Dict[str, str]] = Field(
        None, description="User's LLM preferences for fallback hierarchy"
    )
```

#### 2. AI Orchestrator (`src/ai_karen_engine/services/ai_orchestrator/ai_orchestrator.py`)
- Updated `_process_conversation_with_memory` method to implement proper fallback hierarchy
- Extracts LLM preferences from context
- Implements three-tier fallback system

```python
async def _process_conversation_with_memory(
    self, input_data: FlowInput, context: Dict[str, Any]
) -> str:
    """Process conversation using LLM with memory/context awareness and proper LLM fallback hierarchy."""
    
    # Extract LLM preferences from context
    llm_preferences = input_data.context.get("llm_preferences", {}) if input_data.context else {}
    preferred_provider = llm_preferences.get("preferred_llm_provider", "llamacpp")
    preferred_model = llm_preferences.get("preferred_model", "llama3.2:latest")
    
    # Step 1: Try user's chosen LLM
    # Step 2: Try system default LLMs
    # Step 3: Use hardcoded fallback response
```

#### 3. Chat Orchestrator (`src/ai_karen_engine/chat/chat_orchestrator.py`)
- Updated `_generate_ai_response_enhanced` method to implement fallback hierarchy
- Added helper methods `_try_user_chosen_llm` and `_try_system_default_llms`
- Extracts user preferences from processing context metadata

```python
async def _generate_ai_response_enhanced(
    self,
    message: str,
    parsed_message: ParsedMessage,
    embeddings: List[float],
    integrated_context: Optional[Any],
    active_instructions: List[Any],
    processing_context: ProcessingContext
) -> str:
    """Generate AI response using enhanced context integration and instruction following with proper LLM fallback hierarchy."""
    
    # Get user preferences from processing context
    user_llm_choice = processing_context.metadata.get('preferred_llm_provider', 'llamacpp')
    user_model_choice = processing_context.metadata.get('preferred_model', 'llama3.2:latest')
    
    # Step 1: Try user's chosen LLM
    # Step 2: Try system default LLMs
    # Step 3: Use hardcoded fallback response
```

#### 4. LLM Router (`src/ai_karen_engine/integrations/llm_router.py`)
- Updated `invoke` method to accept `preferred_provider` and `preferred_model` parameters
- Passes preferred model to `llm_utils.generate_text`

```python
def invoke(self, llm_utils, prompt: str, task_intent: str, preferred_provider: Optional[str] = None, preferred_model: Optional[str] = None, **kwargs) -> str:
    # Use preferred provider if specified, otherwise use profile-based selection
    if preferred_provider:
        provider = preferred_provider
        logging.info(f"Using preferred provider: {provider}")
    else:
        provider = self.select_provider(task_intent)
    
    # Pass preferred model if specified
    if preferred_model:
        kwargs['model'] = preferred_model
        logging.info(f"Using preferred model: {preferred_model}")
```

## Fallback Hierarchy Implementation

### Level 1: User's Chosen LLM
- Uses the user's `preferredLLMProvider` and `preferredModel` from their profile
- Default: `llamacpp:llama3.2:latest`
- Logs success/failure for debugging

### Level 2: System Default LLMs
- Tries multiple system default providers in priority order:
  1. `llamacpp:llama3.2:latest` (primary system default)
  2. `openai:gpt-3.5-turbo`
  3. `gemini:gemini-1.5-flash`
  4. `deepseek:deepseek-chat`
  5. `huggingface:distilbert-base-uncased`
- Falls back to generic routing if specific models fail

### Level 3: Hardcoded Fallback Response
- Uses the existing `_generate_enhanced_fallback_response` method
- Provides contextual responses based on parsed message and context
- Acknowledges instructions and provides helpful fallback text

## Data Flow

1. **Frontend**: User preferences → Chat Interface → Chat Service → Karen Backend
2. **Backend API**: Request → AI Orchestrator Routes → Flow Input with LLM preferences
3. **AI Orchestrator**: Flow Input → Conversation Processing → LLM Router with preferences
4. **LLM Router**: Preferred provider/model → LLM Utils → Response
5. **Fallback**: If any step fails, try next level in hierarchy

## Error Handling

- Each level of the hierarchy has proper exception handling
- Failures are logged with appropriate log levels (warning for expected failures, error for unexpected)
- System gracefully degrades through the fallback levels
- Final fallback always provides a meaningful response to the user

## Testing

A test script (`test_llm_fallback_hierarchy.py`) has been created to verify the implementation:

```bash
python test_llm_fallback_hierarchy.py
```

The test demonstrates:
- Chat orchestrator with user LLM preferences
- AI orchestrator with LLM preferences in context
- Fallback level documentation and verification

## Configuration

Users can configure their LLM preferences through:
- **Web UI**: Profile settings page
- **User Preferences**: `preferredLLMProvider` and `preferredModel` fields
- **API**: Direct specification in request context

## Benefits

1. **User Control**: Users get their preferred LLM (like Llama) as first choice
2. **Reliability**: System gracefully falls back if preferred LLM is unavailable
3. **Consistency**: Always provides a response, even if all LLMs fail
4. **Transparency**: Clear logging shows which LLM was used or why fallback occurred
5. **Flexibility**: Easy to add new providers or change fallback order

## Future Enhancements

1. **Dynamic Provider Discovery**: Automatically detect available LLM providers
2. **Performance-Based Fallback**: Use response time and success rate for provider selection
3. **User Feedback Integration**: Learn from user preferences and adjust fallback order
4. **Provider Health Monitoring**: Proactively disable failing providers
5. **Custom Fallback Rules**: Allow users to define their own fallback sequences

## Conclusion

The LLM fallback hierarchy implementation ensures that users get their preferred LLM experience while maintaining system reliability through proper fallback mechanisms. The system now correctly follows the expected order: User's choice → System defaults → Hardcoded responses.