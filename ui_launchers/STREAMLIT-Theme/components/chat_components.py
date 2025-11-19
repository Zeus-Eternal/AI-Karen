"""
Chat UI Components for Kari AI Streamlit Console
"""

import streamlit as st
from datetime import datetime
from styles.neon_theme import load_neon_theme
from utils.helpers import get_relative_time, copy_to_clipboard, insert_formatting

def render_chat_zone():
    """Render main chat interface with conversation history and input area"""
    st.markdown("## Chat Stream")
    
    # Display conversation history with enhanced styling
    st.markdown(
        '<div class="enhanced-chat-container">',
        unsafe_allow_html=True
    )
    
    # Display conversation history
    for i, message in enumerate(st.session_state.conversation_history):
        render_enhanced_message(message, i)
    
    # Display streaming response if active
    if st.session_state.streaming_response['active']:
        render_streaming_response()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced input area
    st.markdown("---")
    render_enhanced_input_area()

def render_enhanced_message(message, index):
    """Render a single message with enhanced styling and metadata"""
    message_type = "user-message" if message['role'] == 'user' else "assistant-message"
    
    # Message container
    st.markdown(
        f'<div class="enhanced-message {message_type}">',
        unsafe_allow_html=True
    )
    
    # Message header with avatar and info
    col1, col2 = st.columns([1, 11])
    
    with col1:
        render_message_avatar(message['role'])
    
    with col2:
        render_message_header(message)
        render_message_body(message)
        
        # Message actions
        if st.session_state.show_message_actions:
            render_message_actions(message, index)
        
        # Message metadata
        if message['role'] == 'assistant' and 'metadata' in message and st.session_state.show_message_metadata:
            render_enhanced_message_metadata(message['metadata'])
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-message

def render_message_avatar(role):
    """Render avatar for a message"""
    avatar_icon = "👤" if role == 'user' else "🤖"
    avatar_class = "user-avatar" if role == 'user' else "assistant-avatar"
    st.markdown(
        f'<div class="message-avatar {avatar_class}">{avatar_icon}</div>',
        unsafe_allow_html=True
    )

def render_message_header(message):
    """Render header for a message with author, timestamp, and status"""
    st.markdown(
        '<div class="message-header">',
        unsafe_allow_html=True
    )
    
    # Author and timestamp
    author_name = "You" if message['role'] == 'user' else "Kari"
    timestamp = message.get('timestamp', '')
    timestamp_display = format_timestamp(timestamp)
    
    st.markdown(
        '<div class="message-info">',
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
            render_message_status(metadata['status'])
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-info
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-header

def render_message_status(status):
    """Render status indicator for a message"""
    status_class = f"status-{status}"
    st.markdown(
        f'<div class="message-status">'
        f'<div class="status-indicator-small {status_class}"></div>'
        f'{status.capitalize()}'
        f'</div>',
        unsafe_allow_html=True
    )

def render_message_body(message):
    """Render body content of a message"""
    st.markdown(
        '<div class="message-content">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div class="message-body">{message["content"]}</div>',
        unsafe_allow_html=True
    )

def render_message_actions(message, index):
    """Render action buttons for a message"""
    st.markdown(
        f'<div class="message-actions">',
        unsafe_allow_html=True
    )
    
    action_cols = st.columns(4)
    
    with action_cols[0]:
        if st.button("📋 Copy", key=f"copy_msg_{index}", help="Copy message to clipboard"):
            if copy_to_clipboard(message["content"]):
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

def render_enhanced_message_metadata(metadata):
    """Render enhanced metadata for a message"""
    st.markdown(
        '<div class="message-metadata">',
        unsafe_allow_html=True
    )
    
    # Model badge
    if 'model' in metadata:
        model_name = metadata['model']
        display_name = metadata.get('model_name', model_name)
        render_metadata_badge("model", "🧠", display_name)
    
    # Response time badge
    if 'response_time' in metadata:
        response_time = metadata['response_time']
        render_metadata_badge("time", "⏱️", f"{response_time:.2f}s")
    
    # Plugin badges
    if 'plugins' in metadata:
        plugins = metadata['plugins']
        if isinstance(plugins, dict) and 'active' in plugins:
            active_plugins = plugins['active']
            for plugin in active_plugins:
                plugin_icon = get_plugin_icon(plugins, plugin)
                render_metadata_badge("plugin", plugin_icon, plugin)
    
    # Reasoning badge
    if 'reasoning' in metadata:
        reasoning = metadata['reasoning']
        if 'mode' in reasoning and reasoning['mode'] != 'Off':
            reasoning_mode = reasoning['mode']
            render_metadata_badge("model", "🧠", reasoning_mode)
    
    # Memory hits badge
    if 'memory_hits' in metadata and metadata['memory_hits'] > 0:
        memory_hits = metadata['memory_hits']
        render_metadata_badge("model", "🧠", f"{memory_hits} memories")
    
    # Search results badge
    if 'search_results' in metadata and metadata['search_results'] > 0:
        search_results = metadata['search_results']
        render_metadata_badge("model", "🔍", f"{search_results} results")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-metadata

def render_metadata_badge(badge_class, icon, text):
    """Render a metadata badge"""
    st.markdown(
        f'<div class="metadata-badge {badge_class}">'
        f'{icon} {text}'
        f'</div>',
        unsafe_allow_html=True
    )

def get_plugin_icon(plugins, plugin):
    """Get icon for a plugin"""
    plugin_icon = "🔌"
    if 'plugin_results' in plugins and plugin in plugins['plugin_results']:
        plugin_result = plugins['plugin_results'][plugin]
        if 'status' in plugin_result:
            if plugin_result['status'] == 'success':
                plugin_icon = "✅"
            elif plugin_result['status'] in ['error', 'timeout']:
                plugin_icon = "❌"
    return plugin_icon

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp)
        return get_relative_time(dt)
    except:
        return timestamp

