"""
AI Routes for Karen's Intelligence

Handles AI-powered features including:
- Prompt enhancement and optimization
- Content analysis and suggestions
- Multi-modal reasoning
- Karen's personality-driven responses
"""

import logging
import time
from typing import Dict, List, Optional, Any

from ai_karen_engine.fastapi_stub import (
    APIRouter as _StubAPIRouter,
    HTTPException as _StubHTTPException,
)
from ai_karen_engine.pydantic_stub import BaseModel as _StubBaseModel, Field as _StubField

APIRouter = _StubAPIRouter
HTTPException = _StubHTTPException
BaseModel = _StubBaseModel
Field = _StubField

try:
    from fastapi import APIRouter as FastAPIAPIRouter, HTTPException as FastAPIHTTPException
except ImportError:
    pass
else:
    APIRouter = FastAPIAPIRouter
    HTTPException = FastAPIHTTPException

try:
    from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
except ImportError:
    pass
else:
    BaseModel = PydanticBaseModel
    Field = PydanticField

logger = logging.getLogger("kari.ai_routes")

router = APIRouter(prefix="/api/ai", tags=["ai"])

class PromptAnalysisRequest(BaseModel):
    """Request for prompt analysis."""
    prompt: str
    context: Optional[str] = None
    target_type: Optional[str] = None  # 'image', 'text', 'audio', 'video'

class PromptAnalysisResponse(BaseModel):
    """Response for prompt analysis."""
    category: str
    confidence: float
    suggestions: List[str]
    improvements: List[str]
    estimated_quality: str
    recommended_providers: List[str]

class ContentSuggestionRequest(BaseModel):
    """Request for content suggestions."""
    user_input: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    selected_models: Dict[str, str] = Field(default_factory=dict)

class ContentSuggestionResponse(BaseModel):
    """Response for content suggestions."""
    text_response: Optional[str] = None
    suggested_media: Optional[List[Dict[str, Any]]] = []
    reasoning: str
    confidence: float

@router.post("/analyze-prompt", response_model=PromptAnalysisResponse)
async def analyze_prompt(request: PromptAnalysisRequest):
    """
    Analyze a prompt and provide Karen's insights.
    """
    try:
        analysis = await karen_analyze_prompt(request.prompt, request.target_type)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-prompt", response_model=Dict[str, Any])
async def enhance_prompt_ai(request: Dict[str, Any]):
    """
    Enhanced prompt improvement with Karen's personality.
    """
    try:
        prompt = request.get("prompt", "")
        content_type = request.get("type", "text")
        provider = request.get("provider")
        personality = request.get("personality", "karen")
        
        enhanced = await karen_enhance_with_personality(
            prompt, content_type, provider, personality
        )
        
        return enhanced
    except Exception as e:
        logger.error(f"Failed to enhance prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-content", response_model=ContentSuggestionResponse)
async def suggest_content(request: ContentSuggestionRequest):
    """
    Suggest appropriate content and media based on user input.
    """
    try:
        suggestion = await karen_suggest_content(
            request.user_input,
            request.conversation_history,
            request.selected_models
        )
        return suggestion
    except Exception as e:
        logger.error(f"Failed to suggest content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/karen-personality")
async def get_karen_personality():
    """
    Get Karen's personality configuration and preferences.
    """
    return {
        "name": "Karen",
        "personality_traits": [
            "Intelligent and analytical",
            "Helpful and supportive", 
            "Detail-oriented",
            "Creative and artistic",
            "Technically proficient"
        ],
        "specialties": [
            "Multi-modal content generation",
            "Prompt optimization",
            "Technical analysis",
            "Creative enhancement",
            "User experience optimization"
        ],
        "preferences": {
            "image_generation": {
                "quality_focus": True,
                "technical_accuracy": True,
                "artistic_enhancement": True,
                "preferred_styles": ["photorealistic", "artistic", "professional"]
            },
            "text_generation": {
                "clarity_focus": True,
                "helpful_tone": True,
                "detailed_explanations": True
            },
            "interaction_style": {
                "proactive_suggestions": True,
                "educational_approach": True,
                "encouraging_feedback": True
            }
        }
    }

# Karen's AI Logic Functions

async def karen_analyze_prompt(prompt: str, target_type: Optional[str] = None) -> PromptAnalysisResponse:
    """
    Karen's intelligent prompt analysis.
    """
    # Analyze prompt characteristics
    category = detect_prompt_category(prompt)
    confidence = calculate_confidence(prompt, category)
    suggestions = generate_suggestions(prompt, category, target_type)
    improvements = suggest_improvements(prompt, category)
    quality = estimate_quality(prompt)
    providers = recommend_providers(prompt, category, target_type)
    
    return PromptAnalysisResponse(
        category=category,
        confidence=confidence,
        suggestions=suggestions,
        improvements=improvements,
        estimated_quality=quality,
        recommended_providers=providers
    )

