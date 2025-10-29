"""
Extension Error Tracker

Tracks, analyzes, and manages errors that occur in extensions including
error classification, pattern detection, and automated resolution suggestions.
"""

import uuid
import traceback
import hashlib
from datetime import datetime, timedelta
from typing import (
    Dict, 
    List, 
    Optional, 
    Any, 
    Callable
    )
from collections import defaultdict, Counter
from dataclasses import dataclass
import re

from .models import ErrorRecord


@dataclass
class ErrorPattern:
    """Represents a pattern of similar errors."""
    pattern_id: str
    error_type: str
    message_pattern: str
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    extensions: List[str]
    stack_trace_hash: str
    resolution_suggestions: List[str]


@dataclass
class ErrorAnalysis:
    """Analysis results for error patterns and trends."""
    total_errors: int
    unique_errors: int
    error_rate: float
    top_error_types: List[tuple]  # (error_type, count)
    error_trends: Dict[str, List[int]]  # hourly error counts
    patterns: List[ErrorPattern]
    recommendations: List[str]


class ErrorClassifier:
    """Classifies errors into categories and suggests resolutions."""
    
    def __init__(self):
        self.classification_rules = {
            'network': {
                'patterns': [
                    r'connection.*timeout',
                    r'network.*unreachable',
                    r'dns.*resolution.*failed',
                    r'http.*error.*[45]\d\d',
                    r'ssl.*certificate.*error'
                ],
                'suggestions': [
                    'Check network connectivity',
                    'Verify API endpoints are accessible',
                    'Review SSL certificate configuration',
                    'Implement retry logic with exponential backoff'
                ]
            },
            'authentication': {
                'patterns': [
                    r'authentication.*failed',
                    r'unauthorized.*access',
                    r'invalid.*credentials',
                    r'token.*expired',
                    r'permission.*denied'
                ],
                'suggestions': [
                    'Verify API credentials are correct',
                    'Check token expiration and refresh logic',
                    'Review permission settings',
                    'Implement proper authentication error handling'
                ]
            },
            'database': {
                'patterns': [
                    r'database.*connection.*failed',
                    r'sql.*syntax.*error',
                    r'table.*does.*not.*exist',
                    r'constraint.*violation',
                    r'deadlock.*detected'
                ],
                'suggestions': [
                    'Check database connection settings',
                    'Verify database schema is up to date',
                    'Review SQL query syntax',
                    'Implement proper transaction handling'
                ]
            },
            'configuration': {
                'patterns': [
                    r'configuration.*error',
                    r'missing.*required.*parameter',
                    r'invalid.*configuration',
                    r'file.*not.*found.*config',
                    r'environment.*variable.*not.*set'
                ],
                'suggestions': [
                    'Review extension configuration',
                    'Check required parameters are set',
                    'Verify configuration file paths',
                    'Validate environment variables'
                ]
            },
            'resource': {
                'patterns': [
                    r'out.*of.*memory',
                    r'disk.*space.*full',
                    r'too.*many.*open.*files',
                    r'resource.*temporarily.*unavailable',
                    r'timeout.*exceeded'
                ],
                'suggestions': [
                    'Monitor resource usage',
                    'Implement resource cleanup',
                    'Add resource limits and monitoring',
                    'Optimize memory usage patterns'
                ]
            },
            'dependency': {
                'patterns': [
                    r'module.*not.*found',
                    r'import.*error',
                    r'dependency.*not.*available',
                    r'version.*mismatch',
                    r'plugin.*not.*found'
                ],
                'suggestions': [
                    'Check extension dependencies',
                    'Verify required plugins are installed',
                    'Review version compatibility',
                    'Update dependency manifest'
                ]
            }
        }
    
    def classify_error(self, error_record: ErrorRecord) -> tuple[str, List[str]]:
        """Classify error and provide resolution suggestions."""
        error_text = f"{error_record.error_message} {error_record.stack_trace}".lower()
        
        for category, rules in self.classification_rules.items():
            for pattern in rules['patterns']:
                if re.search(pattern, error_text, re.IGNORECASE):
                    return category, rules['suggestions']
        
        return 'unknown', ['Review error details and stack trace', 'Check extension logs for more context']


