"""
Advanced threat protection and intrusion detection systems.
Provides real-time threat monitoring, detection, and response capabilities.
"""

import asyncio
import json
import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from ipaddress import ip_address, ip_network
import hashlib

try:
    import aioredis
    AIOREDIS_AVAILABLE = True
except (ImportError, TypeError):
    # Handle both ImportError and TypeError from aioredis compatibility issues
    aioredis = None
    AIOREDIS_AVAILABLE = False
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AttackType(Enum):
    """Types of detected attacks."""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    DIRECTORY_TRAVERSAL = "directory_traversal"
    COMMAND_INJECTION = "command_injection"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    MALICIOUS_PAYLOAD = "malicious_payload"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


@dataclass
class ThreatEvent:
    """Represents a detected security threat."""
    id: str
    timestamp: datetime
    source_ip: str
    user_agent: str
    attack_type: AttackType
    threat_level: ThreatLevel
    endpoint: str
    payload: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    false_positive: bool = False


@dataclass
class AttackPattern:
    """Defines patterns for attack detection."""
    name: str
    attack_type: AttackType
    threat_level: ThreatLevel
    patterns: List[str]
    description: str
    remediation: str


class ThreatDetectionEngine:
    """Core threat detection engine with pattern matching."""
    
    def __init__(self):
        self.attack_patterns = self._load_attack_patterns()
        self.ip_reputation_cache: Dict[str, Tuple[bool, datetime]] = {}
        self.behavioral_baselines: Dict[str, Dict[str, float]] = {}
        
    def _load_attack_patterns(self) -> List[AttackPattern]:
        """Load predefined attack patterns."""
        return [
            # SQL Injection Patterns
            AttackPattern(
                name="SQL Injection - Union Based",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                patterns=[
                    r"(?i)union\s+select",
                    r"(?i)union\s+all\s+select",
                    r"(?i)\'\s+union\s+select",
                    r"(?i)\"\s+union\s+select"
                ],
                description="Union-based SQL injection attempt",
                remediation="Use parameterized queries"
            ),
            AttackPattern(
                name="SQL Injection - Boolean Based",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                patterns=[
                    r"(?i)\'\s+or\s+\'\d+\'\s*=\s*\'\d+",
                    r"(?i)\'\s+or\s+\d+\s*=\s*\d+",
                    r"(?i)\'\s+and\s+\'\d+\'\s*=\s*\'\d+",
                    r"(?i)admin\'\s*--",
                    r"(?i)\'\s+or\s+1\s*=\s*1"
                ],
                description="Boolean-based SQL injection attempt",
                remediation="Implement input validation and parameterized queries"
            ),
            
            # XSS Patterns
            AttackPattern(
                name="Cross-Site Scripting",
                attack_type=AttackType.XSS_ATTEMPT,
                threat_level=ThreatLevel.HIGH,
                patterns=[
                    r"(?i)<script[^>]*>.*?</script>",
                    r"(?i)<script[^>]*>",
                    r"(?i)javascript:",
                    r"(?i)on\w+\s*=",
                    r"(?i)<iframe[^>]*src\s*=",
                    r"(?i)<img[^>]*onerror\s*=",
                    r"(?i)<svg[^>]*onload\s*="
                ],
                description="Cross-site scripting attempt",
                remediation="Implement output encoding and CSP headers"
            ),
            
            # Directory Traversal
            AttackPattern(
                name="Directory Traversal",
                attack_type=AttackType.DIRECTORY_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                patterns=[
                    r"\.\.\/",
                    r"\.\.\\",
                    r"%2e%2e%2f",
                    r"%2e%2e%5c",
                    r"..%2f",
                    r"..%5c"
                ],
                description="Directory traversal attempt",
                remediation="Validate and sanitize file paths"
            ),
            
            # Command Injection
            AttackPattern(
                name="Command Injection",
                attack_type=AttackType.COMMAND_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                patterns=[
                    r"(?i);\s*(ls|dir|cat|type|whoami|id|pwd)",
                    r"(?i)\|\s*(ls|dir|cat|type|whoami|id|pwd)",
                    r"(?i)&&\s*(ls|dir|cat|type|whoami|id|pwd)",
                    r"(?i)`.*`",
                    r"(?i)\$\(.*\)"
                ],
                description="Command injection attempt",
                remediation="Avoid system calls with user input"
            ),
            
            # Suspicious User Agents
            AttackPattern(
                name="Malicious User Agent",
                attack_type=AttackType.SUSPICIOUS_USER_AGENT,
                threat_level=ThreatLevel.MEDIUM,
                patterns=[
                    r"(?i)sqlmap",
                    r"(?i)nikto",
                    r"(?i)nessus",
                    r"(?i)openvas",
                    r"(?i)w3af",
                    r"(?i)burp",
                    r"(?i)nmap",
                    r"(?i)masscan"
                ],
                description="Suspicious security tool user agent",
                remediation="Block or monitor suspicious user agents"
            )
        ]
    
    def detect_threats(self, request_data: Dict[str, Any]) -> List[ThreatEvent]:
        """Detect threats in request data."""
        threats = []
        
        # Extract request components
        url = request_data.get('url', '')
        query_params = request_data.get('query_params', {})
        post_data = request_data.get('post_data', {})
        headers = request_data.get('headers', {})
        user_agent = headers.get('user-agent', '')
        
        # Combine all text data for pattern matching
        text_data = [
            url,
            str(query_params),
            str(post_data),
            user_agent
        ]
        
        # Check against attack patterns
        for pattern in self.attack_patterns:
            for regex in pattern.patterns:
                for text in text_data:
                    if re.search(regex, text):
                        threat = ThreatEvent(
                            id=self._generate_threat_id(request_data, pattern.attack_type),
                            timestamp=datetime.utcnow(),
                            source_ip=request_data.get('source_ip', ''),
                            user_agent=user_agent,
                            attack_type=pattern.attack_type,
                            threat_level=pattern.threat_level,
                            endpoint=request_data.get('endpoint', ''),
                            payload=text,
                            user_id=request_data.get('user_id'),
                            tenant_id=request_data.get('tenant_id'),
                            session_id=request_data.get('session_id'),
                            additional_data={
                                'pattern_name': pattern.name,
                                'matched_regex': regex,
                                'description': pattern.description,
                                'remediation': pattern.remediation
                            }
                        )
                        threats.append(threat)
        
        return threats
    
    def _generate_threat_id(self, request_data: Dict[str, Any], attack_type: AttackType) -> str:
        """Generate unique threat ID."""
        data_str = f"{request_data.get('source_ip', '')}{attack_type.value}{time.time()}"
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def check_ip_reputation(self, ip: str) -> Tuple[bool, str]:
        """Check IP reputation against known threat feeds."""
        # Check cache first
        if ip in self.ip_reputation_cache:
            is_malicious, cached_time = self.ip_reputation_cache[ip]
            if datetime.utcnow() - cached_time < timedelta(hours=1):
                return is_malicious, "cached"
        
        # Known malicious IP ranges (example - in production, use threat feeds)
        malicious_ranges = [
            "10.0.0.0/8",  # Example - replace with actual threat intelligence
            "192.168.0.0/16"  # Example
        ]
        
        try:
            ip_obj = ip_address(ip)
            for range_str in malicious_ranges:
                if ip_obj in ip_network(range_str):
                    self.ip_reputation_cache[ip] = (True, datetime.utcnow())
                    return True, "threat_feed"
        except ValueError:
            pass
        
        # Cache as clean
        self.ip_reputation_cache[ip] = (False, datetime.utcnow())
        return False, "clean"
    
    def analyze_behavioral_anomaly(
        self, 
        user_id: str, 
        current_behavior: Dict[str, float]
    ) -> Optional[ThreatEvent]:
        """Analyze user behavior for anomalies."""
        if user_id not in self.behavioral_baselines:
            # Initialize baseline
            self.behavioral_baselines[user_id] = current_behavior.copy()
            return None
        
        baseline = self.behavioral_baselines[user_id]
        anomaly_score = 0.0
        anomalies = []
        
        for metric, current_value in current_behavior.items():
            if metric in baseline:
                baseline_value = baseline[metric]
                if baseline_value > 0:
                    deviation = abs(current_value - baseline_value) / baseline_value
                    if deviation > 2.0:  # More than 200% deviation
                        anomaly_score += deviation
                        anomalies.append(f"{metric}: {current_value} vs baseline {baseline_value}")
        
        # Update baseline with exponential moving average
        alpha = 0.1
        for metric, current_value in current_behavior.items():
            if metric in baseline:
                baseline[metric] = alpha * current_value + (1 - alpha) * baseline[metric]
            else:
                baseline[metric] = current_value
        
        if anomaly_score > 3.0:  # Threshold for anomaly
            return ThreatEvent(
                id=f"anomaly_{user_id}_{int(time.time())}",
                timestamp=datetime.utcnow(),
                source_ip="",
                user_agent="",
                attack_type=AttackType.ANOMALOUS_BEHAVIOR,
                threat_level=ThreatLevel.MEDIUM,
                endpoint="",
                user_id=user_id,
                additional_data={
                    'anomaly_score': anomaly_score,
                    'anomalies': anomalies,
                    'current_behavior': current_behavior,
                    'baseline': baseline.copy()
                }
            )
        
        return None


