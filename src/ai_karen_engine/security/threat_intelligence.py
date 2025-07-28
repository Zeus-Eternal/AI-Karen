"""
Threat Intelligence Engine for intelligent authentication system.

This module provides comprehensive threat intelligence capabilities including
IP reputation checking, threat indicator matching, and external threat feed integration.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from ipaddress import ip_address, ip_network, AddressValueError
import aiohttp
from cachetools import TTLCache

from .models import AuthContext, ThreatAnalysis

logger = logging.getLogger(__name__)


class ThreatIndicatorType(Enum):
    """Types of threat indicators."""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    USER_AGENT = "user_agent"
    HASH = "hash"
    PATTERN = "pattern"


class ThreatSource(Enum):
    """Sources of threat intelligence."""
    INTERNAL = "internal"
    COMMERCIAL_FEED = "commercial_feed"
    OPEN_SOURCE = "open_source"
    COMMUNITY = "community"
    HONEYPOT = "honeypot"
    MANUAL = "manual"


class ReputationLevel(Enum):
    """IP reputation levels."""
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class ThreatIndicator:
    """Represents a threat indicator."""
    value: str
    indicator_type: ThreatIndicatorType
    reputation_level: ReputationLevel
    source: ThreatSource
    first_seen: datetime
    last_seen: datetime
    confidence: float  # 0.0 to 1.0
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'value': self.value,
            'indicator_type': self.indicator_type.value,
            'reputation_level': self.reputation_level.value,
            'source': self.source.value,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'confidence': self.confidence,
            'tags': self.tags,
            'description': self.description,
            'ttl': self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreatIndicator':
        """Create instance from dictionary."""
        return cls(
            value=data['value'],
            indicator_type=ThreatIndicatorType(data['indicator_type']),
            reputation_level=ReputationLevel(data['reputation_level']),
            source=ThreatSource(data['source']),
            first_seen=datetime.fromisoformat(data['first_seen']),
            last_seen=datetime.fromisoformat(data['last_seen']),
            confidence=data['confidence'],
            tags=data.get('tags', []),
            description=data.get('description'),
            ttl=data.get('ttl')
        )
    
    def is_expired(self) -> bool:
        """Check if indicator has expired."""
        if self.ttl is None:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() > self.ttl


@dataclass
class IPReputationResult:
    """Result of IP reputation check."""
    ip_address: str
    reputation_level: ReputationLevel
    confidence: float
    sources: List[str]
    tags: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ip_address': self.ip_address,
            'reputation_level': self.reputation_level.value,
            'confidence': self.confidence,
            'sources': self.sources,
            'tags': self.tags,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'additional_info': self.additional_info
        }


@dataclass
class ThreatContext:
    """Comprehensive threat context for authentication attempt."""
    ip_reputation: IPReputationResult
    threat_indicators: List[ThreatIndicator]
    risk_score: float
    threat_categories: List[str] = field(default_factory=list)
    attribution: Optional[str] = None
    campaign_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ip_reputation': self.ip_reputation.to_dict(),
            'threat_indicators': [indicator.to_dict() for indicator in self.threat_indicators],
            'risk_score': self.risk_score,
            'threat_categories': self.threat_categories,
            'attribution': self.attribution,
            'campaign_id': self.campaign_id
        }


class ThreatFeedManager:
    """Manages external threat intelligence feeds."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.feed_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour cache
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI-Karen-ThreatIntel/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def query_abuse_ipdb(self, ip: str) -> Optional[Dict[str, Any]]:
        """Query AbuseIPDB for IP reputation."""
        if not self.config.get('abuseipdb_api_key'):
            return None
        
        # Check rate limits (1000 requests per day)
        if not self._check_rate_limit('abuseipdb', 1000, 86400):
            logger.warning("AbuseIPDB rate limit exceeded")
            return None
        
        cache_key = f"abuseipdb:{ip}"
        if cache_key in self.feed_cache:
            return self.feed_cache[cache_key]
        
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                'Key': self.config['abuseipdb_api_key'],
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': 90,
                'verbose': ''
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data', {})
                    self.feed_cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"AbuseIPDB API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying AbuseIPDB: {e}")
            return None
    
    async def query_virustotal(self, ip: str) -> Optional[Dict[str, Any]]:
        """Query VirusTotal for IP reputation."""
        if not self.config.get('virustotal_api_key'):
            return None
        
        # Check rate limits (4 requests per minute for free tier)
        if not self._check_rate_limit('virustotal', 4, 60):
            logger.warning("VirusTotal rate limit exceeded")
            return None
        
        cache_key = f"virustotal:{ip}"
        if cache_key in self.feed_cache:
            return self.feed_cache[cache_key]
        
        try:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
            headers = {
                'x-apikey': self.config['virustotal_api_key']
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data', {})
                    self.feed_cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"VirusTotal API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying VirusTotal: {e}")
            return None
    
    async def query_shodan(self, ip: str) -> Optional[Dict[str, Any]]:
        """Query Shodan for IP information."""
        if not self.config.get('shodan_api_key'):
            return None
        
        # Check rate limits (100 requests per month for free tier)
        if not self._check_rate_limit('shodan', 100, 2592000):  # 30 days
            logger.warning("Shodan rate limit exceeded")
            return None
        
        cache_key = f"shodan:{ip}"
        if cache_key in self.feed_cache:
            return self.feed_cache[cache_key]
        
        try:
            url = f"https://api.shodan.io/shodan/host/{ip}"
            params = {
                'key': self.config['shodan_api_key']
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.feed_cache[cache_key] = data
                    return data
                else:
                    logger.warning(f"Shodan API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying Shodan: {e}")
            return None
    
    def _check_rate_limit(self, service: str, limit: int, window: int) -> bool:
        """Check if service is within rate limits."""
        now = time.time()
        service_requests = self.rate_limits[service]
        
        # Remove old requests outside the window
        service_requests[:] = [req_time for req_time in service_requests if now - req_time < window]
        
        # Check if we're within limits
        if len(service_requests) >= limit:
            return False
        
        # Add current request
        service_requests.append(now)
        return True


class ThreatIndicatorDatabase:
    """In-memory threat indicator database with persistence."""
    
    def __init__(self, persistence_file: Optional[str] = None):
        self.indicators: Dict[str, ThreatIndicator] = {}
        self.ip_networks: List[Tuple[ip_network, ThreatIndicator]] = []
        self.persistence_file = persistence_file
        self.last_cleanup = time.time()
        
        # Load from persistence file if available
        if persistence_file:
            self._load_from_file()
    
    def add_indicator(self, indicator: ThreatIndicator) -> None:
        """Add threat indicator to database."""
        key = self._get_indicator_key(indicator)
        self.indicators[key] = indicator
        
        # Handle IP networks separately for efficient matching
        if indicator.indicator_type == ThreatIndicatorType.IP_ADDRESS:
            try:
                if '/' in indicator.value:
                    network = ip_network(indicator.value, strict=False)
                    self.ip_networks.append((network, indicator))
            except AddressValueError:
                pass
        
        # Periodic cleanup
        if time.time() - self.last_cleanup > 3600:  # Every hour
            self._cleanup_expired()
    
    def get_indicator(self, value: str, indicator_type: ThreatIndicatorType) -> Optional[ThreatIndicator]:
        """Get threat indicator by value and type."""
        key = f"{indicator_type.value}:{value}"
        indicator = self.indicators.get(key)
        
        if indicator and indicator.is_expired():
            del self.indicators[key]
            return None
        
        return indicator
    
    def match_ip(self, ip_str: str) -> List[ThreatIndicator]:
        """Match IP address against indicators and networks."""
        matches = []
        
        try:
            ip_obj = ip_address(ip_str)
            
            # Check exact IP match
            exact_match = self.get_indicator(ip_str, ThreatIndicatorType.IP_ADDRESS)
            if exact_match:
                matches.append(exact_match)
            
            # Check network matches
            for network, indicator in self.ip_networks:
                if not indicator.is_expired() and ip_obj in network:
                    matches.append(indicator)
                    
        except AddressValueError:
            pass
        
        return matches
    
    def search_indicators(self, 
                         indicator_type: Optional[ThreatIndicatorType] = None,
                         reputation_level: Optional[ReputationLevel] = None,
                         tags: Optional[List[str]] = None) -> List[ThreatIndicator]:
        """Search indicators by criteria."""
        results = []
        
        for indicator in self.indicators.values():
            if indicator.is_expired():
                continue
                
            if indicator_type and indicator.indicator_type != indicator_type:
                continue
                
            if reputation_level and indicator.reputation_level != reputation_level:
                continue
                
            if tags and not any(tag in indicator.tags for tag in tags):
                continue
            
            results.append(indicator)
        
        return results
    
    def _get_indicator_key(self, indicator: ThreatIndicator) -> str:
        """Generate key for indicator storage."""
        return f"{indicator.indicator_type.value}:{indicator.value}"
    
    def _cleanup_expired(self) -> None:
        """Remove expired indicators."""
        expired_keys = []
        
        for key, indicator in self.indicators.items():
            if indicator.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.indicators[key]
        
        # Clean up IP networks
        self.ip_networks = [
            (network, indicator) for network, indicator in self.ip_networks
            if not indicator.is_expired()
        ]
        
        self.last_cleanup = time.time()
        logger.info(f"Cleaned up {len(expired_keys)} expired threat indicators")
    
    def _load_from_file(self) -> None:
        """Load indicators from persistence file."""
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    indicator = ThreatIndicator.from_dict(item)
                    if not indicator.is_expired():
                        self.add_indicator(indicator)
            logger.info(f"Loaded {len(self.indicators)} threat indicators from file")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load threat indicators from file: {e}")
    
    def save_to_file(self) -> None:
        """Save indicators to persistence file."""
        if not self.persistence_file:
            return
        
        try:
            data = [indicator.to_dict() for indicator in self.indicators.values()]
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} threat indicators to file")
        except Exception as e:
            logger.error(f"Could not save threat indicators to file: {e}")


