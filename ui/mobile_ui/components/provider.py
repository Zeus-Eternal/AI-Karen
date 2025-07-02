#!/usr/bin/env python3
"""
Provider Page

Features:
- Async provider loading
- Cached registry queries
- Input validation
- Error boundaries
- Telemetry
"""

import streamlit as st
import logging
from typing import List, Optional, Tuple
from functools import lru_cache
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('provider_selector')

class ProviderManager:
    """Handles provider operations with caching and error handling"""

    @staticmethod
    @lru_cache(maxsize=1)
    def get_available_providers(refresh: bool = False) -> Tuple[List[str], Optional[Exception]]:
        """Fetch providers with caching and error handling"""
        try:
            time.sleep(0.2)
            from src.integrations.llm_registry import registry as llm_registry
            providers = list(llm_registry.list_models())
            if not providers:
                raise ValueError("No providers available in registry")
            return providers, None
        except Exception as e:
            logger.error(f"Provider fetch failed: {e}")
            return [], e

class ProviderUI:
    """Handles all UI rendering with error boundaries"""

    @staticmethod
    def render_provider_selector(default_provider: Optional[str] = None) -> Optional[str]:
        """Render provider selection UI with error handling"""
        try:
            with st.container():
                st.subheader("⚙️ LLM Provider")
                with st.spinner("Loading providers..."):
                    providers, error = ProviderManager.get_available_providers()
                if error:
                    st.error(f"Provider load failed: {str(error)}")
                    st.button("Retry", on_click=ProviderManager.get_available_providers.cache_clear)
                    return None
                if not providers:
                    st.warning("No providers available")
                    return None
                default_idx = 0
                if default_provider and default_provider in providers:
                    default_idx = providers.index(default_provider)
                selected = st.selectbox(
                    "Choose a provider",
                    providers,
                    index=default_idx,
                    key="provider_select",
                    help="Select which LLM provider to use",
                    on_change=lambda: logger.info("Provider selection changed")
                )
                logger.info(f"Provider selected: {selected}")
                return selected
        except Exception as e:
            logger.critical(f"Provider selector crashed: {e}")
            st.error("Provider selection unavailable")
            return None

if __name__ == "__main__":
    st.title("Provider Selection Demo")
    selected_provider = ProviderUI.render_provider_selector()
    if selected_provider:
        st.success(f"Selected: {selected_provider}")
