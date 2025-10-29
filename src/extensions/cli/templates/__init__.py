"""
Extension templates for scaffolding.
"""

from .basic import BasicTemplate
from .api_only import ApiOnlyTemplate
from .ui_only import UiOnlyTemplate
from .background_task import BackgroundTaskTemplate
from .full import FullTemplate

TEMPLATES = {
    "basic": BasicTemplate,
    "api-only": ApiOnlyTemplate,
    "ui-only": UiOnlyTemplate,
    "background-task": BackgroundTaskTemplate,
    "full": FullTemplate
}

__all__ = ["TEMPLATES", "BasicTemplate", "ApiOnlyTemplate", "UiOnlyTemplate", "BackgroundTaskTemplate", "FullTemplate"]