
import asyncio
import logging
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.core.langgraph_orchestrator import (
    get_default_orchestrator,
    LangGraphOrchestrationConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_chat_response():
    """Test that the orchestrator can produce a chat response"""
    logger.info("=== Testing LangGraph Chat Response ===")
    
    try:
        orchestrator = get_default_orchestrator()
        
        # Simple message
        messages = [HumanMessage(content="Hello Karen, are you working correctly?")]
        user_id = "test_user"
        session_id = "test_session_123"
        
        logger.info(f"Processing message: {messages[0].content}")
        
        # Process the message
        result = await orchestrator.process(
            messages=messages,
            user_id=user_id,
            session_id=session_id
        )
        
        # Extract response
        response = result.get("response")
        logger.info(f"Received response: {response}")
        
        if not response:
            logger.error("No response received from orchestrator")
            return False
            
        if "degraded mode" in response.lower():
            logger.warning("Received response in degraded mode. This might be expected if no LLM provider is available.")
        
        logger.info("✓ Chat response test successful")
        return True
        
    except Exception as e:
        logger.error(f"Chat response test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_response())
    sys.exit(0 if success else 1)
