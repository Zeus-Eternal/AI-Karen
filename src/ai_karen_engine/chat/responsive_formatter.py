"""
Responsive Formatting System for Different Display Sizes

This module provides responsive formatting that adapts content presentation
based on display context, screen size, and device capabilities.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from .response_formatting_models import (
        DisplayContext, LayoutType, ContentType, AccessibilityLevel
    )
except ImportError:
    # Fallback imports for circular dependency
    from enum import Enum
    
    class DisplayContext(Enum):
        DESKTOP = "desktop"
        MOBILE = "mobile"
        TABLET = "tablet"
        TERMINAL = "terminal"
        API = "api"
        PRINT = "print"
        EMBEDDED = "embedded"
        VOICE = "voice"
    
    class LayoutType(Enum):
        DEFAULT = "default"
        MENU = "menu"
        MOVIE_LIST = "movie_list"
        BULLET_LIST = "bullet_list"
        SYSTEM_STATUS = "system_status"
        CODE_BLOCK = "code_block"
        TABLE = "table"
        STEPS = "steps"
        COMPARISON = "comparison"
        TIMELINE = "timeline"
        TREE = "tree"
        GRID = "grid"
        ACCORDION = "accordion"
        TABS = "tabs"
    
    class ContentType(Enum):
        TEXT = "text"
        CODE = "code"
        MARKDOWN = "markdown"
        JSON = "json"
        XML = "xml"
        YAML = "yaml"
        SQL = "sql"
        HTML = "html"
        CSS = "css"
        JAVASCRIPT = "javascript"
        PYTHON = "python"
        DATA_TABLE = "data_table"
        LIST = "list"
        MENU = "menu"
        STEPS = "steps"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        SUCCESS = "success"
    
    class AccessibilityLevel(Enum):
        BASIC = "basic"
        ENHANCED = "enhanced"
        FULL = "full"
        SCREEN_READER = "screen_reader"

logger = logging.getLogger(__name__)


class ScreenSize(Enum):
    """Screen size categories."""
    EXTRA_SMALL = "extra_small"  # < 576px
    SMALL = "small"           # 576px - 768px
    MEDIUM = "medium"         # 768px - 992px
    LARGE = "large"           # 992px - 1200px
    EXTRA_LARGE = "extra_large" # > 1200px


class DeviceType(Enum):
    """Device type categories."""
    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    TV = "tv"
    WEARABLE = "wearable"
    UNKNOWN = "unknown"


@dataclass
class ResponsiveConfig:
    """Configuration for responsive formatting."""
    display_context: DisplayContext
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    device_pixel_ratio: float = 1.0
    touch_enabled: bool = False
    high_dpi: bool = False
    prefers_reduced_motion: bool = False
    prefers_dark_theme: bool = False
    max_width_chars: int = 80  # For terminal contexts
    max_height_lines: int = 24  # For terminal contexts


@dataclass
class ResponsiveBreakpoint:
    """Responsive breakpoint definition."""
    name: str
    min_width: int
    max_width: Optional[int] = None
    layout_adaptations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponsiveLayout:
    """Responsive layout definition."""
    base_layout: LayoutType
    breakpoints: List[ResponsiveBreakpoint]
    mobile_fallback: Optional[LayoutType] = None
    tablet_adaptation: Optional[Dict[str, Any]] = None
    desktop_enhancements: Optional[Dict[str, Any]] = None


class ResponsiveFormatter:
    """
    Advanced responsive formatting system with multi-device support.
    
    This class provides:
    - Responsive layout adaptation
    - Device-specific formatting
    - Screen size optimization
    - Touch interface support
    - Accessibility adaptation
    - Performance optimization for different devices
    """
    
    def __init__(self):
        """Initialize responsive formatter."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize responsive breakpoints
        self._init_breakpoints()
        
        # Initialize device detection patterns
        self._init_device_patterns()
        
        # Initialize layout adaptations
        self._init_layout_adaptations()
        
        # Performance metrics
        self._performance_metrics = {
            "total_formatting": 0,
            "responsive_adaptations": 0,
            "device_detections": 0,
            "breakpoint_matches": 0,
            "average_processing_time": 0.0
        }
        
        self.logger.info("ResponsiveFormatter initialized")
    
    def _init_breakpoints(self):
        """Initialize responsive breakpoints."""
        self.breakpoints = {
            'extra_small': ResponsiveBreakpoint(
                name='extra_small',
                min_width=0,
                max_width=575,
                layout_adaptations={
                    'simplify_tables': True,
                    'collapse_menus': True,
                    'single_column': True,
                    'reduce_font_size': True,
                    'hide_non_essential': True
                }
            ),
            'small': ResponsiveBreakpoint(
                name='small',
                min_width=576,
                max_width=767,
                layout_adaptations={
                    'simplify_tables': True,
                    'compact_layout': True,
                    'stack_vertical': True,
                    'reduce_spacing': True
                }
            ),
            'medium': ResponsiveBreakpoint(
                name='medium',
                min_width=768,
                max_width=991,
                layout_adaptations={
                    'two_column_layout': True,
                    'optimized_tables': True,
                    'balanced_spacing': True
                }
            ),
            'large': ResponsiveBreakpoint(
                name='large',
                min_width=992,
                max_width=1199,
                layout_adaptations={
                    'multi_column_layout': True,
                    'enhanced_features': True,
                    'full_width_content': True
                }
            ),
            'extra_large': ResponsiveBreakpoint(
                name='extra_large',
                min_width=1200,
                max_width=None,
                layout_adaptations={
                    'max_columns': True,
                    'side_by_side_layout': True,
                    'advanced_features': True
                }
            )
        }
    
    def _init_device_patterns(self):
        """Initialize device detection patterns."""
        self.device_patterns = {
            'phone': {
                'user_agents': [
                    r'iPhone', r'Android.*Mobile', r'Windows Phone',
                    r'BlackBerry', r'Opera Mini', r'IEMobile'
                ],
                'screen_ranges': [(0, 767)],
                'touch_fallback': True,
                'simplified_ui': True
            },
            'tablet': {
                'user_agents': [
                    r'iPad', r'Android.*Tablet', r'Tablet',
                    r'Silk', r'Kindle', r'PlayBook'
                ],
                'screen_ranges': [(768, 1023)],
                'touch_fallback': True,
                'adaptive_layout': True
            },
            'desktop': {
                'user_agents': [
                    r'Windows NT', r'Macintosh', r'Linux',
                    r'X11', r'Ubuntu', r'Chrome.*Desktop'
                ],
                'screen_ranges': [(1024, None)],
                'mouse_input': True,
                'full_features': True
            },
            'tv': {
                'user_agents': [
                    r'TV', r'Smart-TV', r'GoogleTV', r'AppleTV'
                ],
                'screen_ranges': [(1920, None)],
                'large_text': True,
                'simplified_navigation': True
            }
        }
    
    def _init_layout_adaptations(self):
        """Initialize layout adaptation rules."""
        self.layout_adaptations = {
            # Table adaptations
            'table': {
                'extra_small': self._adapt_table_for_mobile,
                'small': self._adapt_table_for_mobile,
                'medium': self._adapt_table_for_tablet,
                'large': self._adapt_table_for_desktop,
                'extra_large': self._adapt_table_for_desktop
            },
            # List adaptations
            'list': {
                'extra_small': self._adapt_list_for_mobile,
                'small': self._adapt_list_for_mobile,
                'medium': self._adapt_list_for_tablet,
                'large': self._adapt_list_for_desktop,
                'extra_large': self._adapt_list_for_desktop
            },
            # Code block adaptations
            'code': {
                'extra_small': self._adapt_code_for_mobile,
                'small': self._adapt_code_for_mobile,
                'medium': self._adapt_code_for_tablet,
                'large': self._adapt_code_for_desktop,
                'extra_large': self._adapt_code_for_desktop
            },
            # Navigation adaptations
            'navigation': {
                'extra_small': self._adapt_navigation_for_mobile,
                'small': self._adapt_navigation_for_mobile,
                'medium': self._adapt_navigation_for_tablet,
                'large': self._adapt_navigation_for_desktop,
                'extra_large': self._adapt_navigation_for_desktop
            }
        }
    
    async def format_responsive(
        self,
        content: str,
        config: ResponsiveConfig,
        layout_type: LayoutType
    ) -> Dict[str, Any]:
        """
        Format content responsively based on display configuration.
        
        Args:
            content: Content to format
            config: Responsive configuration
            layout_type: Base layout type
            
        Returns:
            Dictionary with responsive formatting results
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.debug(
                f"Formatting content for {config.display_context.value} "
                f"({config.screen_width}x{config.screen_height})"
            )
            
            # Detect device type
            device_type = self._detect_device_type(config)
            
            # Determine screen size category
            screen_size = self._determine_screen_size(config.screen_width)
            
            # Get active breakpoint
            active_breakpoint = self._get_active_breakpoint(config.screen_width)
            
            # Apply responsive adaptations
            adapted_content = await self._apply_responsive_adaptations(
                content, layout_type, screen_size, device_type, config
            )
            
            # Generate responsive metadata
            responsive_metadata = self._generate_responsive_metadata(
                config, device_type, screen_size, active_breakpoint
            )
            
            # Create result
            result = {
                'content': adapted_content,
                'layout_type': layout_type.value,
                'display_context': config.display_context.value,
                'device_type': device_type.value,
                'screen_size': screen_size.value,
                'active_breakpoint': active_breakpoint.name if active_breakpoint else 'default',
                'responsive_metadata': responsive_metadata,
                'css_classes': self._generate_responsive_css_classes(
                    device_type, screen_size, active_breakpoint
                ),
                'javascript_enhancements': self._generate_javascript_enhancements(
                    device_type, config
                ),
                'accessibility_adaptations': self._generate_accessibility_adaptations(
                    device_type, config
                )
            }
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(device_type, processing_time)
            
            self.logger.debug(
                f"Responsive formatting completed in {processing_time:.4f}s "
                f"for {device_type.value}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in responsive formatting: {e}")
            # Return basic formatting on error
            return {
                'content': content,
                'layout_type': layout_type.value,
                'display_context': config.display_context.value,
                'device_type': 'unknown',
                'screen_size': 'medium',
                'error': str(e)
            }
    
    def _detect_device_type(self, config: ResponsiveConfig) -> DeviceType:
        """Detect device type based on configuration."""
        # For terminal context, always return desktop-like behavior
        if config.display_context == DisplayContext.TERMINAL:
            return DeviceType.DESKTOP
        
        # For API context, device doesn't matter
        if config.display_context == DisplayContext.API:
            return DeviceType.UNKNOWN
        
        # Check screen width for basic device detection
        if config.screen_width:
            if config.screen_width <= 767:
                return DeviceType.PHONE
            elif config.screen_width <= 1023:
                return DeviceType.TABLET
            else:
                return DeviceType.DESKTOP
        
        # Default to desktop if no width information
        return DeviceType.DESKTOP
    
    def _determine_screen_size(self, width: Optional[int]) -> ScreenSize:
        """Determine screen size category."""
        if width is None:
            return ScreenSize.MEDIUM
        
        if width < 576:
            return ScreenSize.EXTRA_SMALL
        elif width < 768:
            return ScreenSize.SMALL
        elif width < 992:
            return ScreenSize.MEDIUM
        elif width < 1200:
            return ScreenSize.LARGE
        else:
            return ScreenSize.EXTRA_LARGE
    
    def _get_active_breakpoint(self, width: Optional[int]) -> Optional[ResponsiveBreakpoint]:
        """Get the active breakpoint for screen width."""
        if width is None:
            return None
        
        for breakpoint in self.breakpoints.values():
            if width >= breakpoint.min_width:
                if breakpoint.max_width is None or width <= breakpoint.max_width:
                    return breakpoint
        
        return None
    
    async def _apply_responsive_adaptations(
        self,
        content: str,
        layout_type: LayoutType,
        screen_size: ScreenSize,
        device_type: DeviceType,
        config: ResponsiveConfig
    ) -> str:
        """Apply responsive adaptations to content."""
        # Get layout adaptation function
        layout_key = layout_type.value.lower()
        adaptations = self.layout_adaptations.get(layout_key, {})
        
        # Get adaptation function for screen size
        adaptation_func = adaptations.get(screen_size.value)
        
        if adaptation_func:
            adapted_content = adaptation_func(content, config)
            self.logger.debug(
                f"Applied {screen_size.value} adaptation for {layout_type.value}"
            )
            return adapted_content
        
        # No specific adaptation, return original content
        return content
    
    def _adapt_table_for_mobile(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt table for mobile devices."""
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            # Simplify table structure
            if '|' in line:
                # Convert to simple list format
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) > 2:
                    # Create bullet points from table cells
                    adapted_lines.append(f"• {cells[1]}")
                else:
                    adapted_lines.append(line)
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_table_for_tablet(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt table for tablet devices."""
        # For tablets, keep table structure but optimize width
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            if '|' in line:
                # Add responsive table class
                adapted_lines.append(f'<div class="table-responsive">{line}</div>')
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_table_for_desktop(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt table for desktop devices."""
        # For desktop, enhance table with sorting and filtering
        lines = content.split('\n')
        adapted_lines = []
        
        # Add table enhancement wrapper
        adapted_lines.append('<div class="table-enhanced">')
        adapted_lines.extend(lines)
        adapted_lines.append('</div>')
        
        return '\n'.join(adapted_lines)
    
    def _adapt_list_for_mobile(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt list for mobile devices."""
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            # Simplify list items
            if re.match(r'^\s*[-*+]\s+', line):
                # Keep bullet points but make them more touch-friendly
                item_text = re.sub(r'^\s*[-*+]\s+', '', line).strip()
                adapted_lines.append(f'<div class="touch-target">• {item_text}</div>')
            elif re.match(r'^\s*\d+\.\s+', line):
                # Convert numbered lists to simple bullets
                item_text = re.sub(r'^\s*\d+\.\s+', '', line).strip()
                adapted_lines.append(f'<div class="touch-target">• {item_text}</div>')
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_list_for_tablet(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt list for tablet devices."""
        # For tablets, enhance list with better spacing
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            if re.match(r'^\s*[-*+\d]\.', line):
                # Add touch-friendly list styling
                adapted_lines.append(f'<div class="list-item-tablet">{line}</div>')
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_list_for_desktop(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt list for desktop devices."""
        # For desktop, enhance with hover effects and interactions
        lines = content.split('\n')
        adapted_lines = []
        
        # Add list enhancement wrapper
        adapted_lines.append('<div class="list-enhanced">')
        adapted_lines.extend(lines)
        adapted_lines.append('</div>')
        
        return '\n'.join(adapted_lines)
    
    def _adapt_code_for_mobile(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt code blocks for mobile devices."""
        # For mobile, simplify code display and add horizontal scrolling
        lines = content.split('\n')
        adapted_lines = []
        
        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                adapted_lines.append(line)
            elif in_code_block:
                # Wrap long lines in scrollable container
                if len(line) > config.max_width_chars:
                    adapted_lines.append(f'<div class="code-scrollable">{line}</div>')
                else:
                    adapted_lines.append(line)
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_code_for_tablet(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt code blocks for tablet devices."""
        # For tablets, optimize code readability
        lines = content.split('\n')
        adapted_lines = []
        
        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                adapted_lines.append(line)
            elif in_code_block:
                # Add tablet-specific code styling
                adapted_lines.append(f'<div class="code-tablet">{line}</div>')
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_code_for_desktop(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt code blocks for desktop devices."""
        # For desktop, enhance with line numbers and copy functionality
        lines = content.split('\n')
        adapted_lines = []
        
        in_code_block = False
        line_number = 1
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                adapted_lines.append(line)
            elif in_code_block:
                # Add desktop code enhancements
                adapted_lines.append(
                    f'<div class="code-desktop" data-line="{line_number}">{line}</div>'
                )
                line_number += 1
            else:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def _adapt_navigation_for_mobile(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt navigation for mobile devices."""
        # For mobile, convert to hamburger menu and touch targets
        return f'<nav class="nav-mobile">{content}</nav>'
    
    def _adapt_navigation_for_tablet(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt navigation for tablet devices."""
        # For tablets, optimize for touch but keep more visible items
        return f'<nav class="nav-tablet">{content}</nav>'
    
    def _adapt_navigation_for_desktop(self, content: str, config: ResponsiveConfig) -> str:
        """Adapt navigation for desktop devices."""
        # For desktop, enhance with hover states and full menus
        return f'<nav class="nav-desktop">{content}</nav>'
    
    def _generate_responsive_metadata(
        self,
        config: ResponsiveConfig,
        device_type: DeviceType,
        screen_size: ScreenSize,
        active_breakpoint: Optional[ResponsiveBreakpoint]
    ) -> Dict[str, Any]:
        """Generate metadata for responsive formatting."""
        metadata = {
            'device_type': device_type.value,
            'screen_size': screen_size.value,
            'screen_width': config.screen_width,
            'screen_height': config.screen_height,
            'pixel_ratio': config.device_pixel_ratio,
            'touch_enabled': config.touch_enabled,
            'high_dpi': config.high_dpi,
            'prefers_reduced_motion': config.prefers_reduced_motion,
            'prefers_dark_theme': config.prefers_dark_theme,
            'breakpoint_name': active_breakpoint.name if active_breakpoint else None,
            'breakpoint_adaptations': active_breakpoint.layout_adaptations if active_breakpoint else {}
        }
        
        # Add device-specific metadata
        if device_type == DeviceType.PHONE:
            metadata.update({
                'primary_input': 'touch',
                'screen_orientation': 'variable',
                'network_considerations': True
            })
        elif device_type == DeviceType.TABLET:
            metadata.update({
                'primary_input': 'touch',
                'screen_orientation': 'variable',
                'keyboard_availability': 'optional'
            })
        elif device_type == DeviceType.DESKTOP:
            metadata.update({
                'primary_input': 'mouse',
                'screen_orientation': 'landscape',
                'full_keyboard_available': True
            })
        
        return metadata
    
    def _generate_responsive_css_classes(
        self,
        device_type: DeviceType,
        screen_size: ScreenSize,
        active_breakpoint: Optional[ResponsiveBreakpoint]
    ) -> List[str]:
        """Generate CSS classes for responsive design."""
        classes = [
            'responsive-formatted',
            f'device-{device_type.value}',
            f'screen-{screen_size.value}'
        ]
        
        if active_breakpoint:
            classes.append(f'breakpoint-{active_breakpoint.name}')
            
            # Add breakpoint-specific classes
            adaptations = active_breakpoint.layout_adaptations
            for adaptation, enabled in adaptations.items():
                if enabled:
                    classes.append(f'adaptation-{adaptation}')
        
        return classes
    
    def _generate_javascript_enhancements(
        self,
        device_type: DeviceType,
        config: ResponsiveConfig
    ) -> List[str]:
        """Generate JavaScript enhancements for different devices."""
        enhancements = []
        
        if device_type in [DeviceType.PHONE, DeviceType.TABLET]:
            if config.touch_enabled:
                enhancements.extend([
                    'touch-event-listeners',
                    'swipe-gestures',
                    'virtual-keyboard-support'
                ])
        
        if config.prefers_reduced_motion:
            enhancements.append('reduced-motion-support')
        
        if config.high_dpi:
            enhancements.append('high-dpi-optimization')
        
        return enhancements
    
    def _generate_accessibility_adaptations(
        self,
        device_type: DeviceType,
        config: ResponsiveConfig
    ) -> List[str]:
        """Generate accessibility adaptations for different devices."""
        adaptations = []
        
        if device_type == DeviceType.PHONE:
            adaptations.extend([
                'large-touch-targets',
                'voice-control-support',
                'screen-reader-optimization'
            ])
        elif device_type == DeviceType.TABLET:
            adaptations.extend([
                'medium-touch-targets',
                'gesture-support',
                'adjustable-text-size'
            ])
        elif device_type == DeviceType.DESKTOP:
            adaptations.extend([
                'keyboard-navigation',
                'screen-reader-support',
                'high-contrast-mode'
            ])
        
        if config.prefers_dark_theme:
            adaptations.append('dark-theme-support')
        
        return adaptations
    
    def _update_performance_metrics(self, device_type: DeviceType, processing_time: float):
        """Update performance metrics."""
        self._performance_metrics["total_formatting"] += 1
        self._performance_metrics["responsive_adaptations"] += 1
        self._performance_metrics["device_detections"] += 1
        
        # Update average processing time
        total = self._performance_metrics["total_formatting"]
        current_avg = self._performance_metrics["average_processing_time"]
        self._performance_metrics["average_processing_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """Reset performance metrics."""
        self._performance_metrics = {
            "total_formatting": 0,
            "responsive_adaptations": 0,
            "device_detections": 0,
            "breakpoint_matches": 0,
            "average_processing_time": 0.0
        }
    
    def add_custom_breakpoint(self, breakpoint: ResponsiveBreakpoint):
        """Add a custom responsive breakpoint."""
        self.breakpoints[breakpoint.name] = breakpoint
        self.logger.info(f"Added custom breakpoint: {breakpoint.name}")
    
    def add_custom_adaptation(
        self,
        layout_type: str,
        screen_size: str,
        adaptation_func
    ):
        """Add a custom adaptation function."""
        if layout_type not in self.layout_adaptations:
            self.layout_adaptations[layout_type] = {}
        
        self.layout_adaptations[layout_type][screen_size] = adaptation_func
        self.logger.info(f"Added custom adaptation for {layout_type} on {screen_size}")


# Global formatter instance
_responsive_formatter_instance: Optional[ResponsiveFormatter] = None


def get_responsive_formatter() -> ResponsiveFormatter:
    """Get global responsive formatter instance."""
    global _responsive_formatter_instance
    if _responsive_formatter_instance is None:
        _responsive_formatter_instance = ResponsiveFormatter()
    return _responsive_formatter_instance