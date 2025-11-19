# Chat UI Enhancement Plan

## Overview
This document outlines the plan for refining the chat UI with better message styling and metadata display in the Kari AI Lite Streamlit Console. The goal is to create a more visually appealing and informative chat interface that enhances the user experience and provides better visibility into the AI's responses.

## Current State Analysis
The current implementation has a basic chat interface:
- Simple message bubbles with basic styling
- Limited metadata display in captions
- No message actions or interactions
- Basic input area with minimal controls
- No streaming response display
- Limited visual hierarchy and emphasis

## Implementation Plan

### 1. Enhanced Message Styling

#### 1.1 Visual Message Hierarchy
- Implement distinct visual styles for user vs. assistant messages
- Add visual emphasis for important messages
- Create message grouping for related content
- Implement message status indicators

#### 1.2 Advanced Message Components
- Add message avatars and icons
- Implement message timestamps with relative time display
- Create message badges for special content types
- Add message reaction indicators

#### 1.3 Message Interaction Features
- Implement message actions (copy, edit, delete, retry)
- Add message expansion/collapse for long content
- Create message quoting and referencing
- Include message sharing capabilities

### 2. Enhanced Metadata Display

#### 2.1 Rich Metadata Visualization
- Create visually appealing metadata cards
- Implement metadata grouping and categorization
- Add metadata expand/collapse functionality
- Include metadata search and filtering

#### 2.2 Contextual Metadata Presentation
- Show relevant metadata based on message content
- Implement metadata priority and importance
- Add metadata visual indicators and badges
- Include metadata drill-down capabilities

#### 2.3 Interactive Metadata Elements
- Create clickable metadata elements
- Implement metadata tooltips and explanations
- Add metadata editing capabilities
- Include metadata history tracking

### 3. Advanced Input Controls

#### 3.1 Enhanced Input Area
- Implement resizable input area
- Add input formatting options
- Create input history and suggestions
- Include input validation and feedback

#### 3.2 Smart Input Features
- Implement auto-completion and suggestions
- Add command shortcuts and macros
- Create input templates and presets
- Include input preview and formatting

#### 3.3 Input Submission Options
- Implement multiple submission methods
- Add submission scheduling options
- Create input priority levels
- Include input attachment capabilities

### 4. Streaming Response Display

#### 4.1 Real-time Streaming
- Implement token-by-token streaming display
- Add streaming progress indicators
- Create streaming pause/resume controls
- Include streaming speed controls

#### 4.2 Streaming Visualization
- Implement typing indicators and animations
- Add streaming status badges
- Create streaming completion notifications
- Include streaming error handling

#### 4.3 Post-Streaming Features
- Implement response editing and refinement
- Add response regeneration options
- Create response feedback mechanisms
- Include response sharing capabilities

### 5. Implementation Details

#### 5.1 Enhanced CSS Styling

