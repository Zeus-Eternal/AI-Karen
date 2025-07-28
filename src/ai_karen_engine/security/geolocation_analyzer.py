"""
Geolocation Analyzer for intelligent authentication system.

This module provides geolocation-based risk assessment, VPN/Tor detection,
and location pattern learning for users.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
from ipaddress import ip_address, ip_network, AddressValueError
import aiohttp
from cachetools import TTLCache
try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    geoip2 = None
    GEOIP2_AVAILABLE = False

from .models import AuthContext, GeoLocation

logger = logging.getLogger(__name__)


class LocationRiskLevel(Enum):
    """Location-based risk levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConnectionType(Enum):
    """Types of network connections."""
    RESIDENTIAL = "residential"
    BUSINESS = "business"
    MOBILE = "mobile"
    HOSTING = "hosting"
    VPN = "vpn"
    TOR = "tor"
    PROXY = "proxy"
    UNKNOWN = "unknown"


@dataclass
class LocationAnalysisResult:
    """Result of location analysis."""
    geolocation: GeoLocation
    connection_type: ConnectionType
    risk_level: LocationRiskLevel
    risk_score: float  # 0.0 to 1.0
    is_vpn: bool = False
    is_tor: bool = False
    is_proxy: bool = False
    is_usual_location: bool = False
    distance_from_usual: Optional[float] = None  # km
    velocity_anomaly: Optional[float] = None  # km/h if previous location known
    high_risk_country: bool = False
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'geolocation': self.geolocation.to_dict(),
            'connection_type': self.connection_type.value,
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'is_vpn': self.is_vpn,
            'is_tor': self.is_tor,
            'is_proxy': self.is_proxy,
            'is_usual_location': self.is_usual_location,
            'distance_from_usual': self.distance_from_usual,
            'velocity_anomaly': self.velocity_anomaly,
            'high_risk_country': self.high_risk_country,
            'additional_info': self.additional_info
        }


@dataclass
class UserLocationProfile:
    """User's location profile for pattern learning."""
    user_id: str
    usual_locations: List[GeoLocation] = field(default_factory=list)
    usual_countries: Set[str] = field(default_factory=set)
    usual_timezones: Set[str] = field(default_factory=set)
    last_known_location: Optional[GeoLocation] = None
    last_login_time: Optional[datetime] = None
    location_history: List[Tuple[GeoLocation, datetime]] = field(default_factory=list)
    max_velocity_observed: float = 0.0  # km/h
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_id': self.user_id,
            'usual_locations': [loc.to_dict() for loc in self.usual_locations],
            'usual_countries': list(self.usual_countries),
            'usual_timezones': list(self.usual_timezones),
            'last_known_location': self.last_known_location.to_dict() if self.last_known_location else None,
            'last_login_time': self.last_login_time.isoformat() if self.last_login_time else None,
            'location_history': [
                (loc.to_dict(), timestamp.isoformat()) 
                for loc, timestamp in self.location_history
            ],
            'max_velocity_observed': self.max_velocity_observed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserLocationProfile':
        """Create instance from dictionary."""
        profile = cls(user_id=data['user_id'])
        profile.usual_locations = [GeoLocation.from_dict(loc) for loc in data.get('usual_locations', [])]
        profile.usual_countries = set(data.get('usual_countries', []))
        profile.usual_timezones = set(data.get('usual_timezones', []))
        
        if data.get('last_known_location'):
            profile.last_known_location = GeoLocation.from_dict(data['last_known_location'])
        
        if data.get('last_login_time'):
            profile.last_login_time = datetime.fromisoformat(data['last_login_time'])
        
        profile.location_history = [
            (GeoLocation.from_dict(loc_data), datetime.fromisoformat(timestamp))
            for loc_data, timestamp in data.get('location_history', [])
        ]
        
        profile.max_velocity_observed = data.get('max_velocity_observed', 0.0)
        
        return profile


