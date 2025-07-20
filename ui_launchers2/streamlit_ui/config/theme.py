"""
Enhanced Theme Management System for AI Karen Streamlit UI
Provides comprehensive theming with smooth transitions, persistence, and dynamic switching.
"""

from __future__ import annotations

import importlib.resources
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import streamlit as st

THEME_DIR = Path(__file__).resolve().parents[1] / "styles"
THEME_CONFIG_FILE = THEME_DIR / "theme_config.json"


@dataclass
class ThemeConfig:
    """Configuration for a theme."""
    name: str
    display_name: str
    description: str
    category: str = "standard"  # standard, premium, custom
    author: str = "AI Karen Team"
    version: str = "1.0.0"
    created_at: str = ""
    primary_color: str = "#2563eb"
    secondary_color: str = "#64748b"
    accent_color: str = "#10b981"
    background_color: str = "#ffffff"
    surface_color: str = "#f8fafc"
    text_color: str = "#1e293b"
    border_color: str = "#e2e8f0"
    success_color: str = "#10b981"
    warning_color: str = "#f59e0b"
    error_color: str = "#ef4444"
    info_color: str = "#3b82f6"
    font_family: str = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    border_radius: str = "8px"
    shadow: str = "0 1px 3px 0 rgba(0, 0, 0, 0.1)"
    transition: str = "all 0.2s ease"
    supports_dark_mode: bool = False
    custom_properties: Dict[str, str] = None
    
    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.custom_properties is None:
            self.custom_properties = {}