```css
/* Enhanced message styling */
.enhanced-chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    max-height: calc(100vh - 200px);
    overflow-y: auto;
}

.enhanced-message {
    display: flex;
    margin-bottom: 1.5rem;
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 1rem;
    flex-shrink: 0;
    font-weight: bold;
    font-size: 1.2rem;
}

.user-avatar {
    background: linear-gradient(135deg, var(--primary-neon), rgba(0, 255, 255, 0.2));
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.assistant-avatar {
    background: linear-gradient(135deg, var(--secondary-neon), rgba(255, 0, 255, 0.2));
    box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
}

.message-content {
    flex: 1;
    min-width: 0;
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.message-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.message-author {
    font-weight: 600;
    font-size: 0.9rem;
}

.message-timestamp {
    font-size: 0.8rem;
    color: var(--text-secondary);
    opacity: 0.8;
}

.message-body {
    background-color: rgba(26, 26, 46, 0.6);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-left: 3px solid transparent;
    position: relative;
    overflow: hidden;
}

.user-message .message-body {
    border-left-color: var(--primary-neon);
    background-color: rgba(0, 255, 255, 0.1);
}

.assistant-message .message-body {
    border-left-color: var(--secondary-neon);
    background-color: rgba(255, 0, 255, 0.1);
}

.message-body::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    opacity: 0.5;
}

.message-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.enhanced-message:hover .message-actions {
    opacity: 1;
}

.message-action-button {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.message-action-button:hover {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.message-metadata {
    margin-top: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.metadata-badge {
    background-color: rgba(26, 26, 46, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    white-space: nowrap;
}

.metadata-badge.model {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.metadata-badge.plugin {
    background-color: rgba(255, 0, 255, 0.1);
    border-color: var(--secondary-neon);
    color: var(--secondary-neon);
}

.metadata-badge.time {
    background-color: rgba(255, 255, 0, 0.1);
    border-color: #FFFF00;
    color: #FFFF00;
}

.streaming-message {
    position: relative;
}

.streaming-cursor {
    display: inline-block;
    width: 8px;
    height: 1.2em;
    background-color: var(--primary-neon);
    animation: blink 1s infinite;
    margin-left: 2px;
    vertical-align: text-bottom;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.streaming-controls {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.streaming-message:hover .streaming-controls {
    opacity: 1;
}

.streaming-control-button {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.streaming-control-button:hover {
    background-color: rgba(0, 255, 255, 0.1);
    border-color: var(--primary-neon);
    color: var(--primary-neon);
}

.enhanced-input-area {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background-color: rgba(26, 26, 46, 0.4);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.input-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.input-formatting {
    display: flex;
    gap: 0.5rem;
}

.formatting-button {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 0.25rem;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.formatting-button:hover {
    background-color: rgba(0, 255, 255, 0.1);
    color: var(--primary-neon);
}

.input-options {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.input-textarea {
    background-color: rgba(15, 15, 27, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-primary);
    padding: 0.75rem;
    resize: vertical;
    min-height: 100px;
    max-height: 300px;
    font-family: inherit;
    font-size: 0.95rem;
    transition: border-color 0.2s ease;
}

.input-textarea:focus {
    outline: none;
    border-color: var(--primary-neon);
    box-shadow: 0 0 0 2px rgba(0, 255, 255, 0.2);
}

.input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.5rem;
}

.input-actions-left {
    display: flex;
    gap: 0.5rem;
}

.input-actions-right {
    display: flex;
    gap: 0.5rem;
}

.input-hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
    opacity: 0.8;
}

.message-status {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-left: 0.5rem;
}

.status-indicator-small {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}

.status-success {
    background-color: #00FF00;
    box-shadow: 0 0 4px rgba(0, 255, 0, 0.6);
}

.status-error {
    background-color: #FF0000;
    box-shadow: 0 0 4px rgba(255, 0, 0, 0.6);
}

.status-pending {
    background-color: #FFFF00;
    box-shadow: 0 0 4px rgba(255, 255, 0, 0.6);
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
```

#### 5.2 Enhanced Message Components

