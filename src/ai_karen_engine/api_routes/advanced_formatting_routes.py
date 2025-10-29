"""
API routes for advanced formatting and structure optimization system.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..services.advanced_formatting_engine import (
    AdvancedFormattingEngine,
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
    FormatType,
    ContentType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/formatting", tags=["Advanced Formatting"])

# Global formatting engine instance
formatting_engine = AdvancedFormattingEngine()


class FormatRequest(BaseModel):
    """Request model for formatting content."""
    content: str = Field(..., description="Content to format")
    display_context: str = Field(default="desktop", description="Display context (desktop, mobile, tablet, terminal, api, print)")
    accessibility_level: str = Field(default="basic", description="Accessibility level (basic, enhanced, full)")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User formatting preferences")
    technical_level: str = Field(default="intermediate", description="User technical level")
    language: str = Field(default="en", description="Content language")


class FormatResponse(BaseModel):
    """Response model for formatted content."""
    formatted_content: str
    format_type: str
    sections_count: int
    navigation_aids_count: int
    accessibility_features: Dict[str, Any]
    metadata: Dict[str, Any]
    estimated_reading_time: Optional[int]


class AnalysisRequest(BaseModel):
    """Request model for content analysis."""
    content: str = Field(..., description="Content to analyze")


class AnalysisResponse(BaseModel):
    """Response model for content analysis."""
    content_type: str
    complexity: str
    sections_count: int
    code_blocks_count: int
    data_structures_count: int
    length: int
    reading_time: int
    technical_density: float


@router.post("/format", response_model=FormatResponse)
async def format_content(request: FormatRequest) -> FormatResponse:
    """
    Format content with advanced formatting and structure optimization.
    
    This endpoint applies intelligent formatting including:
    - Automatic format selection
    - Hierarchical content organization
    - Syntax highlighting for code
    - Navigation aids for long content
    - Accessibility features
    - Responsive formatting for different display contexts
    """
    try:
        logger.info(f"Formatting request for {len(request.content)} characters")
        
        # Create formatting context
        context = FormattingContext(
            display_context=DisplayContext(request.display_context),
            accessibility_level=AccessibilityLevel(request.accessibility_level),
            user_preferences=request.user_preferences,
            content_length=len(request.content),
            technical_level=request.technical_level,
            language=request.language
        )
        
        # Format the content
        formatted_response = await formatting_engine.format_response(request.content, context)
        
        return FormatResponse(
            formatted_content=formatted_response.content,
            format_type=formatted_response.format_type.value,
            sections_count=len(formatted_response.sections),
            navigation_aids_count=len(formatted_response.navigation_aids),
            accessibility_features=formatted_response.accessibility_features,
            metadata=formatted_response.metadata,
            estimated_reading_time=formatted_response.estimated_reading_time
        )
        
    except ValueError as e:
        logger.error(f"Invalid formatting parameters: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error formatting content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during formatting")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze content structure to determine optimal formatting approach.
    
    This endpoint provides detailed analysis of content including:
    - Content type detection
    - Complexity assessment
    - Section identification
    - Code block extraction
    - Data structure identification
    - Reading time estimation
    - Technical density calculation
    """
    try:
        logger.info(f"Analyzing content structure for {len(request.content)} characters")
        
        # Analyze content structure
        analysis = await formatting_engine.analyze_content_structure(request.content)
        
        return AnalysisResponse(
            content_type=analysis['content_type'].value,
            complexity=analysis['complexity'],
            sections_count=len(analysis['sections']),
            code_blocks_count=len(analysis['code_blocks']),
            data_structures_count=len(analysis['data_structures']),
            length=analysis['length'],
            reading_time=analysis['reading_time'],
            technical_density=analysis['technical_density']
        )
        
    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")


@router.post("/format/optimal-type")
async def get_optimal_format_type(request: FormatRequest) -> Dict[str, str]:
    """
    Determine the optimal format type for given content and context.
    
    Returns the recommended format type based on content analysis and display context.
    """
    try:
        logger.info(f"Determining optimal format type for {len(request.content)} characters")
        
        # Create formatting context
        context = FormattingContext(
            display_context=DisplayContext(request.display_context),
            accessibility_level=AccessibilityLevel(request.accessibility_level),
            user_preferences=request.user_preferences,
            content_length=len(request.content),
            technical_level=request.technical_level,
            language=request.language
        )
        
        # Get optimal format type
        format_type = await formatting_engine.select_optimal_format(request.content, context)
        
        return {
            "optimal_format": format_type.value,
            "display_context": request.display_context,
            "content_length": len(request.content)
        }
        
    except ValueError as e:
        logger.error(f"Invalid parameters for format type selection: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error determining optimal format type: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/organize")
