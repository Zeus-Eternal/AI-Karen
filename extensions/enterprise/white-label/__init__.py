"""
White Label Branding Extension - Migrated from ui_logic/pages/white_label.py

This extension provides comprehensive white-label branding capabilities including:
- Custom theming and color schemes
- Logo and asset management
- Multi-tenant branding configuration
- Brand consistency enforcement
- Custom domain and URL management
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import json
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

logger = logging.getLogger(__name__)


class BrandTheme(BaseModel):
    """Brand theme configuration."""
    id: str
    name: str
    description: Optional[str] = None
    colors: Dict[str, str]  # Color palette
    fonts: Dict[str, str]  # Font configurations
    spacing: Dict[str, Union[int, str]]  # Spacing values
    borders: Dict[str, str]  # Border styles
    shadows: Dict[str, str]  # Shadow styles
    created_at: str
    updated_at: str
    is_active: bool = False


class BrandAsset(BaseModel):
    """Brand asset (logo, images, etc.)."""
    id: str
    name: str
    asset_type: str  # "logo", "favicon", "background", "icon"
    file_path: str
    file_size: int
    mime_type: str
    dimensions: Optional[Dict[str, int]] = None
    alt_text: Optional[str] = None
    usage_contexts: List[str] = []  # Where this asset is used
    uploaded_at: str


class BrandConfiguration(BaseModel):
    """Overall brand configuration."""
    tenant_id: str
    brand_name: str
    tagline: Optional[str] = None
    primary_domain: Optional[str] = None
    custom_domains: List[str] = []
    active_theme_id: str
    logo_asset_id: Optional[str] = None
    favicon_asset_id: Optional[str] = None
    email_settings: Dict[str, Any] = {}
    social_links: Dict[str, str] = {}
    contact_info: Dict[str, str] = {}
    legal_info: Dict[str, str] = {}
    feature_flags: Dict[str, bool] = {}
    created_at: str
    updated_at: str


class ThemeRequest(BaseModel):
    """Request to create or update a theme."""
    name: str
    description: Optional[str] = None
    colors: Dict[str, str]
    fonts: Optional[Dict[str, str]] = None
    spacing: Optional[Dict[str, Union[int, str]]] = None
    borders: Optional[Dict[str, str]] = None
    shadows: Optional[Dict[str, str]] = None


class WhiteLabelBrandingExtension(BaseExtension, HookMixin):
    """White Label Branding Extension for enterprise customization."""
    
    async def _initialize(self) -> None:
        """Initialize the White Label Branding Extension."""
        self.logger.info("White Label Branding Extension initializing...")
        
        # Initialize branding storage
        self.themes: Dict[str, BrandTheme] = {}
        self.assets: Dict[str, BrandAsset] = {}
        self.brand_configs: Dict[str, BrandConfiguration] = {}  # tenant_id -> config
        self.branding_history: List[Dict[str, Any]] = []
        
        # Initialize default themes
        await self._load_default_themes()
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        self.logger.info("White Label Branding Extension initialized successfully")
    
    async def _load_default_themes(self) -> None:
        """Load default brand themes."""
        default_themes = {
            "corporate_blue": BrandTheme(
                id="corporate_blue",
                name="Corporate Blue",
                description="Professional blue theme for corporate environments",
                colors={
                    "primary": "#2563eb",
                    "secondary": "#64748b",
                    "accent": "#0ea5e9",
                    "background": "#ffffff",
                    "surface": "#f8fafc",
                    "text": "#1e293b",
                    "text_secondary": "#64748b",
                    "border": "#e2e8f0",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                },
                fonts={
                    "primary": "Inter, system-ui, sans-serif",
                    "secondary": "Inter, system-ui, sans-serif",
                    "monospace": "JetBrains Mono, monospace"
                },
                spacing={
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                    "2xl": "3rem"
                },
                borders={
                    "radius": "0.375rem",
                    "width": "1px",
                    "style": "solid"
                },
                shadows={
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)"
                },
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                is_active=True
            ),
            "modern_dark": BrandTheme(
                id="modern_dark",
                name="Modern Dark",
                description="Sleek dark theme for modern applications",
                colors={
                    "primary": "#8b5cf6",
                    "secondary": "#6b7280",
                    "accent": "#a855f7",
                    "background": "#111827",
                    "surface": "#1f2937",
                    "text": "#f9fafb",
                    "text_secondary": "#9ca3af",
                    "border": "#374151",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                },
                fonts={
                    "primary": "Inter, system-ui, sans-serif",
                    "secondary": "Inter, system-ui, sans-serif",
                    "monospace": "JetBrains Mono, monospace"
                },
                spacing={
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                    "2xl": "3rem"
                },
                borders={
                    "radius": "0.5rem",
                    "width": "1px",
                    "style": "solid"
                },
                shadows={
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.3)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.4)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.4)"
                },
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                is_active=False
            ),
            "minimal_green": BrandTheme(
                id="minimal_green",
                name="Minimal Green",
                description="Clean minimal theme with green accents",
                colors={
                    "primary": "#059669",
                    "secondary": "#6b7280",
                    "accent": "#10b981",
                    "background": "#ffffff",
                    "surface": "#f9fafb",
                    "text": "#111827",
                    "text_secondary": "#6b7280",
                    "border": "#d1d5db",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                },
                fonts={
                    "primary": "system-ui, sans-serif",
                    "secondary": "system-ui, sans-serif",
                    "monospace": "Monaco, monospace"
                },
                spacing={
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                    "2xl": "3rem"
                },
                borders={
                    "radius": "0.25rem",
                    "width": "1px",
                    "style": "solid"
                },
                shadows={
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)"
                },
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                is_active=False
            )
        }
        
        self.themes.update(default_themes)
        self.logger.info(f"Loaded {len(default_themes)} default themes")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered branding assistance."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register branding tools
            await self.register_mcp_tool(
                name="create_brand_theme",
                handler=self._create_brand_theme_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Theme name"},
                        "description": {"type": "string", "description": "Theme description"},
                        "primary_color": {"type": "string", "description": "Primary brand color (hex)"},
                        "style": {"type": "string", "enum": ["corporate", "modern", "minimal", "creative"], "description": "Theme style"},
                        "dark_mode": {"type": "boolean", "default": False, "description": "Create dark mode variant"}
                    },
                    "required": ["name", "primary_color", "style"]
                },
                description="Create a custom brand theme with AI-generated color palette and styling"
            )
            
            await self.register_mcp_tool(
                name="analyze_brand_consistency",
                handler=self._analyze_brand_consistency_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "tenant_id": {"type": "string", "description": "Tenant to analyze"},
                        "check_assets": {"type": "boolean", "default": True, "description": "Check asset consistency"},
                        "check_colors": {"type": "boolean", "default": True, "description": "Check color usage"},
                        "check_typography": {"type": "boolean", "default": True, "description": "Check typography consistency"}
                    },
                    "required": ["tenant_id"]
                },
                description="Analyze brand consistency across tenant configuration"
            )
            
            await self.register_mcp_tool(
                name="generate_brand_guidelines",
                handler=self._generate_brand_guidelines_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "tenant_id": {"type": "string", "description": "Tenant ID"},
                        "include_usage_examples": {"type": "boolean", "default": True, "description": "Include usage examples"},
                        "format": {"type": "string", "enum": ["markdown", "html", "json"], "default": "markdown", "description": "Output format"}
                    },
                    "required": ["tenant_id"]
                },
                description="Generate comprehensive brand guidelines document"
            )
    
    async def _create_brand_theme_tool(self, name: str, primary_color: str, style: str, description: Optional[str] = None, dark_mode: bool = False) -> Dict[str, Any]:
        """MCP tool to create AI-generated brand themes."""
        try:
            # Generate theme ID
            theme_id = f"theme_{len(self.themes) + 1}"
            
            # Generate color palette based on primary color and style
            color_palette = self._generate_color_palette(primary_color, style, dark_mode)
            
            # Generate typography based on style
            typography = self._generate_typography(style)
            
            # Generate spacing and layout based on style
            spacing = self._generate_spacing(style)
            borders = self._generate_borders(style)
            shadows = self._generate_shadows(style, dark_mode)
            
            # Create theme
            theme = BrandTheme(
                id=theme_id,
                name=name,
                description=description or f"AI-generated {style} theme",
                colors=color_palette,
                fonts=typography,
                spacing=spacing,
                borders=borders,
                shadows=shadows,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                is_active=False
            )
            
            self.themes[theme_id] = theme
            
            # Log theme creation
            self._log_branding_action("theme_created", {
                "theme_id": theme_id,
                "name": name,
                "style": style,
                "dark_mode": dark_mode
            })
            
            return {
                "success": True,
                "theme": theme.dict(),
                "message": f"Theme '{name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create brand theme: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_brand_consistency_tool(self, tenant_id: str, check_assets: bool = True, check_colors: bool = True, check_typography: bool = True) -> Dict[str, Any]:
        """MCP tool to analyze brand consistency."""
        try:
            brand_config = self.brand_configs.get(tenant_id)
            if not brand_config:
                return {
                    "success": False,
                    "error": f"No brand configuration found for tenant '{tenant_id}'"
                }
            
            consistency_analysis = {
                "tenant_id": tenant_id,
                "overall_score": 0.0,
                "issues": [],
                "recommendations": [],
                "checks_performed": []
            }
            
            total_checks = 0
            passed_checks = 0
            
            # Check theme consistency
            if brand_config.active_theme_id in self.themes:
                passed_checks += 1
                consistency_analysis["checks_performed"].append("Active theme exists")
            else:
                consistency_analysis["issues"].append("Active theme not found")
                consistency_analysis["recommendations"].append("Set a valid active theme")
            total_checks += 1
            
            # Check asset consistency
            if check_assets:
                if brand_config.logo_asset_id and brand_config.logo_asset_id in self.assets:
                    passed_checks += 1
                    consistency_analysis["checks_performed"].append("Logo asset exists")
                else:
                    consistency_analysis["issues"].append("Logo asset missing or invalid")
                    consistency_analysis["recommendations"].append("Upload a brand logo")
                total_checks += 1
                
                if brand_config.favicon_asset_id and brand_config.favicon_asset_id in self.assets:
                    passed_checks += 1
                    consistency_analysis["checks_performed"].append("Favicon asset exists")
                else:
                    consistency_analysis["issues"].append("Favicon asset missing or invalid")
                    consistency_analysis["recommendations"].append("Upload a favicon")
                total_checks += 1
            
            # Check color consistency
            if check_colors:
                theme = self.themes.get(brand_config.active_theme_id)
                if theme and len(theme.colors) >= 5:  # Minimum color palette
                    passed_checks += 1
                    consistency_analysis["checks_performed"].append("Complete color palette")
                else:
                    consistency_analysis["issues"].append("Incomplete color palette")
                    consistency_analysis["recommendations"].append("Define a complete color palette")
                total_checks += 1
            
            # Check typography consistency
            if check_typography:
                theme = self.themes.get(brand_config.active_theme_id)
                if theme and theme.fonts and len(theme.fonts) >= 2:
                    passed_checks += 1
                    consistency_analysis["checks_performed"].append("Typography defined")
                else:
                    consistency_analysis["issues"].append("Typography not properly defined")
                    consistency_analysis["recommendations"].append("Define primary and secondary fonts")
                total_checks += 1
            
            # Calculate overall score
            consistency_analysis["overall_score"] = (passed_checks / total_checks) if total_checks > 0 else 0.0
            
            return {
                "success": True,
                "analysis": consistency_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze brand consistency: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_brand_guidelines_tool(self, tenant_id: str, include_usage_examples: bool = True, format: str = "markdown") -> Dict[str, Any]:
        """MCP tool to generate brand guidelines."""
        try:
            brand_config = self.brand_configs.get(tenant_id)
            if not brand_config:
                return {
                    "success": False,
                    "error": f"No brand configuration found for tenant '{tenant_id}'"
                }
            
            theme = self.themes.get(brand_config.active_theme_id)
            if not theme:
                return {
                    "success": False,
                    "error": "Active theme not found"
                }
            
            # Generate guidelines content
            guidelines = self._generate_guidelines_content(brand_config, theme, include_usage_examples, format)
            
            return {
                "success": True,
                "guidelines": guidelines,
                "format": format,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate brand guidelines: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_color_palette(self, primary_color: str, style: str, dark_mode: bool) -> Dict[str, str]:
        """Generate a complete color palette from primary color."""
        # This is a simplified color generation - in practice, you'd use color theory algorithms
        base_colors = {
            "primary": primary_color,
            "secondary": "#6b7280",  # Neutral gray
            "accent": primary_color,  # Same as primary for now
        }
        
        if dark_mode:
            base_colors.update({
                "background": "#111827",
                "surface": "#1f2937",
                "text": "#f9fafb",
                "text_secondary": "#9ca3af",
                "border": "#374151"
            })
        else:
            base_colors.update({
                "background": "#ffffff",
                "surface": "#f8fafc" if style == "corporate" else "#f9fafb",
                "text": "#1e293b" if style == "corporate" else "#111827",
                "text_secondary": "#64748b" if style == "corporate" else "#6b7280",
                "border": "#e2e8f0" if style == "corporate" else "#d1d5db"
            })
        
        # Add semantic colors
        base_colors.update({
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444"
        })
        
        return base_colors
    
    def _generate_typography(self, style: str) -> Dict[str, str]:
        """Generate typography based on style."""
        typography_map = {
            "corporate": {
                "primary": "Inter, system-ui, sans-serif",
                "secondary": "Inter, system-ui, sans-serif",
                "monospace": "JetBrains Mono, monospace"
            },
            "modern": {
                "primary": "Poppins, system-ui, sans-serif",
                "secondary": "Inter, system-ui, sans-serif",
                "monospace": "Fira Code, monospace"
            },
            "minimal": {
                "primary": "system-ui, sans-serif",
                "secondary": "system-ui, sans-serif",
                "monospace": "Monaco, monospace"
            },
            "creative": {
                "primary": "Montserrat, system-ui, sans-serif",
                "secondary": "Open Sans, system-ui, sans-serif",
                "monospace": "Source Code Pro, monospace"
            }
        }
        
        return typography_map.get(style, typography_map["corporate"])
    
    def _generate_spacing(self, style: str) -> Dict[str, str]:
        """Generate spacing values based on style."""
        if style == "minimal":
            return {
                "xs": "0.125rem",
                "sm": "0.25rem",
                "md": "0.5rem",
                "lg": "1rem",
                "xl": "1.5rem",
                "2xl": "2rem"
            }
        elif style == "creative":
            return {
                "xs": "0.375rem",
                "sm": "0.75rem",
                "md": "1.25rem",
                "lg": "2rem",
                "xl": "2.5rem",
                "2xl": "4rem"
            }
        else:  # corporate, modern
            return {
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem",
                "2xl": "3rem"
            }
    
    def _generate_borders(self, style: str) -> Dict[str, str]:
        """Generate border styles based on style."""
        border_map = {
            "corporate": {"radius": "0.375rem", "width": "1px", "style": "solid"},
            "modern": {"radius": "0.5rem", "width": "1px", "style": "solid"},
            "minimal": {"radius": "0.25rem", "width": "1px", "style": "solid"},
            "creative": {"radius": "0.75rem", "width": "2px", "style": "solid"}
        }
        
        return border_map.get(style, border_map["corporate"])
    
    def _generate_shadows(self, style: str, dark_mode: bool) -> Dict[str, str]:
        """Generate shadow styles based on style and mode."""
        if dark_mode:
            return {
                "sm": "0 1px 2px 0 rgb(0 0 0 / 0.3)",
                "md": "0 4px 6px -1px rgb(0 0 0 / 0.4)",
                "lg": "0 10px 15px -3px rgb(0 0 0 / 0.4)"
            }
        else:
            shadow_map = {
                "corporate": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)"
                },
                "modern": {
                    "sm": "0 1px 3px 0 rgb(0 0 0 / 0.1)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 20px 25px -5px rgb(0 0 0 / 0.1)"
                },
                "minimal": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "md": "0 2px 4px 0 rgb(0 0 0 / 0.06)",
                    "lg": "0 4px 8px 0 rgb(0 0 0 / 0.08)"
                },
                "creative": {
                    "sm": "0 2px 4px 0 rgb(0 0 0 / 0.1)",
                    "md": "0 8px 16px 0 rgb(0 0 0 / 0.15)",
                    "lg": "0 16px 32px 0 rgb(0 0 0 / 0.2)"
                }
            }
            
            return shadow_map.get(style, shadow_map["corporate"])
    
    def _generate_guidelines_content(self, brand_config: BrandConfiguration, theme: BrandTheme, include_examples: bool, format: str) -> str:
        """Generate brand guidelines content."""
        if format == "markdown":
            return self._generate_markdown_guidelines(brand_config, theme, include_examples)
        elif format == "html":
            return self._generate_html_guidelines(brand_config, theme, include_examples)
        elif format == "json":
            return json.dumps(self._generate_json_guidelines(brand_config, theme, include_examples), indent=2)
        else:
            return self._generate_markdown_guidelines(brand_config, theme, include_examples)
    
    def _generate_markdown_guidelines(self, brand_config: BrandConfiguration, theme: BrandTheme, include_examples: bool) -> str:
        """Generate markdown format brand guidelines."""
        guidelines = f"""# {brand_config.brand_name} Brand Guidelines