async def karen_enhance_with_personality(
    prompt: str, 
    content_type: str, 
    provider: Optional[str] = None,
    personality: str = "karen"
) -> Dict[str, Any]:
    """
    Enhanced prompt improvement with Karen's personality and expertise.
    """
    improvements = []
    enhanced_prompt = prompt
    
    # Karen's personality-driven enhancements
    if content_type == "image-generation":
        # Karen prefers high-quality, detailed imagery
        quality_enhancers = [
            "masterpiece", "best quality", "highly detailed", 
            "professional", "8k resolution", "sharp focus"
        ]
        
        # Check if quality terms are missing
        missing_quality = [term for term in quality_enhancers 
                          if term.lower() not in prompt.lower()]
        
        if missing_quality:
            enhanced_prompt += f", {', '.join(missing_quality[:3])}"
            improvements.append("Added quality enhancers for professional results")
        
        # Karen's technical expertise
        if "lighting" not in prompt.lower():
            enhanced_prompt += ", perfect lighting, cinematic lighting"
            improvements.append("Enhanced lighting specifications")
        
        # Karen's artistic sensibility
        if detect_artistic_intent(prompt):
            enhanced_prompt += ", artistic composition, creative perspective"
            improvements.append("Enhanced artistic elements")
        
        # Karen's attention to detail
        if len(prompt.split()) < 10:
            enhanced_prompt += ", detailed background, rich textures, atmospheric"
            improvements.append("Added descriptive details for richer output")
    
    elif content_type == "text-generation":
        # Karen's communication style
        if not prompt.endswith(('?', '.', '!')):
            enhanced_prompt += "."
            improvements.append("Added proper punctuation")
        
        # Karen's helpful nature
        if "help" in prompt.lower() or "how" in prompt.lower():
            enhanced_prompt = f"Please provide a detailed and helpful response to: {enhanced_prompt}"
            improvements.append("Enhanced for helpful, detailed response")
    
    # Karen's reasoning about provider selection
    reasoning = generate_karen_reasoning(prompt, content_type, provider)
    
    return {
        "original_prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "improvements": improvements,
        "confidence": 0.9,  # Karen is confident in her enhancements
        "karen_reasoning": reasoning,
        "suggested_provider": suggest_best_provider(prompt, content_type),
        "suggested_parameters": suggest_parameters(prompt, content_type),
        "personality_notes": [
            "Enhanced with attention to quality and detail",
            "Optimized for professional results",
            "Balanced technical accuracy with creative expression"
        ]
    }

async def karen_suggest_content(
    user_input: str,
    conversation_history: List[Dict[str, str]],
    selected_models: Dict[str, str]
) -> ContentSuggestionResponse:
    """
    Karen's intelligent content suggestions based on context.
    """
    # Analyze if media would enhance the response
    media_suggestions = []
    reasoning_parts = []
    
    # Check for visual content opportunities
    if should_suggest_image(user_input, conversation_history):
        media_suggestions.append({
            "type": "image",
            "prompt": generate_image_prompt(user_input),
            "reasoning": "Visual content would help illustrate this concept",
            "provider": selected_models.get("image", "stable-diffusion-local")
        })
        reasoning_parts.append("Suggested image to enhance understanding")
    
    # Check for audio content opportunities  
    if should_suggest_audio(user_input, conversation_history):
        media_suggestions.append({
            "type": "audio",
            "prompt": generate_audio_prompt(user_input),
            "reasoning": "Audio content would provide better accessibility",
            "provider": selected_models.get("audio", "elevenlabs-tts")
        })
        reasoning_parts.append("Suggested audio for accessibility")
    
    # Generate text response
    text_response = generate_karen_text_response(user_input, conversation_history)
    
    # Karen's reasoning
    reasoning = f"Karen analyzed your request and {', '.join(reasoning_parts) if reasoning_parts else 'provided a comprehensive text response'}."
    
    return ContentSuggestionResponse(
        text_response=text_response,
        suggested_media=media_suggestions,
        reasoning=reasoning,
        confidence=0.85
    )

# Helper Functions

def detect_prompt_category(prompt: str) -> str:
    """Detect the category of a prompt."""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["photo", "picture", "image", "draw", "paint"]):
        return "visual"
    elif any(word in prompt_lower for word in ["sound", "music", "audio", "voice"]):
        return "audio"
    elif any(word in prompt_lower for word in ["video", "animation", "movie"]):
        return "video"
    elif any(word in prompt_lower for word in ["write", "text", "story", "article"]):
        return "text"
    else:
        return "general"

def calculate_confidence(prompt: str, category: str) -> float:
    """Calculate confidence in the analysis."""
    base_confidence = 0.7
    
    # Longer prompts generally get higher confidence
    length_bonus = min(len(prompt.split()) * 0.02, 0.2)
    
    # Specific keywords increase confidence
    keyword_bonus = 0.1 if any(word in prompt.lower() 
                              for word in ["detailed", "high quality", "professional"]) else 0
    
    return min(base_confidence + length_bonus + keyword_bonus, 0.95)

