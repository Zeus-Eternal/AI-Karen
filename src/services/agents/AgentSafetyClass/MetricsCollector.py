class MetricsCollector:
    """Collector for performance metrics."""
    
    def __init__(self, metrics_name: str):
        self.metrics_name = metrics_name
        self._initialized = False
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    async def initialize(self) -> None:
        """Initialize the metrics collector."""
        if self._initialized:
            return
            
        # Initialize metrics
        self._metrics = {
            "validation_count": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "output_filtering_count": 0,
            "output_filtered": 0,
            "output_passed": 0,
            "rule_application_count": 0,
            "ml_prediction_count": 0,
            "validation_times": [],
            "output_filtering_times": [],
            "ml_prediction_times": [],
            "risk_level_counts": {
                "safe": 0,
                "low_risk": 0,
                "medium_risk": 0,
                "high_risk": 0,
                "critical_risk": 0
            },
            "content_type_counts": {
                "text": 0,
                "image": 0,
                "audio": 0,
                "video": 0,
                "structured": 0
            }
        }
        
        self._initialized = True
        logger.info(f"Metrics collector {self.metrics_name} initialized successfully")
    
    async def record_validation(self, is_safe: bool, validation_time: float, risk_level: RiskLevel, content_type: ContentType) -> None:
        """Record a validation metric."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            self._metrics["validation_count"] += 1
            
            if is_safe:
                self._metrics["validation_passed"] += 1
            else:
                self._metrics["validation_failed"] += 1
            
            self._metrics["validation_times"].append(validation_time)
            
            # Keep only the last 1000 validation times
            if len(self._metrics["validation_times"]) > 1000:
                self._metrics["validation_times"] = self._metrics["validation_times"][-1000:]
            
            # Update risk level counts
            self._metrics["risk_level_counts"][risk_level.value] += 1
            
            # Update content type counts
            self._metrics["content_type_counts"][content_type.value] += 1
    
    async def record_output_filtering(self, original_length: int, filtered_length: int, filtering_time: float) -> None:
        """Record an output filtering metric."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            self._metrics["output_filtering_count"] += 1
            
            if filtered_length < original_length:
                self._metrics["output_filtered"] += 1
            else:
                self._metrics["output_passed"] += 1
            
            self._metrics["output_filtering_times"].append(filtering_time)
            
            # Keep only the last 1000 filtering times
            if len(self._metrics["output_filtering_times"]) > 1000:
                self._metrics["output_filtering_times"] = self._metrics["output_filtering_times"][-1000:]
    
    async def record_rule_application(self) -> None:
        """Record a rule application metric."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            self._metrics["rule_application_count"] += 1
    
    async def record_ml_prediction(self, prediction_time: float) -> None:
        """Record an ML prediction metric."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            self._metrics["ml_prediction_count"] += 1
            self._metrics["ml_prediction_times"].append(prediction_time)
            
            # Keep only the last 1000 prediction times
            if len(self._metrics["ml_prediction_times"]) > 1000:
                self._metrics["ml_prediction_times"] = self._metrics["ml_prediction_times"][-1000:]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            metrics = self._metrics.copy()
            
            # Calculate averages
            if metrics["validation_times"]:
                metrics["avg_validation_time"] = sum(metrics["validation_times"]) / len(metrics["validation_times"])
                metrics["max_validation_time"] = max(metrics["validation_times"])
                metrics["min_validation_time"] = min(metrics["validation_times"])
            
            if metrics["output_filtering_times"]:
                metrics["avg_output_filtering_time"] = sum(metrics["output_filtering_times"]) / len(metrics["output_filtering_times"])
                metrics["max_output_filtering_time"] = max(metrics["output_filtering_times"])
                metrics["min_output_filtering_time"] = min(metrics["output_filtering_times"])
            
            if metrics["ml_prediction_times"]:
                metrics["avg_ml_prediction_time"] = sum(metrics["ml_prediction_times"]) / len(metrics["ml_prediction_times"])
                metrics["max_ml_prediction_time"] = max(metrics["ml_prediction_times"])
                metrics["min_ml_prediction_time"] = min(metrics["ml_prediction_times"])
            
            # Calculate rates
            if metrics["validation_count"] > 0:
                metrics["validation_pass_rate"] = metrics["validation_passed"] / metrics["validation_count"]
                metrics["validation_fail_rate"] = metrics["validation_failed"] / metrics["validation_count"]
            
            if metrics["output_filtering_count"] > 0:
                metrics["output_filter_rate"] = metrics["output_filtered"] / metrics["output_filtering_count"]
                metrics["output_pass_rate"] = metrics["output_passed"] / metrics["output_filtering_count"]
            
            return metrics
    
    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        if not self._initialized:
            await self.initialize()
            
        with self._lock:
            # Reset counters
            self._metrics["validation_count"] = 0
            self._metrics["validation_passed"] = 0
            self._metrics["validation_failed"] = 0
            self._metrics["output_filtering_count"] = 0
            self._metrics["output_filtered"] = 0
            self._metrics["output_passed"] = 0
            self._metrics["rule_application_count"] = 0
            self._metrics["ml_prediction_count"] = 0
            
            # Reset times
            self._metrics["validation_times"] = []
            self._metrics["output_filtering_times"] = []
            self._metrics["ml_prediction_times"] = []
            
            # Reset counts
            for level in self._metrics["risk_level_counts"]:
                self._metrics["risk_level_counts"][level] = 0
            
            for content_type in self._metrics["content_type_counts"]:
                self._metrics["content_type_counts"][content_type] = 0
    
    async def health_check(self) -> bool:
        """Check health of the metrics collector."""
        return self._initialized

