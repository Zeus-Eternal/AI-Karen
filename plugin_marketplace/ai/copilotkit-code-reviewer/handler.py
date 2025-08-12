"""
CopilotKit Code Reviewer Plugin

Extends existing code analysis plugins with CopilotKit review assistance features.
Provides comprehensive code review capabilities including security analysis,
performance assessment, best practices checking, and maintainability evaluation.
"""

# mypy: ignore-errors

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.service_registry import (
    get_service_registry,  # type: ignore[import-not-found]
)
from ai_karen_engine.hooks.hook_mixin import HookMixin  # type: ignore[import-not-found]
from ai_karen_engine.llm_orchestrator import (
    get_orchestrator,  # type: ignore[import-not-found]
)
from ai_karen_engine.services.memory_service import (  # type: ignore[import-not-found]
    MemoryType,
    UISource,
)

logger = logging.getLogger(__name__)


@dataclass
class ReviewFinding:
    """Represents a code review finding."""

    category: str
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: float = 0.8


@dataclass
class ReviewReport:
    """Comprehensive code review report."""

    overall_score: float
    findings: List[ReviewFinding] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    review_categories: Dict[str, float] = field(default_factory=dict)


class CopilotKitCodeReviewer(HookMixin):  # type: ignore[misc]
    """CopilotKit-powered code reviewer with comprehensive analysis capabilities."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "copilotkit_code_reviewer"
        self.orchestrator = get_orchestrator()

        # Review categories and their weights
        self.review_categories = {
            "security": 0.25,
            "performance": 0.20,
            "maintainability": 0.20,
            "readability": 0.15,
            "best_practices": 0.10,
            "testing": 0.05,
            "documentation": 0.05,
        }

        # Severity scoring
        self.severity_scores = {
            "critical": 0.0,
            "high": 0.2,
            "medium": 0.5,
            "low": 0.7,
            "info": 0.9,
        }

        # Register review hooks
        asyncio.create_task(self._register_review_hooks())

    async def _register_review_hooks(self) -> None:
        """Register code review hooks."""
        try:
            # Pre-execution validation hook
            await self.register_hook(
                "validate_review_request",
                self._validate_review_request,
                priority=10,
                source_name="code_reviewer_validation",
            )

            # Post-execution report generation hook
            await self.register_hook(
                "generate_review_report",
                self._generate_review_report,
                priority=80,
                source_name="code_reviewer_reporting",
            )

            # Error handling fallback hook
            await self.register_hook(
                "fallback_code_analysis",
                self._fallback_code_analysis,
                priority=95,
                source_name="code_reviewer_fallback",
            )

            logger.info("CopilotKit code reviewer hooks registered successfully")

        except Exception as e:
            logger.warning(f"Failed to register code reviewer hooks: {e}")

    async def _validate_review_request(
        self, context: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate code review request."""
        code = context.get("code", "")
        review_scope = context.get("review_scope", [])

        validation_result: Dict[str, Any] = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
        }

        # Validate code content
        if not code.strip():
            validation_result["valid"] = False
            validation_result["warnings"].append("No code provided for review")
            return validation_result

        # Check code length
        if len(code) > 50000:  # 50KB limit
            validation_result["warnings"].append(
                "Code is very large, review may take longer"
            )
            validation_result["suggestions"].append(
                "Consider breaking large files into smaller modules"
            )

        # Validate review scope
        if review_scope:
            invalid_categories = [
                cat for cat in review_scope if cat not in self.review_categories
            ]
            if invalid_categories:
                validation_result["warnings"].append(
                    f"Unknown review categories: {', '.join(invalid_categories)}"
                )
                validation_result["suggestions"].append(
                    f"Available categories: {', '.join(self.review_categories.keys())}"
                )

        return validation_result

    async def _generate_review_report(
        self, context: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive review report."""
        try:
            review_report = context.get("review_report")
            if not isinstance(review_report, ReviewReport):
                return {"generated": False, "error": "Invalid review report format"}

            # Generate summary statistics
            findings_by_severity = {}
            for finding in review_report.findings:
                severity = finding.severity
                if severity not in findings_by_severity:
                    findings_by_severity[severity] = 0
                findings_by_severity[severity] += 1

            # Generate formatted report
            report_sections = []

            # Executive summary
            report_sections.append("## Code Review Summary")
            report_sections.append(
                f"**Overall Score:** {review_report.overall_score:.1f}/10"
            )
            report_sections.append(f"**Total Findings:** {len(review_report.findings)}")
            report_sections.append("")

            # Findings by severity
            if findings_by_severity:
                report_sections.append("### Findings by Severity")
                for severity in ["critical", "high", "medium", "low", "info"]:
                    count = findings_by_severity.get(severity, 0)
                    if count > 0:
                        report_sections.append(f"- **{severity.title()}:** {count}")
                report_sections.append("")

            formatted_report = "\n".join(report_sections)

            return {
                "generated": True,
                "formatted_report": formatted_report,
                "findings_summary": findings_by_severity,
                "report_length": len(formatted_report),
            }

        except Exception as e:
            logger.error(f"Failed to generate review report: {e}")
            return {"generated": False, "error": str(e)}

    async def _fallback_code_analysis(
        self, context: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide fallback code analysis when CopilotKit is unavailable."""
        code = context.get("code", "")
        language = context.get("language", "python")

        # Basic static analysis
        findings = []

        # Language-specific basic checks
        if language == "python":
            findings.extend(await self._python_static_analysis(code))
        elif language in ["javascript", "typescript"]:
            findings.extend(await self._javascript_static_analysis(code))

        # Create basic review report
        review_report = ReviewReport(
            overall_score=max(1.0, 10.0 - len(findings) * 0.5),
            findings=findings,
            summary=f"Basic static analysis found {len(findings)} potential issues",
            recommendations=[
                "Consider using a specialized linter for more detailed analysis"
            ],
            metrics={"analysis_type": "fallback", "findings_count": len(findings)},
        )

        return {"review_report": review_report, "analysis_type": "fallback"}

    async def _python_static_analysis(self, code: str) -> List[ReviewFinding]:
        """Basic Python static analysis."""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for potential security issues
            if "eval(" in line_stripped:
                findings.append(
                    ReviewFinding(
                        category="security",
                        severity="high",
                        title="Use of eval() function",
                        description="eval() can execute arbitrary code and poses security risks",
                        line_number=i,
                        suggestion="Consider using ast.literal_eval() or alternative approaches",
                        code_snippet=line.strip(),
                    )
                )

            # Check for bare except clauses
            if line_stripped == "except:":
                findings.append(
                    ReviewFinding(
                        category="best_practices",
                        severity="medium",
                        title="Bare except clause",
                        description="Catching all exceptions can hide bugs",
                        line_number=i,
                        suggestion="Specify the exception type or use 'except Exception:'",
                        code_snippet=line.strip(),
                    )
                )

        return findings

    async def _javascript_static_analysis(self, code: str) -> List[ReviewFinding]:
        """Basic JavaScript/TypeScript static analysis."""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for == instead of ===
            if " == " in line_stripped and "==" not in line_stripped.replace(
                " == ", ""
            ):
                findings.append(
                    ReviewFinding(
                        category="best_practices",
                        severity="medium",
                        title="Use of == instead of ===",
                        description="Use strict equality (===) to avoid type coercion issues",
                        line_number=i,
                        suggestion="Replace == with === for strict equality",
                        code_snippet=line.strip(),
                    )
                )

        return findings

    async def _parse_analysis_response(
        self, response: str, category: str
    ) -> List[ReviewFinding]:
        """Parse CopilotKit analysis response into structured findings."""
        findings = []

        # Simple parsing - look for numbered items or bullet points
        lines = response.split("\n")
        current_finding = None

        for line in lines:
            line = line.strip()

            # Look for numbered findings or bullet points
            if (
                re.match(r"^\d+\.", line)
                or line.startswith("- ")
                or line.startswith("* ")
            ):
                if current_finding:
                    findings.append(current_finding)

                # Extract title
                title = re.sub(r"^\d+\.\s*|\-\s*|\*\s*", "", line)

                # Determine severity based on keywords
                severity = "medium"  # default
                if any(
                    word in line.lower() for word in ["critical", "severe", "dangerous"]
                ):
                    severity = "critical"
                elif any(
                    word in line.lower() for word in ["high", "important", "major"]
                ):
                    severity = "high"
                elif any(
                    word in line.lower() for word in ["low", "minor", "suggestion"]
                ):
                    severity = "low"
                elif any(word in line.lower() for word in ["info", "note", "consider"]):
                    severity = "info"

                current_finding = ReviewFinding(
                    category=category,
                    severity=severity,
                    title=title[:100],  # Limit title length
                    description=title,
                )

            elif current_finding and line:
                # Add to description
                current_finding.description += f" {line}"

        # Add last finding
        if current_finding:
            findings.append(current_finding)

        return findings[:10]  # Limit to 10 findings per category


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for CopilotKit code reviewer plugin.

    Args:
        params: Plugin parameters containing:
            - code: Code to review
            - language: Programming language (default: python)
            - review_scope: List of review categories
            - include_suggestions: Whether to include improvement suggestions
            - user_context: User context for personalization

    Returns:
        Dictionary containing code review results
    """
    try:
        # Initialize code reviewer
        code_reviewer: Any = CopilotKitCodeReviewer()

        # Extract parameters
        code = params.get("code", "")
        language = params.get("language", "python")
        review_scope = params.get("review_scope", [])
        user_context = params.get("user_context", {})

        # Validate input
        validation_context = {
            "code": code,
            "language": language,
            "review_scope": review_scope,
        }

        validation_result = await code_reviewer.trigger_hook_safe(
            "validate_review_request", validation_context, user_context
        )

        if not validation_result.get("valid", True):
            return {
                "success": False,
                "error": "Input validation failed",
                "validation_warnings": validation_result.get("warnings", []),
                "suggestions": validation_result.get("suggestions", []),
            }

        # Get LLM orchestrator for CopilotKit integration
        orchestrator = get_orchestrator()

        # Perform code review using CopilotKit
        if not review_scope:
            review_scope = ["security", "performance", "maintainability", "readability"]

        all_findings = []

        # Perform category-specific reviews
        for category in review_scope:
            try:
                # Create category-specific analysis prompt
                category_prompt = f"Analyze this {language} code for {category} issues and provide specific recommendations:\n\n```{language}\n{code}\n```"

                # Get analysis from enhanced routing
                analysis_response = await orchestrator.enhanced_route(category_prompt)

                # Parse response into findings (simplified)
                category_findings = await code_reviewer._parse_analysis_response(
                    analysis_response, category
                )
                all_findings.extend(category_findings)

            except Exception as e:
                logger.warning(f"Category review failed for {category}: {e}")
                continue

        # Calculate overall score
        overall_score = max(1.0, 10.0 - len(all_findings) * 0.3)

        # Create review report
        review_report = ReviewReport(
            overall_score=overall_score,
            findings=all_findings,
            summary=f"Code review completed with {len(all_findings)} findings across {len(review_scope)} categories",
            recommendations=[
                "Address high-priority findings first",
                "Consider adding unit tests",
            ],
            metrics={
                "total_findings": len(all_findings),
                "categories_reviewed": len(review_scope),
                "language": language,
                "code_length": len(code),
            },
        )

        # Generate formatted report
        report_context = {"review_report": review_report, "language": language}

        report_result = await code_reviewer.trigger_hook_safe(
            "generate_review_report", report_context, user_context
        )

        # Store review findings in long-term memory
        try:
            registry = get_service_registry()
            memory_service = await registry.get_service("memory_service")
            tenant_id = user_context.get("tenant_id")
            user_id = user_context.get("user_id", "unknown")
            if tenant_id and memory_service:
                await memory_service.store_web_ui_memory(
                    tenant_id=tenant_id,
                    content=report_result.get("formatted_report", ""),
                    user_id=user_id,
                    ui_source=UISource.API,
                    memory_type=MemoryType.INSIGHT,
                    tags=["code_review", "copilotkit"],
                    ai_generated=True,
                    metadata={
                        "plugin": "copilotkit_code_reviewer",
                        "overall_score": overall_score,
                        "findings_count": len(all_findings),
                        "categories": review_scope,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
        except Exception as mem_error:
            logger.warning(f"Failed to store review memory: {mem_error}")

        # Prepare response
        response = {
            "success": True,
            "language": language,
            "overall_score": overall_score,
            "findings_count": len(all_findings),
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "line_number": f.line_number,
                    "suggestion": f.suggestion,
                }
                for f in all_findings
            ],
            "formatted_report": report_result.get("formatted_report", ""),
            "validation_warnings": validation_result.get("warnings", []),
            "provider": "copilotkit_code_reviewer",
            "plugin_version": "1.0.0",
        }

        return response

    except Exception as e:
        logger.error(f"CopilotKit code reviewer failed: {e}")

        # Try fallback analysis
        try:
            fallback_reviewer: Any = CopilotKitCodeReviewer()
            fallback_context = {
                "code": params.get("code", ""),
                "language": params.get("language", "python"),
            }

            fallback_result = await fallback_reviewer.trigger_hook_safe(
                "fallback_code_analysis",
                fallback_context,
                params.get("user_context", {}),
            )

            review_report = fallback_result.get("review_report")

            return {
                "success": True,
                "language": params.get("language", "python"),
                "overall_score": review_report.overall_score if review_report else 5.0,
                "findings_count": len(review_report.findings) if review_report else 0,
                "findings": [
                    {
                        "category": f.category,
                        "severity": f.severity,
                        "title": f.title,
                        "description": f.description,
                        "line_number": f.line_number,
                        "suggestion": f.suggestion,
                    }
                    for f in (review_report.findings if review_report else [])
                ],
                "provider": "fallback_analyzer",
                "warning": "CopilotKit unavailable, using fallback analysis",
            }

        except Exception as fallback_error:
            logger.error(f"Fallback analysis also failed: {fallback_error}")
            return {
                "success": False,
                "error": str(e),
                "fallback_error": str(fallback_error),
                "provider": "copilotkit_code_reviewer",
            }


# Plugin metadata for discovery
__plugin_info__ = {
    "name": "copilotkit-code-reviewer",
    "version": "1.0.0",
    "description": "CopilotKit-powered code review assistance",
    "capabilities": [
        "code_review",
        "security_analysis",
        "performance_analysis",
        "best_practices_check",
    ],
    "supported_languages": [
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "rust",
        "go",
    ],
}
