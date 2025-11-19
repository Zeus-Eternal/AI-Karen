# Personal DB Integration Plan for Kari AI Lite Streamlit Console

## Overview
This document outlines the plan for enhancing personal database awareness and data integration in the Kari AI Lite Streamlit Console. The goal is to connect the UI with real user data, enabling personalized experiences and persistent conversation history.

## Current State Analysis
The current implementation uses hardcoded user data and doesn't connect to a real database:
- User ID is hardcoded as "dev_user"
- Personal context is static and not fetched from a database
- Conversation history is stored in session state only (lost on refresh)
- No authentication or user selection mechanism

## Implementation Plan

### 1. Data Access Layer

#### 1.1 Create Data Access Module
- Create `data_access.py` module to handle all database operations
- Implement functions for:
  - User profile retrieval
  - Personal context fetching
  - Conversation history persistence
  - User authentication/verification

#### 1.2 Database Connection Setup
- Configure connection to the Kari backend database
- Implement connection pooling and error handling
- Add environment variables for database configuration
- Implement retry logic for failed connections

### 2. User Authentication and Selection

#### 2.1 User Authentication Mechanism
- Implement simple authentication for development
- Add user login form in the sidebar
- Support for API key authentication
- Session management for authenticated users

#### 2.2 User Selection Interface
- Create user selection dropdown for development/testing
- Display user information in the sidebar
- Add user avatar/initials display
- Show user role and profile tags

### 3. User Profile Management

#### 3.1 User Profile Retrieval
- Fetch user profile from database
- Display user preferences and settings
- Show user language and timezone settings
- Display user role and capabilities

#### 3.2 User Profile Updates
- Allow users to update their preferences
- Save preference changes to database
- Sync preferences with backend
- Implement preference validation

### 4. Conversation History Persistence

#### 4.1 Conversation Storage
- Save conversations to database with user ID
- Store conversation metadata (model used, plugins, response time)
- Implement conversation tagging and search
- Add conversation export functionality

#### 4.2 Conversation Retrieval
- Load conversation history from database
- Implement pagination for long conversation histories
- Add conversation search and filtering
- Support conversation resumption

### 5. Personal Context Integration

#### 5.1 Context Fetching
- Retrieve user's personal context from database
- Fetch recent user activity and interactions
- Load user memories and preferences
- Get user's current projects and tasks

#### 5.2 Context Display
- Display personal context in the right sidebar
- Show recent activity and memories
- Highlight relevant context for current conversation
- Add context refresh mechanism

### 6. Implementation Details

#### 6.1 Data Access Layer Implementation

```python
# data_access.py
import os
import requests
import json
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class DataAccessLayer:
    def __init__(self):
        self.backend_url = os.getenv("KARI_BACKEND_URL", "http://localhost:8000/api")
        self.api_key = os.getenv("KARI_API_KEY", "")
        self.timeout = int(os.getenv("RESPONSE_TIMEOUT", "30"))
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Fetch user profile from database"""
        try:
            response = requests.get(
                f"{self.backend_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Fallback to default profile for development
            return {
                "user_id": user_id,
                "name": user_id,
                "role": "Creator",
                "preferences": {
                    "language": "English",
                    "timezone": "UTC"
                }
            }
    
    def get_user_context(self, user_id: str) -> Dict:
        """Fetch personal context including recent activity and memories"""
        try:
            response = requests.get(
                f"{self.backend_url}/users/{user_id}/context",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Fallback to default context for development
            return {
                "recent_activity": [
                    "Created new project",
                    "Updated documentation"
                ],
                "key_memories": [
                    "Prefers concise responses",
                    "Working on AI project"
                ],
                "current_projects": [
                    {"name": "Kari AI", "status": "active"}
                ]
            }
    
    def save_conversation(self, user_id: str, conversation: List[Dict]) -> bool:
        """Save conversation to database"""
        try:
            response = requests.post(
                f"{self.backend_url}/conversations",
                json={
                    "user_id": user_id,
                    "conversation": conversation
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Fetch conversation history from database"""
        try:
            response = requests.get(
                f"{self.backend_url}/conversations/{user_id}",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("conversations", [])
        except Exception as e:
            print(f"Error fetching conversation history: {e}")
            return []
```

#### 6.2 Enhanced Session State Initialization

```python
# Enhanced session state initialization in index.py
def init_session_state():
    # Initialize data access layer
    if 'data_access' not in st.session_state:
        st.session_state.data_access = DataAccessLayer()
    
    # User authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}
    
    if 'user_context' not in st.session_state:
        st.session_state.user_context = {}
    
    # Initialize other session state variables
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = os.getenv("DEFAULT_USER_ID", "dev_user")
    
    # Load user profile and context if authenticated
    if st.session_state.authenticated and st.session_state.user_id:
        if not st.session_state.user_profile:
            st.session_state.user_profile = st.session_state.data_access.get_user_profile(st.session_state.user_id)
        
        if not st.session_state.user_context:
            st.session_state.user_context = st.session_state.data_access.get_user_context(st.session_state.user_id)
    
    # Rest of existing session state initialization...
```

#### 6.3 User Authentication Interface

