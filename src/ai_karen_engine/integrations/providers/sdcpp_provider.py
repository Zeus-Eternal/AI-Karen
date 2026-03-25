"""
Stable Diffusion CPP Provider
Local low-VRAM edge-optimized image generation.
"""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Dict, List, Optional
from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, record_llm_metric

try:
    from stable_diffusion_cpp import StableDiffusion
    SDCPP_AVAILABLE = True
except ImportError:
    SDCPP_AVAILABLE = False
    StableDiffusion = Any

logger = logging.getLogger(__name__)

class SDCPPProvider(LLMProviderBase):
    """Provides ultra-fast local image inference via stable-diffusion.cpp."""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
            
        self.provider_name = "sdcpp"
        self.model_path = config.get("model_path", "models/stable-diffusion/v1-5-pruned-emaonly.safetensors")
        self.vae_path = config.get("vae_path", "")
        self.threads = config.get("threads", 4)
        
        # Lazy load pipeline
        self._pipeline: Optional['StableDiffusion'] = None

    def _initialize_pipeline(self):
        """Lazy load the native C++ pipeline into memory."""
        if not SDCPP_AVAILABLE:
            raise GenerationFailed("stable-diffusion-cpp-python is not installed. Run `pip install stable-diffusion-cpp-python`")
            
        if self._pipeline is None:
            logger.info(f"Loading sdcpp model from {self.model_path}...")
            self._pipeline = StableDiffusion(
                model_path=self.model_path,
                vae_path=self.vae_path,
                n_threads=self.threads,
                # wtype="f16"  # Optional quantization casting
            )
            logger.info("sdcpp pipeline loaded successfully.")

    def generate_image(self, prompt: str, negative_prompt: str = "", width: int = 512, height: int = 512, num_inference_steps: int = 20, guidance_scale: float = 7.5, **kwargs) -> Dict[str, Any]:
        """Generate image synchronously (will be offloaded by caller if needed)."""
        self._initialize_pipeline()
        
        t0 = time.time()
        try:
            # sd.cpp native sample generation
            images = self._pipeline.txt2img(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                sample_steps=num_inference_steps,
                cfg_scale=guidance_scale,
                seed=kwargs.get("seed", -1)
            )
            
            # sd.cpp returns a list of PIL Images
            images_b64 = []
            for img in images:
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                images_b64.append(base64.b64encode(buffer.getvalue()).decode())
                
            gen_time = time.time() - t0
            record_llm_metric("generate_image", gen_time, True, "sdcpp")
            
            return {
                "images": images_b64,
                "prompt": prompt,
                "generation_time": gen_time,
                "parameters": {
                    "width": width, "height": height, "steps": num_inference_steps, "cfg": guidance_scale
                }
            }
        except Exception as e:
            record_llm_metric("generate_image", time.time() - t0, False, "sdcpp", error=str(e))
            raise GenerationFailed(f"SDCPP failed: {e}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        raise GenerationFailed("Text generation not supported.")

    def generate_img2img(self, prompt: str, image: Any, **kwargs) -> Dict[str, Any]:
        """Image to image logic goes here"""
        raise NotImplementedError("Img2Img to be mapped for SDCPP")

    def embed(self, text: Any, **kwargs) -> List[float]:
        raise GenerationFailed("Embeddings not supported.")

    def get_available_models(self) -> List[str]:
        return [self.model_path]

    def is_available(self) -> bool:
        return SDCPP_AVAILABLE

    async def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "available": self.is_available(),
            "pipeline_loaded": self._pipeline is not None
        }
