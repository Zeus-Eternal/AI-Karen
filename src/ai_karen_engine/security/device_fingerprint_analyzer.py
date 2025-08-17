"""
Device Fingerprint Analyzer for intelligent authentication system.

This module provides device identification, tracking, and pattern learning
for enhanced authentication security.
"""

import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
try:
    from user_agents import parse as parse_user_agent
    USER_AGENTS_AVAILABLE = True
except ImportError:
    parse_user_agent = None
    USER_AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Types of devices."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    BOT = "bot"
    UNKNOWN = "unknown"


class DeviceRiskLevel(Enum):
    """Device-based risk levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DeviceFingerprint:
    """Device fingerprint information."""
    fingerprint_id: str
    user_agent: str
    browser_family: str
    browser_version: str
    os_family: str
    os_version: str
    device_family: str
    device_type: DeviceType
    is_mobile: bool
    is_tablet: bool
    is_bot: bool
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    plugins: List[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'fingerprint_id': self.fingerprint_id,
            'user_agent': self.user_agent,
            'browser_family': self.browser_family,
            'browser_version': self.browser_version,
            'os_family': self.os_family,
            'os_version': self.os_version,
            'device_family': self.device_family,
            'device_type': self.device_type.value,
            'is_mobile': self.is_mobile,
            'is_tablet': self.is_tablet,
            'is_bot': self.is_bot,
            'screen_resolution': self.screen_resolution,
            'timezone': self.timezone,
            'language': self.language,
            'plugins': self.plugins,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceFingerprint':
        """Create instance from dictionary."""
        return cls(
            fingerprint_id=data['fingerprint_id'],
            user_agent=data['user_agent'],
            browser_family=data['browser_family'],
            browser_version=data['browser_version'],
            os_family=data['os_family'],
            os_version=data['os_version'],
            device_family=data['device_family'],
            device_type=DeviceType(data['device_type']),
            is_mobile=data['is_mobile'],
            is_tablet=data['is_tablet'],
            is_bot=data['is_bot'],
            screen_resolution=data.get('screen_resolution'),
            timezone=data.get('timezone'),
            language=data.get('language'),
            plugins=data.get('plugins', []),
            first_seen=datetime.fromisoformat(data['first_seen']),
            last_seen=datetime.fromisoformat(data['last_seen'])
        )


@dataclass
class DeviceAnalysisResult:
    """Result of device analysis."""
    device_fingerprint: DeviceFingerprint
    is_known_device: bool
    device_similarity_score: float  # 0.0 to 1.0
    risk_level: DeviceRiskLevel
    risk_score: float  # 0.0 to 1.0
    is_suspicious_user_agent: bool = False
    user_agent_anomalies: List[str] = field(default_factory=list)
    device_change_detected: bool = False
    new_device_for_user: bool = False
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'device_fingerprint': self.device_fingerprint.to_dict(),
            'is_known_device': self.is_known_device,
            'device_similarity_score': self.device_similarity_score,
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'is_suspicious_user_agent': self.is_suspicious_user_agent,
            'user_agent_anomalies': self.user_agent_anomalies,
            'device_change_detected': self.device_change_detected,
            'new_device_for_user': self.new_device_for_user,
            'additional_info': self.additional_info
        }


@dataclass
class UserDeviceProfile:
    """User's device profile for pattern learning."""
    user_id: str
    known_devices: Dict[str, DeviceFingerprint] = field(default_factory=dict)
    primary_device: Optional[str] = None  # fingerprint_id of primary device
    device_usage_patterns: Dict[str, int] = field(default_factory=dict)  # fingerprint_id -> usage_count
    last_device_used: Optional[str] = None
    device_change_frequency: float = 0.0  # Average days between device changes
    suspicious_devices: Set[str] = field(default_factory=set)  # fingerprint_ids
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_id': self.user_id,
            'known_devices': {k: v.to_dict() for k, v in self.known_devices.items()},
            'primary_device': self.primary_device,
            'device_usage_patterns': self.device_usage_patterns,
            'last_device_used': self.last_device_used,
            'device_change_frequency': self.device_change_frequency,
            'suspicious_devices': list(self.suspicious_devices)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserDeviceProfile':
        """Create instance from dictionary."""
        profile = cls(user_id=data['user_id'])
        profile.known_devices = {
            k: DeviceFingerprint.from_dict(v) 
            for k, v in data.get('known_devices', {}).items()
        }
        profile.primary_device = data.get('primary_device')
        profile.device_usage_patterns = data.get('device_usage_patterns', {})
        profile.last_device_used = data.get('last_device_used')
        profile.device_change_frequency = data.get('device_change_frequency', 0.0)
        profile.suspicious_devices = set(data.get('suspicious_devices', []))
        return profile


