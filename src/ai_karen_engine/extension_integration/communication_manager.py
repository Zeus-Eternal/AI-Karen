"""
Extension Communication Manager - Inter-extension messaging and communication system.

This module provides comprehensive communication including:
- Inter-extension message passing
- Event-driven communication patterns
- Extension service discovery and registration
- Secure communication channels
- Message routing and filtering
- Communication audit and monitoring
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from uuid import uuid4

from ai_karen_engine.extension_host.models import ExtensionManifest, ExtensionRecord, ExtensionStatus


class MessageType(Enum):
    """Types of messages that can be sent between extensions."""
    
    REQUEST = "request"          # Request for service or data
    RESPONSE = "response"        # Response to a request
    EVENT = "event"            # Event notification
    COMMAND = "command"          # Command to be executed
    DATA = "data"              # Data sharing
    HEARTBEAT = "heartbeat"     # Health check
    ERROR = "error"             # Error notification


class MessagePriority(Enum):
    """Priority levels for inter-extension messages."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ExtensionMessage:
    """Message sent between extensions."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    type: MessageType
    sender: str
    recipient: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    ttl: Optional[int] = None  # Time to live in seconds
    requires_response: bool = False
    response_to: Optional[str] = None  # Message ID to respond to
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "payload": self.payload,
            "headers": self.headers,
            "ttl": self.ttl,
            "requires_response": self.requires_response,
            "response_to": self.response_to,
        }


@dataclass
class ExtensionService:
    """Service provided by an extension for other extensions to use."""
    
    name: str
    extension_id: str
    description: str
    version: str
    methods: List[str]  # HTTP methods or function names
    schema: Dict[str, Any]  # JSON schema for requests/responses
    endpoint: Optional[str] = None  # URL endpoint if HTTP-based
    handler: Optional[Callable] = None  # Async function to handle calls
    enabled: bool = True
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    usage_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class CommunicationChannel:
    """Communication channel between extensions."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str  # direct, event_bus, queue, etc.
    participants: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    bytes_transferred: int = 0
    is_encrypted: bool = False
    max_message_size: int = 1024 * 1024  # 1MB
    ttl: Optional[int] = None  # Channel TTL in seconds


