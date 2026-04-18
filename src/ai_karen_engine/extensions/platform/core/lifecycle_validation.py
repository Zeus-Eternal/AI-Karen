"""
Lifecycle Validation Service - Enforces strict lifecycle separation rules.

This service ensures that the three critical lifecycle separations are maintained:
1. Discovery ≠ Installation (discovered plugins don't auto-install)
2. Installation ≠ Registration (installed plugins don't auto-register)
3. Registration ≠ Mounting (registered plugins don't auto-mount)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from extensions.core.authority_chain import (
    AuthorityChainService,
    AuthorityLevel,
    LifecycleStage,
    AuthorityViolation,
    LifecycleViolation,
)

logger = logging.getLogger("kari.lifecycle_validation")


class ValidationSeverity(str, Enum):
    """Validation severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LifecycleViolationReport:
    """Report of lifecycle violations."""

    plugin_name: str
    violation_type: str
    severity: ValidationSeverity
    message: str
    current_stage: LifecycleStage
    forbidden_stage: LifecycleStage
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plugin_name": self.plugin_name,
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "message": self.message,
            "current_stage": self.current_stage.value,
            "forbidden_stage": self.forbidden_stage.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ValidationResult:
    """Result of lifecycle validation."""

    is_valid: bool
    violations: List[LifecycleViolationReport]
    warnings: List[LifecycleViolationReport]
    info: List[LifecycleViolationReport]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total_violations": len(self.violations),
                "total_warnings": len(self.warnings),
                "total_info": len(self.info),
            },
        }