class UserAgentAnalyzer:
    """Analyzer for user agent strings."""
    
    def __init__(self):
        # Suspicious user agent patterns
        self.suspicious_patterns = [
            r'(?i)curl',
            r'(?i)wget',
            r'(?i)python',
            r'(?i)java',
            r'(?i)perl',
            r'(?i)ruby',
            r'(?i)php',
            r'(?i)bot',
            r'(?i)crawler',
            r'(?i)spider',
            r'(?i)scraper',
            r'(?i)scanner',
            r'(?i)sqlmap',
            r'(?i)nikto',
            r'(?i)nessus',
            r'(?i)openvas',
            r'(?i)w3af',
            r'(?i)burp',
            r'(?i)nmap',
            r'(?i)masscan'
        ]
        
        # Common legitimate user agents (for validation)
        self.common_browsers = {
            'chrome', 'firefox', 'safari', 'edge', 'opera', 
            'internet explorer', 'ie'
        }
    
    def analyze_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Analyze user agent string for anomalies."""
        result = {
            'is_suspicious': False,
            'anomalies': [],
            'parsed_info': {},
            'risk_score': 0.0
        }
        
        # Parse user agent
        if USER_AGENTS_AVAILABLE:
            try:
                parsed = parse_user_agent(user_agent)
                result['parsed_info'] = {
                    'browser_family': parsed.browser.family,
                    'browser_version': parsed.browser.version_string,
                    'os_family': parsed.os.family,
                    'os_version': parsed.os.version_string,
                    'device_family': parsed.device.family,
                    'is_mobile': parsed.is_mobile,
                    'is_tablet': parsed.is_tablet,
                    'is_bot': parsed.is_bot
                }
            except Exception as e:
                result['anomalies'].append(f"Failed to parse user agent: {e}")
                result['risk_score'] += 0.3
        else:
            # Fallback parsing when user_agents library is not available
            result['parsed_info'] = self._fallback_parse_user_agent(user_agent)
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, user_agent):
                result['is_suspicious'] = True
                result['anomalies'].append(f"Matches suspicious pattern: {pattern}")
                result['risk_score'] += 0.4
        
        # Check for empty or very short user agent
        if not user_agent or len(user_agent.strip()) < 10:
            result['anomalies'].append("User agent is empty or too short")
            result['risk_score'] += 0.3
        
        # Check for very long user agent (potential obfuscation)
        if len(user_agent) > 1000:
            result['anomalies'].append("User agent is unusually long")
            result['risk_score'] += 0.2
        
        # Check for unusual characters
        if re.search(r'[^\x20-\x7E]', user_agent):
            result['anomalies'].append("Contains non-ASCII characters")
            result['risk_score'] += 0.2
        
        # Check if browser is recognized
        if result['parsed_info']:
            browser_family = result['parsed_info']['browser_family'].lower()
            if browser_family not in self.common_browsers and not result['parsed_info']['is_bot']:
                result['anomalies'].append(f"Uncommon browser: {browser_family}")
                result['risk_score'] += 0.1
        
        # Normalize risk score
        result['risk_score'] = min(result['risk_score'], 1.0)
        
        return result
    
    def _fallback_parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Fallback user agent parsing when user_agents library is not available."""
        result = {
            'browser_family': 'Unknown',
            'browser_version': 'Unknown',
            'os_family': 'Unknown',
            'os_version': 'Unknown',
            'device_family': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_bot': False
        }
        
        ua_lower = user_agent.lower()
        
        # Basic browser detection
        if 'chrome' in ua_lower and 'edg' not in ua_lower:  # Exclude Edge
            result['browser_family'] = 'Chrome'
            # Try to extract version
            match = re.search(r'chrome/(\d+\.\d+)', ua_lower)
            if match:
                result['browser_version'] = match.group(1)
        elif 'firefox' in ua_lower:
            result['browser_family'] = 'Firefox'
            match = re.search(r'firefox/(\d+\.\d+)', ua_lower)
            if match:
                result['browser_version'] = match.group(1)
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            # Check if it's mobile Safari
            if 'mobile' in ua_lower and ('iphone' in ua_lower or 'ipad' in ua_lower):
                result['browser_family'] = 'Mobile Safari'
            else:
                result['browser_family'] = 'Safari'
            match = re.search(r'version/(\d+\.\d+)', ua_lower)
            if match:
                result['browser_version'] = match.group(1)
        elif 'edge' in ua_lower or 'edg' in ua_lower:
            result['browser_family'] = 'Edge'
            match = re.search(r'edg?e?/(\d+\.\d+)', ua_lower)
            if match:
                result['browser_version'] = match.group(1)
        
        # Basic OS detection (order matters - check iOS before Mac OS X)
        if 'iphone' in ua_lower or 'ipad' in ua_lower or ('cpu iphone os' in ua_lower):
            result['os_family'] = 'iOS'
            if 'ipad' in ua_lower:
                result['is_tablet'] = True
                result['device_family'] = 'iPad'
            else:
                result['is_mobile'] = True
                result['device_family'] = 'iPhone'
            # Look for iOS version patterns
            match = re.search(r'os (\d+[._]\d+)', ua_lower)
            if not match:
                match = re.search(r'cpu iphone os (\d+[._]\d+)', ua_lower)
            if match:
                result['os_version'] = match.group(1).replace('_', '.')
        elif 'android' in ua_lower:
            result['os_family'] = 'Android'
            result['is_mobile'] = True
            match = re.search(r'android (\d+\.\d+)', ua_lower)
            if match:
                result['os_version'] = match.group(1)
        elif 'windows' in ua_lower:
            result['os_family'] = 'Windows'
            if 'windows nt 10' in ua_lower:
                result['os_version'] = '10'
            elif 'windows nt 6.3' in ua_lower:
                result['os_version'] = '8.1'
            elif 'windows nt 6.1' in ua_lower:
                result['os_version'] = '7'
        elif 'mac os x' in ua_lower or 'macos' in ua_lower:
            result['os_family'] = 'Mac OS X'
            match = re.search(r'mac os x (\d+[._]\d+)', ua_lower)
            if match:
                result['os_version'] = match.group(1).replace('_', '.')
        elif 'linux' in ua_lower:
            result['os_family'] = 'Linux'
        
        # Basic bot detection
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
        if any(indicator in ua_lower for indicator in bot_indicators):
            result['is_bot'] = True
        
        # Mobile detection (additional patterns)
        mobile_indicators = ['mobile', 'phone', 'android', 'iphone']
        if any(indicator in ua_lower for indicator in mobile_indicators) and not result['is_tablet']:
            result['is_mobile'] = True
        
        # Tablet detection (additional patterns)
        tablet_indicators = ['tablet', 'ipad']
        if any(indicator in ua_lower for indicator in tablet_indicators):
            result['is_tablet'] = True
            result['is_mobile'] = False  # Tablets are not mobile phones
        
        return result


