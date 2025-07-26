# Weather Plugin Developer Sheet

This quick reference explains how to enable and use Karen's built‑in `getWeather` tool so weather related queries automatically produce a forecast widget.

## 1. Prerequisites

- Ensure the tool is registered under `ToolType.GET_WEATHER` in `DecisionEngine._initialize_default_tools`.
- Add a decision rule so weather‑related intents map to `ToolType.GET_WEATHER`.
- Verify `AIOrchestrator` and `FlowManager` include the `DECIDE_ACTION` flow.
- The FastAPI endpoint `/api/chat/process` should invoke the decide‑action flow.

## 2. Intent Analysis

```python
# DecisionEngine.analyze_intent()
if any(word in prompt_lower for word in ["weather", "temperature", "rain", "sunny"]):
    intent_analysis = {
        "primary_intent": "weather_query",
        "confidence": 0.8,
        "entities": [{"type": "location", "value": city}],  # extracted elsewhere
        "suggested_tools": [ToolType.GET_WEATHER.value]
    }
```

## 3. Decision Flow

1. **Client** sends POST `/api/chat/process`:
   ```jsonc
   {
     "message": "What's the weather in Detroit?",
     "conversation_history": [...],
     "relevant_memories": [...],
     "user_settings": { ... }
   }
   ```
2. **AIOrchestrator** → **FlowManager** → `DECIDE_ACTION` → `DecisionEngine.decide_action`.
3. `decide_action` detects `GET_WEATHER` and builds `ToolInput(location="Detroit")`.
4. Returns `FlowOutput` with
   ```python
   tool_to_call = ToolType.GET_WEATHER
   tool_input = ToolInput(location="Detroit")
   intermediate_response = "Let me check the weather for Detroit..."
   ```
5. The API route sees `requires_plugin=True` and calls the weather tool.

## 4. Calling the Plugin

Inside `/api/chat/process` detect:

```python
if flow_output.requires_plugin and flow_output.tool_to_call == ToolType.GET_WEATHER:
    weather_resp = await web.run({
        "weather": [{
            "location": flow_output.tool_input.location,
            "start": None,
            "duration": None
        }]
    })
    return {"widget": ""}
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

When the user asks:

> **User:** What's the weather in Detroit?

Karen replies with a short acknowledgement and a forecast widget showing the results.