class ThreatIntelligenceEngine:
    """Main threat intelligence engine."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.indicator_db = ThreatIndicatorDatabase(
            config.get('persistence_file', 'data/intelligent_auth/threat_indicators.json')
        )
        self.feed_manager_config = config.get('threat_feeds', {})
        self.ip_reputation_cache = TTLCache(maxsize=50000, ttl=3600)  # 1 hour cache
        
        # Initialize with some default malicious indicators
        self._initialize_default_indicators()
    
    def _initialize_default_indicators(self) -> None:
        """Initialize with default threat indicators."""
        default_indicators = [
            # Known malicious IP ranges (examples - replace with real threat intel)
            ThreatIndicator(
                value="10.0.0.0/8",
                indicator_type=ThreatIndicatorType.IP_ADDRESS,
                reputation_level=ReputationLevel.SUSPICIOUS,
                source=ThreatSource.INTERNAL,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                confidence=0.7,
                tags=["internal_network", "test"],
                description="Internal network range - suspicious for external access"
            ),
            # Tor exit nodes (example)
            ThreatIndicator(
                value="tor_exit_node",
                indicator_type=ThreatIndicatorType.PATTERN,
                reputation_level=ReputationLevel.SUSPICIOUS,
                source=ThreatSource.OPEN_SOURCE,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                confidence=0.8,
                tags=["tor", "anonymization"],
                description="Tor exit node"
            ),
            # Malicious user agents
            ThreatIndicator(
                value="sqlmap",
                indicator_type=ThreatIndicatorType.USER_AGENT,
                reputation_level=ReputationLevel.MALICIOUS,
                source=ThreatSource.INTERNAL,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                confidence=0.95,
                tags=["sql_injection", "scanner"],
                description="SQL injection tool user agent"
            )
        ]
        
        for indicator in default_indicators:
            self.indicator_db.add_indicator(indicator)
    
    async def analyze_ip_reputation(self, ip: str) -> IPReputationResult:
        """Analyze IP reputation using multiple sources."""
        # Check cache first
        cache_key = f"ip_reputation:{ip}"
        if cache_key in self.ip_reputation_cache:
            return self.ip_reputation_cache[cache_key]
        
        # Check local indicators first
        local_matches = self.indicator_db.match_ip(ip)
        
        # Initialize result
        reputation_level = ReputationLevel.CLEAN
        confidence = 0.0
        sources = []
        tags = []
        additional_info = {}
        
        # Process local matches
        if local_matches:
            # Use highest reputation level from matches
            reputation_levels = [match.reputation_level for match in local_matches]
            if ReputationLevel.CRITICAL in reputation_levels:
                reputation_level = ReputationLevel.CRITICAL
            elif ReputationLevel.MALICIOUS in reputation_levels:
                reputation_level = ReputationLevel.MALICIOUS
            elif ReputationLevel.SUSPICIOUS in reputation_levels:
                reputation_level = ReputationLevel.SUSPICIOUS
            
            # Aggregate confidence and tags
            confidence = max(match.confidence for match in local_matches)
            sources.extend([match.source.value for match in local_matches])
            for match in local_matches:
                tags.extend(match.tags)
        
        # Query external feeds if configured
        async with ThreatFeedManager(self.feed_manager_config) as feed_manager:
            # Query AbuseIPDB
            abuseipdb_data = await feed_manager.query_abuse_ipdb(ip)
            if abuseipdb_data:
                abuse_confidence = abuseipdb_data.get('abuseConfidencePercentage', 0) / 100.0
                if abuse_confidence > 0.5:
                    reputation_level = ReputationLevel.MALICIOUS
                    confidence = max(confidence, abuse_confidence)
                elif abuse_confidence > 0.2:
                    reputation_level = max(reputation_level, ReputationLevel.SUSPICIOUS, key=lambda x: x.value)
                    confidence = max(confidence, abuse_confidence)
                
                sources.append('abuseipdb')
                additional_info['abuseipdb'] = abuseipdb_data
            
            # Query VirusTotal
            virustotal_data = await feed_manager.query_virustotal(ip)
            if virustotal_data:
                attributes = virustotal_data.get('attributes', {})
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                malicious_count = last_analysis_stats.get('malicious', 0)
                total_count = sum(last_analysis_stats.values())
                
                if total_count > 0:
                    vt_confidence = malicious_count / total_count
                    if vt_confidence > 0.3:
                        reputation_level = ReputationLevel.MALICIOUS
                        confidence = max(confidence, vt_confidence)
                    elif vt_confidence > 0.1:
                        reputation_level = max(reputation_level, ReputationLevel.SUSPICIOUS, key=lambda x: x.value)
                        confidence = max(confidence, vt_confidence)
                
                sources.append('virustotal')
                additional_info['virustotal'] = virustotal_data
            
            # Query Shodan for additional context
            shodan_data = await feed_manager.query_shodan(ip)
            if shodan_data:
                # Shodan provides context but not direct reputation
                sources.append('shodan')
                additional_info['shodan'] = {
                    'ports': shodan_data.get('ports', []),
                    'hostnames': shodan_data.get('hostnames', []),
                    'org': shodan_data.get('org', ''),
                    'country_code': shodan_data.get('country_code', '')
                }
        
        # Create result
        result = IPReputationResult(
            ip_address=ip,
            reputation_level=reputation_level,
            confidence=confidence,
            sources=list(set(sources)),  # Remove duplicates
            tags=list(set(tags)),  # Remove duplicates
            first_seen=min(match.first_seen for match in local_matches) if local_matches else None,
            last_seen=max(match.last_seen for match in local_matches) if local_matches else None,
            additional_info=additional_info
        )
        
        # Cache result
        self.ip_reputation_cache[cache_key] = result
        
        return result
    
    async def get_threat_context(self, context: AuthContext) -> ThreatContext:
        """Get comprehensive threat context for authentication attempt."""
        # Analyze IP reputation
        ip_reputation = await self.analyze_ip_reputation(context.client_ip)
        
        # Find matching threat indicators
        threat_indicators = []
        
        # Check IP indicators
        ip_indicators = self.indicator_db.match_ip(context.client_ip)
        threat_indicators.extend(ip_indicators)
        
        # Check user agent indicators
        if context.user_agent:
            # Check for exact user agent match
            ua_indicator = self.indicator_db.get_indicator(
                context.user_agent.lower(), 
                ThreatIndicatorType.USER_AGENT
            )
            if ua_indicator:
                threat_indicators.append(ua_indicator)
            
            # Check for user agent patterns (substring matching)
            for ua_pattern_indicator in self.indicator_db.search_indicators(
                indicator_type=ThreatIndicatorType.USER_AGENT
            ):
                if ua_pattern_indicator.value.lower() in context.user_agent.lower():
                    threat_indicators.append(ua_pattern_indicator)
            
            # Check for general patterns in user agent
            for pattern_indicator in self.indicator_db.search_indicators(
                indicator_type=ThreatIndicatorType.PATTERN
            ):
                if pattern_indicator.value.lower() in context.user_agent.lower():
                    threat_indicators.append(pattern_indicator)
        
        # Check email indicators
        email_indicator = self.indicator_db.get_indicator(
            context.email, 
            ThreatIndicatorType.EMAIL
        )
        if email_indicator:
            threat_indicators.append(email_indicator)
        
        # Calculate overall risk score
        risk_score = self._calculate_threat_risk_score(ip_reputation, threat_indicators)
        
        # Determine threat categories
        threat_categories = self._determine_threat_categories(ip_reputation, threat_indicators)
        
        # Attempt attribution (simplified)
        attribution = self._attempt_attribution(threat_indicators)
        
        return ThreatContext(
            ip_reputation=ip_reputation,
            threat_indicators=threat_indicators,
            risk_score=risk_score,
            threat_categories=threat_categories,
            attribution=attribution
        )
    
    def _calculate_threat_risk_score(self, 
                                   ip_reputation: IPReputationResult, 
                                   indicators: List[ThreatIndicator]) -> float:
        """Calculate overall threat risk score."""
        base_score = 0.0
        
        # IP reputation contribution
        if ip_reputation.reputation_level == ReputationLevel.CRITICAL:
            base_score += 0.8 * ip_reputation.confidence
        elif ip_reputation.reputation_level == ReputationLevel.MALICIOUS:
            base_score += 0.6 * ip_reputation.confidence
        elif ip_reputation.reputation_level == ReputationLevel.SUSPICIOUS:
            base_score += 0.3 * ip_reputation.confidence
        
        # Threat indicators contribution
        for indicator in indicators:
            indicator_score = 0.0
            
            if indicator.reputation_level == ReputationLevel.CRITICAL:
                indicator_score = 0.7 * indicator.confidence
            elif indicator.reputation_level == ReputationLevel.MALICIOUS:
                indicator_score = 0.5 * indicator.confidence
            elif indicator.reputation_level == ReputationLevel.SUSPICIOUS:
                indicator_score = 0.2 * indicator.confidence
            
            base_score += indicator_score
        
        # Normalize to 0.0-1.0 range
        return min(base_score, 1.0)
    
    def _determine_threat_categories(self, 
                                   ip_reputation: IPReputationResult, 
                                   indicators: List[ThreatIndicator]) -> List[str]:
        """Determine threat categories from reputation and indicators."""
        categories = set()
        
        # Add categories from IP reputation tags
        categories.update(ip_reputation.tags)
        
        # Add categories from threat indicators
        for indicator in indicators:
            categories.update(indicator.tags)
        
        return list(categories)
    
    def _attempt_attribution(self, indicators: List[ThreatIndicator]) -> Optional[str]:
        """Attempt to attribute threat to known actors or campaigns."""
        # Simple attribution based on indicator tags
        # In a real implementation, this would be more sophisticated
        
        for indicator in indicators:
            if 'apt' in indicator.tags:
                return f"APT (based on {indicator.value})"
            elif 'botnet' in indicator.tags:
                return f"Botnet (based on {indicator.value})"
            elif 'scanner' in indicator.tags:
                return f"Automated Scanner (based on {indicator.value})"
        
        return None
    
    def update_threat_intelligence(self, new_indicators: List[ThreatIndicator]) -> None:
        """Update threat intelligence with new indicators."""
        for indicator in new_indicators:
            self.indicator_db.add_indicator(indicator)
        
        # Save to persistence file
        self.indicator_db.save_to_file()
        
        logger.info(f"Updated threat intelligence with {len(new_indicators)} new indicators")
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat intelligence statistics."""
        all_indicators = list(self.indicator_db.indicators.values())
        
        # Count by type
        type_counts = defaultdict(int)
        for indicator in all_indicators:
            type_counts[indicator.indicator_type.value] += 1
        
        # Count by reputation level
        reputation_counts = defaultdict(int)
        for indicator in all_indicators:
            reputation_counts[indicator.reputation_level.value] += 1
        
        # Count by source
        source_counts = defaultdict(int)
        for indicator in all_indicators:
            source_counts[indicator.source.value] += 1
        
        return {
            'total_indicators': len(all_indicators),
            'by_type': dict(type_counts),
            'by_reputation': dict(reputation_counts),
            'by_source': dict(source_counts),
            'cache_size': len(self.ip_reputation_cache),
            'cache_hits': getattr(self.ip_reputation_cache, 'hits', 0),
            'cache_misses': getattr(self.ip_reputation_cache, 'misses', 0)
        }