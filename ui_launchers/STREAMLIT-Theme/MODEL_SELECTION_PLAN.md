# Model Selection and Reasoning Controls Enhancement Plan

## Overview
This document outlines the plan for enhancing model selection and reasoning controls in the Kari AI Lite Streamlit Console. The goal is to provide users with more granular control over model selection and reasoning modes, improving the overall user experience and system flexibility.

## Current State Analysis
The current implementation has basic model selection and reasoning controls:
- Model selection is available in the left sidebar with a simple dropdown
- Reasoning mode has basic options (Off, Standard, Detailed)
- Model information is limited to names without descriptions
- No model-specific parameters or settings
- No model status indicators

## Implementation Plan

### 1. Enhanced Model Selection Interface

#### 1.1 Model Organization
- Group models by type (Local/Cloud)
- Add model descriptions and capabilities
- Implement model search and filtering
- Add model performance indicators

#### 1.2 Model Information Display
- Show model version and size
- Display model capabilities and specialties
- Add model performance metrics
- Show model availability status

#### 1.3 Model-Specific Settings
- Add temperature control
- Implement max tokens setting
- Add top-p and top-k parameters
- Include model-specific advanced options

### 2. Advanced Reasoning Controls

#### 2.1 Reasoning Mode Enhancements
- Add more granular reasoning levels
- Implement custom reasoning presets
- Add reasoning style options
- Include reasoning confidence controls

#### 2.2 Reasoning Visualization
- Add reasoning step display
- Implement reasoning confidence indicators
- Show reasoning time metrics
- Add reasoning export functionality

#### 2.3 Reasoning Persistence
- Save reasoning preferences per user
- Implement reasoning mode presets
- Add reasoning history tracking
- Include reasoning analytics

### 3. Model Status Monitoring

#### 3.1 Model Health Indicators
- Show model availability status
- Add model response time metrics
- Implement model error rate tracking
- Display model load indicators

#### 3.2 Model Performance Metrics
- Show model response time history
- Add model usage statistics
- Implement model cost tracking
- Display model quality metrics

#### 3.3 Model Fallback Mechanism
- Implement automatic model fallback
- Add manual model override
- Include model degradation handling
- Show model selection recommendations

### 4. Implementation Details

#### 4.1 Enhanced Model Configuration

```python
# Model configuration data structure
MODEL_CONFIG = {
    "local": {
        "llama-cpp-7B": {
            "name": "LLaMA-CPP 7B",
            "description": "Fast and efficient local model for general tasks",
            "capabilities": ["text-generation", "question-answering", "code-generation"],
            "parameters": {
                "temperature": {"min": 0.0, "max": 2.0, "default": 0.7, "step": 0.1},
                "max_tokens": {"min": 50, "max": 2048, "default": 512, "step": 50},
                "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05},
                "top_k": {"min": 1, "max": 100, "default": 40, "step": 1}
            },
            "performance": {
                "avg_response_time": 0.65,
                "quality_score": 8.5,
                "cost_per_token": 0.0
            }
        },
        "llama-cpp-13B": {
            "name": "LLaMA-CPP 13B",
            "description": "Higher quality local model with better reasoning",
            "capabilities": ["text-generation", "reasoning", "code-generation", "analysis"],
            "parameters": {
                "temperature": {"min": 0.0, "max": 2.0, "default": 0.7, "step": 0.1},
                "max_tokens": {"min": 50, "max": 2048, "default": 512, "step": 50},
                "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05},
                "top_k": {"min": 1, "max": 100, "default": 40, "step": 1}
            },
            "performance": {
                "avg_response_time": 1.2,
                "quality_score": 9.0,
                "cost_per_token": 0.0
            }
        }
    },
    "cloud": {
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "Fast and capable cloud model for most tasks",
            "capabilities": ["text-generation", "question-answering", "code-generation", "analysis"],
            "parameters": {
                "temperature": {"min": 0.0, "max": 2.0, "default": 0.7, "step": 0.1},
                "max_tokens": {"min": 50, "max": 4096, "default": 1000, "step": 50},
                "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05}
            },
            "performance": {
                "avg_response_time": 0.42,
                "quality_score": 8.8,
                "cost_per_token": 0.002
            }
        },
        "gpt-4": {
            "name": "GPT-4",
            "description": "Most capable cloud model for complex reasoning tasks",
            "capabilities": ["text-generation", "complex-reasoning", "code-generation", "analysis", "creative-writing"],
            "parameters": {
                "temperature": {"min": 0.0, "max": 2.0, "default": 0.7, "step": 0.1},
                "max_tokens": {"min": 50, "max": 8192, "default": 2000, "step": 50},
                "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05}
            },
            "performance": {
                "avg_response_time": 1.8,
                "quality_score": 9.5,
                "cost_per_token": 0.06
            }
        },
        "claude-3-sonnet": {
            "name": "Claude 3 Sonnet",
            "description": "Balanced model with strong reasoning capabilities",
            "capabilities": ["text-generation", "reasoning", "analysis", "creative-writing"],
            "parameters": {
                "temperature": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.1},
                "max_tokens": {"min": 50, "max": 4096, "default": 1000, "step": 50},
                "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05}
            },
            "performance": {
                "avg_response_time": 0.95,
                "quality_score": 9.2,
                "cost_per_token": 0.015
            }
        }
    }
}
```

