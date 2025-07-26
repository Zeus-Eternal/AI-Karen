# Weather Plugin Integration Dev Sheet

A comprehensive guide to merge Karen’s backend business logic with the Web UI’s front-end weather plugin, ensuring seamless weather forecasts in the UI.

---

## 1. Overview

* **Goal:** User queries like “What’s the weather in Detroit?” automatically trigger backend weather lookup and render a rich forecast widget on the front-end.
* **Components:**

  * **DecisionEngine**: Detects weather intent and selects the `getWeather` tool.
  * **AIOrchestrator**: Orchestrates flow and returns a `FlowOutput` indicating a plugin call.
  * **Web UI**: React component that renders the forecast widget based on backend response.

---

## 2. Architecture Diagram

```
User → Frontend Chat Component → HTTP POST /api/chat/process → AIOrchestrator
   ↓                            ↓                          ↓
   Forecast Widget Logic ← FlowManager → DecisionEngine → getWeather Tool
```

---

## 3. Backend Implementation

### 3.1. DecisionEngine: Intent & Tool Mapping

```python
# decision_engine.py
def analyze_intent(self, prompt: str, context: ...):
    if "weather" in prompt.lower():
        return {
            "primary_intent": "weather_query",
            "confidence": 0.8,
            "entities": [{"type": "location", "value": extract_location(prompt)}],
            "suggested_tools": [ToolType.GET_WEATHER.value]
        }
```

### 3.2. AIOrchestrator: Handling Weather Tool

```python
# ai_orchestrator.py
async def _handle_decide_action_flow(...):
    result = await self.decision_engine.decide_action(...)
    return FlowOutput(
        response=result.intermediate_response,
        requires_plugin=(result.tool_to_call != ToolType.NONE),
        tool_to_call=result.tool_to_call,
        tool_input=result.tool_input)
```

### 3.3. API Route: Dispatch Weather Plugin

```python
# api/routes/chat.py
@router.post("/chat/process")
async def chat_process(request):
    flow_out = await ai_orchestrator.process_flow(...)
    if flow_out.requires_plugin and flow_out.tool_to_call == ToolType.GET_WEATHER:
        weather_src = await web.run({
            "weather":[{"location":flow_out.tool_input.location}]
        })
        return ChatResponse(
            content=flow_out.intermediate_response,
            widget=f"forecast{weather_src.ref_id}"
        )
    return ChatResponse(content=flow_out.response)
```

---

## 4. Front-End Implementation

### 4.1. React ForecastWidget Component

```jsx
// components/ForecastWidget.jsx
import React from 'react';
export function ForecastWidget({ refId }) {
  return (
    <div className="forecast-widget">
      {/* The UI framework will render the forecast based on refId */}
      <Forecast refId={refId} />
    </div>
  );
}
```

### 4.2. ChatMessage Renderer

```jsx
// components/ChatMessage.jsx
import { ForecastWidget } from './ForecastWidget';
export function ChatMessage({ message, widget }) {
  return (
    <div className="chat-message">
      <p>{message}</p>
      {widget && <ForecastWidget refId={widgetRefId(widget)} />}
    </div>
  );
}
```

### 4.3. Utility to Parse Widget Tags

```js
// lib/utils.js
export function widgetRefId(tag) {
  // tag == "forecastturn123forecast0"
  return tag.match(/forecast(.*?)/)[1];
}
```

---

## 5. Matching Web UI Features

* **Styling:** Use existing `.forecast-widget` CSS for card layout, icons, and typography.
* **Interactivity:** Allow click-to-expand hourly/daily view.
* **Fallback:** If no plugin, show plain text response.

---

## 6. Testing

1. **Unit Tests** for `DecisionEngine` intent detection.
2. **Integration Test**: Mock `/api/chat/process` with weather query, assert widget in response.
3. **UI Test**: Render `ChatMessage` with widget tag and verify forecast display.

---
This update the current UI, extracting the weather business logic as plugin and use the current ui as is, while using plugin implementation

