import asyncio
import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from ai_karen_engine.core.services.base import ServiceConfig

# Import Agent Safety classes
from .BehaviorTracker import BehaviorTracker
from .AnomalyDetector import AnomalyDetector
from .PatternRecognizer import PatternRecognizer
from .BaselineGenerator import BaselineGenerator
from .BehaviorProfiler import BehaviorProfiler
from .RiskAssessor import RiskAssessor
from .CorrelationEngine import CorrelationEngine
from .BehaviorLogger import BehaviorLogger
from ..agent_safety import AgentSafety

# Import data structures
from ..agent_safety import (
    SafetyConfig, BehaviorData, BehaviorProfile, RiskAssessment,
    BehaviorAnalysis, CorrelationResult, RiskLevel
)

logger = logging.getLogger(__name__)


class AgentSafetyMonitor:
    """
    Agent Safety Monitor service that integrates Content Safety and Behavior Monitoring.
    
    This service provides comprehensive safety mechanisms for agents, including content filtering,
    action validation, security checks, and behavior monitoring to ensure agents operate safely.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig(name="agent_safety_monitor")
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize content safety module
        safety_config = SafetyConfig()
        self.content_safety = AgentSafety(safety_config)
        
        # Initialize behavior monitoring modules
        self.behavior_tracker = BehaviorTracker(config=self.config)
        self.anomaly_detector = AnomalyDetector(config=self.config)
        self.pattern_recognizer = PatternRecognizer(config=self.config)
        self.baseline_generator = BaselineGenerator(config=self.config)
        self.behavior_profiler = BehaviorProfiler(config=self.config)
        self.risk_assessor = RiskAssessor(config=self.config)
        self.correlation_engine = CorrelationEngine(config=self.config)
        self.behavior_logger = BehaviorLogger(config=self.config)
        
        # Behavior monitoring configuration
        self._behavior_config = {
            # General monitoring settings
            "enable_real_time_monitoring": True,
            "monitoring_interval": 5.0,  # seconds
            "enable_adaptive_learning": True,
            "max_history_size": 1000,
            
            # Threshold settings
            "anomaly_threshold": 0.7,
            "baseline_threshold": 0.5,
            "risk_threshold": 0.6,
            "correlation_threshold": 0.8,
            
            # Anomaly detection settings
            "enable_statistical_anomaly_detection": True,
            "enable_ml_anomaly_detection": True,
            "enable_rule_based_anomaly_detection": True,
            "anomaly_detection_sensitivity": "medium",  # low, medium, high
            
            # Pattern recognition settings
            "enable_sequence_pattern_detection": True,
            "enable_frequency_pattern_detection": True,
            "enable_trend_pattern_detection": True,
            "enable_correlation_pattern_detection": True,
            "pattern_detection_sensitivity": "medium",  # low, medium, high
            
            # Baseline settings
            "baseline_update_interval": 3600.0,  # seconds (1 hour)
            "baseline_adaptation_rate": 0.1,  # 0.0 to 1.0
            "enable_individual_baselines": True,
            "enable_group_baselines": True,
            
            # Risk assessment settings
            "enable_resource_risk_assessment": True,
            "enable_performance_risk_assessment": True,
            "enable_behavior_risk_assessment": True,
            "enable_anomaly_risk_assessment": True,
            "enable_pattern_risk_assessment": True,
            "enable_baseline_risk_assessment": True,
            "enable_profile_risk_assessment": True,
            "risk_assessment_sensitivity": "medium",  # low, medium, high
            
            # Correlation settings
            "enable_temporal_correlation": True,
            "enable_behavioral_correlation": True,
            "enable_anomaly_correlation": True,
            "enable_pattern_correlation": True,
            "correlation_analysis_window": 300.0,  # seconds (5 minutes)
            
            # Logging settings
            "log_file_path": "logs/behavior_monitor.log",
            "enable_detailed_logging": True,
            "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            "max_log_size": 10485760,  # 10MB in bytes
            "log_backup_count": 5,
            "enable_log_rotation": True,
            
            # Recovery settings
            "enable_auto_recovery": True,
            "recovery_attempts": 3,
            "recovery_interval": 60.0,  # seconds
            "enable_circuit_breaker": True,
            "circuit_breaker_threshold": 5,  # number of failures
            "circuit_breaker_timeout": 300.0,  # seconds (5 minutes)
            
            # Performance settings
            "enable_performance_monitoring": True,
            "performance_metrics_interval": 60.0,  # seconds
            "enable_memory_usage_monitoring": True,
            "enable_cpu_usage_monitoring": True,
            "enable_disk_usage_monitoring": True,
            "enable_network_usage_monitoring": True,
            
            # Security settings
            "enable_security_checks": True,
            "security_check_interval": 30.0,  # seconds
            "enable_data_encryption": True,
            "enable_access_control": True,
            "enable_audit_trail": True
        }
        
        # Thread-safe agent behavior data storage
        self._agent_behavior_data: Dict[str, List[BehaviorData]] = defaultdict(list)
        self._agent_behavior_profiles: Dict[str, BehaviorProfile] = {}
        self._agent_baselines: Dict[str, Dict[str, Any]] = {}
        self._agent_risk_history: Dict[str, List[RiskAssessment]] = defaultdict(list)
        
        # Thread-safe locks for data structures
        self._behavior_data_lock = asyncio.Lock()
        self._profiles_lock = asyncio.Lock()
        self._baselines_lock = asyncio.Lock()
        self._risk_history_lock = asyncio.Lock()
        self._config_lock = asyncio.Lock()
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring: bool = False
        self._last_update_time: Optional[datetime] = None
    
    async def initialize(self) -> None:
        """Initialize the agent safety monitor service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize content safety module
                try:
                    await self.content_safety.initialize()
                except Exception as e:
                    logger.error(f"Failed to initialize content safety module: {e}")
                    raise RuntimeError(f"Content safety module initialization failed: {e}")
                
                # Initialize behavior monitoring modules
                modules_to_initialize = [
                    ("behavior tracker", self.behavior_tracker),
                    ("anomaly detector", self.anomaly_detector),
                    ("pattern recognizer", self.pattern_recognizer),
                    ("baseline generator", self.baseline_generator),
                    ("behavior profiler", self.behavior_profiler),
                    ("risk assessor", self.risk_assessor),
                    ("correlation engine", self.correlation_engine),
                    ("behavior logger", self.behavior_logger)
                ]
                
                for module_name, module in modules_to_initialize:
                    try:
                        await module.initialize()
                        logger.debug(f"Successfully initialized {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize {module_name}: {e}")
                        # Continue with other modules even if one fails
                        # This allows partial functionality
                
                # Start monitoring task if real-time monitoring is enabled
                if self._behavior_config["enable_real_time_monitoring"]:
                    try:
                        self._monitoring_task = asyncio.create_task(self._monitor_agents_behavior())
                        logger.debug("Successfully started behavior monitoring task")
                    except Exception as e:
                        logger.error(f"Failed to start behavior monitoring task: {e}")
                        # Continue without monitoring task
                        # This allows other functionality to work even if monitoring fails
                
                self._initialized = True
                logger.info("Agent safety monitor service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize agent safety monitor: {e}")
                # Attempt to clean up any partial initialization
                try:
                    await self.stop()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup after initialization failure: {cleanup_error}")
                raise RuntimeError(f"Agent safety monitor initialization failed: {e}")
    
    async def start(self) -> None:
        """Start the agent safety monitor service."""
        if not self._initialized:
            await self.initialize()
            
        logger.info("Agent safety monitor service started")
    
    async def stop(self) -> None:
        """Stop the agent safety monitor service."""
        # Cancel monitoring task if it exists
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Agent safety monitor service stopped")
    
    async def health_check(self) -> bool:
        """Check health of the agent safety monitor service."""
        if not self._initialized:
            return False
            
        try:
            # Check content safety module health
            content_safety_healthy = await self.content_safety.health_check()
            
            # Check behavior monitoring modules health
            behavior_modules_healthy = all([
                await self.behavior_tracker.health_check(),
                await self.anomaly_detector.health_check(),
                await self.pattern_recognizer.health_check(),
                await self.baseline_generator.health_check(),
                await self.behavior_profiler.health_check(),
                await self.risk_assessor.health_check(),
                await self.correlation_engine.health_check(),
                await self.behavior_logger.health_check()
            ])
            
            return content_safety_healthy and behavior_modules_healthy
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def _monitor_agents_behavior(self) -> None:
        """Monitor agent behavior in real-time."""
        logger.info("Starting real-time behavior monitoring")
        
        # Create a set to track agents that have been processed
        processed_agents = set()
        
        while True:
            try:
                # Get all agent IDs
                agent_ids = list(self._agent_behavior_data.keys())
                
                # Track if any new agents were added
                new_agents = set(agent_ids) - processed_agents
                if new_agents:
                    logger.info(f"New agents detected for monitoring: {list(new_agents)}")
                    processed_agents.update(new_agents)
                
                # Track if any agents were removed
                removed_agents = processed_agents - set(agent_ids)
                if removed_agents:
                    logger.info(f"Agents removed from monitoring: {list(removed_agents)}")
                    processed_agents = set(agent_ids)
                
                for agent_id in agent_ids:
                    try:
                        # Get latest behavior data
                        try:
                            behavior_data_list = self._agent_behavior_data.get(agent_id, [])
                            if not behavior_data_list:
                                continue
                            
                            latest_behavior_data = behavior_data_list[-1]
                        except Exception as e:
                            logger.error(f"Error retrieving behavior data for agent {agent_id}: {e}")
                            continue
                        
                        # Check if behavior data is recent (within 2 monitoring intervals)
                        try:
                            time_since_last_update = (datetime.utcnow() - latest_behavior_data.timestamp).total_seconds()
                            if time_since_last_update > (2 * self._behavior_config["monitoring_interval"]):
                                logger.debug(f"Agent {agent_id} behavior data is stale (last update: {time_since_last_update:.2f}s ago)")
                                continue
                        except Exception as e:
                            logger.error(f"Error checking behavior data freshness for agent {agent_id}: {e}")
                            # Continue with analysis even if freshness check fails
                            pass
                        
                        # Analyze agent behavior
                        try:
                            analysis_result = await self.analyze_agent_behavior(agent_id, latest_behavior_data)
                        except Exception as e:
                            logger.error(f"Error analyzing behavior for agent {agent_id}: {e}")
                            # Continue with next agent if analysis fails
                            continue
                        
                        # Log the analysis result
                        try:
                            await self.behavior_logger.log_analysis_result(analysis_result)
                        except Exception as e:
                            logger.error(f"Error logging analysis result for agent {agent_id}: {e}")
                            # Continue with risk assessment even if logging fails
                            pass
                        
                        # Check if risk level is above threshold
                        try:
                            if analysis_result.risk_result.risk_score > self._behavior_config["risk_threshold"]:
                                logger.warning(f"Agent {agent_id} behavior risk above threshold: {analysis_result.risk_result.risk_score}")
                                
                                # Take appropriate action based on risk level
                                if analysis_result.risk_result.risk_level == RiskLevel.CRITICAL_RISK:
                                    # Implement critical risk response
                                    try:
                                        await self._handle_critical_risk(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling critical risk for agent {agent_id}: {e}")
                                elif analysis_result.risk_result.risk_level == RiskLevel.HIGH_RISK:
                                    # Implement high risk response
                                    try:
                                        await self._handle_high_risk(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling high risk for agent {agent_id}: {e}")
                                elif analysis_result.risk_result.risk_level == RiskLevel.MEDIUM_RISK:
                                    # Implement medium risk response
                                    try:
                                        await self._handle_medium_risk(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling medium risk for agent {agent_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error assessing risk for agent {agent_id}: {e}")
                            # Continue with other checks even if risk assessment fails
                            pass
                        
                        # Check for anomalies
                        try:
                            if analysis_result.anomaly_result.is_anomaly:
                                logger.warning(f"Anomaly detected for agent {agent_id}: {analysis_result.anomaly_result.description}")
                                
                                # Take appropriate action based on anomaly severity
                                if analysis_result.anomaly_result.anomaly_score > 0.9:
                                    # Critical anomaly
                                    try:
                                        await self._handle_critical_anomaly(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling critical anomaly for agent {agent_id}: {e}")
                                elif analysis_result.anomaly_result.anomaly_score > 0.7:
                                    # High anomaly
                                    try:
                                        await self._handle_high_anomaly(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling high anomaly for agent {agent_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error checking anomalies for agent {agent_id}: {e}")
                            # Continue with other checks even if anomaly check fails
                            pass
                        
                        # Check for unsafe patterns
                        try:
                            if analysis_result.pattern_result.pattern_detected:
                                logger.warning(f"Unsafe pattern detected for agent {agent_id}: {analysis_result.pattern_result.description}")
                                
                                # Take appropriate action based on pattern severity
                                if analysis_result.pattern_result.severity == RiskLevel.CRITICAL_RISK:
                                    # Critical pattern
                                    try:
                                        await self._handle_critical_pattern(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling critical pattern for agent {agent_id}: {e}")
                                elif analysis_result.pattern_result.severity == RiskLevel.HIGH_RISK:
                                    # High pattern
                                    try:
                                        await self._handle_high_pattern(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling high pattern for agent {agent_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error checking patterns for agent {agent_id}: {e}")
                            # Continue with other checks even if pattern check fails
                            pass
                        
                        # Check for baseline deviations
                        try:
                            if not analysis_result.baseline_result.is_within_threshold:
                                logger.warning(f"Baseline deviation detected for agent {agent_id}: deviation score {analysis_result.baseline_result.deviation_score}")
                                
                                # Take appropriate action based on deviation severity
                                if analysis_result.baseline_result.deviation_score > 0.9:
                                    # Critical deviation
                                    try:
                                        await self._handle_critical_baseline_deviation(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling critical baseline deviation for agent {agent_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error checking baseline deviation for agent {agent_id}: {e}")
                            # Continue with other checks even if baseline check fails
                            pass
                        
                        # Check for correlations
                        try:
                            if analysis_result.correlation_result.correlation_detected:
                                logger.warning(f"Behavior correlation detected for agent {agent_id}: {analysis_result.correlation_result.description}")
                                
                                # Take appropriate action based on correlation strength
                                if analysis_result.correlation_result.correlation_strength > 0.9:
                                    # Critical correlation
                                    try:
                                        await self._handle_critical_correlation(agent_id, analysis_result)
                                    except Exception as e:
                                        logger.error(f"Error handling critical correlation for agent {agent_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error checking correlations for agent {agent_id}: {e}")
                            # Continue even if correlation check fails
                            pass
                    except Exception as e:
                        logger.error(f"Unexpected error monitoring agent {agent_id}: {e}")
                        # Continue with next agent
                        continue
                
                # Wait for next monitoring interval
                await asyncio.sleep(self._behavior_config["monitoring_interval"])
            except asyncio.CancelledError:
                logger.info("Real-time behavior monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in behavior monitoring: {e}")
                await asyncio.sleep(self._behavior_config["monitoring_interval"])
    
    async def _handle_critical_risk(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle critical risk situations."""
        logger.critical(f"Critical risk detected for agent {agent_id}: {analysis_result.risk_result}")
        
        # Log the critical risk event
        await self.behavior_logger.log_event(
            event_type="critical_risk",
            component="BehaviorMonitor",
            level="CRITICAL",
            message=f"Critical risk detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "risk_level": analysis_result.risk_result.risk_level.value,
                "risk_score": analysis_result.risk_result.risk_score,
                "factors": analysis_result.risk_result.factors,
                "recommendations": analysis_result.risk_result.recommendations
            }
        )
        
        # Implement additional risk mitigation strategies here
        # For example: pause agent, notify administrator, etc.
    
    async def _handle_high_risk(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle high risk situations."""
        logger.error(f"High risk detected for agent {agent_id}: {analysis_result.risk_result}")
        
        # Log the high risk event
        await self.behavior_logger.log_event(
            event_type="high_risk",
            component="BehaviorMonitor",
            level="ERROR",
            message=f"High risk detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "risk_level": analysis_result.risk_result.risk_level.value,
                "risk_score": analysis_result.risk_result.risk_score,
                "factors": analysis_result.risk_result.factors,
                "recommendations": analysis_result.risk_result.recommendations
            }
        )
        
        # Implement additional risk mitigation strategies here
        # For example: restrict agent capabilities, increase monitoring frequency, etc.
    
    async def _handle_medium_risk(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle medium risk situations."""
        logger.warning(f"Medium risk detected for agent {agent_id}: {analysis_result.risk_result}")
        
        # Log the medium risk event
        await self.behavior_logger.log_event(
            event_type="medium_risk",
            component="BehaviorMonitor",
            level="WARNING",
            message=f"Medium risk detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "risk_level": analysis_result.risk_result.risk_level.value,
                "risk_score": analysis_result.risk_result.risk_score,
                "factors": analysis_result.risk_result.factors,
                "recommendations": analysis_result.risk_result.recommendations
            }
        )
        
        # Implement additional risk mitigation strategies here
        # For example: log more frequently, notify for review, etc.
    
    async def _handle_critical_anomaly(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle critical anomaly situations."""
        logger.critical(f"Critical anomaly detected for agent {agent_id}: {analysis_result.anomaly_result}")
        
        # Log the critical anomaly event
        await self.behavior_logger.log_event(
            event_type="critical_anomaly",
            component="BehaviorMonitor",
            level="CRITICAL",
            message=f"Critical anomaly detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "anomaly_type": analysis_result.anomaly_result.anomaly_type,
                "anomaly_score": analysis_result.anomaly_result.anomaly_score,
                "confidence": analysis_result.anomaly_result.confidence,
                "description": analysis_result.anomaly_result.description
            }
        )
        
        # Implement additional anomaly mitigation strategies here
        # For example: pause agent, notify administrator, etc.
    
    async def _handle_high_anomaly(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle high anomaly situations."""
        logger.error(f"High anomaly detected for agent {agent_id}: {analysis_result.anomaly_result}")
        
        # Log the high anomaly event
        await self.behavior_logger.log_event(
            event_type="high_anomaly",
            component="BehaviorMonitor",
            level="ERROR",
            message=f"High anomaly detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "anomaly_type": analysis_result.anomaly_result.anomaly_type,
                "anomaly_score": analysis_result.anomaly_result.anomaly_score,
                "confidence": analysis_result.anomaly_result.confidence,
                "description": analysis_result.anomaly_result.description
            }
        )
        
        # Implement additional anomaly mitigation strategies here
        # For example: restrict agent capabilities, increase monitoring frequency, etc.
    
    async def _handle_critical_pattern(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle critical pattern situations."""
        logger.critical(f"Critical pattern detected for agent {agent_id}: {analysis_result.pattern_result}")
        
        # Log the critical pattern event
        await self.behavior_logger.log_event(
            event_type="critical_pattern",
            component="BehaviorMonitor",
            level="CRITICAL",
            message=f"Critical pattern detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "pattern_type": analysis_result.pattern_result.pattern_type,
                "pattern_id": analysis_result.pattern_result.pattern_id,
                "confidence": analysis_result.pattern_result.confidence,
                "severity": analysis_result.pattern_result.severity.value,
                "description": analysis_result.pattern_result.description
            }
        )
        
        # Implement additional pattern mitigation strategies here
        # For example: pause agent, notify administrator, etc.
    
    async def _handle_high_pattern(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle high pattern situations."""
        logger.error(f"High pattern detected for agent {agent_id}: {analysis_result.pattern_result}")
        
        # Log the high pattern event
        await self.behavior_logger.log_event(
            event_type="high_pattern",
            component="BehaviorMonitor",
            level="ERROR",
            message=f"High pattern detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "pattern_type": analysis_result.pattern_result.pattern_type,
                "pattern_id": analysis_result.pattern_result.pattern_id,
                "confidence": analysis_result.pattern_result.confidence,
                "severity": analysis_result.pattern_result.severity.value,
                "description": analysis_result.pattern_result.description
            }
        )
        
        # Implement additional pattern mitigation strategies here
        # For example: restrict agent capabilities, increase monitoring frequency, etc.
    
    async def _handle_critical_baseline_deviation(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle critical baseline deviation situations."""
        logger.critical(f"Critical baseline deviation detected for agent {agent_id}: {analysis_result.baseline_result}")
        
        # Log the critical baseline deviation event
        await self.behavior_logger.log_event(
            event_type="critical_baseline_deviation",
            component="BehaviorMonitor",
            level="CRITICAL",
            message=f"Critical baseline deviation detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "baseline_id": analysis_result.baseline_result.baseline_id,
                "deviation_score": analysis_result.baseline_result.deviation_score,
                "threshold": analysis_result.baseline_result.threshold,
                "is_within_threshold": analysis_result.baseline_result.is_within_threshold
            }
        )
        
        # Implement additional baseline deviation mitigation strategies here
        # For example: pause agent, notify administrator, regenerate baseline, etc.
    
    async def _handle_critical_correlation(self, agent_id: str, analysis_result: BehaviorAnalysis) -> None:
        """Handle critical correlation situations."""
        logger.critical(f"Critical correlation detected for agent {agent_id}: {analysis_result.correlation_result}")
        
        # Log the critical correlation event
        await self.behavior_logger.log_event(
            event_type="critical_correlation",
            component="BehaviorMonitor",
            level="CRITICAL",
            message=f"Critical correlation detected for agent {agent_id}",
            agent_id=agent_id,
            data={
                "correlation_type": analysis_result.correlation_result.correlation_type,
                "correlated_agents": analysis_result.correlation_result.correlated_agents,
                "correlation_strength": analysis_result.correlation_result.correlation_strength,
                "confidence": analysis_result.correlation_result.confidence,
                "description": analysis_result.correlation_result.description
            }
        )
        
        # Implement additional correlation mitigation strategies here
        # For example: pause all correlated agents, notify administrator, etc.
    
    async def track_agent_behavior(self, agent_id: str, behavior_data: BehaviorData) -> bool:
        """
        Track agent behavior.
        
        Args:
            agent_id: Unique identifier of the agent
            behavior_data: Behavior data to track
            
        Returns:
            True if tracking was successful, False otherwise
        """
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize agent safety monitor for tracking behavior: {e}")
                return False
            
        try:
            # Validate behavior data
            if not behavior_data or not agent_id:
                logger.error("Invalid behavior data or agent ID")
                return False
            
            # Thread-safe access to behavior data
            try:
                async with self._behavior_data_lock:
                    # Add behavior data to agent's history
                    self._agent_behavior_data[agent_id].append(behavior_data)
                    
                    # Limit history size
                    if len(self._agent_behavior_data[agent_id]) > self._behavior_config["max_history_size"]:
                        self._agent_behavior_data[agent_id] = self._agent_behavior_data[agent_id][-self._behavior_config["max_history_size"]:]
            except Exception as e:
                logger.error(f"Failed to store behavior data for agent {agent_id}: {e}")
                return False
            
            # Log the behavior data
            try:
                await self.behavior_logger.log_behavior_data(behavior_data)
            except Exception as e:
                logger.error(f"Failed to log behavior data for agent {agent_id}: {e}")
                # Continue even if logging fails
                # This allows the behavior tracking to work even if logging fails
            
            return True
        except Exception as e:
            logger.error(f"Unexpected error tracking agent behavior for agent {agent_id}: {e}")
            return False
    
    async def analyze_agent_behavior(self, agent_id: str, behavior_data: BehaviorData) -> BehaviorAnalysis:
        """
        Analyze agent behavior.
        
        Args:
            agent_id: Unique identifier of the agent
            behavior_data: Behavior data to analyze
            
        Returns:
            Behavior analysis result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Thread-safe access to behavior history
            async with self._behavior_data_lock:
                # Get agent's behavior history
                behavior_history = self._agent_behavior_data.get(agent_id, [])
            
            # Detect anomalies
            anomaly_result = await self.anomaly_detector.detect_anomalies(behavior_data)
            
            # Recognize patterns
            pattern_result = await self.pattern_recognizer.recognize_patterns(behavior_data)
            
            # Thread-safe access to baselines
            async with self._baselines_lock:
                # Get or create baseline
                baseline_id = f"{agent_id}_baseline"
                baseline_data = self._agent_baselines.get(baseline_id)
                if not baseline_data:
                    baseline_result = await self.baseline_generator.generate_baseline(agent_id, behavior_history)
                    if baseline_result:
                        self._agent_baselines[baseline_id] = baseline_result.__dict__
            
            # Compare with baseline
            baseline_result = await self.baseline_generator.compare_to_baseline(agent_id, behavior_data)
            
            # Thread-safe access to profiles
            async with self._profiles_lock:
                # Get or create behavior profile
                profile = self._agent_behavior_profiles.get(agent_id)
                if not profile:
                    profile = await self.behavior_profiler.create_profile(agent_id, behavior_history)
                    if profile:
                        self._agent_behavior_profiles[agent_id] = profile
                else:
                    # Update profile with new behavior data
                    update_success = await self.behavior_profiler.update_profile(agent_id, [behavior_data])
                    if update_success and isinstance(update_success, bool):
                        # Get updated profile
                        profile = await self.behavior_profiler.get_profile(agent_id)
                        if profile:
                            self._agent_behavior_profiles[agent_id] = profile
            
            # Assess risk
            risk_result = await self.risk_assessor.assess_risk(agent_id, behavior_data)
            
            # Thread-safe access to risk history
            async with self._risk_history_lock:
                # Store risk history
                self._agent_risk_history[agent_id].append(risk_result)
            
            # Thread-safe access to behavior data for correlation analysis
            async with self._behavior_data_lock:
                # Perform correlation analysis if there are multiple agents
                correlation_result = CorrelationResult(
                    correlation_detected=False,
                    correlation_type="none",
                    correlated_agents=[],
                    correlation_strength=0.0,
                    confidence=0.0,
                    description="No correlation analysis performed"
                )
                
                if len(self._agent_behavior_data) > 1:
                    # Get other agent IDs
                    other_agent_ids = [aid for aid in self._agent_behavior_data.keys() if aid != agent_id]
                    
                    if other_agent_ids:
                        # Get other agents' behavior data
                        other_agents_data = {
                            aid: self._agent_behavior_data[aid][-1] if self._agent_behavior_data[aid] else None
                            for aid in other_agent_ids
                        }
                        
                        # Filter out None values
                        other_agents_data = {aid: data for aid, data in other_agents_data.items() if data}
                        
                        if other_agents_data:
                            # Perform correlation analysis
                            # Add behavior data for correlation analysis
                            await self.correlation_engine.add_behavior_data(behavior_data)
                            
                            # Get correlation results
                            correlation_results = await self.correlation_engine.get_correlations(agent_id)
                            
                            # Use the most recent correlation result or create a default one
                            correlation_result = correlation_results[-1] if correlation_results else CorrelationResult(
                                correlation_detected=False,
                                correlation_type="none",
                                correlated_agents=[],
                                correlation_strength=0.0,
                                confidence=0.0,
                                description="No correlation detected"
                            )
            
            # Create behavior analysis result
            # Handle cases where some results might be lists or None
            pattern_result_single = pattern_result[0] if pattern_result and isinstance(pattern_result, list) else pattern_result
            
            analysis_result = BehaviorAnalysis(
                agent_id=agent_id,
                anomaly_result=anomaly_result,
                pattern_result=pattern_result_single,
                baseline_result=baseline_result,
                profile_result=profile if profile else None,
                risk_result=risk_result,
                correlation_result=correlation_result
            )
            
            return analysis_result
        except Exception as e:
            logger.error(f"Failed to analyze agent behavior: {e}")
            raise
    
    async def check_content_safety(self, content: str, agent_id: str = "unknown") -> Dict[str, Any]:
        """
        Check if content is safe.
        
        Args:
            content: Content to check
            agent_id: ID of the agent generating the content
            
        Returns:
            Safety check result
        """
        if not self._initialized:
            await self.initialize()
            
        result = await self.content_safety.check_content_safety(content)
        return result.__dict__ if result else {}
    
    async def check_action_safety(
        self, 
        agent_id: str, 
        action: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if an action is safe for an agent to perform.
        
        Args:
            agent_id: Unique identifier of the agent
            action: Action to check
            parameters: Parameters for the action
            
        Returns:
            Safety check result
        """
        if not self._initialized:
            await self.initialize()
            
        result = await self.content_safety.check_action_safety(agent_id, action, parameters)
        return result.__dict__ if result else {}
    
    async def check_response_safety(
        self, 
        agent_id: str, 
        response: str
    ) -> Dict[str, Any]:
        """
        Check if a response from an agent is safe.
        
        Args:
            agent_id: Unique identifier of the agent
            response: Response to check
            
        Returns:
            Safety check result
        """
        if not self._initialized:
            await self.initialize()
            
        result = await self.content_safety.check_response_safety(agent_id, response)
        return result.__dict__ if result else {}
    
    async def get_agent_behavior_profile(self, agent_id: str) -> Optional[BehaviorProfile]:
        """
        Get agent behavior profile.
        
        Args:
            agent_id: Unique identifier of the agent
            
        Returns:
            Agent behavior profile if it exists, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        # Thread-safe access to profiles
        async with self._profiles_lock:
            return self._agent_behavior_profiles.get(agent_id)
    
    async def get_agent_risk_history(self, agent_id: str, limit: int = 100) -> List[RiskAssessment]:
        """
        Get agent risk history.
        
        Args:
            agent_id: Unique identifier of the agent
            limit: Maximum number of risk assessments to return
            
        Returns:
            List of risk assessments
        """
        if not self._initialized:
            await self.initialize()
            
        # Thread-safe access to risk history
        async with self._risk_history_lock:
            risk_history = self._agent_risk_history.get(agent_id, [])
            return risk_history[-limit:] if limit > 0 else risk_history
    
    async def get_behavior_logs(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get behavior logs.
        
        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Maximum number of logs to return
            
        Returns:
            List of behavior logs
        """
        if not self._initialized:
            await self.initialize()
            
        # Get logs from behavior logger
        if agent_id:
            log_entries = await self.behavior_logger.get_agent_logs(agent_id, start_time, end_time, None, None, limit)
        else:
            log_entries = await self.behavior_logger.get_all_logs(start_time, end_time, None, None, None)
        
        # Log entries are already dictionaries
        return log_entries
    
    async def get_behavior_metrics(self) -> Dict[str, Any]:
        """
        Get behavior monitoring metrics.
        
        Returns:
            Behavior monitoring metrics
        """
        if not self._initialized:
            await self.initialize()
            
        # Thread-safe access to metrics data
        async with self._behavior_data_lock, self._profiles_lock, self._baselines_lock, self._config_lock:
            return {
                "tracked_agents": len(self._agent_behavior_data),
                "profiles_created": len(self._agent_behavior_profiles),
                "baselines_created": len(self._agent_baselines),
                "total_behavior_data": sum(len(data) for data in self._agent_behavior_data.values()),
                "monitoring_interval": self._behavior_config["monitoring_interval"],
                "anomaly_threshold": self._behavior_config["anomaly_threshold"],
                "baseline_threshold": self._behavior_config["baseline_threshold"],
                "risk_threshold": self._behavior_config["risk_threshold"],
                "correlation_threshold": self._behavior_config["correlation_threshold"]
            }
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get the current monitoring status.

        Returns:
            Dict[str, Any]: Current monitoring status
        """
        async with self._lock:
            return {
                "is_monitoring": self._is_monitoring if hasattr(self, '_is_monitoring') else False,
                "monitored_agents": list(self._agent_behavior_data.keys()),
                "agent_count": len(self._agent_behavior_data),
                "last_update_time": getattr(self, '_last_update_time', None),
                "config": self._behavior_config
            }

    async def update_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the behavior monitoring configuration.

        Args:
            config_updates: Dictionary of configuration updates

        Returns:
            bool: True if configuration was updated successfully, False otherwise
        """
        try:
            async with self._config_lock:
                # Validate configuration updates
                for key, value in config_updates.items():
                    if key in self._behavior_config:
                        # Type validation for specific keys
                        if key.endswith("_threshold") or key.endswith("_interval") or key.endswith("_rate"):
                            if not isinstance(value, (int, float)) or value < 0:
                                await self.behavior_logger.log_event(
                                    event_type="config_error",
                                    component="BehaviorMonitor",
                                    level="ERROR",
                                    message=f"Invalid value for {key}: {value}. Must be a positive number."
                                )
                                return False
                        elif key.endswith("_enabled") or key.startswith("enable_"):
                            if not isinstance(value, bool):
                                await self.behavior_logger.log_event(
                                    event_type="config_error",
                                    component="BehaviorMonitor",
                                    level="ERROR",
                                    message=f"Invalid value for {key}: {value}. Must be a boolean."
                                )
                                return False
                        elif key.endswith("_path"):
                            if not isinstance(value, str):
                                await self.behavior_logger.log_event(
                                    event_type="config_error",
                                    component="BehaviorMonitor",
                                    level="ERROR",
                                    message=f"Invalid value for {key}: {value}. Must be a string."
                                )
                                return False
                        elif key.endswith("_sensitivity"):
                            if value not in ["low", "medium", "high"]:
                                await self.behavior_logger.log_event(
                                    event_type="config_error",
                                    component="BehaviorMonitor",
                                    level="ERROR",
                                    message=f"Invalid value for {key}: {value}. Must be 'low', 'medium', or 'high'."
                                )
                                return False
                        elif key.endswith("_level"):
                            if value not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                                await self.behavior_logger.log_event(
                                    event_type="config_error",
                                    component="BehaviorMonitor",
                                    level="ERROR",
                                    message=f"Invalid value for {key}: {value}. Must be a valid log level."
                                )
                                return False
                        
                        # Update the configuration
                        self._behavior_config[key] = value
                        
                        # Apply specific configuration changes
                        if key == "log_file_path" and hasattr(self.behavior_logger, "set_log_file_path"):
                            if isinstance(value, str):
                                self.behavior_logger.set_log_file_path(value)
                        elif key == "log_level" and hasattr(self.behavior_logger, "set_log_level"):
                            if isinstance(value, str):
                                self.behavior_logger.set_log_level(value)
                        elif key == "enable_detailed_logging" and hasattr(self.behavior_logger, "set_detailed_logging"):
                            if isinstance(value, bool):
                                self.behavior_logger.set_detailed_logging(value)
                        elif key == "max_log_size" and hasattr(self.behavior_logger, "set_max_log_size"):
                            if isinstance(value, int):
                                self.behavior_logger.set_max_log_size(value)
                        elif key == "log_backup_count" and hasattr(self.behavior_logger, "set_log_backup_count"):
                            if isinstance(value, int):
                                self.behavior_logger.set_log_backup_count(value)
                        elif key == "enable_log_rotation" and hasattr(self.behavior_logger, "set_log_rotation"):
                            if isinstance(value, bool):
                                self.behavior_logger.set_log_rotation(value)
                        elif key == "enable_real_time_monitoring":
                            # Restart monitoring task if setting changed
                            if self._monitoring_task:
                                self._monitoring_task.cancel()
                                try:
                                    await self._monitoring_task
                                except asyncio.CancelledError:
                                    pass
                            
                            if value:
                                self._monitoring_task = asyncio.create_task(self._monitor_agents_behavior())
                    else:
                        await self.behavior_logger.log_event(
                            event_type="config_error",
                            component="BehaviorMonitor",
                            level="ERROR",
                            message=f"Unknown configuration key: {key}"
                        )
                        return False
                
                # Log the configuration update
                await self.behavior_logger.log_event(
                    event_type="config_update",
                    component="BehaviorMonitor",
                    level="INFO",
                    message=f"Configuration updated with keys: {list(config_updates.keys())}"
                )
                
                return True
        except Exception as e:
            await self.behavior_logger.log_event(
                event_type="config_error",
                component="BehaviorMonitor",
                level="ERROR",
                message=f"Configuration update error: {str(e)}"
            )
            return False

    async def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current behavior monitoring configuration.

        Returns:
            Dict[str, Any]: Current configuration
        """
        async with self._config_lock:
            return self._behavior_config.copy()

    async def reset_configuration(self) -> bool:
        """
        Reset the behavior monitoring configuration to default values.

        Returns:
            bool: True if configuration was reset successfully, False otherwise
        """
        # Store current configuration for rollback if needed
        old_config = self._behavior_config.copy()
        
        try:
            async with self._config_lock:
                # Reset to default configuration
                self._behavior_config = {
                    # General monitoring settings
                    "enable_real_time_monitoring": True,
                    "monitoring_interval": 5.0,  # seconds
                    "enable_adaptive_learning": True,
                    "max_history_size": 1000,
                    
                    # Threshold settings
                    "anomaly_threshold": 0.7,
                    "baseline_threshold": 0.5,
                    "risk_threshold": 0.6,
                    "correlation_threshold": 0.8,
                    
                    # Anomaly detection settings
                    "enable_statistical_anomaly_detection": True,
                    "enable_ml_anomaly_detection": True,
                    "enable_rule_based_anomaly_detection": True,
                    "anomaly_detection_sensitivity": "medium",  # low, medium, high
                    
                    # Pattern recognition settings
                    "enable_sequence_pattern_detection": True,
                    "enable_frequency_pattern_detection": True,
                    "enable_trend_pattern_detection": True,
                    "enable_correlation_pattern_detection": True,
                    "pattern_detection_sensitivity": "medium",  # low, medium, high
                    
                    # Baseline settings
                    "baseline_update_interval": 3600.0,  # seconds (1 hour)
                    "baseline_adaptation_rate": 0.1,  # 0.0 to 1.0
                    "enable_individual_baselines": True,
                    "enable_group_baselines": True,
                    
                    # Risk assessment settings
                    "enable_resource_risk_assessment": True,
                    "enable_performance_risk_assessment": True,
                    "enable_behavior_risk_assessment": True,
                    "enable_anomaly_risk_assessment": True,
                    "enable_pattern_risk_assessment": True,
                    "enable_baseline_risk_assessment": True,
                    "enable_profile_risk_assessment": True,
                    "risk_assessment_sensitivity": "medium",  # low, medium, high
                    
                    # Correlation settings
                    "enable_temporal_correlation": True,
                    "enable_behavioral_correlation": True,
                    "enable_anomaly_correlation": True,
                    "enable_pattern_correlation": True,
                    "correlation_analysis_window": 300.0,  # seconds (5 minutes)
                    
                    # Logging settings
                    "log_file_path": "logs/behavior_monitor.log",
                    "enable_detailed_logging": True,
                    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                    "max_log_size": 10485760,  # 10MB in bytes
                    "log_backup_count": 5,
                    "enable_log_rotation": True,
                    
                    # Recovery settings
                    "enable_auto_recovery": True,
                    "recovery_attempts": 3,
                    "recovery_interval": 60.0,  # seconds
                    "enable_circuit_breaker": True,
                    "circuit_breaker_threshold": 5,  # number of failures
                    "circuit_breaker_timeout": 300.0,  # seconds (5 minutes)
                    
                    # Performance settings
                    "enable_performance_monitoring": True,
                    "performance_metrics_interval": 60.0,  # seconds
                    "enable_memory_usage_monitoring": True,
                    "enable_cpu_usage_monitoring": True,
                    "enable_disk_usage_monitoring": True,
                    "enable_network_usage_monitoring": True,
                    
                    # Security settings
                    "enable_security_checks": True,
                    "security_check_interval": 30.0,  # seconds
                    "enable_data_encryption": True,
                    "enable_access_control": True,
                    "enable_audit_trail": True
                }
                
                # Log the configuration reset
                await self.behavior_logger.log_event(
                    event_type="config_reset",
                    component="BehaviorMonitor",
                    level="INFO",
                    message="Configuration reset to default values"
                )
                
                return True
        except Exception as e:
            # Restore old configuration if reset failed
            self._behavior_config = old_config
            await self.behavior_logger.log_event(
                event_type="config_error",
                component="BehaviorMonitor",
                level="ERROR",
                message=f"Configuration reset error: {str(e)}"
            )
            return False

    async def update_behavior_config(self, config: Dict[str, Any]) -> bool:
        """
        Update behavior monitoring configuration.
        
        Args:
            config: New configuration
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Thread-safe access to configuration
            async with self._config_lock:
                # Update configuration
                self._behavior_config.update(config)
                
                # Restart monitoring task if real-time monitoring setting changed
                if "enable_real_time_monitoring" in config:
                    if self._monitoring_task:
                        self._monitoring_task.cancel()
                        try:
                            await self._monitoring_task
                        except asyncio.CancelledError:
                            pass
                    
                    if config["enable_real_time_monitoring"]:
                        self._monitoring_task = asyncio.create_task(self._monitor_agents_behavior())
            
            logger.info("Behavior monitoring configuration updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update behavior monitoring configuration: {e}")
            return False
    
    async def export_behavior_data(self, agent_id: Optional[str] = None, format: str = "json") -> str:
        """
        Export behavior data.
        
        Args:
            agent_id: Optional agent ID to export data for
            format: Export format (json, csv)
            
        Returns:
            Exported behavior data as a string
        """
        if not self._initialized:
            await self.initialize()
            
        # Thread-safe access to all data structures
        async with self._behavior_data_lock, self._risk_history_lock, self._profiles_lock, self._config_lock:
            if agent_id:
                # Export data for specific agent
                behavior_data = self._agent_behavior_data.get(agent_id, [])
                risk_history = self._agent_risk_history.get(agent_id, [])
                profile = self._agent_behavior_profiles.get(agent_id)
                
                export_data = {
                    "agent_id": agent_id,
                    "behavior_data": [data.__dict__ for data in behavior_data],
                    "risk_history": [risk.__dict__ for risk in risk_history],
                    "profile": profile.__dict__ if profile else None
                }
            else:
                # Export data for all agents
                export_data = {
                    "agents": {},
                    "config": self._behavior_config
                }
                
                for aid in self._agent_behavior_data:
                    export_data["agents"][aid] = {
                        "behavior_data": [data.__dict__ for data in self._agent_behavior_data[aid]],
                        "risk_history": [risk.__dict__ for risk in self._agent_risk_history[aid]],
                        "profile": self._agent_behavior_profiles[aid].__dict__ if aid in self._agent_behavior_profiles else None
                    }
            
            if format.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
