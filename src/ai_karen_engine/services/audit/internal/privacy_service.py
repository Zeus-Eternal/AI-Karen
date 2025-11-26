"""
Privacy Service Helper

This module provides helper functionality for privacy operations in the KAREN AI system.
It handles privacy validation, privacy monitoring, and other privacy-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class PrivacyServiceHelper:
    """
    Helper service for privacy operations.
    
    This service provides methods for validating, monitoring, and reporting on privacy
    in the KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the privacy service helper.
        
        Args:
            config: Configuration dictionary for the privacy service
        """
        self.config = config
        self.privacy_enabled = config.get("privacy_enabled", True)
        self.privacy_frameworks = config.get("privacy_frameworks", ["GDPR", "CCPA", "HIPAA"])
        self.privacy_checks = config.get("privacy_checks", [
            "data_collection", "data_processing", "data_storage", 
            "data_sharing", "user_consent", "data_retention", "user_rights"
        ])
        self.check_interval = config.get("check_interval", 3600)  # 1 hour
        self.alert_thresholds = config.get("alert_thresholds", {
            "privacy_score": 80.0,  # 80%
            "critical_violations": 1,
            "major_violations": 3,
            "minor_violations": 5
        })
        self._is_connected = False
        self._privacy_reports = []
        
    async def initialize(self) -> bool:
        """
        Initialize the privacy service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing privacy service")
            
            # Initialize privacy monitoring
            if self.privacy_enabled:
                await self._initialize_privacy_monitoring()
                
            self._is_connected = True
            logger.info("Privacy service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing privacy service: {str(e)}")
            return False
    
    async def _initialize_privacy_monitoring(self) -> None:
        """Initialize privacy monitoring."""
        # In a real implementation, this would set up privacy monitoring
        logger.info(f"Initializing privacy monitoring with frameworks: {self.privacy_frameworks}")
        
    async def start(self) -> bool:
        """
        Start the privacy service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting privacy service")
            
            # Start privacy monitoring
            if self.privacy_enabled:
                await self._start_privacy_monitoring()
                
            logger.info("Privacy service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting privacy service: {str(e)}")
            return False
    
    async def _start_privacy_monitoring(self) -> None:
        """Start privacy monitoring."""
        # In a real implementation, this would start privacy monitoring
        logger.info("Starting privacy monitoring")
        
    async def stop(self) -> bool:
        """
        Stop the privacy service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping privacy service")
            
            # Stop privacy monitoring
            if self.privacy_enabled:
                await self._stop_privacy_monitoring()
                
            self._is_connected = False
            self._privacy_reports.clear()
            logger.info("Privacy service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping privacy service: {str(e)}")
            return False
    
    async def _stop_privacy_monitoring(self) -> None:
        """Stop privacy monitoring."""
        # In a real implementation, this would stop privacy monitoring
        logger.info("Stopping privacy monitoring")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the privacy service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_connected:
                return {"status": "unhealthy", "message": "Privacy service is not connected"}
                
            # Check privacy monitoring health
            monitoring_health = {"status": "healthy", "message": "Privacy monitoring is healthy"}
            if self.privacy_enabled:
                monitoring_health = await self._health_check_privacy_monitoring()
                
            # Determine overall health
            overall_status = monitoring_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Privacy service is {overall_status}",
                "monitoring_health": monitoring_health
            }
            
        except Exception as e:
            logger.error(f"Error checking privacy service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_privacy_monitoring(self) -> Dict[str, Any]:
        """Check privacy monitoring health."""
        # In a real implementation, this would check privacy monitoring health
        return {"status": "healthy", "message": "Privacy monitoring is healthy"}
        
    async def validate_privacy(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate privacy.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Privacy service is not connected"}
                
            # Check if privacy is enabled
            if not self.privacy_enabled:
                return {"status": "success", "message": "Privacy is disabled"}
                
            # Get validation parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            
            # Validate framework
            if framework and framework not in self.privacy_frameworks:
                return {"status": "error", "message": f"Unsupported privacy framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.privacy_checks:
                return {"status": "error", "message": f"Unsupported privacy check: {check_type}"}
                
            # Create privacy validation
            validation_id = str(uuid.uuid4())
            
            # Perform privacy validation
            validation_result = await self._perform_privacy_validation(framework, check_type, target, context)
            
            # Create privacy report
            report = {
                "report_id": str(uuid.uuid4()),
                "validation_id": validation_id,
                "timestamp": datetime.now().isoformat(),
                "framework": framework,
                "check_type": check_type,
                "target": target,
                "result": validation_result,
                "context": context or {}
            }
            
            # Add report to storage
            self._privacy_reports.append(report)
            
            # Check if we need to prune old reports
            if len(self._privacy_reports) > 100:  # Keep only the most recent 100 reports
                await self._prune_old_reports()
                
            return {
                "status": "success",
                "message": "Privacy validation completed successfully",
                "validation_id": validation_id,
                "report_id": report["report_id"],
                "result": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error validating privacy: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _perform_privacy_validation(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform privacy validation."""
        # In a real implementation, this would perform actual privacy validation
        
        # Simulate privacy validation
        violations = []
        
        # Add some sample violations for demonstration
        if check_type == "data_collection":
            violations.append({
                "type": "minor",
                "description": "Data collection purpose not clearly stated",
                "recommendation": "Clearly state the purpose of data collection"
            })
        elif check_type == "data_processing":
            violations.append({
                "type": "major",
                "description": "Data processing without explicit user consent",
                "recommendation": "Obtain explicit user consent before processing data"
            })
        elif check_type == "data_storage":
            violations.append({
                "type": "minor",
                "description": "Data retention period not defined",
                "recommendation": "Define data retention periods for all data types"
            })
        elif check_type == "data_sharing":
            violations.append({
                "type": "critical",
                "description": "Data sharing with third parties without user consent",
                "recommendation": "Obtain user consent before sharing data with third parties"
            })
        elif check_type == "user_consent":
            violations.append({
                "type": "major",
                "description": "User consent mechanism not granular enough",
                "recommendation": "Provide granular consent options for users"
            })
        elif check_type == "data_retention":
            violations.append({
                "type": "minor",
                "description": "Data retention policy not easily accessible",
                "recommendation": "Make data retention policy easily accessible to users"
            })
        elif check_type == "user_rights":
            violations.append({
                "type": "major",
                "description": "User rights not clearly communicated",
                "recommendation": "Clearly communicate user rights regarding their data"
            })
            
        # Calculate privacy score
        total_checks = 10  # Assume 10 privacy checks
        critical_violations = sum(1 for v in violations if v["type"] == "critical")
        major_violations = sum(1 for v in violations if v["type"] == "major")
        minor_violations = sum(1 for v in violations if v["type"] == "minor")
        
        # Deduct points for violations
        score_deduction = (critical_violations * 25) + (major_violations * 15) + (minor_violations * 5)
        privacy_score = max(0, 100 - score_deduction)
        
        # Determine overall status
        if privacy_score >= 90:
            overall_status = "compliant"
        elif privacy_score >= 80:
            overall_status = "partially_compliant"
        else:
            overall_status = "non_compliant"
            
        return {
            "framework": framework,
            "check_type": check_type,
            "target": target,
            "overall_status": overall_status,
            "privacy_score": privacy_score,
            "total_checks": total_checks,
            "passed_checks": total_checks - len(violations),
            "failed_checks": len(violations),
            "violations": violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _prune_old_reports(self) -> None:
        """Prune old privacy reports."""
        # In a real implementation, this would prune old reports based on retention policy
        logger.info(f"Pruning old privacy reports, current count: {len(self._privacy_reports)}")
        
        # Sort by timestamp (oldest first)
        self._privacy_reports.sort(key=lambda x: x["timestamp"])
        
        # Keep only the most recent reports
        self._privacy_reports = self._privacy_reports[-100:]
        
    async def monitor_privacy(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor privacy.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Privacy service is not connected"}
                
            # Check if privacy is enabled
            if not self.privacy_enabled:
                return {"status": "success", "message": "Privacy is disabled"}
                
            # Get monitoring parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            continuous = data.get("continuous", False) if data else False
            
            # Validate framework
            if framework and framework not in self.privacy_frameworks:
                return {"status": "error", "message": f"Unsupported privacy framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.privacy_checks:
                return {"status": "error", "message": f"Unsupported privacy check: {check_type}"}
                
            # Start privacy monitoring
            if continuous:
                await self._start_continuous_privacy_monitoring(framework, check_type, target, context)
                return {
                    "status": "success",
                    "message": "Continuous privacy monitoring started successfully",
                    "framework": framework,
                    "check_type": check_type,
                    "target": target,
                    "continuous": True
                }
            else:
                # Perform one-time privacy check
                result = await self.validate_privacy(data, context)
                return result
                
        except Exception as e:
            logger.error(f"Error monitoring privacy: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _start_continuous_privacy_monitoring(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> None:
        """Start continuous privacy monitoring."""
        # In a real implementation, this would start continuous privacy monitoring
        logger.info(f"Starting continuous privacy monitoring for framework: {framework}, check: {check_type}, target: {target}")
        
    async def generate_privacy_report(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a privacy report.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Privacy service is not connected"}
                
            # Get report parameters
            report_type = data.get("report_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            format_type = data.get("format", "json") if data else "json"
            
            # Filter privacy reports based on parameters
            filtered_reports = self._privacy_reports
            
            if framework:
                filtered_reports = [r for r in filtered_reports if r["framework"] == framework]
                
            if start_time:
                filtered_reports = [r for r in filtered_reports if r["timestamp"] >= start_time]
                
            if end_time:
                filtered_reports = [r for r in filtered_reports if r["timestamp"] <= end_time]
                
            # Generate report based on report type
            if report_type == "summary":
                report = await self._generate_summary_report(filtered_reports)
            elif report_type == "detailed":
                report = await self._generate_detailed_report(filtered_reports)
            elif report_type == "framework":
                report = await self._generate_framework_report(filtered_reports, framework)
            elif report_type == "violations":
                report = await self._generate_violations_report(filtered_reports)
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
                "message": "Privacy report generated successfully",
                "report_type": report_type,
                "format_type": format_type,
                "report": formatted_report
            }
            
        except Exception as e:
            logger.error(f"Error generating privacy report: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_summary_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary privacy report."""
        # Count by framework
        framework_counts = {}
        for report in reports:
            framework = report["framework"]
            if framework not in framework_counts:
                framework_counts[framework] = 0
            framework_counts[framework] += 1
            
        # Count by status
        status_counts = {}
        for report in reports:
            status = report["result"]["overall_status"]
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
            
        # Calculate average privacy score
        total_score = sum(report["result"]["privacy_score"] for report in reports)
        average_score = total_score / len(reports) if reports else 0
        
        # Count violations
        total_violations = sum(len(report["result"]["violations"]) for report in reports)
        critical_violations = sum(report["result"]["critical_violations"] for report in reports)
        major_violations = sum(report["result"]["major_violations"] for report in reports)
        minor_violations = sum(report["result"]["minor_violations"] for report in reports)
        
        return {
            "report_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "framework_counts": framework_counts,
            "status_counts": status_counts,
            "average_privacy_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_detailed_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed privacy report."""
        return {
            "report_type": "detailed",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "reports": reports
        }
    
    async def _generate_framework_report(self, reports: List[Dict[str, Any]], framework: Optional[str]) -> Dict[str, Any]:
        """Generate a framework-specific privacy report."""
        # Filter reports by framework
        if framework:
            framework_reports = [r for r in reports if r["framework"] == framework]
        else:
            framework_reports = reports
            
        # Group by check type
        check_type_reports = {}
        for report in framework_reports:
            check_type = report["check_type"]
            if check_type not in check_type_reports:
                check_type_reports[check_type] = []
            check_type_reports[check_type].append(report)
            
        # Calculate average privacy score
        total_score = sum(report["result"]["privacy_score"] for report in framework_reports)
        average_score = total_score / len(framework_reports) if framework_reports else 0
        
        # Count violations
        total_violations = sum(len(report["result"]["violations"]) for report in framework_reports)
        critical_violations = sum(report["result"]["critical_violations"] for report in framework_reports)
        major_violations = sum(report["result"]["major_violations"] for report in framework_reports)
        minor_violations = sum(report["result"]["minor_violations"] for report in framework_reports)
        
        return {
            "report_type": "framework",
            "framework": framework,
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(framework_reports),
            "check_type_reports": check_type_reports,
            "average_privacy_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_violations_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a violations privacy report."""
        # Collect all violations
        all_violations = []
        for report in reports:
            for violation in report["result"]["violations"]:
                violation["framework"] = report["framework"]
                violation["check_type"] = report["check_type"]
                violation["target"] = report["target"]
                violation["timestamp"] = report["timestamp"]
                all_violations.append(violation)
                
        # Group by violation type
        violation_types = {}
        for violation in all_violations:
            violation_type = violation["type"]
            if violation_type not in violation_types:
                violation_types[violation_type] = []
            violation_types[violation_type].append(violation)
            
        # Group by framework
        framework_violations = {}
        for violation in all_violations:
            framework = violation["framework"]
            if framework not in framework_violations:
                framework_violations[framework] = []
            framework_violations[framework].append(violation)
            
        return {
            "report_type": "violations",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "total_violations": len(all_violations),
            "violation_types": violation_types,
            "framework_violations": framework_violations,
            "violations": all_violations
        }
    
    async def _format_report_as_csv(self, report: Dict[str, Any]) -> str:
        """Format a report as CSV."""
        # In a real implementation, this would format the report as CSV
        return json.dumps(report, indent=2)
        
    async def analyze_privacy(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze privacy.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Privacy service is not connected"}
                
            # Get analysis parameters
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            
            # Filter privacy reports based on parameters
            filtered_reports = self._privacy_reports
            
            if framework:
                filtered_reports = [r for r in filtered_reports if r["framework"] == framework]
                
            if start_time:
                filtered_reports = [r for r in filtered_reports if r["timestamp"] >= start_time]
                
            if end_time:
                filtered_reports = [r for r in filtered_reports if r["timestamp"] <= end_time]
                
            # Analyze based on analysis type
            if analysis_type == "summary":
                analysis = await self._analyze_summary(filtered_reports)
            elif analysis_type == "trends":
                analysis = await self._analyze_trends(filtered_reports)
            elif analysis_type == "violations":
                analysis = await self._analyze_violations(filtered_reports)
            elif analysis_type == "frameworks":
                analysis = await self._analyze_frameworks(filtered_reports)
            else:
                return {"status": "error", "message": f"Unsupported analysis type: {analysis_type}"}
                
            return {
                "status": "success",
                "message": "Privacy analysis completed successfully",
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing privacy: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_summary(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze privacy for summary statistics."""
        # Count by framework
        framework_counts = {}
        for report in reports:
            framework = report["framework"]
            if framework not in framework_counts:
                framework_counts[framework] = 0
            framework_counts[framework] += 1
            
        # Count by status
        status_counts = {}
        for report in reports:
            status = report["result"]["overall_status"]
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
            
        # Calculate average privacy score
        total_score = sum(report["result"]["privacy_score"] for report in reports)
        average_score = total_score / len(reports) if reports else 0
        
        # Count violations
        total_violations = sum(len(report["result"]["violations"]) for report in reports)
        critical_violations = sum(report["result"]["critical_violations"] for report in reports)
        major_violations = sum(report["result"]["major_violations"] for report in reports)
        minor_violations = sum(report["result"]["minor_violations"] for report in reports)
        
        return {
            "analysis_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "framework_counts": framework_counts,
            "status_counts": status_counts,
            "average_privacy_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _analyze_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze privacy for trends."""
        # In a real implementation, this would analyze trends in the privacy reports
        return {
            "analysis_type": "trends",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "message": "Trend analysis not implemented"
        }
    
    async def _analyze_violations(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze privacy for violations."""
        # Collect all violations
        all_violations = []
        for report in reports:
            for violation in report["result"]["violations"]:
                violation["framework"] = report["framework"]
                violation["check_type"] = report["check_type"]
                violation["target"] = report["target"]
                violation["timestamp"] = report["timestamp"]
                all_violations.append(violation)
                
        # Group by violation type
        violation_types = {}
        for violation in all_violations:
            violation_type = violation["type"]
            if violation_type not in violation_types:
                violation_types[violation_type] = []
            violation_types[violation_type].append(violation)
            
        # Group by framework
        framework_violations = {}
        for violation in all_violations:
            framework = violation["framework"]
            if framework not in framework_violations:
                framework_violations[framework] = []
            framework_violations[framework].append(violation)
                
        return {
            "analysis_type": "violations",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "total_violations": len(all_violations),
            "violation_types": violation_types,
            "framework_violations": framework_violations,
            "violations": all_violations
        }
    
    async def _analyze_frameworks(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze privacy by frameworks."""
        # Group by framework
        framework_reports = {}
        for report in reports:
            framework = report["framework"]
            if framework not in framework_reports:
                framework_reports[framework] = []
            framework_reports[framework].append(report)
                
        # Calculate statistics for each framework
        framework_stats = {}
        for framework, f_reports in framework_reports.items():
            # Calculate average privacy score
            total_score = sum(report["result"]["privacy_score"] for report in f_reports)
            average_score = total_score / len(f_reports) if f_reports else 0
                
            # Count violations
            total_violations = sum(len(report["result"]["violations"]) for report in f_reports)
            critical_violations = sum(report["result"]["critical_violations"] for report in f_reports)
            major_violations = sum(report["result"]["major_violations"] for report in f_reports)
            minor_violations = sum(report["result"]["minor_violations"] for report in f_reports)
                
            framework_stats[framework] = {
                "total_reports": len(f_reports),
                "average_privacy_score": average_score,
                "total_violations": total_violations,
                "critical_violations": critical_violations,
                "major_violations": major_violations,
                "minor_violations": minor_violations
            }
                
        return {
            "analysis_type": "frameworks",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "framework_reports": framework_reports,
            "framework_stats": framework_stats
        }
        
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get privacy statistics.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Privacy service is not connected"}
                
            # Get privacy statistics
            privacy_stats = {
                "privacy_enabled": self.privacy_enabled,
                "privacy_frameworks": self.privacy_frameworks,
                "privacy_checks": self.privacy_checks,
                "check_interval": self.check_interval,
                "alert_thresholds": self.alert_thresholds,
                "current_reports_count": len(self._privacy_reports)
            }
            
            # Calculate statistics from reports
            if self._privacy_reports:
                # Calculate average privacy score
                total_score = sum(report["result"]["privacy_score"] for report in self._privacy_reports)
                average_score = total_score / len(self._privacy_reports)
                
                # Count violations
                total_violations = sum(len(report["result"]["violations"]) for report in self._privacy_reports)
                critical_violations = sum(report["result"]["critical_violations"] for report in self._privacy_reports)
                major_violations = sum(report["result"]["major_violations"] for report in self._privacy_reports)
                minor_violations = sum(report["result"]["minor_violations"] for report in self._privacy_reports)
                
                # Count by status
                status_counts = {}
                for report in self._privacy_reports:
                    status = report["result"]["overall_status"]
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                    
                privacy_stats["average_privacy_score"] = average_score
                privacy_stats["total_violations"] = total_violations
                privacy_stats["critical_violations"] = critical_violations
                privacy_stats["major_violations"] = major_violations
                privacy_stats["minor_violations"] = minor_violations
                privacy_stats["status_counts"] = status_counts
            else:
                privacy_stats["average_privacy_score"] = 0
                privacy_stats["total_violations"] = 0
                privacy_stats["critical_violations"] = 0
                privacy_stats["major_violations"] = 0
                privacy_stats["minor_violations"] = 0
                privacy_stats["status_counts"] = {}
                
            return {
                "status": "success",
                "message": "Privacy statistics retrieved successfully",
                "privacy_stats": privacy_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting privacy statistics: {str(e)}")
            return {"status": "error", "message": str(e)}