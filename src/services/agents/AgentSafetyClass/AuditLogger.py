class AuditLogger:
    """Logger for content filtering actions."""
    
    def __init__(self, log_name: str):
        self.log_name = log_name
        self._initialized = False
        self._logger = logging.getLogger(f"agent_safety.{log_name}")
        self._audit_logs: List[Dict[str, Any]] = []
        self._max_log_entries = 10000
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the audit logger."""
        if self._initialized:
            return
            
        # Set up logger
        self._logger.setLevel(logging.INFO)
        
        # Create file handler if it doesn't exist
        if not self._logger.handlers:
            handler = logging.FileHandler(f"logs/{self.log_name}.log")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
        
        self._initialized = True
        logger.info(f"Audit logger {self.log_name} initialized successfully")
    
    async def log_validation(self, content: ContentInput, context: Context, result: ValidationResult) -> None:
        """Log a content validation action."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "validation",
                "content_type": content.content_type.value,
                "agent_id": context.agent_id,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "task_id": context.task_id,
                "is_safe": result.is_safe,
                "confidence": result.confidence,
                "risk_level": result.risk_level.value,
                "violations": result.violations,
                "matched_patterns": result.matched_patterns,
                "metadata": result.metadata
            }
            
            self._audit_logs.append(log_entry)
            
            # Trim logs if necessary
            if len(self._audit_logs) > self._max_log_entries:
                self._audit_logs = self._audit_logs[-self._max_log_entries:]
            
            # Log to file
            if result.is_safe:
                self._logger.info(f"Validation passed for {context.agent_id}")
            else:
                self._logger.warning(f"Validation failed for {context.agent_id}: {result.violations}")
    
    async def log_output_filtering(self, input_content: ContentOutput, output_content: FilteredOutput, context: Context) -> None:
        """Log an output filtering action."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "output_filtering",
                "content_type": output_content.content_type.value,
                "agent_id": context.agent_id,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "task_id": context.task_id,
                "is_filtered": output_content.is_filtered,
                "filter_reason": output_content.filter_reason,
                "processing_time": output_content.processing_time,
                "metadata": output_content.metadata
            }
            
            self._audit_logs.append(log_entry)
            
            # Trim logs if necessary
            if len(self._audit_logs) > self._max_log_entries:
                self._audit_logs = self._audit_logs[-self._max_log_entries:]
            
            # Log to file
            if output_content.is_filtered:
                self._logger.info(f"Output filtered for {context.agent_id}: {output_content.filter_reason}")
            else:
                self._logger.info(f"Output passed through for {context.agent_id}")
    
    async def log_rule_application(self, rule_id: str, content: ContentInput, context: Context, result: Dict[str, Any]) -> None:
        """Log a rule application action."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rule_application",
                "rule_id": rule_id,
                "content_type": content.content_type.value,
                "agent_id": context.agent_id,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "task_id": context.task_id,
                "result": result
            }
            
            self._audit_logs.append(log_entry)
            
            # Trim logs if necessary
            if len(self._audit_logs) > self._max_log_entries:
                self._audit_logs = self._audit_logs[-self._max_log_entries:]
            
            # Log to file
            self._logger.info(f"Rule {rule_id} applied for {context.agent_id}")
    
    async def get_audit_logs(self, agent_id: Optional[str] = None, start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs, optionally filtered."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            logs = self._audit_logs.copy()
            
            # Filter by agent_id if specified
            if agent_id:
                logs = [log for log in logs if log.get("agent_id") == agent_id]
            
            # Filter by time range if specified
            if start_time:
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) >= start_time]
            
            if end_time:
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) <= end_time]
            
            # Limit results
            logs = logs[-limit:] if limit > 0 else logs
            
            return logs
    
    async def health_check(self) -> bool:
        """Check health of the audit logger."""
        return self._initialized

