class MLModelsManager:
    """Manager for machine learning models."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._models: Dict[str, Any] = {}
        self._model_configs: Dict[str, Dict[str, Any]] = {}
        self._model_performance: Dict[str, Dict[str, float]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the ML models manager."""
        if self._initialized:
            return
            
        # Initialize model configurations
        self._model_configs = {
            "toxicity": {
                "threshold": 0.7,
                "enabled": True
            },
            "sentiment": {
                "threshold": 0.6,
                "enabled": True
            },
            "sensitivity": {
                "threshold": 0.5,
                "enabled": True
            }
        }
        
        # Load custom configurations
        if "models" in self.config:
            self._model_configs.update(self.config["models"])
        
        # Initialize models
        for model_name, model_config in self._model_configs.items():
            if model_config.get("enabled", True):
                await self._initialize_model(model_name, model_config)
        
        self._initialized = True
        logger.info("ML models manager initialized successfully")
    
    async def _initialize_model(self, model_name: str, model_config: Dict[str, Any]) -> None:
        """Initialize a specific ML model."""
        # This would typically load a pre-trained model
        # For now, we'll use placeholder implementations
        self._models[model_name] = {
            "model": None,  # Placeholder for actual model
            "config": model_config,
            "loaded_at": datetime.utcnow()
        }
        
        # Initialize performance tracking
        self._model_performance[model_name] = {
            "accuracy": 0.0,
            "latency": 0.0,
            "usage_count": 0
        }
        
        logger.info(f"Initialized ML model: {model_name}")
    
    async def predict(self, model_name: str, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Make a prediction using an ML model."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if model_name not in self._models:
                logger.error(f"Model {model_name} not found")
                return {"is_safe": True, "confidence": 0.0, "risk_score": 0.0}
            
            model_info = self._models[model_name]
            model_config = model_info["config"]
            
            # Check if model is enabled
            if not model_config.get("enabled", True):
                return {"is_safe": True, "confidence": 0.0, "risk_score": 0.0}
            
            start_time = time.time()
            
            # Make prediction
            result = await self._make_prediction(model_name, content, context)
            
            # Update performance metrics
            latency = time.time() - start_time
            usage_count = self._model_performance[model_name]["usage_count"] + 1
            
            # Update moving average for latency
            current_latency = self._model_performance[model_name]["latency"]
            new_latency = (current_latency * (usage_count - 1) + latency) / usage_count
            
            self._model_performance[model_name].update({
                "latency": new_latency,
                "usage_count": usage_count
            })
            
            return result
    
    async def _make_prediction(self, model_name: str, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Make a prediction using a specific model."""
        # This would typically use the actual model to make a prediction
        # For now, we'll use placeholder implementations
        
        if model_name == "toxicity":
            return await self._predict_toxicity(content, context)
        elif model_name == "sentiment":
            return await self._predict_sentiment(content, context)
        elif model_name == "sensitivity":
            return await self._predict_sensitivity(content, context)
        else:
            logger.error(f"Unknown model: {model_name}")
            return {"is_safe": True, "confidence": 0.0, "risk_score": 0.0}
    
    async def _predict_toxicity(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Predict toxicity of content."""
        # Placeholder implementation
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            toxic_words = ["toxic", "poison", "harmful", "dangerous", "abuse"]
            text = content.content.lower()
            
            toxic_count = sum(1 for word in toxic_words if word in text)
            if toxic_count > 0:
                violations.append(f"Content may be toxic (contains {toxic_count} toxic words)")
                risk_score = min(0.2 * toxic_count, 1.0)
        
        threshold = self._model_configs["toxicity"].get("threshold", 0.7)
        is_safe = risk_score < threshold
        confidence = 1.0 - risk_score
        
        return {
            "is_safe": is_safe,
            "confidence": confidence,
            "risk_score": risk_score,
            "violations": violations
        }
    
    async def _predict_sentiment(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Predict sentiment of content."""
        # Placeholder implementation
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            negative_words = ["hate", "angry", "sad", "bad", "terrible", "awful"]
            text = content.content.lower()
            
            negative_count = sum(1 for word in negative_words if word in text)
            if negative_count > 2:
                violations.append("Content has overly negative sentiment")
                risk_score = min(0.15 * negative_count, 1.0)
        
        threshold = self._model_configs["sentiment"].get("threshold", 0.6)
        is_safe = risk_score < threshold
        confidence = 1.0 - risk_score
        
        return {
            "is_safe": is_safe,
            "confidence": confidence,
            "risk_score": risk_score,
            "violations": violations
        }
    
    async def _predict_sensitivity(self, content: ContentInput, context: Context) -> Dict[str, Any]:
        """Predict sensitivity of content."""
        # Placeholder implementation
        violations = []
        risk_score = 0.0
        
        if content.content_type == ContentType.TEXT and isinstance(content.content, str):
            # Simple heuristic for demonstration
            sensitive_topics = ["politics", "religion", "race", "gender", "health"]
            text = content.content.lower()
            
            sensitive_count = sum(1 for topic in sensitive_topics if topic in text)
            if sensitive_count > 0:
                violations.append(f"Content may be sensitive (contains {sensitive_count} sensitive topics)")
                risk_score = min(0.2 * sensitive_count, 1.0)
        
        threshold = self._model_configs["sensitivity"].get("threshold", 0.5)
        is_safe = risk_score < threshold
        confidence = 1.0 - risk_score
        
        return {
            "is_safe": is_safe,
            "confidence": confidence,
            "risk_score": risk_score,
            "violations": violations
        }
    
    async def update_model(self, model_name: str, model_data: Any) -> bool:
        """Update an ML model."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if model_name not in self._models:
                logger.error(f"Model {model_name} not found")
                return False
            
            # This would typically update the actual model
            # For now, we'll just update the timestamp
            self._models[model_name]["updated_at"] = datetime.utcnow()
            
            logger.info(f"Updated ML model: {model_name}")
            return True
    
    async def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for ML models."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if model_name:
                return self._model_performance.get(model_name, {})
            else:
                return self._model_performance.copy()
    
    async def health_check(self) -> bool:
        """Check health of the ML models manager."""
        return self._initialized