#### 4.2 Enhanced Model Selection Interface

```python
# Enhanced model selection in left sidebar
def render_enhanced_model_selection():
    st.markdown("#### Model Selection")
    
    # Model type tabs
    model_type = st.radio(
        "Model Type",
        ["Local", "Cloud"],
        horizontal=True,
        key="model_type_selector"
    )
    
    # Model selection
    model_options = []
    model_descriptions = {}
    
    for model_id, config in MODEL_CONFIG[model_type.lower()].items():
        model_options.append(config["name"])
        model_descriptions[config["name"]] = config["description"]
    
    selected_model_name = st.selectbox(
        "Model",
        options=model_options,
        index=0,
        key="model_selector"
    )
    
    # Show model description
    st.caption(model_descriptions.get(selected_model_name, ""))
    
    # Find selected model config
    selected_model_id = None
    for model_id, config in MODEL_CONFIG[model_type.lower()].items():
        if config["name"] == selected_model_name:
            selected_model_id = model_id
            break
    
    if selected_model_id:
        model_config = MODEL_CONFIG[model_type.lower()][selected_model_id]
        
        # Model capabilities
        with st.expander("Capabilities", expanded=False):
            for capability in model_config["capabilities"]:
                st.markdown(f"- {capability}")
        
        # Model parameters
        with st.expander("Parameters", expanded=False):
            # Initialize model parameters in session state if not exists
            if 'model_parameters' not in st.session_state:
                st.session_state.model_parameters = {}
            
            if selected_model_id not in st.session_state.model_parameters:
                st.session_state.model_parameters[selected_model_id] = {}
                for param, config in model_config["parameters"].items():
                    st.session_state.model_parameters[selected_model_id][param] = config["default"]
            
            # Render parameter controls
            for param, config in model_config["parameters"].items():
                if param == "max_tokens":
                    st.session_state.model_parameters[selected_model_id][param] = st.slider(
                        param,
                        min_value=config["min"],
                        max_value=config["max"],
                        value=st.session_state.model_parameters[selected_model_id][param],
                        step=config["step"],
                        key=f"{selected_model_id}_{param}"
                    )
                else:
                    st.session_state.model_parameters[selected_model_id][param] = st.slider(
                        param,
                        min_value=config["min"],
                        max_value=config["max"],
                        value=st.session_state.model_parameters[selected_model_id][param],
                        step=config["step"],
                        format="%.2f",
                        key=f"{selected_model_id}_{param}"
                    )
        
        # Model performance metrics
        with st.expander("Performance", expanded=False):
            perf = model_config["performance"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Response Time", f"{perf['avg_response_time']}s")
                st.metric("Quality Score", f"{perf['quality_score']}/10")
            with col2:
                cost_text = "Free" if perf["cost_per_token"] == 0 else f"${perf['cost_per_token']}/token"
                st.metric("Cost", cost_text)
        
        # Update session state
        st.session_state.current_model = selected_model_id
        st.session_state.current_model_type = model_type.lower()
```

