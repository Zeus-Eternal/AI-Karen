
class BaseFilterEngine(ABC):
    """Base class for filter engines."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the filter engine."""
        pass
    
    @abstractmethod
    async def process(self, content: ContentInput, context: Context) -> ValidationResult:
        """Process content through the filter."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check health of the filter engine."""
        pass


class InputFilterEngine(BaseFilterEngine):
    """Input Filter Engine for validating incoming content."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._blocked_patterns: List[str] = []
        self._allowed_content_types: Set[ContentType] = set()
        self._max_content_sizes: Dict[ContentType, int] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the input filter engine."""
        if self._initialized:
            return
            
        # Initialize with default blocked patterns
        self._blocked_patterns = [
            r"(?i)\b(password|secret|token|key)\b.*=.*",  # Potential credential leakage
            r"(?i)\b(delete|drop|remove)\b.*\b(table|database|file)\b",  # Destructive actions
            r"(?i)\b(exec|eval|system)\b.*\(",  # Code execution
        ]
        
        # Initialize allowed content types
        self._allowed_content_types = {ContentType.TEXT, ContentType.STRUCTURED}
        
        # Initialize max content sizes (in bytes)
        self._max_content_sizes = {
            ContentType.TEXT: 1024 * 1024,  # 1MB
            ContentType.IMAGE: 10 * 1024 * 1024,  # 10MB
            ContentType.AUDIO: 50 * 1024 * 1024,  # 50MB
            ContentType.STRUCTURED: 5 * 1024 * 1024,  # 5MB
        }
        
        # Load custom configurations
        if "blocked_patterns" in self.config:
            self._blocked_patterns.extend(self.config["blocked_patterns"])
        
        if "allowed_content_types" in self.config:
            for ct in self.config["allowed_content_types"]:
                self._allowed_content_types.add(ContentType(ct))
        
        if "max_content_sizes" in self.config:
            for ct, size in self.config["max_content_sizes"].items():
                self._max_content_sizes[ContentType(ct)] = size
        
        self._initialized = True
        logger.info("Input filter engine initialized successfully")
    
    async def process(self, content: ContentInput, context: Context) -> ValidationResult:
        """Process content through the input filter."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            # Check content type
            if content.content_type not in self._allowed_content_types:
                return ValidationResult(
                    is_safe=False,
                    confidence=1.0,
                    risk_level=RiskLevel.HIGH_RISK,
                    violations=[f"Content type {content.content_type} is not allowed"],
                    metadata={"content_type": content.content_type}
                )
            
            # Check content size
            content_size = self._get_content_size(content)
            max_size = self._max_content_sizes.get(content.content_type, 0)
            if content_size > max_size:
                return ValidationResult(
                    is_safe=False,
                    confidence=1.0,
                    risk_level=RiskLevel.MEDIUM_RISK,
                    violations=[f"Content size {content_size} exceeds maximum allowed size {max_size}"],
                    metadata={"content_size": content_size, "max_size": max_size}
                )
            
            # Check against blocked patterns (for text content)
            if content.content_type == ContentType.TEXT and isinstance(content.content, str):
                for pattern in self._blocked_patterns:
                    if re.search(pattern, content.content):
                        return ValidationResult(
                            is_safe=False,
                            confidence=0.9,
                            risk_level=RiskLevel.HIGH_RISK,
                            violations=[f"Content matches blocked pattern: {pattern}"],
                            matched_patterns=[pattern],
                            metadata={"pattern": pattern}
                        )
            
            # All checks passed
            return ValidationResult(is_safe=True, confidence=1.0, risk_level=RiskLevel.SAFE)
    
    def _get_content_size(self, content: ContentInput) -> int:
        """Get the size of the content in bytes."""
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            return len(content.content.encode('utf-8'))
        elif content.content_type == ContentType.STRUCTURED:
            return len(json.dumps(content.content).encode('utf-8'))
        # For other content types, we would need specific implementations
        return 0
    
    async def health_check(self) -> bool:
        """Check health of the input filter engine."""
        return self._initialized
    
    async def add_blocked_pattern(self, pattern: str) -> bool:
        """Add a pattern to the blocked list."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            try:
                # Validate the pattern by compiling it
                re.compile(pattern)
                
                if pattern not in self._blocked_patterns:
                    self._blocked_patterns.append(pattern)
                    logger.info(f"Added blocked pattern: {pattern}")
                    return True
                return False
            except re.error as e:
                logger.error(f"Invalid regex pattern {pattern}: {e}")
                return False
    
    async def remove_blocked_pattern(self, pattern: str) -> bool:
        """Remove a pattern from the blocked list."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if pattern in self._blocked_patterns:
                self._blocked_patterns.remove(pattern)
                logger.info(f"Removed blocked pattern: {pattern}")
                return True
            return False


class ContentScanEngine(BaseFilterEngine):
    """Content Scan Engine for deep analysis of content."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._scanners: Dict[str, Any] = {}
        self._ml_models: Dict[str, Any] = {}
        self._risk_thresholds: Dict[RiskLevel, float] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the content scan engine."""
        if self._initialized:
            return
            
        # Initialize risk thresholds
        self._risk_thresholds = {
            RiskLevel.SAFE: 0.1,
            RiskLevel.LOW_RISK: 0.3,
            RiskLevel.MEDIUM_RISK: 0.6,
            RiskLevel.HIGH_RISK: 0.8,
            RiskLevel.CRITICAL_RISK: 0.95
        }
        
        # Initialize scanners
        self._scanners = {
            "keyword": self._keyword_scanner,
            "semantic": self._semantic_scanner,
            "pattern": self._pattern_scanner
        }
        
        # Load custom configurations
        if "risk_thresholds" in self.config:
            for level, threshold in self.config["risk_thresholds"].items():
                self._risk_thresholds[RiskLevel(level)] = threshold
        
        if "scanners" in self.config:
            self._scanners.update(self.config["scanners"])
        
        # Initialize ML models if enabled
        if self.config.get("enable_ml_models", True):
            await self._initialize_ml_models()
        
        self._initialized = True
        logger.info("Content scan engine initialized successfully")
    
    async def process(self, content: ContentInput, context: Context) -> ValidationResult:
        """Process content through the content scanner."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            violations = []
            matched_patterns = []
            risk_score = 0.0
            
            # Run all scanners
            for scanner_name, scanner_func in self._scanners.items():
                try:
                    result = await scanner_func(content, context)
                    if not result["is_safe"]:
                        violations.extend(result["violations"])
                        matched_patterns.extend(result.get("matched_patterns", []))
                        risk_score = max(risk_score, result.get("risk_score", 0.0))
                except Exception as e:
                    logger.error(f"Error in scanner {scanner_name}: {e}")
            
            # Run ML models if enabled
            if self._ml_models and self.config.get("enable_ml_models", True):
                ml_result = await self._run_ml_models(content, context)
                if not ml_result["is_safe"]:
                    violations.extend(ml_result["violations"])
                    risk_score = max(risk_score, ml_result.get("risk_score", 0.0))
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Determine if content is safe
            is_safe = risk_score < self._risk_thresholds[RiskLevel.MEDIUM_RISK]
            
            # Calculate confidence
            confidence = 1.0 - risk_score
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations,
                matched_patterns=matched_patterns,
                metadata={"risk_score": risk_score}
            )
    
    async def _keyword_scanner(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Scan content for unsafe keywords."""
        violations = []
        risk_score = 0.0
        
        # Define unsafe keywords by category
        unsafe_keywords = {
            "violence": ["kill", "harm", "attack", "violence", "weapon"],
            "hate": ["hate", "discrimination", "racism", "sexism"],
            "inappropriate": ["profanity", "obscene", "vulgar"],
            "security": ["hack", "exploit", "vulnerability", "breach"]
        }
        
        # Only scan text content
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            text = content.content.lower()
            
            for category, keywords in unsafe_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        violations.append(f"Content contains unsafe keyword: {keyword}")
                        risk_score += 0.2
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _semantic_scanner(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Scan content for unsafe semantic patterns."""
        violations = []
        risk_score = 0.0
        
        # Only scan text content
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            text = content.content.lower()
            
            # Define unsafe semantic patterns
            unsafe_patterns = [
                (r"how to.*(?:hack|crack|bypass)", "instruction for illegal activities"),
                (r"i want to.*(?:hurt|kill|harm)", "expression of harmful intent"),
                (r"i hate.*(?:group|people|race)", "hate speech"),
                (r"this is.*(?:stupid|dumb|worthless)", "harassment")
            ]
            
            for pattern, description in unsafe_patterns:
                if re.search(pattern, text):
                    violations.append(f"Content contains unsafe semantic pattern: {description}")
                    risk_score += 0.3
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _pattern_scanner(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Scan content for unsafe patterns."""
        violations = []
        matched_patterns = []
        risk_score = 0.0
        
        # Only scan text content
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            text = content.content
            
            # Define unsafe patterns
            unsafe_patterns = [
                (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "potential credit card number", 0.7),
                (r"\b\d{3}-\d{2}-\d{4}\b", "potential SSN", 0.8),
                (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email address", 0.4),
                (r"(?i)\b(?:password|pwd)\s*[:=]\s*\S+", "potential password", 0.9)
            ]
            
            for pattern, description, score in unsafe_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    violations.append(f"Content contains {description}")
                    matched_patterns.append(pattern)
                    risk_score += score
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "matched_patterns": matched_patterns,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _initialize_ml_models(self) -> None:
        """Initialize ML models for content analysis."""
        # This would typically load pre-trained models for content classification
        # For now, we'll use placeholder implementations
        self._ml_models = {
            "toxicity": self._toxicity_model,
            "sentiment": self._sentiment_model,
            "sensitivity": self._sensitivity_model
        }
        logger.info("ML models initialized")
    
    async def _run_ml_models(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Run ML models on content."""
        violations = []
        risk_score = 0.0
        
        # Only process text content
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            for model_name, model_func in self._ml_models.items():
                try:
                    result = await model_func(content, context)
                    if not result["is_safe"]:
                        violations.extend(result["violations"])
                        risk_score = max(risk_score, result.get("risk_score", 0.0))
                except Exception as e:
                    logger.error(f"Error in ML model {model_name}: {e}")
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _toxicity_model(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """ML model for toxicity detection."""
        # Placeholder implementation
        # In a real implementation, this would use a pre-trained toxicity model
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            toxic_words = ["toxic", "poison", "harmful", "dangerous"]
            text = content.content.lower()
            
            for word in toxic_words:
                if word in text:
                    violations.append(f"Content may be toxic (contains: {word})")
                    risk_score += 0.25
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _sentiment_model(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """ML model for sentiment analysis."""
        # Placeholder implementation
        # In a real implementation, this would use a pre-trained sentiment model
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            negative_words = ["hate", "angry", "sad", "bad", "terrible"]
            text = content.content.lower()
            
            negative_count = sum(1 for word in negative_words if word in text)
            if negative_count > 2:
                violations.append("Content has overly negative sentiment")
                risk_score += 0.3 * (negative_count / len(negative_words))
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _sensitivity_model(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """ML model for sensitivity detection."""
        # Placeholder implementation
        # In a real implementation, this would use a pre-trained sensitivity model
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            sensitive_topics = ["politics", "religion", "race", "gender"]
            text = content.content.lower()
            
            for topic in sensitive_topics:
                if topic in text:
                    violations.append(f"Content may be sensitive (topic: {topic})")
                    risk_score += 0.2
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on risk score."""
        for level, threshold in sorted(self._risk_thresholds.items(), key=lambda x: x[1], reverse=True):
            if risk_score >= threshold:
                return level
        return RiskLevel.SAFE
    
    async def health_check(self) -> bool:
        """Check health of the content scan engine."""
        return self._initialized


class ContextAnalysisEngine(BaseFilterEngine):
    """Context Analysis Engine for evaluating content in context."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._context_rules: Dict[str, Any] = {}
        self._whitelist: Dict[str, List[str]] = {}
        self._blacklist: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the context analysis engine."""
        if self._initialized:
            return
            
        # Initialize context rules
        self._context_rules = {
            "conversation_history": self._analyze_conversation_history,
            "user_relationship": self._analyze_user_relationship,
            "task_context": self._analyze_task_context,
            "session_context": self._analyze_session_context
        }
        
        # Initialize whitelist and blacklist
        self._whitelist = {
            "agents": [],
            "users": [],
            "sessions": []
        }
        
        self._blacklist = {
            "agents": [],
            "users": [],
            "sessions": [],
            "keywords": []
        }
        
        # Load custom configurations
        if "context_rules" in self.config:
            self._context_rules.update(self.config["context_rules"])
        
        if "whitelist" in self.config:
            self._whitelist.update(self.config["whitelist"])
        
        if "blacklist" in self.config:
            self._blacklist.update(self.config["blacklist"])
        
        self._initialized = True
        logger.info("Context analysis engine initialized successfully")
    
    async def process(self, content: ContentInput, context: Context) -> ValidationResult:
        """Process content through the context analyzer."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            violations = []
            risk_score = 0.0
            
            # Check blacklist
            blacklist_result = await self._check_blacklist(context)
            if not blacklist_result["is_safe"]:
                violations.extend(blacklist_result["violations"])
                risk_score = max(risk_score, blacklist_result.get("risk_score", 0.0))
            
            # Check whitelist
            whitelist_result = await self._check_whitelist(context)
            if whitelist_result["is_safe"]:
                # Content is whitelisted, reduce risk score
                risk_score *= 0.5
            
            # Run context rules
            for rule_name, rule_func in self._context_rules.items():
                try:
                    result = await rule_func(content, context)
                    if not result["is_safe"]:
                        violations.extend(result["violations"])
                        risk_score = max(risk_score, result.get("risk_score", 0.0))
                except Exception as e:
                    logger.error(f"Error in context rule {rule_name}: {e}")
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Determine if content is safe
            is_safe = risk_score < 0.6
            
            # Calculate confidence
            confidence = 1.0 - risk_score
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations,
                metadata={"risk_score": risk_score}
            )
    
    async def _check_blacklist(self, context: Context) -> Dict[str, Any]:
        """Check if context is blacklisted."""
        violations = []
        risk_score = 0.0
        
        # Check agent blacklist
        if context.agent_id in self._blacklist["agents"]:
            violations.append(f"Agent {context.agent_id} is blacklisted")
            risk_score += 0.9
        
        # Check user blacklist
        if context.user_id and context.user_id in self._blacklist["users"]:
            violations.append(f"User {context.user_id} is blacklisted")
            risk_score += 0.8
        
        # Check session blacklist
        if context.session_id and context.session_id in self._blacklist["sessions"]:
            violations.append(f"Session {context.session_id} is blacklisted")
            risk_score += 0.7
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _check_whitelist(self, context: Context) -> Dict[str, Any]:
        """Check if context is whitelisted."""
        # Check agent whitelist
        if context.agent_id in self._whitelist["agents"]:
            return {"is_safe": True}
        
        # Check user whitelist
        if context.user_id and context.user_id in self._whitelist["users"]:
            return {"is_safe": True}
        
        # Check session whitelist
        if context.session_id and context.session_id in self._whitelist["sessions"]:
            return {"is_safe": True}
        
        return {"is_safe": False}
    
    async def _analyze_conversation_history(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Analyze conversation history for context."""
        violations = []
        risk_score = 0.0
        
        if not context.conversation_history:
            return {"is_safe": True, "risk_score": 0.0}
        
        # Check for repeated violations
        recent_messages = context.conversation_history[-5:]  # Last 5 messages
        violation_count = sum(1 for msg in recent_messages if msg.get("had_violation", False))
        
        if violation_count >= 3:
            violations.append("Multiple recent violations in conversation")
            risk_score += 0.5 * (violation_count / 5)
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _analyze_user_relationship(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Analyze user relationship for context."""
        # Placeholder implementation
        # In a real implementation, this would analyze the relationship between users
        violations = []
        risk_score = 0.0
        
        # For now, we'll just check if the user and agent have interacted before
        if context.conversation_history and len(context.conversation_history) < 3:
            # New conversation, slightly higher risk
            risk_score += 0.1
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _analyze_task_context(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Analyze task context."""
        # Placeholder implementation
        # In a real implementation, this would analyze the task context
        violations = []
        risk_score = 0.0
        
        # For now, we'll just check if the task is potentially sensitive
        if context.task_id:
            # Sensitive tasks might include personal data, financial info, etc.
            sensitive_keywords = ["personal", "financial", "medical", "confidential"]
            task_str = str(context.task_id).lower()
            
            for keyword in sensitive_keywords:
                if keyword in task_str:
                    violations.append(f"Task context may be sensitive (contains: {keyword})")
                    risk_score += 0.3
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    async def _analyze_session_context(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Analyze session context."""
        # Placeholder implementation
        # In a real implementation, this would analyze the session context
        violations = []
        risk_score = 0.0
        
        # For now, we'll just check if the session is new
        if context.session_id and context.conversation_history:
            # Check if this is the first message in the session
            if len(context.conversation_history) == 1:
                # First message, slightly higher risk
                risk_score += 0.1
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(risk_score, 1.0)
        }
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on risk score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL_RISK
        elif risk_score >= 0.6:
            return RiskLevel.HIGH_RISK
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM_RISK
        elif risk_score >= 0.2:
            return RiskLevel.LOW_RISK
        else:
            return RiskLevel.SAFE
    
    async def health_check(self) -> bool:
        """Check health of the context analysis engine."""
        return self._initialized


class OutputFilterEngine(BaseFilterEngine):
    """Output Filter Engine for validating agent outputs."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._blocked_patterns: List[str] = []
        self._max_output_sizes: Dict[ContentType, int] = {}
        self._sanitization_rules: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the output filter engine."""
        if self._initialized:
            return
            
        # Initialize with default blocked patterns
        self._blocked_patterns = [
            r"(?i)\b(password|secret|token|key)\b.*=.*",  # Potential credential leakage
            r"(?i)\b(delete|drop|remove)\b.*\b(table|database|file)\b",  # Destructive actions
            r"(?i)\b(exec|eval|system)\b.*\(",  # Code execution
        ]
        
        # Initialize max output sizes (in bytes)
        self._max_output_sizes = {
            ContentType.TEXT: 10 * 1024 * 1024,  # 10MB
            ContentType.IMAGE: 20 * 1024 * 1024,  # 20MB
            ContentType.STRUCTURED: 10 * 1024 * 1024,  # 10MB
        }
        
        # Initialize sanitization rules
        self._sanitization_rules = {
            "pii": self._sanitize_pii,
            "credentials": self._sanitize_credentials,
            "sensitive_data": self._sanitize_sensitive_data
        }
        
        # Load custom configurations
        if "blocked_patterns" in self.config:
            self._blocked_patterns.extend(self.config["blocked_patterns"])
        
        if "max_output_sizes" in self.config:
            for ct, size in self.config["max_output_sizes"].items():
                self._max_output_sizes[ContentType(ct)] = size
        
        if "sanitization_rules" in self.config:
            self._sanitization_rules.update(self.config["sanitization_rules"])
        
        self._initialized = True
        logger.info("Output filter engine initialized successfully")
    
    async def process(self, content: ContentInput, context: Context) -> ValidationResult:
        """Process content through the output filter."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            violations = []
            matched_patterns = []
            
            # Check content size
            content_size = self._get_content_size(content)
            max_size = self._max_output_sizes.get(content.content_type, 0)
            if content_size > max_size:
                violations.append(f"Content size {content_size} exceeds maximum allowed size {max_size}")
            
            # Check against blocked patterns (for text content)
            if content.content_type == ContentType.TEXT and isinstance(content.content, str):
                for pattern in self._blocked_patterns:
                    if re.search(pattern, content.content):
                        violations.append(f"Content matches blocked pattern: {pattern}")
                        matched_patterns.append(pattern)
            
            # Determine if content is safe
            is_safe = len(violations) == 0
            
            # Calculate confidence
            confidence = 0.0 if violations else 1.0
            
            # Determine risk level
            risk_level = RiskLevel.HIGH_RISK if violations else RiskLevel.SAFE
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations,
                matched_patterns=matched_patterns
            )
    
    async def filter(self, content: ContentOutput, context: Context) -> FilteredOutput:
        """Filter output content."""
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        
        async with self._lock:
            filtered_content = content.content
            is_filtered = False
            filter_reason = None
            
            # Apply sanitization rules
            if content.content_type == ContentType.TEXT and isinstance(filtered_content, str):
                for rule_name, rule_func in self._sanitization_rules.items():
                    try:
                        result = await rule_func(filtered_content, context)
                        if result["is_sanitized"]:
                            filtered_content = result["content"]
                            is_filtered = True
                            if not filter_reason:
                                filter_reason = f"Applied {rule_name} sanitization"
                            else:
                                filter_reason += f", {rule_name} sanitization"
                    except Exception as e:
                        logger.error(f"Error in sanitization rule {rule_name}: {e}")
            
            processing_time = time.time() - start_time
            
            return FilteredOutput(
                content=filtered_content,
                content_type=content.content_type,
                is_filtered=is_filtered,
                filter_reason=filter_reason,
                processing_time=processing_time
            )
    
    def _get_content_size(self, content: ContentInput) -> int:
        """Get the size of the content in bytes."""
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            return len(content.content.encode('utf-8'))
        elif content.content_type == ContentType.STRUCTURED:
            return len(json.dumps(content.content).encode('utf-8'))
        # For other content types, we would need specific implementations
        return 0
    
    async def _sanitize_pii(self, content: str, context: Context) -> Dict[str, Any]:
        """Sanitize personally identifiable information."""
        # Define PII patterns
        pii_patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
            (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CREDIT_CARD]"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
            (r"\b\d{3}-\d{3}-\d{4}\b", "[PHONE]")
        ]
        
        is_sanitized = False
        for pattern, replacement in pii_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                is_sanitized = True
        
        return {
            "is_sanitized": is_sanitized,
            "content": content
        }
    
    async def _sanitize_credentials(self, content: str, context: Context) -> Dict[str, Any]:
        """Sanitize credential information."""
        # Define credential patterns
        credential_patterns = [
            (r"(?i)\b(password|pwd)\s*[:=]\s*[^\s]+", "[PASSWORD]"),
            (r"(?i)\b(api_key|apikey)\s*[:=]\s*[^\s]+", "[API_KEY]"),
            (r"(?i)\b(token|access_token)\s*[:=]\s*[^\s]+", "[TOKEN]"),
            (r"(?i)\b(secret|secret_key)\s*[:=]\s*[^\s]+", "[SECRET]")
        ]
        
        is_sanitized = False
        for pattern, replacement in credential_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                is_sanitized = True
        
        return {
            "is_sanitized": is_sanitized,
            "content": content
        }
    
    async def _sanitize_sensitive_data(self, content: str, context: Context) -> Dict[str, Any]:
        """Sanitize other sensitive data."""
        # Define sensitive data patterns
        sensitive_patterns = [
            (r"(?i)\b(medical|health)\b.*\b(record|info|data)\b", "[MEDICAL_DATA]"),
            (r"(?i)\b(financial|bank)\b.*\b(account|info|data)\b", "[FINANCIAL_DATA]"),
            (r"(?i)\b(personal|private)\b.*\b(info|data)\b", "[PERSONAL_DATA]")
        ]
        
        is_sanitized = False
        for pattern, replacement in sensitive_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                is_sanitized = True
        
        return {
            "is_sanitized": is_sanitized,
            "content": content
        }
    
    async def health_check(self) -> bool:
        """Check health of the output filter engine."""
        return self._initialized


class FilterRulesManager:
    """Manager for filter rules and configurations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._rules: Dict[str, FilterRule] = {}
        self._rule_categories: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the filter rules manager."""
        if self._initialized:
            return
            
        # Initialize rule categories
        self._rule_categories = {
            "content": [],
            "behavior": [],
            "security": [],
            "privacy": []
        }
        
        # Load rules from config
        if "rules" in self.config:
            for rule_data in self.config["rules"]:
                rule = FilterRule(**rule_data)
                self._rules[rule.rule_id] = rule
                
                # Add to category
                if "category" in rule.metadata:
                    category = rule.metadata["category"]
                    if category not in self._rule_categories:
                        self._rule_categories[category] = []
                    self._rule_categories[category].append(rule.rule_id)
        
        self._initialized = True
        logger.info("Filter rules manager initialized successfully")
    
    async def add_rule(self, rule: FilterRule) -> bool:
        """Add a filter rule."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if rule.rule_id in self._rules:
                logger.warning(f"Rule {rule.rule_id} already exists")
                return False
            
            self._rules[rule.rule_id] = rule
            
            # Add to category if specified
            if "category" in rule.metadata:
                category = rule.metadata["category"]
                if category not in self._rule_categories:
                    self._rule_categories[category] = []
                if rule.rule_id not in self._rule_categories[category]:
                    self._rule_categories[category].append(rule.rule_id)
            
            logger.info(f"Added filter rule: {rule.rule_id}")
            return True
    
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a filter rule."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if rule_id not in self._rules:
                logger.warning(f"Rule {rule_id} does not exist")
                return False
            
            # Remove from categories
            rule = self._rules[rule_id]
            if "category" in rule.metadata:
                category = rule.metadata["category"]
                if category in self._rule_categories and rule_id in self._rule_categories[category]:
                    self._rule_categories[category].remove(rule_id)
            
            del self._rules[rule_id]
            logger.info(f"Removed filter rule: {rule_id}")
            return True
    
    async def get_rule(self, rule_id: str) -> Optional[FilterRule]:
        """Get a filter rule by ID."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            return self._rules.get(rule_id)
    
    async def get_rules(self, category: Optional[str] = None, active_only: bool = True) -> List[FilterRule]:
        """Get filter rules, optionally filtered by category."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            rules = []
            
            # Filter by category if specified
            rule_ids = self._rule_categories.get(category, list(self._rules.keys())) if category else list(self._rules.keys())
            
            for rule_id in rule_ids:
                if rule_id in self._rules:
                    rule = self._rules[rule_id]
                    if not active_only or rule.is_active:
                        rules.append(rule)
            
            return rules
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a filter rule."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if rule_id not in self._rules:
                logger.warning(f"Rule {rule_id} does not exist")
                return False
            
            rule = self._rules[rule_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.utcnow()
            logger.info(f"Updated filter rule: {rule_id}")
            return True
    
    async def activate_rule(self, rule_id: str) -> bool:
        """Activate a filter rule."""
        return await self.update_rule(rule_id, {"is_active": True})
    
    async def deactivate_rule(self, rule_id: str) -> bool:
        """Deactivate a filter rule."""
        return await self.update_rule(rule_id, {"is_active": False})
    
    async def health_check(self) -> bool:
        """Check health of the filter rules manager."""
        return self._initialized

