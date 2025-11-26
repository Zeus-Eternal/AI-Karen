"""
Conversation Service Helper

This module provides helper functionality for conversation operations in KAREN AI system.
It handles conversation management, message processing, and other conversation-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConversationServiceHelper:
    """
    Helper service for conversation operations.
    
    This service provides methods for managing conversations, processing messages,
    and other conversation-related operations in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the conversation service helper.
        
        Args:
            config: Configuration dictionary for the conversation service
        """
        self.config = config
        self.conversation_enabled = config.get("conversation_enabled", True)
        self.max_conversations = config.get("max_conversations", 100)
        self.max_messages_per_conversation = config.get("max_messages_per_conversation", 1000)
        self.conversation_timeout = config.get("conversation_timeout", 3600)  # 1 hour
        self.message_timeout = config.get("message_timeout", 300)  # 5 minutes
        self.conversations = {}
        self.active_conversations = {}
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the conversation service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing conversation service")
            
            # Initialize conversation
            if self.conversation_enabled:
                await self._initialize_conversation()
                
            self._is_initialized = True
            logger.info("Conversation service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing conversation service: {str(e)}")
            return False
    
    async def _initialize_conversation(self) -> None:
        """Initialize conversation."""
        # In a real implementation, this would set up conversation
        logger.info("Initializing conversation")
        
    async def start(self) -> bool:
        """
        Start the conversation service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting conversation service")
            
            # Start conversation
            if self.conversation_enabled:
                await self._start_conversation()
                
            self._is_running = True
            logger.info("Conversation service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting conversation service: {str(e)}")
            return False
    
    async def _start_conversation(self) -> None:
        """Start conversation."""
        # In a real implementation, this would start conversation
        logger.info("Starting conversation")
        
    async def stop(self) -> bool:
        """
        Stop the conversation service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping conversation service")
            
            # Stop conversation
            if self.conversation_enabled:
                await self._stop_conversation()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Conversation service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping conversation service: {str(e)}")
            return False
    
    async def _stop_conversation(self) -> None:
        """Stop conversation."""
        # In a real implementation, this would stop conversation
        logger.info("Stopping conversation")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the conversation service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Conversation service is not initialized"}
                
            # Check conversation health
            conversation_health = {"status": "healthy", "message": "Conversation is healthy"}
            if self.conversation_enabled:
                conversation_health = await self._health_check_conversation()
                
            # Determine overall health
            overall_status = conversation_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Conversation service is {overall_status}",
                "conversation_health": conversation_health,
                "conversations_count": len(self.conversations),
                "active_conversations_count": len(self.active_conversations)
            }
            
        except Exception as e:
            logger.error(f"Error checking conversation service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_conversation(self) -> Dict[str, Any]:
        """Check conversation health."""
        # In a real implementation, this would check conversation health
        return {"status": "healthy", "message": "Conversation is healthy"}
        
    async def create_conversation(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Check if conversation is enabled
            if not self.conversation_enabled:
                return {"status": "error", "message": "Conversation is disabled"}
                
            # Get conversation parameters
            title = data.get("title") if data else None
            description = data.get("description") if data else None
            participants = data.get("participants", []) if data else []
            metadata = data.get("metadata", {}) if data else {}
            
            # Validate title
            if not title:
                return {"status": "error", "message": "Title is required for conversation"}
                
            # Check if we have reached the maximum number of conversations
            if len(self.conversations) >= self.max_conversations:
                return {"status": "error", "message": "Maximum number of conversations reached"}
                
            # Create conversation
            conversation_id = str(uuid.uuid4())
            conversation = {
                "conversation_id": conversation_id,
                "title": title,
                "description": description,
                "participants": participants,
                "messages": [],
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata,
                "context": context or {}
            }
            
            # Add conversation to active conversations
            self.active_conversations[conversation_id] = conversation
            
            return {
                "status": "success",
                "message": "Conversation created successfully",
                "conversation_id": conversation_id,
                "conversation": conversation
            }
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_conversation(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get conversation parameters
            conversation_id = data.get("conversation_id") if data else None
            
            # Validate conversation_id
            if not conversation_id:
                return {"status": "error", "message": "Conversation ID is required"}
                
            # Check if conversation is in active conversations
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations[conversation_id]
            else:
                # Check if conversation is in conversations
                if conversation_id in self.conversations:
                    conversation = self.conversations[conversation_id]
                else:
                    return {"status": "error", "message": f"Conversation {conversation_id} not found"}
                    
            return {
                "status": "success",
                "message": "Conversation retrieved successfully",
                "conversation_id": conversation_id,
                "conversation": conversation
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def update_conversation(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get conversation parameters
            conversation_id = data.get("conversation_id") if data else None
            title = data.get("title") if data else None
            description = data.get("description") if data else None
            participants = data.get("participants") if data else None
            status = data.get("status") if data else None
            metadata = data.get("metadata") if data else None
            
            # Validate conversation_id
            if not conversation_id:
                return {"status": "error", "message": "Conversation ID is required"}
                
            # Check if conversation is in active conversations
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations[conversation_id]
            else:
                # Check if conversation is in conversations
                if conversation_id in self.conversations:
                    conversation = self.conversations[conversation_id]
                else:
                    return {"status": "error", "message": f"Conversation {conversation_id} not found"}
                    
            # Update conversation
            if title is not None:
                conversation["title"] = title
            if description is not None:
                conversation["description"] = description
            if participants is not None:
                conversation["participants"] = participants
            if status is not None:
                conversation["status"] = status
            if metadata is not None:
                conversation["metadata"].update(metadata)
                
            # Update timestamp
            conversation["updated_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": "Conversation updated successfully",
                "conversation_id": conversation_id,
                "conversation": conversation
            }
            
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def delete_conversation(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delete a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get conversation parameters
            conversation_id = data.get("conversation_id") if data else None
            
            # Validate conversation_id
            if not conversation_id:
                return {"status": "error", "message": "Conversation ID is required"}
                
            # Check if conversation is in active conversations
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations.pop(conversation_id)
            else:
                # Check if conversation is in conversations
                if conversation_id in self.conversations:
                    conversation = self.conversations.pop(conversation_id)
                else:
                    return {"status": "error", "message": f"Conversation {conversation_id} not found"}
                    
            return {
                "status": "success",
                "message": "Conversation deleted successfully",
                "conversation_id": conversation_id,
                "conversation": conversation
            }
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def converse(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converse with a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Check if conversation is enabled
            if not self.conversation_enabled:
                return {"status": "error", "message": "Conversation is disabled"}
                
            # Get conversation parameters
            conversation_id = data.get("conversation_id") if data else None
            message = data.get("message") if data else None
            sender = data.get("sender") if data else None
            message_type = data.get("message_type", "text") if data else "text"
            
            # Validate conversation_id
            if not conversation_id:
                return {"status": "error", "message": "Conversation ID is required"}
                
            # Validate message
            if not message:
                return {"status": "error", "message": "Message is required for conversation"}
                
            # Validate sender
            if not sender:
                return {"status": "error", "message": "Sender is required for conversation"}
                
            # Check if conversation is in active conversations
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations[conversation_id]
            else:
                # Check if conversation is in conversations
                if conversation_id in self.conversations:
                    conversation = self.conversations[conversation_id]
                    # Move conversation to active conversations
                    self.conversations.pop(conversation_id)
                    self.active_conversations[conversation_id] = conversation
                else:
                    return {"status": "error", "message": f"Conversation {conversation_id} not found"}
                    
            # Check if we have reached the maximum number of messages
            if len(conversation["messages"]) >= self.max_messages_per_conversation:
                return {"status": "error", "message": "Maximum number of messages reached"}
                
            # Create message
            message_id = str(uuid.uuid4())
            message_obj = {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "sender": sender,
                "message": message,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add message to conversation
            conversation["messages"].append(message_obj)
            
            # Update conversation timestamp
            conversation["updated_at"] = datetime.now().isoformat()
            
            # Process message
            response = await self._process_message(conversation, message_obj, context)
            
            return {
                "status": "success",
                "message": "Message sent successfully",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "message": message_obj,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error conversing: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _process_message(self, conversation: Dict[str, Any], message: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message and generate a response."""
        # In a real implementation, this would process the message and generate a response
        logger.info(f"Processing message {message['message_id']} in conversation {conversation['conversation_id']}")
        
        # Get message details
        sender = message["sender"]
        message_text = message["message"]
        message_type = message["message_type"]
        
        # Simulate message processing
        await asyncio.sleep(0.5)
        
        # Generate response
        response_id = str(uuid.uuid4())
        response = {
            "message_id": response_id,
            "conversation_id": conversation["conversation_id"],
            "sender": "KAREN",
            "message": f"Response to: {message_text}",
            "message_type": message_type,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Add response to conversation
        conversation["messages"].append(response)
        
        return response
    
    async def list_conversations(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List conversations.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get list parameters
            status = data.get("status") if data else None
            participant = data.get("participant") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all conversations
            all_conversations = list(self.active_conversations.values()) + list(self.conversations.values())
                
            # Filter conversations based on parameters
            filtered_conversations = []
            for conversation in all_conversations:
                if status and conversation["status"] != status:
                    continue
                if participant and participant not in conversation["participants"]:
                    continue
                filtered_conversations.append(conversation)
                
            # Sort conversations by update time (newest first)
            filtered_conversations.sort(key=lambda x: x["updated_at"], reverse=True)
                
            # Apply pagination
            paginated_conversations = filtered_conversations[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Conversations listed successfully",
                "total_count": len(filtered_conversations),
                "limit": limit,
                "offset": offset,
                "conversations": paginated_conversations
            }
            
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def search_conversations(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search conversations.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get search parameters
            query = data.get("query") if data else None
            status = data.get("status") if data else None
            participant = data.get("participant") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            if not query:
                return {"status": "error", "message": "Query is required for search"}
                
            # Get all conversations
            all_conversations = list(self.active_conversations.values()) + list(self.conversations.values())
                
            # Search conversations based on query
            matched_conversations = []
            for conversation in all_conversations:
                # Check if conversation matches query
                conversation_json = json.dumps(conversation, default=str)
                if query.lower() in conversation_json.lower():
                    # Check additional filters
                    if status and conversation["status"] != status:
                        continue
                    if participant and participant not in conversation["participants"]:
                        continue
                    if start_time and conversation["created_at"] < start_time:
                        continue
                    if end_time and conversation["created_at"] > end_time:
                        continue
                    matched_conversations.append(conversation)
                    
            # Sort conversations by update time (newest first)
            matched_conversations.sort(key=lambda x: x["updated_at"], reverse=True)
                
            # Apply pagination
            paginated_conversations = matched_conversations[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Conversations searched successfully",
                "query": query,
                "total_count": len(matched_conversations),
                "limit": limit,
                "offset": offset,
                "conversations": paginated_conversations
            }
            
        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_conversation(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a conversation.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get analysis parameters
            conversation_id = data.get("conversation_id") if data else None
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            
            # Validate conversation_id
            if not conversation_id:
                return {"status": "error", "message": "Conversation ID is required"}
                
            # Check if conversation is in active conversations
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations[conversation_id]
            else:
                # Check if conversation is in conversations
                if conversation_id in self.conversations:
                    conversation = self.conversations[conversation_id]
                else:
                    return {"status": "error", "message": f"Conversation {conversation_id} not found"}
                    
            # Analyze based on analysis type
            if analysis_type == "summary":
                analysis = await self._analyze_conversation_summary(conversation)
            elif analysis_type == "messages":
                analysis = await self._analyze_conversation_messages(conversation)
            elif analysis_type == "participants":
                analysis = await self._analyze_conversation_participants(conversation)
            elif analysis_type == "timeline":
                analysis = await self._analyze_conversation_timeline(conversation)
            else:
                return {"status": "error", "message": f"Unsupported analysis type: {analysis_type}"}
                
            return {
                "status": "success",
                "message": "Conversation analyzed successfully",
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_conversation_summary(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation for summary statistics."""
        # Get conversation details
        title = conversation["title"]
        description = conversation["description"]
        participants = conversation["participants"]
        messages = conversation["messages"]
        status = conversation["status"]
        created_at = conversation["created_at"]
        updated_at = conversation["updated_at"]
        
        # Count messages by sender
        sender_counts = {}
        for message in messages:
            sender = message["sender"]
            if sender not in sender_counts:
                sender_counts[sender] = 0
            sender_counts[sender] += 1
                
        # Count messages by type
        type_counts = {}
        for message in messages:
            message_type = message["message_type"]
            if message_type not in type_counts:
                type_counts[message_type] = 0
            type_counts[message_type] += 1
                
        # Calculate conversation duration
        if messages:
            first_message_time = datetime.fromisoformat(messages[0]["timestamp"])
            last_message_time = datetime.fromisoformat(messages[-1]["timestamp"])
            duration = (last_message_time - first_message_time).total_seconds()
        else:
            duration = 0
            
        return {
            "analysis_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "conversation_id": conversation["conversation_id"],
            "title": title,
            "description": description,
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
            "participants_count": len(participants),
            "messages_count": len(messages),
            "sender_counts": sender_counts,
            "type_counts": type_counts,
            "duration_seconds": duration
        }
    
    async def _analyze_conversation_messages(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation messages."""
        # Get messages
        messages = conversation["messages"]
        
        # Count messages by sender
        sender_counts = {}
        for message in messages:
            sender = message["sender"]
            if sender not in sender_counts:
                sender_counts[sender] = 0
            sender_counts[sender] += 1
                
        # Count messages by type
        type_counts = {}
        for message in messages:
            message_type = message["message_type"]
            if message_type not in type_counts:
                type_counts[message_type] = 0
            type_counts[message_type] += 1
                
        # Calculate message lengths
        message_lengths = []
        for message in messages:
            message_length = len(message["message"])
            message_lengths.append(message_length)
            
        # Calculate statistics
        if message_lengths:
            min_length = min(message_lengths)
            max_length = max(message_lengths)
            avg_length = sum(message_lengths) / len(message_lengths)
            
            # Sort for median calculation
            message_lengths.sort()
            median_length = message_lengths[len(message_lengths) // 2]
        else:
            min_length = 0
            max_length = 0
            avg_length = 0
            median_length = 0
            
        return {
            "analysis_type": "messages",
            "generated_at": datetime.now().isoformat(),
            "conversation_id": conversation["conversation_id"],
            "messages_count": len(messages),
            "sender_counts": sender_counts,
            "type_counts": type_counts,
            "min_message_length": min_length,
            "max_message_length": max_length,
            "avg_message_length": avg_length,
            "median_message_length": median_length
        }
    
    async def _analyze_conversation_participants(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation participants."""
        # Get participants and messages
        participants = conversation["participants"]
        messages = conversation["messages"]
        
        # Count messages by participant
        participant_counts = {}
        for message in messages:
            sender = message["sender"]
            if sender not in participant_counts:
                participant_counts[sender] = 0
            participant_counts[sender] += 1
                
        # Calculate participant activity
        participant_activity = {}
        for participant in participants:
            if participant in participant_counts:
                activity = participant_counts[participant] / len(messages) if messages else 0
            else:
                activity = 0
            participant_activity[participant] = activity
                
        return {
            "analysis_type": "participants",
            "generated_at": datetime.now().isoformat(),
            "conversation_id": conversation["conversation_id"],
            "participants_count": len(participants),
            "participants": participants,
            "participant_counts": participant_counts,
            "participant_activity": participant_activity
        }
    
    async def _analyze_conversation_timeline(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation timeline."""
        # Get messages
        messages = conversation["messages"]
        
        # Group messages by day
        day_messages = {}
        for message in messages:
            timestamp = datetime.fromisoformat(message["timestamp"])
            day = timestamp.strftime("%Y-%m-%d")
            if day not in day_messages:
                day_messages[day] = []
            day_messages[day].append(message)
                
        # Calculate statistics for each day
        day_stats = {}
        for day, d_messages in day_messages.items():
            # Count messages by sender
            sender_counts = {}
            for message in d_messages:
                sender = message["sender"]
                if sender not in sender_counts:
                    sender_counts[sender] = 0
                sender_counts[sender] += 1
                
            day_stats[day] = {
                "messages_count": len(d_messages),
                "sender_counts": sender_counts
            }
                
        return {
            "analysis_type": "timeline",
            "generated_at": datetime.now().isoformat(),
            "conversation_id": conversation["conversation_id"],
            "messages_count": len(messages),
            "days_count": len(day_messages),
            "day_stats": day_stats
        }
        
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the conversation service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            status = {
                "conversation_enabled": self.conversation_enabled,
                "is_running": self._is_running,
                "conversations_count": len(self.conversations),
                "active_conversations_count": len(self.active_conversations),
                "max_conversations": self.max_conversations,
                "max_messages_per_conversation": self.max_messages_per_conversation,
                "conversation_timeout": self.conversation_timeout,
                "message_timeout": self.message_timeout
            }
            
            return {
                "status": "success",
                "message": "Conversation status retrieved successfully",
                "conversation_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the conversation service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Conversation service is not initialized"}
                
            # Get all conversations
            all_conversations = list(self.active_conversations.values()) + list(self.conversations.values())
                
            # Count by status
            status_counts = {}
            for conversation in all_conversations:
                status = conversation["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Count messages by type
            type_counts = {}
            total_messages = 0
            for conversation in all_conversations:
                for message in conversation["messages"]:
                    message_type = message["message_type"]
                    if message_type not in type_counts:
                        type_counts[message_type] = 0
                    type_counts[message_type] += 1
                    total_messages += 1
                
            # Calculate average messages per conversation
            avg_messages_per_conversation = total_messages / len(all_conversations) if all_conversations else 0
            
            stats = {
                "conversation_enabled": self.conversation_enabled,
                "is_running": self._is_running,
                "total_conversations": len(all_conversations),
                "conversations_count": len(self.conversations),
                "active_conversations_count": len(self.active_conversations),
                "max_conversations": self.max_conversations,
                "max_messages_per_conversation": self.max_messages_per_conversation,
                "conversation_timeout": self.conversation_timeout,
                "message_timeout": self.message_timeout,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "total_messages": total_messages,
                "avg_messages_per_conversation": avg_messages_per_conversation
            }
            
            return {
                "status": "success",
                "message": "Conversation statistics retrieved successfully",
                "conversation_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation statistics: {str(e)}")
            return {"status": "error", "message": str(e)}