"""
Chat service for Kari AI Streamlit Console
"""

import time
import streamlit as st
import re
from datetime import datetime

def process_user_input(input_text):
    """Process user input and generate response"""
    # Add user message to conversation
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': input_text,
        'timestamp': datetime.now().isoformat()
    })
    
    # Simulate processing and response
    with st.spinner("Thinking..."):
        # This would be replaced with actual backend call
        response, metadata = simulate_backend_call(input_text)
    
    # Add assistant response to conversation
    st.session_state.conversation_history.append({
        'role': 'assistant',
        'content': response,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata
    })

# Simulate backend call (placeholder for actual implementation)
def simulate_backend_call(user_input: str) -> tuple[str, dict]:
    """Simulate a backend call to Kari AI"""
    # Simulate processing time
    time.sleep(0.5)
    
    # Normalize input for processing
    normalized_input = user_input.lower().strip()
    
    # Get current model and settings
    current_model = st.session_state.current_model
    reasoning_mode = st.session_state.reasoning_mode
    active_plugins = st.session_state.active_plugins
    
    # Model-specific response patterns
    model_responses = {
        "llama-cpp": {
            "greeting": "Hello! I'm Kari, running locally on llama-cpp. How can I assist you today?",
            "help": "I can help you with various tasks. As a local model, I prioritize your privacy and can work offline.",
            "joke": "Why don't programmers like nature? It has too many bugs! 🐛",
            "weather": "I don't have real-time weather data, but I can help you understand weather patterns or find weather information online.",
            "factual": "I don't have access to current real-world data, but I can help you find information or explain concepts.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI running locally on llama-cpp."
        },
        "gpt-3": {
            "greeting": "Hello! I'm Kari, powered by GPT-3.5-turbo. I'm here to help with any questions or tasks you might have.",
            "help": "I can assist with a wide range of tasks including writing, analysis, coding, and creative work. What would you like help with?",
            "joke": "Why did AI go to therapy? It had too many layers and couldn't stop overthinking everything! 🤖",
            "weather": "I don't have access to real-time weather data, but I can explain weather concepts or help you find weather information.",
            "factual": "I don't have access to current real-world data, but I can help explain concepts or find information on topics.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by GPT-3.5-turbo."
        },
        "gpt-4": {
            "greeting": "Hello! I'm Kari, powered by GPT-4. I'm here to help with any questions or tasks you might have.",
            "help": "I can assist with a wide range of tasks including writing, analysis, coding, and creative work. What would you like help with?",
            "joke": "Why did AI go to therapy? It had too many layers and couldn't stop overthinking everything! 🤖",
            "weather": "I don't have access to real-time weather data, but I can explain weather concepts or help you find weather information.",
            "factual": "I don't have access to current real-world data, but I can help explain concepts or find information on topics.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by GPT-4."
        },
        "claude-3": {
            "greeting": "Hello! I'm Kari, running on Claude 3. I'm designed to be helpful, harmless, and honest. How can I assist you?",
            "help": "I can help with writing, analysis, math, coding, creative tasks, and more. What would you like assistance with?",
            "joke": "Why don't scientists trust atoms? Because they make up everything! ⚛️",
            "weather": "I don't have access to current weather data, but I can explain meteorological concepts or help you understand weather patterns.",
            "factual": "I don't have access to current real-world information, but I can help explain concepts or provide general knowledge.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by Claude 3."
        }
    }
    
    # Handle math calculations
    math_response = ""
    if any(math_word in normalized_input for math_word in ["calculate", "compute", "math", "+", "-", "*", "/", "=", "sum", "total"]):
        try:
            # Simple math expression evaluator
            import re
            # Extract math expression
            math_expr = re.search(r'(\d+\s*[\+\-\*\/]\s*\d+)', normalized_input)
            if math_expr:
                expr = math_expr.group(1).replace(" ", "")
                # Safely evaluate expression
                result = eval(expr)
                math_response = f"The answer to {expr} is {result}."
        except:
            math_response = "I can help with math problems, but I couldn't understand calculation you asked for."
    
    # Determine response type based on input
    response_type = "default"
    
    # Check for greetings
    if any(greeting in normalized_input for greeting in ["hello", "hi", "hey", "greetings"]):
        response_type = "greeting"
    
    # Check for help requests
    elif any(help_word in normalized_input for help_word in ["help", "assist", "support"]):
        response_type = "help"
    
    # Check for joke requests
    elif any(joke_word in normalized_input for joke_word in ["joke", "funny", "laugh"]):
        response_type = "joke"
    
    # Check for weather questions
    elif any(weather_word in normalized_input for weather_word in ["weather", "temperature", "rain", "sunny", "cloudy"]):
        response_type = "weather"
    
    # Check for math questions
    elif any(math_word in normalized_input for math_word in ["calculate", "compute", "math", "+", "-", "*", "/", "=", "sum", "total"]):
        response_type = "math"
    
    # Check for factual questions
    elif any(factual_word in normalized_input for factual_word in ["who", "what", "where", "when", "why", "how", "president", "capital", "country"]):
        response_type = "factual"
    
    # Get base response based on model and input type
    if response_type == "math" and math_response:
        response = math_response
    else:
        response = model_responses.get(current_model, model_responses["llama-cpp"]).get(response_type, model_responses["llama-cpp"]["default"])
    
    # Add plugin-specific enhancements
    plugin_enhancement = ""
    
    # Memory plugin enhancements
    if active_plugins['memory']:
        if any(memory_word in normalized_input for memory_word in ["remember", "recall", "previous", "again"]):
            plugin_enhancement = " I've checked your memory and found relevant information."
    
    # Search plugin enhancements
    if active_plugins['search']:
        if any(search_word in normalized_input for search_word in ["search", "find", "look up", "information", "current"]):
            plugin_enhancement = " I've performed a search to provide you with most current information."
    
    # Tools plugin enhancements
    if active_plugins['tools']:
        if any(tool_word in normalized_input for tool_word in ["calculate", "compute", "analyze", "math", "=", "+", "-", "*"]):
            plugin_enhancement = " I've used appropriate tools to process your request."
    
    # Combine response with plugin enhancements
    if plugin_enhancement:
        response += plugin_enhancement
    
    # Generate metadata with model-specific details
    response_times = {
        "llama-cpp": 0.65,  # Slower for local model
        "gpt-4": 0.42,     # Fast for cloud model
        "claude-3": 0.38   # Fastest for cloud model
    }
    
    # Generate reasoning steps based on mode
    reasoning_steps = []
    if reasoning_mode != "Off":
        reasoning_steps = [
            "Analyzed user input and intent",
            "Selected appropriate response strategy"
        ]
        
        if active_plugins['memory']:
            reasoning_steps.append("Checked memory for relevant context")
        
        if active_plugins['search']:
            reasoning_steps.append("Performed information search")
        
        if active_plugins['tools']:
            reasoning_steps.append("Applied computational tools")
        
        if reasoning_mode == "Detailed":
            reasoning_steps.extend([
                "Evaluated multiple response options",
                "Optimized for clarity and relevance",
                "Applied safety and quality checks"
            ])
        
        reasoning_steps.append("Generated final response")
    
    # Collect active plugins for metadata
    active_plugins_list = [plugin for plugin, is_active in active_plugins.items() if is_active]
    
    # Generate metadata
    metadata = {
        "model": current_model,
        "response_time": response_times.get(current_model, 0.42),
        "plugins": active_plugins_list,
        "reasoning": {
            "mode": reasoning_mode,
            "steps": reasoning_steps
        },
        "memory_hits": 1 if active_plugins['memory'] else 0,
        "search_results": 3 if active_plugins['search'] else 0,
        "tool_usage": 1 if active_plugins['tools'] else 0
    }
    
    return response, metadata