## Brand Identity

**Brand Name:** {brand_config.brand_name}
**Tagline:** {brand_config.tagline or 'Not specified'}
**Primary Domain:** {brand_config.primary_domain or 'Not specified'}

## Color Palette

### Primary Colors
"""
        
        for color_name, color_value in theme.colors.items():
            guidelines += f"- **{color_name.replace('_', ' ').title()}:** `{color_value}`\n"
        
        guidelines += f"""
## Typography

### Font Families
"""
        
        for font_type, font_family in theme.fonts.items():
            guidelines += f"- **{font_type.replace('_', ' ').title()}:** {font_family}\n"
        
        guidelines += f"""
## Spacing System

### Spacing Scale
"""
        
        for size, value in theme.spacing.items():
            guidelines += f"- **{size}:** {value}\n"
        
        if include_examples:
            guidelines += """
## Usage Examples

### Color Usage
- Use primary color for main actions and highlights
- Use secondary color for supporting elements
- Use accent color sparingly for emphasis

### Typography Usage
- Use primary font for headings and important text
- Use secondary font for body text and descriptions
- Use monospace font for code and technical content

### Spacing Usage
- Use consistent spacing throughout the interface
- Follow the spacing scale for margins and padding
- Maintain visual hierarchy with appropriate spacing
"""
        
        guidelines += f"""
