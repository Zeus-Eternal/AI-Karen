"""
Compliance Service Helper

This module provides helper functionality for compliance operations in the KAREN AI system.
It handles compliance validation, compliance monitoring, and other compliance-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ComplianceServiceHelper:
    """
    Helper service for compliance operations.
    
    This service provides methods for validating, monitoring, and reporting on compliance
    in the KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the compliance service helper.
        
        Args:
            config: Configuration dictionary for the compliance service
        """
        self.config = config
        self.compliance_enabled = config.get("compliance_enabled", True)
        self.compliance_frameworks = config.get("compliance_frameworks", ["GDPR", "HIPAA", "SOC2", "ISO27001"])
        self.compliance_checks = config.get("compliance_checks", ["data_privacy", "security_controls", "access_controls", "audit_trails"])
        self.check_interval = config.get("check_interval", 3600)  # 1 hour
        self.alert_thresholds = config.get("alert_thresholds", {
            "compliance_score": 70.0,  # 70%
            "critical_violations": 1,
            "major_violations": 5,
            "minor_violations": 10
        })
        self._is_connected = False
        self._compliance_reports = []
        
    async def initialize(self) -> bool:
        """
        Initialize the compliance service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing compliance service")
            
            # Initialize compliance monitoring
            if self.compliance_enabled:
                await self._initialize_compliance_monitoring()
                
            self._is_connected = True
            logger.info("Compliance service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing compliance service: {str(e)}")
            return False
    
    async def _initialize_compliance_monitoring(self) -> None:
        """Initialize compliance monitoring."""
        # In a real implementation, this would set up compliance monitoring
        logger.info(f"Initializing compliance monitoring with frameworks: {self.compliance_frameworks}")
        
    async def start(self) -> bool:
        """
        Start the compliance service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting compliance service")
            
            # Start compliance monitoring
            if self.compliance_enabled:
                await self._start_compliance_monitoring()
                
            logger.info("Compliance service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting compliance service: {str(e)}")
            return False
    
    async def _start_compliance_monitoring(self) -> None:
        """Start compliance monitoring."""
        # In a real implementation, this would start compliance monitoring
        logger.info("Starting compliance monitoring")
        
    async def stop(self) -> bool:
        """
        Stop the compliance service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping compliance service")
            
            # Stop compliance monitoring
            if self.compliance_enabled:
                await self._stop_compliance_monitoring()
                
            self._is_connected = False
            self._compliance_reports.clear()
            logger.info("Compliance service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping compliance service: {str(e)}")
            return False
    
    async def _stop_compliance_monitoring(self) -> None:
        """Stop compliance monitoring."""
        # In a real implementation, this would stop compliance monitoring
        logger.info("Stopping compliance monitoring")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the compliance service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_connected:
                return {"status": "unhealthy", "message": "Compliance service is not connected"}
                
            # Check compliance monitoring health
            monitoring_health = {"status": "healthy", "message": "Compliance monitoring is healthy"}
            if self.compliance_enabled:
                monitoring_health = await self._health_check_compliance_monitoring()
                
            # Determine overall health
            overall_status = monitoring_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Compliance service is {overall_status}",
                "monitoring_health": monitoring_health
            }
            
        except Exception as e:
            logger.error(f"Error checking compliance service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_compliance_monitoring(self) -> Dict[str, Any]:
        """Check compliance monitoring health."""
        # In a real implementation, this would check compliance monitoring health
        return {"status": "healthy", "message": "Compliance monitoring is healthy"}
        
    async def validate_compliance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate compliance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Compliance service is not connected"}
                
            # Check if compliance is enabled
            if not self.compliance_enabled:
                return {"status": "success", "message": "Compliance is disabled"}
                
            # Get validation parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            
            # Validate framework
            if framework and framework not in self.compliance_frameworks:
                return {"status": "error", "message": f"Unsupported compliance framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.compliance_checks:
                return {"status": "error", "message": f"Unsupported compliance check: {check_type}"}
                
            # Create compliance validation
            validation_id = str(uuid.uuid4())
            
            # Perform compliance validation
            validation_result = await self._perform_compliance_validation(framework, check_type, target, context)
            
            # Create compliance report
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
            self._compliance_reports.append(report)
            
            # Check if we need to prune old reports
            if len(self._compliance_reports) > 100:  # Keep only the most recent 100 reports
                await self._prune_old_reports()
                
            return {
                "status": "success",
                "message": "Compliance validation completed successfully",
                "validation_id": validation_id,
                "report_id": report["report_id"],
                "result": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error validating compliance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _perform_compliance_validation(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform compliance validation."""
        # In a real implementation, this would perform actual compliance validation
        
        # Simulate compliance validation
        violations = []
        
        # Add some sample violations for demonstration
        if check_type == "data_privacy":
            violations.append({
                "type": "minor",
                "description": "Data retention policy not clearly documented",
                "recommendation": "Document data retention policies for all data types"
            })
        elif check_type == "security_controls":
            violations.append({
                "type": "major",
                "description": "Encryption not enabled for some sensitive data",
                "recommendation": "Enable encryption for all sensitive data"
            })
        elif check_type == "access_controls":
            violations.append({
                "type": "critical",
                "description": "Unrestricted access to admin functions",
                "recommendation": "Restrict access to admin functions to authorized personnel only"
            })
        elif check_type == "audit_trails":
            violations.append({
                "type": "minor",
                "description": "Audit logs not retained for required period",
                "recommendation": "Ensure audit logs are retained for the required period"
            })
            
        # Calculate compliance score
        total_checks = 10  # Assume 10 compliance checks
        critical_violations = sum(1 for v in violations if v["type"] == "critical")
        major_violations = sum(1 for v in violations if v["type"] == "major")
        minor_violations = sum(1 for v in violations if v["type"] == "minor")
        
        # Deduct points for violations
        score_deduction = (critical_violations * 20) + (major_violations * 10) + (minor_violations * 5)
        compliance_score = max(0, 100 - score_deduction)
        
        # Determine overall status
        if compliance_score >= 90:
            overall_status = "compliant"
        elif compliance_score >= 70:
            overall_status = "partially_compliant"
        else:
            overall_status = "non_compliant"
            
        return {
            "framework": framework,
            "check_type": check_type,
            "target": target,
            "overall_status": overall_status,
            "compliance_score": compliance_score,
            "total_checks": total_checks,
            "passed_checks": total_checks - len(violations),
            "failed_checks": len(violations),
            "violations": violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _prune_old_reports(self) -> None:
        """Prune old compliance reports."""
        # In a real implementation, this would prune old reports based on retention policy
        logger.info(f"Pruning old compliance reports, current count: {len(self._compliance_reports)}")
        
        # Sort by timestamp (oldest first)
        self._compliance_reports.sort(key=lambda x: x["timestamp"])
        
        # Keep only the most recent reports
        self._compliance_reports = self._compliance_reports[-100:]
        
    async def monitor_compliance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor compliance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Compliance service is not connected"}
                
            # Check if compliance is enabled
            if not self.compliance_enabled:
                return {"status": "success", "message": "Compliance is disabled"}
                
            # Get monitoring parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            continuous = data.get("continuous", False) if data else False
            
            # Validate framework
            if framework and framework not in self.compliance_frameworks:
                return {"status": "error", "message": f"Unsupported compliance framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.compliance_checks:
                return {"status": "error", "message": f"Unsupported compliance check: {check_type}"}
                
            # Start compliance monitoring
            if continuous:
                await self._start_continuous_compliance_monitoring(framework, check_type, target, context)
                return {
                    "status": "success",
                    "message": "Continuous compliance monitoring started successfully",
                    "framework": framework,
                    "check_type": check_type,
                    "target": target,
                    "continuous": True
                }
            else:
                # Perform one-time compliance check
                result = await self.validate_compliance(data, context)
                return result
                
        except Exception as e:
            logger.error(f"Error monitoring compliance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _start_continuous_compliance_monitoring(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> None:
        """Start continuous compliance monitoring."""
        # In a real implementation, this would start continuous compliance monitoring
        logger.info(f"Starting continuous compliance monitoring for framework: {framework}, check: {check_type}, target: {target}")
        
    async def generate_compliance_report(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a compliance report.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Compliance service is not connected"}
                
            # Get report parameters
            report_type = data.get("report_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            format_type = data.get("format", "json") if data else "json"
            
            # Filter compliance reports based on parameters
            filtered_reports = self._compliance_reports
            
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
                "message": "Compliance report generated successfully",
                "report_type": report_type,
                "format_type": format_type,
                "report": formatted_report
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_summary_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary compliance report."""
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
            
        # Calculate average compliance score
        total_score = sum(report["result"]["compliance_score"] for report in reports)
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
            "average_compliance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_detailed_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed compliance report."""
        return {
            "report_type": "detailed",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "reports": reports
        }
    
    async def _generate_framework_report(self, reports: List[Dict[str, Any]], framework: Optional[str]) -> Dict[str, Any]:
        """Generate a framework-specific compliance report."""
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
            
        # Calculate average compliance score
        total_score = sum(report["result"]["compliance_score"] for report in framework_reports)
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
            "average_compliance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_violations_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a violations compliance report."""
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
        
    async def analyze_compliance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze compliance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Compliance service is not connected"}
                
            # Get analysis parameters
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            
            # Filter compliance reports based on parameters
            filtered_reports = self._compliance_reports
            
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
                "message": "Compliance analysis completed successfully",
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing compliance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_summary(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compliance for summary statistics."""
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
            
        # Calculate average compliance score
        total_score = sum(report["result"]["compliance_score"] for report in reports)
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
            "average_compliance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _analyze_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compliance for trends."""
        # In a real implementation, this would analyze trends in the compliance reports
        return {
            "analysis_type": "trends",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "message": "Trend analysis not implemented"
        }
    
    async def _analyze_violations(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compliance for violations."""
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
        """Analyze compliance by frameworks."""
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
            # Calculate average compliance score
            total_score = sum(report["result"]["compliance_score"] for report in f_reports)
            average_score = total_score / len(f_reports) if f_reports else 0
                
            # Count violations
            total_violations = sum(len(report["result"]["violations"]) for report in f_reports)
            critical_violations = sum(report["result"]["critical_violations"] for report in f_reports)
            major_violations = sum(report["result"]["major_violations"] for report in f_reports)
            minor_violations = sum(report["result"]["minor_violations"] for report in f_reports)
                
            framework_stats[framework] = {
                "total_reports": len(f_reports),
                "average_compliance_score": average_score,
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
        Get compliance statistics.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Compliance service is not connected"}
                
            # Get compliance statistics
            compliance_stats = {
                "compliance_enabled": self.compliance_enabled,
                "compliance_frameworks": self.compliance_frameworks,
                "compliance_checks": self.compliance_checks,
                "check_interval": self.check_interval,
                "alert_thresholds": self.alert_thresholds,
                "current_reports_count": len(self._compliance_reports)
            }
            
            # Calculate statistics from reports
            if self._compliance_reports:
                # Calculate average compliance score
                total_score = sum(report["result"]["compliance_score"] for report in self._compliance_reports)
                average_score = total_score / len(self._compliance_reports)
                
                # Count violations
                total_violations = sum(len(report["result"]["violations"]) for report in self._compliance_reports)
                critical_violations = sum(report["result"]["critical_violations"] for report in self._compliance_reports)
                major_violations = sum(report["result"]["major_violations"] for report in self._compliance_reports)
                minor_violations = sum(report["result"]["minor_violations"] for report in self._compliance_reports)
                
                # Count by status
                status_counts = {}
                for report in self._compliance_reports:
                    status = report["result"]["overall_status"]
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                    
                compliance_stats["average_compliance_score"] = average_score
                compliance_stats["total_violations"] = total_violations
                compliance_stats["critical_violations"] = critical_violations
                compliance_stats["major_violations"] = major_violations
                compliance_stats["minor_violations"] = minor_violations
                compliance_stats["status_counts"] = status_counts
            else:
                compliance_stats["average_compliance_score"] = 0
                compliance_stats["total_violations"] = 0
                compliance_stats["critical_violations"] = 0
                compliance_stats["major_violations"] = 0
                compliance_stats["minor_violations"] = 0
                compliance_stats["status_counts"] = {}
                
            return {
                "status": "success",
                "message": "Compliance statistics retrieved successfully",
                "compliance_stats": compliance_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance statistics: {str(e)}")
            return {"status": "error", "message": str(e)}