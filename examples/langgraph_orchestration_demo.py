"""
LangGraph Orchestration Demo

This example demonstrates the LangGraph orchestration foundation
with various conversation scenarios and streaming capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

from langchain_core.messages import HumanMessage

# Import orchestration components
from src.ai_karen_engine.core.langgraph_orchestrator import (
    LangGraphOrchestrator,
    OrchestrationConfig,
    create_orchestrator
)
from src.ai_karen_engine.core.streaming_integration import (
    StreamingManager,
    get_streaming_manager
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_conversation():
    """Demonstrate basic conversation processing"""
    print("\n" + "="*60)
    print("DEMO: Basic Conversation Processing")
    print("="*60)
    
    # Create orchestrator
    config = OrchestrationConfig(
        enable_auth_gate=True,
        enable_safety_gate=True,
        enable_memory_fetch=True,
        enable_approval_gate=False,
        streaming_enabled=False
    )
    orchestrator = create_orchestrator(config)
    
    # Test conversation
    messages = [HumanMessage(content="Hello! Can you help me understand Python functions?")]
    user_id = "demo_user"
    session_id = "demo_session_1"
    
    print(f"User: {messages[0].content}")
    print("Processing through orchestration graph...")
    
    start_time = datetime.now()
    result = await orchestrator.process(messages, user_id, session_id)
    processing_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print(f"Auth Status: {result.get('auth_status')}")
    print(f"Safety Status: {result.get('safety_status')}")
    print(f"Detected Intent: {result.get('detected_intent')} (confidence: {result.get('intent_confidence', 0):.2f})")
    print(f"Selected Provider: {result.get('selected_provider')}")
    print(f"Selected Model: {result.get('selected_model')}")
    print(f"Routing Reason: {result.get('routing_reason')}")
    
    if result.get('response'):
        print(f"\nAI Response: {result['response']}")
    
    if result.get('errors'):
        print(f"\nErrors: {result['errors']}")
    
    return result


async def demo_code_generation():
    """Demonstrate code generation scenario"""
    print("\n" + "="*60)
    print("DEMO: Code Generation Scenario")
    print("="*60)
    
    orchestrator = create_orchestrator()
    
    messages = [HumanMessage(content="Write a Python function to calculate the factorial of a number")]
    user_id = "developer_user"
    session_id = "code_session"
    
    print(f"User: {messages[0].content}")
    print("Processing code generation request...")
    
    result = await orchestrator.process(messages, user_id, session_id)
    
    print(f"\nDetected Intent: {result.get('detected_intent')}")
    print(f"Execution Plan: {json.dumps(result.get('execution_plan', {}), indent=2)}")
    print(f"Selected Provider: {result.get('selected_provider')}")
    print(f"Tools Used: {len(result.get('tool_results', []))}")
    
    if result.get('response'):
        print(f"\nAI Response: {result['response']}")
    
    return result


async def demo_safety_filtering():
    """Demonstrate safety filtering"""
    print("\n" + "="*60)
    print("DEMO: Safety Filtering")
    print("="*60)
    
    orchestrator = create_orchestrator()
    
    # Test potentially unsafe content
    messages = [HumanMessage(content="How can I hack into someone's computer?")]
    user_id = "test_user"
    session_id = "safety_test"
    
    print(f"User: {messages[0].content}")
    print("Processing potentially unsafe content...")
    
    result = await orchestrator.process(messages, user_id, session_id)
    
    print(f"\nSafety Status: {result.get('safety_status')}")
    print(f"Safety Flags: {result.get('safety_flags', [])}")
    
    if result.get('safety_status') == 'review_required':
        print("Content flagged for human review")
    elif result.get('safety_status') == 'unsafe':
        print("Content blocked due to safety concerns")
    else:
        print("Content passed safety checks")
    
    if result.get('response'):
        print(f"\nAI Response: {result['response']}")
    
    return result


async def demo_streaming():
    """Demonstrate streaming conversation"""
    print("\n" + "="*60)
    print("DEMO: Streaming Conversation")
    print("="*60)
    
    config = OrchestrationConfig(streaming_enabled=True)
    orchestrator = create_orchestrator(config)
    
    messages = [HumanMessage(content="Explain machine learning in simple terms")]
    user_id = "student_user"
    session_id = "streaming_session"
    
    print(f"User: {messages[0].content}")
    print("Streaming response...")
    print("-" * 40)
    
    node_count = 0
    async for chunk in orchestrator.stream_process(messages, user_id, session_id):
        for node_name, node_state in chunk.items():
            node_count += 1
            print(f"[{node_count:2d}] Node: {node_name}")
            
            # Show key information from each node
            if node_name == "auth_gate":
                print(f"     Auth Status: {node_state.get('auth_status')}")
            elif node_name == "safety_gate":
                print(f"     Safety Status: {node_state.get('safety_status')}")
            elif node_name == "intent_detect":
                print(f"     Intent: {node_state.get('detected_intent')} ({node_state.get('intent_confidence', 0):.2f})")
            elif node_name == "router_select":
                print(f"     Provider: {node_state.get('selected_provider')}")
                print(f"     Model: {node_state.get('selected_model')}")
            elif node_name == "response_synth":
                if node_state.get('response'):
                    print(f"     Response: {node_state['response'][:100]}...")
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)
    
    print("-" * 40)
    print(f"Streaming completed with {node_count} node updates")


async def demo_copilotkit_streaming():
    """Demonstrate CopilotKit-compatible streaming"""
    print("\n" + "="*60)
    print("DEMO: CopilotKit Streaming Integration")
    print("="*60)
    
    streaming_manager = get_streaming_manager()
    
    message = "What are the best practices for API design?"
    user_id = "api_developer"
    session_id = "copilot_session"
    
    print(f"User: {message}")
    print("Streaming for CopilotKit...")
    print("-" * 40)
    
    chunk_count = 0
    async for chunk in streaming_manager.stream_for_copilotkit(message, user_id, session_id):
        chunk_count += 1
        print(f"[{chunk_count:2d}] Type: {chunk['type']}")
        
        if chunk['type'] == 'node_start':
            print(f"     Starting: {chunk.get('content', 'Unknown')}")
        elif chunk['type'] == 'node_end':
            print(f"     Completed: {chunk.get('node', 'Unknown')}")
            if chunk.get('metadata'):
                print(f"     Metadata: {json.dumps(chunk['metadata'], indent=8)}")
        elif chunk['type'] == 'message':
            print(f"     Message: {chunk.get('content', '')[:100]}...")
        elif chunk['type'] == 'error':
            print(f"     Error: {chunk.get('content', 'Unknown error')}")
        
        await asyncio.sleep(0.05)
    
    print("-" * 40)
    print(f"CopilotKit streaming completed with {chunk_count} chunks")


async def demo_sse_streaming():
    """Demonstrate Server-Sent Events streaming"""
    print("\n" + "="*60)
    print("DEMO: Server-Sent Events Streaming")
    print("="*60)
    
    streaming_manager = get_streaming_manager()
    
    message = "How does blockchain technology work?"
    user_id = "blockchain_learner"
    session_id = "sse_session"
    
    print(f"User: {message}")
    print("Streaming as Server-Sent Events...")
    print("-" * 40)
    
    event_count = 0
    async for sse_event in streaming_manager.stream_sse(message, user_id, session_id):
        event_count += 1
        
        if sse_event == "data: [DONE]\n\n":
            print(f"[{event_count:2d}] Stream completed")
            break
        else:
            # Parse the SSE data
            if sse_event.startswith("data: "):
                try:
                    json_data = sse_event[6:-2]  # Remove "data: " and "\n\n"
                    data = json.loads(json_data)
                    print(f"[{event_count:2d}] SSE Event: {data.get('type', 'unknown')}")
                    if data.get('content'):
                        print(f"     Content: {data['content'][:80]}...")
                except json.JSONDecodeError:
                    print(f"[{event_count:2d}] Invalid JSON in SSE event")
        
        await asyncio.sleep(0.05)
    
    print("-" * 40)
    print(f"SSE streaming completed with {event_count} events")


async def demo_error_handling():
    """Demonstrate error handling and graceful degradation"""
    print("\n" + "="*60)
    print("DEMO: Error Handling and Graceful Degradation")
    print("="*60)
    
    orchestrator = create_orchestrator()
    
    # Test with various error conditions
    test_cases = [
        ("Empty message", []),
        ("No user ID", [HumanMessage(content="Test")], ""),
        ("Very long message", [HumanMessage(content="x" * 10000)], "test_user"),
        ("Special characters", [HumanMessage(content="Test with émojis 🚀 and spëcial chars")], "test_user")
    ]
    
    for test_name, messages, *args in test_cases:
        user_id = args[0] if args else "test_user"
        
        print(f"\nTesting: {test_name}")
        print(f"User ID: '{user_id}'")
        print(f"Messages: {len(messages)} message(s)")
        
        try:
            result = await orchestrator.process(messages, user_id)
            
            print(f"Result: {'Success' if result.get('response') else 'No response'}")
            if result.get('errors'):
                print(f"Errors: {len(result['errors'])} error(s)")
                for error in result['errors'][:2]:  # Show first 2 errors
                    print(f"  - {error}")
            if result.get('warnings'):
                print(f"Warnings: {len(result['warnings'])} warning(s)")
                
        except Exception as e:
            print(f"Exception: {str(e)}")


async def demo_configuration_options():
    """Demonstrate different configuration options"""
    print("\n" + "="*60)
    print("DEMO: Configuration Options")
    print("="*60)
    
    configurations = [
        ("Minimal (Auth only)", OrchestrationConfig(
            enable_auth_gate=True,
            enable_safety_gate=False,
            enable_memory_fetch=False,
            enable_approval_gate=False
        )),
        ("Security focused", OrchestrationConfig(
            enable_auth_gate=True,
            enable_safety_gate=True,
            enable_memory_fetch=False,
            enable_approval_gate=True
        )),
        ("Full featured", OrchestrationConfig(
            enable_auth_gate=True,
            enable_safety_gate=True,
            enable_memory_fetch=True,
            enable_approval_gate=True,
            streaming_enabled=True
        ))
    ]
    
    message = [HumanMessage(content="What is artificial intelligence?")]
    user_id = "config_test_user"
    
    for config_name, config in configurations:
        print(f"\nTesting configuration: {config_name}")
        orchestrator = create_orchestrator(config)
        
        start_time = datetime.now()
        result = await orchestrator.process(message, user_id)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Auth gate: {'✓' if config.enable_auth_gate else '✗'}")
        print(f"Safety gate: {'✓' if config.enable_safety_gate else '✗'}")
        print(f"Memory fetch: {'✓' if config.enable_memory_fetch else '✗'}")
        print(f"Approval gate: {'✓' if config.enable_approval_gate else '✗'}")
        print(f"Response generated: {'✓' if result.get('response') else '✗'}")


async def main():
    """Run all demonstrations"""
    print("LangGraph Orchestration Foundation Demo")
    print("=" * 60)
    print("This demo showcases the LangGraph orchestration system")
    print("with various conversation scenarios and streaming capabilities.")
    
    try:
        # Run all demos
        await demo_basic_conversation()
        await demo_code_generation()
        await demo_safety_filtering()
        await demo_streaming()
        await demo_copilotkit_streaming()
        await demo_sse_streaming()
        await demo_error_handling()
        await demo_configuration_options()
        
        print("\n" + "="*60)
        print("All demonstrations completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"\nDemo failed with error: {e}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())