## Brand Assets

### Logo
- Asset ID: {brand_config.logo_asset_id or 'Not specified'}
- Usage: Primary brand identifier

### Favicon
- Asset ID: {brand_config.favicon_asset_id or 'Not specified'}
- Usage: Browser tab and bookmark icon

---

*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
        
        return guidelines
    
    def _generate_html_guidelines(self, brand_config: BrandConfiguration, theme: BrandTheme, include_examples: bool) -> str:
        """Generate HTML format brand guidelines."""
        # Simplified HTML generation
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{brand_config.brand_name} Brand Guidelines</title>
    <style>
        body {{ font-family: {theme.fonts.get('primary', 'sans-serif')}; color: {theme.colors.get('text', '#000')}; }}
        .color-swatch {{ display: inline-block; width: 50px; height: 50px; margin: 5px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>{brand_config.brand_name} Brand Guidelines</h1>
    <h2>Color Palette</h2>
    {''.join([f'<div class="color-swatch" style="background-color: {color}" title="{name}: {color}"></div>' for name, color in theme.colors.items()])}
    <h2>Typography</h2>
    <p>Primary Font: {theme.fonts.get('primary', 'Not specified')}</p>
    <p>Secondary Font: {theme.fonts.get('secondary', 'Not specified')}</p>
</body>
</html>
"""
    
    def _generate_json_guidelines(self, brand_config: BrandConfiguration, theme: BrandTheme, include_examples: bool) -> Dict[str, Any]:
        """Generate JSON format brand guidelines."""
        return {
            "brand": {
                "name": brand_config.brand_name,
                "tagline": brand_config.tagline,
                "domain": brand_config.primary_domain
            },
            "theme": theme.dict(),
            "assets": {
                "logo": brand_config.logo_asset_id,
                "favicon": brand_config.favicon_asset_id
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _log_branding_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log branding actions for audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        
        self.branding_history.append(log_entry)
        
        # Keep only recent history
        if len(self.branding_history) > 1000:
            self.branding_history = self.branding_history[-1000:]
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the White Label Branding Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.get("/themes")
        async def list_themes():
            """List all available themes."""
            return {"themes": [theme.dict() for theme in self.themes.values()]}
        
        @router.post("/themes")
        async def create_theme(request: ThemeRequest):
            """Create a new brand theme."""
            result = await self._create_brand_theme_tool(
                request.name,
                request.colors.get("primary", "#2563eb"),
                "custom",
                request.description
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/themes/{theme_id}")
        async def get_theme(theme_id: str):
            """Get a specific theme."""
            if theme_id not in self.themes:
                raise HTTPException(status_code=404, detail="Theme not found")
            return self.themes[theme_id].dict()
        
        @router.put("/themes/{theme_id}")
        async def update_theme(theme_id: str, request: ThemeRequest):
            """Update an existing theme."""
            if theme_id not in self.themes:
                raise HTTPException(status_code=404, detail="Theme not found")
            
            theme = self.themes[theme_id]
            theme.name = request.name
            theme.description = request.description
            theme.colors = request.colors
            if request.fonts:
                theme.fonts = request.fonts
            if request.spacing:
                theme.spacing = request.spacing
            if request.borders:
                theme.borders = request.borders
            if request.shadows:
                theme.shadows = request.shadows
            theme.updated_at = datetime.utcnow().isoformat()
            
            self._log_branding_action("theme_updated", {"theme_id": theme_id, "name": request.name})
            
            return theme.dict()
        
        @router.post("/assets")
        async def upload_asset(
            file: UploadFile = File(...),
            asset_type: str = Form(...),
            name: str = Form(...),
            alt_text: str = Form(default=""),
            usage_contexts: str = Form(default="")
        ):
            """Upload a brand asset."""
            try:
                # Read file data
                file_data = await file.read()
                
                # Generate asset ID and file path
                asset_id = f"asset_{len(self.assets) + 1}"
                file_path = f"/assets/{asset_id}_{file.filename}"
                
                # Create asset record
                asset = BrandAsset(
                    id=asset_id,
                    name=name,
                    asset_type=asset_type,
                    file_path=file_path,
                    file_size=len(file_data),
                    mime_type=file.content_type or "application/octet-stream",
                    alt_text=alt_text,
                    usage_contexts=usage_contexts.split(",") if usage_contexts else [],
                    uploaded_at=datetime.utcnow().isoformat()
                )
                
                self.assets[asset_id] = asset
                
                # Log asset upload
                self._log_branding_action("asset_uploaded", {
                    "asset_id": asset_id,
                    "name": name,
                    "type": asset_type,
                    "size": len(file_data)
                })
                
                return asset.dict()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/assets")
        async def list_assets(asset_type: Optional[str] = None):
            """List brand assets."""
            assets = list(self.assets.values())
            if asset_type:
                assets = [asset for asset in assets if asset.asset_type == asset_type]
            return {"assets": [asset.dict() for asset in assets]}
        
        @router.delete("/assets/{asset_id}")
        async def delete_asset(asset_id: str):
            """Delete a brand asset."""
            if asset_id not in self.assets:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            asset = self.assets.pop(asset_id)
            
            # Log asset deletion
            self._log_branding_action("asset_deleted", {
                "asset_id": asset_id,
                "name": asset.name,
                "type": asset.asset_type
            })
            
            return {"message": f"Asset '{asset.name}' deleted successfully"}
        
        @router.get("/config/{tenant_id}")
        async def get_brand_config(tenant_id: str):
            """Get brand configuration for a tenant."""
            if tenant_id not in self.brand_configs:
                raise HTTPException(status_code=404, detail="Brand configuration not found")
            return self.brand_configs[tenant_id].dict()
        
        @router.put("/config/{tenant_id}")
        async def update_brand_config(tenant_id: str, config_data: Dict[str, Any]):
            """Update brand configuration for a tenant."""
            if tenant_id in self.brand_configs:
                config = self.brand_configs[tenant_id]
                # Update existing config
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.updated_at = datetime.utcnow().isoformat()
            else:
                # Create new config
                config = BrandConfiguration(
                    tenant_id=tenant_id,
                    brand_name=config_data.get("brand_name", "Unnamed Brand"),
                    tagline=config_data.get("tagline"),
                    primary_domain=config_data.get("primary_domain"),
                    custom_domains=config_data.get("custom_domains", []),
                    active_theme_id=config_data.get("active_theme_id", "corporate_blue"),
                    logo_asset_id=config_data.get("logo_asset_id"),
                    favicon_asset_id=config_data.get("favicon_asset_id"),
                    email_settings=config_data.get("email_settings", {}),
                    social_links=config_data.get("social_links", {}),
                    contact_info=config_data.get("contact_info", {}),
                    legal_info=config_data.get("legal_info", {}),
                    feature_flags=config_data.get("feature_flags", {}),
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat()
                )
                self.brand_configs[tenant_id] = config
            
            # Log config update
            self._log_branding_action("config_updated", {
                "tenant_id": tenant_id,
                "brand_name": config.brand_name
            })
            
            return config.dict()
        
        @router.post("/analyze/{tenant_id}")
        async def analyze_brand_consistency(tenant_id: str):
            """Analyze brand consistency for a tenant."""
            result = await self._analyze_brand_consistency_tool(tenant_id)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/guidelines/{tenant_id}")
        async def generate_brand_guidelines(tenant_id: str, format: str = "markdown", include_examples: bool = True):
            """Generate brand guidelines for a tenant."""
            result = await self._generate_brand_guidelines_tool(tenant_id, include_examples, format)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/history")
        async def get_branding_history(limit: int = 100):
            """Get branding action history."""
            return {
                "history": self.branding_history[-limit:] if limit > 0 else self.branding_history,
                "total_actions": len(self.branding_history)
            }
        
        return router
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Branding Center."""
        components = super().create_ui_components()
        
        # Add branding center data
        components["branding_center"] = {
            "title": "White Label Branding Center",
            "description": "Enterprise branding and customization management",
            "data": {
                "total_themes": len(self.themes),
                "active_themes": len([t for t in self.themes.values() if t.is_active]),
                "total_assets": len(self.assets),
                "configured_tenants": len(self.brand_configs),
                "recent_actions": len([a for a in self.branding_history if 
                                     datetime.fromisoformat(a["timestamp"]) > datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)]),
                "asset_types": list(set(asset.asset_type for asset in self.assets.values()))
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the White Label Branding Extension."""
        self.logger.info("White Label Branding Extension shutting down...")
        
        # Clear data structures
        self.themes.clear()
        self.assets.clear()
        self.brand_configs.clear()
        self.branding_history.clear()
        
        self.logger.info("White Label Branding Extension shut down successfully")


# Export the extension class
__all__ = ["WhiteLabelBrandingExtension"]