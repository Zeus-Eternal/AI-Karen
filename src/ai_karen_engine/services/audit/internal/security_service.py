"""
Security Service Helper

This module provides helper functionality for security operations in the KAREN AI system.
It handles security event recording, security monitoring, and other security-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class SecurityServiceHelper:
    """
    Helper service for security operations.
    
    This service provides methods for recording, querying, and analyzing security events
    in the KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the security service helper.
        
        Args:
            config: Configuration dictionary for the security service
        """
        self.config = config
        self.security_enabled = config.get("security_enabled", True)
        self.security_levels = config.get("security_levels", ["INFO", "WARNING", "CRITICAL"])
        self.event_types = config.get("event_types", [
            "authentication", "authorization", "data_access", "data_modification",
            "admin_action", "system_change", "security_violation", "suspicious_activity"
        ])
        self.max_security_records = config.get("max_security_records", 10000)
        self.retention_days = config.get("retention_days", 90)
        self.alert_thresholds = config.get("alert_thresholds", {
            "critical_events_per_hour": 5,
            "failed_logins_per_user": 5,
            "suspicious_activities_per_hour": 10
        })
        self._is_connected = False
        self._security_records = []
        
    async def initialize(self) -> bool:
        """
        Initialize the security service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing security service")
            
            # Initialize security monitoring
            if self.security_enabled:
                await self._initialize_security_monitoring()
                
            self._is_connected = True
            logger.info("Security service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing security service: {str(e)}")
            return False
    
    async def _initialize_security_monitoring(self) -> None:
        """Initialize security monitoring."""
        # In a real implementation, this would set up security monitoring
        logger.info(f"Initializing security monitoring with event types: {self.event_types}")
        
    async def start(self) -> bool:
        """
        Start the security service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting security service")
            
            # Start security monitoring
            if self.security_enabled:
                await self._start_security_monitoring()
                
            logger.info("Security service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting security service: {str(e)}")
            return False
    
    async def _start_security_monitoring(self) -> None:
        """Start security monitoring."""
        # In a real implementation, this would start security monitoring
        logger.info("Starting security monitoring")
        
    async def stop(self) -> bool:
        """
        Stop the security service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping security service")
            
            # Stop security monitoring
            if self.security_enabled:
                await self._stop_security_monitoring()
                
            self._is_connected = False
            self._security_records.clear()
            logger.info("Security service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping security service: {str(e)}")
            return False
    
    async def _stop_security_monitoring(self) -> None:
        """Stop security monitoring."""
        # In a real implementation, this would stop security monitoring
        logger.info("Stopping security monitoring")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the security service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_connected:
                return {"status": "unhealthy", "message": "Security service is not connected"}
                
            # Check security monitoring health
            monitoring_health = {"status": "healthy", "message": "Security monitoring is healthy"}
            if self.security_enabled:
                monitoring_health = await self._health_check_security_monitoring()
                
            # Determine overall health
            overall_status = monitoring_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Security service is {overall_status}",
                "monitoring_health": monitoring_health
            }
            
        except Exception as e:
            logger.error(f"Error checking security service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_security_monitoring(self) -> Dict[str, Any]:
        """Check security monitoring health."""
        # In a real implementation, this would check security monitoring health
        return {"status": "healthy", "message": "Security monitoring is healthy"}
        
    async def record_security_event(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Record a security event.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Check if security is enabled
            if not self.security_enabled:
                return {"status": "success", "message": "Security is disabled"}
                
            # Get event parameters
            event_type = data.get("event_type") if data else None
            security_level = data.get("security_level", "INFO") if data else "INFO"
            user = data.get("user", "unknown_user") if data else "unknown_user"
            resource = data.get("resource", "unknown_resource") if data else "unknown_resource"
            action = data.get("action", "unknown_action") if data else "unknown_action"
            result = data.get("result", "unknown_result") if data else "unknown_result"
            details = data.get("details", {}) if data else {}
            ip_address = data.get("ip_address", "unknown_ip") if data else "unknown_ip"
            user_agent = data.get("user_agent", "unknown_user_agent") if data else "unknown_user_agent"
            session_id = data.get("session_id", "unknown_session") if data else "unknown_session"
            request_id = data.get("request_id", "unknown_request") if data else "unknown_request"
            
            # Validate event type
            if event_type and event_type not in self.event_types:
                return {"status": "error", "message": f"Unsupported event type: {event_type}"}
                
            # Validate security level
            if security_level and security_level not in self.security_levels:
                return {"status": "error", "message": f"Unsupported security level: {security_level}"}
                
            # Create security event record
            event_record = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "security_level": security_level,
                "user": user,
                "resource": resource,
                "action": action,
                "result": result,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id,
                "request_id": request_id,
                "context": context or {}
            }
            
            # Add event record to storage
            self._security_records.append(event_record)
            
            # Check if we need to prune old records
            if len(self._security_records) > self.max_security_records:
                await self._prune_old_records()
                
            # Check for alerts
            alert_triggered = await self._check_for_alerts(event_record)
            
            return {
                "status": "success",
                "message": "Security event recorded successfully",
                "event_id": event_record["event_id"],
                "event_record": event_record,
                "alert_triggered": alert_triggered
            }
            
        except Exception as e:
            logger.error(f"Error recording security event: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _prune_old_records(self) -> None:
        """Prune old security records."""
        # In a real implementation, this would prune old records based on retention policy
        logger.info(f"Pruning old security records, current count: {len(self._security_records)}")
        
        # Sort by timestamp (oldest first)
        self._security_records.sort(key=lambda x: x["timestamp"])
        
        # Keep only the most recent records
        self._security_records = self._security_records[-self.max_security_records:]
        
    async def _check_for_alerts(self, event_record: Dict[str, Any]) -> bool:
        """Check if the event record triggers any alerts."""
        # In a real implementation, this would check if the event record triggers any alerts
        # based on the alert thresholds
        
        # Check for critical events
        if event_record["security_level"] == "CRITICAL":
            # Check if we've exceeded the threshold for critical events per hour
            recent_critical_events = [
                r for r in self._security_records
                if (r["security_level"] == "CRITICAL" and 
                    r["timestamp"] >= event_record["timestamp"] and
                    (datetime.fromisoformat(event_record["timestamp"]) - datetime.fromisoformat(r["timestamp"])).total_seconds() <= 3600)
            ]
            
            if len(recent_critical_events) > self.alert_thresholds["critical_events_per_hour"]:
                logger.warning(f"Critical events threshold exceeded: {len(recent_critical_events)} events in the last hour")
                return True
                
        # Check for failed logins
        if (event_record["event_type"] == "authentication" and 
            event_record["result"] == "failed"):
            
            # Check if we've exceeded the threshold for failed logins per user
            recent_failed_logins = [
                r for r in self._security_records
                if (r["event_type"] == "authentication" and 
                    r["result"] == "failed" and
                    r["user"] == event_record["user"] and
                    r["timestamp"] >= event_record["timestamp"] and
                    (datetime.fromisoformat(event_record["timestamp"]) - datetime.fromisoformat(r["timestamp"])).total_seconds() <= 3600)
            ]
            
            if len(recent_failed_logins) > self.alert_thresholds["failed_logins_per_user"]:
                logger.warning(f"Failed logins threshold exceeded for user {event_record['user']}: {len(recent_failed_logins)} failed logins in the last hour")
                return True
                
        # Check for suspicious activities
        if event_record["event_type"] == "suspicious_activity":
            # Check if we've exceeded the threshold for suspicious activities per hour
            recent_suspicious_activities = [
                r for r in self._security_records
                if (r["event_type"] == "suspicious_activity" and 
                    r["timestamp"] >= event_record["timestamp"] and
                    (datetime.fromisoformat(event_record["timestamp"]) - datetime.fromisoformat(r["timestamp"])).total_seconds() <= 3600)
            ]
            
            if len(recent_suspicious_activities) > self.alert_thresholds["suspicious_activities_per_hour"]:
                logger.warning(f"Suspicious activities threshold exceeded: {len(recent_suspicious_activities)} activities in the last hour")
                return True
                
        return False
        
    async def query_security_events(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query security events.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Get query parameters
            event_type = data.get("event_type") if data else None
            security_level = data.get("security_level") if data else None
            user = data.get("user") if data else None
            resource = data.get("resource") if data else None
            action = data.get("action") if data else None
            result = data.get("result") if data else None
            ip_address = data.get("ip_address") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Filter security records
            filtered_records = self._security_records
            
            if event_type:
                filtered_records = [r for r in filtered_records if r["event_type"] == event_type]
                
            if security_level:
                filtered_records = [r for r in filtered_records if r["security_level"] == security_level]
                
            if user:
                filtered_records = [r for r in filtered_records if r["user"] == user]
                
            if resource:
                filtered_records = [r for r in filtered_records if r["resource"] == resource]
                
            if action:
                filtered_records = [r for r in filtered_records if r["action"] == action]
                
            if result:
                filtered_records = [r for r in filtered_records if r["result"] == result]
                
            if ip_address:
                filtered_records = [r for r in filtered_records if r["ip_address"] == ip_address]
                
            if start_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] >= start_time]
                
            if end_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] <= end_time]
                
            # Sort by timestamp (newest first)
            filtered_records.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Apply pagination
            total_count = len(filtered_records)
            paginated_records = filtered_records[offset:offset + limit]
            
            return {
                "status": "success",
                "message": "Security events queried successfully",
                "security_events": paginated_records,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Error querying security events: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def monitor_security(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor security.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Check if security is enabled
            if not self.security_enabled:
                return {"status": "success", "message": "Security is disabled"}
                
            # Get monitoring parameters
            event_type = data.get("event_type") if data else None
            user = data.get("user") if data else None
            resource = data.get("resource") if data else None
            continuous = data.get("continuous", False) if data else False
            
            # Validate event type
            if event_type and event_type not in self.event_types:
                return {"status": "error", "message": f"Unsupported event type: {event_type}"}
                
            # Start security monitoring
            if continuous:
                await self._start_continuous_security_monitoring(event_type, user, resource, context)
                return {
                    "status": "success",
                    "message": "Continuous security monitoring started successfully",
                    "event_type": event_type,
                    "user": user,
                    "resource": resource,
                    "continuous": True
                }
            else:
                # Perform one-time security check
                result = await self._perform_security_check(event_type, user, resource, context)
                return result
                
        except Exception as e:
            logger.error(f"Error monitoring security: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _start_continuous_security_monitoring(self, event_type: Optional[str], user: Optional[str], resource: Optional[str], context: Optional[Dict[str, Any]] = None) -> None:
        """Start continuous security monitoring."""
        # In a real implementation, this would start continuous security monitoring
        logger.info(f"Starting continuous security monitoring for event type: {event_type}, user: {user}, resource: {resource}")
        
    async def _perform_security_check(self, event_type: Optional[str], user: Optional[str], resource: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a security check."""
        # In a real implementation, this would perform an actual security check
        
        # Simulate security check
        security_issues = []
        
        # Add some sample security issues for demonstration
        if event_type == "authentication":
            security_issues.append({
                "type": "warning",
                "description": "Multiple failed login attempts detected",
                "recommendation": "Consider implementing stronger authentication measures"
            })
        elif event_type == "authorization":
            security_issues.append({
                "type": "critical",
                "description": "Unauthorized access attempt detected",
                "recommendation": "Review and tighten access controls"
            })
        elif event_type == "data_access":
            security_issues.append({
                "type": "warning",
                "description": "Unusual data access pattern detected",
                "recommendation": "Monitor for potential data breaches"
            })
            
        # Determine overall security status
        if any(issue["type"] == "critical" for issue in security_issues):
            overall_status = "critical"
        elif any(issue["type"] == "warning" for issue in security_issues):
            overall_status = "warning"
        else:
            overall_status = "secure"
            
        return {
            "status": "success",
            "message": "Security check completed successfully",
            "event_type": event_type,
            "user": user,
            "resource": resource,
            "overall_status": overall_status,
            "security_issues": security_issues,
            "issues_count": len(security_issues)
        }
        
    async def generate_security_report(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a security report.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Get report parameters
            report_type = data.get("report_type", "summary") if data else "summary"
            event_type = data.get("event_type") if data else None
            security_level = data.get("security_level") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            format_type = data.get("format", "json") if data else "json"
            
            # Filter security records based on parameters
            filtered_records = self._security_records
            
            if event_type:
                filtered_records = [r for r in filtered_records if r["event_type"] == event_type]
                
            if security_level:
                filtered_records = [r for r in filtered_records if r["security_level"] == security_level]
                
            if start_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] >= start_time]
                
            if end_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] <= end_time]
                
            # Generate report based on report type
            if report_type == "summary":
                report = await self._generate_summary_report(filtered_records)
            elif report_type == "detailed":
                report = await self._generate_detailed_report(filtered_records)
            elif report_type == "threat_analysis":
                report = await self._generate_threat_analysis_report(filtered_records)
            elif report_type == "user_activity":
                report = await self._generate_user_activity_report(filtered_records)
            else:
                return {"status": "error", "message": f"Unsupported report type: {report_type}"}
                
            # Format report based on format type
            if format_type == "json":
                formatted_report = json.dumps(report, indent=2)
            elif format_type == "csv":
                formatted_report = await self._format_report_as_csv(report)
            else:
                return {"status": "error", "message": f"Unsupported format type: {format_type}"}
                
            return {
                "status": "success",
                "message": "Security report generated successfully",
                "report_type": report_type,
                "format_type": format_type,
                "report": formatted_report
            }
            
        except Exception as e:
            logger.error(f"Error generating security report: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_summary_report(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary security report."""
        # Count by event type
        event_type_counts = {}
        for record in records:
            event_type = record["event_type"]
            if event_type not in event_type_counts:
                event_type_counts[event_type] = 0
            event_type_counts[event_type] += 1
            
        # Count by security level
        security_level_counts = {}
        for record in records:
            security_level = record["security_level"]
            if security_level not in security_level_counts:
                security_level_counts[security_level] = 0
            security_level_counts[security_level] += 1
            
        # Count by user
        user_counts = {}
        for record in records:
            user = record["user"]
            if user not in user_counts:
                user_counts[user] = 0
            user_counts[user] += 1
            
        # Count by IP address
        ip_counts = {}
        for record in records:
            ip = record["ip_address"]
            if ip not in ip_counts:
                ip_counts[ip] = 0
            ip_counts[ip] += 1
            
        return {
            "report_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "event_type_counts": event_type_counts,
            "security_level_counts": security_level_counts,
            "user_counts": user_counts,
            "ip_counts": ip_counts
        }
    
    async def _generate_detailed_report(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed security report."""
        return {
            "report_type": "detailed",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "records": records
        }
    
    async def _generate_threat_analysis_report(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a threat analysis security report."""
        # Filter for suspicious activities
        suspicious_records = [r for r in records if r["event_type"] == "suspicious_activity"]
        
        # Filter for security violations
        violation_records = [r for r in records if r["event_type"] == "security_violation"]
        
        # Filter for critical events
        critical_records = [r for r in records if r["security_level"] == "CRITICAL"]
        
        # Group by IP address
        ip_records = {}
        for record in records:
            ip = record["ip_address"]
            if ip not in ip_records:
                ip_records[ip] = []
            ip_records[ip].append(record)
            
        # Identify suspicious IPs (more than 10 events)
        suspicious_ips = {ip: ip_records[ip] for ip in ip_records if len(ip_records[ip]) > 10}
        
        return {
            "report_type": "threat_analysis",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "suspicious_records_count": len(suspicious_records),
            "violation_records_count": len(violation_records),
            "critical_records_count": len(critical_records),
            "suspicious_ips": suspicious_ips,
            "suspicious_ips_count": len(suspicious_ips)
        }
    
    async def _generate_user_activity_report(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a user activity security report."""
        # Group by user
        user_records = {}
        for record in records:
            user = record["user"]
            if user not in user_records:
                user_records[user] = []
            user_records[user].append(record)
            
        # Count activities per user
        user_activity_counts = {user: len(records) for user, records in user_records.items()}
        
        # Identify suspicious users (more than 50 events)
        suspicious_users = {user: user_records[user] for user in user_records if len(user_records[user]) > 50}
        
        return {
            "report_type": "user_activity",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "user_activity_counts": user_activity_counts,
            "suspicious_users": suspicious_users,
            "suspicious_users_count": len(suspicious_users)
        }
    
    async def _format_report_as_csv(self, report: Dict[str, Any]) -> str:
        """Format a report as CSV."""
        # In a real implementation, this would format the report as CSV
        return json.dumps(report, indent=2)
        
    async def analyze_security(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze security events.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Get analysis parameters
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            event_type = data.get("event_type") if data else None
            security_level = data.get("security_level") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            
            # Filter security records based on parameters
            filtered_records = self._security_records
            
            if event_type:
                filtered_records = [r for r in filtered_records if r["event_type"] == event_type]
                
            if security_level:
                filtered_records = [r for r in filtered_records if r["security_level"] == security_level]
                
            if start_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] >= start_time]
                
            if end_time:
                filtered_records = [r for r in filtered_records if r["timestamp"] <= end_time]
                
            # Analyze based on analysis type
            if analysis_type == "summary":
                analysis = await self._analyze_summary(filtered_records)
            elif analysis_type == "trends":
                analysis = await self._analyze_trends(filtered_records)
            elif analysis_type == "threats":
                analysis = await self._analyze_threats(filtered_records)
            elif analysis_type == "anomalies":
                analysis = await self._analyze_anomalies(filtered_records)
            else:
                return {"status": "error", "message": f"Unsupported analysis type: {analysis_type}"}
                
            return {
                "status": "success",
                "message": "Security analysis completed successfully",
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing security: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events for summary statistics."""
        # Count by event type
        event_type_counts = {}
        for record in records:
            event_type = record["event_type"]
            if event_type not in event_type_counts:
                event_type_counts[event_type] = 0
            event_type_counts[event_type] += 1
            
        # Count by security level
        security_level_counts = {}
        for record in records:
            security_level = record["security_level"]
            if security_level not in security_level_counts:
                security_level_counts[security_level] = 0
            security_level_counts[security_level] += 1
            
        # Count by user
        user_counts = {}
        for record in records:
            user = record["user"]
            if user not in user_counts:
                user_counts[user] = 0
            user_counts[user] += 1
            
        # Count by IP address
        ip_counts = {}
        for record in records:
            ip = record["ip_address"]
            if ip not in ip_counts:
                ip_counts[ip] = 0
            ip_counts[ip] += 1
            
        return {
            "analysis_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "event_type_counts": event_type_counts,
            "security_level_counts": security_level_counts,
            "user_counts": user_counts,
            "ip_counts": ip_counts
        }
    
    async def _analyze_trends(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events for trends."""
        # In a real implementation, this would analyze trends in the security events
        return {
            "analysis_type": "trends",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "message": "Trend analysis not implemented"
        }
    
    async def _analyze_threats(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events for threats."""
        # Filter for suspicious activities
        suspicious_records = [r for r in records if r["event_type"] == "suspicious_activity"]
        
        # Filter for security violations
        violation_records = [r for r in records if r["event_type"] == "security_violation"]
        
        # Filter for critical events
        critical_records = [r for r in records if r["security_level"] == "CRITICAL"]
        
        # Group by IP address
        ip_records = {}
        for record in records:
            ip = record["ip_address"]
            if ip not in ip_records:
                ip_records[ip] = []
            ip_records[ip].append(record)
            
        # Identify suspicious IPs (more than 10 events)
        suspicious_ips = {ip: ip_records[ip] for ip in ip_records if len(ip_records[ip]) > 10}
        
        return {
            "analysis_type": "threats",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "suspicious_records_count": len(suspicious_records),
            "violation_records_count": len(violation_records),
            "critical_records_count": len(critical_records),
            "suspicious_ips": suspicious_ips,
            "suspicious_ips_count": len(suspicious_ips)
        }
    
    async def _analyze_anomalies(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events for anomalies."""
        # In a real implementation, this would analyze anomalies in the security events
        return {
            "analysis_type": "anomalies",
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "message": "Anomaly analysis not implemented"
        }
        
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get security statistics.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Security service is not connected"}
                
            # Get security statistics
            security_stats = {
                "security_enabled": self.security_enabled,
                "security_levels": self.security_levels,
                "event_types": self.event_types,
                "max_security_records": self.max_security_records,
                "retention_days": self.retention_days,
                "alert_thresholds": self.alert_thresholds,
                "current_records_count": len(self._security_records),
                "storage_usage_percent": (len(self._security_records) / self.max_security_records) * 100
            }
            
            # Count by event type
            event_type_counts = {}
            for record in self._security_records:
                event_type = record["event_type"]
                if event_type not in event_type_counts:
                    event_type_counts[event_type] = 0
                event_type_counts[event_type] += 1
                
            # Count by security level
            security_level_counts = {}
            for record in self._security_records:
                security_level = record["security_level"]
                if security_level not in security_level_counts:
                    security_level_counts[security_level] = 0
                security_level_counts[security_level] += 1
                
            security_stats["event_type_counts"] = event_type_counts
            security_stats["security_level_counts"] = security_level_counts
            
            return {
                "status": "success",
                "message": "Security statistics retrieved successfully",
                "security_stats": security_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting security statistics: {str(e)}")
            return {"status": "error", "message": str(e)}