#### 4.3 Advanced Reasoning Controls

```python
# Advanced reasoning controls
def render_advanced_reasoning_controls():
    st.markdown("#### Reasoning Controls")
    
    # Initialize reasoning settings in session state if not exists
    if 'reasoning_settings' not in st.session_state:
        st.session_state.reasoning_settings = {
            "mode": "Standard",
            "verbosity": "Medium",
            "style": "Analytical",
            "confidence_threshold": 0.7,
            "show_steps": True,
            "save_history": True
        }
    
    # Reasoning mode
    reasoning_modes = ["Off", "Standard", "Detailed", "Expert", "Custom"]
    reasoning_mode = st.selectbox(
        "Reasoning Mode",
        options=reasoning_modes,
        index=reasoning_modes.index(st.session_state.reasoning_settings["mode"]),
        key="reasoning_mode"
    )
    st.session_state.reasoning_settings["mode"] = reasoning_mode
    
    # Show advanced options only if not "Off"
    if reasoning_mode != "Off":
        # Reasoning verbosity
        verbosity_levels = ["Low", "Medium", "High", "Maximum"]
        verbosity = st.selectbox(
            "Verbosity",
            options=verbosity_levels,
            index=verbosity_levels.index(st.session_state.reasoning_settings["verbosity"]),
            key="reasoning_verbosity"
        )
        st.session_state.reasoning_settings["verbosity"] = verbosity
        
        # Reasoning style
        reasoning_styles = ["Analytical", "Creative", "Balanced", "Concise"]
        reasoning_style = st.selectbox(
            "Style",
            options=reasoning_styles,
            index=reasoning_styles.index(st.session_state.reasoning_settings["style"]),
            key="reasoning_style"
        )
        st.session_state.reasoning_settings["style"] = reasoning_style
        
        # Confidence threshold
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.reasoning_settings["confidence_threshold"],
            step=0.05,
            format="%.2f",
            key="confidence_threshold"
        )
        st.session_state.reasoning_settings["confidence_threshold"] = confidence_threshold
        
        # Additional options
        col1, col2 = st.columns(2)
        with col1:
            show_steps = st.checkbox(
                "Show Reasoning Steps",
                value=st.session_state.reasoning_settings["show_steps"],
                key="show_reasoning_steps"
            )
            st.session_state.reasoning_settings["show_steps"] = show_steps
        
        with col2:
            save_history = st.checkbox(
                "Save Reasoning History",
                value=st.session_state.reasoning_settings["save_history"],
                key="save_reasoning_history"
            )
            st.session_state.reasoning_settings["save_history"] = save_history
        
        # Custom reasoning presets
        if reasoning_mode == "Custom":
            st.markdown("##### Custom Reasoning Preset")
            preset_name = st.text_input(
                "Preset Name",
                value="My Custom Preset",
                key="custom_preset_name"
            )
            
            # Save preset button
            if st.button("Save Preset", key="save_custom_preset"):
                if 'custom_reasoning_presets' not in st.session_state:
                    st.session_state.custom_reasoning_presets = {}
                
                st.session_state.custom_reasoning_presets[preset_name] = {
                    "verbosity": verbosity,
                    "style": reasoning_style,
                    "confidence_threshold": confidence_threshold,
                    "show_steps": show_steps
                }
                st.success(f"Preset '{preset_name}' saved!")
    
    # Load custom presets
    if 'custom_reasoning_presets' in st.session_state and st.session_state.custom_reasoning_presets:
        with st.expander("Custom Presets", expanded=False):
            for preset_name, preset_config in st.session_state.custom_reasoning_presets.items():
                if st.button(f"Load: {preset_name}", key=f"load_preset_{preset_name}"):
                    st.session_state.reasoning_settings.update(preset_config)
                    st.session_state.reasoning_settings["mode"] = "Custom"
                    st.success(f"Loaded preset '{preset_name}'!")
                    st.rerun()
```

