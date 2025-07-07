"""
Kari IoT Page
- Orchestrates: device manager, iot logs, scene builder
"""

from src.ui_logic.components.iot.device_manager import render_device_manager
from src.ui_logic.components.iot.iot_logs import render_iot_logs
from src.ui_logic.components.iot.scene_builder import render_scene_builder


def iot_page(user_ctx=None):
    render_device_manager(user_ctx=user_ctx)
    render_scene_builder(user_ctx=user_ctx)
    render_iot_logs(user_ctx=user_ctx)
