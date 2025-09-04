"""
Security Analyzer for HTTP Request Threat Detection

This module provides comprehensive security analysis capabilities for HTTP requests,
including attack pattern detection, threat intelligence, and security assessment.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from fastapi import Request
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SecurityAssessment:
    """Security assessment result for an HTTP request."""
    threat_level: str  # "none", "low", "medium", "high", "critical"
    detected_patterns: List[str]
    client_reputation: str  # "trusted", "unknown", "suspicious", "malicious"
    recommended_action: str  # "allow", "monitor", "rate_limit", "block"
    confidence_score: float
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    client_ip_hash: Optional[str] = None
    attack_categories: List[str] = field(default_factory=list)
    risk_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatIntelligence:
    """Threat intelligence data for tracking malicious activity."""
    ip_hash: str
    threat_score: float
    attack_count: int
    last_seen: datetime
    attack_types: Set[str] = field(default_factory=set)
    first_seen: datetime = field(default_factory=datetime.now)
    blocked: bool = False
    notes: str = ""


class SecurityAnalyzer:
    """
    Comprehensive security analyzer for HTTP request threat detection.
    
    This class provides advanced security analysis capabilities including:
    - Attack pattern detection (SQL injection, XSS, CSRF, etc.)
    - Behavioral analysis and anomaly detection
    - Threat intelligence storage and updates
    - Client reputation tracking
    - Risk scoring and assessment
    """
    
    def __init__(self, threat_intelligence_file: Optional[str] = None):
        """
        Initialize the security analyzer.
        
        Args:
            threat_intelligence_file: Path to threat intelligence storage file
        """
        self.threat_intelligence_file = threat_intelligence_file or "data/threat_intelligence.json"
        self.threat_intelligence: Dict[str, ThreatIntelligence] = {}
        self.attack_patterns = self._load_attack_patterns()
        self.suspicious_ips: Set[str] = set()
        self._load_threat_intelligence()
        
        # Rate limiting for analysis to prevent DoS
        self.analysis_cache: Dict[str, Tuple[SecurityAssessment, float]] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _load_attack_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load and compile attack detection patterns."""
        patterns = {
            "sql_injection": [
                re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
                re.compile(r"(\bselect\b.*\bfrom\b)", re.IGNORECASE),
                re.compile(r"(\binsert\b.*\binto\b)", re.IGNORECASE),
                re.compile(r"(\bdelete\b.*\bfrom\b)", re.IGNORECASE),
                re.compile(r"(\bdrop\b.*\btable\b)", re.IGNORECASE),
                re.compile(r"(\bupdate\b.*\bset\b)", re.IGNORECASE),
                re.compile(r"(\bor\b.*1\s*=\s*1)", re.IGNORECASE),
                re.compile(r"(\band\b.*1\s*=\s*1)", re.IGNORECASE),
                re.compile(r"'.*(\bor\b|\band\b).*'", re.IGNORECASE),
                re.compile(r";\s*(drop|delete|insert|update)", re.IGNORECASE),
            ],
            "xss": [
                re.compile(r"<script[^>]*>", re.IGNORECASE),
                re.compile(r"</script>", re.IGNORECASE),
                re.compile(r"javascript:", re.IGNORECASE),
                re.compile(r"on\w+\s*=", re.IGNORECASE),
                re.compile(r"<iframe[^>]*>", re.IGNORECASE),
                re.compile(r"<object[^>]*>", re.IGNORECASE),
                re.compile(r"<embed[^>]*>", re.IGNORECASE),
                re.compile(r"<link[^>]*>", re.IGNORECASE),
                re.compile(r"<meta[^>]*>", re.IGNORECASE),
                re.compile(r"vbscript:", re.IGNORECASE),
            ],
            "path_traversal": [
                re.compile(r"\.\.\/"),
                re.compile(r"\.\.\\"),
                re.compile(r"%2e%2e%2f", re.IGNORECASE),
                re.compile(r"%2e%2e%5c", re.IGNORECASE),
                re.compile(r"\.\.%2f", re.IGNORECASE),
                re.compile(r"\.\.%5c", re.IGNORECASE),
                re.compile(r"%2e%2e/", re.IGNORECASE),
                re.compile(r"%2e%2e\\", re.IGNORECASE),
            ],
            "command_injection": [
                re.compile(r";\s*(cat|ls|pwd|whoami|id|uname)", re.IGNORECASE),
                re.compile(r"\|\s*(cat|ls|pwd|whoami|id|uname)", re.IGNORECASE),
                re.compile(r"&&\s*(cat|ls|pwd|whoami|id|uname)", re.IGNORECASE),
                re.compile(r"`.*`", re.IGNORECASE),
                re.compile(r"\$\(.*\)", re.IGNORECASE),
                re.compile(r"nc\s+-", re.IGNORECASE),
                re.compile(r"wget\s+", re.IGNORECASE),
                re.compile(r"curl\s+", re.IGNORECASE),
            ],
            "ldap_injection": [
                re.compile(r"\(\|", re.IGNORECASE),
                re.compile(r"\(&", re.IGNORECASE),
                re.compile(r"\(!", re.IGNORECASE),
                re.compile(r"\*\)", re.IGNORECASE),
                re.compile(r"\)\(", re.IGNORECASE),
            ],
            "xml_injection": [
                re.compile(r"<\?xml", re.IGNORECASE),
                re.compile(r"<!DOCTYPE", re.IGNORECASE),
                re.compile(r"<!ENTITY", re.IGNORECASE),
                re.compile(r"SYSTEM\s+", re.IGNORECASE),
                re.compile(r"PUBLIC\s+", re.IGNORECASE),
            ],
            "csrf": [
                re.compile(r"<form[^>]*action\s*=", re.IGNORECASE),
                re.compile(r"<input[^>]*type\s*=\s*['\"]hidden['\"]", re.IGNORECASE),
            ],
            "header_injection": [
                re.compile(r"\r\n", re.IGNORECASE),
                re.compile(r"%0d%0a", re.IGNORECASE),
                re.compile(r"%0a", re.IGNORECASE),
                re.compile(r"%0d", re.IGNORECASE),
                re.compile(r"\n", re.IGNORECASE),
                re.compile(r"\r", re.IGNORECASE),
            ],
            "nosql_injection": [
                re.compile(r"\$where", re.IGNORECASE),
                re.compile(r"\$ne", re.IGNORECASE),
                re.compile(r"\$gt", re.IGNORECASE),
                re.compile(r"\$lt", re.IGNORECASE),
                re.compile(r"\$regex", re.IGNORECASE),
                re.compile(r"\$or", re.IGNORECASE),
                re.compile(r"\$and", re.IGNORECASE),
            ]
        }
        
        logger.info(f"Loaded {sum(len(p) for p in patterns.values())} attack patterns across {len(patterns)} categories")
        return patterns
    
    def _load_threat_intelligence(self) -> None:
        """Load threat intelligence data from storage."""
        try:
            # Ensure directory exists
            Path(self.threat_intelligence_file).parent.mkdir(parents=True, exist_ok=True)
            
            if Path(self.threat_intelligence_file).exists():
                with open(self.threat_intelligence_file, 'r') as f:
                    data = json.load(f)
                    
                for ip_hash, intel_data in data.items():
                    self.threat_intelligence[ip_hash] = ThreatIntelligence(
                        ip_hash=ip_hash,
                        threat_score=intel_data.get('threat_score', 0.0),
                        attack_count=intel_data.get('attack_count', 0),
                        last_seen=datetime.fromisoformat(intel_data.get('last_seen', datetime.now().isoformat())),
                        attack_types=set(intel_data.get('attack_types', [])),
                        first_seen=datetime.fromisoformat(intel_data.get('first_seen', datetime.now().isoformat())),
                        blocked=intel_data.get('blocked', False),
                        notes=intel_data.get('notes', '')
                    )
                    
                logger.info(f"Loaded threat intelligence for {len(self.threat_intelligence)} IP addresses")
            else:
                logger.info("No existing threat intelligence file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading threat intelligence: {e}")
            self.threat_intelligence = {}
    
    def _save_threat_intelligence(self) -> None:
        """Save threat intelligence data to storage."""
        try:
            # Ensure directory exists
            Path(self.threat_intelligence_file).parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for ip_hash, intel in self.threat_intelligence.items():
                data[ip_hash] = {
                    'threat_score': intel.threat_score,
                    'attack_count': intel.attack_count,
                    'last_seen': intel.last_seen.isoformat(),
                    'attack_types': list(intel.attack_types),
                    'first_seen': intel.first_seen.isoformat(),
                    'blocked': intel.blocked,
                    'notes': intel.notes
                }
            
            with open(self.threat_intelligence_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved threat intelligence for {len(data)} IP addresses")
            
        except Exception as e:
            logger.error(f"Error saving threat intelligence: {e}")
    
    def _hash_ip(self, ip: str) -> str:
        """Create a hash of the IP address for privacy."""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Try various headers for real IP
        headers_to_check = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip",
            "true-client-ip"
        ]
        
        for header in headers_to_check:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip and ip != "unknown":
                    return ip
        
        # Fallback to request.client.host
        if hasattr(request, 'client') and request.client and hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    async def analyze_request(self, request: Request) -> SecurityAssessment:
        """
        Perform comprehensive security analysis of an HTTP request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            SecurityAssessment with detailed analysis results
        """
        try:
            client_ip = self._get_client_ip(request)
            client_ip_hash = self._hash_ip(client_ip)
            
            # Check cache first
            cache_key = f"{client_ip_hash}:{request.method}:{str(request.url.path)}"
            current_time = time.time()
            
            if cache_key in self.analysis_cache:
                cached_assessment, cache_time = self.analysis_cache[cache_key]
                if current_time - cache_time < self.cache_ttl:
                    return cached_assessment
            
            # Perform analysis
            detected_patterns = []
            attack_categories = []
            risk_factors = {}
            confidence_score = 0.0
            
            # Analyze URL path and query parameters
            path = str(request.url.path)
            query = str(request.url.query) if request.url.query else ""
            full_url = f"{path}?{query}" if query else path
            
            # Pattern detection
            for category, patterns in self.attack_patterns.items():
                category_matches = []
                for pattern in patterns:
                    if pattern.search(full_url):
                        category_matches.append(pattern.pattern)
                        detected_patterns.append(f"{category}:{pattern.pattern[:50]}")
                
                if category_matches:
                    attack_categories.append(category)
                    risk_factors[f"{category}_matches"] = len(category_matches)
            
            # Analyze headers
            headers = dict(request.headers)
            suspicious_headers = []
            
            for header_name, header_value in headers.items():
                for category, patterns in self.attack_patterns.items():
                    for pattern in patterns:
                        if pattern.search(header_value):
                            detected_patterns.append(f"header_{category}:{header_name}")
                            suspicious_headers.append(header_name)
                            if category not in attack_categories:
                                attack_categories.append(category)
            
            if suspicious_headers:
                risk_factors["suspicious_headers"] = suspicious_headers
            
            # Behavioral analysis
            behavioral_score = await self._analyze_behavior(request, client_ip_hash)
            risk_factors["behavioral_score"] = behavioral_score
            
            # Client reputation analysis
            client_reputation = self._get_client_reputation(client_ip_hash)
            
            # Calculate threat level and confidence
            threat_level, confidence_score = self._calculate_threat_level(
                detected_patterns, attack_categories, behavioral_score, client_reputation
            )
            
            # Determine recommended action
            recommended_action = self._determine_action(threat_level, confidence_score, client_reputation)
            
            # Create assessment
            assessment = SecurityAssessment(
                threat_level=threat_level,
                detected_patterns=detected_patterns,
                client_reputation=client_reputation,
                recommended_action=recommended_action,
                confidence_score=confidence_score,
                client_ip_hash=client_ip_hash,
                attack_categories=attack_categories,
                risk_factors=risk_factors
            )
            
            # Update threat intelligence
            if threat_level in ["medium", "high", "critical"]:
                self.update_threat_intelligence(client_ip_hash, threat_level, attack_categories)
            
            # Cache the result
            self.analysis_cache[cache_key] = (assessment, current_time)
            
            # Clean old cache entries
            self._clean_cache()
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error during security analysis: {e}", exc_info=True)
            return SecurityAssessment(
                threat_level="low",
                detected_patterns=["analysis_error"],
                client_reputation="unknown",
                recommended_action="monitor",
                confidence_score=0.0,
                risk_factors={"error": str(e)}
            )
    
    async def _analyze_behavior(self, request: Request, client_ip_hash: str) -> float:
        """
        Analyze behavioral patterns for anomaly detection.
        
        Args:
            request: FastAPI Request object
            client_ip_hash: Hashed client IP
            
        Returns:
            Behavioral risk score (0.0 to 1.0)
        """
        score = 0.0
        
        try:
            # Check request frequency
            if client_ip_hash in self.threat_intelligence:
                intel = self.threat_intelligence[client_ip_hash]
                time_since_last = (datetime.now() - intel.last_seen).total_seconds()
                
                # High frequency requests are suspicious
                if time_since_last < 1:  # Less than 1 second
                    score += 0.3
                elif time_since_last < 5:  # Less than 5 seconds
                    score += 0.1
                
                # High attack count is very suspicious
                if intel.attack_count > 10:
                    score += 0.4
                elif intel.attack_count > 5:
                    score += 0.2
            
            # Analyze request characteristics
            path = str(request.url.path)
            
            # Very long URLs are suspicious
            if len(path) > 500:
                score += 0.2
            elif len(path) > 200:
                score += 0.1
            
            # Multiple encoded characters are suspicious
            encoded_chars = path.count('%')
            if encoded_chars > 10:
                score += 0.3
            elif encoded_chars > 5:
                score += 0.1
            
            # Check for unusual characters
            unusual_chars = sum(1 for c in path if ord(c) > 127)
            if unusual_chars > 0:
                score += min(0.2, unusual_chars * 0.05)
            
            # Check User-Agent
            user_agent = request.headers.get("user-agent", "").lower()
            if not user_agent:
                score += 0.2  # Missing User-Agent is suspicious
            elif any(bot in user_agent for bot in ["bot", "crawler", "spider", "scraper"]):
                score += 0.1  # Bots are slightly suspicious
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {e}")
            return 0.0
    
    def _get_client_reputation(self, client_ip_hash: str) -> str:
        """
        Get client reputation based on threat intelligence.
        
        Args:
            client_ip_hash: Hashed client IP
            
        Returns:
            Client reputation: "trusted", "unknown", "suspicious", "malicious"
        """
        if client_ip_hash not in self.threat_intelligence:
            return "unknown"
        
        intel = self.threat_intelligence[client_ip_hash]
        
        if intel.blocked:
            return "malicious"
        elif intel.threat_score > 0.8:
            return "malicious"
        elif intel.threat_score > 0.5:
            return "suspicious"
        elif intel.attack_count > 5:
            return "suspicious"
        elif intel.threat_score < 0.1 and intel.attack_count == 0:
            return "trusted"
        else:
            return "unknown"
    
    def _calculate_threat_level(
        self, 
        detected_patterns: List[str], 
        attack_categories: List[str], 
        behavioral_score: float, 
        client_reputation: str
    ) -> Tuple[str, float]:
        """
        Calculate overall threat level and confidence score.
        
        Args:
            detected_patterns: List of detected attack patterns
            attack_categories: List of attack categories found
            behavioral_score: Behavioral risk score
            client_reputation: Client reputation
            
        Returns:
            Tuple of (threat_level, confidence_score)
        """
        base_score = 0.0
        confidence = 0.0
        
        # Pattern-based scoring
        if detected_patterns:
            pattern_score = min(1.0, len(detected_patterns) * 0.2)
            base_score += pattern_score
            confidence += 0.3
        
        # Category-based scoring
        high_risk_categories = ["sql_injection", "command_injection", "xml_injection"]
        medium_risk_categories = ["xss", "path_traversal", "header_injection"]
        
        for category in attack_categories:
            if category in high_risk_categories:
                base_score += 0.4
                confidence += 0.4
            elif category in medium_risk_categories:
                base_score += 0.2
                confidence += 0.2
            else:
                base_score += 0.1
                confidence += 0.1
        
        # Behavioral scoring
        base_score += behavioral_score * 0.3
        if behavioral_score > 0:
            confidence += 0.2
        
        # Reputation scoring
        reputation_scores = {
            "malicious": 0.8,
            "suspicious": 0.4,
            "unknown": 0.0,
            "trusted": -0.2
        }
        base_score += reputation_scores.get(client_reputation, 0.0)
        confidence += 0.3 if client_reputation in ["malicious", "suspicious", "trusted"] else 0.1
        
        # Normalize scores
        base_score = max(0.0, min(1.0, base_score))
        confidence = max(0.0, min(1.0, confidence))
        
        # Determine threat level (adjusted to be less aggressive)
        if base_score >= 0.9:
            threat_level = "critical"
        elif base_score >= 0.7:
            threat_level = "high"
        elif base_score >= 0.4:
            threat_level = "medium"
        elif base_score >= 0.1:
            threat_level = "low"
        else:
            threat_level = "none"
        
        return threat_level, confidence
    
    def _determine_action(self, threat_level: str, confidence_score: float, client_reputation: str) -> str:
        """
        Determine recommended action based on threat assessment.
        
        Args:
            threat_level: Assessed threat level
            confidence_score: Confidence in the assessment
            client_reputation: Client reputation
            
        Returns:
            Recommended action: "allow", "monitor", "rate_limit", "block"
        """
        if client_reputation == "malicious" or threat_level == "critical":
            return "block"
        elif threat_level == "high" and confidence_score > 0.7:
            return "block"
        elif threat_level in ["high", "medium"] or client_reputation == "suspicious":
            return "rate_limit"
        elif threat_level == "low" or confidence_score < 0.3:
            return "monitor"
        elif threat_level == "none" and client_reputation == "trusted":
            return "allow"
        else:
            return "monitor"
    
    def detect_attack_patterns(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Detect known attack patterns in request data.
        
        Args:
            request_data: Dictionary containing request data to analyze
            
        Returns:
            List of detected attack pattern identifiers
        """
        detected = []
        
        try:
            # Combine all text data for analysis
            text_data = []
            if "path" in request_data:
                text_data.append(request_data["path"])
            if "query" in request_data:
                text_data.append(request_data["query"])
            if "headers" in request_data:
                text_data.extend(str(v) for v in request_data["headers"].values())
            if "body" in request_data:
                text_data.append(str(request_data["body"]))
            
            combined_text = " ".join(text_data)
            
            # Check each pattern category
            for category, patterns in self.attack_patterns.items():
                for i, pattern in enumerate(patterns):
                    if pattern.search(combined_text):
                        detected.append(f"{category}_{i}")
            
            return detected
            
        except Exception as e:
            logger.error(f"Error detecting attack patterns: {e}")
            return []
    
    def update_threat_intelligence(self, ip_hash: str, threat_type: str, attack_categories: List[str] = None) -> None:
        """
        Update threat intelligence data for a client.
        
        Args:
            ip_hash: Hashed IP address
            threat_type: Type of threat detected
            attack_categories: List of attack categories detected
        """
        try:
            current_time = datetime.now()
            attack_categories = attack_categories or []
            
            if ip_hash not in self.threat_intelligence:
                self.threat_intelligence[ip_hash] = ThreatIntelligence(
                    ip_hash=ip_hash,
                    threat_score=0.0,
                    attack_count=0,
                    last_seen=current_time,
                    first_seen=current_time
                )
            
            intel = self.threat_intelligence[ip_hash]
            intel.last_seen = current_time
            intel.attack_count += 1
            intel.attack_types.update(attack_categories)
            
            # Update threat score based on threat type
            threat_score_increments = {
                "critical": 0.3,
                "high": 0.2,
                "medium": 0.1,
                "low": 0.05
            }
            
            increment = threat_score_increments.get(threat_type, 0.05)
            intel.threat_score = min(1.0, intel.threat_score + increment)
            
            # Auto-block if threat score is very high
            if intel.threat_score >= 0.9 or intel.attack_count >= 20:
                intel.blocked = True
                intel.notes = f"Auto-blocked: score={intel.threat_score:.2f}, attacks={intel.attack_count}"
            
            # Periodically save threat intelligence
            if len(self.threat_intelligence) % 10 == 0:
                self._save_threat_intelligence()
                
        except Exception as e:
            logger.error(f"Error updating threat intelligence: {e}")
    
    def _clean_cache(self) -> None:
        """Clean expired entries from analysis cache."""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, (_, cache_time) in self.analysis_cache.items()
                if current_time - cache_time > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.analysis_cache[key]
                
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """
        Get threat intelligence statistics.
        
        Returns:
            Dictionary with threat statistics
        """
        try:
            total_ips = len(self.threat_intelligence)
            blocked_ips = sum(1 for intel in self.threat_intelligence.values() if intel.blocked)
            high_risk_ips = sum(1 for intel in self.threat_intelligence.values() if intel.threat_score > 0.7)
            
            attack_type_counts = {}
            for intel in self.threat_intelligence.values():
                for attack_type in intel.attack_types:
                    attack_type_counts[attack_type] = attack_type_counts.get(attack_type, 0) + 1
            
            return {
                "total_tracked_ips": total_ips,
                "blocked_ips": blocked_ips,
                "high_risk_ips": high_risk_ips,
                "attack_type_distribution": attack_type_counts,
                "cache_size": len(self.analysis_cache),
                "patterns_loaded": sum(len(patterns) for patterns in self.attack_patterns.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting threat statistics: {e}")
            return {"error": str(e)}
    
    def cleanup_old_intelligence(self, days_old: int = 30) -> int:
        """
        Clean up old threat intelligence entries.
        
        Args:
            days_old: Remove entries older than this many days
            
        Returns:
            Number of entries removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_entries = [
                ip_hash for ip_hash, intel in self.threat_intelligence.items()
                if intel.last_seen < cutoff_date and not intel.blocked
            ]
            
            for ip_hash in old_entries:
                del self.threat_intelligence[ip_hash]
            
            if old_entries:
                self._save_threat_intelligence()
                logger.info(f"Cleaned up {len(old_entries)} old threat intelligence entries")
            
            return len(old_entries)
            
        except Exception as e:
            logger.error(f"Error cleaning up old intelligence: {e}")
            return 0