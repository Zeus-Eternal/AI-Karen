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
                input_data.prompt, input_data.personal_facts or []
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
            "about the book ", "book called ", "book titled ",
            "read about ", "information on ", "details about "
        ]
        
        for pattern in patterns:
            if pattern in prompt_lower:
                start_idx = prompt_lower.find(pattern) + len(pattern)
                remaining = prompt[start_idx:].strip()
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
                words = remaining.split()
                if words:
                    email_info["recipient"] = words[0]
                break
        
        # Look for subject patterns
        subject_patterns = ["subject ", "about ", "regarding "]
        for pattern in subject_patterns:
            if pattern in prompt_lower:
                start_idx = prompt_lower.find(pattern) + len(pattern)
                remaining = prompt[start_idx:].strip()
                subject_words = remaining.split()[:8]  # Limit subject length
                if subject_words:
                    email_info["subject"] = " ".join(subject_words).rstrip(".,!?")
                break
        
        return email_info if email_info else None
    
    async def _identify_new_facts_enhanced(
        self, 
        prompt: str, 
        existing_facts: List[str]
    ) -> Optional[List[str]]:
        """Identifies new, specific, and potentially recurring personal information."""
        new_facts = []
        prompt_lower = prompt.lower()
        
        # Define patterns for fact extraction
        fact_patterns = {
            "name": ("my name is ", "User's name is "),
            "preference": ("i like ", "User likes "),
            "location": ("i live in ", "User lives in "),
            "work": ("i work at ", "User works at ")
        }
        
        for fact_type, (pattern, prefix) in fact_patterns.items():
            if pattern in prompt_lower:
                fact_start = prompt_lower.find(pattern) + len(pattern)
                fact_part = prompt[fact_start:].strip().split('.')[0] # Take text until the end of the sentence
                if fact_part and not any(fact_part.lower() in fact.lower() for fact in existing_facts):
                    new_facts.append(f"{prefix}{fact_part}")
        
        return new_facts if new_facts else None
    
    async def _generate_proactive_suggestion_enhanced(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        intent_analysis: Dict[str, Any],
        tool_to_call: ToolType
    ) -> Optional[str]:
        """Provides forward-thinking suggestions based on context and user needs."""
        # Don't suggest if a tool is already being used or for simple recall
        if tool_to_call != ToolType.NONE or any(phrase in prompt.lower() for phrase in ["what's my", "my name"]):
            return None
        
        intent = intent_analysis["primary_intent"]
        if intent == "weather_query":
            return "Would you like me to set up weather alerts for this location?"
        elif intent == "time_query":
            return "I can also set reminders or alarms if you need them."
        elif intent == "book_query":
            return "I can help you find similar books or authors if you're interested."
        elif intent == "conversation":
            if any(word in prompt.lower() for word in ["bored", "dunno"]):
                return "I can suggest some interesting topics, help you learn something new, or assist with tasks."
        
        return None