```python
# Enhanced message rendering
def render_enhanced_message(message, index):
    """Render a single message with enhanced styling and metadata"""
    message_type = "user-message" if message['role'] == 'user' else "assistant-message"
    
    # Message container
    with st.container():
        # Message header with avatar and info
        col1, col2 = st.columns([1, 11])
        
        with col1:
            # Avatar
            avatar_icon = "👤" if message['role'] == 'user' else "🤖"
            avatar_class = "user-avatar" if message['role'] == 'user' else "assistant-avatar"
            st.markdown(
                f'<div class="message-avatar {avatar_class}">{avatar_icon}</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            # Message header
            st.markdown(
                f'<div class="message-header">',
                unsafe_allow_html=True
            )
            
            # Author and timestamp
            author_name = "You" if message['role'] == 'user' else "Kari"
            timestamp = message.get('timestamp', '')
            if timestamp:
                # Format timestamp for display
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp)
                    relative_time = get_relative_time(dt)
                    timestamp_display = relative_time
                except:
                    timestamp_display = timestamp
            else:
                timestamp_display = ""
            
            st.markdown(
                f'<div class="message-info">',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="message-author">{author_name}</div>',
                unsafe_allow_html=True
            )
            if timestamp_display:
                st.markdown(
                    f'<div class="message-timestamp">{timestamp_display}</div>',
                    unsafe_allow_html=True
                )
            
            # Message status (for assistant messages)
            if message['role'] == 'assistant' and 'metadata' in message:
                metadata = message['metadata']
                if 'status' in metadata:
                    status = metadata['status']
                    status_class = f"status-{status}"
                    st.markdown(
                        f'<div class="message-status">'
                        f'<div class="status-indicator-small {status_class}"></div>'
                        f'{status.capitalize()}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close message-info
            st.markdown('</div>', unsafe_allow_html=True)  # Close message-header
            
            # Message body
            st.markdown(
                f'<div class="enhanced-message {message_type}">',
                unsafe_allow_html=True
            )
            
            st.markdown(
                f'<div class="message-content">',
                unsafe_allow_html=True
            )
            
            st.markdown(
                f'<div class="message-body">{message["content"]}</div>',
                unsafe_allow_html=True
            )
            
            # Message actions
            st.markdown(
                f'<div class="message-actions">',
                unsafe_allow_html=True
            )
            
            action_cols = st.columns(4)
            
            with action_cols[0]:
                if st.button("📋 Copy", key=f"copy_msg_{index}", help="Copy message to clipboard"):
                    copy_to_clipboard(message["content"])
                    st.success("Message copied to clipboard!")
            
            with action_cols[1]:
                if message['role'] == 'user':
                    if st.button("✏️ Edit", key=f"edit_msg_{index}", help="Edit this message"):
                        # Implement message editing
                        pass
            
            with action_cols[2]:
                if st.button("🔄 Retry", key=f"retry_msg_{index}", help="Regenerate response"):
                    # Implement message retry
                    pass
            
            with action_cols[3]:
                if st.button("🗑️ Delete", key=f"delete_msg_{index}", help="Delete this message"):
                    # Implement message deletion
                    pass
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close message-actions
            
            # Message metadata
            if message['role'] == 'assistant' and 'metadata' in message:
                metadata = message['metadata']
                render_enhanced_message_metadata(metadata)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
            st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-message

def render_enhanced_message_metadata(metadata):
    """Render enhanced metadata for a message"""
    st.markdown(
        '<div class="message-metadata">',
        unsafe_allow_html=True
    )
    
    # Model badge
    if 'model' in metadata:
        model_name = metadata['model']
        model_type = metadata.get('model_type', 'local')
        model_badge_class = "model"
        
        # Get model display name
        if 'model_name' in metadata:
            display_name = metadata['model_name']
        else:
            display_name = model_name
        
        st.markdown(
            f'<div class="metadata-badge {model_badge_class}">'
            f'🧠 {display_name}'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Response time badge
    if 'response_time' in metadata:
        response_time = metadata['response_time']
        time_badge_class = "time"
        
        st.markdown(
            f'<div class="metadata-badge {time_badge_class}">'
            f'⏱️ {response_time:.2f}s'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Plugin badges
    if 'plugins' in metadata:
        plugins = metadata['plugins']
        if isinstance(plugins, dict) and 'active' in plugins:
            active_plugins = plugins['active']
            for plugin in active_plugins:
                plugin_badge_class = "plugin"
                
                # Get plugin icon
                plugin_icon = "🔌"
                if 'plugin_results' in plugins and plugin in plugins['plugin_results']:
                    plugin_result = plugins['plugin_results'][plugin]
                    if 'status' in plugin_result and plugin_result['status'] == 'success':
                        plugin_icon = "✅"
                    elif 'status' in plugin_result and plugin_result['status'] in ['error', 'timeout']:
                        plugin_icon = "❌"
                
                st.markdown(
                    f'<div class="metadata-badge {plugin_badge_class}">'
                    f'{plugin_icon} {plugin}'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    # Reasoning badge
    if 'reasoning' in metadata:
        reasoning = metadata['reasoning']
        if 'mode' in reasoning and reasoning['mode'] != 'Off':
            reasoning_mode = reasoning['mode']
            reasoning_badge_class = "model"
            
            st.markdown(
                f'<div class="metadata-badge {reasoning_badge_class}">'
                f'🧠 {reasoning_mode}'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Memory hits badge
    if 'memory_hits' in metadata and metadata['memory_hits'] > 0:
        memory_hits = metadata['memory_hits']
        memory_badge_class = "model"
        
        st.markdown(
            f'<div class="metadata-badge {memory_badge_class}">'
            f'🧠 {memory_hits} memories'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Search results badge
    if 'search_results' in metadata and metadata['search_results'] > 0:
        search_results = metadata['search_results']
        search_badge_class = "model"
        
        st.markdown(
            f'<div class="metadata-badge {search_badge_class}">'
            f'🔍 {search_results} results'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-metadata

def get_relative_time(dt):
    """Get relative time string from datetime object"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    import pyperclip
    try:
        pyperclip.copy(text)
        return True
    except:
        # Fallback for environments without pyperclip
        return False
```

