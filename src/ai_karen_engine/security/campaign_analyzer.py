"""
Campaign Analyzer for detecting coordinated attack campaigns.

This module provides sophisticated attack campaign correlation capabilities,
including threat actor identification, cross-user attack pattern correlation,
and automated threat intelligence sharing.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from pathlib import Path
try:
    import numpy as np
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    # Fallback when sklearn is not available
    SKLEARN_AVAILABLE = False
    np = None
    DBSCAN = None
    StandardScaler = None

from .models import AuthContext, ThreatAnalysis
# Import will be done locally to avoid circular imports

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    """Types of attack campaigns."""
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ACCOUNT_TAKEOVER = "account_takeover"
    DISTRIBUTED_ATTACK = "distributed_attack"
    APT_CAMPAIGN = "apt_campaign"
    BOTNET_ACTIVITY = "botnet_activity"
    RECONNAISSANCE = "reconnaissance"
    UNKNOWN = "unknown"


class ThreatActor(Enum):
    """Known threat actor categories."""
    SCRIPT_KIDDIE = "script_kiddie"
    CYBERCRIMINAL = "cybercriminal"
    NATION_STATE = "nation_state"
    INSIDER_THREAT = "insider_threat"
    HACKTIVIST = "hacktivist"
    AUTOMATED_TOOL = "automated_tool"
    UNKNOWN = "unknown"


@dataclass
class AttackSignature:
    """Signature pattern for attack identification."""
    signature_id: str
    name: str
    description: str
    indicators: List[str]
    confidence_threshold: float
    campaign_type: CampaignType
    threat_actor: Optional[ThreatActor] = None
    ttl: Optional[int] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'signature_id': self.signature_id,
            'name': self.name,
            'description': self.description,
            'indicators': self.indicators,
            'confidence_threshold': self.confidence_threshold,
            'campaign_type': self.campaign_type.value,
            'threat_actor': self.threat_actor.value if self.threat_actor else None,
            'ttl': self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackSignature':
        """Create instance from dictionary."""
        return cls(
            signature_id=data['signature_id'],
            name=data['name'],
            description=data['description'],
            indicators=data['indicators'],
            confidence_threshold=data['confidence_threshold'],
            campaign_type=CampaignType(data['campaign_type']),
            threat_actor=ThreatActor(data['threat_actor']) if data.get('threat_actor') else None,
            ttl=data.get('ttl')
        )


@dataclass
class CampaignEvent:
    """Individual event within an attack campaign."""
    event_id: str
    timestamp: datetime
    auth_context: AuthContext
    threat_analysis: ThreatAnalysis
    campaign_indicators: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'auth_context': self.auth_context.to_dict(),
            'threat_analysis': self.threat_analysis.to_dict(),
            'campaign_indicators': self.campaign_indicators,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignEvent':
        """Create instance from dictionary."""
        return cls(
            event_id=data['event_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            auth_context=AuthContext.from_dict(data['auth_context']),
            threat_analysis=ThreatAnalysis.from_dict(data['threat_analysis']),
            campaign_indicators=data.get('campaign_indicators', []),
            confidence_score=data.get('confidence_score', 0.0)
        )


@dataclass
class AttackCampaign:
    """Represents a coordinated attack campaign."""
    campaign_id: str
    campaign_type: CampaignType
    threat_actor: Optional[ThreatActor]
    first_seen: datetime
    last_seen: datetime
    events: List[CampaignEvent] = field(default_factory=list)
    
    # Campaign characteristics
    target_users: Set[str] = field(default_factory=set)
    source_ips: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    attack_patterns: List[str] = field(default_factory=list)
    
    # Campaign metrics
    total_attempts: int = 0
    success_rate: float = 0.0
    geographic_distribution: Dict[str, int] = field(default_factory=dict)
    temporal_pattern: Dict[str, int] = field(default_factory=dict)
    
    # Attribution and intelligence
    attribution_confidence: float = 0.0
    related_campaigns: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)  # Indicators of Compromise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'campaign_id': self.campaign_id,
            'campaign_type': self.campaign_type.value,
            'threat_actor': self.threat_actor.value if self.threat_actor else None,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'events': [event.to_dict() for event in self.events],
            'target_users': list(self.target_users),
            'source_ips': list(self.source_ips),
            'user_agents': list(self.user_agents),
            'attack_patterns': self.attack_patterns,
            'total_attempts': self.total_attempts,
            'success_rate': self.success_rate,
            'geographic_distribution': self.geographic_distribution,
            'temporal_pattern': self.temporal_pattern,
            'attribution_confidence': self.attribution_confidence,
            'related_campaigns': self.related_campaigns,
            'iocs': self.iocs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackCampaign':
        """Create instance from dictionary."""
        return cls(
            campaign_id=data['campaign_id'],
            campaign_type=CampaignType(data['campaign_type']),
            threat_actor=ThreatActor(data['threat_actor']) if data.get('threat_actor') else None,
            first_seen=datetime.fromisoformat(data['first_seen']),
            last_seen=datetime.fromisoformat(data['last_seen']),
            events=[CampaignEvent.from_dict(event) for event in data.get('events', [])],
            target_users=set(data.get('target_users', [])),
            source_ips=set(data.get('source_ips', [])),
            user_agents=set(data.get('user_agents', [])),
            attack_patterns=data.get('attack_patterns', []),
            total_attempts=data.get('total_attempts', 0),
            success_rate=data.get('success_rate', 0.0),
            geographic_distribution=data.get('geographic_distribution', {}),
            temporal_pattern=data.get('temporal_pattern', {}),
            attribution_confidence=data.get('attribution_confidence', 0.0),
            related_campaigns=data.get('related_campaigns', []),
            iocs=data.get('iocs', [])
        )
    
    def add_event(self, event: CampaignEvent) -> None:
        """Add event to campaign and update metrics."""
        self.events.append(event)
        self.last_seen = max(self.last_seen, event.timestamp)
        
        # Update campaign characteristics
        self.target_users.add(event.auth_context.email)
        self.source_ips.add(event.auth_context.client_ip)
        self.user_agents.add(event.auth_context.user_agent)
        
        # Update metrics
        self.total_attempts += 1
        
        # Update geographic distribution
        if event.auth_context.geolocation:
            country = event.auth_context.geolocation.country
            self.geographic_distribution[country] = self.geographic_distribution.get(country, 0) + 1
        
        # Update temporal pattern (hour of day)
        hour = event.timestamp.hour
        hour_key = f"hour_{hour:02d}"
        self.temporal_pattern[hour_key] = self.temporal_pattern.get(hour_key, 0) + 1
    
    def calculate_campaign_score(self) -> float:
        """Calculate overall campaign threat score."""
        base_score = 0.0
        
        # Volume factor
        volume_score = min(len(self.events) / 100.0, 1.0)  # Normalize to 100 events
        base_score += volume_score * 0.3
        
        # Distribution factor (more IPs = higher score)
        distribution_score = min(len(self.source_ips) / 50.0, 1.0)  # Normalize to 50 IPs
        base_score += distribution_score * 0.2
        
        # Target diversity factor
        target_score = min(len(self.target_users) / 20.0, 1.0)  # Normalize to 20 users
        base_score += target_score * 0.2
        
        # Attribution confidence
        base_score += self.attribution_confidence * 0.3
        
        return min(base_score, 1.0)


@dataclass
class CampaignAnalysisResult:
    """Result of campaign analysis."""
    detected_campaigns: List[AttackCampaign]
    new_campaigns: List[AttackCampaign]
    updated_campaigns: List[AttackCampaign]
    campaign_correlations: Dict[str, List[str]]
    threat_intelligence_updates: List[Any]
    analysis_timestamp: datetime
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'detected_campaigns': [campaign.to_dict() for campaign in self.detected_campaigns],
            'new_campaigns': [campaign.to_dict() for campaign in self.new_campaigns],
            'updated_campaigns': [campaign.to_dict() for campaign in self.updated_campaigns],
            'campaign_correlations': self.campaign_correlations,
            'threat_intelligence_updates': [indicator.to_dict() for indicator in self.threat_intelligence_updates],
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'processing_time': self.processing_time
        }


class CampaignDatabase:
    """Database for storing and managing attack campaigns."""
    
    def __init__(self, persistence_file: Optional[str] = None):
        self.campaigns: Dict[str, AttackCampaign] = {}
        self.campaign_index: Dict[str, Set[str]] = defaultdict(set)  # Index by various attributes
        self.persistence_file = persistence_file
        self.last_cleanup = time.time()
        
        # Load from persistence file if available
        if persistence_file:
            self._load_from_file()
    
    def add_campaign(self, campaign: AttackCampaign) -> None:
        """Add campaign to database."""
        self.campaigns[campaign.campaign_id] = campaign
        self._update_index(campaign)
    
    def get_campaign(self, campaign_id: str) -> Optional[AttackCampaign]:
        """Get campaign by ID."""
        return self.campaigns.get(campaign_id)
    
    def find_campaigns_by_ip(self, ip: str) -> List[AttackCampaign]:
        """Find campaigns involving specific IP."""
        campaign_ids = self.campaign_index.get(f"ip:{ip}", set())
        return [self.campaigns[cid] for cid in campaign_ids if cid in self.campaigns]
    
    def find_campaigns_by_user(self, email: str) -> List[AttackCampaign]:
        """Find campaigns targeting specific user."""
        campaign_ids = self.campaign_index.get(f"user:{email}", set())
        return [self.campaigns[cid] for cid in campaign_ids if cid in self.campaigns]
    
    def find_campaigns_by_type(self, campaign_type: CampaignType) -> List[AttackCampaign]:
        """Find campaigns by type."""
        campaign_ids = self.campaign_index.get(f"type:{campaign_type.value}", set())
        return [self.campaigns[cid] for cid in campaign_ids if cid in self.campaigns]
    
    def find_recent_campaigns(self, hours: int = 24) -> List[AttackCampaign]:
        """Find campaigns active in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [campaign for campaign in self.campaigns.values() 
                if campaign.last_seen >= cutoff]
    
    def _update_index(self, campaign: AttackCampaign) -> None:
        """Update campaign index."""
        # Index by IPs
        for ip in campaign.source_ips:
            self.campaign_index[f"ip:{ip}"].add(campaign.campaign_id)
        
        # Index by users
        for user in campaign.target_users:
            self.campaign_index[f"user:{user}"].add(campaign.campaign_id)
        
        # Index by type
        self.campaign_index[f"type:{campaign.campaign_type.value}"].add(campaign.campaign_id)
        
        # Index by threat actor
        if campaign.threat_actor:
            self.campaign_index[f"actor:{campaign.threat_actor.value}"].add(campaign.campaign_id)
    
    def _load_from_file(self) -> None:
        """Load campaigns from persistence file."""
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    campaign = AttackCampaign.from_dict(item)
                    self.add_campaign(campaign)
            logger.info(f"Loaded {len(self.campaigns)} attack campaigns from file")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load campaigns from file: {e}")
    
    def save_to_file(self) -> None:
        """Save campaigns to persistence file."""
        if not self.persistence_file:
            return
        
        try:
            # Ensure directory exists
            Path(self.persistence_file).parent.mkdir(parents=True, exist_ok=True)
            
            data = [campaign.to_dict() for campaign in self.campaigns.values()]
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} attack campaigns to file")
        except Exception as e:
            logger.error(f"Could not save campaigns to file: {e}")