class ExtensionCommunicationManager:
    """
    Comprehensive extension communication manager.
    
    Provides:
    - Inter-extension message passing and routing
    - Extension service discovery and registration
    - Event-driven communication patterns
    - Secure communication channels
    - Message filtering and prioritization
    - Communication audit and monitoring
    """
    
    def __init__(
        self,
        enable_event_bus: bool = True,
        max_message_size: int = 1024 * 1024,
        channel_ttl: int = 3600,  # 1 hour
        enable_encryption: bool = False,
        audit_logging: bool = True
    ):
        """
        Initialize the communication manager.
        
        Args:
            enable_event_bus: Whether to enable event bus communication
            max_message_size: Maximum message size in bytes
            channel_ttl: Default channel TTL in seconds
            enable_encryption: Whether to enable message encryption
            audit_logging: Whether to enable audit logging
        """
        self.enable_event_bus = enable_event_bus
        self.max_message_size = max_message_size
        self.channel_ttl = channel_ttl
        self.enable_encryption = enable_encryption
        self.audit_logging = audit_logging
        
        # Communication state
        self.channels: Dict[str, CommunicationChannel] = {}
        self.services: Dict[str, ExtensionService] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.message_history: List[ExtensionMessage] = []
        
        # Event bus
        self.event_listeners: Dict[str, List[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        self.logger = logging.getLogger("extension.communication_manager")
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        self.logger.info("Extension communication manager initialized")
    
    async def initialize(self) -> None:
        """Initialize the communication manager."""
        self.logger.info("Initializing extension communication manager")
        
        try:
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.logger.info("Extension communication manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize communication manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the communication manager."""
        self.logger.info("Shutting down extension communication manager")
        
        try:
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._monitor_task:
                self._monitor_task.cancel()
            
            # Clear all state
            self.channels.clear()
            self.services.clear()
            self.message_handlers.clear()
            self.message_history.clear()
            self.event_listeners.clear()
            
            self.logger.info("Extension communication manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown communication manager: {e}")
    
    async def register_service(
        self,
        extension_id: str,
        service: ExtensionService
    ) -> bool:
        """
        Register a service provided by an extension.
        
        Args:
            extension_id: ID of the extension providing the service
            service: Service description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate service
            if not self._validate_service(service):
                self.logger.error(f"Invalid service registration from {extension_id}: {service.name}")
                return False
            
            # Register service
            service_key = f"{extension_id}:{service.name}"
            self.services[service_key] = service
            
            # Notify interested extensions
            await self._notify_service_registered(extension_id, service)
            
            self.logger.info(f"Service {service.name} registered by extension {extension_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register service {service.name}: {e}")
            return False
    
    async def unregister_service(
        self,
        extension_id: str,
        service_name: str
    ) -> bool:
        """
        Unregister a service provided by an extension.
        
        Args:
            extension_id: ID of the extension providing the service
            service_name: Name of the service to unregister
            
        Returns:
            True if successful, False otherwise
        """
        try:
            service_key = f"{extension_id}:{service_name}"
            
            if service_key in self.services:
                del self.services[service_key]
                
                # Notify interested extensions
                await self._notify_service_unregistered(extension_id, service_name)
                
                self.logger.info(f"Service {service_name} unregistered by extension {extension_id}")
                return True
            else:
                self.logger.warning(f"Service {service_name} not found for extension {extension_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unregister service {service_name}: {e}")
            return False
    
    async def discover_services(self) -> Dict[str, List[ExtensionService]]:
        """
        Discover all available services from extensions.
        
        Returns:
            Dictionary mapping extension IDs to their services
        """
        try:
            discovered_services = {}
            
            for service_key, service in self.services.items():
                extension_id = service_key.split(':')[0]
                
                if extension_id not in discovered_services:
                    discovered_services[extension_id] = []
                
                discovered_services[extension_id].append(service)
            
            self.logger.info(f"Discovered {len(discovered_services)} extensions with services")
            return discovered_services
            
        except Exception as e:
            self.logger.error(f"Failed to discover services: {e}")
            return {}
    
    async def send_message(
        self,
        message: ExtensionMessage,
        channel_type: str = "direct"
    ) -> bool:
        """
        Send a message to another extension or service.
        
        Args:
            message: Message to send
            channel_type: Type of channel to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate message
            if not self._validate_message(message):
                self.logger.error(f"Invalid message: {message.id}")
                return False
            
            # Check message size
            if len(json.dumps(message.payload).encode()) > self.max_message_size:
                self.logger.warning(f"Message {message.id} exceeds maximum size")
                return False
            
            # Route message
            if channel_type == "direct":
                return await self._send_direct_message(message)
            elif channel_type == "event_bus":
                return await self._send_event_bus_message(message)
            elif channel_type == "queue":
                return await self._send_queue_message(message)
            else:
                self.logger.error(f"Unknown channel type: {channel_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message {message.id}: {e}")
            return False
    
    async def _send_direct_message(self, message: ExtensionMessage) -> bool:
        """Send a direct message to an extension."""
        try:
            # Check if recipient is available
            if not self._is_extension_available(message.recipient):
                self.logger.warning(f"Extension {message.recipient} not available for direct message")
                return False
            
            # Get or create channel
            channel = await self._get_or_create_channel(message.sender, message.recipient)
            
            # Send message through channel
            channel.participants.add(message.sender)
            channel.participants.add(message.recipient)
            channel.last_activity = datetime.now(timezone.utc)
            channel.message_count += 1
            
            # Store message
            self.message_history.append(message)
            
            # Notify recipient
            await self._notify_message_received(message)
            
            self.logger.info(f"Direct message sent from {message.sender} to {message.recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send direct message {message.id}: {e}")
            return False
    
    async def _send_event_bus_message(self, message: ExtensionMessage) -> bool:
        """Send a message through the event bus."""
        try:
            # Add to event queue
            await self.event_queue.put(message)
            
            # Store message
            self.message_history.append(message)
            
            # Notify all listeners
            await self._notify_event_bus_message(message)
            
            self.logger.info(f"Event bus message sent: {message.type.value} from {message.sender}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send event bus message {message.id}: {e}")
            return False
    
    async def _send_queue_message(self, message: ExtensionMessage) -> bool:
        """Send a message through a queue channel."""
        try:
            # Find or create queue channel
            channel = await self._get_or_create_queue_channel()
            
            # Add to queue
            channel.participants.add(message.sender)
            channel.last_activity = datetime.now(timezone.utc)
            channel.message_count += 1
            
            # Store message
            self.message_history.append(message)
            
            self.logger.info(f"Queue message sent: {message.type.value} from {message.sender}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send queue message {message.id}: {e}")
            return False
    
    async def _get_or_create_channel(
        self,
        sender: str,
        recipient: str
    ) -> Optional[CommunicationChannel]:
        """Get or create a direct communication channel."""
        try:
            # Generate channel ID
            channel_id = f"{sender}:{recipient}"
            
            # Check if channel exists
            if channel_id in self.channels:
                channel = self.channels[channel_id]
                channel.participants.add(sender)
                channel.participants.add(recipient)
                channel.last_activity = datetime.now(timezone.utc)
                return channel
            
            # Create new channel
            channel = CommunicationChannel(
                id=channel_id,
                type="direct",
                participants={sender, recipient},
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_encrypted=self.enable_encryption
            )
            
            self.channels[channel_id] = channel
            
            self.logger.info(f"Created direct channel: {channel_id}")
            return channel
            
        except Exception as e:
            self.logger.error(f"Failed to create channel {channel_id}: {e}")
            return None
    
    async def _get_or_create_queue_channel(self) -> Optional[CommunicationChannel]:
        """Get or create a queue communication channel."""
        try:
            # Generate channel ID
            channel_id = f"queue:{uuid4().hex[:8]}"
            
            # Check if channel exists
            if channel_id in self.channels:
                channel = self.channels[channel_id]
                channel.last_activity = datetime.now(timezone.utc)
                return channel
            
            # Create new channel
            channel = CommunicationChannel(
                id=channel_id,
                type="queue",
                participants=set(),
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_encrypted=self.enable_encryption
            )
            
            self.channels[channel_id] = channel
            
            self.logger.info(f"Created queue channel: {channel_id}")
            return channel
            
        except Exception as e:
            self.logger.error(f"Failed to create queue channel: {channel_id}: {e}")
            return None
    
    def _is_extension_available(self, extension_id: str) -> bool:
        """Check if an extension is available for communication."""
        # This would integrate with the extension lifecycle manager
        # For now, return True as a placeholder
        return True
    
    async def _notify_message_received(self, message: ExtensionMessage) -> None:
        """Notify an extension that it received a message."""
        try:
            # Get message handlers for the recipient
            handlers = self.message_handlers.get(message.recipient, [])
            
            # Call all handlers
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    self.logger.error(f"Message handler error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to notify message received: {e}")
    
    async def _notify_service_registered(self, extension_id: str, service: ExtensionService) -> None:
        """Notify extensions that a service was registered."""
        try:
            # Create event message
            message = ExtensionMessage(
                type=MessageType.EVENT,
                sender="system",
                recipient="broadcast",
                payload={
                    "event": "service_registered",
                    "extension_id": extension_id,
                    "service": service.to_dict()
                }
            )
            
            # Send through event bus
            if self.enable_event_bus:
                await self._send_event_bus_message(message)
            
        except Exception as e:
            self.logger.error(f"Failed to notify service registered: {e}")
    
    async def _notify_service_unregistered(self, extension_id: str, service_name: str) -> None:
        """Notify extensions that a service was unregistered."""
        try:
            # Create event message
            message = ExtensionMessage(
                type=MessageType.EVENT,
                sender="system",
                recipient="broadcast",
                payload={
                    "event": "service_unregistered",
                    "extension_id": extension_id,
                    "service_name": service_name
                }
            )
            
            # Send through event bus
            if self.enable_event_bus:
                await self._send_event_bus_message(message)
            
        except Exception as e:
            self.logger.error(f"Failed to notify service unregistered: {e}")
    
    async def _notify_event_bus_message(self, message: ExtensionMessage) -> None:
        """Notify event bus listeners of a message."""
        try:
            # Get listeners for message type
            listeners = self.event_listeners.get(message.type.value, [])
            
            # Notify all listeners
            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(message)
                    else:
                        listener(message)
                except Exception as e:
                    self.logger.error(f"Event bus listener error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to notify event bus message: {e}")
    
    def _validate_message(self, message: ExtensionMessage) -> bool:
        """Validate a message before sending."""
        try:
            # Check required fields
            if not message.id or not message.sender or not message.recipient:
                return False
            
            # Check message size
            message_size = len(json.dumps(message.payload).encode())
            if message_size > self.max_message_size:
                return False
            
            # Check TTL
            if message.ttl and message.ttl <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate message: {e}")
            return False
    
    def _validate_service(self, service: ExtensionService) -> bool:
        """Validate a service before registration."""
        try:
            # Check required fields
            if not service.name or not service.extension_id:
                return False
            
            # Check methods
            if not service.methods:
                return False
            
            # Check schema
            if not service.schema:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate service: {e}")
            return False
    
    async def register_message_handler(
        self,
        extension_id: str,
        message_type: MessageType,
        handler: Callable[[ExtensionMessage], None]
    ) -> bool:
        """
        Register a handler for specific message types.
        
        Args:
            extension_id: ID of the extension
            message_type: Type of messages to handle
            handler: Handler function
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to handlers
            if extension_id not in self.message_handlers:
                self.message_handlers[extension_id] = {}
            
            self.message_handlers[extension_id][message_type.value] = handler
            
            self.logger.info(f"Registered message handler for {extension_id}: {message_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register message handler: {e}")
            return False
    
    async def unregister_message_handler(
        self,
        extension_id: str,
        message_type: MessageType
    ) -> bool:
        """
        Unregister a message handler.
        
        Args:
            extension_id: ID of the extension
            message_type: Type of messages to handle
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if extension_id in self.message_handlers:
                handlers = self.message_handlers[extension_id]
                if message_type.value in handlers:
                    del handlers[message_type.value]
                    
                    self.logger.info(f"Unregistered message handler for {extension_id}: {message_type.value}")
                    return True
            
            self.logger.warning(f"No message handler found for {extension_id}: {message_type.value}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to unregister message handler: {e}")
            return False
    
    async def call_service(
        self,
        extension_id: str,
        service_name: str,
        method: str,
        params: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Call a service provided by an extension.
        
        Args:
            extension_id: ID of the extension providing the service
            service_name: Name of the service to call
            method: Method to call
            params: Parameters for the method call
            timeout: Call timeout in seconds
            
        Returns:
            Service response or error
        """
        try:
            service_key = f"{extension_id}:{service_name}"
            
            if service_key not in self.services:
                return {"error": f"Service {service_name} not found"}
            
            service = self.services[service_key]
            
            if method not in service.methods:
                return {"error": f"Method {method} not supported by service {service_name}"}
            
            if not service.handler:
                return {"error": f"Service {service_name} has no handler"}
            
            # Call service handler
            try:
                if asyncio.iscoroutinefunction(service.handler):
                    result = await asyncio.wait_for(
                        service.handler(method, params),
                        timeout=timeout or 30.0
                    )
                else:
                    result = service.handler(method, params)
                    
                # Update usage stats
                service.usage_stats[method] = service.usage_stats.get(method, 0) + 1
                
                return {
                    "result": result,
                    "service": service_name,
                    "method": method,
                    "extension_id": extension_id
                }
                
            except asyncio.TimeoutError:
                return {"error": f"Service call to {service_name}.{method} timed out"}
            except Exception as e:
                return {"error": f"Service call failed: {str(e)}"}
                
        except Exception as e:
            self.logger.error(f"Failed to call service {service_name}: {e}")
            return {"error": f"Communication error: {str(e)}"}
    
    def get_service_info(self, extension_id: str, service_name: str) -> Optional[ExtensionService]:
        """Get information about a specific service."""
        try:
            service_key = f"{extension_id}:{service_name}"
            return self.services.get(service_key)
            
        except Exception as e:
            self.logger.error(f"Failed to get service info: {e}")
            return None
    
    def get_all_services(self) -> Dict[str, List[ExtensionService]]:
        """Get all registered services."""
        try:
            all_services = {}
            
            for service_key, service in self.services.items():
                extension_id = service_key.split(':')[0]
                
                if extension_id not in all_services:
                    all_services[extension_id] = []
                
                all_services[extension_id].append(service)
            
            return all_services
            
        except Exception as e:
            self.logger.error(f"Failed to get all services: {e}")
            return {}
    
    def get_message_history(
        self,
        extension_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ExtensionMessage]:
        """Get message history for an extension or all extensions."""
        try:
            messages = self.message_history
            
            # Filter by extension
            if extension_id:
                messages = [msg for msg in messages if msg.recipient == extension_id]
            
            # Limit results
            if limit > 0:
                messages = messages[-limit:]
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get message history: {e}")
            return []
    
    def get_channel_info(self, channel_id: str) -> Optional[CommunicationChannel]:
        """Get information about a communication channel."""
        try:
            return self.channels.get(channel_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get channel info: {e}")
            return None
    
    def get_all_channels(self) -> Dict[str, CommunicationChannel]:
        """Get all communication channels."""
        try:
            return self.channels.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to get all channels: {e}")
            return {}
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        try:
            total_messages = len(self.message_history)
            total_channels = len(self.channels)
            total_services = len(self.services)
            
            return {
                "total_messages": total_messages,
                "total_channels": total_channels,
                "total_services": total_services,
                "active_channels": len([
                    ch for ch in self.channels.values()
                    if ch.last_activity > datetime.now(timezone.utc).timestamp() - 300  # Active in last 5 minutes
                ]),
                "message_types": {
                    msg_type.value: len([
                        msg for msg in self.message_history
                        if msg.type == msg_type
                    ])
                    for msg_type in MessageType
                },
                "channel_types": {
                    ch_type: len([
                        ch for ch in self.channels.values()
                        if ch.type == ch_type
                    ])
                    for ch_type in ["direct", "queue", "event_bus"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get communication stats: {e}")
            return {"error": str(e)}
    
    async def _cleanup_loop(self) -> None:
        """Cleanup old channels and messages."""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Clean up old channels
            channels_to_remove = []
            for channel_id, channel in self.channels.items():
                if (current_time - channel.last_activity).total_seconds() > self.channel_ttl:
                    channels_to_remove.append(channel_id)
            
            for channel_id in channels_to_remove:
                del self.channels[channel_id]
            
            # Clean up old messages
            messages_to_remove = []
            for message in self.message_history:
                if (current_time - message.timestamp).total_seconds() > 3600:  # 1 hour
                    messages_to_remove.append(message)
            
            for message in messages_to_remove:
                self.message_history.remove(message)
            
            if channels_to_remove or messages_to_remove:
                self.logger.info(f"Cleaned up {len(channels_to_remove)} channels and {len(messages_to_remove)} messages")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup communication resources: {e}")
    
    async def _monitor_loop(self) -> None:
        """Monitor communication system health and performance."""
        try:
            while True:
                # Log communication stats
                stats = self.get_communication_stats()
                
                if self.audit_logging:
                    self.logger.info(f"Communication stats: {stats}")
                
                # Sleep between monitoring cycles
                await asyncio.sleep(60.0)  # Monitor every minute
                
        except asyncio.CancelledError:
            self.logger.info("Communication monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in communication monitoring loop: {e}")


__all__ = [
    "ExtensionCommunicationManager",
    "ExtensionMessage",
    "MessageType",
    "MessagePriority",
    "ExtensionService",
    "CommunicationChannel",
]