# Weather Plugin Developer Sheet

This short guide explains how to wire Karen's built-in `getWeather` tool so that chat messages like "What’s the weather in Detroit" return a forecast widget.

## 1. Prerequisites

- Ensure `ToolType.GET_WEATHER` is registered in `DecisionEngine._initialize_default_tools`.
- Add an intent rule in `DecisionEngine.analyze_intent` that suggests this tool when the prompt mentions weather terms.
- Route chat requests through `AIOrchestrator` and `FlowManager` using `FlowType.DECIDE_ACTION`.
- Expose the FastAPI route `/api/chat/process` which calls the decide-action flow.

## 2. Intent Analysis Example

```python
# in DecisionEngine.analyze_intent()
if any(word in prompt_lower for word in ["weather", "temperature", "rain", "sunny"]):
    intent_analysis = {
        "primary_intent": "weather_query",
        "confidence": 0.8,
        "entities": [{"type": "location", "value": city}],  # extracted elsewhere
        "suggested_tools": [ToolType.GET_WEATHER.value]
    }
```

## 3. Decision Flow

1. **Client request** to `/api/chat/process`:
   ```jsonc
   {
     "message": "What's the weather in Detroit?",
     "conversation_history": [...],
     "relevant_memories": [...],
     "user_settings": { ... }
   }
   ```
2. **AIOrchestrator** → **FlowManager** → `FlowType.DECIDE_ACTION` → `DecisionEngine.decide_action`.
3. The engine builds `ToolInput(location="Detroit")` and returns:
   ```python
   FlowOutput(
       tool_to_call=ToolType.GET_WEATHER,
       tool_input=ToolInput(location="Detroit"),
       intermediate_response="Let me check the weather for Detroit..."
   )
   ```
4. Because `requires_plugin=True`, the API handler invokes the weather tool.

## 4. Calling the Weather Plugin

Within the `/api/chat/process` endpoint (or plugin dispatcher):

```python
if flow_output.requires_plugin and flow_output.tool_to_call == ToolType.GET_WEATHER:
    weather_resp = await web.run({
        "weather": [{
            "location": flow_output.tool_input.location,
            "start": None,
            "duration": None
        }]
    })
    return ChatResponse(
        content=flow_output.intermediate_response,
        widget=""  # render the weather forecast here
    )
```

## 5. Example Stub

```python
@router.post("/chat/process")
async def chat_process(request: ChatRequest):
    flow_in = FlowInput(
        prompt=request.message,
        conversation_history=request.conversation_history,
        user_settings=request.user_settings,
    )
    flow_out = await ai_orchestrator.process_flow(FlowType.DECIDE_ACTION, flow_in)

    if flow_out.requires_plugin and flow_out.tool_to_call == ToolType.GET_WEATHER:
        weather_src = await web.run({
            "weather": [{"location": flow_out.tool_input.location}]
        })
        return ChatResponse(
            content=flow_out.intermediate_response,
            widget=""
        )

    return ChatResponse(content=flow_out.response)
```

## 6. UI Result

A user asking **“What’s the weather in Detroit?”** receives:

```markdown
Let me check the weather for Detroit...
```

which the UI renders as a forecast widget.