def generate_suggestions(prompt: str, category: str, target_type: Optional[str]) -> List[str]:
    """Generate improvement suggestions."""
    suggestions = []
    
    if category == "visual":
        suggestions.extend([
            "Consider adding style specifications (e.g., 'photorealistic', 'artistic')",
            "Include lighting details for better results",
            "Specify image composition (e.g., 'close-up', 'wide shot')"
        ])
    elif category == "text":
        suggestions.extend([
            "Be more specific about the desired tone",
            "Include context or background information",
            "Specify the target audience"
        ])
    
    return suggestions

def suggest_improvements(prompt: str, category: str) -> List[str]:
    """Suggest specific improvements."""
    improvements = []
    
    if len(prompt.split()) < 5:
        improvements.append("Add more descriptive details")
    
    if category == "visual" and "quality" not in prompt.lower():
        improvements.append("Add quality specifications")
    
    return improvements

def estimate_quality(prompt: str) -> str:
    """Estimate the quality potential of a prompt."""
    score = 0
    
    # Length factor
    word_count = len(prompt.split())
    if word_count > 10:
        score += 2
    elif word_count > 5:
        score += 1
    
    # Quality keywords
    quality_keywords = ["detailed", "high quality", "professional", "masterpiece"]
    score += sum(1 for keyword in quality_keywords if keyword in prompt.lower())
    
    # Technical terms
    technical_terms = ["lighting", "composition", "focus", "resolution"]
    score += sum(1 for term in technical_terms if term in prompt.lower())
    
    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"

def recommend_providers(prompt: str, category: str, target_type: Optional[str]) -> List[str]:
    """Recommend suitable providers."""
    if category == "visual" or target_type == "image":
        if "artistic" in prompt.lower():
            return ["midjourney", "stable-diffusion-local"]
        elif "photo" in prompt.lower():
            return ["dalle-3", "stable-diffusion-local"]
        else:
            return ["stable-diffusion-local", "dalle-3"]
    
    return ["stable-diffusion-local"]  # Default fallback

def detect_artistic_intent(prompt: str) -> bool:
    """Detect if the prompt has artistic intent."""
    artistic_keywords = ["art", "artistic", "painting", "drawing", "creative", "abstract"]
    return any(keyword in prompt.lower() for keyword in artistic_keywords)

def generate_karen_reasoning(prompt: str, content_type: str, provider: Optional[str]) -> str:
    """Generate Karen's reasoning for her enhancements."""
    reasoning = f"I analyzed your {content_type} prompt and enhanced it based on my expertise. "
    
    if content_type == "image-generation":
        reasoning += "I added quality specifications and technical details to ensure professional results. "
        if provider == "stable-diffusion-local":
            reasoning += "Since you're using local Stable Diffusion, I optimized for the best local generation quality."
        elif provider == "dalle-3":
            reasoning += "For DALL-E 3, I focused on clear, descriptive language that works well with their model."
    
    return reasoning

def suggest_best_provider(prompt: str, content_type: str) -> Optional[str]:
    """Suggest the best provider for a prompt."""
    if content_type == "image-generation":
        if "artistic" in prompt.lower() or "creative" in prompt.lower():
            return "midjourney"
        elif "photo" in prompt.lower() or "realistic" in prompt.lower():
            return "dalle-3"
        else:
            return "stable-diffusion-local"
    
    return None

def suggest_parameters(prompt: str, content_type: str) -> Dict[str, Any]:
    """Suggest optimal parameters."""
    if content_type == "image-generation":
        return {
            "steps": 30 if "high quality" in prompt.lower() else 20,
            "guidance_scale": 8.0 if "creative" in prompt.lower() else 7.5,
            "quality": "high"
        }
    
    return {}

def should_suggest_image(user_input: str, history: List[Dict[str, str]]) -> bool:
    """Determine if an image would enhance the response."""
    visual_keywords = ["show", "see", "look", "visual", "picture", "diagram", "chart"]
    return any(keyword in user_input.lower() for keyword in visual_keywords)

def should_suggest_audio(user_input: str, history: List[Dict[str, str]]) -> bool:
    """Determine if audio would enhance the response."""
    audio_keywords = ["hear", "listen", "sound", "pronunciation", "audio"]
    return any(keyword in user_input.lower() for keyword in audio_keywords)

def generate_image_prompt(user_input: str) -> str:
    """Generate an appropriate image prompt."""
    return f"Professional illustration of {user_input}, high quality, detailed, clear"

def generate_audio_prompt(user_input: str) -> str:
    """Generate an appropriate audio prompt."""
    return f"Clear, professional narration: {user_input}"

def generate_karen_text_response(user_input: str, history: List[Dict[str, str]]) -> str:
    """Generate Karen's text response."""
    return f"I understand you're asking about {user_input}. Let me provide a comprehensive response that addresses your needs."