class DeviceFingerprintAnalyzer:
    """Main device fingerprint analyzer."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ua_analyzer = UserAgentAnalyzer()
        self.user_profiles: Dict[str, UserDeviceProfile] = {}
        self.device_database: Dict[str, DeviceFingerprint] = {}
        
        # Load profiles and device database
        self.persistence_file = config.get('persistence_file', 'data/intelligent_auth/device_profiles.json')
        self._load_data()
    
    def _load_data(self):
        """Load user profiles and device database from persistence file."""
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
                
                # Load user profiles
                for user_id, profile_data in data.get('user_profiles', {}).items():
                    self.user_profiles[user_id] = UserDeviceProfile.from_dict(profile_data)
                
                # Load device database
                for fingerprint_id, device_data in data.get('device_database', {}).items():
                    self.device_database[fingerprint_id] = DeviceFingerprint.from_dict(device_data)
                
            logger.info(f"Loaded {len(self.user_profiles)} user device profiles and {len(self.device_database)} devices")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.info(f"No existing device data found: {e}")
    
    def _save_data(self):
        """Save user profiles and device database to persistence file."""
        try:
            import os
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            
            data = {
                'user_profiles': {
                    user_id: profile.to_dict() 
                    for user_id, profile in self.user_profiles.items()
                },
                'device_database': {
                    fingerprint_id: device.to_dict()
                    for fingerprint_id, device in self.device_database.items()
                }
            }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved device data for {len(self.user_profiles)} users")
        except Exception as e:
            logger.error(f"Could not save device data: {e}")
    
    def generate_device_fingerprint(self, 
                                  user_agent: str,
                                  additional_info: Optional[Dict[str, Any]] = None) -> DeviceFingerprint:
        """Generate device fingerprint from user agent and additional info."""
        # Analyze user agent
        ua_analysis = self.ua_analyzer.analyze_user_agent(user_agent)
        parsed_info = ua_analysis['parsed_info']
        
        # Create fingerprint components
        fingerprint_components = [
            user_agent,
            parsed_info.get('browser_family', ''),
            parsed_info.get('browser_version', ''),
            parsed_info.get('os_family', ''),
            parsed_info.get('os_version', ''),
            parsed_info.get('device_family', '')
        ]
        
        # Add additional info if available
        if additional_info:
            fingerprint_components.extend([
                additional_info.get('screen_resolution', ''),
                additional_info.get('timezone', ''),
                additional_info.get('language', ''),
                ','.join(sorted(additional_info.get('plugins', [])))
            ])
        
        # Generate fingerprint ID
        fingerprint_string = '|'.join(fingerprint_components)
        fingerprint_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
        
        # Determine device type
        if parsed_info.get('is_mobile'):
            device_type = DeviceType.MOBILE
        elif parsed_info.get('is_tablet'):
            device_type = DeviceType.TABLET
        elif parsed_info.get('is_bot'):
            device_type = DeviceType.BOT
        else:
            device_type = DeviceType.DESKTOP
        
        # Create device fingerprint
        fingerprint = DeviceFingerprint(
            fingerprint_id=fingerprint_id,
            user_agent=user_agent,
            browser_family=parsed_info.get('browser_family', 'Unknown'),
            browser_version=parsed_info.get('browser_version', 'Unknown'),
            os_family=parsed_info.get('os_family', 'Unknown'),
            os_version=parsed_info.get('os_version', 'Unknown'),
            device_family=parsed_info.get('device_family', 'Unknown'),
            device_type=device_type,
            is_mobile=parsed_info.get('is_mobile', False),
            is_tablet=parsed_info.get('is_tablet', False),
            is_bot=parsed_info.get('is_bot', False),
            screen_resolution=additional_info.get('screen_resolution') if additional_info else None,
            timezone=additional_info.get('timezone') if additional_info else None,
            language=additional_info.get('language') if additional_info else None,
            plugins=additional_info.get('plugins', []) if additional_info else []
        )
        
        return fingerprint
    
    def analyze_device(self, 
                      user_id: str,
                      user_agent: str,
                      additional_info: Optional[Dict[str, Any]] = None) -> DeviceAnalysisResult:
        """Analyze device for authentication attempt."""
        # Generate device fingerprint
        device_fingerprint = self.generate_device_fingerprint(user_agent, additional_info)
        
        # Analyze user agent for suspicious patterns
        ua_analysis = self.ua_analyzer.analyze_user_agent(user_agent)
        
        # Get or create user profile
        user_profile = self._get_user_profile(user_id)
        
        # Check if device is known
        is_known_device = device_fingerprint.fingerprint_id in user_profile.known_devices
        
        # Calculate device similarity score
        device_similarity_score = self._calculate_device_similarity(device_fingerprint, user_profile)
        
        # Detect device changes
        device_change_detected = self._detect_device_change(device_fingerprint, user_profile)
        
        # Check if this is a new device for the user
        new_device_for_user = device_fingerprint.fingerprint_id not in user_profile.known_devices
        
        # Calculate risk score
        risk_score = self._calculate_device_risk_score(
            device_fingerprint,
            ua_analysis,
            user_profile,
            is_known_device,
            device_similarity_score,
            device_change_detected
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Update user profile and device database
        self._update_user_profile(user_profile, device_fingerprint)
        self._update_device_database(device_fingerprint)
        
        # Create result
        result = DeviceAnalysisResult(
            device_fingerprint=device_fingerprint,
            is_known_device=is_known_device,
            device_similarity_score=device_similarity_score,
            risk_level=risk_level,
            risk_score=risk_score,
            is_suspicious_user_agent=ua_analysis['is_suspicious'],
            user_agent_anomalies=ua_analysis['anomalies'],
            device_change_detected=device_change_detected,
            new_device_for_user=new_device_for_user,
            additional_info={
                'user_agent_risk_score': ua_analysis['risk_score'],
                'known_devices_count': len(user_profile.known_devices),
                'device_usage_count': user_profile.device_usage_patterns.get(device_fingerprint.fingerprint_id, 0)
            }
        )
        
        return result
    
    def _get_user_profile(self, user_id: str) -> UserDeviceProfile:
        """Get or create user device profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserDeviceProfile(user_id=user_id)
        return self.user_profiles[user_id]
    
    def _calculate_device_similarity(self, 
                                   device: DeviceFingerprint, 
                                   profile: UserDeviceProfile) -> float:
        """Calculate similarity score between device and user's known devices."""
        if not profile.known_devices:
            return 0.0
        
        max_similarity = 0.0
        
        for known_device in profile.known_devices.values():
            similarity = self._calculate_fingerprint_similarity(device, known_device)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_fingerprint_similarity(self, 
                                        device1: DeviceFingerprint, 
                                        device2: DeviceFingerprint) -> float:
        """Calculate similarity between two device fingerprints."""
        # If it's the exact same fingerprint ID, return perfect match
        if device1.fingerprint_id == device2.fingerprint_id:
            return 1.0
        
        similarity_score = 0.0
        
        # Browser family (30% weight)
        if device1.browser_family == device2.browser_family:
            similarity_score += 0.3
        
        # OS family (25% weight)
        if device1.os_family == device2.os_family:
            similarity_score += 0.25
        
        # Device family (20% weight)
        if device1.device_family == device2.device_family:
            similarity_score += 0.2
        
        # Device type (15% weight)
        if device1.device_type == device2.device_type:
            similarity_score += 0.15
        
        # Screen resolution (5% weight)
        if device1.screen_resolution and device2.screen_resolution:
            if device1.screen_resolution == device2.screen_resolution:
                similarity_score += 0.05
        elif not device1.screen_resolution and not device2.screen_resolution:
            # Both have no screen resolution info, consider it a match
            similarity_score += 0.05
        
        # Timezone (3% weight)
        if device1.timezone and device2.timezone:
            if device1.timezone == device2.timezone:
                similarity_score += 0.03
        elif not device1.timezone and not device2.timezone:
            # Both have no timezone info, consider it a match
            similarity_score += 0.03
        
        # Language (2% weight)
        if device1.language and device2.language:
            if device1.language == device2.language:
                similarity_score += 0.02
        elif not device1.language and not device2.language:
            # Both have no language info, consider it a match
            similarity_score += 0.02
        
        return similarity_score
    
    def _detect_device_change(self, 
                            device: DeviceFingerprint, 
                            profile: UserDeviceProfile) -> bool:
        """Detect if user has changed devices."""
        if not profile.last_device_used:
            return False
        
        return device.fingerprint_id != profile.last_device_used
    
    def _calculate_device_risk_score(self,
                                   device: DeviceFingerprint,
                                   ua_analysis: Dict[str, Any],
                                   profile: UserDeviceProfile,
                                   is_known_device: bool,
                                   similarity_score: float,
                                   device_change_detected: bool) -> float:
        """Calculate overall device risk score."""
        risk_score = 0.0
        
        # User agent risk
        risk_score += ua_analysis['risk_score'] * 0.4
        
        # Unknown device risk
        if not is_known_device:
            risk_score += 0.3
        
        # Low similarity risk
        if similarity_score < 0.5:
            risk_score += (0.5 - similarity_score) * 0.4
        
        # Device change risk (if frequent changes)
        if device_change_detected and profile.device_change_frequency > 0:
            # Higher risk if user rarely changes devices
            if profile.device_change_frequency > 30:  # Changes device less than once per month
                risk_score += 0.2
        
        # Bot detection
        if device.is_bot:
            risk_score += 0.5
        
        # Suspicious device in profile
        if device.fingerprint_id in profile.suspicious_devices:
            risk_score += 0.3
        
        # Normalize risk score
        return min(risk_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> DeviceRiskLevel:
        """Determine risk level from risk score."""
        if risk_score >= 0.8:
            return DeviceRiskLevel.VERY_HIGH
        elif risk_score >= 0.6:
            return DeviceRiskLevel.HIGH
        elif risk_score >= 0.4:
            return DeviceRiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return DeviceRiskLevel.LOW
        else:
            return DeviceRiskLevel.VERY_LOW
    
    def _update_user_profile(self, profile: UserDeviceProfile, device: DeviceFingerprint):
        """Update user device profile with new device information."""
        # Add or update device in known devices
        if device.fingerprint_id in profile.known_devices:
            # Update last seen time
            profile.known_devices[device.fingerprint_id].last_seen = device.last_seen
        else:
            # Add new device
            profile.known_devices[device.fingerprint_id] = device
        
        # Update usage patterns
        profile.device_usage_patterns[device.fingerprint_id] = \
            profile.device_usage_patterns.get(device.fingerprint_id, 0) + 1
        
        # Update primary device (most used device)
        if not profile.primary_device or \
           profile.device_usage_patterns[device.fingerprint_id] > \
           profile.device_usage_patterns.get(profile.primary_device, 0):
            profile.primary_device = device.fingerprint_id
        
        # Calculate device change frequency
        if profile.last_device_used and profile.last_device_used != device.fingerprint_id:
            # Simple approximation - in production, would track actual time between changes
            profile.device_change_frequency = max(1.0, profile.device_change_frequency * 0.9 + 1.0 * 0.1)
        
        # Update last device used
        profile.last_device_used = device.fingerprint_id
        
        # Clean up old devices (keep only last 20 devices per user)
        if len(profile.known_devices) > 20:
            # Remove least used devices
            sorted_devices = sorted(
                profile.device_usage_patterns.items(),
                key=lambda x: x[1]
            )
            devices_to_remove = [device_id for device_id, _ in sorted_devices[:-20]]
            
            for device_id in devices_to_remove:
                profile.known_devices.pop(device_id, None)
                profile.device_usage_patterns.pop(device_id, None)
        
        # Save data periodically
        self._save_data()
    
    def _update_device_database(self, device: DeviceFingerprint):
        """Update global device database."""
        if device.fingerprint_id in self.device_database:
            # Update last seen time
            self.device_database[device.fingerprint_id].last_seen = device.last_seen
        else:
            # Add new device to database
            self.device_database[device.fingerprint_id] = device
    
    def mark_device_suspicious(self, user_id: str, fingerprint_id: str):
        """Mark a device as suspicious for a user."""
        profile = self._get_user_profile(user_id)
        profile.suspicious_devices.add(fingerprint_id)
        self._save_data()
    
    def get_user_device_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get device statistics for a user."""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {'error': 'User profile not found'}
        
        # Calculate device type distribution
        device_types = defaultdict(int)
        for device in profile.known_devices.values():
            device_types[device.device_type.value] += 1
        
        # Calculate browser distribution
        browsers = defaultdict(int)
        for device in profile.known_devices.values():
            browsers[device.browser_family] += 1
        
        # Calculate OS distribution
        operating_systems = defaultdict(int)
        for device in profile.known_devices.values():
            operating_systems[device.os_family] += 1
        
        return {
            'user_id': user_id,
            'total_devices': len(profile.known_devices),
            'primary_device': profile.primary_device,
            'device_change_frequency': profile.device_change_frequency,
            'suspicious_devices_count': len(profile.suspicious_devices),
            'device_types': dict(device_types),
            'browsers': dict(browsers),
            'operating_systems': dict(operating_systems),
            'most_used_devices': sorted(
                profile.device_usage_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def get_global_device_statistics(self) -> Dict[str, Any]:
        """Get global device statistics."""
        device_types = defaultdict(int)
        browsers = defaultdict(int)
        operating_systems = defaultdict(int)
        
        for device in self.device_database.values():
            device_types[device.device_type.value] += 1
            browsers[device.browser_family] += 1
            operating_systems[device.os_family] += 1
        
        return {
            'total_devices': len(self.device_database),
            'total_users': len(self.user_profiles),
            'device_types': dict(device_types),
            'top_browsers': sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_operating_systems': sorted(operating_systems.items(), key=lambda x: x[1], reverse=True)[:10]
        }