```python
# User authentication in sidebar
def render_user_authentication():
    st.markdown("### User Authentication")
    
    if not st.session_state.authenticated:
        # Simple login form for development
        with st.form("login_form"):
            user_id = st.text_input("User ID", value=st.session_state.user_id)
            api_key = st.text_input("API Key", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # For development, accept any user ID
                st.session_state.user_id = user_id
                st.session_state.authenticated = True
                
                # Load user profile and context
                st.session_state.user_profile = st.session_state.data_access.get_user_profile(user_id)
                st.session_state.user_context = st.session_state.data_access.get_user_context(user_id)
                
                # Load conversation history
                history = st.session_state.data_access.get_conversation_history(user_id)
                if history:
                    st.session_state.conversation_history = history
                
                st.success("Logged in successfully!")
                st.rerun()
    else:
        # Display user info and logout option
        user_profile = st.session_state.user_profile
        st.markdown(f"**Logged in as:** {user_profile.get('name', st.session_state.user_id)}")
        st.markdown(f"**Role:** {user_profile.get('role', 'User')}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_profile = {}
            st.session_state.user_context = {}
            st.session_state.conversation_history = []
            st.rerun()
```

#### 6.4 Enhanced Personal Context Display

```python
# Enhanced personal context display in right sidebar
def render_enhanced_personal_context():
    st.markdown("### Personal Context")
    
    if st.session_state.authenticated and st.session_state.user_context:
        user_context = st.session_state.user_context
        
        # User preferences
        with st.expander("Preferences", expanded=True):
            user_profile = st.session_state.user_profile
            preferences = user_profile.get('preferences', {})
            st.json(preferences)
        
        # Recent activity
        with st.expander("Recent Activity", expanded=True):
            activities = user_context.get('recent_activity', [])
            for activity in activities:
                st.markdown(f"- {activity}")
        
        # Key memories
        with st.expander("Key Memories", expanded=True):
            memories = user_context.get('key_memories', [])
            for memory in memories:
                st.markdown(f"- {memory}")
        
        # Current projects
        with st.expander("Current Projects", expanded=True):
            projects = user_context.get('current_projects', [])
            for project in projects:
                status_color = "green" if project.get('status') == 'active' else "gray"
                st.markdown(f"- <span style='color:{status_color}'>{project.get('name')}</span>", unsafe_allow_html=True)
        
        # Context refresh button
        if st.button("Refresh Context"):
            with st.spinner("Refreshing context..."):
                st.session_state.user_context = st.session_state.data_access.get_user_context(st.session_state.user_id)
                st.success("Context refreshed!")
                st.rerun()
    else:
        st.info("Please log in to view personal context.")
```

#### 6.5 Conversation History Persistence

```python
# Enhanced conversation handling
def save_conversation_to_db():
    """Save current conversation to database"""
    if st.session_state.authenticated and st.session_state.conversation_history:
        success = st.session_state.data_access.save_conversation(
            st.session_state.user_id,
            st.session_state.conversation_history
        )
        if success:
            st.toast("Conversation saved!", icon="💾")
        else:
            st.toast("Failed to save conversation", icon="⚠️")

# Modify the chat submission handler to save conversations
def handle_chat_submission(user_input):
    # Add user message to conversation
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })
    
    # Simulate processing and response
    with st.spinner("Thinking..."):
        response, metadata = simulate_backend_call(user_input)
    
    # Add assistant response to conversation
    st.session_state.conversation_history.append({
        'role': 'assistant',
        'content': response,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata
    })
    
    # Save conversation to database
    save_conversation_to_db()
    
    # Rerun to update the chat
    st.rerun()
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
DEFAULT_MODEL=llama-cpp
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

# Database Configuration
DB_CONNECTION_URL=postgresql://user:password@localhost/kari_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

#### 7.2 Update requirements.txt

```
streamlit>=1.28.0
requests>=2.28.0
python-dotenv>=1.0.0
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
```

### 8. Integration Points

#### 8.1 Integration with Existing Components

1. **Left Sidebar Integration**:
   - Add user authentication section
   - Display user information
   - Add context refresh controls

2. **Chat Zone Integration**:
   - Save conversations to database
   - Load conversation history
   - Display user-specific context in responses

3. **Right Sidebar Integration**:
   - Enhance personal context display
   - Add user preferences section
   - Show recent activity and memories

#### 8.2 Error Handling and Fallbacks

1. **Database Connection Errors**:
   - Implement retry logic
   - Provide fallback to local data
   - Display error messages to users

2. **Authentication Errors**:
   - Handle invalid credentials
   - Provide clear error messages
   - Offer retry options

3. **Data Sync Issues**:
   - Implement conflict resolution
   - Provide manual sync options
   - Show sync status indicators

### 9. Testing Strategy

#### 9.1 Unit Testing
- Test data access layer functions
- Test authentication mechanisms
- Test conversation persistence

#### 9.2 Integration Testing
- Test end-to-end user flows
- Test database connectivity
- Test conversation history loading

#### 9.3 User Acceptance Testing
- Test with real user data
- Test conversation persistence
- Test personal context display

### 10. Success Metrics

1. **User Authentication**:
   - Successful login rate
   - Authentication error rate

2. **Data Persistence**:
   - Conversation save success rate
   - Conversation load success rate

3. **Personal Context**:
   - Context refresh success rate
   - Context display accuracy

### 11. Rollout Plan

#### 11.1 Phase 1: Basic Data Access
- Implement data access layer
- Add basic user authentication
- Implement conversation persistence

#### 11.2 Phase 2: Enhanced Features
- Add personal context display
- Implement conversation history loading
- Add user preferences

#### 11.3 Phase 3: Advanced Features
- Add conversation search and filtering
- Implement conversation export
- Add advanced user preferences

## Conclusion

This plan outlines a comprehensive approach to enhancing personal DB awareness and data integration in the Kari AI Lite Streamlit Console. By implementing these features, we'll create a more personalized and persistent user experience that meets the requirements outlined in the specification document.

The implementation will be done in phases, starting with basic data access and authentication, then moving to more advanced features like personal context display and conversation history management.