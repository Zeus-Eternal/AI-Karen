"""
SearxNG Plugin for AI-Karen
Privacy-respecting search engine plugin with Docker deployment
"""

from .searxng_plugin import SearxNGPlugin
from .searxng_manager import SearxNGManager

__all__ = ['SearxNGPlugin', 'SearxNGManager']
