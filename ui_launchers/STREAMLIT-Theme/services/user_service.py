"""
User Service for Kari AI Streamlit Console
Handles data access layer for user profiles
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

class UserService:
    """Service class for managing user data"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the user service"""
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.profiles_dir = os.path.join(data_dir, "profiles")
        self.conversations_dir = os.path.join(data_dir, "conversations")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        # Initialize users data
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Ensure the users file exists with default users"""
        if not os.path.exists(self.users_file):
            default_users = {
                "admin": {
                    "name": "Administrator",
                    "email": "admin@kari.ai",
                    "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
                    "role": "admin",
                    "preferences": {
                        "language": "English",
                        "timezone": "UTC",
                        "theme": "Dark Neon",
                        "notification_level": "All"
                    },
                    "account_type": "Premium",
                    "member_since": "Jan 2023",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                },
                "creator": {
                    "name": "Creator",
                    "email": "creator@kari.ai",
                    "password_hash": hashlib.sha256("creator123".encode()).hexdigest(),
                    "role": "creator",
                    "preferences": {
                        "language": "English",
                        "timezone": "UTC",
                        "theme": "Dark Neon",
                        "notification_level": "Important"
                    },
                    "account_type": "Premium",
                    "member_since": "Jan 2023",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                },
                "user": {
                    "name": "Demo User",
                    "email": "user@kari.ai",
                    "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
                    "role": "user",
                    "preferences": {
                        "language": "English",
                        "timezone": "UTC",
                        "theme": "Dark Neon",
                        "notification_level": "Important"
                    },
                    "account_type": "Standard",
                    "member_since": "Nov 2023",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                }
            }
            
            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """Get all users from the data store"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by username"""
        users = self.get_all_users()
        return users.get(username)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email address"""
        users = self.get_all_users()
        for username, user_data in users.items():
            if user_data.get('email') == email:
                return user_data
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        user = self.get_user(username)
        if not user:
            # Try to find by email
            user = self.get_user_by_email(username)
            if not user:
                return None
        
        # Check password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == user.get('password_hash'):
            # Update last login time
            users = self.get_all_users()
            for user_key, user_data in users.items():
                if user_data.get('email') == user.get('email'):
                    users[user_key]['last_login'] = datetime.now().isoformat()
                    self._save_users(users)
                    break
            
            return user
        
        return None
    
    def create_user(self, username: str, name: str, email: str, password: str, 
                  role: str = "user", account_type: str = "Standard") -> bool:
        """Create a new user"""
        if not username or not name or not email or not password:
            return False
        
        # Check if username already exists
        if self.get_user(username):
            return False
        
        # Check if email already exists
        if self.get_user_by_email(email):
            return False
        
        # Create new user
        new_user = {
            "name": name,
            "email": email,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "role": role,
            "preferences": {
                "language": "English",
                "timezone": "UTC",
                "theme": "Dark Neon",
                "notification_level": "Important"
            },
            "account_type": account_type,
            "member_since": datetime.now().strftime("%b %Y"),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        # Add to users
        users = self.get_all_users()
        users[username] = new_user
        self._save_users(users)
        
        # Create user profile file
        self._create_user_profile(username)
        
        return True
    
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update user data"""
        users = self.get_all_users()
        if username not in users:
            return False
        
        # Preserve certain fields
        preserved_fields = ['password_hash', 'created_at', 'member_since']
        for field in preserved_fields:
            if field in users[username] and field not in user_data:
                user_data[field] = users[username][field]
        
        # Update user
        users[username] = user_data
        self._save_users(users)
        
        # Update user profile
        self._update_user_profile(username, user_data)
        
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        users = self.get_all_users()
        if username not in users:
            return False
        
        # Remove from users
        del users[username]
        self._save_users(users)
        
        # Delete user profile file if it exists
        profile_file = os.path.join(self.profiles_dir, f"{username}.json")
        if os.path.exists(profile_file):
            os.remove(profile_file)
        
        # Delete user conversations if they exist
        conversation_file = os.path.join(self.conversations_dir, f"{username}.json")
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
        
        return True
    
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get extended user profile data"""
        profile_file = os.path.join(self.profiles_dir, f"{username}.json")
        
        if not os.path.exists(profile_file):
            # Create default profile
            user = self.get_user(username)
            if user:
                self._create_user_profile(username)
            else:
                return None
        
        try:
            with open(profile_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile data"""
        profile_file = os.path.join(self.profiles_dir, f"{username}.json")
        
        # Ensure profile file exists
        if not os.path.exists(profile_file):
            self._create_user_profile(username)
        
        try:
            # Load existing profile
            with open(profile_file, 'r') as f:
                existing_profile = json.load(f)
            
            # Update with new data
            existing_profile.update(profile_data)
            
            # Save updated profile
            with open(profile_file, 'w') as f:
                json.dump(existing_profile, f, indent=2)
            
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def get_user_conversations(self, username: str) -> List[Dict[str, Any]]:
        """Get user conversation history"""
        conversation_file = os.path.join(self.conversations_dir, f"{username}.json")
        
        if not os.path.exists(conversation_file):
            return []
        
        try:
            with open(conversation_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_user_conversation(self, username: str, conversation: Dict[str, Any]) -> bool:
        """Save a user conversation"""
        conversations = self.get_user_conversations(username)
        
        # Add timestamp if not present
        if 'timestamp' not in conversation:
            conversation['timestamp'] = datetime.now().isoformat()
        
        # Add to conversations
        conversations.append(conversation)
        
        # Save to file
        conversation_file = os.path.join(self.conversations_dir, f"{username}.json")
        try:
            with open(conversation_file, 'w') as f:
                json.dump(conversations, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]) -> bool:
        """Save users data to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def _create_user_profile(self, username: str) -> bool:
        """Create a default user profile"""
        user = self.get_user(username)
        if not user:
            return False
        
        profile_file = os.path.join(self.profiles_dir, f"{username}.json")
        
        default_profile = {
            "username": username,
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "interests": [],
            "expertise": [],
            "preferences": user.get("preferences", {}),
            "key_memories": [],
            "recent_activity": [],
            "knowledge_graph": {},
            "personalization": {
                "response_style": {
                    "formality": "Semi-formal",
                    "detail_level": "Balanced",
                    "tone": "Helpful",
                    "creativity": "Medium",
                    "technical_depth": "Medium-High",
                    "example_usage": "Included"
                },
                "content_preferences": {
                    "code_examples": True,
                    "visual_aids": True,
                    "step_by_step": True,
                    "analogies": False
                }
            },
            "created_at": user.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with open(profile_file, 'w') as f:
                json.dump(default_profile, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def _update_user_profile(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update user profile with user data"""
        profile = self.get_user_profile(username)
        if not profile:
            return False
        
        # Update basic info
        profile['name'] = user_data.get('name', profile['name'])
        profile['email'] = user_data.get('email', profile['email'])
        profile['preferences'] = user_data.get('preferences', profile.get('preferences', {}))
        profile['updated_at'] = datetime.now().isoformat()
        
        # Save updated profile
        profile_file = os.path.join(self.profiles_dir, f"{username}.json")
        try:
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

# Global user service instance
user_service = UserService()

# Standalone functions for easier importing
def get_user_profile(username):
    """Get user profile data"""
    return user_service.get_user_profile(username)