async def organize_content_hierarchically(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Organize content into hierarchical sections.
    
    Returns the content organized into prioritized sections with metadata.
    """
    try:
        logger.info(f"Organizing content hierarchically for {len(request.content)} characters")
        
        # Organize content
        sections = await formatting_engine.organize_content_hierarchically(request.content)
        
        return {
            "sections": [
                {
                    "content": section.content,
                    "section_type": section.section_type.value,
                    "priority": section.priority,
                    "format_hint": section.format_hint.value if section.format_hint else None,
                    "metadata": section.metadata,
                    "navigation_id": section.navigation_id,
                    "accessibility_text": section.accessibility_text
                }
                for section in sections
            ],
            "total_sections": len(sections)
        }
        
    except Exception as e:
        logger.error(f"Error organizing content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during organization")


@router.post("/syntax-highlight")
async def apply_syntax_highlighting(
    code: str,
    language: str = "text"
) -> Dict[str, str]:
    """
    Apply syntax highlighting to code blocks.
    
    Returns the code with syntax highlighting markup applied.
    """
    try:
        logger.info(f"Applying syntax highlighting for {language} code ({len(code)} characters)")
        
        # Apply syntax highlighting
        highlighted_code = await formatting_engine.apply_syntax_highlighting(code, language)
        
        return {
            "original_code": code,
            "highlighted_code": highlighted_code,
            "language": language,
            "highlighting_applied": highlighted_code != code
        }
        
    except Exception as e:
        logger.error(f"Error applying syntax highlighting: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during syntax highlighting")


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported programming languages for syntax highlighting.
    
    Returns information about supported languages and their features.
    """
    try:
        return {
            "supported_languages": list(formatting_engine.code_languages),
            "total_languages": len(formatting_engine.code_languages),
            "syntax_highlighters": list(formatting_engine.syntax_highlighters.keys()),
            "features": {
                "keyword_highlighting": True,
                "builtin_highlighting": True,
                "string_highlighting": True,
                "comment_highlighting": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/display-contexts")
async def get_display_contexts() -> Dict[str, Any]:
    """
    Get available display contexts for responsive formatting.
    
    Returns information about supported display contexts and their characteristics.
    """
    try:
        return {
            "display_contexts": [context.value for context in DisplayContext],
            "accessibility_levels": [level.value for level in AccessibilityLevel],
            "format_types": [format_type.value for format_type in FormatType],
            "content_types": [content_type.value for content_type in ContentType],
            "responsive_features": {
                "mobile_optimization": True,
                "tablet_optimization": True,
                "terminal_formatting": True,
                "print_formatting": True,
                "api_structured_output": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting display contexts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/accessibility-features")
async def get_accessibility_features(request: FormatRequest) -> Dict[str, Any]:
    """
    Get accessibility features for formatted content.
    
    Returns accessibility enhancements based on the specified accessibility level.
    """
    try:
        logger.info(f"Getting accessibility features for {len(request.content)} characters")
        
        # Create formatting context
        context = FormattingContext(
            display_context=DisplayContext(request.display_context),
            accessibility_level=AccessibilityLevel(request.accessibility_level),
            user_preferences=request.user_preferences,
            content_length=len(request.content),
            technical_level=request.technical_level,
            language=request.language
        )
        
        # Format content to get accessibility features
        formatted_response = await formatting_engine.format_response(request.content, context)
        
        return {
            "accessibility_level": request.accessibility_level,
            "features": formatted_response.accessibility_features,
            "estimated_reading_time": formatted_response.estimated_reading_time,
            "content_warnings": formatted_response.accessibility_features.get('content_warning'),
            "screen_reader_optimized": 'screen_reader_text' in formatted_response.accessibility_features,
            "keyboard_navigation": 'keyboard_navigation' in formatted_response.accessibility_features
        }
        
    except ValueError as e:
        logger.error(f"Invalid accessibility parameters: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting accessibility features: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the advanced formatting service."""
    try:
        # Test basic functionality
        test_content = "# Test\nThis is a test with `code` and a list:\n- Item 1\n- Item 2"
        analysis = await formatting_engine.analyze_content_structure(test_content)
        
        return {
            "status": "healthy",
            "service": "Advanced Formatting Engine",
            "features": "format_selection,hierarchical_organization,syntax_highlighting,navigation_aids,accessibility,responsive_formatting",
            "test_analysis": f"detected_{analysis['content_type'].value}_content"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")