"""
Conversation Service for Kari AI Streamlit Console
Handles conversation history persistence and retrieval
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class ConversationService:
    """Service class for managing conversation data"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize conversation service"""
        self.data_dir = data_dir
        self.conversations_dir = os.path.join(data_dir, "conversations")
        self.sessions_dir = os.path.join(data_dir, "sessions")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def get_user_conversations(self, username: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        conversations_file = os.path.join(self.conversations_dir, f"{username}.json")
        
        if not os.path.exists(conversations_file):
            return []
        
        try:
            with open(conversations_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_user_conversation(self, username: str, conversation: Dict[str, Any]) -> bool:
        """Save a conversation for a user"""
        conversations = self.get_user_conversations(username)
        
        # Add timestamp if not present
        if 'timestamp' not in conversation:
            conversation['timestamp'] = datetime.now().isoformat()
        
        # Add ID if not present
        if 'id' not in conversation:
            conversation['id'] = str(uuid.uuid4())
        
        # Add to conversations
        conversations.append(conversation)
        
        # Save to file
        conversations_file = os.path.join(self.conversations_dir, f"{username}.json")
        try:
            with open(conversations_file, 'w') as f:
                json.dump(conversations, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def get_conversation_by_id(self, username: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation by ID"""
        conversations = self.get_user_conversations(username)
        
        for conversation in conversations:
            if conversation.get('id') == conversation_id:
                return conversation
        
        return None
    
    def update_conversation(self, username: str, conversation_id: str, updated_conversation: Dict[str, Any]) -> bool:
        """Update a specific conversation"""
        conversations = self.get_user_conversations(username)
        
        for i, conversation in enumerate(conversations):
            if conversation.get('id') == conversation_id:
                # Preserve certain fields
                preserved_fields = ['id', 'timestamp', 'created_at']
                for field in preserved_fields:
                    if field in conversation and field not in updated_conversation:
                        updated_conversation[field] = conversation[field]
                
                # Update the conversation
                conversations[i] = updated_conversation
                
                # Save to file
                conversations_file = os.path.join(self.conversations_dir, f"{username}.json")
                try:
                    with open(conversations_file, 'w') as f:
                        json.dump(conversations, f, indent=2)
                    return True
                except (FileNotFoundError, json.JSONDecodeError):
                    return False
        
        return False
    
    def delete_conversation(self, username: str, conversation_id: str) -> bool:
        """Delete a specific conversation"""
        conversations = self.get_user_conversations(username)
        
        for i, conversation in enumerate(conversations):
            if conversation.get('id') == conversation_id:
                # Remove the conversation
                del conversations[i]
                
                # Save to file
                conversations_file = os.path.join(self.conversations_dir, f"{username}.json")
                try:
                    with open(conversations_file, 'w') as f:
                        json.dump(conversations, f, indent=2)
                    return True
                except (FileNotFoundError, json.JSONDecodeError):
                    return False
        
        return False
    
    def create_session(self, username: str) -> str:
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        session_data = {
            "id": session_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "conversation_history": []
        }
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            return session_id
        except (FileNotFoundError, json.JSONDecodeError):
            return ""
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update a session"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        # Preserve certain fields
        existing_session = self.get_session(session_id)
        if existing_session:
            preserved_fields = ['id', 'username', 'created_at']
            for field in preserved_fields:
                if field in existing_session and field not in session_data:
                    session_data[field] = existing_session[field]
        
        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                return True
            except FileNotFoundError:
                return False
        
        return False
    
    def add_message_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Add message to conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        session['conversation_history'].append(message)
        
        # Update session
        return self.update_session(session_id, session)
    
    def get_recent_conversations(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for a user"""
        conversations = self.get_user_conversations(username)
        
        # Sort by timestamp (newest first)
        conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return limited number
        return conversations[:limit]
    
    def search_conversations(self, username: str, query: str) -> List[Dict[str, Any]]:
        """Search conversations for a user"""
        conversations = self.get_user_conversations(username)
        
        # Simple text search in conversation content
        results = []
        query_lower = query.lower()
        
        for conversation in conversations:
            # Search in title
            if 'title' in conversation and query_lower in conversation['title'].lower():
                results.append(conversation)
                continue
            
            # Search in messages
            if 'messages' in conversation:
                for message in conversation['messages']:
                    if 'content' in message and query_lower in message['content'].lower():
                        results.append(conversation)
                        break
        
        return results
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Clean up sessions older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('.json'):
                session_file = os.path.join(self.sessions_dir, filename)
                
                try:
                    with open(session_file, 'r') as f:
                        session = json.load(f)
                    
                    last_activity = session.get('last_activity', session.get('created_at', ''))
                    if last_activity:
                        try:
                            activity_date = datetime.fromisoformat(last_activity)
                            if activity_date < cutoff_date:
                                os.remove(session_file)
                                cleaned_count += 1
                        except ValueError:
                            pass
                except (FileNotFoundError, json.JSONDecodeError):
                    # Remove corrupted files
                    os.remove(session_file)
                    cleaned_count += 1
        
        return cleaned_count
    
    def export_conversations(self, username: str, format: str = 'json') -> Optional[str]:
        """Export user conversations in specified format"""
        conversations = self.get_user_conversations(username)
        
        if format == 'json':
            return json.dumps(conversations, indent=2)
        elif format == 'txt':
            # Simple text export
            text_export = ""
            for conv in conversations:
                text_export += f"=== {conv.get('title', 'Untitled')} ===\n"
                text_export += f"Date: {conv.get('timestamp', 'Unknown')}\n\n"
                
                if 'messages' in conv:
                    for msg in conv['messages']:
                        role = msg.get('role', 'Unknown')
                        content = msg.get('content', '')
                        timestamp = msg.get('timestamp', '')
                        
                        text_export += f"{role.capitalize()} ({timestamp}):\n{content}\n\n"
                
                text_export += "\n"
            
            return text_export
        else:
            return None

# Global conversation service instance
conversation_service = ConversationService()

# Standalone functions for easier importing
def create_conversation(user_id, title="New Conversation", messages=None):
    """Create a new conversation for a user"""
    if messages is None:
        messages = []
    
    conversation = {
        "title": title,
        "messages": messages,
        "user_id": user_id
    }
    
    # Save the conversation and return it
    success = conversation_service.save_user_conversation(user_id, conversation)
    if success:
        return conversation
    return None

def get_conversation(conversation_id, user_id=None):
    """Get a conversation by ID"""
    if user_id is None:
        # If no user_id provided, we can't find the conversation
        return None
    
    return conversation_service.get_conversation_by_id(user_id, conversation_id)

def get_user_conversations(user_id):
    """Get all conversations for a user"""
    return conversation_service.get_user_conversations(user_id)

def add_message_to_conversation(conversation_id, message, user_id=None):
    """Add a message to a conversation"""
    if user_id is None:
        return False
    
    # Get the conversation
    conversation = conversation_service.get_conversation_by_id(user_id, conversation_id)
    if not conversation:
        return False
    
    # Add the message
    if 'messages' not in conversation:
        conversation['messages'] = []
    
    conversation['messages'].append(message)
    
    # Update the conversation
    return conversation_service.update_conversation(user_id, conversation_id, conversation)

def delete_conversation(conversation_id, user_id=None):
    """Delete a conversation"""
    if user_id is None:
        return False
    
    return conversation_service.delete_conversation(user_id, conversation_id)

def search_conversations(user_id, query):
    """Search conversations for a user"""
    return conversation_service.search_conversations(user_id, query)

def create_session(user_id, session_id=None):
    """Create a new session for a user"""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    return conversation_service.create_session(user_id)

def get_session(session_id):
    """Get a session by ID"""
    return conversation_service.get_session(session_id)

def update_session(session_id, user_id=None, session_data=None):
    """Update a session"""
    if session_data is None:
        session_data = {}
    
    # Get the current session
    current_session = conversation_service.get_session(session_id)
    if not current_session:
        return False
    
    # Update with new data
    if user_id:
        session_data['username'] = user_id
    
    # Merge with existing session data
    merged_session = current_session.copy()
    merged_session.update(session_data)
    
    return conversation_service.update_session(session_id, merged_session)