#### 4.4 Model Status Monitoring

```python
# Model status monitoring
def render_model_status_monitoring():
    st.markdown("#### Model Status")
    
    # Initialize model status in session state if not exists
    if 'model_status' not in st.session_state:
        st.session_state.model_status = {
            "local": {
                "llama-cpp-7B": {"status": "online", "response_time": 0.65, "error_rate": 0.02},
                "llama-cpp-13B": {"status": "online", "response_time": 1.2, "error_rate": 0.01}
            },
            "cloud": {
                "gpt-3.5-turbo": {"status": "online", "response_time": 0.42, "error_rate": 0.01},
                "gpt-4": {"status": "online", "response_time": 1.8, "error_rate": 0.005},
                "claude-3-sonnet": {"status": "online", "response_time": 0.95, "error_rate": 0.008}
            }
        }
    
    # Model type selector
    status_model_type = st.radio(
        "Show Status For",
        ["Local", "Cloud"],
        horizontal=True,
        key="status_model_type"
    )
    
    # Display model status
    for model_id, status in st.session_state.model_status[status_model_type.lower()].items():
        model_name = MODEL_CONFIG[status_model_type.lower()][model_id]["name"]
        
        # Status indicator and model name
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            status_color = {
                "online": "green",
                "degraded": "yellow",
                "offline": "red"
            }.get(status["status"], "gray")
            
            st.markdown(
                f'<div class="status-indicator status-{status_color}"></div>',
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(f"**{model_name}**")
        
        with col3:
            status_text = status["status"].capitalize()
            st.markdown(f"`{status_text}`")
        
        # Performance metrics
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Response Time", f"{status['response_time']}s")
        with col5:
            st.metric("Error Rate", f"{status['error_rate']*100:.1f}%")
        
        st.markdown("---")
    
    # Refresh button
    if st.button("Refresh Status", key="refresh_model_status"):
        # In a real implementation, this would fetch actual status from the backend
        st.success("Model status refreshed!")
        st.rerun()
```

#### 4.5 Model Fallback Mechanism