#### 5.3 Enhanced Input Area

```python
# Enhanced input area
def render_enhanced_input_area():
    """Render enhanced input area with formatting options and controls"""
    st.markdown(
        '<div class="enhanced-input-area">',
        unsafe_allow_html=True
    )
    
    # Input toolbar
    st.markdown(
        '<div class="input-toolbar">',
        unsafe_allow_html=True
    )
    
    # Formatting options
    st.markdown(
        '<div class="input-formatting">',
        unsafe_allow_html=True
    )
    
    format_cols = st.columns(5)
    
    with format_cols[0]:
        if st.button("B", key="format_bold", help="Bold text"):
            insert_formatting("**", "**")
    
    with format_cols[1]:
        if st.button("I", key="format_italic", help="Italic text"):
            insert_formatting("*", "*")
    
    with format_cols[2]:
        if st.button("U", key="format_underline", help="Underline text"):
            insert_formatting("<u>", "</u>")
    
    with format_cols[3]:
        if st.button("C", key="format_code", help="Code block"):
            insert_formatting("```\n", "\n```")
    
    with format_cols[4]:
        if st.button("🔗", key="format_link", help="Insert link"):
            insert_formatting("[", "](url)")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-formatting
    
    # Input options
    st.markdown(
        '<div class="input-options">',
        unsafe_allow_html=True
    )
    
    # Auto-resize toggle
    auto_resize = st.checkbox(
        "Auto-resize",
        value=True,
        key="input_auto_resize",
        help="Automatically resize input area based on content"
    )
    
    # Character count
    if 'input_text' in st.session_state:
        char_count = len(st.session_state.input_text)
        st.markdown(
            f'<div class="input-hint">{char_count} characters</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-options
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-toolbar
    
    # Input textarea
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    
    input_height = 100 if auto_resize else None
    if not auto_resize and 'input_height' in st.session_state:
        input_height = st.session_state.input_height
    
    input_text = st.text_area(
        "Message",
        value=st.session_state.input_text,
        height=input_height,
        key="enhanced_input_text",
        placeholder="Type your message to Kari...",
        help="Press Shift+Enter for new line, Enter to send"
    )
    
    # Update session state
    st.session_state.input_text = input_text
    
    # Update input height if not auto-resizing
    if not auto_resize:
        lines = input_text.count('\n') + 1
        st.session_state.input_height = max(100, min(300, lines * 25))
    
    # Input actions
    st.markdown(
        '<div class="input-actions">',
        unsafe_allow_html=True
    )
    
    # Left actions
    st.markdown(
        '<div class="input-actions-left">',
        unsafe_allow_html=True
    )
    
    # Attach file button
    if st.button("📎 Attach", key="attach_file", help="Attach a file"):
        # Implement file attachment
        pass
    
    # Insert template button
    if st.button("📝 Template", key="insert_template", help="Insert a message template"):
        # Implement template insertion
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions-left
    
    # Right actions
    st.markdown(
        '<div class="input-actions-right">',
        unsafe_allow_html=True
    )
    
    # Clear button
    if st.button("Clear", key="clear_input", help="Clear input"):
        st.session_state.input_text = ""
        st.rerun()
    
    # Send button
    send_disabled = not input_text.strip()
    if st.button("Send", key="send_message", disabled=send_disabled, help="Send your message to Kari"):
        if input_text.strip():
            # Process and send message
            process_user_input(input_text)
            st.session_state.input_text = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions-right
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions
    
    # Input hints
    st.markdown(
        '<div class="input-hint">',
        unsafe_allow_html=True
    )
    st.markdown("Press **Shift+Enter** for new line, **Enter** to send")
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-hint
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-input-area

def insert_formatting(before, after):
    """Insert formatting around selected text in input"""
    # This would be implemented with JavaScript in a real application
    # For Streamlit, we'll just append the formatting
    if 'input_text' in st.session_state:
        st.session_state.input_text += before + "text" + after
        st.rerun()

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
```

