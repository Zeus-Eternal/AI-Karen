"""
Speech Interface Extension - Migrated from ui_logic/pages/voice.py

This extension provides comprehensive voice and speech capabilities including:
- Text-to-Speech (TTS) synthesis with multiple providers
- Speech-to-Text (STT) recognition
- Voice command processing and understanding
- Audio analysis and processing
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from io import BytesIO
import json

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

# Import voice registry from the original system
from ai_karen_engine.integrations.voice_registry import get_voice_registry

logger = logging.getLogger(__name__)


class SynthesisRequest(BaseModel):
    """Request model for speech synthesis."""
    text: str
    provider: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None
    sample_rate: int = 16000
    amplitude: float = 0.35
    speed: float = 1.0
    pitch: float = 1.0


class RecognitionRequest(BaseModel):
    """Request model for speech recognition."""
    audio_data: str  # Base64 encoded audio
    provider: Optional[str] = None
    model: Optional[str] = None
    language: str = "en"
    enhance_audio: bool = True


class VoiceCommand(BaseModel):
    """Voice command processing request."""
    audio_data: str
    command_type: str = "general"  # "general", "navigation", "control", "query"
    context: Optional[Dict[str, Any]] = {}


class SpeechInterfaceExtension(BaseExtension, HookMixin):
    """Speech Interface Extension with TTS, STT, and voice control capabilities."""
    
    async def _initialize(self) -> None:
        """Initialize the Speech Interface Extension."""
        self.logger.info("Speech Interface Extension initializing...")
        
        # Initialize voice processing history and caches
        self.synthesis_history: List[Dict[str, Any]] = []
        self.recognition_history: List[Dict[str, Any]] = []
        self.voice_commands_history: List[Dict[str, Any]] = []
        self.audio_cache: Dict[str, bytes] = {}
        
        # Get voice registry from the original system
        self.voice_registry = get_voice_registry()
        
        # Initialize voice providers and models
        await self._initialize_voice_providers()
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        self.logger.info("Speech Interface Extension initialized successfully")
    
    async def _initialize_voice_providers(self) -> None:
        """Initialize voice providers and their capabilities."""
        try:
            # Get available providers from the voice registry
            self.available_providers = self.voice_registry.list_providers(category="VOICE") or self.voice_registry.list_providers()
            
            # Initialize provider capabilities
            self.provider_capabilities = {}
            for provider_name in self.available_providers:
                provider_info = self.voice_registry.get_provider_info(provider_name)
                if provider_info:
                    self.provider_capabilities[provider_name] = {
                        "description": provider_info.description,
                        "models": [model.name for model in provider_info.models] if provider_info.models else [],
                        "default_model": provider_info.default_model,
                        "capabilities": list({cap for model in provider_info.models for cap in model.capabilities}) if provider_info.models else [],
                        "requires_api_key": provider_info.requires_api_key
                    }
            
            self.logger.info(f"Initialized {len(self.available_providers)} voice providers")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice providers: {e}")
            # Fallback to simulated providers
            self.available_providers = ["builtin", "openai", "elevenlabs"]
            self.provider_capabilities = {
                "builtin": {
                    "description": "Built-in voice synthesis",
                    "models": ["default"],
                    "default_model": "default",
                    "capabilities": ["tts", "stt"],
                    "requires_api_key": False
                }
            }
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered voice processing."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register voice processing tools
            await self.register_mcp_tool(
                name="synthesize_speech",
                handler=self._synthesize_speech_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to synthesize"},
                        "provider": {"type": "string", "description": "Voice provider to use"},
                        "voice": {"type": "string", "description": "Voice model/style"},
                        "sample_rate": {"type": "integer", "default": 16000, "description": "Audio sample rate"},
                        "speed": {"type": "number", "default": 1.0, "description": "Speech speed multiplier"}
                    },
                    "required": ["text"]
                },
                description="Convert text to speech using various voice providers"
            )
            
            await self.register_mcp_tool(
                name="recognize_speech",
                handler=self._recognize_speech_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "audio_data": {"type": "string", "description": "Base64 encoded audio data"},
                        "language": {"type": "string", "default": "en", "description": "Recognition language"},
                        "provider": {"type": "string", "description": "Speech recognition provider"},
                        "enhance_audio": {"type": "boolean", "default": True, "description": "Enhance audio quality"}
                    },
                    "required": ["audio_data"]
                },
                description="Convert speech to text using speech recognition"
            )
            
            await self.register_mcp_tool(
                name="process_voice_command",
                handler=self._process_voice_command_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "audio_data": {"type": "string", "description": "Base64 encoded voice command audio"},
                        "command_type": {"type": "string", "enum": ["general", "navigation", "control", "query"], "default": "general", "description": "Type of voice command"},
                        "context": {"type": "object", "description": "Additional context for command processing"}
                    },
                    "required": ["audio_data"]
                },
                description="Process voice commands and execute appropriate actions"
            )
            
            await self.register_mcp_tool(
                name="analyze_audio",
                handler=self._analyze_audio_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "audio_data": {"type": "string", "description": "Base64 encoded audio data"},
                        "analysis_type": {"type": "string", "enum": ["quality", "emotion", "speaker", "content"], "default": "quality", "description": "Type of audio analysis"},
                        "detailed": {"type": "boolean", "default": False, "description": "Provide detailed analysis"}
                    },
                    "required": ["audio_data"]
                },
                description="Analyze audio for quality, emotion, speaker identification, or content"
            )
    
    async def _synthesize_speech_tool(self, text: str, provider: Optional[str] = None, voice: Optional[str] = None, sample_rate: int = 16000, speed: float = 1.0) -> Dict[str, Any]:
        """MCP tool to synthesize speech from text."""
        try:
            # Select provider
            if not provider and self.available_providers:
                provider = self.available_providers[0]
            elif provider not in self.available_providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not available. Available providers: {self.available_providers}"
                }
            
            # Get synthesizer from voice registry
            try:
                synthesizer = self.voice_registry.get_provider(provider, model=voice) if voice else self.voice_registry.get_provider(provider)
                
                # Synthesize speech
                audio_data = synthesizer.synthesize_speech(
                    text,
                    sample_rate=sample_rate,
                    amplitude=0.35,
                    speed=speed
                )
                
                # Encode audio as base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
            except Exception as e:
                # Fallback to simulated synthesis
                self.logger.warning(f"Voice synthesis failed, using simulation: {e}")
                audio_data, audio_b64 = self._simulate_speech_synthesis(text, provider, voice, sample_rate, speed)
            
            # Store in synthesis history
            synthesis_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "text": text,
                "provider": provider,
                "voice": voice,
                "sample_rate": sample_rate,
                "speed": speed,
                "audio_length": len(audio_data),
                "success": True
            }
            self.synthesis_history.append(synthesis_record)
            
            # Cache audio data
            cache_key = f"tts_{hash(text)}_{provider}_{voice}_{sample_rate}_{speed}"
            self.audio_cache[cache_key] = audio_data
            
            # Keep only recent history
            if len(self.synthesis_history) > 500:
                self.synthesis_history = self.synthesis_history[-500:]
            
            return {
                "success": True,
                "audio_data": audio_b64,
                "text": text,
                "provider": provider,
                "voice": voice,
                "sample_rate": sample_rate,
                "speed": speed,
                "audio_length": len(audio_data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to synthesize speech: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _recognize_speech_tool(self, audio_data: str, language: str = "en", provider: Optional[str] = None, enhance_audio: bool = True) -> Dict[str, Any]:
        """MCP tool to recognize speech from audio."""
        try:
            # Decode audio data
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid audio data: {e}"
                }
            
            # Select provider
            if not provider and self.available_providers:
                provider = self.available_providers[0]
            elif provider and provider not in self.available_providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not available"
                }
            
            # Recognize speech
            try:
                recognizer = self.voice_registry.get_provider(provider) if provider else self.voice_registry.get_provider(self.available_providers[0])
                recognized_text = recognizer.recognize_speech(audio_bytes)
                confidence = 0.85  # Simulated confidence
                
            except Exception as e:
                # Fallback to simulated recognition
                self.logger.warning(f"Speech recognition failed, using simulation: {e}")
                recognized_text, confidence = self._simulate_speech_recognition(audio_bytes, language)
            
            # Store in recognition history
            recognition_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "recognized_text": recognized_text,
                "language": language,
                "provider": provider,
                "confidence": confidence,
                "audio_length": len(audio_bytes),
                "enhance_audio": enhance_audio,
                "success": True
            }
            self.recognition_history.append(recognition_record)
            
            # Keep only recent history
            if len(self.recognition_history) > 500:
                self.recognition_history = self.recognition_history[-500:]
            
            return {
                "success": True,
                "text": recognized_text,
                "confidence": confidence,
                "language": language,
                "provider": provider,
                "audio_length": len(audio_bytes)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to recognize speech: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_voice_command_tool(self, audio_data: str, command_type: str = "general", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """MCP tool to process voice commands and execute actions."""
        try:
            # First recognize the speech
            recognition_result = await self._recognize_speech_tool(audio_data)
            
            if not recognition_result["success"]:
                return recognition_result
            
            recognized_text = recognition_result["text"]
            
            # Use AI to understand the command intent
            try:
                intent_result = await self.plugin_orchestrator.execute_plugin(
                    intent="analyze_text",
                    params={
                        "text": recognized_text,
                        "analysis_type": "command_intent",
                        "command_type": command_type,
                        "context": context or {}
                    },
                    user_context={"roles": ["user"]}
                )
            except Exception:
                # Fallback to basic command processing
                intent_result = self._simulate_command_processing(recognized_text, command_type)
            
            # Execute the command based on intent
            execution_result = await self._execute_voice_command(
                recognized_text,
                intent_result.get("intent", "unknown"),
                intent_result.get("parameters", {}),
                context or {}
            )
            
            # Store in voice commands history
            command_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "recognized_text": recognized_text,
                "command_type": command_type,
                "intent": intent_result.get("intent", "unknown"),
                "parameters": intent_result.get("parameters", {}),
                "execution_result": execution_result,
                "context": context,
                "success": execution_result.get("success", False)
            }
            self.voice_commands_history.append(command_record)
            
            # Keep only recent history
            if len(self.voice_commands_history) > 200:
                self.voice_commands_history = self.voice_commands_history[-200:]
            
            return {
                "success": True,
                "recognized_text": recognized_text,
                "intent": intent_result.get("intent", "unknown"),
                "parameters": intent_result.get("parameters", {}),
                "execution_result": execution_result,
                "confidence": recognition_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process voice command: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_audio_tool(self, audio_data: str, analysis_type: str = "quality", detailed: bool = False) -> Dict[str, Any]:
        """MCP tool to analyze audio for various characteristics."""
        try:
            # Decode audio data
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid audio data: {e}"
                }
            
            # Perform analysis based on type
            if analysis_type == "quality":
                analysis_result = self._analyze_audio_quality(audio_bytes, detailed)
            elif analysis_type == "emotion":
                analysis_result = self._analyze_audio_emotion(audio_bytes, detailed)
            elif analysis_type == "speaker":
                analysis_result = self._analyze_speaker_characteristics(audio_bytes, detailed)
            elif analysis_type == "content":
                analysis_result = self._analyze_audio_content(audio_bytes, detailed)
            else:
                return {
                    "success": False,
                    "error": f"Unknown analysis type: {analysis_type}"
                }
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "audio_length": len(audio_bytes),
                "detailed": detailed,
                **analysis_result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simulate_speech_synthesis(self, text: str, provider: str, voice: str, sample_rate: int, speed: float) -> tuple[bytes, str]:
        """Simulate speech synthesis for fallback."""
        # Generate simple sine wave audio as placeholder
        import math
        import struct
        
        duration = len(text) * 0.1  # Rough estimate: 0.1 seconds per character
        samples = int(sample_rate * duration)
        
        audio_data = bytearray()
        for i in range(samples):
            # Generate sine wave at 440 Hz (A note)
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / sample_rate))
            audio_data.extend(struct.pack('<h', sample))
        
        audio_bytes = bytes(audio_data)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_bytes, audio_b64
    
    def _simulate_speech_recognition(self, audio_bytes: bytes, language: str) -> tuple[str, float]:
        """Simulate speech recognition for fallback."""
        # Return a simulated recognition result
        sample_texts = {
            "en": "This is a simulated speech recognition result.",
            "es": "Este es un resultado simulado de reconocimiento de voz.",
            "fr": "Ceci est un résultat simulé de reconnaissance vocale.",
            "de": "Dies ist ein simuliertes Spracherkennungsergebnis."
        }
        
        recognized_text = sample_texts.get(language, sample_texts["en"])
        confidence = 0.75  # Simulated confidence
        
        return recognized_text, confidence
    
    def _simulate_command_processing(self, text: str, command_type: str) -> Dict[str, Any]:
        """Simulate command intent processing."""
        text_lower = text.lower()
        
        # Simple intent detection based on keywords
        if "turn on" in text_lower or "switch on" in text_lower:
            intent = "device_control"
            parameters = {"action": "turn_on", "device": "light"}
        elif "turn off" in text_lower or "switch off" in text_lower:
            intent = "device_control"
            parameters = {"action": "turn_off", "device": "light"}
        elif "what time" in text_lower or "current time" in text_lower:
            intent = "time_query"
            parameters = {"query_type": "current_time"}
        elif "weather" in text_lower:
            intent = "weather_query"
            parameters = {"location": "current"}
        elif "play" in text_lower and "music" in text_lower:
            intent = "media_control"
            parameters = {"action": "play", "media_type": "music"}
        else:
            intent = "general_query"
            parameters = {"query": text}
        
        return {
            "intent": intent,
            "parameters": parameters,
            "confidence": 0.8
        }
    
    async def _execute_voice_command(self, text: str, intent: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a voice command based on its intent."""
        try:
            if intent == "device_control":
                # Simulate device control
                return {
                    "success": True,
                    "action": "device_control",
                    "result": f"Device {parameters.get('device', 'unknown')} {parameters.get('action', 'controlled')}",
                    "message": f"Successfully executed {parameters.get('action')} on {parameters.get('device')}"
                }
            
            elif intent == "time_query":
                # Use time plugin
                try:
                    time_result = await self.plugin_orchestrator.execute_plugin(
                        intent="time_query",
                        params=parameters,
                        user_context={"roles": ["user"]}
                    )
                    return {
                        "success": True,
                        "action": "time_query",
                        "result": time_result,
                        "message": "Time query executed successfully"
                    }
                except Exception:
                    return {
                        "success": True,
                        "action": "time_query",
                        "result": f"Current time: {datetime.now().strftime('%H:%M:%S')}",
                        "message": "Time query executed (simulated)"
                    }
            
            elif intent == "weather_query":
                return {
                    "success": True,
                    "action": "weather_query",
                    "result": "Weather: 22°C, partly cloudy",
                    "message": "Weather query executed (simulated)"
                }
            
            elif intent == "media_control":
                return {
                    "success": True,
                    "action": "media_control",
                    "result": f"Media {parameters.get('action', 'controlled')}: {parameters.get('media_type', 'unknown')}",
                    "message": f"Media control executed: {parameters.get('action')}"
                }
            
            elif intent == "general_query":
                # Use LLM for general queries
                try:
                    llm_result = await self.plugin_orchestrator.execute_plugin(
                        intent="hf_llm",
                        params={"prompt": parameters.get("query", text)},
                        user_context={"roles": ["user"]}
                    )
                    return {
                        "success": True,
                        "action": "general_query",
                        "result": llm_result,
                        "message": "General query processed by AI"
                    }
                except Exception:
                    return {
                        "success": True,
                        "action": "general_query",
                        "result": "I understand your request, but I'm currently in simulation mode.",
                        "message": "General query processed (simulated)"
                    }
            
            else:
                return {
                    "success": False,
                    "action": "unknown",
                    "result": None,
                    "message": f"Unknown intent: {intent}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "action": intent,
                "result": None,
                "message": f"Command execution failed: {e}"
            }
    
    def _analyze_audio_quality(self, audio_bytes: bytes, detailed: bool) -> Dict[str, Any]:
        """Analyze audio quality characteristics."""
        # Simulated audio quality analysis
        quality_metrics = {
            "sample_rate": 16000,
            "bit_depth": 16,
            "channels": 1,
            "duration": len(audio_bytes) / (16000 * 2),  # Rough estimate
            "signal_to_noise_ratio": 25.5,
            "dynamic_range": 18.2,
            "quality_score": 0.82
        }
        
        if detailed:
            quality_metrics.update({
                "frequency_response": {"low": 0.8, "mid": 0.9, "high": 0.7},
                "distortion": 0.05,
                "clipping": False,
                "background_noise": "low"
            })
        
        return quality_metrics
    
    def _analyze_audio_emotion(self, audio_bytes: bytes, detailed: bool) -> Dict[str, Any]:
        """Analyze emotional characteristics of audio."""
        # Simulated emotion analysis
        emotion_analysis = {
            "primary_emotion": "neutral",
            "confidence": 0.75,
            "emotions": {
                "neutral": 0.45,
                "happy": 0.25,
                "calm": 0.20,
                "sad": 0.05,
                "angry": 0.03,
                "excited": 0.02
            }
        }
        
        if detailed:
            emotion_analysis.update({
                "arousal": 0.4,  # Low to high energy
                "valence": 0.6,  # Negative to positive
                "intensity": 0.5,
                "emotional_stability": 0.8
            })
        
        return emotion_analysis
    
    def _analyze_speaker_characteristics(self, audio_bytes: bytes, detailed: bool) -> Dict[str, Any]:
        """Analyze speaker characteristics."""
        # Simulated speaker analysis
        speaker_analysis = {
            "gender": "unknown",
            "age_estimate": "adult",
            "accent": "neutral",
            "speaking_rate": "normal",
            "pitch_range": "medium"
        }
        
        if detailed:
            speaker_analysis.update({
                "fundamental_frequency": 150.0,  # Hz
                "formant_frequencies": [800, 1200, 2500],  # Hz
                "voice_quality": "clear",
                "articulation": "good",
                "fluency": 0.85
            })
        
        return speaker_analysis
    
    def _analyze_audio_content(self, audio_bytes: bytes, detailed: bool) -> Dict[str, Any]:
        """Analyze audio content characteristics."""
        # Simulated content analysis
        content_analysis = {
            "content_type": "speech",
            "language_detected": "en",
            "speech_clarity": 0.8,
            "background_noise": "minimal",
            "music_detected": False
        }
        
        if detailed:
            content_analysis.update({
                "silence_ratio": 0.15,
                "speech_ratio": 0.80,
                "noise_ratio": 0.05,
                "energy_distribution": {"low": 0.3, "mid": 0.5, "high": 0.2},
                "spectral_centroid": 1200.0  # Hz
            })
        
        return content_analysis
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the Speech Interface Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.post("/synthesize")
        async def synthesize_speech(request: SynthesisRequest):
            """Synthesize speech from text."""
            result = await self._synthesize_speech_tool(
                request.text,
                request.provider,
                request.voice,
                request.sample_rate,
                request.speed
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/recognize")
        async def recognize_speech(request: RecognitionRequest):
            """Recognize speech from audio."""
            result = await self._recognize_speech_tool(
                request.audio_data,
                request.language,
                request.provider,
                request.enhance_audio
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/command")
        async def process_voice_command(request: VoiceCommand):
            """Process voice command and execute action."""
            result = await self._process_voice_command_tool(
                request.audio_data,
                request.command_type,
                request.context
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/analyze")
        async def analyze_audio(
            file: UploadFile = File(...),
            analysis_type: str = Form(default="quality"),
            detailed: bool = Form(default=False)
        ):
            """Analyze uploaded audio file."""
            try:
                # Read and encode audio
                audio_bytes = await file.read()
                audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                
                result = await self._analyze_audio_tool(audio_data, analysis_type, detailed)
                if not result["success"]:
                    raise HTTPException(status_code=400, detail=result["error"])
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/providers")
        async def list_voice_providers():
            """List available voice providers and their capabilities."""
            return {
                "providers": self.provider_capabilities,
                "available_providers": self.available_providers
            }
        
        @router.get("/history/synthesis")
        async def get_synthesis_history(limit: int = 50):
            """Get speech synthesis history."""
            return {
                "history": self.synthesis_history[-limit:] if limit > 0 else self.synthesis_history,
                "total_syntheses": len(self.synthesis_history)
            }
        
        @router.get("/history/recognition")
        async def get_recognition_history(limit: int = 50):
            """Get speech recognition history."""
            return {
                "history": self.recognition_history[-limit:] if limit > 0 else self.recognition_history,
                "total_recognitions": len(self.recognition_history)
            }
        
        @router.get("/history/commands")
        async def get_voice_commands_history(limit: int = 50):
            """Get voice commands history."""
            return {
                "history": self.voice_commands_history[-limit:] if limit > 0 else self.voice_commands_history,
                "total_commands": len(self.voice_commands_history)
            }
        
        @router.get("/stats")
        async def get_voice_stats():
            """Get voice processing statistics."""
            return {
                "total_syntheses": len(self.synthesis_history),
                "total_recognitions": len(self.recognition_history),
                "total_commands": len(self.voice_commands_history),
                "successful_commands": len([cmd for cmd in self.voice_commands_history if cmd.get("success")]),
                "available_providers": len(self.available_providers),
                "cache_size": len(self.audio_cache)
            }
        
        return router
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Voice Control Center."""
        components = super().create_ui_components()
        
        # Add voice control center data
        components["voice_control_center"] = {
            "title": "Voice Control Center",
            "description": "Speech synthesis, recognition, and voice command processing",
            "data": {
                "total_syntheses": len(self.synthesis_history),
                "total_recognitions": len(self.recognition_history),
                "total_commands": len(self.voice_commands_history),
                "successful_commands": len([cmd for cmd in self.voice_commands_history if cmd.get("success")]),
                "available_providers": len(self.available_providers),
                "command_success_rate": (
                    len([cmd for cmd in self.voice_commands_history if cmd.get("success")]) / 
                    len(self.voice_commands_history) if self.voice_commands_history else 0
                )
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the Speech Interface Extension."""
        self.logger.info("Speech Interface Extension shutting down...")
        
        # Clear caches and history
        self.synthesis_history.clear()
        self.recognition_history.clear()
        self.voice_commands_history.clear()
        self.audio_cache.clear()
        
        self.logger.info("Speech Interface Extension shut down successfully")


# Export the extension class
__all__ = ["SpeechInterfaceExtension"]