class GeoIPService:
    """Service for IP geolocation using multiple providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour cache
        self.session: Optional[aiohttp.ClientSession] = None
        self.geoip_db = None
        
        # Initialize MaxMind GeoIP database if available
        if config.get('maxmind_db_path') and GEOIP2_AVAILABLE:
            try:
                self.geoip_db = geoip2.database.Reader(config['maxmind_db_path'])
                logger.info("MaxMind GeoIP database loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load MaxMind GeoIP database: {e}")
        elif config.get('maxmind_db_path') and not GEOIP2_AVAILABLE:
            logger.warning("MaxMind database path provided but geoip2 library not available")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'AI-Karen-GeoLocation/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        if self.geoip_db:
            self.geoip_db.close()
    
    async def get_location(self, ip: str) -> Optional[GeoLocation]:
        """Get geolocation for IP address."""
        cache_key = f"geo:{ip}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        location = None
        
        # Try MaxMind database first (fastest and most reliable)
        if self.geoip_db:
            location = await self._get_location_maxmind(ip)
        
        # Fallback to online services
        if not location:
            location = await self._get_location_ipapi(ip)
        
        if not location:
            location = await self._get_location_ipinfo(ip)
        
        # Cache result
        if location:
            self.cache[cache_key] = location
        
        return location
    
    async def _get_location_maxmind(self, ip: str) -> Optional[GeoLocation]:
        """Get location using MaxMind GeoIP database."""
        if not GEOIP2_AVAILABLE:
            return None
            
        try:
            response = self.geoip_db.city(ip)
            
            return GeoLocation(
                country=response.country.name or "Unknown",
                region=response.subdivisions.most_specific.name or "Unknown",
                city=response.city.name or "Unknown",
                latitude=float(response.location.latitude or 0.0),
                longitude=float(response.location.longitude or 0.0),
                timezone=response.location.time_zone or "UTC"
            )
            
        except Exception as e:
            logger.debug(f"MaxMind lookup failed for {ip}: {e}")
            return None
    
    async def _get_location_ipapi(self, ip: str) -> Optional[GeoLocation]:
        """Get location using ip-api.com (free service)."""
        try:
            url = f"http://ip-api.com/json/{ip}"
            params = {
                'fields': 'status,country,regionName,city,lat,lon,timezone,query'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        return GeoLocation(
                            country=data.get('country', 'Unknown'),
                            region=data.get('regionName', 'Unknown'),
                            city=data.get('city', 'Unknown'),
                            latitude=float(data.get('lat', 0.0)),
                            longitude=float(data.get('lon', 0.0)),
                            timezone=data.get('timezone', 'UTC')
                        )
                        
        except Exception as e:
            logger.debug(f"ip-api lookup failed for {ip}: {e}")
        
        return None
    
    async def _get_location_ipinfo(self, ip: str) -> Optional[GeoLocation]:
        """Get location using ipinfo.io."""
        if not self.config.get('ipinfo_token'):
            return None
        
        try:
            url = f"https://ipinfo.io/{ip}/json"
            headers = {
                'Authorization': f"Bearer {self.config['ipinfo_token']}"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse location data
                    loc = data.get('loc', '0,0').split(',')
                    latitude = float(loc[0]) if len(loc) > 0 else 0.0
                    longitude = float(loc[1]) if len(loc) > 1 else 0.0
                    
                    return GeoLocation(
                        country=data.get('country', 'Unknown'),
                        region=data.get('region', 'Unknown'),
                        city=data.get('city', 'Unknown'),
                        latitude=latitude,
                        longitude=longitude,
                        timezone=data.get('timezone', 'UTC')
                    )
                    
        except Exception as e:
            logger.debug(f"ipinfo lookup failed for {ip}: {e}")
        
        return None


class VPNTorDetector:
    """Detector for VPN, Tor, and proxy connections."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = TTLCache(maxsize=5000, ttl=1800)  # 30 minute cache
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Known Tor exit nodes (would be updated regularly in production)
        self.tor_exit_nodes: Set[str] = set()
        
        # Known VPN/proxy IP ranges
        self.vpn_ranges: List[ip_network] = []
        
        # Load static lists if available
        self._load_static_lists()
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'AI-Karen-VPNDetector/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _load_static_lists(self):
        """Load static VPN/Tor lists from configuration."""
        # Load Tor exit nodes
        tor_file = self.config.get('tor_exit_nodes_file')
        if tor_file:
            try:
                with open(tor_file, 'r') as f:
                    self.tor_exit_nodes = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.tor_exit_nodes)} Tor exit nodes")
            except Exception as e:
                logger.warning(f"Could not load Tor exit nodes: {e}")
        
        # Load VPN ranges
        vpn_file = self.config.get('vpn_ranges_file')
        if vpn_file:
            try:
                with open(vpn_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                self.vpn_ranges.append(ip_network(line))
                            except ValueError:
                                pass
                logger.info(f"Loaded {len(self.vpn_ranges)} VPN ranges")
            except Exception as e:
                logger.warning(f"Could not load VPN ranges: {e}")
    
    async def analyze_connection(self, ip: str) -> Dict[str, Any]:
        """Analyze connection type for IP address."""
        cache_key = f"conn:{ip}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = {
            'is_tor': False,
            'is_vpn': False,
            'is_proxy': False,
            'connection_type': ConnectionType.UNKNOWN,
            'confidence': 0.0,
            'sources': []
        }
        
        # Check static lists first
        if ip in self.tor_exit_nodes:
            result['is_tor'] = True
            result['connection_type'] = ConnectionType.TOR
            result['confidence'] = 0.95
            result['sources'].append('static_tor_list')
        
        # Check VPN ranges
        try:
            ip_obj = ip_address(ip)
            for vpn_range in self.vpn_ranges:
                if ip_obj in vpn_range:
                    result['is_vpn'] = True
                    result['connection_type'] = ConnectionType.VPN
                    result['confidence'] = max(result['confidence'], 0.8)
                    result['sources'].append('static_vpn_ranges')
                    break
        except AddressValueError:
            pass
        
        # Check online services if not already detected
        if not any([result['is_tor'], result['is_vpn'], result['is_proxy']]):
            # Check VPN detection services
            vpn_result = await self._check_vpn_services(ip)
            if vpn_result:
                result.update(vpn_result)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    async def _check_vpn_services(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check VPN detection services."""
        # Check IPQualityScore if API key available
        if self.config.get('ipqualityscore_api_key'):
            return await self._check_ipqualityscore(ip)
        
        # Check ProxyCheck.io if API key available
        if self.config.get('proxycheck_api_key'):
            return await self._check_proxycheck(ip)
        
        return None
    
    async def _check_ipqualityscore(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check IPQualityScore for VPN/proxy detection."""
        try:
            url = f"https://ipqualityscore.com/api/json/ip/{self.config['ipqualityscore_api_key']}/{ip}"
            params = {
                'strictness': 1,
                'allow_public_access_points': True,
                'fast': True
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success'):
                        result = {
                            'is_tor': data.get('tor', False),
                            'is_vpn': data.get('vpn', False),
                            'is_proxy': data.get('proxy', False),
                            'confidence': data.get('fraud_score', 0) / 100.0,
                            'sources': ['ipqualityscore']
                        }
                        
                        # Determine connection type
                        if result['is_tor']:
                            result['connection_type'] = ConnectionType.TOR
                        elif result['is_vpn']:
                            result['connection_type'] = ConnectionType.VPN
                        elif result['is_proxy']:
                            result['connection_type'] = ConnectionType.PROXY
                        else:
                            # Determine based on ISP type
                            isp_type = data.get('ISP', '').lower()
                            if 'hosting' in isp_type or 'datacenter' in isp_type:
                                result['connection_type'] = ConnectionType.HOSTING
                            elif 'mobile' in isp_type:
                                result['connection_type'] = ConnectionType.MOBILE
                            else:
                                result['connection_type'] = ConnectionType.RESIDENTIAL
                        
                        return result
                        
        except Exception as e:
            logger.debug(f"IPQualityScore check failed for {ip}: {e}")
        
        return None
    
    async def _check_proxycheck(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check ProxyCheck.io for proxy detection."""
        try:
            url = f"https://proxycheck.io/v2/{ip}"
            params = {
                'key': self.config['proxycheck_api_key'],
                'vpn': 1,
                'asn': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'ok' and ip in data:
                        ip_data = data[ip]
                        
                        result = {
                            'is_tor': False,  # ProxyCheck doesn't specifically detect Tor
                            'is_vpn': ip_data.get('vpn') == 'yes',
                            'is_proxy': ip_data.get('proxy') == 'yes',
                            'confidence': 0.8,  # ProxyCheck is generally reliable
                            'sources': ['proxycheck']
                        }
                        
                        # Determine connection type
                        if result['is_vpn']:
                            result['connection_type'] = ConnectionType.VPN
                        elif result['is_proxy']:
                            result['connection_type'] = ConnectionType.PROXY
                        else:
                            result['connection_type'] = ConnectionType.RESIDENTIAL
                        
                        return result
                        
        except Exception as e:
            logger.debug(f"ProxyCheck check failed for {ip}: {e}")
        
        return None


class GeoLocationAnalyzer:
    """Main geolocation analyzer for location-based risk assessment."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.geoip_service = GeoIPService(config.get('geoip', {}))
        self.vpn_detector = VPNTorDetector(config.get('vpn_detection', {}))
        self.user_profiles: Dict[str, UserLocationProfile] = {}
        
        # High-risk countries (configurable)
        self.high_risk_countries = set(config.get('high_risk_countries', [
            'CN', 'RU', 'KP', 'IR'  # Example - adjust based on your threat model
        ]))
        
        # Load user profiles if persistence file exists
        self.persistence_file = config.get('persistence_file', 'data/intelligent_auth/user_location_profiles.json')
        self._load_user_profiles()
    
    def _load_user_profiles(self):
        """Load user location profiles from persistence file."""
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
                for user_id, profile_data in data.items():
                    self.user_profiles[user_id] = UserLocationProfile.from_dict(profile_data)
            logger.info(f"Loaded {len(self.user_profiles)} user location profiles")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.info(f"No existing user location profiles found: {e}")
    
    def _save_user_profiles(self):
        """Save user location profiles to persistence file."""
        try:
            import os
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            
            data = {
                user_id: profile.to_dict() 
                for user_id, profile in self.user_profiles.items()
            }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.user_profiles)} user location profiles")
        except Exception as e:
            logger.error(f"Could not save user location profiles: {e}")
    
    async def analyze_location(self, context: AuthContext) -> LocationAnalysisResult:
        """Analyze location-based risk for authentication attempt."""
        async with self.geoip_service, self.vpn_detector:
            # Get geolocation
            geolocation = await self.geoip_service.get_location(context.client_ip)
            if not geolocation:
                # Fallback to unknown location
                geolocation = GeoLocation(
                    country="Unknown",
                    region="Unknown", 
                    city="Unknown",
                    latitude=0.0,
                    longitude=0.0,
                    timezone="UTC"
                )
            
            # Analyze connection type
            connection_analysis = await self.vpn_detector.analyze_connection(context.client_ip)
            
            # Get or create user profile
            user_profile = self._get_user_profile(context.email)
            
            # Calculate risk factors
            risk_factors = self._calculate_risk_factors(
                geolocation, 
                connection_analysis, 
                user_profile,
                context
            )
            
            # Update user profile with new location
            self._update_user_profile(user_profile, geolocation, context.timestamp)
            
            # Create result
            result = LocationAnalysisResult(
                geolocation=geolocation,
                connection_type=ConnectionType(connection_analysis['connection_type']),
                risk_level=risk_factors['risk_level'],
                risk_score=risk_factors['risk_score'],
                is_vpn=connection_analysis['is_vpn'],
                is_tor=connection_analysis['is_tor'],
                is_proxy=connection_analysis['is_proxy'],
                is_usual_location=risk_factors['is_usual_location'],
                distance_from_usual=risk_factors['distance_from_usual'],
                velocity_anomaly=risk_factors['velocity_anomaly'],
                high_risk_country=geolocation.country in self.high_risk_countries,
                additional_info={
                    'connection_confidence': connection_analysis['confidence'],
                    'connection_sources': connection_analysis['sources'],
                    'user_location_history_count': len(user_profile.location_history)
                }
            )
            
            return result
    
    def _get_user_profile(self, user_id: str) -> UserLocationProfile:
        """Get or create user location profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserLocationProfile(user_id=user_id)
        return self.user_profiles[user_id]
    
    def _calculate_risk_factors(self, 
                              geolocation: GeoLocation,
                              connection_analysis: Dict[str, Any],
                              user_profile: UserLocationProfile,
                              context: AuthContext) -> Dict[str, Any]:
        """Calculate location-based risk factors."""
        risk_score = 0.0
        risk_factors = {}
        
        # Check if location is usual for user
        is_usual_location = self._is_usual_location(geolocation, user_profile)
        risk_factors['is_usual_location'] = is_usual_location
        
        if not is_usual_location:
            risk_score += 0.3
        
        # Calculate distance from usual locations
        distance_from_usual = self._calculate_distance_from_usual(geolocation, user_profile)
        risk_factors['distance_from_usual'] = distance_from_usual
        
        if distance_from_usual and distance_from_usual > 1000:  # > 1000km
            risk_score += min(distance_from_usual / 10000, 0.4)  # Max 0.4 for distance
        
        # Check velocity anomaly (impossible travel)
        velocity_anomaly = self._calculate_velocity_anomaly(
            geolocation, 
            user_profile, 
            context.timestamp
        )
        risk_factors['velocity_anomaly'] = velocity_anomaly
        
        if velocity_anomaly and velocity_anomaly > 1000:  # > 1000 km/h (impossible)
            risk_score += 0.5
        
        # Connection type risk
        if connection_analysis['is_tor']:
            risk_score += 0.6
        elif connection_analysis['is_vpn']:
            risk_score += 0.4
        elif connection_analysis['is_proxy']:
            risk_score += 0.3
        
        # High-risk country
        if geolocation.country in self.high_risk_countries:
            risk_score += 0.2
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = LocationRiskLevel.VERY_HIGH
        elif risk_score >= 0.6:
            risk_level = LocationRiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = LocationRiskLevel.MEDIUM
        elif risk_score >= 0.2:
            risk_level = LocationRiskLevel.LOW
        else:
            risk_level = LocationRiskLevel.VERY_LOW
        
        risk_factors['risk_score'] = risk_score
        risk_factors['risk_level'] = risk_level
        
        return risk_factors
    
    def _is_usual_location(self, location: GeoLocation, profile: UserLocationProfile) -> bool:
        """Check if location is usual for user."""
        # Check country
        if location.country in profile.usual_countries:
            return True
        
        # Check proximity to usual locations (within 100km)
        for usual_location in profile.usual_locations:
            distance = self._calculate_distance(location, usual_location)
            if distance < 100:  # 100km threshold
                return True
        
        return False
    
    def _calculate_distance_from_usual(self, 
                                     location: GeoLocation, 
                                     profile: UserLocationProfile) -> Optional[float]:
        """Calculate minimum distance from usual locations."""
        if not profile.usual_locations:
            return None
        
        min_distance = float('inf')
        for usual_location in profile.usual_locations:
            distance = self._calculate_distance(location, usual_location)
            min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else None
    
    def _calculate_velocity_anomaly(self, 
                                  location: GeoLocation,
                                  profile: UserLocationProfile,
                                  current_time: datetime) -> Optional[float]:
        """Calculate velocity anomaly (impossible travel detection)."""
        if not profile.last_known_location or not profile.last_login_time:
            return None
        
        # Calculate distance and time difference
        distance = self._calculate_distance(location, profile.last_known_location)
        time_diff = (current_time - profile.last_login_time).total_seconds() / 3600  # hours
        
        if time_diff <= 0:
            return None
        
        # Calculate velocity in km/h
        velocity = distance / time_diff
        
        # Return velocity if it's anomalous (> 800 km/h is impossible for commercial travel)
        return velocity if velocity > 800 else None
    
    def _calculate_distance(self, loc1: GeoLocation, loc2: GeoLocation) -> float:
        """Calculate distance between two locations using Haversine formula."""
        import math
        
        # Convert to radians
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    def _update_user_profile(self, 
                           profile: UserLocationProfile, 
                           location: GeoLocation, 
                           timestamp: datetime):
        """Update user location profile with new location."""
        # Add to location history
        profile.location_history.append((location, timestamp))
        
        # Keep only recent history (last 100 locations)
        if len(profile.location_history) > 100:
            profile.location_history = profile.location_history[-100:]
        
        # Update usual countries and timezones
        profile.usual_countries.add(location.country)
        profile.usual_timezones.add(location.timezone)
        
        # Update usual locations (clustering similar locations)
        self._update_usual_locations(profile, location)
        
        # Update velocity tracking
        if profile.last_known_location and profile.last_login_time:
            distance = self._calculate_distance(location, profile.last_known_location)
            time_diff = (timestamp - profile.last_login_time).total_seconds() / 3600
            
            if time_diff > 0:
                velocity = distance / time_diff
                profile.max_velocity_observed = max(profile.max_velocity_observed, velocity)
        
        # Update last known location and time
        profile.last_known_location = location
        profile.last_login_time = timestamp
        
        # Save profiles periodically
        self._save_user_profiles()
    
    def _update_usual_locations(self, profile: UserLocationProfile, location: GeoLocation):
        """Update usual locations using clustering."""
        # Check if location is close to existing usual locations
        for i, usual_location in enumerate(profile.usual_locations):
            distance = self._calculate_distance(location, usual_location)
            if distance < 50:  # Within 50km, consider it the same location
                # Update the usual location (weighted average)
                weight = 0.1  # Give new location 10% weight
                profile.usual_locations[i] = GeoLocation(
                    country=location.country,  # Use current country
                    region=location.region,    # Use current region
                    city=location.city,        # Use current city
                    latitude=usual_location.latitude * (1 - weight) + location.latitude * weight,
                    longitude=usual_location.longitude * (1 - weight) + location.longitude * weight,
                    timezone=location.timezone  # Use current timezone
                )
                return
        
        # If not close to any existing location, add as new usual location
        profile.usual_locations.append(location)
        
        # Keep only top 10 usual locations (by frequency would be better, but this is simpler)
        if len(profile.usual_locations) > 10:
            profile.usual_locations = profile.usual_locations[-10:]
    
    def get_user_location_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get location statistics for a user."""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {'error': 'User profile not found'}
        
        return {
            'user_id': user_id,
            'usual_locations_count': len(profile.usual_locations),
            'usual_countries': list(profile.usual_countries),
            'usual_timezones': list(profile.usual_timezones),
            'location_history_count': len(profile.location_history),
            'max_velocity_observed': profile.max_velocity_observed,
            'last_known_location': profile.last_known_location.to_dict() if profile.last_known_location else None,
            'last_login_time': profile.last_login_time.isoformat() if profile.last_login_time else None
        }