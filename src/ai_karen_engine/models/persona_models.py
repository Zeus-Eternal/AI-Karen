"""
Persona and Style Control Models
Core data models for AI Karen's persona-driven chat system
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToneEnum(str, Enum):
    """Available tone options for AI responses"""
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"


class VerbosityEnum(str, Enum):
    """Response length preferences"""
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class LanguageEnum(str, Enum):
    """Supported languages and locales"""
    EN_US = "en-US"
    EN_UK = "en-UK"
    EN_CA = "en-CA"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    IT_IT = "it-IT"
    PT_BR = "pt-BR"
    JA_JP = "ja-JP"
    KO_KR = "ko-KR"
    ZH_CN = "zh-CN"


class PersonaMemoryWeight(str, Enum):
    """Memory weighting strategies for different personas"""
    LOW = "low"          # Show minimal past context
    MEDIUM = "medium"    # Balanced context recall
    HIGH = "high"        # Rich context from past interactions
    ADAPTIVE = "adaptive" # AI-driven context selection


class Persona(BaseModel):
    """Individual persona configuration"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Core persona settings
    system_prompt: str = Field(..., min_length=10, max_length=2000)
    default_tone: ToneEnum = ToneEnum.FRIENDLY
    default_verbosity: VerbosityEnum = VerbosityEnum.BALANCED
    default_language: LanguageEnum = LanguageEnum.EN_US
    
    # Memory and context settings
    memory_weight: PersonaMemoryWeight = PersonaMemoryWeight.MEDIUM
    context_window_size: int = Field(default=10, ge=1, le=50)
    
    # Domain-specific settings
    domain_knowledge: List[str] = Field(default_factory=list)
    specialized_instructions: Optional[str] = Field(None, max_length=1000)
    
    # Behavioral modifiers
    use_emoji: bool = False
    formality_level: float = Field(default=0.5, ge=0.0, le=1.0)  # 0=casual, 1=formal
    creativity_level: float = Field(default=0.5, ge=0.0, le=1.0)  # 0=conservative, 1=creative
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_system_persona: bool = False  # Built-in vs user-created
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v):
        if not v.strip():
            raise ValueError('System prompt cannot be empty')
        return v.strip()
    
    @field_validator('domain_knowledge')
    @classmethod
    def validate_domain_knowledge(cls, v):
        return [domain.strip().lower() for domain in v if domain.strip()]


class PersonaStyleOverride(BaseModel):
    """Temporary style overrides for a single conversation turn"""
    
    tone: Optional[ToneEnum] = None
    verbosity: Optional[VerbosityEnum] = None
    language: Optional[LanguageEnum] = None
    use_emoji: Optional[bool] = None
    formality_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    creativity_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Special instructions for this turn only
    turn_instructions: Optional[str] = Field(None, max_length=500)


class UserPersonaPreferences(BaseModel):
    """User's persona and style preferences"""
    
    user_id: str
    tenant_id: str = "default"
    
    # Active persona
    active_persona_id: Optional[str] = None
    
    # Global style preferences (applied when no persona is active)
    default_tone: ToneEnum = ToneEnum.FRIENDLY
    default_verbosity: VerbosityEnum = VerbosityEnum.BALANCED
    default_language: LanguageEnum = LanguageEnum.EN_US
    
    # User's custom personas
    custom_personas: List[Persona] = Field(default_factory=list)
    
    # Style adaptation settings
    enable_style_adaptation: bool = True
    adaptation_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Memory preferences
    enable_persona_memory_filtering: bool = True
    cross_persona_memory_sharing: bool = False
    
    # UI preferences
    show_persona_selector: bool = True
    show_style_controls: bool = True
    enable_quick_style_adjustments: bool = True
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('custom_personas')
    @classmethod
    def validate_custom_personas(cls, v):
        # Ensure persona names are unique
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError('Persona names must be unique')
        return v


class ChatStyleContext(BaseModel):
    """Complete style context for a chat interaction"""
    
    # Active persona
    persona: Optional[Persona] = None
    
    # Style overrides for this turn
    style_override: Optional[PersonaStyleOverride] = None
    
    # Detected user style (from NLP analysis)
    detected_user_tone: Optional[ToneEnum] = None
    detected_formality: Optional[float] = Field(None, ge=0.0, le=1.0)
    detected_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
    # Memory context filtering
    memory_persona_filter: Optional[str] = None
    memory_tone_filter: Optional[ToneEnum] = None
    
    # Conversation metadata
    conversation_id: Optional[str] = None
    turn_number: int = 1
    
    def get_effective_tone(self) -> ToneEnum:
        """Get the effective tone considering overrides and persona"""
        if self.style_override and self.style_override.tone:
            return self.style_override.tone
        if self.persona:
            return self.persona.default_tone
        return ToneEnum.FRIENDLY
    
    def get_effective_verbosity(self) -> VerbosityEnum:
        """Get the effective verbosity considering overrides and persona"""
        if self.style_override and self.style_override.verbosity:
            return self.style_override.verbosity
        if self.persona:
            return self.persona.default_verbosity
        return VerbosityEnum.BALANCED
    
    def get_effective_language(self) -> LanguageEnum:
        """Get the effective language considering overrides and persona"""
        if self.style_override and self.style_override.language:
            return self.style_override.language
        if self.persona:
            return self.persona.default_language
        return LanguageEnum.EN_US
    
    def build_system_prompt(self) -> str:
        """Build the complete system prompt with persona and style instructions"""
        base_prompt = ""
        
        if self.persona:
            base_prompt = self.persona.system_prompt
            
            # Add specialized instructions
            if self.persona.specialized_instructions:
                base_prompt += f"\n\nSpecialized Instructions: {self.persona.specialized_instructions}"
        
        # Add style instructions
        tone = self.get_effective_tone()
        verbosity = self.get_effective_verbosity()
        language = self.get_effective_language()
        
        style_instructions = f"""

Style Guidelines:
- Tone: {tone.value}
- Verbosity: {verbosity.value}
- Language: {language.value}"""
        
        # Add formality and creativity levels
        if self.persona:
            formality = self.style_override.formality_level if (
                self.style_override and self.style_override.formality_level is not None
            ) else self.persona.formality_level
            
            creativity = self.style_override.creativity_level if (
                self.style_override and self.style_override.creativity_level is not None
            ) else self.persona.creativity_level
            
            style_instructions += f"""
- Formality Level: {formality:.1f}/1.0 (0=casual, 1=formal)
- Creativity Level: {creativity:.1f}/1.0 (0=conservative, 1=creative)"""
        
        # Add emoji usage
        use_emoji = False
        if self.style_override and self.style_override.use_emoji is not None:
            use_emoji = self.style_override.use_emoji
        elif self.persona:
            use_emoji = self.persona.use_emoji
        
        if use_emoji:
            style_instructions += "\n- Use appropriate emojis to enhance communication"
        else:
            style_instructions += "\n- Avoid using emojis"
        
        # Add turn-specific instructions
        if self.style_override and self.style_override.turn_instructions:
            style_instructions += f"\n\nSpecial Instructions for this response: {self.style_override.turn_instructions}"
        
        return base_prompt + style_instructions


