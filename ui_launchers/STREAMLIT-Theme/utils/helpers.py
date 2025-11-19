"""
Helper utilities for Kari AI Streamlit Console
"""

import time
import streamlit as st
from datetime import datetime, timedelta

def get_relative_time(dt):
    """Get relative time string from datetime object"""
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
    try:
        # Try to use pyperclip if available
        import pyperclip
        pyperclip.copy(text)
        return True
    except:
        # Fallback for environments without pyperclip
        return False

def insert_formatting(before, after):
    """Insert formatting around selected text in input"""
    # This would be implemented with JavaScript in a real application
    # For Streamlit, we'll just append the formatting
    if 'input_text' in st.session_state:
        st.session_state.input_text += before + "text" + after
        st.rerun()

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp)
        return get_relative_time(dt)
    except:
        return timestamp