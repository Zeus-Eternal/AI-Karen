"""
AI Orchestrator Service for AI Karen Engine.

This service coordinates AI processing, decision-making, and workflow orchestration.
It converts TypeScript AI flows to Python services while maintaining compatibility
with the existing AI Karen architecture.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.models.shared_types import (
    FlowType, FlowInput, FlowOutput, DecideActionInput, DecideActionOutput,
    ToolType, ToolInput, MemoryDepth, PersonalityTone, PersonalityVerbosity,
    AiData, MemoryContext, PluginInfo
)
from ai_karen_engine.integrations.llm_router import LLMProfileRouter
from ai_karen_engine.integrations.llm_utils import LLMUtils


class FlowRegistrationError(Exception):
    """Raised when flow registration fails."""
    pass


class FlowExecutionError(Exception):
    """Raised when flow execution fails."""
    pass


class FlowManager:
    """
    Manages AI processing workflows similar to Genkit flows.
    Handles flow registration, discovery, and execution.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.flow_manager")
        self._flows: Dict[FlowType, Callable] = {}
        self._flow_metadata: Dict[FlowType, Dict[str, Any]] = {}
        self._execution_stats: Dict[FlowType, Dict[str, Any]] = {}
        
        # Initialize execution stats for all flow types
        for flow_type in FlowType:
            self._execution_stats[flow_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_duration": 0.0,
                "last_execution": None
            }
    
    def register_flow(
        self, 
        flow_type: FlowType, 
        handler: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a flow handler with optional metadata."""
        try:
            if flow_type in self._flows:
                self.logger.warning(f"Overriding existing flow handler for {flow_type}")
            
            self._flows[flow_type] = handler
            self._flow_metadata[flow_type] = metadata or {}
            
            self.logger.info(f"Registered flow handler for {flow_type}")
            
        except Exception as e:
            raise FlowRegistrationError(f"Failed to register flow {flow_type}: {e}")
    
    def get_available_flows(self) -> List[FlowType]:
        """Get list of available flow types."""
        return list(self._flows.keys())
    
    def get_flow_metadata(self, flow_type: FlowType) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific flow type."""
        return self._flow_metadata.get(flow_type)
    
    def get_flow_stats(self, flow_type: FlowType) -> Optional[Dict[str, Any]]:
        """Get execution statistics for a specific flow type."""
        return self._execution_stats.get(flow_type)
    
    async def execute_flow(self, flow_type: FlowType, input_data: FlowInput) -> FlowOutput:
        """Execute a registered flow with the given input."""
        if flow_type not in self._flows:
            raise FlowExecutionError(f"Flow {flow_type} is not registered")
        
        handler = self._flows[flow_type]
        stats = self._execution_stats[flow_type]
        
        start_time = datetime.now()
        stats["total_executions"] += 1
        
        try:
            self.logger.info(f"Executing flow {flow_type}")
            result = await handler(input_data)
            
            # Update success stats
            stats["successful_executions"] += 1
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update average duration
            if stats["average_duration"] == 0.0:
                stats["average_duration"] = duration
            else:
                stats["average_duration"] = (stats["average_duration"] + duration) / 2
            
            stats["last_execution"] = datetime.now()
            
            self.logger.info(f"Flow {flow_type} executed successfully in {duration:.2f}s")
            return result
            
        except Exception as e:
            stats["failed_executions"] += 1
            self.logger.error(f"Flow {flow_type} execution failed: {e}")
            raise FlowExecutionError(f"Flow {flow_type} execution failed: {e}")

# ---

class DecisionEngine:
    """
    Handles cognitive decision-making processes.
    Determines the optimal next step based on user input and context.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.decision_engine")
        self._decision_rules: List[Callable] = []
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default tool registry
        self._initialize_default_tools()
    
    def _initialize_default_tools(self) -> None:
        """Initialize the default tool registry."""
        default_tools = {
            ToolType.GET_CURRENT_DATE: {
                "name": "getCurrentDate",
                "description": "Gets the current date from the system",
                "requires_input": False,
                "input_schema": {}
            },
            ToolType.GET_CURRENT_TIME: {
                "name": "getCurrentTime", 
                "description": "Gets the current time, optionally for a specific location",
                "requires_input": False,
                "input_schema": {"location": {"type": "string", "optional": True}}
            },
            ToolType.GET_WEATHER: {
                "name": "getWeather",
                "description": "Fetches current weather information for a location",
                "requires_input": True,
                "input_schema": {"location": {"type": "string", "required": True}}
            },
            ToolType.QUERY_BOOK_DATABASE: {
                "name": "queryBookDatabase",
                "description": "Queries a database for book/item information",
                "requires_input": True,
                "input_schema": {"book_title": {"type": "string", "required": True}}
            },
            ToolType.CHECK_GMAIL_UNREAD: {
                "name": "checkGmailUnread",
                "description": "Checks for unread Gmail messages",
                "requires_input": False,
                "input_schema": {}
            },
            ToolType.COMPOSE_GMAIL: {
                "name": "composeGmail",
                "description": "Composes and sends a Gmail message",
                "requires_input": True,
                "input_schema": {
                    "gmail_recipient": {"type": "string", "optional": True},
                    "gmail_subject": {"type": "string", "optional": True},
                    "gmail_body": {"type": "string", "optional": True}
                }
            }
        }
        
        for tool_type, info in default_tools.items():
            self._tool_registry[tool_type.value] = info
    
    def register_decision_rule(self, rule: Callable) -> None:
        """Register a decision rule function."""
        self._decision_rules.append(rule)
        self.logger.info(f"Registered decision rule: {rule.__name__}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self._tool_registry.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        return self._tool_registry.get(tool_name)
    
    async def analyze_intent(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user intent from prompt and context.
        Returns intent analysis including confidence and suggested actions.
        """
        try:
            # Basic intent analysis - can be enhanced with ML models
            intent_analysis = {
                "primary_intent": "unknown",
                "confidence": 0.5,
                "entities": [],
                "suggested_tools": [],
                "requires_clarification": False
            }
            
            prompt_lower = prompt.lower()
            
            # Weather intent
            if any(word in prompt_lower for word in ["weather", "temperature", "rain", "sunny", "cloudy"]):
                intent_analysis["primary_intent"] = "weather_query"
                intent_analysis["confidence"] = 0.8
                intent_analysis["suggested_tools"] = [ToolType.GET_WEATHER.value]
                
                # Extract location if present
                location_indicators = ["in ", "at ", "for "]
                for indicator in location_indicators:
                    if indicator in prompt_lower:
                        location_start = prompt_lower.find(indicator) + len(indicator)
                        location_part = prompt[location_start:].split()[0:3]  # Take up to 3 words
                        if location_part:
                            intent_analysis["entities"].append({
                                "type": "location",
                                "value": " ".join(location_part).rstrip("?.,!")
                            })
            
            # Time intent
            elif any(word in prompt_lower for word in ["time", "clock", "hour", "minute"]):
                intent_analysis["primary_intent"] = "time_query"
                intent_analysis["confidence"] = 0.8
                intent_analysis["suggested_tools"] = [ToolType.GET_CURRENT_TIME.value]
            
            # Date intent
            elif any(word in prompt_lower for word in ["date", "today", "day", "calendar"]):
                intent_analysis["primary_intent"] = "date_query"
                intent_analysis["confidence"] = 0.8
                intent_analysis["suggested_tools"] = [ToolType.GET_CURRENT_DATE.value]
            
            # Email intent
            elif any(word in prompt_lower for word in ["email", "gmail", "mail", "send", "compose"]):
                if any(word in prompt_lower for word in ["send", "compose", "write"]):
                    intent_analysis["primary_intent"] = "email_compose"
                    intent_analysis["suggested_tools"] = [ToolType.COMPOSE_GMAIL.value]
                else:
                    intent_analysis["primary_intent"] = "email_check"
                    intent_analysis["suggested_tools"] = [ToolType.CHECK_GMAIL_UNREAD.value]
                intent_analysis["confidence"] = 0.7
            
            # Book/item query intent
            elif any(word in prompt_lower for word in ["book", "author", "novel", "story", "read"]):
                intent_analysis["primary_intent"] = "book_query"
                intent_analysis["confidence"] = 0.7
                intent_analysis["suggested_tools"] = [ToolType.QUERY_BOOK_DATABASE.value]
            
            # Conversational intent
            else:
                intent_analysis["primary_intent"] = "conversation"
                intent_analysis["confidence"] = 0.6
                intent_analysis["suggested_tools"] = []
            
            self.logger.debug(f"Intent analysis for '{prompt}': {intent_analysis}")
            return intent_analysis
            
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            return {
                "primary_intent": "unknown",
                "confidence": 0.1,
                "entities": [],
                "suggested_tools": [],
                "requires_clarification": True,
                "error": str(e)
            }
    
    async def decide_action(self, input_data: DecideActionInput) -> DecideActionOutput:
        """
        Main decision-making method that determines the next action.
        Equivalent to TypeScript decideAction logic with enhanced memory integration.
        """
        try:
            # Build comprehensive context
            context = {
                "short_term_memory": input_data.short_term_memory,
                "long_term_memory": input_data.long_term_memory,
                "keywords": input_data.keywords or [],
                "knowledge_graph_insights": input_data.knowledge_graph_insights,
                "personal_facts": input_data.personal_facts or [],
                "memory_depth": input_data.memory_depth or MemoryDepth.MEDIUM,
                "personality_tone": input_data.personality_tone or PersonalityTone.FRIENDLY,
                "personality_verbosity": input_data.personality_verbosity or PersonalityVerbosity.BALANCED,
                "custom_persona_instructions": input_data.custom_persona_instructions
            }
            
            # First, check if the query is asking for known information
            known_info_response = await self._check_for_known_information(input_data.prompt, context)
            if known_info_response:
                return DecideActionOutput(
                    intermediate_response=known_info_response,
                    tool_to_call=ToolType.NONE,
                    tool_input=None,
                    suggested_new_facts=None,
                    proactive_suggestion=None  # Don't suggest for simple recall
                )
            
            # Analyze user intent
            intent_analysis = await self.analyze_intent(input_data.prompt, context)
            
            # Determine if a tool is needed
            tool_to_call = ToolType.NONE
            tool_input = None
            intermediate_response = ""
            
            if intent_analysis["suggested_tools"]:
                tool_name = intent_analysis["suggested_tools"][0]
                
                # Map tool name to ToolType
                for tool_type in ToolType:
                    if tool_type.value == tool_name:
                        tool_to_call = tool_type
                        break
                
                # Prepare tool input based on entities and tool requirements
                if tool_to_call != ToolType.NONE:
                    tool_input = ToolInput()
                    
                    # Extract location for weather/time tools
                    if tool_to_call in [ToolType.GET_WEATHER, ToolType.GET_CURRENT_TIME]:
                        location_entities = [e for e in intent_analysis["entities"] if e["type"] == "location"]
                        if location_entities:
                            tool_input.location = location_entities[0]["value"]
                        elif tool_to_call == ToolType.GET_WEATHER:
                            # Weather requires location, ask for it
                            intermediate_response = await self._generate_contextual_response(
                                "I'd be happy to check the weather for you. Which location would you like me to check?",
                                context
                            )
                            tool_to_call = ToolType.NONE
                            tool_input = None
                    
                    # Extract book title for book queries
                    elif tool_to_call == ToolType.QUERY_BOOK_DATABASE:
                        book_entities = [e for e in intent_analysis["entities"] if e["type"] == "book_title"]
                        if book_entities:
                            tool_input.book_title = book_entities[0]["value"]
                        else:
                            # Try to extract book title from prompt
                            book_title = await self._extract_book_title(input_data.prompt)
                            if book_title:
                                tool_input.book_title = book_title
                            else:
                                intermediate_response = await self._generate_contextual_response(
                                    "I'd be happy to look up book information for you. Which book are you interested in?",
                                    context
                                )
                                tool_to_call = ToolType.NONE
                                tool_input = None
                    
                    # Extract email information for Gmail tools
                    elif tool_to_call == ToolType.COMPOSE_GMAIL:
                        email_info = await self._extract_email_info(input_data.prompt)
                        if email_info:
                            tool_input.gmail_recipient = email_info.get("recipient")
                            tool_input.gmail_subject = email_info.get("subject")
                            tool_input.gmail_body = email_info.get("body")
                    
                    # Set appropriate acknowledgment message
                    if tool_to_call != ToolType.NONE:
                        intermediate_response = await self._generate_tool_acknowledgment(
                            tool_to_call, tool_input, context
                        )
            
            # If no tool is needed, provide direct response
            if tool_to_call == ToolType.NONE and not intermediate_response:
                # Generate conversational response based on context and personality
                intermediate_response = await self._generate_conversational_response(
                    input_data.prompt, context, intent_analysis
                )
            
            # Identify new facts to suggest (enhanced logic)
            suggested_new_facts = await self._identify_new_facts_enhanced(
                input_data.prompt, input_data.personal_facts or [], context
            )
            
            # Generate proactive suggestion if appropriate (enhanced logic)
            proactive_suggestion = await self._generate_proactive_suggestion_enhanced(
                input_data.prompt, context, intent_analysis, tool_to_call
            )
            
            return DecideActionOutput(
                intermediate_response=intermediate_response,
                tool_to_call=tool_to_call,
                tool_input=tool_input,
                suggested_new_facts=suggested_new_facts,
                proactive_suggestion=proactive_suggestion
            )
            
        except Exception as e:
            self.logger.error(f"Decision making failed: {e}")
            return DecideActionOutput(
                intermediate_response="I'm having a little trouble understanding that. Could you try rephrasing?",
                tool_to_call=ToolType.NONE,
                tool_input=None,
                suggested_new_facts=None,
                proactive_suggestion=None
            )
    
    async def _generate_conversational_response(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate a conversational response when no tool is needed."""
        # This is a simplified implementation - in production, this would use LLM
        tone = context.get("personality_tone", PersonalityTone.FRIENDLY)
        
        # Basic response generation based on tone
        if intent_analysis["primary_intent"] == "conversation":
            if tone == PersonalityTone.FORMAL:
                response = "I understand your inquiry. How may I assist you further?"
            elif tone == PersonalityTone.HUMOROUS:
                response = "Well, that's an interesting way to put it! What can I help you with?"
            else:  # FRIENDLY or NEUTRAL
                response = "I'm here to help! What would you like to know or do?"
        else:
            response = "I'm not sure I understand exactly what you're looking for. Could you provide more details?"
        
        return response
    
    async def _identify_new_facts(self, prompt: str, existing_facts: List[str]) -> Optional[List[str]]:
        """Identify new personal facts from the prompt."""
        # Simple fact extraction - in production, this would use NLP
        new_facts = []
        
        prompt_lower = prompt.lower()
        
        # Look for "my name is" patterns
        if "my name is" in prompt_lower:
            name_start = prompt_lower.find("my name is") + len("my name is")
            name_part = prompt[name_start:].strip().split()[0]
            if name_part and not any(name_part.lower() in fact.lower() for fact in existing_facts):
                new_facts.append(f"User's name is {name_part}")
        
        # Look for "i like" patterns
        if "i like" in prompt_lower:
            like_start = prompt_lower.find("i like") + len("i like")
            like_part = prompt[like_start:].strip()
            if like_part and not any(like_part.lower() in fact.lower() for fact in existing_facts):
                new_facts.append(f"User likes {like_part}")
        
        return new_facts if new_facts else None
    
    async def _generate_proactive_suggestion(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        intent_analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Generate proactive suggestions based on context."""
        # Simple proactive suggestion logic
        if intent_analysis["primary_intent"] == "weather_query":
            return "Would you like me to set up weather alerts for this location?"
        elif intent_analysis["primary_intent"] == "time_query":
            return "I can also set reminders or alarms if you need them."
        elif intent_analysis["primary_intent"] == "book_query":
            return "I can help you find similar books or authors if you're interested."
        
        return None
    
    async def _check_for_known_information(self, prompt: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Check if the user is asking for information we already know.
        This implements the TypeScript logic for checking memory before asking.
        """
        prompt_lower = prompt.lower()
        personal_facts = context.get("personal_facts", [])
        short_term_memory = context.get("short_term_memory", "")
        
        # Check for name queries
        if any(phrase in prompt_lower for phrase in ["what's my name", "my name", "who am i"]):
            # Check personal facts first
            for fact in personal_facts:
                if "name is" in fact.lower():
                    name = fact.split("name is")[-1].strip()
                    return f"Your name is {name}!"
            
            # Check short-term memory
            if short_term_memory and "name is" in short_term_memory.lower():
                # Extract name from memory
                memory_lower = short_term_memory.lower()
                if "my name is" in memory_lower:
                    name_start = memory_lower.find("my name is") + len("my name is")
                    name_part = short_term_memory[name_start:].strip().split()[0]
                    if name_part:
                        return f"Your name is {name_part}!"
        
        # Check for preference queries
        if "what do i like" in prompt_lower or "my favorite" in prompt_lower:
            likes = [fact for fact in personal_facts if "likes" in fact.lower() or "favorite" in fact.lower()]
            if likes:
                return f"Based on what you've told me: {', '.join(likes)}"
        
        return None
    
    async def _generate_contextual_response(self, base_response: str, context: Dict[str, Any]) -> str:
        """Generate a response adapted to the user's personality and context."""
        tone = context.get("personality_tone", PersonalityTone.FRIENDLY)
        verbosity = context.get("personality_verbosity", PersonalityVerbosity.BALANCED)
        
        # Adapt tone
        if tone == PersonalityTone.FORMAL:
            if "I'd be happy to" in base_response:
                base_response = base_response.replace("I'd be happy to", "I would be pleased to")
        elif tone == PersonalityTone.HUMOROUS:
            if "Which location" in base_response:
                base_response = base_response.replace("Which location", "What magical place")
        
        # Adapt verbosity
        if verbosity == PersonalityVerbosity.CONCISE:
            # Make more concise
            base_response = base_response.replace("I'd be happy to check the weather for you. ", "")
            base_response = base_response.replace("I'd be happy to look up book information for you. ", "")
        elif verbosity == PersonalityVerbosity.DETAILED:
            # Add more detail
            if "weather" in base_response.lower():
                base_response += " I can provide current conditions, temperature, and forecast information."
            elif "book" in base_response.lower():
                base_response += " I can find details like author, publication date, summary, and reviews."
        
        return base_response
    
    async def _generate_tool_acknowledgment(
        self, 
        tool_to_call: ToolType, 
        tool_input: Optional[ToolInput], 
        context: Dict[str, Any]
    ) -> str:
        """Generate appropriate acknowledgment message for tool execution."""
        base_messages = {
            ToolType.GET_WEATHER: "Let me check the weather for {location}...",
            ToolType.GET_CURRENT_TIME: "Let me get the current time{location_part}...",
            ToolType.GET_CURRENT_DATE: "Let me get today's date for you...",
            ToolType.CHECK_GMAIL_UNREAD: "Let me check your unread emails...",
            ToolType.COMPOSE_GMAIL: "I'll help you compose an email...",
            ToolType.QUERY_BOOK_DATABASE: "Let me search for that book information..."
        }
        
        base_message = base_messages.get(tool_to_call, "Let me help you with that...")
        
        # Customize based on tool input
        if tool_to_call == ToolType.GET_WEATHER and tool_input and tool_input.location:
            base_message = base_message.format(location=tool_input.location)
        elif tool_to_call == ToolType.GET_CURRENT_TIME:
            if tool_input and tool_input.location:
                base_message = base_message.format(location_part=f" for {tool_input.location}")
            else:
                base_message = base_message.format(location_part="")
        
        return await self._generate_contextual_response(base_message, context)
    
    async def _extract_book_title(self, prompt: str) -> Optional[str]:
        """Extract book title from the prompt."""
        prompt_lower = prompt.lower()
        
        # Look for common book query patterns
        patterns = [
            "about the book ",
            "book called ",
            "book titled ",
            "read about ",
            "information on ",
            "details about "
        ]
        
        for pattern in patterns:
            if pattern in prompt_lower:
                start_idx = prompt_lower.find(pattern) + len(pattern)
                # Extract the next few words as potential book title
                remaining = prompt[start_idx:].strip()
                # Take words until punctuation or common stop words
                words = remaining.split()
                title_words = []
                for word in words:
                    clean_word = word.rstrip("?.,!;")
                    if clean_word.lower() in ["by", "written", "author", "please", "can", "you"]:
                        break
                    title_words.append(clean_word)
                    if len(title_words) >= 5:  # Limit title length
                        break
                
                if title_words:
                    return " ".join(title_words)
        
        return None
    
    async def _extract_email_info(self, prompt: str) -> Optional[Dict[str, str]]:
        """Extract email information from the prompt."""
        email_info = {}
        prompt_lower = prompt.lower()
        
        # Look for recipient patterns
        recipient_patterns = ["send email to ", "email ", "write to ", "compose to "]
        for pattern in recipient_patterns:
            if pattern in prompt_lower:
                start_idx = prompt_lower.find(pattern) + len(pattern)
                remaining = prompt[start_idx:].strip()
                # Extract email address or name
                words = remaining.split()
                if words and ("@" in words[0] or words[0].endswith(".com")):
                    email_info["recipient"] = words[0]
                elif words:
                    email_info["recipient"] = words[0]
                break
        
        # Look for subject patterns
        subject_patterns = ["subject ", "about ", "regarding "]
        for pattern in subject_patterns:
            if pattern in prompt_lower:
                start_idx = prompt_lower.find(pattern) + len(pattern)
                remaining = prompt[start_idx:].strip()
                # Extract subject line
                subject_words = remaining.split()[:8]  # Limit subject length
                if subject_words:
                    email_info["subject"] = " ".join(subject_words).rstrip(".,!?")
                break
        
        return email_info if email_info else None
    
    async def _identify_new_facts_enhanced(
        self, 
        prompt: str, 
        existing_facts: List[str], 
        context: Dict[str, Any]
    ) -> Optional[List[str]]:
        """
        Enhanced fact identification that matches TypeScript logic.
        Identifies new, specific, and potentially recurring personal information.
        """
        new_facts = []
        prompt_lower = prompt.lower()
        
        # Enhanced name extraction
        name_patterns = [
            ("my name is ", "User's name is "),
            ("i'm ", "User's name is "),
            ("i am ", "User's name is "),
            ("call me ", "User prefers to be called ")
        ]
        
        for pattern, prefix in name_patterns:
            if pattern in prompt_lower:
                name_start = prompt_lower.find(pattern) + len(pattern)
                name_part = prompt[name_start:].strip().split()[0]
                if name_part and not any(name_part.lower() in fact.lower() for fact in existing_facts):
                    new_facts.append(f"{prefix}{name_part}")
        
        # Enhanced preference extraction
        preference_patterns = [
            ("i like ", "User likes "),
            ("i love ", "User loves "),
            ("i enjoy ", "User enjoys "),
            ("i prefer ", "User prefers "),
            ("my favorite ", "User's favorite "),
            ("i hate ", "User dislikes "),
            ("i don't like ", "User doesn't like ")
        ]
        
        for pattern, prefix in preference_patterns:
            if pattern in prompt_lower:
                pref_start = prompt_lower.find(pattern) + len(pattern)
                pref_part = prompt[pref_start:].strip()
                # Take reasonable amount of text for preference
                pref_words = pref_part.split()[:10]
                if pref_words:
                    pref_text = " ".join(pref_words).rstrip(".,!?")
                    if not any(pref_text.lower() in fact.lower() for fact in existing_facts):
                        new_facts.append(f"{prefix}{pref_text}")
        
        # Enhanced personal information extraction
        personal_patterns = [
            ("i work at ", "User works at "),
            ("i work for ", "User works for "),
            ("my job is ", "User's job is "),
            ("i live in ", "User lives in "),
            ("i'm from ", "User is from "),
            ("i study ", "User studies "),
            ("i'm studying ", "User is studying "),
            ("i have a ", "User has a "),
            ("i own a ", "User owns a ")
        ]
        
        for pattern, prefix in personal_patterns:
            if pattern in prompt_lower:
                info_start = prompt_lower.find(pattern) + len(pattern)
                info_part = prompt[info_start:].strip()
                info_words = info_part.split()[:8]
                if info_words:
                    info_text = " ".join(info_words).rstrip(".,!?")
                    if not any(info_text.lower() in fact.lower() for fact in existing_facts):
                        new_facts.append(f"{prefix}{info_text}")
        
        return new_facts if new_facts else None
    
    async def _generate_proactive_suggestion_enhanced(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        intent_analysis: Dict[str, Any],
        tool_to_call: ToolType
    ) -> Optional[str]:
        """
        Enhanced proactive suggestion generation that matches TypeScript logic.
        Provides forward-thinking suggestions based on context and user needs.
        """
        # Don't provide suggestions for simple recall queries
        if any(phrase in prompt.lower() for phrase in ["what's my", "my name", "who am i"]):
            return None
        
        # Context-aware suggestions based on intent
        if intent_analysis["primary_intent"] == "weather_query":
            personal_facts = context.get("personal_facts", [])
            if any("travel" in fact.lower() or "trip" in fact.lower() for fact in personal_facts):
                return "Since you travel, would you like me to set up weather alerts for multiple locations?"
            else:
                return "Would you like me to set up weather alerts for this location?"
        
        elif intent_analysis["primary_intent"] == "time_query":
            if tool_to_call != ToolType.NONE:  # Only suggest if we're actually getting time
                return "I can also set reminders or alarms if you need them."
        
        elif intent_analysis["primary_intent"] == "book_query":
            return "I can help you find similar books or authors if you're interested."
        
        elif intent_analysis["primary_intent"] == "email_compose":
            return "I can also help you schedule emails or set up email templates for future use."
        
        elif intent_analysis["primary_intent"] == "conversation":
            # Provide contextual suggestions based on conversation themes
            themes = context.get("conversation_themes", [])
            if "technology" in themes:
                return "I can help you with various tech-related tasks like coding, troubleshooting, or explaining concepts."
            elif "work" in themes:
                return "I can assist with work-related tasks like scheduling, email management, or project planning."
        
        # Suggest based on user's stated interests
        personal_facts = context.get("personal_facts", [])
        if personal_facts:
            for fact in personal_facts:
                if "coding" in fact.lower() or "programming" in fact.lower():
                    if "help" in prompt.lower():
                        return "Given your interest in programming, I can help with code reviews, debugging, or explaining algorithms."
                elif "reading" in fact.lower() or "books" in fact.lower():
                    if intent_analysis["primary_intent"] == "conversation":
                        return "Since you enjoy reading, I can recommend books or discuss literature topics."
        
        return None

# ---

class ContextManager:
    """
    Manages conversation context and memory integration.
    Builds context from various sources including memory, conversation history, and user preferences.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.context_manager")
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def build_context(
        self, 
        user_id: Optional[str],
        session_id: Optional[str],
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        user_settings: Dict[str, Any],
        memories: Optional[List[MemoryContext]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for AI processing.
        """
        try:
            context = {
                "user_id": user_id,
                "session_id": session_id,
                "current_prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "conversation_history": conversation_history,
                "user_settings": user_settings,
                "memories": memories or [],
                "context_summary": "",
                "relevant_facts": [],
                "conversation_themes": []
            }
            
            # Extract relevant facts from memories
            if memories:
                context["relevant_facts"] = [
                    {
                        "content": mem.content,
                        "relevance": mem.similarity_score or 0.0,
                        "tags": mem.tags or []
                    }
                    for mem in memories
                ]
            
            # Analyze conversation themes
            if conversation_history:
                themes = await self._extract_conversation_themes(conversation_history)
                context["conversation_themes"] = themes
            
            # Generate context summary
            context["context_summary"] = await self._generate_context_summary(context)
            
            # Cache context for reuse
            if user_id and session_id:
                cache_key = f"{user_id}:{session_id}"
                self._context_cache[cache_key] = {
                    "context": context,
                    "timestamp": datetime.now()
                }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Context building failed: {e}")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "current_prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _extract_conversation_themes(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract themes from conversation history."""
        # Simple theme extraction - in production, this would use NLP
        themes = []
        
        all_content = " ".join([
            msg.get("content", "") for msg in conversation_history
            if isinstance(msg.get("content"), str)
        ]).lower()
        
        # Common theme keywords
        theme_keywords = {
            "weather": ["weather", "temperature", "rain", "sunny", "cloudy"],
            "time": ["time", "clock", "hour", "minute", "schedule"],
            "technology": ["computer", "software", "app", "tech", "digital"],
            "personal": ["family", "friend", "personal", "life", "home"],
            "work": ["work", "job", "career", "office", "business"],
            "entertainment": ["movie", "music", "game", "book", "show"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    async def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a summary of the current context."""
        summary_parts = []
        
        if context.get("conversation_themes"):
            themes_str = ", ".join(context["conversation_themes"])
            summary_parts.append(f"Conversation themes: {themes_str}")
        
        if context.get("relevant_facts"):
            fact_count = len(context["relevant_facts"])
            summary_parts.append(f"{fact_count} relevant memories available")
        
        if context.get("user_settings"):
            settings = context["user_settings"]
            if settings.get("personality_tone"):
                summary_parts.append(f"Tone: {settings['personality_tone']}")
            if settings.get("memory_depth"):
                summary_parts.append(f"Memory depth: {settings['memory_depth']}")
        
        return "; ".join(summary_parts) if summary_parts else "Basic context available"
    
    def get_cached_context(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached context if available and not expired."""
        cache_key = f"{user_id}:{session_id}"
        cached = self._context_cache.get(cache_key)
        
        if cached:
            age = (datetime.now() - cached["timestamp"]).total_seconds()
            if age < self._cache_ttl:
                return cached["context"]
            else:
                # Remove expired cache
                del self._context_cache[cache_key]
        
        return None
    
    def clear_context_cache(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """Clear context cache for specific user/session or all."""
        if user_id and session_id:
            cache_key = f"{user_id}:{session_id}"
            self._context_cache.pop(cache_key, None)
        elif user_id:
            # Clear all sessions for user
            keys_to_remove = [k for k in self._context_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._context_cache[key]
        else:
            # Clear all cache
            self._context_cache.clear()

# ---

class PromptManager:
    """
    Handles structured prompt templates and generation.
    Similar to Genkit's prompt management approach.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.prompt_manager")
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._default_templates = self._load_default_templates()
        
        # Register default templates
        for name, template in self._default_templates.items():
            self.register_template(name, template)
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load default prompt templates."""
        return {
            "decide_action": {
                "system_prompt": """You are Karen, an intelligent AI assistant. Your primary directive is to be exceptionally helpful, deeply understanding, and demonstrate "human forward thinking" by anticipating user needs, making insightful connections, and offering relevant guidance.

**Available Tools:**
- getCurrentDate: Gets the current date from the system
- getCurrentTime: Gets the current time, optionally for a specific location
- getWeather: Fetches current weather information for a specified location
- queryBookDatabase: Queries database for book/item information
- checkGmailUnread: Checks for unread Gmail messages
- composeGmail: Composes and sends a Gmail message

**Decision Process:**
1. Analyze the user's prompt considering all available context
2. Determine if the query can be answered directly or requires a tool
3. If a tool is needed, identify the appropriate tool and parameters
4. Provide an appropriate response or acknowledgment
5. Identify any new personal facts to remember
6. Consider proactive suggestions based on the interaction""",
                
                "user_template": """**User's Current Query:** "{prompt}"

**Context:**
{context_info}

**Instructions:**
Analyze the query and determine the best response. If a tool is needed, specify which tool and any required parameters. Always provide a helpful response.""",
                
                "variables": ["prompt", "context_info"]
            },
            
            "conversation_processing": {
                "system_prompt": """You are Karen, an advanced AI assistant with access to comprehensive backend services including memory management, plugin execution, and analytics. You have evolved beyond simple chat responses to become a truly intelligent assistant with persistent memory and extensible capabilities.

**Core Identity & Capabilities:**
You are not just a conversational AI - you are an intelligent system with:
- Persistent memory across conversations
- Access to specialized plugins for various tasks
- Deep understanding of user context and preferences
- Ability to learn and adapt over time
- Proactive assistance capabilities

**Processing Instructions:**
1. Context Integration: Use all available context to provide personalized, contextually aware responses
2. Memory-Enhanced Responses: Reference relevant memories naturally and build upon previous conversations
3. Plugin Assessment: Determine if the user's request requires plugin execution
4. Memory Storage: Identify important information to remember for future conversations
5. Proactive Assistance: Anticipate user needs and suggest relevant actions
6. Response Adaptation: Match the user's preferred communication style""",
                
                "user_template": """**User Query:** "{prompt}"

**Available Context:**
{context_info}

**Available Plugins:**
{plugin_info}

**Relevant Memories:**
{memory_info}

**User Preferences:**
{user_preferences}

**Instructions:**
Provide a comprehensive response that demonstrates your enhanced capabilities. Consider plugin execution, memory storage, and proactive suggestions.""",
                
                "variables": ["prompt", "context_info", "plugin_info", "memory_info", "user_preferences"]
            }
        }
    
    def register_template(self, name: str, template: Dict[str, Any]) -> None:
        """Register a prompt template."""
        try:
            required_fields = ["system_prompt", "user_template", "variables"]
            for field in required_fields:
                if field not in template:
                    raise ValueError(f"Template missing required field: {field}")
            
            self._templates[name] = template
            self.logger.info(f"Registered prompt template: {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register template {name}: {e}")
            raise
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered template."""
        return self._templates.get(name)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self._templates.keys())

# ---

class AIOrchestrator(BaseService):
    """
    Central AI Orchestrator Service that coordinates AI processing, decision-making, and workflow orchestration.
    Converts TypeScript AI flows to Python services while maintaining compatibility.
    """
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        
        # Initialize components
        self.flow_manager = FlowManager()
        self.decision_engine = DecisionEngine()
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()
        self.llm_utils = LLMUtils()
        self.llm_router = LLMProfileRouter()
        
        # Service state
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the AI Orchestrator service."""
        try:
            self.logger.info("Initializing AI Orchestrator Service")
            
            # Register default flows
            await self._register_default_flows()
            
            self._initialized = True
            self.logger.info("AI Orchestrator Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Orchestrator: {e}")
            raise
    
    async def start(self) -> None:
        """Start the AI Orchestrator service."""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        self.logger.info("AI Orchestrator Service started")
    
    async def stop(self) -> None:
        """Stop the AI Orchestrator service."""
        self.logger.info("Stopping AI Orchestrator Service")
        
        # Clear caches
        self.context_manager.clear_context_cache()
        
        self.logger.info("AI Orchestrator Service stopped")
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Check if components are responsive
            available_flows = self.flow_manager.get_available_flows()
            available_tools = self.decision_engine.get_available_tools()
            available_templates = self.prompt_manager.get_available_templates()
            
            # Basic health indicators
            return (
                len(available_flows) > 0 and
                len(available_tools) > 0 and
                len(available_templates) > 0 and
                self._initialized
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def _register_default_flows(self) -> None:
        """Register default flow handlers."""
        # Register decide action flow
        self.flow_manager.register_flow(
            FlowType.DECIDE_ACTION,
            self._handle_decide_action_flow,
            {"description": "Decision-making flow for determining next actions"}
        )
        
        # Register conversation processing flow
        self.flow_manager.register_flow(
            FlowType.CONVERSATION_PROCESSING,
            self._handle_conversation_processing_flow,
            {"description": "Comprehensive conversation processing with memory integration"}
        )
        
        self.logger.info("Default flows registered")
    
    async def _handle_decide_action_flow(self, input_data: FlowInput) -> FlowOutput:
        """Handle decide action flow processing."""
        try:
            # Convert FlowInput to DecideActionInput
            decide_input = DecideActionInput(
                prompt=input_data.prompt,
                short_term_memory=input_data.short_term_memory,
                long_term_memory=input_data.long_term_memory,
                keywords=input_data.keywords,
                knowledge_graph_insights=input_data.knowledge_graph_insights,
                memory_depth=input_data.memory_depth,
                personality_tone=input_data.personality_tone,
                personality_verbosity=input_data.personality_verbosity,
                personal_facts=input_data.personal_facts,
                custom_persona_instructions=input_data.custom_persona_instructions
            )
            
            # Process through decision engine
            result = await self.decision_engine.decide_action(decide_input)
            
            # Convert DecideActionOutput to FlowOutput
            return FlowOutput(
                response=result.intermediate_response,
                requires_plugin=result.tool_to_call != ToolType.NONE,
                tool_to_call=result.tool_to_call,
                tool_input=result.tool_input,
                suggested_new_facts=result.suggested_new_facts,
                proactive_suggestion=result.proactive_suggestion
            )
            
        except Exception as e:
            self.logger.error(f"Decide action flow failed: {e}")
            raise FlowExecutionError(f"Decide action flow failed: {e}")
    
    async def _handle_conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """
        Handle conversation processing flow.
        Enhanced version that matches TypeScript karen-enhanced-flow logic.
        """
        try:
            # Build comprehensive context
            context = await self.context_manager.build_context(
                user_id=input_data.user_id,
                session_id=input_data.session_id,
                prompt=input_data.prompt,
                conversation_history=input_data.conversation_history,
                user_settings=input_data.user_settings,
                memories=input_data.context_from_memory
            )
            
            # Enhanced conversation processing with memory integration
            response = await self._process_conversation_with_memory(input_data, context)
            
            # Determine if plugin execution is needed
            requires_plugin, plugin_to_execute, plugin_parameters = await self._assess_plugin_needs(
                input_data.prompt, context, input_data.available_plugins or []
            )
            
            # Identify memory to store
            memory_to_store = await self._identify_memory_to_store(input_data, context)
            
            # Generate proactive suggestions based on enhanced context
            proactive_suggestion = await self._generate_conversation_proactive_suggestion(
                input_data, context
            )
            
            # Generate AI metadata with reasoning
            ai_data = await self._generate_conversation_ai_data(input_data, context, response)
            
            return FlowOutput(
                response=response,
                requires_plugin=requires_plugin,
                plugin_to_execute=plugin_to_execute,
                plugin_parameters=plugin_parameters,
                memory_to_store=memory_to_store,
                proactive_suggestion=proactive_suggestion,
                ai_data=ai_data
            )
            
        except Exception as e:
            self.logger.error(f"Conversation processing flow failed: {e}")
            # Fallback response
            return FlowOutput(
                response="I'm experiencing some technical difficulties with my enhanced capabilities right now. Let me try to help you with a basic response.",
                requires_plugin=False,
                ai_data=AiData(
                    confidence=0.3,
                    reasoning="Fallback response due to processing issues"
                )
            )
    
    async def _process_conversation_with_memory(self, input_data: FlowInput, context: Dict[str, Any]) -> str:
        """Process conversation using LLM with memory/context awareness."""
        try:
            template = self.prompt_manager.get_template("conversation_processing")
            if not template:
                raise ValueError("conversation_processing template missing")

            context_info = context.get("context_summary", "")
            plugin_info = ", ".join(p.name for p in input_data.available_plugins or [])
            memory_info = "; ".join(m.get("content", "") for m in context.get("memories", [])[:3])
            user_preferences = ", ".join(f"{k}={v}" for k, v in input_data.user_settings.items())

            user_prompt = template["user_template"].format(
                prompt=input_data.prompt,
                context_info=context_info,
                plugin_info=plugin_info,
                memory_info=memory_info,
                user_preferences=user_preferences,
            )
            full_prompt = f"{template['system_prompt']}\n\n{user_prompt}"

            raw = self.llm_router.invoke(self.llm_utils, full_prompt, task_intent="chat")
            if not isinstance(raw, str):
                raise TypeError("LLM response must be text")
            response = raw.strip()
            if not response:
                raise ValueError("empty response")
            if len(response) > 4000:
                response = response[:4000]
            return response
        except Exception as ex:
            self.logger.error(f"LLM processing failed: {ex}")
            return await self._fallback_conversation_response(input_data, context)

    async def _fallback_conversation_response(self, input_data: FlowInput, context: Dict[str, Any]) -> str:
        """Fallback rule-based conversation processing used if LLM fails."""
        prompt = input_data.prompt
        memories = context.get("memories", [])
        conversation_history = context.get("conversation_history", [])
        user_settings = context.get("user_settings", {})

        response_parts: List[str] = []

        if memories:
            relevant_memories = [m for m in memories if m.get("relevance", 0) > 0.7]
            if relevant_memories and "remember" not in prompt.lower():
                response_parts.append(f"I recall that {relevant_memories[0]['content'].lower()}.")

        if conversation_history:
            themes = context.get("conversation_themes", [])
            if themes and len(conversation_history) > 2:
                response_parts.append(f"Continuing our discussion about {themes[0]},")

        if "help" in prompt.lower():
            response_parts.append("I'm here to assist you with various tasks.")
            capabilities: List[str] = []
            if input_data.available_plugins:
                plugin_categories = {
                    plugin.category for plugin in input_data.available_plugins if plugin.enabled
                }
                if plugin_categories:
                    capabilities.append(f"I have access to {', '.join(plugin_categories)} plugins")
            if memories:
                capabilities.append("I can remember our conversations")
            if capabilities:
                response_parts.append(f"With my enhanced capabilities, {' and '.join(capabilities)}.")

        elif any(k in prompt.lower() for k in ["remember", "my name", "i like", "i am"]):
            response_parts.append(f"I've noted that information: '{prompt}'.")
            response_parts.append("I'll remember this for our future conversations.")

        elif any(k in prompt.lower() for k in ["thank", "thanks"]):
            tone = user_settings.get("personality_tone", "friendly")
            if tone == "formal":
                response_parts.append("You are most welcome. It was my pleasure to assist you.")
            else:
                response_parts.append("You're welcome! I'm glad I could help.")
        else:
            response_parts.append(f"I understand you're saying: '{prompt}'.")
            if memories:
                response_parts.append(
                    "Based on our previous conversations, I can provide more personalized assistance."
                )

        if response_parts:
            return " ".join(response_parts)
        return f"I hear you saying '{prompt}'. How can I help you further?"
    
    async def _assess_plugin_needs(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        available_plugins: List[PluginInfo]
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Assess if the user's request requires plugin execution.
        Returns (requires_plugin, plugin_name, parameters).
        """
        prompt_lower = prompt.lower()
        
        # Check for plugin-specific requests
        for plugin in available_plugins:
            if not plugin.enabled:
                continue
                
            plugin_name_lower = plugin.name.lower()
            plugin_desc_lower = plugin.description.lower()
            
            # Simple keyword matching - in production this would be more sophisticated
            if (plugin_name_lower in prompt_lower or 
                any(keyword in prompt_lower for keyword in plugin_desc_lower.split()[:3])):
                
                # Extract parameters based on plugin type
                parameters = {}
                if "weather" in plugin_name_lower and "location" in prompt_lower:
                    # Extract location
                    location_indicators = ["in ", "at ", "for "]
                    for indicator in location_indicators:
                        if indicator in prompt_lower:
                            location_start = prompt_lower.find(indicator) + len(indicator)
                            location_part = prompt[location_start:].split()[0:3]
                            if location_part:
                                parameters["location"] = " ".join(location_part).rstrip("?.,!")
                                break
                
                return True, plugin.name, parameters
        
        return False, None, None
    
    async def _identify_memory_to_store(self, input_data: FlowInput, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Identify important information to store in memory.
        Enhanced logic that matches TypeScript implementation.
        """
        prompt = input_data.prompt
        prompt_lower = prompt.lower()
        
        # Store explicit memory requests
        if any(keyword in prompt_lower for keyword in ["remember", "don't forget", "keep in mind"]):
            return {
                "content": prompt,
                "tags": ["explicit_memory", "user_request"],
                "metadata": {
                    "context_summary": context.get("context_summary", ""),
                    "conversation_themes": context.get("conversation_themes", []),
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Store personal information
        if any(keyword in prompt_lower for keyword in ["my name", "i like", "i am", "i work", "i live"]):
            tags = ["personal_info"]
            
            # Add specific tags based on content
            if "name" in prompt_lower:
                tags.append("name")
            if any(word in prompt_lower for word in ["like", "love", "enjoy", "prefer"]):
                tags.append("preferences")
            if any(word in prompt_lower for word in ["work", "job", "career"]):
                tags.append("professional")
            
            return {
                "content": prompt,
                "tags": tags,
                "metadata": {
                    "context_summary": context.get("context_summary", ""),
                    "importance": "high",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Store significant interactions
        if len(prompt) > 50 and any(keyword in prompt_lower for keyword in ["help", "problem", "issue", "question"]):
            return {
                "content": prompt,
                "tags": ["interaction", "help_request"],
                "metadata": {
                    "context_summary": context.get("context_summary", ""),
                    "importance": "medium",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        return None
    
    async def _generate_conversation_proactive_suggestion(
        self, 
        input_data: FlowInput, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate proactive suggestions for conversation processing.
        Enhanced logic that anticipates user needs.
        """
        prompt = input_data.prompt
        prompt_lower = prompt.lower()
        memories = context.get("memories", [])
        themes = context.get("conversation_themes", [])
        
        # Don't suggest for simple acknowledgments
        if any(word in prompt_lower for word in ["thanks", "thank you", "ok", "okay", "yes", "no"]):
            return None
        
        # Suggest based on conversation themes and history
        if "help" in prompt_lower:
            if input_data.available_plugins:
                plugin_categories = set(plugin.category for plugin in input_data.available_plugins if plugin.enabled)
                if plugin_categories:
                    return f"I can assist with {', '.join(plugin_categories)} tasks. What specific area interests you?"
            return "I can help with various tasks like information lookup, scheduling, or just having a conversation."
        
        # Suggest based on user's interests from memory
        if memories:
            interests = []
            for memory in memories:
                content = memory.get("content", "").lower()
                if "like" in content or "enjoy" in content:
                    # Extract what they like
                    if "like" in content:
                        like_start = content.find("like") + 4
                        interest = content[like_start:].strip().split()[0:3]
                        if interest:
                            interests.extend(interest)
            
            if interests and "conversation" in themes:
                return f"Since you're interested in {interests[0]}, I can share more information or help you explore related topics."
        
        # Suggest based on conversation flow
        if len(input_data.conversation_history) > 3:
            return "I notice we've been chatting for a while. Is there anything specific I can help you accomplish?"
        
        # Suggest memory-related features
        if any(keyword in prompt_lower for keyword in ["remember", "recall", "memory"]):
            return "I can help you keep track of important information across our conversations. Just let me know what you'd like me to remember!"
        
        return None
    
    async def _generate_conversation_ai_data(
        self, 
        input_data: FlowInput, 
        context: Dict[str, Any], 
        response: str
    ) -> AiData:
        """
        Generate AI metadata for the conversation processing.
        """
        prompt = input_data.prompt
        memories = context.get("memories", [])
        themes = context.get("conversation_themes", [])
        
        # Extract keywords from prompt
        keywords = []
        for word in prompt.lower().split():
            if len(word) > 3 and word not in ["the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how", "its", "may", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "man", "men", "put", "say", "she", "too", "use"]:
                keywords.append(word.rstrip(".,!?"))
        
        # Calculate confidence based on available context
        confidence = 0.5  # Base confidence
        
        if memories:
            confidence += 0.2  # Boost for memory context
        if themes:
            confidence += 0.1  # Boost for conversation themes
        if len(input_data.conversation_history) > 0:
            confidence += 0.1  # Boost for conversation history
        if input_data.user_settings:
            confidence += 0.1  # Boost for user settings
        
        confidence = min(confidence, 0.95)  # Cap at 95%
        
        # Generate reasoning
        reasoning_parts = ["Processed conversation with"]
        if memories:
            reasoning_parts.append(f"{len(memories)} relevant memories")
        if themes:
            reasoning_parts.append(f"themes: {', '.join(themes)}")
        if input_data.available_plugins:
            reasoning_parts.append(f"{len(input_data.available_plugins)} available plugins")
        
        reasoning = " ".join(reasoning_parts) + "."
        
        return AiData(
            keywords=keywords[:5],  # Limit to top 5 keywords
            confidence=confidence,
            reasoning=reasoning,
            knowledge_graph_insights=context.get("context_summary")
        )
    
    # Public API methods
    
    async def process_flow(self, flow_type: FlowType, input_data: FlowInput) -> FlowOutput:
        """Process an AI flow with the given input."""
        return await self.flow_manager.execute_flow(flow_type, input_data)
    
    async def decide_action(self, input_data: FlowInput) -> FlowOutput:
        """Execute the decide action flow."""
        return await self.process_flow(FlowType.DECIDE_ACTION, input_data)
    
    async def conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Execute the conversation processing flow."""
        return await self.process_flow(FlowType.CONVERSATION_PROCESSING, input_data)
    
    def get_available_flows(self) -> List[FlowType]:
        """Get list of available flow types."""
        return self.flow_manager.get_available_flows()
    
    def get_flow_stats(self, flow_type: FlowType) -> Optional[Dict[str, Any]]:
        """Get execution statistics for a flow type."""
        return self.flow_manager.get_flow_stats(flow_type)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.decision_engine.get_available_tools()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        return self.decision_engine.get_tool_info(tool_name)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics including flow statistics."""
        base_metrics = super().get_metrics()
        
        # Add flow-specific metrics
        flow_metrics = {}
        for flow_type in FlowType:
            stats = self.flow_manager.get_flow_stats(flow_type)
            if stats:
                flow_metrics[flow_type.value] = stats
        
        base_metrics["flows"] = flow_metrics
        base_metrics["available_flows"] = len(self.flow_manager.get_available_flows())
        base_metrics["available_tools"] = len(self.decision_engine.get_available_tools())
        base_metrics["available_templates"] = len(self.prompt_manager.get_available_templates())
        
        return base_metrics