```python
# Model fallback mechanism
def handle_model_fallback():
    """Handle model selection with fallback mechanism"""
    
    # Check if current model is available
    current_model_type = st.session_state.get('current_model_type', 'local')
    current_model = st.session_state.get('current_model', 'llama-cpp-7B')
    
    if current_model_type in st.session_state.model_status:
        model_status = st.session_state.model_status[current_model_type]
        
        if current_model in model_status:
            status = model_status[current_model]["status"]
            
            # If model is offline, show fallback options
            if status == "offline":
                st.error(f"Selected model {MODEL_CONFIG[current_model_type][current_model]['name']} is currently offline.")
                
                # Show fallback options
                st.markdown("##### Fallback Options")
                
                # Auto-select best available model
                fallback_model = None
                best_response_time = float('inf')
                
                for model_id, model_status_info in model_status.items():
                    if model_status_info["status"] == "online" and model_status_info["response_time"] < best_response_time:
                        fallback_model = model_id
                        best_response_time = model_status_info["response_time"]
                
                if fallback_model:
                    fallback_model_name = MODEL_CONFIG[current_model_type][fallback_model]["name"]
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info(f"Recommended fallback: {fallback_model_name}")
                    with col2:
                        if st.button("Use Fallback", key="use_fallback_model"):
                            st.session_state.current_model = fallback_model
                            st.success(f"Switched to {fallback_model_name}")
                            st.rerun()
                
                # Manual model selection
                available_models = [
                    model_id for model_id, status_info in model_status.items()
                    if status_info["status"] == "online"
                ]
                
                if available_models:
                    manual_fallback = st.selectbox(
                        "Or select manually:",
                        options=[
                            MODEL_CONFIG[current_model_type][model_id]["name"]
                            for model_id in available_models
                        ],
                        key="manual_fallback_selection"
                    )
                    
                    if st.button("Use Selected", key="use_manual_fallback"):
                        # Find model ID from name
                        for model_id in available_models:
                            if MODEL_CONFIG[current_model_type][model_id]["name"] == manual_fallback:
                                st.session_state.current_model = model_id
                                st.success(f"Switched to {manual_fallback}")
                                st.rerun()
                                break
            
            # If model is degraded, show warning
            elif status == "degraded":
                st.warning(f"Selected model {MODEL_CONFIG[current_model_type][current_model]['name']} is running in degraded mode.")
                
                if st.button("Use Anyway", key="use_degraded_model"):
                    st.info("Continuing with degraded model...")
```

### 5. Integration with Existing Components

#### 5.1 Update Left Sidebar

```python
# Update left sidebar to include enhanced model controls
def render_left_sidebar():
    st.markdown('<div class="left-sidebar">', unsafe_allow_html=True)
    
    # New chat button
    if st.button("➕ New Chat", key="new_chat_button"):
        st.session_state.conversation_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Chat history (existing code)
    # ...
    
    st.markdown("---")
    
    # Enhanced model selection
    render_enhanced_model_selection()
    
    st.markdown("---")
    
    # Advanced reasoning controls
    render_advanced_reasoning_controls()
    
    st.markdown("---")
    
    # Model status monitoring
    render_model_status_monitoring()
    
    st.markdown("---")
    
    # Plugin toggles (existing code)
    # ...
    
    st.markdown("---")
    
    # User info
    st.markdown(f"**User:** {st.session_state.user_id}")
    
    st.markdown('</div>', unsafe_allow_html=True)
```

#### 5.2 Update Backend Call Simulation

```python
# Update simulate_backend_call to use enhanced model and reasoning settings
def simulate_backend_call(user_input: str) -> tuple[str, dict]:
    # Get current model and settings
    current_model = st.session_state.current_model
    current_model_type = st.session_state.get('current_model_type', 'local')
    model_parameters = st.session_state.model_parameters.get(current_model, {})
    reasoning_settings = st.session_state.reasoning_settings
    
    # Get model config
    model_config = MODEL_CONFIG[current_model_type][current_model]
    
    # Simulate processing time based on model
    base_time = model_config["performance"]["avg_response_time"]
    
    # Adjust processing time based on parameters
    if "max_tokens" in model_parameters:
        token_factor = model_parameters["max_tokens"] / 512  # Normalized to default
        base_time *= token_factor
    
    # Adjust processing time based on reasoning mode
    reasoning_mode = reasoning_settings["mode"]
    if reasoning_mode == "Off":
        reasoning_factor = 0.8
    elif reasoning_mode == "Standard":
        reasoning_factor = 1.0
    elif reasoning_mode == "Detailed":
        reasoning_factor = 1.3
    elif reasoning_mode == "Expert":
        reasoning_factor = 1.6
    else:  # Custom
        reasoning_factor = 1.2
    
    processing_time = base_time * reasoning_factor
    time.sleep(processing_time)
    
    # Generate response based on model and settings
    # ... (existing response generation logic)
    
    # Generate enhanced metadata
    metadata = {
        "model": current_model,
        "model_type": current_model_type,
        "model_name": model_config["name"],
        "response_time": processing_time,
        "parameters": model_parameters,
        "reasoning": {
            "mode": reasoning_mode,
            "verbosity": reasoning_settings["verbosity"],
            "style": reasoning_settings["style"],
            "confidence_threshold": reasoning_settings["confidence_threshold"],
            "show_steps": reasoning_settings["show_steps"]
        },
        "performance": {
            "quality_score": model_config["performance"]["quality_score"],
            "cost_per_token": model_config["performance"]["cost_per_token"]
        }
    }
    
    # Add reasoning steps if enabled
    if reasoning_settings["show_steps"] and reasoning_mode != "Off":
        metadata["reasoning"]["steps"] = generate_reasoning_steps(
            user_input, reasoning_mode, reasoning_settings
        )
    
    return response, metadata
```