def render_streaming_response():
    """Render streaming response with controls"""
    streaming = st.session_state.streaming_response
    
    st.markdown(
        '<div class="streaming-message enhanced-message assistant-message">',
        unsafe_allow_html=True
    )
    
    # Message header
    render_streaming_header()
    
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
    render_streaming_controls(streaming)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
    st.markdown('</div>', unsafe_allow_html=True)  # Close streaming-message

def render_streaming_header():
    """Render header for streaming message"""
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
        '<div class="message-timestamp">just now</div>',
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

def render_streaming_controls(streaming):
    """Render controls for streaming response"""
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
        if st.button("⏭️ Skip", key="skip_streaming", help="Skip to end of response"):
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

def render_enhanced_input_area():
    """Render enhanced input area with formatting options and controls"""
    st.markdown(
        '<div class="enhanced-input-area">',
        unsafe_allow_html=True
    )
    
    # Input toolbar
    render_input_toolbar()
    
    # Input textarea
    render_input_textarea()
    
    # Input actions
    render_input_actions()
    
    # Input hints
    render_input_hints()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-input-area

def render_input_toolbar():
    """Render input toolbar with formatting options"""
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
        value=st.session_state.auto_resize_input,
        key="input_auto_resize",
        help="Automatically resize input area based on content"
    )
    
    # Update auto-resize state
    st.session_state.auto_resize_input = auto_resize
    
    # Character count
    if 'input_text' in st.session_state:
        char_count = len(st.session_state.input_text)
        st.markdown(
            f'<div class="input-hint">{char_count} characters</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-options
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-toolbar

def render_input_textarea():
    """Render input textarea"""
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    
    auto_resize = st.session_state.auto_resize_input
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

def render_input_actions():
    """Render input actions"""
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
    send_disabled = not st.session_state.input_text.strip()
    if st.button("Send", key="send_message", disabled=send_disabled, help="Send your message to Kari"):
        if st.session_state.input_text.strip():
            # Process and send message
            from services.chat_service import process_user_input
            process_user_input(st.session_state.input_text)
            st.session_state.input_text = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions-right
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions

def render_input_hints():
    """Render input hints"""
    st.markdown(
        '<div class="input-hint">',
        unsafe_allow_html=True
    )
    st.markdown("Press **Shift+Enter** for new line, **Enter** to send")
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-hint