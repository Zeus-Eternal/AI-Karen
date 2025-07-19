"""
Advanced Notification System for AI Karen Premium UI
- Toast notifications with stacking and persistence
- Real-time alerts and system notifications
- User notification preferences and management
- Integration with backend notification services
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class NotificationType(Enum):
    """Notification types with different styling and behavior."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    CHAT = "chat"
    TASK = "task"

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Notification:
    """Notification data structure."""
    id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    timestamp: datetime
    read: bool = False
    persistent: bool = False
    auto_dismiss: bool = True
    dismiss_after: int = 5000  # milliseconds
    action_label: Optional[str] = None
    action_callback: Optional[callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class NotificationSystem:
    """Advanced notification management system."""
    
    def __init__(self):
        self.notifications = []
        self.max_notifications = 50
        self.toast_stack_limit = 5
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize notification-related session state."""
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        if 'notification_settings' not in st.session_state:
            st.session_state.notification_settings = {
                'enabled': True,
                'sound_enabled': True,
                'desktop_notifications': False,
                'email_notifications': False,
                'types': {
                    'success': True,
                    'info': True,
                    'warning': True,
                    'error': True,
                    'system': True,
                    'chat': True,
                    'task': True
                },
                'priority_filter': 'normal'  # minimum priority to show
            }
        
        if 'notification_counter' not in st.session_state:
            st.session_state.notification_counter = 0
    
    def add_notification(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        persistent: bool = False,
        auto_dismiss: bool = True,
        dismiss_after: int = 5000,
        action_label: Optional[str] = None,
        action_callback: Optional[callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new notification."""
        # Check if notifications are enabled
        settings = st.session_state.notification_settings
        if not settings['enabled'] or not settings['types'].get(type.value, True):
            return ""
        
        # Check priority filter
        priority_levels = ['low', 'normal', 'high', 'urgent']
        min_priority_index = priority_levels.index(settings['priority_filter'])
        current_priority_index = priority_levels.index(priority.value)
        
        if current_priority_index < min_priority_index:
            return ""
        
        # Generate unique ID
        notification_id = f"notif_{int(time.time() * 1000)}_{st.session_state.notification_counter}"
        st.session_state.notification_counter += 1
        
        # Create notification
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            timestamp=datetime.now(),
            persistent=persistent,
            auto_dismiss=auto_dismiss,
            dismiss_after=dismiss_after,
            action_label=action_label,
            action_callback=action_callback,
            metadata=metadata or {}
        )
        
        # Add to session state
        st.session_state.notifications.append(notification)
        
        # Limit notification count
        if len(st.session_state.notifications) > self.max_notifications:
            st.session_state.notifications = st.session_state.notifications[-self.max_notifications:]
        
        return notification_id
    
    def remove_notification(self, notification_id: str):
        """Remove a notification by ID."""
        st.session_state.notifications = [
            n for n in st.session_state.notifications 
            if n.id != notification_id
        ]
    
    def mark_as_read(self, notification_id: str):
        """Mark a notification as read."""
        for notification in st.session_state.notifications:
            if notification.id == notification_id:
                notification.read = True
                break
    
    def mark_all_as_read(self):
        """Mark all notifications as read."""
        for notification in st.session_state.notifications:
            notification.read = True
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        st.session_state.notifications = []
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return len([n for n in st.session_state.notifications if not n.read])
    
    def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """Get notifications filtered by type."""
        return [n for n in st.session_state.notifications if n.type == notification_type]
    
    def get_recent_notifications(self, hours: int = 24) -> List[Notification]:
        """Get notifications from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [n for n in st.session_state.notifications if n.timestamp > cutoff_time]
    
    def render_notifications(self):
        """Render notification toasts and system."""
        self._render_toast_notifications()
        self._inject_notification_css()
    
    def _render_toast_notifications(self):
        """Render toast notifications that auto-dismiss."""
        current_time = datetime.now()
        toasts_to_show = []
        
        # Get notifications that should be shown as toasts
        for notification in st.session_state.notifications:
            if not notification.read and notification.auto_dismiss:
                # Check if notification should still be visible
                time_diff = (current_time - notification.timestamp).total_seconds() * 1000
                if time_diff < notification.dismiss_after:
                    toasts_to_show.append(notification)
                else:
                    # Auto-dismiss expired notifications
                    notification.read = True
        
        # Limit number of visible toasts
        toasts_to_show = toasts_to_show[-self.toast_stack_limit:]
        
        # Render toasts
        if toasts_to_show:
            toast_html = self._generate_toast_html(toasts_to_show)
            st.markdown(toast_html, unsafe_allow_html=True)
    
    def _generate_toast_html(self, notifications: List[Notification]) -> str:
        """Generate HTML for toast notifications."""
        toasts_html = ""
        
        for i, notification in enumerate(notifications):
            # Determine toast styling based on type
            toast_class = f"toast-{notification.type.value}"
            priority_class = f"priority-{notification.priority.value}"
            
            # Calculate position (stack from top)
            top_position = 20 + (i * 80)
            
            # Generate action button if provided
            action_button = ""
            if notification.action_label and notification.action_callback:
                action_button = f"""
                <button class="toast-action-btn" onclick="handleNotificationAction('{notification.id}')">
                    {notification.action_label}
                </button>
                """
            
            # Generate toast HTML
            toast_html = f"""
            <div class="notification-toast {toast_class} {priority_class}" 
                 id="toast-{notification.id}"
                 style="top: {top_position}px;">
                <div class="toast-header">
                    <span class="toast-icon">{self._get_notification_icon(notification.type)}</span>
                    <span class="toast-title">{notification.title}</span>
                    <button class="toast-close" onclick="dismissToast('{notification.id}')">&times;</button>
                </div>
                <div class="toast-body">
                    <p>{notification.message}</p>
                    {action_button}
                </div>
                <div class="toast-progress">
                    <div class="toast-progress-bar" style="animation-duration: {notification.dismiss_after}ms;"></div>
                </div>
            </div>
            """
            
            toasts_html += toast_html
        
        # Wrap in container with JavaScript
        return f"""
        <div id="notification-container">
            {toasts_html}
        </div>
        
        <script>
        function dismissToast(notificationId) {{
            const toast = document.getElementById('toast-' + notificationId);
            if (toast) {{
                toast.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => {{
                    toast.remove();
                }}, 300);
            }}
        }}
        
        function handleNotificationAction(notificationId) {{
            // This would trigger a callback to Streamlit
            console.log('Action clicked for notification:', notificationId);
            dismissToast(notificationId);
        }}
        
        // Auto-dismiss toasts after their timeout
        document.querySelectorAll('.notification-toast').forEach(toast => {{
            const progressBar = toast.querySelector('.toast-progress-bar');
            if (progressBar) {{
                const duration = parseFloat(progressBar.style.animationDuration);
                setTimeout(() => {{
                    if (toast.parentNode) {{
                        dismissToast(toast.id.replace('toast-', ''));
                    }}
                }}, duration);
            }}
        }});
        </script>
        """
    
    def _inject_notification_css(self):
        """Inject CSS for notification styling."""
        css = """
        <style>
        #notification-container {
            position: fixed;
            top: 0;
            right: 0;
            z-index: 9999;
            pointer-events: none;
        }
        
        .notification-toast {
            position: fixed;
            right: 20px;
            width: 350px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            border-left: 4px solid #3b82f6;
            animation: slideIn 0.3s ease-out;
            pointer-events: auto;
            overflow: hidden;
        }
        
        .toast-success {
            border-left-color: #10b981;
        }
        
        .toast-warning {
            border-left-color: #f59e0b;
        }
        
        .toast-error {
            border-left-color: #ef4444;
        }
        
        .toast-system {
            border-left-color: #8b5cf6;
        }
        
        .toast-chat {
            border-left-color: #06b6d4;
        }
        
        .toast-task {
            border-left-color: #84cc16;
        }
        
        .priority-urgent {
            box-shadow: 0 10px 25px rgba(239, 68, 68, 0.3);
            animation: pulse 1s infinite;
        }
        
        .priority-high {
            box-shadow: 0 10px 25px rgba(245, 158, 11, 0.2);
        }
        
        .toast-header {
            display: flex;
            align-items: center;
            padding: 12px 16px 8px 16px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .toast-icon {
            font-size: 18px;
            margin-right: 8px;
        }
        
        .toast-title {
            font-weight: 600;
            color: #1f2937;
            flex: 1;
        }
        
        .toast-close {
            background: none;
            border: none;
            font-size: 20px;
            color: #9ca3af;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .toast-close:hover {
            color: #6b7280;
        }
        
        .toast-body {
            padding: 8px 16px 12px 16px;
        }
        
        .toast-body p {
            margin: 0;
            color: #4b5563;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .toast-action-btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            margin-top: 8px;
            transition: background-color 0.2s;
        }
        
        .toast-action-btn:hover {
            background: #2563eb;
        }
        
        .toast-progress {
            height: 3px;
            background: #f3f4f6;
            overflow: hidden;
        }
        
        .toast-progress-bar {
            height: 100%;
            background: #3b82f6;
            width: 100%;
            animation: progressBar linear;
            transform-origin: left;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes progressBar {
            from {
                transform: scaleX(1);
            }
            to {
                transform: scaleX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.02);
            }
        }
        
        /* Dark theme support */
        [data-theme="dark"] .notification-toast {
            background: #1f2937;
            color: #f9fafb;
        }
        
        [data-theme="dark"] .toast-title {
            color: #f9fafb;
        }
        
        [data-theme="dark"] .toast-body p {
            color: #d1d5db;
        }
        
        [data-theme="dark"] .toast-header {
            border-bottom-color: #374151;
        }
        
        [data-theme="dark"] .toast-progress {
            background: #374151;
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def _get_notification_icon(self, notification_type: NotificationType) -> str:
        """Get icon for notification type."""
        icons = {
            NotificationType.SUCCESS: "✅",
            NotificationType.INFO: "ℹ️",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.SYSTEM: "🔧",
            NotificationType.CHAT: "💬",
            NotificationType.TASK: "📋"
        }
        return icons.get(notification_type, "📢")
    
    def render_notification_center(self):
        """Render notification center/inbox."""
        st.subheader("🔔 Notification Center")
        
        # Notification stats
        total_notifications = len(st.session_state.notifications)
        unread_count = self.get_unread_count()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", total_notifications)
        
        with col2:
            st.metric("Unread", unread_count)
        
        with col3:
            recent_count = len(self.get_recent_notifications(24))
            st.metric("Last 24h", recent_count)
        
        with col4:
            if st.button("Mark All Read"):
                self.mark_all_as_read()
                st.success("All notifications marked as read")
                st.rerun()
        
        # Notification filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All"] + [t.value.title() for t in NotificationType],
                key="notif_filter_type"
            )
        
        with col2:
            filter_read = st.selectbox(
                "Filter by Status",
                ["All", "Unread", "Read"],
                key="notif_filter_read"
            )
        
        with col3:
            if st.button("Clear All", type="secondary"):
                if st.session_state.get('confirm_clear', False):
                    self.clear_all_notifications()
                    st.success("All notifications cleared")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm clearing all notifications")
        
        # Display notifications
        filtered_notifications = self._filter_notifications(filter_type, filter_read)
        
        if not filtered_notifications:
            st.info("No notifications to display")
            return
        
        # Pagination
        notifications_per_page = 10
        total_pages = (len(filtered_notifications) + notifications_per_page - 1) // notifications_per_page
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1), key="notif_page") - 1
            start_idx = page * notifications_per_page
            end_idx = start_idx + notifications_per_page
            page_notifications = filtered_notifications[start_idx:end_idx]
        else:
            page_notifications = filtered_notifications
        
        # Display notifications
        for notification in page_notifications:
            self._render_notification_item(notification)
    
    def _filter_notifications(self, type_filter: str, read_filter: str) -> List[Notification]:
        """Filter notifications based on criteria."""
        notifications = st.session_state.notifications.copy()
        notifications.reverse()  # Show newest first
        
        # Filter by type
        if type_filter != "All":
            notifications = [
                n for n in notifications 
                if n.type.value.title() == type_filter
            ]
        
        # Filter by read status
        if read_filter == "Unread":
            notifications = [n for n in notifications if not n.read]
        elif read_filter == "Read":
            notifications = [n for n in notifications if n.read]
        
        return notifications
    
    def _render_notification_item(self, notification: Notification):
        """Render individual notification item."""
        # Notification container
        read_class = "read" if notification.read else "unread"
        priority_indicator = "🔴" if notification.priority == NotificationPriority.URGENT else ""
        
        with st.container():
            col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
            
            with col1:
                st.markdown(f"<div style='font-size: 24px;'>{self._get_notification_icon(notification.type)}</div>", 
                           unsafe_allow_html=True)
            
            with col2:
                # Notification content
                title_style = "font-weight: bold;" if not notification.read else "font-weight: normal; opacity: 0.7;"
                
                st.markdown(f"""
                <div style="{title_style}">
                    {priority_indicator} {notification.title}
                </div>
                <div style="font-size: 14px; color: #666; margin: 4px 0;">
                    {notification.message}
                </div>
                <div style="font-size: 12px; color: #999;">
                    {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')} • {notification.type.value.title()}
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Action buttons
                if not notification.read:
                    if st.button("✓", key=f"read_{notification.id}", help="Mark as read"):
                        self.mark_as_read(notification.id)
                        st.rerun()
                
                if st.button("🗑️", key=f"delete_{notification.id}", help="Delete"):
                    self.remove_notification(notification.id)
                    st.rerun()
        
        st.divider()
    
    def render_notification_settings(self):
        """Render notification settings interface."""
        st.subheader("🔔 Notification Settings")
        
        settings = st.session_state.notification_settings
        
        # General settings
        st.markdown("### General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            settings['enabled'] = st.checkbox(
                "Enable Notifications",
                value=settings['enabled'],
                key="notif_enabled"
            )
            
            settings['sound_enabled'] = st.checkbox(
                "Sound Notifications",
                value=settings['sound_enabled'],
                key="notif_sound",
                disabled=not settings['enabled']
            )
        
        with col2:
            settings['desktop_notifications'] = st.checkbox(
                "Desktop Notifications",
                value=settings['desktop_notifications'],
                key="notif_desktop",
                disabled=not settings['enabled']
            )
            
            settings['email_notifications'] = st.checkbox(
                "Email Notifications",
                value=settings['email_notifications'],
                key="notif_email",
                disabled=not settings['enabled']
            )
        
        # Priority filter
        st.markdown("### Priority Filter")
        settings['priority_filter'] = st.selectbox(
            "Minimum Priority Level",
            ['low', 'normal', 'high', 'urgent'],
            index=['low', 'normal', 'high', 'urgent'].index(settings['priority_filter']),
            key="notif_priority_filter",
            disabled=not settings['enabled']
        )
        
        # Notification types
        st.markdown("### Notification Types")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for i, (type_key, enabled) in enumerate(list(settings['types'].items())[:4]):
                settings['types'][type_key] = st.checkbox(
                    f"{type_key.title()} Notifications",
                    value=enabled,
                    key=f"notif_type_{type_key}",
                    disabled=not settings['enabled']
                )
        
        with col2:
            for i, (type_key, enabled) in enumerate(list(settings['types'].items())[4:]):
                settings['types'][type_key] = st.checkbox(
                    f"{type_key.title()} Notifications",
                    value=enabled,
                    key=f"notif_type_{type_key}",
                    disabled=not settings['enabled']
                )
        
        # Save settings
        if st.button("Save Settings"):
            st.session_state.notification_settings = settings
            st.success("Notification settings saved!")
    
    # Convenience methods for common notification types
    def success(self, title: str, message: str, **kwargs):
        """Add success notification."""
        return self.add_notification(title, message, NotificationType.SUCCESS, **kwargs)
    
    def info(self, title: str, message: str, **kwargs):
        """Add info notification."""
        return self.add_notification(title, message, NotificationType.INFO, **kwargs)
    
    def warning(self, title: str, message: str, **kwargs):
        """Add warning notification."""
        return self.add_notification(title, message, NotificationType.WARNING, **kwargs)
    
    def error(self, title: str, message: str, **kwargs):
        """Add error notification."""
        return self.add_notification(title, message, NotificationType.ERROR, **kwargs)
    
    def system(self, title: str, message: str, **kwargs):
        """Add system notification."""
        return self.add_notification(title, message, NotificationType.SYSTEM, **kwargs)