### 6. Environment Configuration Updates

#### 6.1 Update .env.example

```bash
# Kari AI Streamlit Console Environment Configuration

# Backend API Configuration
KARI_BACKEND_URL=http://localhost:8000/api

# Authentication (if needed)
KARI_API_KEY=your_api_key_here

# Default Settings
DEFAULT_MODEL=llama-cpp-7B
DEFAULT_MODEL_TYPE=local
DEFAULT_REASONING_MODE=Standard

# Plugin Defaults
DEFAULT_PLUGINS_SEARCH=true
DEFAULT_PLUGINS_MEMORY=true
DEFAULT_PLUGINS_TOOLS=true

# Debug and Development
DEBUG_MODE=false
LOG_LEVEL=INFO

# User Configuration (for development)
DEFAULT_USER_ID=dev_user
DEFAULT_USER_ROLE=Creator

# Performance Settings
MAX_CONVERSATION_HISTORY=50
RESPONSE_TIMEOUT=30

# Model Defaults
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=512
DEFAULT_TOP_P=0.9
DEFAULT_TOP_K=40

# Reasoning Defaults
DEFAULT_REASONING_VERBOSITY=Medium
DEFAULT_REASONING_STYLE=Analytical
DEFAULT_CONFIDENCE_THRESHOLD=0.7
DEFAULT_SHOW_REASONING_STEPS=true
DEFAULT_SAVE_REASONING_HISTORY=true
```

### 7. Testing Strategy

#### 7.1 Unit Testing
- Test model selection functionality
- Test parameter validation
- Test reasoning mode controls
- Test model status monitoring

#### 7.2 Integration Testing
- Test model switching
- Test parameter persistence
- Test reasoning integration
- Test fallback mechanism

#### 7.3 User Acceptance Testing
- Test model selection UX
- Test reasoning controls usability
- Test model status visibility
- Test fallback mechanism effectiveness

### 8. Success Metrics

1. **Model Selection**:
   - Model switch success rate
   - Parameter adjustment frequency
   - Model type preference distribution

2. **Reasoning Controls**:
   - Reasoning mode usage distribution
   - Custom preset creation rate
   - Reasoning step display usage

3. **Model Monitoring**:
   - Model status refresh rate
   - Fallback mechanism usage
   - Model performance awareness

### 9. Rollout Plan

#### 9.1 Phase 1: Basic Enhancements
- Implement enhanced model selection
- Add basic reasoning controls
- Include model status indicators

#### 9.2 Phase 2: Advanced Features
- Add model-specific parameters
- Implement custom reasoning presets
- Include model fallback mechanism

#### 9.3 Phase 3: Analytics and Optimization
- Add model usage analytics
- Implement model performance tracking
- Include model recommendation system

## Conclusion

This plan outlines a comprehensive approach to enhancing model selection and reasoning controls in the Kari AI Lite Streamlit Console. By implementing these features, we'll provide users with more granular control over model selection and reasoning modes, improving the overall user experience and system flexibility.

The implementation will be done in phases, starting with basic model selection enhancements, then moving to more advanced features like custom reasoning presets and model fallback mechanisms.