"""
Governance Service Helper

This module provides helper functionality for governance operations in KAREN AI system.
It handles governance validation, governance monitoring, and other governance-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class GovernanceServiceHelper:
    """
    Helper service for governance operations.
    
    This service provides methods for validating, monitoring, and reporting on governance
    in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the governance service helper.
        
        Args:
            config: Configuration dictionary for the governance service
        """
        self.config = config
        self.governance_enabled = config.get("governance_enabled", True)
        self.governance_frameworks = config.get("governance_frameworks", ["ISO38500", "COBIT", "ITIL"])
        self.governance_checks = config.get("governance_checks", [
            "policy_compliance", "risk_management", "control_effectiveness",
            "stakeholder_communication", "value_delivery", "resource_optimization"
        ])
        self.check_interval = config.get("check_interval", 86400)  # 24 hours
        self.alert_thresholds = config.get("alert_thresholds", {
            "governance_score": 75.0,  # 75%
            "critical_violations": 1,
            "major_violations": 3,
            "minor_violations": 5
        })
        self._is_connected = False
        self._governance_reports = []
        
    async def initialize(self) -> bool:
        """
        Initialize the governance service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing governance service")
            
            # Initialize governance monitoring
            if self.governance_enabled:
                await self._initialize_governance_monitoring()
                
            self._is_connected = True
            logger.info("Governance service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing governance service: {str(e)}")
            return False
    
    async def _initialize_governance_monitoring(self) -> None:
        """Initialize governance monitoring."""
        # In a real implementation, this would set up governance monitoring
        logger.info(f"Initializing governance monitoring with frameworks: {self.governance_frameworks}")
        
    async def start(self) -> bool:
        """
        Start the governance service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting governance service")
            
            # Start governance monitoring
            if self.governance_enabled:
                await self._start_governance_monitoring()
                
            logger.info("Governance service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting governance service: {str(e)}")
            return False
    
    async def _start_governance_monitoring(self) -> None:
        """Start governance monitoring."""
        # In a real implementation, this would start governance monitoring
        logger.info("Starting governance monitoring")
        
    async def stop(self) -> bool:
        """
        Stop the governance service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping governance service")
            
            # Stop governance monitoring
            if self.governance_enabled:
                await self._stop_governance_monitoring()
                
            self._is_connected = False
            self._governance_reports.clear()
            logger.info("Governance service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping governance service: {str(e)}")
            return False
    
    async def _stop_governance_monitoring(self) -> None:
        """Stop governance monitoring."""
        # In a real implementation, this would stop governance monitoring
        logger.info("Stopping governance monitoring")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the governance service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_connected:
                return {"status": "unhealthy", "message": "Governance service is not connected"}
                
            # Check governance monitoring health
            monitoring_health = {"status": "healthy", "message": "Governance monitoring is healthy"}
            if self.governance_enabled:
                monitoring_health = await self._health_check_governance_monitoring()
                
            # Determine overall health
            overall_status = monitoring_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Governance service is {overall_status}",
                "monitoring_health": monitoring_health
            }
            
        except Exception as e:
            logger.error(f"Error checking governance service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_governance_monitoring(self) -> Dict[str, Any]:
        """Check governance monitoring health."""
        # In a real implementation, this would check governance monitoring health
        return {"status": "healthy", "message": "Governance monitoring is healthy"}
        
    async def validate_governance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate governance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Governance service is not connected"}
                
            # Check if governance is enabled
            if not self.governance_enabled:
                return {"status": "success", "message": "Governance is disabled"}
                
            # Get validation parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            
            # Validate framework
            if framework and framework not in self.governance_frameworks:
                return {"status": "error", "message": f"Unsupported governance framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.governance_checks:
                return {"status": "error", "message": f"Unsupported governance check: {check_type}"}
                
            # Create governance validation
            validation_id = str(uuid.uuid4())
            
            # Perform governance validation
            validation_result = await self._perform_governance_validation(framework, check_type, target, context)
            
            # Create governance report
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
            self._governance_reports.append(report)
            
            # Check if we need to prune old reports
            if len(self._governance_reports) > 100:  # Keep only the most recent 100 reports
                await self._prune_old_reports()
                
            return {
                "status": "success",
                "message": "Governance validation completed successfully",
                "validation_id": validation_id,
                "report_id": report["report_id"],
                "result": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error validating governance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _perform_governance_validation(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform governance validation."""
        # In a real implementation, this would perform actual governance validation
        
        # Simulate governance validation
        violations = []
        
        # Add some sample violations for demonstration
        if check_type == "policy_compliance":
            violations.append({
                "type": "minor",
                "description": "Some policies are not documented",
                "recommendation": "Document all policies and procedures"
            })
        elif check_type == "risk_management":
            violations.append({
                "type": "major",
                "description": "Risk assessment not performed regularly",
                "recommendation": "Perform regular risk assessments"
            })
        elif check_type == "control_effectiveness":
            violations.append({
                "type": "critical",
                "description": "Key controls not tested for effectiveness",
                "recommendation": "Test key controls for effectiveness regularly"
            })
        elif check_type == "stakeholder_communication":
            violations.append({
                "type": "minor",
                "description": "Stakeholder communication not documented",
                "recommendation": "Document all stakeholder communications"
            })
        elif check_type == "value_delivery":
            violations.append({
                "type": "major",
                "description": "Value delivery metrics not defined",
                "recommendation": "Define and track value delivery metrics"
            })
        elif check_type == "resource_optimization":
            violations.append({
                "type": "minor",
                "description": "Resource utilization not optimized",
                "recommendation": "Optimize resource utilization"
            })
            
        # Calculate governance score
        total_checks = 10  # Assume 10 governance checks
        critical_violations = sum(1 for v in violations if v["type"] == "critical")
        major_violations = sum(1 for v in violations if v["type"] == "major")
        minor_violations = sum(1 for v in violations if v["type"] == "minor")
        
        # Deduct points for violations
        score_deduction = (critical_violations * 25) + (major_violations * 15) + (minor_violations * 5)
        governance_score = max(0, 100 - score_deduction)
        
        # Determine overall status
        if governance_score >= 90:
            overall_status = "compliant"
        elif governance_score >= 75:
            overall_status = "partially_compliant"
        else:
            overall_status = "non_compliant"
            
        return {
            "framework": framework,
            "check_type": check_type,
            "target": target,
            "overall_status": overall_status,
            "governance_score": governance_score,
            "total_checks": total_checks,
            "passed_checks": total_checks - len(violations),
            "failed_checks": len(violations),
            "violations": violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _prune_old_reports(self) -> None:
        """Prune old governance reports."""
        # In a real implementation, this would prune old reports based on retention policy
        logger.info(f"Pruning old governance reports, current count: {len(self._governance_reports)}")
        
        # Sort by timestamp (oldest first)
        self._governance_reports.sort(key=lambda x: x["timestamp"])
        
        # Keep only the most recent reports
        self._governance_reports = self._governance_reports[-100:]
        
    async def monitor_governance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor governance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Governance service is not connected"}
                
            # Check if governance is enabled
            if not self.governance_enabled:
                return {"status": "success", "message": "Governance is disabled"}
                
            # Get monitoring parameters
            framework = data.get("framework") if data else None
            check_type = data.get("check_type") if data else None
            target = data.get("target") if data else None
            continuous = data.get("continuous", False) if data else False
            
            # Validate framework
            if framework and framework not in self.governance_frameworks:
                return {"status": "error", "message": f"Unsupported governance framework: {framework}"}
                
            # Validate check type
            if check_type and check_type not in self.governance_checks:
                return {"status": "error", "message": f"Unsupported governance check: {check_type}"}
                
            # Start governance monitoring
            if continuous:
                await self._start_continuous_governance_monitoring(framework, check_type, target, context)
                return {
                    "status": "success",
                    "message": "Continuous governance monitoring started successfully",
                    "framework": framework,
                    "check_type": check_type,
                    "target": target,
                    "continuous": True
                }
            else:
                # Perform one-time governance check
                result = await self.validate_governance(data, context)
                return result
                
        except Exception as e:
            logger.error(f"Error monitoring governance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _start_continuous_governance_monitoring(self, framework: Optional[str], check_type: Optional[str], target: Optional[str], context: Optional[Dict[str, Any]] = None) -> None:
        """Start continuous governance monitoring."""
        # In a real implementation, this would start continuous governance monitoring
        logger.info(f"Starting continuous governance monitoring for framework: {framework}, check: {check_type}, target: {target}")
        
    async def generate_governance_report(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a governance report.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Governance service is not connected"}
                
            # Get report parameters
            report_type = data.get("report_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            format_type = data.get("format", "json") if data else "json"
            
            # Filter governance reports based on parameters
            filtered_reports = self._governance_reports
            
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
                "message": "Governance report generated successfully",
                "report_type": report_type,
                "format_type": format_type,
                "report": formatted_report
            }
            
        except Exception as e:
            logger.error(f"Error generating governance report: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_summary_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary governance report."""
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
            
        # Calculate average governance score
        total_score = sum(report["result"]["governance_score"] for report in reports)
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
            "average_governance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_detailed_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed governance report."""
        return {
            "report_type": "detailed",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "reports": reports
        }
    
    async def _generate_framework_report(self, reports: List[Dict[str, Any]], framework: Optional[str]) -> Dict[str, Any]:
        """Generate a framework-specific governance report."""
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
            
        # Calculate average governance score
        total_score = sum(report["result"]["governance_score"] for report in framework_reports)
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
            "average_governance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _generate_violations_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a violations governance report."""
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
        
    async def analyze_governance(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze governance.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Governance service is not connected"}
                
            # Get analysis parameters
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            framework = data.get("framework") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            
            # Filter governance reports based on parameters
            filtered_reports = self._governance_reports
            
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
                "message": "Governance analysis completed successfully",
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing governance: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_summary(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze governance for summary statistics."""
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
            
        # Calculate average governance score
        total_score = sum(report["result"]["governance_score"] for report in reports)
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
            "average_governance_score": average_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "major_violations": major_violations,
            "minor_violations": minor_violations
        }
    
    async def _analyze_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze governance for trends."""
        # In a real implementation, this would analyze trends in the governance reports
        return {
            "analysis_type": "trends",
            "generated_at": datetime.now().isoformat(),
            "total_reports": len(reports),
            "message": "Trend analysis not implemented"
        }
    
    async def _analyze_violations(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze governance for violations."""
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
        """Analyze governance by frameworks."""
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
            # Calculate average governance score
            total_score = sum(report["result"]["governance_score"] for report in f_reports)
            average_score = total_score / len(f_reports) if f_reports else 0
                
            # Count violations
            total_violations = sum(len(report["result"]["violations"]) for report in f_reports)
            critical_violations = sum(report["result"]["critical_violations"] for report in f_reports)
            major_violations = sum(report["result"]["major_violations"] for report in f_reports)
            minor_violations = sum(report["result"]["minor_violations"] for report in f_reports)
                
            framework_stats[framework] = {
                "total_reports": len(f_reports),
                "average_governance_score": average_score,
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
        Get governance statistics.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Governance service is not connected"}
                
            # Get governance statistics
            governance_stats = {
                "governance_enabled": self.governance_enabled,
                "governance_frameworks": self.governance_frameworks,
                "governance_checks": self.governance_checks,
                "check_interval": self.check_interval,
                "alert_thresholds": self.alert_thresholds,
                "current_reports_count": len(self._governance_reports)
            }
            
            # Calculate statistics from reports
            if self._governance_reports:
                # Calculate average governance score
                total_score = sum(report["result"]["governance_score"] for report in self._governance_reports)
                average_score = total_score / len(self._governance_reports)
                
                # Count violations
                total_violations = sum(len(report["result"]["violations"]) for report in self._governance_reports)
                critical_violations = sum(report["result"]["critical_violations"] for report in self._governance_reports)
                major_violations = sum(report["result"]["major_violations"] for report in self._governance_reports)
                minor_violations = sum(report["result"]["minor_violations"] for report in self._governance_reports)
                
                # Count by status
                status_counts = {}
                for report in self._governance_reports:
                    status = report["result"]["overall_status"]
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                    
                governance_stats["average_governance_score"] = average_score
                governance_stats["total_violations"] = total_violations
                governance_stats["critical_violations"] = critical_violations
                governance_stats["major_violations"] = major_violations
                governance_stats["minor_violations"] = minor_violations
                governance_stats["status_counts"] = status_counts
            else:
                governance_stats["average_governance_score"] = 0
                governance_stats["total_violations"] = 0
                governance_stats["critical_violations"] = 0
                governance_stats["major_violations"] = 0
                governance_stats["minor_violations"] = 0
                governance_stats["status_counts"] = {}
                
            return {
                "status": "success",
                "message": "Governance statistics retrieved successfully",
                "governance_stats": governance_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting governance statistics: {str(e)}")
            return {"status": "error", "message": str(e)}