class LifecycleValidationService:
    """
    Service that enforces strict lifecycle separation rules.

    This service prevents automatic progression between lifecycle stages,
    ensuring that each stage requires explicit authorization and validation.
    """

    def __init__(self, authority_chain_service: AuthorityChainService):
        """Initialize lifecycle validation service."""
        self.authority_chain = authority_chain_service
        self.validation_history: List[ValidationResult] = []

        logger.info("LifecycleValidationService initialized")

    def validate_discovery_installation_separation(
        self,
    ) -> List[LifecycleViolationReport]:
        """
        Validate that discovered plugins are not automatically installed.

        Rule: DISCOVERED ≠ INSTALLATION
        """
        violations = []

        discovered_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.DISCOVERED
        )
        installed_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.INSTALLED
        )

        # Check if any discovered plugins have been installed without explicit validation
        for plugin_name in discovered_plugins:
            if plugin_name in installed_plugins:
                violation = LifecycleViolationReport(
                    plugin_name=plugin_name,
                    violation_type="discovery_installation_violation",
                    severity=ValidationSeverity.CRITICAL,
                    message="Plugin discovered and installed without explicit validation",
                    current_stage=LifecycleStage.DISCOVERED,
                    forbidden_stage=LifecycleStage.INSTALLED,
                )
                violations.append(violation)
                logger.warning(
                    f"Discovery-Installation violation detected: {plugin_name}"
                )

        return violations

    def validate_installation_registration_separation(
        self,
    ) -> List[LifecycleViolationReport]:
        """
        Validate that installed plugins are not automatically registered.

        Rule: INSTALLATION ≠ REGISTRATION
        """
        violations = []

        installed_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.INSTALLED
        )
        registered_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.REGISTERED
        )

        # Check if any installed plugins have been registered without explicit validation
        for plugin_name in installed_plugins:
            if plugin_name in registered_plugins:
                violation = LifecycleViolationReport(
                    plugin_name=plugin_name,
                    violation_type="installation_registration_violation",
                    severity=ValidationSeverity.CRITICAL,
                    message="Plugin installed and registered without explicit validation",
                    current_stage=LifecycleStage.INSTALLED,
                    forbidden_stage=LifecycleStage.REGISTERED,
                )
                violations.append(violation)
                logger.warning(
                    f"Installation-Registration violation detected: {plugin_name}"
                )

        return violations

    def validate_registration_mounting_separation(
        self,
    ) -> List[LifecycleViolationReport]:
        """
        Validate that registered plugins are not automatically mounted.

        Rule: REGISTRATION ≠ MOUNTING
        """
        violations = []

        registered_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.REGISTERED
        )
        mounted_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.MOUNTED
        )
        enabled_plugins = self.authority_chain.get_plugins_by_lifecycle_stage(
            LifecycleStage.ENABLED
        )

        # Check if any registered plugins have been mounted without explicit validation
        for plugin_name in registered_plugins:
            if plugin_name in mounted_plugins or plugin_name in enabled_plugins:
                violation = LifecycleViolationReport(
                    plugin_name=plugin_name,
                    violation_type="registration_mounting_violation",
                    severity=ValidationSeverity.CRITICAL,
                    message="Plugin registered and mounted without explicit validation",
                    current_stage=LifecycleStage.REGISTERED,
                    forbidden_stage=LifecycleStage.MOUNTED,
                )
                violations.append(violation)
                logger.warning(
                    f"Registration-Mounting violation detected: {plugin_name}"
                )

        return violations

    def validate_stage_progression_authorization(
        self,
    ) -> List[LifecycleViolationReport]:
        """
        Validate that stage progressions are properly authorized.
        """
        violations = []

        for (
            plugin_name,
            authority_record,
        ) in self.authority_chain.authority_records.items():
            current_stage = authority_record.lifecycle_stage

            # Check if the plugin has appropriate authority for its current stage
            stage_authority_requirements = {
                LifecycleStage.DISCOVERED: AuthorityLevel.GUEST,
                LifecycleStage.DOWNLOADED: AuthorityLevel.USER,
                LifecycleStage.VALIDATED: AuthorityLevel.USER,
                LifecycleStage.INSTALLED: AuthorityLevel.PLUGIN,
                LifecycleStage.REGISTERED: AuthorityLevel.PLUGIN,
                LifecycleStage.MOUNTED: AuthorityLevel.FRONTEND,
                LifecycleStage.ENABLED: AuthorityLevel.FRONTEND,
                LifecycleStage.DISABLED: AuthorityLevel.FRONTEND,
            }

            required_authority = stage_authority_requirements.get(
                current_stage, AuthorityLevel.USER
            )

            if authority_record.authority_level.value < required_authority.value:
                violation = LifecycleViolationReport(
                    plugin_name=plugin_name,
                    violation_type="insufficient_authority",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Plugin at stage {current_stage.value} requires {required_authority.value} authority, has {authority_record.authority_level.value}",
                    current_stage=current_stage,
                    forbidden_stage=current_stage,  # Actually the same stage, but wrong authority
                )
                violations.append(violation)
                logger.warning(f"Insufficient authority violation: {plugin_name}")

        return violations

    def validate_category_restrictions(self) -> List[LifecycleViolationReport]:
        """
        Validate that plugins follow category restrictions.
        """
        violations = []

        # This would need to be implemented with actual category validation
        # For now, we'll check if plugins are in valid categories based on their authority level

        category_authority_mapping = {
            "plugins": AuthorityLevel.USER,
            "sys_extensions": AuthorityLevel.ADMIN,
            "channels": AuthorityLevel.PLUGIN,
        }

        for (
            plugin_name,
            authority_record,
        ) in self.authority_chain.authority_records.items():
            # For now, we'll assume plugins have a category field in their authority record
            # In a real implementation, this would come from the plugin manifest

            # Check if plugin authority level matches category requirements
            plugin_category = getattr(authority_record, "category", None)
            if plugin_category and plugin_category in category_authority_mapping:
                required_authority = category_authority_mapping[plugin_category]
                if authority_record.authority_level.value < required_authority.value:
                    violation = LifecycleViolationReport(
                        plugin_name=plugin_name,
                        violation_type="category_authority_mismatch",
                        severity=ValidationSeverity.WARNING,
                        message=f"Plugin category '{plugin_category}' requires {required_authority.value} authority, has {authority_record.authority_level.value}",
                        current_stage=authority_record.lifecycle_stage,
                        forbidden_stage=authority_record.lifecycle_stage,
                    )
                    violations.append(violation)
                    logger.warning(f"Category-Authority mismatch: {plugin_name}")

        return violations

    def run_comprehensive_validation(self) -> ValidationResult:
        """
        Run all lifecycle validations and return comprehensive results.
        """
        logger.info("Running comprehensive lifecycle validation")

        violations = []
        warnings = []
        info = []

        # Check the three critical separations
        violations.extend(self.validate_discovery_installation_separation())
        violations.extend(self.validate_installation_registration_separation())
        violations.extend(self.validate_registration_mounting_separation())

        # Check authority requirements
        violations.extend(self.validate_stage_progression_authorization())

        # Check category restrictions
        warnings.extend(self.validate_category_restrictions())

        # Add informational checks
        info.extend(self._get_lifecycle_statistics())

        result = ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            info=info,
        )

        # Store validation history
        self.validation_history.append(result)

        logger.info(
            f"Lifecycle validation completed: {len(violations)} violations, {len(warnings)} warnings, {len(info)} info"
        )
        return result

    def _get_lifecycle_statistics(self) -> List[LifecycleViolationReport]:
        """Get lifecycle stage statistics as informational reports."""
        stats = []

        stage_counts = {}
        for record in self.authority_chain.authority_records.values():
            stage = record.lifecycle_stage.value
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        for stage, count in stage_counts.items():
            stat = LifecycleViolationReport(
                plugin_name="system",
                violation_type="lifecycle_statistics",
                severity=ValidationSeverity.INFO,
                message=f"Stage '{stage}': {count} plugins",
                current_stage=LifecycleStage.DISCOVERED,  # Dummy value
                forbidden_stage=LifecycleStage.DISCOVERED,  # Dummy value
            )
            stats.append(stat)

        return stats

    def get_validation_history(self, limit: int = 10) -> List[ValidationResult]:
        """Get validation history."""
        return self.validation_history[-limit:]

    def validate_transition_request(
        self,
        plugin_name: str,
        from_stage: LifecycleStage,
        to_stage: LifecycleStage,
        requested_by: AuthorityLevel,
    ) -> Tuple[bool, List[str]]:
        """
        Validate a specific transition request.

        Args:
            plugin_name: Name of the plugin
            from_stage: Current lifecycle stage
            to_stage: Requested lifecycle stage
            requested_by: Authority level making the request

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            # Check if plugin exists
            authority_record = self.authority_chain.get_plugin_authority(plugin_name)
            if not authority_record:
                errors.append(f"Plugin not found: {plugin_name}")
                return False, errors

            # Check if transition is valid
            if not self.authority_chain.validate_lifecycle_transition(
                plugin_name, from_stage, to_stage
            ):
                errors.append(
                    f"Invalid transition: {from_stage.value} → {to_stage.value}"
                )
                return False, errors

            # Check authority boundary
            self.authority_chain.verify_authority_boundary(
                plugin_name, f"transition_to_{to_stage.value}", requested_by
            )

            # Check for rule violations
            if (
                from_stage == LifecycleStage.DISCOVERED
                and to_stage == LifecycleStage.INSTALLED
            ):
                errors.append("Cannot transition directly from DISCOVERED to INSTALLED")
                return False, errors

            if (
                from_stage == LifecycleStage.INSTALLED
                and to_stage == LifecycleStage.MOUNTED
            ):
                errors.append("Cannot transition directly from INSTALLED to MOUNTED")
                return False, errors

            if (
                from_stage == LifecycleStage.REGISTERED
                and to_stage == LifecycleStage.ENABLED
            ):
                errors.append("Cannot transition directly from REGISTERED to ENABLED")
                return False, errors

            return True, errors

        except AuthorityViolation as e:
            errors.append(f"Authority violation: {str(e)}")
            return False, errors
        except LifecycleViolation as e:
            errors.append(f"Lifecycle violation: {str(e)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors


# Global singleton instance
_lifecycle_validation_service: Optional[LifecycleValidationService] = None


def get_lifecycle_validation_service(
    authority_chain_service: AuthorityChainService,
) -> LifecycleValidationService:
    """Get the global lifecycle validation service instance."""
    global _lifecycle_validation_service
    if _lifecycle_validation_service is None:
        _lifecycle_validation_service = LifecycleValidationService(
            authority_chain_service
        )
    return _lifecycle_validation_service


__all__ = [
    "LifecycleValidationService",
    "ValidationSeverity",
    "LifecycleViolationReport",
    "ValidationResult",
    "get_lifecycle_validation_service",
]