class ExtensionErrorTracker:
    """
    Tracks and analyzes errors that occur in extensions.
    
    Features:
    - Error recording and storage
    - Error pattern detection
    - Automatic error classification
    - Resolution suggestion system
    - Error trend analysis
    - Duplicate error detection
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        max_errors: int = 10000,
        pattern_detection_threshold: int = 3,
        debug_manager=None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.max_errors = max_errors
        self.pattern_detection_threshold = pattern_detection_threshold
        self.debug_manager = debug_manager
        
        # Error storage
        self.errors: List[ErrorRecord] = []
        self.error_patterns: Dict[str, ErrorPattern] = {}
        
        # Error classification
        self.classifier = ErrorClassifier()
        
        # Pattern detection
        self.stack_trace_hashes: Dict[str, List[str]] = defaultdict(list)  # hash -> error_ids
        self.message_patterns: Dict[str, List[str]] = defaultdict(list)  # pattern -> error_ids
        
        # Custom error handlers
        self.error_handlers: Dict[str, Callable] = {}
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> ErrorRecord:
        """Record a new error occurrence."""
        error_record = ErrorRecord(
            id=str(uuid.uuid4()),
            extension_id=self.extension_id,
            extension_name=self.extension_name,
            timestamp=datetime.utcnow(),
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context or {},
            correlation_id=correlation_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Add to storage
        self.errors.append(error_record)
        
        # Maintain max size
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Detect patterns
        self._detect_patterns(error_record)
        
        # Classify error
        category, suggestions = self.classifier.classify_error(error_record)
        error_record.context['category'] = category
        error_record.context['suggestions'] = suggestions
        
        # Call custom handlers
        self._call_error_handlers(error_record)
        
        # Notify debug manager
        if self.debug_manager:
            self.debug_manager.add_error_record(error_record)
        
        return error_record
    
    def record_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> ErrorRecord:
        """Record an exception as an error."""
        return self.record_error(
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            context=context,
            correlation_id=correlation_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
    
    def register_error_handler(self, error_type: str, handler: Callable[[ErrorRecord], None]):
        """Register a custom error handler for specific error types."""
        self.error_handlers[error_type] = handler
    
    def get_errors(
        self,
        error_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        resolved_only: bool = False,
        unresolved_only: bool = False
    ) -> List[ErrorRecord]:
        """Get errors with optional filtering."""
        errors = self.errors
        
        # Filter by error type
        if error_type:
            errors = [e for e in errors if e.error_type == error_type]
        
        # Filter by time
        if since:
            errors = [e for e in errors if e.timestamp >= since]
        
        # Filter by resolution status
        if resolved_only:
            errors = [e for e in errors if e.resolved]
        elif unresolved_only:
            errors = [e for e in errors if not e.resolved]
        
        # Apply limit
        if limit:
            errors = errors[-limit:]
        
        return errors
    
    def get_error_patterns(self) -> List[ErrorPattern]:
        """Get detected error patterns."""
        return list(self.error_patterns.values())
    
    def get_error_analysis(self, time_window: timedelta = timedelta(hours=24)) -> ErrorAnalysis:
        """Get comprehensive error analysis."""
        since = datetime.utcnow() - time_window
        recent_errors = self.get_errors(since=since)
        
        if not recent_errors:
            return ErrorAnalysis(
                total_errors=0,
                unique_errors=0,
                error_rate=0.0,
                top_error_types=[],
                error_trends={},
                patterns=[],
                recommendations=[]
            )
        
        # Basic statistics
        total_errors = len(recent_errors)
        unique_error_types = len(set(e.error_type for e in recent_errors))
        
        # Error rate (errors per hour)
        hours = time_window.total_seconds() / 3600
        error_rate = total_errors / hours
        
        # Top error types
        error_type_counts = Counter(e.error_type for e in recent_errors)
        top_error_types = error_type_counts.most_common(10)
        
        # Error trends (hourly buckets)
        error_trends = self._calculate_error_trends(recent_errors, time_window)
        
        # Get patterns
        patterns = [p for p in self.error_patterns.values() 
                   if p.last_seen >= since]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(recent_errors, patterns)
        
        return ErrorAnalysis(
            total_errors=total_errors,
            unique_errors=unique_error_types,
            error_rate=error_rate,
            top_error_types=top_error_types,
            error_trends=error_trends,
            patterns=patterns,
            recommendations=recommendations
        )
    
    def resolve_error(self, error_id: str, resolution_notes: str):
        """Mark an error as resolved."""
        for error in self.errors:
            if error.id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                break
    
    def resolve_pattern(self, pattern_id: str, resolution_notes: str):
        """Mark all errors in a pattern as resolved."""
        pattern = self.error_patterns.get(pattern_id)
        if not pattern:
            return
        
        # Find all errors matching this pattern
        for error in self.errors:
            if (error.error_type == pattern.error_type and 
                self._get_stack_trace_hash(error.stack_trace) == pattern.stack_trace_hash):
                error.resolved = True
                error.resolution_notes = resolution_notes
    
    def export_errors(self, format: str = "json") -> str:
        """Export errors in specified format."""
        errors = self.get_errors()
        
        if format.lower() == "json":
            import json
            return json.dumps([e.to_dict() for e in errors], indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if errors:
                fieldnames = ['id', 'timestamp', 'error_type', 'error_message', 'resolved']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for error in errors:
                    writer.writerow({
                        'id': error.id,
                        'timestamp': error.timestamp.isoformat(),
                        'error_type': error.error_type,
                        'error_message': error.error_message,
                        'resolved': error.resolved
                    })
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _detect_patterns(self, error_record: ErrorRecord):
        """Detect if this error is part of a pattern."""
        # Generate stack trace hash
        stack_hash = self._get_stack_trace_hash(error_record.stack_trace)
        self.stack_trace_hashes[stack_hash].append(error_record.id)
        
        # Check if we have enough occurrences to form a pattern
        if len(self.stack_trace_hashes[stack_hash]) >= self.pattern_detection_threshold:
            self._create_or_update_pattern(error_record, stack_hash)
    
    def _create_or_update_pattern(self, error_record: ErrorRecord, stack_hash: str):
        """Create or update an error pattern."""
        pattern_id = f"{error_record.error_type}_{stack_hash[:8]}"
        
        if pattern_id in self.error_patterns:
            # Update existing pattern
            pattern = self.error_patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_seen = error_record.timestamp
            if self.extension_id not in pattern.extensions:
                pattern.extensions.append(self.extension_id)
        else:
            # Create new pattern
            message_pattern = self._extract_message_pattern(error_record.error_message)
            
            pattern = ErrorPattern(
                pattern_id=pattern_id,
                error_type=error_record.error_type,
                message_pattern=message_pattern,
                occurrences=len(self.stack_trace_hashes[stack_hash]),
                first_seen=error_record.timestamp,
                last_seen=error_record.timestamp,
                extensions=[self.extension_id],
                stack_trace_hash=stack_hash,
                resolution_suggestions=error_record.context.get('suggestions', [])
            )
            
            self.error_patterns[pattern_id] = pattern
    
    def _get_stack_trace_hash(self, stack_trace: str) -> str:
        """Generate a hash for stack trace to identify similar errors."""
        # Normalize stack trace by removing line numbers and file paths
        normalized = re.sub(r'line \d+', 'line XXX', stack_trace)
        normalized = re.sub(r'File ".*?([^/\\]+\.py)"', r'File "\1"', normalized)
        
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _extract_message_pattern(self, message: str) -> str:
        """Extract a pattern from error message by replacing variable parts."""
        # Replace numbers with placeholders
        pattern = re.sub(r'\b\d+\b', 'N', message)
        
        # Replace UUIDs with placeholders
        pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', pattern)
        
        # Replace file paths with placeholders
        pattern = re.sub(r'/[^\s]+', '/PATH', pattern)
        
        # Replace URLs with placeholders
        pattern = re.sub(r'https?://[^\s]+', 'URL', pattern)
        
        return pattern
    
    def _calculate_error_trends(self, errors: List[ErrorRecord], time_window: timedelta) -> Dict[str, List[int]]:
        """Calculate hourly error trends."""
        now = datetime.utcnow()
        hours = int(time_window.total_seconds() / 3600)
        
        # Initialize hourly buckets
        hourly_counts = [0] * hours
        
        for error in errors:
            # Calculate which hour bucket this error belongs to
            hours_ago = (now - error.timestamp).total_seconds() / 3600
            bucket_index = int(hours_ago)
            
            if 0 <= bucket_index < hours:
                hourly_counts[hours - 1 - bucket_index] += 1
        
        return {
            'hourly_counts': hourly_counts,
            'labels': [f"{i}h ago" for i in range(hours, 0, -1)]
        }
    
    def _generate_recommendations(self, errors: List[ErrorRecord], patterns: List[ErrorPattern]) -> List[str]:
        """Generate recommendations based on error analysis."""
        recommendations = []
        
        if not errors:
            return recommendations
        
        # High error rate recommendation
        if len(errors) > 50:  # More than 50 errors in time window
            recommendations.append("High error rate detected. Consider implementing circuit breaker pattern.")
        
        # Pattern-based recommendations
        if patterns:
            recommendations.append(f"Found {len(patterns)} error patterns. Focus on resolving the most frequent patterns first.")
        
        # Category-based recommendations
        categories = [e.context.get('category', 'unknown') for e in errors]
        category_counts = Counter(categories)
        
        for category, count in category_counts.most_common(3):
            if category != 'unknown' and count > 5:
                recoations.append(f"High number of {category} errors ({count}). Review {category} configuration and handling.")
        
        # Unresolved errors recommendation
        unresolved_count = len([e for e in errors if not e.resolved])
        if unresolved_count > 10:
            recommendations.append(f"{unresolved_count} unresolved errors. Consider implementing automated error resolution for common patterns.")
        
        return recommendations
    
    def _call_error_handlers(self, error_record: ErrorRecord):
        """Call registered error handlers."""
        # Call specific handler for this error type
        handler = self.error_handlers.get(error_record.error_type)
        if handler:
            try:
                handler(error_record)
            except Exception as e:
                # Don't let handler errors break error recording
                pass
        
        # Call generic handler
        generic_handler = self.error_handlers.get('*')
        if generic_handler:
            try:
                generic_handler(error_record)
            except Exception as e:
                pass