#### 5.4 Streaming Response Display

```python
# Streaming response display
def render_streaming_response():
    """Render streaming response with controls"""
    # Initialize streaming state
    if 'streaming_response' not in st.session_state:
        st.session_state.streaming_response = {
            'active': False,
            'content': '',
            'metadata': {},
            'paused': False,
            'speed': 1.0
        }
    
    streaming = st.session_state.streaming_response
    
    if streaming['active']:
        st.markdown(
            '<div class="streaming-message enhanced-message assistant-message">',
            unsafe_allow_html=True
        )
        
        # Message header
        st.markdown(
            '<div class="message-header">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="message-info">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="message-author">Kari</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(
            f'<div class="message-timestamp">just now</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '<div class="message-status">'
            '<div class="status-indicator-small status-pending"></div>'
            'Streaming'
            '</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close message-info
        st.markdown('</div>', unsafe_allow_html=True)  # Close message-header
        
        # Message body with streaming cursor
        st.markdown(
            '<div class="message-content">',
            unsafe_allow_html=True
        )
        
        st.markdown(
            f'<div class="message-body">{streaming["content"]}<span class="streaming-cursor"></span></div>',
            unsafe_allow_html=True
        )
        
        # Streaming controls
        st.markdown(
            '<div class="streaming-controls">',
            unsafe_allow_html=True
        )
        
        control_cols = st.columns(4)
        
        with control_cols[0]:
            if streaming['paused']:
                if st.button("▶️ Resume", key="resume_streaming", help="Resume streaming"):
                    streaming['paused'] = False
            else:
                if st.button("⏸️ Pause", key="pause_streaming", help="Pause streaming"):
                    streaming['paused'] = True
        
        with control_cols[1]:
            speed_options = [0.5, 1.0, 1.5, 2.0]
            speed_labels = ["0.5x", "1.0x", "1.5x", "2.0x"]
            current_speed_index = speed_options.index(streaming['speed'])
            selected_speed = st.selectbox(
                "Speed",
                options=speed_labels,
                index=current_speed_index,
                key="streaming_speed"
            )
            streaming['speed'] = speed_options[speed_labels.index(selected_speed)]
        
        with control_cols[2]:
            if st.button("⏹️ Skip", key="skip_streaming", help="Skip to end of response"):
                # Skip to end of response
                pass
        
        with control_cols[3]:
            if st.button("⏹️ Stop", key="stop_streaming", help="Stop streaming and keep current response"):
                streaming['active'] = False
                # Add completed response to conversation
                st.session_state.conversation_history.append({
                    'role': 'assistant',
                    'content': streaming['content'],
                    'timestamp': datetime.now().isoformat(),
                    'metadata': streaming['metadata']
                })
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close streaming-controls
        st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close streaming-message
        
        # Simulate streaming in a real implementation
        # This would be replaced with actual streaming from backend
        simulate_streaming_response()

def simulate_streaming_response():
    """Simulate streaming response for demonstration"""
    streaming = st.session_state.streaming_response
    
    if not streaming['paused'] and streaming['active']:
        # Simulate receiving a chunk of text
        import time
        import random
        
        # Sample response chunks
        response_chunks = [
            "I'm processing your request",
            " and analyzing the information",
            " to provide you with a comprehensive response",
            " that addresses all aspects of your question",
            " with the most relevant and accurate information available."
        ]
        
        # Add next chunk if available
        if len(streaming['content'].split()) < len(' '.join(response_chunks).split()):
            # Find the next chunk to add
            all_words = ' '.join(response_chunks).split()
            current_words = streaming['content'].split()
            
            if len(current_words) < len(all_words):
                next_word = all_words[len(current_words)]
                streaming['content'] += ' ' + next_word
        
        # Check if streaming is complete
        if len(streaming['content'].split()) >= len(' '.join(response_chunks).split()):
            streaming['active'] = False
            
            # Add completed response to conversation
            st.session_state.conversation_history.append({
                'role': 'assistant',
                'content': streaming['content'],
                'timestamp': datetime.now().isoformat(),
                'metadata': streaming['metadata']
            })
            
            st.rerun()
        else:
            # Schedule next update
            time.sleep(0.1 / streaming['speed'])
            st.rerun()
```

