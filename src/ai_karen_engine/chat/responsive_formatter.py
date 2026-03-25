"""
Responsive Formatting System for Different Display Sizes
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import shared models
from .response_formatting_models import (
    DisplayContext, LayoutType, ContentType, AccessibilityLevel
)

logger = logging.getLogger(__name__)

class ScreenSize(Enum):
    EXTRA_SMALL = "extra_small"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"

class DeviceType(Enum):
    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    TV = "tv"
    WEARABLE = "wearable"
    UNKNOWN = "unknown"

@dataclass
class ResponsiveConfig:
    display_context: DisplayContext
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    device_pixel_ratio: float = 1.0
    touch_enabled: bool = False
    high_dpi: bool = False
    prefers_reduced_motion: bool = False
    prefers_dark_theme: bool = False
    max_width_chars: int = 80
    max_height_lines: int = 24

@dataclass
class ResponsiveBreakpoint:
    name: str
    min_width: int
    max_width: Optional[int] = None
    layout_adaptations: Dict[str, Any] = field(default_factory=dict)

class ResponsiveFormatter:
    """
    Advanced responsive formatting system with multi-device support.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._init_breakpoints()
        self._init_layout_adaptations()
        self._performance_metrics = {
            "total_formatting": 0,
            "responsive_adaptations": 0,
            "average_processing_time": 0.0
        }
    
    def _init_breakpoints(self):
        self.breakpoints = {
            'extra_small': ResponsiveBreakpoint('extra_small', 0, 575, {'simplify_tables': True, 'collapse_menus': True}),
            'small': ResponsiveBreakpoint('small', 576, 767, {'compact_layout': True}),
            'medium': ResponsiveBreakpoint('medium', 768, 991, {'two_column_layout': True}),
            'large': ResponsiveBreakpoint('large', 992, 1199, {'multi_column_layout': True}),
            'extra_large': ResponsiveBreakpoint('extra_large', 1200, None, {'max_columns': True})
        }
    
    def _init_layout_adaptations(self):
        self.layout_adaptations = {
            'table': {'extra_small': self._adapt_table_for_mobile, 'small': self._adapt_table_for_mobile, 'medium': self._adapt_table_for_tablet},
            'list': {'extra_small': self._adapt_list_for_mobile, 'small': self._adapt_list_for_mobile, 'medium': self._adapt_list_for_tablet},
            'code': {'extra_small': self._adapt_code_for_mobile, 'small': self._adapt_code_for_mobile, 'medium': self._adapt_code_for_tablet},
        }
    
    async def format_responsive(self, content: str, config: ResponsiveConfig, layout_type: LayoutType) -> Dict[str, Any]:
        try:
            device_type = self._detect_device_type(config)
            screen_size = self._determine_screen_size(config.screen_width)
            active_breakpoint = self._get_active_breakpoint(config.screen_width)
            
            adapted_content = await self._apply_responsive_adaptations(content, layout_type, screen_size, device_type, config)
            
            return {
                'content': adapted_content,
                'layout_type': layout_type.value,
                'display_context': config.display_context.value,
                'device_type': device_type.value,
                'screen_size': screen_size.value,
                'css_classes': [f'device-{device_type.value}', f'screen-{screen_size.value}'],
                'accessibility_adaptations': []
            }
        except Exception as e:
            logger.error(f"Error in responsive formatting: {e}")
            return {'content': content, 'layout_type': layout_type.value, 'error': str(e)}

    def _detect_device_type(self, config):
        if config.display_context == DisplayContext.TERMINAL: return DeviceType.DESKTOP
        if config.screen_width and config.screen_width <= 767: return DeviceType.PHONE
        if config.screen_width and config.screen_width <= 1023: return DeviceType.TABLET
        return DeviceType.DESKTOP

    def _determine_screen_size(self, width):
        if width is None: return ScreenSize.MEDIUM
        if width < 576: return ScreenSize.EXTRA_SMALL
        elif width < 768: return ScreenSize.SMALL
        elif width < 992: return ScreenSize.MEDIUM
        elif width < 1200: return ScreenSize.LARGE
        else: return ScreenSize.EXTRA_LARGE

    def _get_active_breakpoint(self, width):
        if width is None: return None
        for b in self.breakpoints.values():
            if width >= b.min_width and (b.max_width is None or width <= b.max_width): return b
        return None

    async def _apply_responsive_adaptations(self, content, layout_type, screen_size, device_type, config):
        adaptations = self.layout_adaptations.get(layout_type.value.lower(), {})
        func = adaptations.get(screen_size.value)
        return func(content, config) if func else content

    def _adapt_table_for_mobile(self, content, config):
        return '\n'.join([f"• {c.strip()}" for l in content.split('\n') if '|' in l for c in l.split('|') if c.strip()])
    def _adapt_table_for_tablet(self, content, config): return content
    def _adapt_list_for_mobile(self, content, config): return content
    def _adapt_list_for_tablet(self, content, config): return content
    def _adapt_code_for_mobile(self, content, config): return content
    def _adapt_code_for_tablet(self, content, config): return content

_responsive_formatter_instance = None
def get_responsive_formatter() -> ResponsiveFormatter:
    global _responsive_formatter_instance
    if _responsive_formatter_instance is None: _responsive_formatter_instance = ResponsiveFormatter()
    return _responsive_formatter_instance