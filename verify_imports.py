
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath("src"))

async def test_imports():
    try:
        from ai_karen_engine.chat.ChatOrchestrator.mixins.llm_mixin import ChatLLMMixin
        from ai_karen_engine.chat.ChatOrchestrator.mixins.prompt_mixin import ChatPromptMixin
        from ai_karen_engine.chat.ChatOrchestrator.models import ProcessingContext, ChatRequest
        print("Imports successful")
        
        # Test class instantiation (partial)
        class MockOrchestrator(ChatLLMMixin, ChatPromptMixin):
            def __init__(self):
                self.fallback_router = MagicMock()
                self.auth_service = MagicMock()
        
        orch = MockOrchestrator()
        print("Instantiation successful")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_imports())
