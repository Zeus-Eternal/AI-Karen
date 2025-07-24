"""
Chat service for integrating with AI Karen backend LLMs
"""

import requests
import json
import os
from typing import Dict, Any, Optional, List
import streamlit as st

from helpers.eco_mode import EcoModeResponder


class ChatService:
    """Service for handling chat interactions with AI Karen backend"""
    
    def __init__(self):
        self.api_url = os.getenv("KARI_API_URL", "http://localhost:8001")
        self.session = requests.Session()
        self._eco_responder: EcoModeResponder | None = None

    def _ensure_eco_responder(self) -> EcoModeResponder:
        if self._eco_responder is None:
            self._eco_responder = EcoModeResponder()
        return self._eco_responder
        
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available LLM models from backend"""
        try:
            response = self.session.get(f"{self.api_url}/models")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            else:
                st.error(f"Failed to fetch models: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
            return []
    
    def select_model(self, model_name: str) -> bool:
        """Select active model for chat"""
        try:
            response = self.session.post(
                f"{self.api_url}/models/select",
                json={"model": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"Error selecting model: {e}")
            return False
    
    def send_message(self, message: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Send message to AI Karen backend and get response"""
        headers = {}
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        
        try:
            response = self.session.post(
                f"{self.api_url}/chat",
                json={"text": message},
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "response": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            response = self.session.get(f"{self.api_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"Health check failed: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_ai_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """Generate AI response using the backend LLM"""
        if st.session_state.get("eco_mode"):
            responder = self._ensure_eco_responder()
            return responder.respond(user_message)

        # Get user token from session
        user_token = st.session_state.get("token")
        
        # Send message to backend
        result = self.send_message(user_message, user_token)
        
        if result["success"]:
            response_data = result["response"]
            
            # Extract the actual response text based on the API structure
            if isinstance(response_data, dict):
                # Try different possible response fields
                response_text = (
                    response_data.get("response") or 
                    response_data.get("text") or 
                    response_data.get("content") or
                    response_data.get("message") or
                    str(response_data)
                )
                
                # Add confidence and intent info if available
                confidence = response_data.get("confidence", 0.0)
                intent = response_data.get("intent", "general")
                
                if confidence > 0:
                    response_text += f"\n\n*[Confidence: {confidence:.2f}, Intent: {intent}]*"
                
                return response_text
            else:
                return str(response_data)
        else:
            error_msg = result.get("error", "Unknown error")
            return f"I apologize, but I encountered an error: {error_msg}. Please try again or contact support if the issue persists."


# Create singleton instance
chat_service = ChatService()