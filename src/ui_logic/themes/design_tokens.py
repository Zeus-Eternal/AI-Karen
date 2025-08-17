"""Design tokens for Kari UI themes."""

COLORS = {
    "light": {
        "background": "#ffffff",
        "surface": "#f5f5f5",
        "accent": "#1e88e5",
    },
    "dark": {
        "background": "#161622",
        "surface": "#212134",
        "accent": "#bb00ff",
    },
    "enterprise": {
        "background": "#f3f4f7",
        "surface": "#ffffff",
        "accent": "#004578",
    },
}

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
}

FONTS = {
    "base": "Inter, Segoe UI, Arial, sans-serif",
    "mono": "Consolas, monospace",
}

__all__ = ["COLORS", "SPACING", "FONTS"]
