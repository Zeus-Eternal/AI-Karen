"""
Enhanced chat interface components for the Streamlit UI
"""

import streamlit as st
import json
import numpy as np
from datetime import datetime
from services.chat_service import chat_service
from ui_launchers.streamlit_ui.helpers.chat_ui import (
    render_message,
    render_typing_indicator,
    render_export_modal,
)


def render_enhanced_chat_interface(user_ctx=None):
    """Enhanced chat interface with advanced features"""
    st.markdown("## 💬 AI Karen Chat Assistant")
    
    # System status indicator
    try:
        health = chat_service.get_system_health()
        if health.get("status") == "ok":
            st.success("🟢 **System Status:** Connected to AI Karen Backend")
        else:
            st.error(f"🔴 **System Status:** {health.get('message', 'Backend unavailable')}")
    except Exception as e:
        st.warning(f"⚠️ **System Status:** Unable to check backend status - {str(e)}")
    
    # Chat controls and settings
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        # Show current model if available
        try:
            models = chat_service.get_available_models()
            active_model = next((m.get("name", "Unknown") for m in models if m.get("active")), "Default")
            st.markdown(f"**Active Model:** {active_model}")
        except:
            st.markdown("**Active Model:** Default")
    with col2:
        show_typing = st.checkbox("💭 Typing indicators", value=True)
    with col3:
        auto_save = st.checkbox("💾 Auto-save", value=True)
    with col4:
        if st.button("📤 Export Chat"):
            st.session_state.show_export_modal = True
    
    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm AI Karen, your intelligent assistant. How can I help you today?", "timestamp": datetime.now(), "attachments": []},
        ]
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Note: Sidebar is now handled globally in components/sidebar.py
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages with rich formatting
        for message in st.session_state.chat_messages:
            render_message(message)
    
    # Typing indicator
    render_typing_indicator(show_typing and st.session_state.get('ai_typing', False))
    
    # Message input area
    st.markdown("---")
    
    # File attachment area
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "📎 Attach files (optional)",
            type=['txt', 'pdf', 'docx', 'csv', 'json', 'py'],
            help="Attach files to your message"
        )
    with col2:
        if uploaded_file:
            st.success(f"📎 {uploaded_file.name}")
    
    # Message composition
    message_col1, message_col2 = st.columns([4, 1])
    
    with message_col1:
        user_input = st.text_area(
            "Type your message...",
            placeholder="Ask me anything! I can help with system configuration, troubleshooting, code analysis, and more.",
            height=100,
            key="chat_input"
        )
    
    with message_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        
        # Quick action buttons
        if st.button("🚀 Send", type="primary", use_container_width=True):
            if user_input.strip():
                # Add user message
                attachments = []
                if uploaded_file:
                    attachments.append({
                        "name": uploaded_file.name,
                        "size": f"{uploaded_file.size} bytes",
                        "type": uploaded_file.type
                    })
                
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now(),
                    "attachments": attachments
                })
                
                # Show AI typing indicator
                st.session_state.ai_typing = True
                st.rerun()
                
                # Generate AI response using backend LLM
                try:
                    with st.spinner("🤖 AI Karen is thinking..."):
                        ai_response = chat_service.generate_ai_response(
                            user_input, 
                            context=st.session_state.chat_messages[-5:]  # Last 5 messages for context
                        )
                except Exception as e:
                    ai_response = f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try again."
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now(),
                    "attachments": []
                })
                
                st.session_state.ai_typing = False
                
                # Auto-save conversation
                if auto_save:
                    st.session_state.conversation_history.append({
                        "timestamp": datetime.now(),
                        "messages": len(st.session_state.chat_messages)
                    })
                
                # Clear input and rerun
                st.session_state.chat_input = ""
                st.rerun()
        
        if st.button("🎤 Voice", use_container_width=True):
            st.info("🎤 Voice input feature coming soon!")
        
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Hello! I'm AI Karen, your intelligent assistant. How can I help you today?", "timestamp": datetime.now(), "attachments": []},
            ]
            st.rerun()
    
    # Quick suggestions
    st.markdown("### 💡 Quick Suggestions")
    suggestion_cols = st.columns(4)
    
    suggestions = [
        "Help me configure the system",
        "Explain the plugin architecture", 
        "Show me performance metrics",
        "Troubleshoot an error"
    ]
    
    for i, suggestion in enumerate(suggestions):
        with suggestion_cols[i]:
            if st.button(f"💭 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": suggestion,
                    "timestamp": datetime.now(),
                    "attachments": []
                })
                
                # Generate contextual AI response
                responses = {
                    "Help me configure the system": "I'd be happy to help you configure the system! Let me guide you through the key configuration areas: database settings, API endpoints, plugin management, and security configurations. Which area would you like to start with?",
                    "Explain the plugin architecture": "The AI Karen plugin architecture is modular and extensible. Plugins are organized into categories like AI services, automation, integrations, and core functionality. Each plugin has a manifest file and handler. Would you like me to explain a specific aspect?",
                    "Show me performance metrics": "Here are the current system performance metrics: CPU usage is at 45%, memory usage at 60%, with 1,200 requests per minute and 0.8% error rate. The system health is excellent at 94%. Would you like detailed analytics?",
                    "Troubleshoot an error": "I'm ready to help troubleshoot any errors you're experiencing. Please share the error message, when it occurred, and what you were trying to do. I can analyze logs, suggest solutions, and guide you through fixes."
                }
                
                ai_response = responses.get(suggestion, "I can help you with that! Please provide more details about what you need.")
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now(),
                    "attachments": []
                })
                
                st.rerun()
    
    # Export modal
    if st.session_state.get('show_export_modal', False):
        render_export_modal()