class ThemeManager:
    """Enhanced theme management system."""
    
    def __init__(self):
        self.theme_dir = THEME_DIR
        self.config_file = THEME_CONFIG_FILE
        self.themes = {}
        self.current_theme = None
        self._load_theme_configs()
    
    def _load_theme_configs(self):
        """Load theme configurations from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    for theme_name, theme_data in config_data.items():
                        self.themes[theme_name] = ThemeConfig(**theme_data)
            except Exception as e:
                st.error(f"Failed to load theme config: {e}")
        
        # Load default themes if config doesn't exist
        if not self.themes:
            self._create_default_themes()
    
    def _create_default_themes(self):
        """Create default theme configurations."""
        default_themes = {
            "light": ThemeConfig(
                name="light",
                display_name="Light Mode",
                description="Clean, bright theme perfect for daytime use",
                category="standard",
                primary_color="#2563eb",
                secondary_color="#64748b",
                accent_color="#10b981",
                background_color="#ffffff",
                surface_color="#f8fafc",
                text_color="#1e293b",
                border_color="#e2e8f0"
            ),
            "dark": ThemeConfig(
                name="dark",
                display_name="Dark Mode",
                description="Easy on the eyes for low-light environments",
                category="standard",
                primary_color="#3b82f6",
                secondary_color="#94a3b8",
                accent_color="#10b981",
                background_color="#0f172a",
                surface_color="#1e293b",
                text_color="#f1f5f9",
                border_color="#334155",
                supports_dark_mode=True
            ),
            "enterprise": ThemeConfig(
                name="enterprise",
                display_name="Enterprise",
                description="Professional theme for business environments",
                category="premium",
                primary_color="#1f2937",
                secondary_color="#6b7280",
                accent_color="#059669",
                background_color="#f9fafb",
                surface_color="#ffffff",
                text_color="#111827",
                border_color="#d1d5db"
            ),
            "ocean": ThemeConfig(
                name="ocean",
                display_name="Ocean Blue",
                description="Calming blue theme inspired by the ocean",
                category="premium",
                primary_color="#0ea5e9",
                secondary_color="#64748b",
                accent_color="#06b6d4",
                background_color="#f0f9ff",
                surface_color="#ffffff",
                text_color="#0c4a6e",
                border_color="#bae6fd"
            ),
            "sunset": ThemeConfig(
                name="sunset",
                display_name="Sunset Orange",
                description="Warm, energizing theme with sunset colors",
                category="premium",
                primary_color="#ea580c",
                secondary_color="#78716c",
                accent_color="#f59e0b",
                background_color="#fffbeb",
                surface_color="#ffffff",
                text_color="#9a3412",
                border_color="#fed7aa"
            ),
            "forest": ThemeConfig(
                name="forest",
                display_name="Forest Green",
                description="Natural green theme for a calming experience",
                category="premium",
                primary_color="#059669",
                secondary_color="#6b7280",
                accent_color="#10b981",
                background_color="#f0fdf4",
                surface_color="#ffffff",
                text_color="#064e3b",
                border_color="#bbf7d0"
            )
        }
        
        self.themes.update(default_themes)
        self._save_theme_configs()
    
    def _save_theme_configs(self):
        """Save theme configurations to file."""
        try:
            self.theme_dir.mkdir(exist_ok=True)
            config_data = {name: asdict(theme) for name, theme in self.themes.items()}
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save theme config: {e}")
    
    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """Get theme configuration by name."""
        return self.themes.get(theme_name)
    
    def get_available_themes(self) -> List[ThemeConfig]:
        """Get list of available themes."""
        return list(self.themes.values())
    
    def get_themes_by_category(self, category: str) -> List[ThemeConfig]:
        """Get themes filtered by category."""
        return [theme for theme in self.themes.values() if theme.category == category]
    
    def theme_exists(self, theme_name: str) -> bool:
        """Check if theme exists."""
        return theme_name in self.themes or (self.theme_dir / f"{theme_name}.css").exists()
    
    def load_css(self, theme_name: str = "light") -> str:
        """Load CSS for the specified theme."""
        # Try to load from file first
        css_file = self.theme_dir / f"{theme_name}.css"
        if css_file.exists():
            return css_file.read_text()
        
        # Generate CSS from theme config
        theme_config = self.get_theme_config(theme_name)
        if theme_config:
            return self._generate_css_from_config(theme_config)
        
        # Fallback to trying importlib
        try:
            return (
                importlib.resources.files("ui_logic.themes")
                .joinpath(f"{theme_name}.css")
                .read_text()
            )
        except FileNotFoundError:
            return ""
    
    def _generate_css_from_config(self, theme_config: ThemeConfig) -> str:
        """Generate CSS from theme configuration."""
        css_template = f"""
        /* {theme_config.display_name} Theme - {theme_config.description} */
        :root {{
            --primary: {theme_config.primary_color};
            --secondary: {theme_config.secondary_color};
            --accent: {theme_config.accent_color};
            --background: {theme_config.background_color};
            --surface: {theme_config.surface_color};
            --text: {theme_config.text_color};
            --border: {theme_config.border_color};
            --success: {theme_config.success_color};
            --warning: {theme_config.warning_color};
            --error: {theme_config.error_color};
            --info: {theme_config.info_color};
            --font-family: {theme_config.font_family};
            --border-radius: {theme_config.border_radius};
            --shadow: {theme_config.shadow};
            --transition: {theme_config.transition};
        }}
        
        /* Apply theme colors */
        .stApp {{
            background-color: var(--background);
            color: var(--text);
            font-family: var(--font-family);
            transition: var(--transition);
        }}
        
        /* Surface elements */
        .stSidebar {{
            background-color: var(--surface);
            border-right: 1px solid var(--border);
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            transition: var(--transition);
            box-shadow: var(--shadow);
        }}
        
        .stButton > button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            color: var(--text);
            transition: var(--transition);
        }}
        
        /* Metrics */
        .metric-container {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
        }}
        
        /* Custom properties */
        """
        
        # Add custom properties
        for prop, value in theme_config.custom_properties.items():
            css_template += f"        --{prop}: {value};\n"
        
        return css_template
    
    def apply_theme(self, theme_name: str = "light") -> None:
        """Apply theme with smooth transitions."""
        css = self.load_css(theme_name)
        if css:
            # Add transition CSS for smooth theme switching
            transition_css = """
            <style>
            * {
                transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
            }
            </style>
            """
            
            st.markdown(transition_css + f"<style>{css}</style>", unsafe_allow_html=True)
            self.current_theme = theme_name
            
            # Store theme preference
            self._store_theme_preference(theme_name)
    
    def _store_theme_preference(self, theme_name: str):
        """Store theme preference in session state and local storage."""
        st.session_state.selected_theme = theme_name
        
        # Use JavaScript to store in localStorage
        js_code = f"""
        <script>
        localStorage.setItem('ai_karen_theme', '{theme_name}');
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)
    
    def get_current_theme(self) -> str:
        """Get current theme from various sources."""
        # Check session state first
        if hasattr(st.session_state, 'selected_theme'):
            return st.session_state.selected_theme
        
        # Check query params
        params = st.query_params
        if "theme" in params:
            return params["theme"]
        
        # Check environment variable
        env_theme = os.getenv("KARI_UI_THEME")
        if env_theme and self.theme_exists(env_theme):
            return env_theme
        
        # Default to light
        return "light"
    
    def create_theme_selector(self) -> str:
        """Create a theme selector widget."""
        available_themes = self.get_available_themes()
        current_theme = self.get_current_theme()
        
        # Group themes by category
        categories = {}
        for theme in available_themes:
            if theme.category not in categories:
                categories[theme.category] = []
            categories[theme.category].append(theme)
        
        st.markdown("### 🎨 Theme Selection")
        
        selected_theme = current_theme
        
        for category, themes in categories.items():
            st.markdown(f"**{category.title()} Themes**")
            
            cols = st.columns(min(3, len(themes)))
            for i, theme in enumerate(themes):
                with cols[i % len(cols)]:
                    # Create theme preview card
                    is_selected = theme.name == current_theme
                    card_style = f"""
                    <div style="
                        background: {theme.surface_color};
                        border: 2px solid {'var(--primary)' if is_selected else theme.border_color};
                        border-radius: {theme.border_radius};
                        padding: 1rem;
                        margin: 0.5rem 0;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        box-shadow: {theme.shadow};
                    ">
                        <div style="
                            width: 100%;
                            height: 40px;
                            background: linear-gradient(45deg, {theme.primary_color}, {theme.accent_color});
                            border-radius: 4px;
                            margin-bottom: 0.5rem;
                        "></div>
                        <h4 style="color: {theme.text_color}; margin: 0.5rem 0;">{theme.display_name}</h4>
                        <p style="color: {theme.secondary_color}; font-size: 0.8rem; margin: 0;">{theme.description}</p>
                    </div>
                    """
                    
                    st.markdown(card_style, unsafe_allow_html=True)
                    
                    if st.button(f"Select {theme.display_name}", key=f"theme_{theme.name}"):
                        selected_theme = theme.name
                        st.rerun()
        
        return selected_theme
    
    def add_custom_theme(self, theme_config: ThemeConfig):
        """Add a custom theme."""
        self.themes[theme_config.name] = theme_config
        self._save_theme_configs()
    
    def remove_theme(self, theme_name: str) -> bool:
        """Remove a theme (only custom themes)."""
        if theme_name in self.themes and self.themes[theme_name].category == "custom":
            del self.themes[theme_name]
            self._save_theme_configs()
            return True
        return False
    
    def export_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Export theme configuration."""
        theme = self.get_theme_config(theme_name)
        if theme:
            return asdict(theme)
        return None
    
    def import_theme(self, theme_data: Dict[str, Any]) -> bool:
        """Import theme configuration."""
        try:
            theme_config = ThemeConfig(**theme_data)
            theme_config.category = "custom"  # Mark as custom
            self.add_custom_theme(theme_config)
            return True
        except Exception as e:
            st.error(f"Failed to import theme: {e}")
            return False


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get or create global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


# Convenience functions for backward compatibility
def load_css(theme: str = "light") -> str:
    """Return CSS for the requested theme or empty string if missing."""
    return get_theme_manager().load_css(theme)


def theme_exists(theme: str) -> bool:
    """Return True if a theme exists."""
    return get_theme_manager().theme_exists(theme)


def available_themes() -> List[str]:
    """Return a sorted list of available theme names."""
    return [theme.name for theme in get_theme_manager().get_available_themes()]


def get_default_theme() -> str:
    """Return the default theme."""
    return os.getenv("KARI_UI_THEME", "light")


def apply_theme(theme: str = "light") -> None:
    """Inject theme CSS into the page if available."""
    get_theme_manager().apply_theme(theme)


def get_current_theme() -> str:
    """Return current theme."""
    return get_theme_manager().get_current_theme()


def apply_default_theme() -> None:
    """Apply the current theme."""
    current_theme = get_current_theme()
    apply_theme(current_theme)


__all__ = [
    "ThemeConfig",
    "ThemeManager",
    "get_theme_manager",
    "load_css",
    "apply_theme",
    "get_current_theme",
    "available_themes",
    "theme_exists",
    "get_default_theme",
    "apply_default_theme",
]