class PersonaMemoryEntry(BaseModel):
    """Memory entry with persona and style context"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    
    # Persona context when memory was created
    persona_id: Optional[str] = None
    persona_name: Optional[str] = None
    tone_used: Optional[ToneEnum] = None
    verbosity_used: Optional[VerbosityEnum] = None
    
    # Standard memory fields
    user_id: str
    tenant_id: str
    conversation_id: Optional[str] = None
    
    # Memory metadata
    memory_type: str = "chat_interaction"
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None
    
    # Vector embedding (stored separately but referenced here)
    embedding_id: Optional[str] = None


# Built-in system personas
SYSTEM_PERSONAS = [
    Persona(
        id="support-assistant",
        name="Support Assistant",
        description="Helpful and patient support agent focused on problem-solving",
        system_prompt="You are a helpful support assistant. Your goal is to understand user problems clearly and provide step-by-step solutions. Be patient, thorough, and always ask clarifying questions when needed.",
        default_tone=ToneEnum.FRIENDLY,
        default_verbosity=VerbosityEnum.DETAILED,
        memory_weight=PersonaMemoryWeight.HIGH,
        domain_knowledge=["technical_support", "troubleshooting", "customer_service"],
        formality_level=0.6,
        is_system_persona=True
    ),
    Persona(
        id="technical-expert",
        name="Technical Expert",
        description="Knowledgeable technical advisor for development and engineering topics",
        system_prompt="You are a technical expert with deep knowledge across software development, engineering, and technology. Provide accurate, detailed technical information with code examples when appropriate. Focus on best practices and practical solutions.",
        default_tone=ToneEnum.TECHNICAL,
        default_verbosity=VerbosityEnum.COMPREHENSIVE,
        memory_weight=PersonaMemoryWeight.HIGH,
        domain_knowledge=["software_development", "engineering", "architecture", "devops"],
        formality_level=0.7,
        creativity_level=0.3,
        is_system_persona=True
    ),
    Persona(
        id="creative-collaborator",
        name="Creative Collaborator",
        description="Imaginative and inspiring assistant for creative projects and brainstorming",
        system_prompt="You are a creative collaborator who helps users explore ideas, brainstorm solutions, and think outside the box. Be enthusiastic, encouraging, and offer multiple creative perspectives on challenges.",
        default_tone=ToneEnum.FRIENDLY,
        default_verbosity=VerbosityEnum.BALANCED,
        memory_weight=PersonaMemoryWeight.MEDIUM,
        domain_knowledge=["creative_writing", "design", "brainstorming", "innovation"],
        formality_level=0.3,
        creativity_level=0.9,
        use_emoji=True,
        is_system_persona=True
    ),
    Persona(
        id="business-advisor",
        name="Business Advisor",
        description="Professional business consultant focused on strategy and growth",
        system_prompt="You are a professional business advisor with expertise in strategy, operations, and growth. Provide structured, actionable business advice with clear reasoning and consideration of risks and opportunities.",
        default_tone=ToneEnum.PROFESSIONAL,
        default_verbosity=VerbosityEnum.DETAILED,
        memory_weight=PersonaMemoryWeight.HIGH,
        domain_knowledge=["business_strategy", "operations", "finance", "marketing"],
        formality_level=0.8,
        creativity_level=0.4,
        is_system_persona=True
    ),
    Persona(
        id="casual-friend",
        name="Casual Friend",
        description="Relaxed and conversational assistant for everyday interactions",
        system_prompt="You are a friendly, casual conversational partner. Keep things light, relatable, and engaging. Use natural language and don't be overly formal. Be supportive and encouraging while maintaining a relaxed tone.",
        default_tone=ToneEnum.CASUAL,
        default_verbosity=VerbosityEnum.BALANCED,
        memory_weight=PersonaMemoryWeight.MEDIUM,
        domain_knowledge=["general_conversation", "lifestyle", "entertainment"],
        formality_level=0.2,
        creativity_level=0.6,
        use_emoji=True,
        is_system_persona=True
    )
]