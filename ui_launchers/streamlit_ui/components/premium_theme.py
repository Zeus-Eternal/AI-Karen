"""
Premium Theme Manager for AI Karen Streamlit UI
- Advanced theming with smooth transitions
- Multiple professional themes
- User preference persistence
- Real-time theme switching
"""

import streamlit as st
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ThemeConfig:
    """Theme configuration data structure."""
    name: str
    display_name: str
    description: str
    colors: Dict[str, str]
    typography: Dict[str, str]
    spacing: Dict[str, str]
    effects: Dict[str, str]

class PremiumThemeManager:
    """Advanced theme management system."""
    
    def __init__(self):
        self.themes = self._load_premium_themes()
        self.current_theme = None
    
    def _load_premium_themes(self) -> Dict[str, ThemeConfig]:
        """Load all available premium themes."""
        themes = {
            "executive": ThemeConfig(
                name="executive",
                display_name="Executive",
                description="Professional theme for business users",
                colors={
                    "primary": "#1e293b",
                    "secondary": "#3b82f6", 
                    "accent": "#10b981",
                    "background": "#f8fafc",
                    "surface": "#ffffff",
                    "text_primary": "#1e293b",
                    "text_secondary": "#64748b",
                    "border": "#e2e8f0",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "info": "#3b82f6"
                },
                typography={
                    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                    "font_size_base": "16px",
                    "font_size_sm": "14px",
                    "font_size_lg": "18px",
                    "font_size_xl": "24px",
                    "font_weight_normal": "400",
                    "font_weight_medium": "500",
                    "font_weight_bold": "600",
                    "line_height": "1.5"
                },
                spacing={
                    "xs": "4px",
                    "sm": "8px", 
                    "md": "16px",
                    "lg": "24px",
                    "xl": "32px",
                    "2xl": "48px"
                },
                effects={
                    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                    "shadow_md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                    "radius_sm": "4px",
                    "radius_md": "8px",
                    "radius_lg": "12px",
                    "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
                }
            ),
            
            "developer": ThemeConfig(
                name="developer",
                display_name="Developer Dark",
                description="Dark theme optimized for development work",
                colors={
                    "primary": "#0f172a",
                    "secondary": "#7c3aed",
                    "accent": "#06b6d4",
                    "background": "#020617",
                    "surface": "#1e293b",
                    "text_primary": "#f1f5f9",
                    "text_secondary": "#94a3b8",
                    "border": "#334155",
                    "success": "#22c55e",
                    "warning": "#eab308",
                    "error": "#f87171",
                    "info": "#06b6d4"
                },
                typography={
                    "font_family": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "font_size_base": "15px",
                    "font_size_sm": "13px",
                    "font_size_lg": "17px",
                    "font_size_xl": "22px",
                    "font_weight_normal": "400",
                    "font_weight_medium": "500",
                    "font_weight_bold": "600",
                    "line_height": "1.6"
                },
                spacing={
                    "xs": "4px",
                    "sm": "8px",
                    "md": "16px", 
                    "lg": "24px",
                    "xl": "32px",
                    "2xl": "48px"
                },
                effects={
                    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
                    "shadow_md": "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
                    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                    "radius_sm": "4px",
                    "radius_md": "6px",
                    "radius_lg": "8px",
                    "transition": "all 0.2s ease-in-out"
                }
            ),
            
            "minimal": ThemeConfig(
                name="minimal",
                display_name="Minimal Clean",
                description="Clean, distraction-free interface",
                colors={
                    "primary": "#374151",
                    "secondary": "#6b7280",
                    "accent": "#f59e0b",
                    "background": "#ffffff",
                    "surface": "#f9fafb",
                    "text_primary": "#111827",
                    "text_secondary": "#6b7280",
                    "border": "#d1d5db",
                    "success": "#059669",
                    "warning": "#d97706",
                    "error": "#dc2626",
                    "info": "#2563eb"
                },
                typography={
                    "font_family": "'System UI', -apple-system, sans-serif",
                    "font_size_base": "16px",
                    "font_size_sm": "14px",
                    "font_size_lg": "18px",
                    "font_size_xl": "24px",
                    "font_weight_normal": "400",
                    "font_weight_medium": "500",
                    "font_weight_bold": "600",
                    "line_height": "1.5"
                },
                spacing={
                    "xs": "4px",
                    "sm": "8px",
                    "md": "16px",
                    "lg": "24px", 
                    "xl": "32px",
                    "2xl": "48px"
                },
                effects={
                    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                    "shadow_md": "0 1px 3px 0 rgba(0, 0, 0, 0.1)",
                    "shadow_lg": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    "radius_sm": "2px",
                    "radius_md": "4px",
                    "radius_lg": "6px",
                    "transition": "all 0.15s ease-out"
                }
            ),
            
            "premium": ThemeConfig(
                name="premium",
                display_name="Premium Gold",
                description="Luxury theme with gold accents",
                colors={
                    "primary": "#1a1a2e",
                    "secondary": "#16213e",
                    "accent": "#ffd700",
                    "background": "#0f0f23",
                    "surface": "#1a1a2e",
                    "text_primary": "#ffffff",
                    "text_secondary": "#b8b8b8",
                    "border": "#2a2a3e",
                    "success": "#00ff88",
                    "warning": "#ffaa00",
                    "error": "#ff4757",
                    "info": "#00d4ff"
                },
                typography={
                    "font_family": "'Playfair Display', 'Georgia', serif",
                    "font_size_base": "16px",
                    "font_size_sm": "14px",
                    "font_size_lg": "18px",
                    "font_size_xl": "28px",
                    "font_weight_normal": "400",
                    "font_weight_medium": "500",
                    "font_weight_bold": "700",
                    "line_height": "1.6"
                },
                spacing={
                    "xs": "6px",
                    "sm": "12px",
                    "md": "20px",
                    "lg": "28px",
                    "xl": "36px",
                    "2xl": "52px"
                },
                effects={
                    "shadow_sm": "0 2px 4px 0 rgba(255, 215, 0, 0.1)",
                    "shadow_md": "0 4px 8px -1px rgba(255, 215, 0, 0.2)",
                    "shadow_lg": "0 12px 20px -3px rgba(255, 215, 0, 0.3)",
                    "radius_sm": "6px",
                    "radius_md": "10px",
                    "radius_lg": "16px",
                    "transition": "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)"
                }
            )
        }
        
        return themes
    
    def get_current_theme(self, user_ctx: Dict[str, Any]) -> str:
        """Get current theme for user."""
        # Check session state first
        if 'current_theme' in st.session_state:
            return st.session_state.current_theme
        
        # Check user preferences
        user_theme = user_ctx.get('preferences', {}).get('theme', 'executive')
        
        # Validate theme exists
        if user_theme in self.themes:
            return user_theme
        
        return 'executive'  # Default fallback
    
    def set_theme(self, theme_name: str, user_ctx: Dict[str, Any]):
        """Set theme for current session."""
        if theme_name in self.themes:
            st.session_state.current_theme = theme_name
            self.current_theme = theme_name
            
            # Save to user preferences (would typically save to backend)
            if 'preferences' not in user_ctx:
                user_ctx['preferences'] = {}
            user_ctx['preferences']['theme'] = theme_name
    
    def generate_theme_css(self, theme_name: str) -> str:
        """Generate CSS for the specified theme."""
        if theme_name not in self.themes:
            theme_name = 'executive'
        
        theme = self.themes[theme_name]
        
        css = f"""
        <style>
        /* {theme.display_name} Theme */
        :root {{
            /* Colors */
            --theme-primary: {theme.colors['primary']};
            --theme-secondary: {theme.colors['secondary']};
            --theme-accent: {theme.colors['accent']};
            --theme-background: {theme.colors['background']};
            --theme-surface: {theme.colors['surface']};
            --theme-text-primary: {theme.colors['text_primary']};
            --theme-text-secondary: {theme.colors['text_secondary']};
            --theme-border: {theme.colors['border']};
            --theme-success: {theme.colors['success']};
            --theme-warning: {theme.colors['warning']};
            --theme-error: {theme.colors['error']};
            --theme-info: {theme.colors['info']};
            
            /* Typography */
            --theme-font-family: {theme.typography['font_family']};
            --theme-font-size-base: {theme.typography['font_size_base']};
            --theme-font-size-sm: {theme.typography['font_size_sm']};
            --theme-font-size-lg: {theme.typography['font_size_lg']};
            --theme-font-size-xl: {theme.typography['font_size_xl']};
            --theme-font-weight-normal: {theme.typography['font_weight_normal']};
            --theme-font-weight-medium: {theme.typography['font_weight_medium']};
            --theme-font-weight-bold: {theme.typography['font_weight_bold']};
            --theme-line-height: {theme.typography['line_height']};
            
            /* Spacing */
            --theme-space-xs: {theme.spacing['xs']};
            --theme-space-sm: {theme.spacing['sm']};
            --theme-space-md: {theme.spacing['md']};
            --theme-space-lg: {theme.spacing['lg']};
            --theme-space-xl: {theme.spacing['xl']};
            --theme-space-2xl: {theme.spacing['2xl']};
            
            /* Effects */
            --theme-shadow-sm: {theme.effects['shadow_sm']};
            --theme-shadow-md: {theme.effects['shadow_md']};
            --theme-shadow-lg: {theme.effects['shadow_lg']};
            --theme-radius-sm: {theme.effects['radius_sm']};
            --theme-radius-md: {theme.effects['radius_md']};
            --theme-radius-lg: {theme.effects['radius_lg']};
            --theme-transition: {theme.effects['transition']};
        }}
        
        /* Apply theme to Streamlit components */
        .stApp {{
            background-color: var(--theme-background);
            color: var(--theme-text-primary);
            font-family: var(--theme-font-family);
            line-height: var(--theme-line-height);
        }}
        
        /* Sidebar theming */
        .css-1d391kg {{
            background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
        }}
        
        /* Main content area */
        .main .block-container {{
            background-color: var(--theme-background);
            padding: var(--theme-space-lg);
        }}
        
        /* Cards and containers */
        .element-container {{
            background-color: var(--theme-surface);
            border-radius: var(--theme-radius-md);
            box-shadow: var(--theme-shadow-sm);
            transition: var(--theme-transition);
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: var(--theme-secondary);
            color: white;
            border: none;
            border-radius: var(--theme-radius-md);
            padding: var(--theme-space-sm) var(--theme-space-md);
            font-weight: var(--theme-font-weight-medium);
            transition: var(--theme-transition);
        }}
        
        .stButton > button:hover {{
            background-color: var(--theme-accent);
            box-shadow: var(--theme-shadow-md);
            transform: translateY(-1px);
        }}
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            background-color: var(--theme-surface);
            border: 1px solid var(--theme-border);
            border-radius: var(--theme-radius-sm);
            color: var(--theme-text-primary);
            transition: var(--theme-transition);
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {{
            border-color: var(--theme-accent);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
        }}
        
        /* Metrics */
        .metric-container {{
            background-color: var(--theme-surface);
            border-radius: var(--theme-radius-lg);
            padding: var(--theme-space-lg);
            box-shadow: var(--theme-shadow-md);
            border-left: 4px solid var(--theme-accent);
        }}
        
        /* Charts */
        .stPlotlyChart {{
            background-color: var(--theme-surface);
            border-radius: var(--theme-radius-md);
            box-shadow: var(--theme-shadow-sm);
        }}
        
        /* Animations */
        .theme-transition {{
            animation: themeTransition 0.3s ease-in-out;
        }}
        
        @keyframes themeTransition {{
            0% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}
        </style>
        """
        
        return css
    
    def apply_theme(self, user_ctx: Dict[str, Any]):
        """Apply the current theme to the page."""
        current_theme = self.get_current_theme(user_ctx)
        theme_css = self.generate_theme_css(current_theme)
        st.markdown(theme_css, unsafe_allow_html=True)
        
        # Add theme transition class to body
        st.markdown("""
        <script>
        document.body.classList.add('theme-transition');
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 300);
        </script>
        """, unsafe_allow_html=True)
    
    def render_theme_switcher(self, user_ctx: Dict[str, Any]):
        """Render premium theme switcher interface."""
        st.markdown("### 🎨 Theme")
        
        current_theme = self.get_current_theme(user_ctx)
        
        # Theme preview cards
        cols = st.columns(2)
        
        for i, (theme_name, theme_config) in enumerate(self.themes.items()):
            col = cols[i % 2]
            
            with col:
                is_current = theme_name == current_theme
                
                # Theme preview card
                card_style = f"""
                background: linear-gradient(135deg, {theme_config.colors['primary']}, {theme_config.colors['secondary']});
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
                border: {'3px solid ' + theme_config.colors['accent'] if is_current else '1px solid #ddd'};
                cursor: pointer;
                transition: all 0.3s ease;
                """
                
                st.markdown(f"""
                <div style="{card_style}">
                    <h4 style="color: white; margin: 0 0 8px 0;">
                        {theme_config.display_name}
                        {'✓' if is_current else ''}
                    </h4>
                    <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 12px;">
                        {theme_config.description}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Apply {theme_config.display_name}", 
                           key=f"theme_{theme_name}",
                           disabled=is_current):
                    self.set_theme(theme_name, user_ctx)
                    st.success(f"Theme changed to {theme_config.display_name}")
                    st.rerun()
        
        # Advanced theme customization
        with st.expander("🔧 Advanced Customization"):
            st.info("Custom theme builder coming soon!")
            
            # Preview of customization options
            st.subheader("Color Customization")
            col1, col2 = st.columns(2)
            
            with col1:
                primary_color = st.color_picker("Primary Color", 
                                              value=self.themes[current_theme].colors['primary'])
            
            with col2:
                accent_color = st.color_picker("Accent Color",
                                             value=self.themes[current_theme].colors['accent'])
            
            st.subheader("Typography")
            font_size = st.slider("Base Font Size", 12, 20, 16)
            
            if st.button("Create Custom Theme"):
                st.info("Custom theme creation will be available in the next update!")
    
    def get_theme_info(self, theme_name: str) -> Dict[str, Any]:
        """Get theme information."""
        if theme_name in self.themes:
            theme = self.themes[theme_name]
            return {
                "name": theme.name,
                "display_name": theme.display_name,
                "description": theme.description,
                "colors": theme.colors,
                "typography": theme.typography
            }
        return {}
    
    def export_theme(self, theme_name: str) -> str:
        """Export theme configuration as JSON."""
        if theme_name in self.themes:
            theme = self.themes[theme_name]
            return json.dumps({
                "name": theme.name,
                "display_name": theme.display_name,
                "description": theme.description,
                "colors": theme.colors,
                "typography": theme.typography,
                "spacing": theme.spacing,
                "effects": theme.effects
            }, indent=2)
        return "{}"