class CampaignAnalyzer:
    """Main campaign analyzer for detecting coordinated attack campaigns."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.campaign_db = CampaignDatabase(
            config.get('persistence_file', 'data/intelligent_auth/attack_campaigns.json')
        )
        self.attack_signatures = self._load_attack_signatures()
        self.correlation_threshold = config.get('correlation_threshold', 0.7)
        self.min_events_for_campaign = config.get('min_events_for_campaign', 5)
        self.campaign_timeout = config.get('campaign_timeout_hours', 72)  # 3 days
        
        # Clustering parameters for pattern detection
        self.clustering_eps = config.get('clustering_eps', 0.5)
        self.clustering_min_samples = config.get('clustering_min_samples', 3)
        
        logger.info("Campaign analyzer initialized")
    
    def _load_attack_signatures(self) -> List[AttackSignature]:
        """Load attack signatures for campaign detection."""
        signatures = [
            # Brute force signatures
            AttackSignature(
                signature_id="bf_rapid_attempts",
                name="Rapid Brute Force",
                description="Multiple failed login attempts in short time",
                indicators=["rapid_attempts", "multiple_failures", "same_ip"],
                confidence_threshold=0.8,
                campaign_type=CampaignType.BRUTE_FORCE,
                threat_actor=ThreatActor.AUTOMATED_TOOL
            ),
            
            # Credential stuffing signatures
            AttackSignature(
                signature_id="cs_distributed",
                name="Distributed Credential Stuffing",
                description="Multiple IPs testing common credentials",
                indicators=["multiple_ips", "common_passwords", "low_success_rate"],
                confidence_threshold=0.7,
                campaign_type=CampaignType.CREDENTIAL_STUFFING,
                threat_actor=ThreatActor.CYBERCRIMINAL
            ),
            
            # Account takeover signatures
            AttackSignature(
                signature_id="ato_location_anomaly",
                name="Account Takeover - Location",
                description="Successful login from unusual location",
                indicators=["location_anomaly", "device_change", "successful_login"],
                confidence_threshold=0.6,
                campaign_type=CampaignType.ACCOUNT_TAKEOVER,
                threat_actor=ThreatActor.CYBERCRIMINAL
            ),
            
            # APT signatures
            AttackSignature(
                signature_id="apt_persistent",
                name="APT Persistent Access",
                description="Low-volume, persistent access attempts",
                indicators=["persistent_attempts", "specific_targets", "advanced_evasion"],
                confidence_threshold=0.9,
                campaign_type=CampaignType.APT_CAMPAIGN,
                threat_actor=ThreatActor.NATION_STATE
            ),
            
            # Botnet signatures
            AttackSignature(
                signature_id="botnet_distributed",
                name="Botnet Activity",
                description="Coordinated activity from multiple compromised hosts",
                indicators=["distributed_sources", "coordinated_timing", "similar_patterns"],
                confidence_threshold=0.8,
                campaign_type=CampaignType.BOTNET_ACTIVITY,
                threat_actor=ThreatActor.CYBERCRIMINAL
            )
        ]
        
        return signatures
    
    async def analyze_attack_campaigns(self, 
                                     auth_attempts: List[Tuple[AuthContext, ThreatAnalysis]],
                                     time_window_hours: int = 24) -> CampaignAnalysisResult:
        """Analyze authentication attempts for attack campaigns."""
        start_time = time.time()
        
        # Convert to campaign events
        events = []
        for i, (auth_context, threat_analysis) in enumerate(auth_attempts):
            event = CampaignEvent(
                event_id=f"event_{int(time.time())}_{i}",
                timestamp=auth_context.timestamp,
                auth_context=auth_context,
                threat_analysis=threat_analysis
            )
            events.append(event)
        
        # Detect new campaigns
        new_campaigns = await self._detect_new_campaigns(events)
        
        # Update existing campaigns
        updated_campaigns = await self._update_existing_campaigns(events)
        
        # Correlate campaigns
        campaign_correlations = await self._correlate_campaigns(new_campaigns + updated_campaigns)
        
        # Generate threat intelligence updates
        threat_intel_updates = await self._generate_threat_intelligence(new_campaigns + updated_campaigns)
        
        # Get all detected campaigns
        all_campaigns = new_campaigns + updated_campaigns
        
        # Save campaigns to database
        for campaign in new_campaigns:
            self.campaign_db.add_campaign(campaign)
        
        self.campaign_db.save_to_file()
        
        processing_time = time.time() - start_time
        
        return CampaignAnalysisResult(
            detected_campaigns=all_campaigns,
            new_campaigns=new_campaigns,
            updated_campaigns=updated_campaigns,
            campaign_correlations=campaign_correlations,
            threat_intelligence_updates=threat_intel_updates,
            analysis_timestamp=datetime.utcnow(),
            processing_time=processing_time
        )
    
    async def _detect_new_campaigns(self, events: List[CampaignEvent]) -> List[AttackCampaign]:
        """Detect new attack campaigns from events."""
        new_campaigns = []
        
        # Group events by potential campaign indicators
        campaign_groups = self._group_events_by_similarity(events)
        
        for group_id, group_events in campaign_groups.items():
            if len(group_events) < self.min_events_for_campaign:
                continue
            
            # Analyze group for campaign characteristics
            campaign_type, threat_actor, confidence = await self._classify_campaign(group_events)
            
            if confidence >= self.correlation_threshold:
                # Create new campaign
                campaign_id = self._generate_campaign_id(group_events)
                
                # Check if campaign already exists
                if self.campaign_db.get_campaign(campaign_id):
                    continue
                
                campaign = AttackCampaign(
                    campaign_id=campaign_id,
                    campaign_type=campaign_type,
                    threat_actor=threat_actor,
                    first_seen=min(event.timestamp for event in group_events),
                    last_seen=max(event.timestamp for event in group_events),
                    attribution_confidence=confidence
                )
                
                # Add events to campaign
                for event in group_events:
                    campaign.add_event(event)
                
                new_campaigns.append(campaign)
                logger.info(f"Detected new campaign: {campaign_id} ({campaign_type.value})")
        
        return new_campaigns
    
    async def _update_existing_campaigns(self, events: List[CampaignEvent]) -> List[AttackCampaign]:
        """Update existing campaigns with new events."""
        updated_campaigns = []
        recent_campaigns = self.campaign_db.find_recent_campaigns(self.campaign_timeout)
        
        for event in events:
            # Find campaigns that might match this event
            matching_campaigns = []
            
            # Check by IP
            ip_campaigns = self.campaign_db.find_campaigns_by_ip(event.auth_context.client_ip)
            matching_campaigns.extend(ip_campaigns)
            
            # Check by user
            user_campaigns = self.campaign_db.find_campaigns_by_user(event.auth_context.email)
            matching_campaigns.extend(user_campaigns)
            
            # Remove duplicates and filter recent campaigns
            seen_campaign_ids = set()
            unique_campaigns = []
            for campaign in matching_campaigns:
                if campaign.campaign_id not in seen_campaign_ids:
                    seen_campaign_ids.add(campaign.campaign_id)
                    unique_campaigns.append(campaign)
            matching_campaigns = [c for c in unique_campaigns if c in recent_campaigns]
            
            # Find best matching campaign
            best_match = None
            best_score = 0.0
            
            for campaign in matching_campaigns:
                score = self._calculate_event_campaign_similarity(event, campaign)
                if score > best_score and score >= self.correlation_threshold:
                    best_match = campaign
                    best_score = score
            
            if best_match:
                best_match.add_event(event)
                if best_match not in updated_campaigns:
                    updated_campaigns.append(best_match)
        
        return updated_campaigns
    
    def _group_events_by_similarity(self, events: List[CampaignEvent]) -> Dict[str, List[CampaignEvent]]:
        """Group events by similarity for campaign detection."""
        if not events:
            return {}
        
        # Extract features for clustering
        features = []
        for event in events:
            feature_vector = self._extract_event_features(event)
            features.append(feature_vector)
        
        # Perform clustering
        if len(features) < self.clustering_min_samples:
            # Not enough events for clustering, group by simple heuristics
            return self._group_events_by_heuristics(events)
        
        if SKLEARN_AVAILABLE:
            try:
                # Normalize features
                scaler = StandardScaler()
                features_normalized = scaler.fit_transform(features)
                
                # Apply DBSCAN clustering
                clustering = DBSCAN(eps=self.clustering_eps, min_samples=self.clustering_min_samples)
                cluster_labels = clustering.fit_predict(features_normalized)
                
                # Group events by cluster
                groups = defaultdict(list)
                for i, label in enumerate(cluster_labels):
                    if label != -1:  # Ignore noise points
                        groups[f"cluster_{label}"].append(events[i])
                
                return dict(groups)
                
            except Exception as e:
                logger.warning(f"Clustering failed, using heuristic grouping: {e}")
                return self._group_events_by_heuristics(events)
        else:
            logger.warning("sklearn not available, using heuristic grouping")
            return self._group_events_by_heuristics(events)
    
    def _group_events_by_heuristics(self, events: List[CampaignEvent]) -> Dict[str, List[CampaignEvent]]:
        """Group events using simple heuristics."""
        groups = defaultdict(list)
        
        for event in events:
            # Group by IP address as primary indicator
            ip_key = f"ip_{event.auth_context.client_ip}"
            groups[ip_key].append(event)
        
        return dict(groups)
    
    def _extract_event_features(self, event: CampaignEvent) -> List[float]:
        """Extract numerical features from event for clustering."""
        features = []
        
        # Time-based features
        features.append(event.timestamp.hour)  # Hour of day
        features.append(event.timestamp.weekday())  # Day of week
        
        # IP-based features (hash to numerical)
        ip_hash = hash(event.auth_context.client_ip) % 10000
        features.append(ip_hash)
        
        # User agent features (hash to numerical)
        ua_hash = hash(event.auth_context.user_agent) % 10000
        features.append(ua_hash)
        
        # Threat analysis features
        features.append(event.threat_analysis.ip_reputation_score)
        features.append(len(event.threat_analysis.known_attack_patterns))
        features.append(event.threat_analysis.similar_attacks_detected)
        
        # Geographic features
        if event.auth_context.geolocation:
            features.append(event.auth_context.geolocation.latitude)
            features.append(event.auth_context.geolocation.longitude)
        else:
            features.extend([0.0, 0.0])
        
        # Boolean features (convert to 0/1)
        features.append(1.0 if event.auth_context.is_tor_exit_node else 0.0)
        features.append(1.0 if event.auth_context.is_vpn else 0.0)
        
        return features
    
    async def _classify_campaign(self, events: List[CampaignEvent]) -> Tuple[CampaignType, Optional[ThreatActor], float]:
        """Classify campaign type and threat actor."""
        # Analyze events against attack signatures
        signature_scores = {}
        
        for signature in self.attack_signatures:
            score = self._calculate_signature_match(events, signature)
            signature_scores[signature.signature_id] = (signature, score)
        
        # Find best matching signature
        best_signature = None
        best_score = 0.0
        
        for sig_id, (signature, score) in signature_scores.items():
            if score > best_score:
                best_signature = signature
                best_score = score
        
        if best_signature and best_score >= best_signature.confidence_threshold:
            return best_signature.campaign_type, best_signature.threat_actor, best_score
        
        # Fallback classification based on event patterns
        return self._classify_by_patterns(events)
    
    def _calculate_signature_match(self, events: List[CampaignEvent], signature: AttackSignature) -> float:
        """Calculate how well events match an attack signature."""
        indicator_matches = 0
        total_indicators = len(signature.indicators)
        
        if total_indicators == 0:
            return 0.0
        
        # Check each indicator
        for indicator in signature.indicators:
            if self._check_indicator_match(events, indicator):
                indicator_matches += 1
        
        return indicator_matches / total_indicators
    
    def _check_indicator_match(self, events: List[CampaignEvent], indicator: str) -> bool:
        """Check if events match a specific indicator."""
        if indicator == "rapid_attempts":
            # Check for rapid succession of attempts
            timestamps = [event.timestamp for event in events]
            timestamps.sort()
            for i in range(1, len(timestamps)):
                if (timestamps[i] - timestamps[i-1]).total_seconds() < 60:  # Within 1 minute
                    return True
        
        elif indicator == "multiple_failures":
            # Check for multiple failed attempts
            return len(events) >= 3
        
        elif indicator == "same_ip":
            # Check if events come from same IP
            ips = set(event.auth_context.client_ip for event in events)
            return len(ips) == 1
        
        elif indicator == "multiple_ips":
            # Check for multiple source IPs
            ips = set(event.auth_context.client_ip for event in events)
            return len(ips) >= 3
        
        elif indicator == "common_passwords":
            # Check for common password patterns (simplified)
            return any("password" in event.auth_context.password_hash.lower() for event in events)
        
        elif indicator == "low_success_rate":
            # Assume all events in this context are failures for simplicity
            return True
        
        elif indicator == "location_anomaly":
            # Check for location anomalies
            return any(event.auth_context.geolocation and 
                      not event.auth_context.geolocation.is_usual_location 
                      for event in events)
        
        elif indicator == "device_change":
            # Check for device changes (simplified)
            user_agents = set(event.auth_context.user_agent for event in events)
            return len(user_agents) > 1
        
        elif indicator == "successful_login":
            # This would need to be determined from context
            return False  # Simplified assumption
        
        elif indicator == "persistent_attempts":
            # Check for attempts over extended period
            if len(events) < 2:
                return False
            timestamps = [event.timestamp for event in events]
            time_span = max(timestamps) - min(timestamps)
            return time_span.total_seconds() > 3600  # Over 1 hour
        
        elif indicator == "specific_targets":
            # Check for targeting specific users
            users = set(event.auth_context.email for event in events)
            return len(users) <= 3  # Targeting few specific users
        
        elif indicator == "advanced_evasion":
            # Check for evasion techniques
            return any(event.auth_context.is_tor_exit_node or event.auth_context.is_vpn 
                      for event in events)
        
        elif indicator == "distributed_sources":
            # Check for distributed source IPs
            ips = set(event.auth_context.client_ip for event in events)
            return len(ips) >= 5
        
        elif indicator == "coordinated_timing":
            # Check for coordinated timing patterns
            timestamps = [event.timestamp for event in events]
            if len(timestamps) < 3:
                return False
            
            # Check if events occur at similar intervals
            intervals = []
            timestamps.sort()
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            # Check if intervals are similar (within 10% variance)
            if len(intervals) < 2:
                return False
            
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
            coefficient_of_variation = (variance ** 0.5) / avg_interval if avg_interval > 0 else 1
            
            return coefficient_of_variation < 0.1
        
        elif indicator == "similar_patterns":
            # Check for similar attack patterns
            user_agents = [event.auth_context.user_agent for event in events]
            return len(set(user_agents)) / len(user_agents) < 0.5  # More than 50% similarity
        
        return False
    
    def _classify_by_patterns(self, events: List[CampaignEvent]) -> Tuple[CampaignType, Optional[ThreatActor], float]:
        """Classify campaign by analyzing event patterns."""
        # Simple pattern-based classification
        ips = set(event.auth_context.client_ip for event in events)
        users = set(event.auth_context.email for event in events)
        
        # Multiple IPs, few users = credential stuffing
        if len(ips) > 5 and len(users) < 5:
            return CampaignType.CREDENTIAL_STUFFING, ThreatActor.CYBERCRIMINAL, 0.6
        
        # Single IP, multiple users = brute force
        if len(ips) == 1 and len(users) > 3:
            return CampaignType.BRUTE_FORCE, ThreatActor.AUTOMATED_TOOL, 0.7
        
        # Multiple IPs, multiple users = distributed attack
        if len(ips) > 3 and len(users) > 3:
            return CampaignType.DISTRIBUTED_ATTACK, ThreatActor.CYBERCRIMINAL, 0.5
        
        return CampaignType.UNKNOWN, None, 0.3
    
    def _calculate_event_campaign_similarity(self, event: CampaignEvent, campaign: AttackCampaign) -> float:
        """Calculate similarity between event and existing campaign."""
        score = 0.0
        
        # IP similarity
        if event.auth_context.client_ip in campaign.source_ips:
            score += 0.4
        
        # User similarity
        if event.auth_context.email in campaign.target_users:
            score += 0.3
        
        # User agent similarity
        if event.auth_context.user_agent in campaign.user_agents:
            score += 0.2
        
        # Time proximity (within campaign timeout)
        time_diff = abs((event.timestamp - campaign.last_seen).total_seconds())
        if time_diff < self.campaign_timeout * 3600:  # Within timeout window
            time_score = max(0, 1 - (time_diff / (self.campaign_timeout * 3600)))
            score += time_score * 0.1
        
        return score
    
    def _generate_campaign_id(self, events: List[CampaignEvent]) -> str:
        """Generate unique campaign ID based on events."""
        # Create hash from key characteristics
        ips = sorted(set(event.auth_context.client_ip for event in events))
        users = sorted(set(event.auth_context.email for event in events))
        first_timestamp = min(event.timestamp for event in events)
        
        hash_input = f"{':'.join(ips)}|{':'.join(users)}|{first_timestamp.isoformat()}"
        campaign_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        return f"campaign_{campaign_hash}"
    
    async def _correlate_campaigns(self, campaigns: List[AttackCampaign]) -> Dict[str, List[str]]:
        """Correlate campaigns to find relationships."""
        correlations = {}
        
        for i, campaign1 in enumerate(campaigns):
            related_campaigns = []
            
            for j, campaign2 in enumerate(campaigns):
                if i != j:
                    similarity = self._calculate_campaign_similarity(campaign1, campaign2)
                    if similarity >= self.correlation_threshold:
                        related_campaigns.append(campaign2.campaign_id)
            
            if related_campaigns:
                correlations[campaign1.campaign_id] = related_campaigns
                campaign1.related_campaigns = related_campaigns
        
        return correlations
    
    def _calculate_campaign_similarity(self, campaign1: AttackCampaign, campaign2: AttackCampaign) -> float:
        """Calculate similarity between two campaigns."""
        score = 0.0
        
        # IP overlap
        ip_overlap = len(campaign1.source_ips & campaign2.source_ips)
        ip_union = len(campaign1.source_ips | campaign2.source_ips)
        if ip_union > 0:
            score += (ip_overlap / ip_union) * 0.4
        
        # User overlap
        user_overlap = len(campaign1.target_users & campaign2.target_users)
        user_union = len(campaign1.target_users | campaign2.target_users)
        if user_union > 0:
            score += (user_overlap / user_union) * 0.3
        
        # Campaign type similarity
        if campaign1.campaign_type == campaign2.campaign_type:
            score += 0.2
        
        # Threat actor similarity
        if campaign1.threat_actor and campaign2.threat_actor and campaign1.threat_actor == campaign2.threat_actor:
            score += 0.1
        
        return score
    
    async def _generate_threat_intelligence(self, campaigns: List[AttackCampaign]) -> List[Any]:
        """Generate threat intelligence indicators from campaigns."""
        # Import locally to avoid circular imports
        try:
            from .threat_intelligence import ThreatIndicator, ThreatIndicatorType, ReputationLevel, ThreatSource
        except ImportError:
            logger.warning("Could not import threat intelligence classes, returning empty list")
            return []
        
        indicators = []
        
        for campaign in campaigns:
            # Generate IP indicators
            for ip in campaign.source_ips:
                if len(campaign.events) >= 5:  # Only for significant campaigns
                    reputation_level = ReputationLevel.SUSPICIOUS
                    if campaign.campaign_type in [CampaignType.APT_CAMPAIGN, CampaignType.BOTNET_ACTIVITY]:
                        reputation_level = ReputationLevel.MALICIOUS
                    
                    indicator = ThreatIndicator(
                        value=ip,
                        indicator_type=ThreatIndicatorType.IP_ADDRESS,
                        reputation_level=reputation_level,
                        source=ThreatSource.INTERNAL,
                        first_seen=campaign.first_seen,
                        last_seen=campaign.last_seen,
                        confidence=campaign.attribution_confidence,
                        tags=[campaign.campaign_type.value, "campaign_detected"],
                        description=f"IP involved in {campaign.campaign_type.value} campaign {campaign.campaign_id}",
                        ttl=7 * 24 * 3600  # 7 days
                    )
                    indicators.append(indicator)
            
            # Generate user agent indicators for suspicious patterns
            for ua in campaign.user_agents:
                if any(pattern in ua.lower() for pattern in ['bot', 'crawler', 'scanner', 'tool']):
                    indicator = ThreatIndicator(
                        value=ua,
                        indicator_type=ThreatIndicatorType.USER_AGENT,
                        reputation_level=ReputationLevel.SUSPICIOUS,
                        source=ThreatSource.INTERNAL,
                        first_seen=campaign.first_seen,
                        last_seen=campaign.last_seen,
                        confidence=campaign.attribution_confidence,
                        tags=[campaign.campaign_type.value, "suspicious_ua"],
                        description=f"Suspicious user agent from campaign {campaign.campaign_id}",
                        ttl=30 * 24 * 3600  # 30 days
                    )
                    indicators.append(indicator)
        
        return indicators
    
    def get_campaign_statistics(self) -> Dict[str, Any]:
        """Get campaign analysis statistics."""
        campaigns = list(self.campaign_db.campaigns.values())
        
        if not campaigns:
            return {
                'total_campaigns': 0,
                'active_campaigns': 0,
                'campaign_types': {},
                'threat_actors': {},
                'avg_campaign_duration': 0,
                'total_events': 0
            }
        
        # Count by type
        type_counts = Counter(campaign.campaign_type.value for campaign in campaigns)
        
        # Count by threat actor
        actor_counts = Counter(
            campaign.threat_actor.value for campaign in campaigns 
            if campaign.threat_actor
        )
        
        # Calculate active campaigns (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        active_campaigns = sum(1 for campaign in campaigns if campaign.last_seen >= cutoff)
        
        # Calculate average duration
        durations = [(campaign.last_seen - campaign.first_seen).total_seconds() 
                    for campaign in campaigns]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Total events
        total_events = sum(len(campaign.events) for campaign in campaigns)
        
        return {
            'total_campaigns': len(campaigns),
            'active_campaigns': active_campaigns,
            'campaign_types': dict(type_counts),
            'threat_actors': dict(actor_counts),
            'avg_campaign_duration': avg_duration,
            'total_events': total_events
        }