class IntrusionDetectionSystem:
    """Real-time intrusion detection and response system."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.detection_engine = ThreatDetectionEngine()
        self.threat_events: deque = deque(maxlen=10000)
        self.blocked_ips: Set[str] = set()
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alert_callbacks: List[Callable] = []
        
    async def analyze_request(self, request: Request) -> List[ThreatEvent]:
        """Analyze incoming request for threats."""
        # Extract request data
        request_data = await self._extract_request_data(request)
        
        # Detect threats using pattern matching
        threats = self.detection_engine.detect_threats(request_data)
        
        # Check IP reputation
        source_ip = request_data['source_ip']
        is_malicious, source = await self.detection_engine.check_ip_reputation(source_ip)
        if is_malicious:
            threat = ThreatEvent(
                id=f"malicious_ip_{source_ip}_{int(time.time())}",
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_agent=request_data.get('user_agent', ''),
                attack_type=AttackType.MALICIOUS_PAYLOAD,
                threat_level=ThreatLevel.HIGH,
                endpoint=request_data['endpoint'],
                additional_data={'reputation_source': source}
            )
            threats.append(threat)
        
        # Check for rate limit abuse
        rate_threat = await self._check_rate_limits(request_data)
        if rate_threat:
            threats.append(rate_threat)
        
        # Behavioral analysis for authenticated users
        if request_data.get('user_id'):
            behavior_data = await self._extract_user_behavior(request_data)
            behavioral_threat = self.detection_engine.analyze_behavioral_anomaly(
                request_data['user_id'], 
                behavior_data
            )
            if behavioral_threat:
                threats.append(behavioral_threat)
        
        # Process detected threats
        for threat in threats:
            await self._process_threat(threat)
        
        return threats
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract relevant data from request for analysis."""
        # Get client IP (handle proxies)
        source_ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
        if not source_ip:
            source_ip = request.headers.get('x-real-ip', '')
        if not source_ip:
            source_ip = request.client.host if request.client else ''
        
        # Extract query parameters
        query_params = dict(request.query_params)
        
        # Extract POST data if available
        post_data = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.headers.get('content-type', '').startswith('application/json'):
                    post_data = await request.json()
                else:
                    form_data = await request.form()
                    post_data = dict(form_data)
            except Exception:
                pass
        
        return {
            'url': str(request.url),
            'endpoint': request.url.path,
            'method': request.method,
            'source_ip': source_ip,
            'user_agent': request.headers.get('user-agent', ''),
            'headers': dict(request.headers),
            'query_params': query_params,
            'post_data': post_data,
            'user_id': getattr(request.state, 'user_id', None),
            'tenant_id': getattr(request.state, 'tenant_id', None),
            'session_id': getattr(request.state, 'session_id', None)
        }
    
    async def _check_rate_limits(self, request_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Check for rate limit abuse."""
        source_ip = request_data['source_ip']
        endpoint = request_data['endpoint']
        
        # Track requests per IP per endpoint
        key = f"{source_ip}:{endpoint}"
        now = time.time()
        
        # Clean old entries (older than 1 minute)
        while self.rate_limiters[key] and now - self.rate_limiters[key][0] > 60:
            self.rate_limiters[key].popleft()
        
        # Add current request
        self.rate_limiters[key].append(now)
        
        # Check if rate limit exceeded (more than 100 requests per minute)
        if len(self.rate_limiters[key]) > 100:
            return ThreatEvent(
                id=f"rate_abuse_{source_ip}_{int(now)}",
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_agent=request_data.get('user_agent', ''),
                attack_type=AttackType.RATE_LIMIT_ABUSE,
                threat_level=ThreatLevel.MEDIUM,
                endpoint=endpoint,
                additional_data={
                    'requests_per_minute': len(self.rate_limiters[key]),
                    'threshold': 100
                }
            )
        
        return None
    
    async def _extract_user_behavior(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract behavioral metrics for user."""
        user_id = request_data['user_id']
        
        # Get recent activity from Redis
        activity_key = f"user_activity:{user_id}"
        activity_data = await self.redis.hgetall(activity_key)
        
        # Calculate behavioral metrics
        behavior = {
            'requests_per_hour': float(activity_data.get('requests_per_hour', 0)),
            'unique_endpoints': float(activity_data.get('unique_endpoints', 0)),
            'error_rate': float(activity_data.get('error_rate', 0)),
            'session_duration': float(activity_data.get('session_duration', 0)),
            'data_volume': float(activity_data.get('data_volume', 0))
        }
        
        return behavior
    
    async def _process_threat(self, threat: ThreatEvent):
        """Process detected threat event."""
        # Store threat event
        self.threat_events.append(threat)
        
        # Store in Redis for persistence
        threat_key = f"threat:{threat.id}"
        threat_data = {
            'timestamp': threat.timestamp.isoformat(),
            'source_ip': threat.source_ip,
            'attack_type': threat.attack_type.value,
            'threat_level': threat.threat_level.value,
            'endpoint': threat.endpoint,
            'payload': threat.payload or '',
            'user_id': threat.user_id or '',
            'tenant_id': threat.tenant_id or '',
            'additional_data': json.dumps(threat.additional_data)
        }
        
        await self.redis.hset(threat_key, mapping=threat_data)
        await self.redis.expire(threat_key, 86400 * 30)  # Keep for 30 days
        
        # Auto-blocking for critical threats
        if threat.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            await self._auto_block_threat(threat)
        
        # Send alerts
        await self._send_threat_alert(threat)
        
        logger.warning(f"Threat detected: {threat.attack_type.value} from {threat.source_ip}")
    
    async def _auto_block_threat(self, threat: ThreatEvent):
        """Automatically block high-severity threats."""
        if threat.source_ip and threat.source_ip not in self.blocked_ips:
            self.blocked_ips.add(threat.source_ip)
            
            # Store in Redis
            block_key = f"blocked_ip:{threat.source_ip}"
            await self.redis.setex(
                block_key, 
                3600,  # Block for 1 hour
                json.dumps({
                    'blocked_at': datetime.utcnow().isoformat(),
                    'reason': threat.attack_type.value,
                    'threat_id': threat.id
                })
            )
            
            threat.blocked = True
            logger.warning(f"Auto-blocked IP {threat.source_ip} due to {threat.attack_type.value}")
    
    async def _send_threat_alert(self, threat: ThreatEvent):
        """Send threat alerts to configured channels."""
        for callback in self.alert_callbacks:
            try:
                await callback(threat)
            except Exception as e:
                logger.error(f"Error sending threat alert: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for threat alerts."""
        self.alert_callbacks.append(callback)
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if ip in self.blocked_ips:
            return True
        
        block_key = f"blocked_ip:{ip}"
        return await self.redis.exists(block_key)
    
    async def unblock_ip(self, ip: str):
        """Manually unblock an IP address."""
        self.blocked_ips.discard(ip)
        block_key = f"blocked_ip:{ip}"
        await self.redis.delete(block_key)
        logger.info(f"Unblocked IP {ip}")
    
    async def get_threat_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat statistics for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_threats = [
            threat for threat in self.threat_events 
            if threat.timestamp > cutoff_time
        ]
        
        # Count by attack type
        attack_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for threat in recent_threats:
            attack_counts[threat.attack_type.value] += 1
            severity_counts[threat.threat_level.value] += 1
        
        # Top attacking IPs
        ip_counts = defaultdict(int)
        for threat in recent_threats:
            ip_counts[threat.source_ip] += 1
        
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_threats': len(recent_threats),
            'attack_types': dict(attack_counts),
            'severity_levels': dict(severity_counts),
            'top_attacking_ips': top_ips,
            'blocked_ips_count': len(self.blocked_ips),
            'time_period_hours': hours
        }


class ThreatProtectionSystem:
    """Main threat protection system coordinator."""
    
    def __init__(self, redis_client, database_session: AsyncSession):
        self.redis = redis_client
        self.database_session = database_session
        self.ids = IntrusionDetectionSystem(redis_client)
        self.setup_alert_callbacks()
        
    def setup_alert_callbacks(self):
        """Setup threat alert callbacks."""
        self.ids.add_alert_callback(self._log_threat_alert)
        self.ids.add_alert_callback(self._store_threat_in_database)
        
    async def _log_threat_alert(self, threat: ThreatEvent):
        """Log threat alert."""
        logger.critical(
            f"SECURITY ALERT: {threat.attack_type.value} detected",
            extra={
                'threat_id': threat.id,
                'source_ip': threat.source_ip,
                'threat_level': threat.threat_level.value,
                'endpoint': threat.endpoint,
                'user_id': threat.user_id,
                'tenant_id': threat.tenant_id
            }
        )
    
    async def _store_threat_in_database(self, threat: ThreatEvent):
        """Store threat event in database for long-term analysis."""
        # This would store in a security_events table
        # Implementation depends on your database schema
        pass
    
    async def middleware_handler(self, request: Request, call_next):
        """Middleware handler for threat detection."""
        # Check if IP is blocked
        source_ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
        if not source_ip:
            source_ip = request.client.host if request.client else ''
        
        if await self.ids.is_ip_blocked(source_ip):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Analyze request for threats
        threats = await self.ids.analyze_request(request)
        
        # Block request if critical threats detected
        critical_threats = [t for t in threats if t.threat_level == ThreatLevel.CRITICAL]
        if critical_threats:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Malicious request detected")
        
        # Continue with request
        response = await call_next(request)
        return response
    
    async def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard."""
        stats = await self.ids.get_threat_statistics()
        
        return {
            'threat_statistics': stats,
            'blocked_ips': list(self.ids.blocked_ips),
            'recent_threats': [
                {
                    'id': threat.id,
                    'timestamp': threat.timestamp.isoformat(),
                    'source_ip': threat.source_ip,
                    'attack_type': threat.attack_type.value,
                    'threat_level': threat.threat_level.value,
                    'endpoint': threat.endpoint,
                    'blocked': threat.blocked
                }
                for threat in list(self.ids.threat_events)[-50:]  # Last 50 threats
            ]
        }