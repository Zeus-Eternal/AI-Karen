"""LLMUtils
Local-first HuggingFace text-generation wrapper with auto-download,
resume support, robust fallback, and NLP toolkit diagnostics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LLMUtils:
    """Self-healing text-generation helper that prefers local cache."""

    # ──────────────────────────────────────────────────────────
    # INITIALISATION
    # ──────────────────────────────────────────────────────────
    def __init__(self, model_name: str = "distilgpt2", cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self.cache_dir = Path(cache_dir or Path.home() / ".cache" / "hf_models" / model_name)
        self._counter: int = 0
        self._error: Optional[Exception] = None
        self.generator = None  # set in _init_pipeline
        self._init_pipeline()

    # ──────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────
    def _init_pipeline(self) -> None:
        """Download (or resume) model, then build a text-generation pipeline."""
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # type: ignore
            from huggingface_hub import snapshot_download  # type: ignore

            logger.info("Attempting local-first load for model '%s'.", self.model_name)

            # Try to ensure files exist locally; if not, auto-download.
            snapshot_download(
                repo_id=self.model_name,
                local_dir=str(self.cache_dir),
                resume_download=True,
                local_dir_use_symlinks=False,  # modern hub behaviour
                local_files_only=False,        # allow remote fetch if missing
            )
            model_path = str(self.cache_dir)

            # Build pipeline
            self.generator = pipeline(
                task="text-generation",
                model=AutoModelForCausalLM.from_pretrained(model_path),
                tokenizer=AutoTokenizer.from_pretrained(model_path),
                device=0 if self._cuda_available() else -1,
                cache_dir=model_path,
            )
            logger.info("LLM pipeline ready: %s", self.model_name)

        except Exception as exc:  # noqa: BLE001
            self._error = exc
            logger.warning(
                "LLM backend unavailable (fallback mode). "
                "Install compatible PyTorch / Transformers. Error: %s",
                exc,
            )

    @staticmethod
    def _cuda_available() -> bool:
        """Return True if CUDA is available and torch is importable."""
        try:
            import torch  # noqa: WPS433
            return torch.cuda.is_available()
        except Exception:  # noqa: BLE001
            return False

    # ──────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────
    def generate_text(self, prompt: str, max_tokens: int = 128, temperature: float | None = None, **kwargs: Any) -> str:
        """
        Generate text with safe kwarg filtering. Falls back to echo if pipeline unavailable.

        Parameters
        ----------
        prompt : str
            The prompt to complete.
        max_tokens : int, default=128
            Maximum new tokens to generate.
        temperature : float | None
            Sampling temperature; if None or 0, deterministic.
        kwargs : Any
            Additional generation kwargs (top_k, top_p, etc.)—validated internally.
        """
        if self.generator:
            safe_args: Dict[str, Any] = {
                "max_new_tokens": max_tokens,
                "do_sample": bool(temperature) and temperature > 0,
            }
            if temperature:
                safe_args["temperature"] = temperature

            allowed_keys = {
                "top_k", "top_p", "repetition_penalty", "num_beams", "no_repeat_ngram_size"
            }
            safe_args.update({k: v for k, v in kwargs.items() if k in allowed_keys})

            try:
                outputs = self.generator(prompt, **safe_args)
                return outputs[0]["generated_text"]
            except Exception as err:  # noqa: BLE001
                logger.error("Pipeline error: %s. Fallback engaged.", err)

        # ── Fallback echo response
        self._counter += 1
        return f"[FALLBACK] {prompt} (attempt {self._counter})"

    # ──────────────────────────────────────────────────────────
    # TOOLKIT CHECKS
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def ensure_spacy_model(model: str = "en_core_web_sm") -> bool:
        """Guarantee spaCy model availability."""
        try:
            import spacy  # noqa: WPS433
            spacy.load(model)
            return True
        except OSError:
            try:
                from spacy.cli import download  # noqa: WPS433
                download(model)
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to download spaCy model '%s': %s", model, exc)
        except ImportError:
            logger.warning("SpaCy not installed.")
        return False

    @staticmethod
    def ensure_sklearn_available() -> bool:
        """Check that scikit-learn is importable."""
        try:
            import sklearn  # noqa: WPS433
            return True
        except ImportError:
            logger.warning("scikit-learn not installed.")
            return False

    # ──────────────────────────────────────────────────────────
    # DIAGNOSTICS
    # ──────────────────────────────────────────────────────────
    def diagnostics(self) -> dict[str, Any]:
        """Return component health snapshot."""
        return {
            "model_loaded": self.generator is not None,
            "model_name": self.model_name,
            "spacy_model_ready": self.ensure_spacy_model(),
            "scikit_learn_ready": self.ensure_sklearn_available(),
            "cuda": self._cuda_available(),
            "last_error": str(self._error) if self._error else None,
        }
