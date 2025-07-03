#!/usr/bin/env python3
"""
Production-Grade Chat Interface

Features:
- Async message processing with proper event loop handling
- Response streaming
- Rate limiting and input validation
- Comprehensive error handling
- Performance telemetry
- Session management
- Memory synchronization
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

MAX_TOKENS = 4000
RATE_LIMIT_WINDOW = 60
REQUEST_TIMEOUT = 300

class ChatManager:
    """Orchestrates chat operations with safety controls"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.last_request_time = 0

    def _check_rate_limit(self) -> bool:
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.0:
            st.warning("Please wait before sending another message")
            return False
        return True
      
    def _validate_input(self, text: str) -> bool:
        if not text or not text.strip():
            st.warning("Message cannot be empty")
            return False
        if len(text) > 2000:
            st.warning("Message too long (max 2000 chars)")
            return False
        return True

    async def _stream_response(self, generator, placeholder):
        full_response = ""
        async for chunk in generator:
            full_response += chunk
            placeholder.markdown(full_response + "▌")
        return full_response

    def _run_async_safe(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.create_task(coro)
        return asyncio.run(coro)

class ChatUI:
    """Handles all UI rendering with error boundaries"""

    @staticmethod
    def initialize_session():
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "model_info" not in st.session_state:
            st.session_state.model_info = {}

    @staticmethod
    def render_model_selector(models: List[str], current_model: str) -> Optional[str]:
        try:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected = st.selectbox(
                    "Active Model",
                    models,
                    index=models.index(current_model) if current_model in models else 0,
                    key="model_select",
                    help="Select which model to chat with"
                )
            with col2:
                st.metric("Available Models", len(models))
            return selected
        except Exception as e:
            logger.error(f"Model selector failed: {e}")
            st.error("Could not load model selector")
            return None

    @staticmethod
    def render_chat_history():
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    @staticmethod
    def render_performance_metrics(duration: float, tokens: int):
        with st.expander("⚙️ Technical Details", expanded=False):
            cols = st.columns(3)
            cols[0].metric("Response Time", f"{duration:.2f}s")
            cols[1].metric("Tokens Generated", tokens)
            cols[2].metric("Model", st.session_state.model_info.get("name", "Unknown"))
            st.caption(
                f"Provider: {st.session_state.model_info.get('provider')} | "
                f"Runtime: {st.session_state.model_info.get('runtime')}"
            )

    @staticmethod
    def render_memory_controls():
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🧠 Recall Memory", help="Restore conversation context"):
                try:
                    from src.services.memory_controller import restore_memory
                    restore_memory()
                    st.toast("Memory restored from database")
                except Exception as e:
                    logger.error(f"Memory restore failed: {e}")
                    st.error("Memory restore failed")
        with col2:
            if st.button("📝 Show Logs", help="View system logs"):
                try:
                    from utils.api_client import get
                    logs = asyncio.run(get("/logs"))
                    if logs and not logs.get("error"):
                        st.expander("System Logs").code("\n".join(logs.get("logs", [])))
                    else:
                        st.warning("No logs available")
                except Exception as e:
                    logger.error(f"Log retrieval failed: {e}")
                    st.error("Couldn't load logs")

async def render_chat_page() -> None:
    try:
        ui = ChatUI()
        chat_mgr = ChatManager()
        ui.initialize_session()

        st.title("💬 AI Chat")
        st.markdown("---")

        try:
            from src.services.model_registry import get_ready_models, get_model_meta
            from src.services.config_manager import load_config, update_config
            from src.services.runtime_dispatcher import dispatch_runtime

            models = [m.get("model_name") for m in get_ready_models()]
            config = load_config()
            active_name = config.get("model", models[0] if models else None)
        except Exception as e:
            logger.critical(f"Initialization failed: {e}")
            st.error("System initialization error")
            return

        selected_model = ui.render_model_selector(models, active_name)
        if not selected_model:
            return
        if selected_model != active_name:
            update_config(model=selected_model)
            st.session_state.model_info = get_model_meta(selected_model) or {}
            st.rerun()

        ui.render_chat_history()
        ui.render_memory_controls()

        prompt = st.chat_input("Message AI...")
        if prompt and chat_mgr._validate_input(prompt):
            if not chat_mgr._check_rate_limit():
                return
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            start_time = time.perf_counter()
            try:
                with st.spinner("Generating response..."):
                    with st.chat_message("ai"):
                        response_placeholder = st.empty()
                    response_gen = dispatch_runtime(
                        st.session_state.model_info,
                        prompt
                    )
                    full_response = await chat_mgr._stream_response(response_gen, response_placeholder)
                    duration = time.perf_counter() - start_time
                    token_count = len(full_response.split())
                    st.session_state.chat_history.append({"role": "ai", "content": full_response})
                    from src.services.memory_controller import sync_memory
                    sync_memory()
                    ui.render_performance_metrics(duration, token_count)
            except Exception as e:
                logger.error(f"Runtime error: {e}")
                st.error(f"Generation failed: {str(e)}")
                st.session_state.chat_history.append({"role": "ai", "content": f"Error: {str(e)}"})
            chat_mgr.last_request_time = time.time()
    except Exception as e:
        logger.critical(f"Chat page crashed: {e}")
        st.error("The chat interface encountered a critical error")
        st.code(traceback.format_exc())

def render_chat() -> None:
    asyncio.run(render_chat_page())


if __name__ == "__main__":
    render_chat()