### 6. Integration with Existing Components

#### 6.1 Update Chat Zone

```python
# Enhanced chat zone
def render_enhanced_chat_zone():
    """Render enhanced chat interface with improved styling and features"""
    st.markdown("## Chat Stream")
    
    # Chat container with enhanced styling
    st.markdown(
        '<div class="enhanced-chat-container">',
        unsafe_allow_html=True
    )
    
    # Display conversation history with enhanced messages
    for i, message in enumerate(st.session_state.conversation_history):
        render_enhanced_message(message, i)
    
    # Display streaming response if active
    if st.session_state.streaming_response['active']:
        render_streaming_response()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-chat-container
    
    # Enhanced input area
    st.markdown("---")
    render_enhanced_input_area()
```

#### 6.2 Update CSS

```python
# Add enhanced CSS to load_neon_theme function
def load_neon_theme():
    # Existing CSS...
    
    # Add enhanced message styling CSS
    enhanced_message_css = """
    /* Enhanced message styling CSS from section 5.1 */
    """
    
    # Combine with existing CSS
    neon_css += enhanced_message_css
    st.markdown(neon_css, unsafe_allow_html=True)
```

### 7. Environment Configuration Updates

#### 7.1 Update .env.example

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
DEFAULT_PLUGINS_WEATHER=false

# Chat UI Defaults
DEFAULT_AUTO_RESIZE_INPUT=true
DEFAULT_INPUT_HEIGHT=100
DEFAULT_MAX_INPUT_HEIGHT=300
DEFAULT_STREAMING_SPEED=1.0
DEFAULT_ENABLE_STREAMING_CONTROLS=true
DEFAULT_SHOW_MESSAGE_ACTIONS=true
DEFAULT_SHOW_MESSAGE_METADATA=true
DEFAULT_ENABLE_MESSAGE_FORMATTING=true

# Debug and Development
DEBUG_MODE=false
LOG_LEVEL=INFO

# User Configuration (for development)
DEFAULT_USER_ID=dev_user
DEFAULT_USER_ROLE=Creator

# Performance Settings
MAX_CONVERSATION_HISTORY=50
RESPONSE_TIMEOUT=30
```

### 8. Testing Strategy

#### 8.1 Unit Testing
- Test message rendering functionality
- Test metadata display components
- Test input area controls
- Test streaming response display

#### 8.2 Integration Testing
- Test message actions (copy, edit, delete, retry)
- Test input formatting options
- Test streaming controls
- Test message metadata display

#### 8.3 User Acceptance Testing
- Test overall chat UI usability
- Test message interaction patterns
- Test input area responsiveness
- Test streaming experience

### 9. Success Metrics

1. **Message Interaction**:
   - Message action usage rate
   - Message copy/edit/delete frequency
   - Message retry rate

2. **Input Experience**:
   - Input formatting usage
   - Input template usage
   - Input area resize frequency

3. **Streaming Experience**:
   - Streaming control usage
   - Streaming speed adjustment frequency
   - Streaming pause/resume rate

### 10. Rollout Plan

#### 10.1 Phase 1: Basic Enhancements
- Implement enhanced message styling
- Add basic message actions
- Include metadata display

#### 10.2 Phase 2: Advanced Features
- Add streaming response display
- Implement input formatting options
- Include message interaction features

#### 10.3 Phase 3: Optimization
- Add performance optimizations
- Implement accessibility features
- Include user preference controls

## Conclusion

This plan outlines a comprehensive approach to refining the chat UI with better message styling and metadata display in Kari AI Lite Streamlit Console. By implementing these features, we'll create a more visually appealing and informative chat interface that enhances the user experience and provides better visibility into the AI's responses.

The implementation will be done in phases, starting with basic message styling enhancements, then moving to more advanced features like streaming response display and input formatting options.