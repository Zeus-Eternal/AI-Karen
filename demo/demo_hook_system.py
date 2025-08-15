#!/usr/bin/env python3
"""
Demo script showing the hook system integration with ChatOrchestrator.

This script demonstrates how hooks can be registered and triggered during
chat message processing, showcasing the AG-UI + CopilotKit chat enhancement
hook capabilities.
"""

import asyncio
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest, ProcessingContext
from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_basic_hook_integration():
    """Demonstrate basic hook integration with ChatOrchestrator."""
    print("\n" + "="*60)
    print("DEMO: Basic Hook Integration with ChatOrchestrator")
    print("="*60)
    
    # Get hook manager
    hook_manager = get_hook_manager()
    
    # Clear any existing demo hooks
    await hook_manager.clear_hooks_by_source("demo")
    
    # Register demo hooks
    async def pre_message_hook(context: HookContext):
        print(f"🔗 PRE-MESSAGE HOOK: Processing message from user {context.data.get('user_id')}")
        print(f"   Message: {context.data.get('message')}")
        return {"status": "pre_processed", "timestamp": datetime.utcnow().isoformat()}
    
    async def message_processed_hook(context: HookContext):
        print(f"🔗 MESSAGE-PROCESSED HOOK: Message processing completed")
        print(f"   Response length: {len(context.data.get('response', ''))}")
        return {"status": "processed", "response_analyzed": True}
    
    async def post_message_hook(context: HookContext):
        print(f"🔗 POST-MESSAGE HOOK: Finalizing message processing")
        print(f"   Total processing time: {context.data.get('processing_time', 0):.3f}s")
        return {"status": "finalized", "cleanup_performed": True}
    
    # Register hooks
    hook_ids = []
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=pre_message_hook,
        priority=100,
        source_type="demo",
        source_name="basic_demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.MESSAGE_PROCESSED,
        handler=message_processed_hook,
        priority=100,
        source_type="demo",
        source_name="basic_demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.POST_MESSAGE,
        handler=post_message_hook,
        priority=100,
        source_type="demo",
        source_name="basic_demo"
    ))
    
    try:
        print(f"\n✅ Registered {len(hook_ids)} demo hooks")
        
        # Create ChatOrchestrator
        chat_orchestrator = ChatOrchestrator()
        
        # Create demo request
        request = ChatRequest(
            message="Hello! Can you help me understand how AG-UI and CopilotKit work together?",
            user_id="demo_user_123",
            conversation_id="demo_conv_456",
            session_id="demo_session_789",
            stream=False,
            include_context=True,
            attachments=["demo_file.txt"],
            metadata={"demo": True, "feature": "ag-ui-copilotkit"}
        )
        
        print(f"\n📨 Processing demo message...")
        print(f"   User: {request.user_id}")
        print(f"   Message: {request.message}")
        
        # Mock the processing pipeline to simulate real processing
        with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                response="Great question! AG-UI provides enterprise-grade React components for data visualization, while CopilotKit offers AI-powered development assistance. Together, they create a modern, intelligent chat interface with advanced UI components and contextual AI suggestions.",
                parsed_message=MagicMock(entities=[("AG-UI", "TECHNOLOGY"), ("CopilotKit", "TECHNOLOGY")]),
                embeddings=[0.1, 0.2, 0.3, 0.4, 0.5],
                context={"memories": [], "context_summary": "Technology integration query"},
                used_fallback=False
            )
            
            # Process the message
            response = await chat_orchestrator._process_traditional(request, ProcessingContext())
            
            print(f"\n✅ Message processed successfully!")
            print(f"   Response: {response.response[:100]}...")
            print(f"   Processing time: {response.processing_time:.3f}s")
            print(f"   Hooks executed: {response.metadata.get('total_hooks_executed', 0)}")
            print(f"   Used fallback: {response.used_fallback}")
            
            # Show hook execution details
            print(f"\n📊 Hook Execution Summary:")
            print(f"   Pre-message hooks: {response.metadata.get('pre_hooks_executed', 0)}")
            print(f"   Message-processed hooks: {response.metadata.get('processed_hooks_executed', 0)}")
            print(f"   Post-message hooks: {response.metadata.get('post_hooks_executed', 0)}")
            
    finally:
        # Clean up
        for hook_id in hook_ids:
            await hook_manager.unregister_hook(hook_id)
        print(f"\n🧹 Cleaned up {len(hook_ids)} demo hooks")


async def demo_hook_priority_and_conditions():
    """Demonstrate hook priority ordering and conditional execution."""
    print("\n" + "="*60)
    print("DEMO: Hook Priority and Conditional Execution")
    print("="*60)
    
    hook_manager = get_hook_manager()
    await hook_manager.clear_hooks_by_source("demo")
    
    execution_log = []
    
    # Create hooks with different priorities
    async def high_priority_hook(context: HookContext):
        execution_log.append("HIGH_PRIORITY")
        print("🔥 HIGH PRIORITY HOOK: Critical preprocessing")
        return {"priority": "high", "order": 1}
    
    async def medium_priority_hook(context: HookContext):
        execution_log.append("MEDIUM_PRIORITY")
        print("⚡ MEDIUM PRIORITY HOOK: Standard processing")
        return {"priority": "medium", "order": 2}
    
    async def low_priority_hook(context: HookContext):
        execution_log.append("LOW_PRIORITY")
        print("📝 LOW PRIORITY HOOK: Logging and cleanup")
        return {"priority": "low", "order": 3}
    
    async def conditional_hook(context: HookContext):
        execution_log.append("CONDITIONAL")
        print("🎯 CONDITIONAL HOOK: Only for demo users")
        return {"conditional": True, "user_type": "demo"}
    
    # Register hooks with different priorities (lower number = higher priority)
    hook_ids = []
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=low_priority_hook,
        priority=300,  # Low priority
        source_type="demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=high_priority_hook,
        priority=100,  # High priority
        source_type="demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=medium_priority_hook,
        priority=200,  # Medium priority
        source_type="demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=conditional_hook,
        priority=150,
        conditions={"custom": {"user_type": "demo"}},  # Only for demo users
        source_type="demo"
    ))
    
    try:
        print(f"\n✅ Registered {len(hook_ids)} priority demo hooks")
        
        # Create ChatOrchestrator
        chat_orchestrator = ChatOrchestrator()
        
        # Create demo request
        request = ChatRequest(
            message="Show me hook priority execution!",
            user_id="demo_user",
            conversation_id="priority_demo",
            stream=False,
            include_context=False,
            metadata={"user_type": "demo"}
        )
        
        print(f"\n📨 Processing priority demo message...")
        
        # Mock processing
        with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                response="Hook priority demonstration completed! Hooks executed in order: HIGH → CONDITIONAL → MEDIUM → LOW",
                parsed_message=None,
                embeddings=None,
                context=None,
                used_fallback=False
            )
            
            # Process the message
            response = await chat_orchestrator._process_traditional(request, ProcessingContext())
            
            print(f"\n✅ Priority demo completed!")
            print(f"   Execution order: {' → '.join(execution_log)}")
            print(f"   Expected order: HIGH_PRIORITY → CONDITIONAL → MEDIUM_PRIORITY → LOW_PRIORITY")
            print(f"   Hooks executed: {response.metadata.get('pre_hooks_executed', 0)}")
            
            # Verify execution order
            expected_order = ["HIGH_PRIORITY", "CONDITIONAL", "MEDIUM_PRIORITY", "LOW_PRIORITY"]
            if execution_log == expected_order:
                print("   ✅ Hook execution order is correct!")
            else:
                print(f"   ❌ Unexpected execution order: {execution_log}")
            
    finally:
        # Clean up
        for hook_id in hook_ids:
            await hook_manager.unregister_hook(hook_id)
        print(f"\n🧹 Cleaned up {len(hook_ids)} priority demo hooks")


async def demo_hook_error_handling():
    """Demonstrate hook error handling and resilience."""
    print("\n" + "="*60)
    print("DEMO: Hook Error Handling and Resilience")
    print("="*60)
    
    hook_manager = get_hook_manager()
    await hook_manager.clear_hooks_by_source("demo")
    
    # Create hooks that will fail and succeed
    async def failing_hook(context: HookContext):
        print("💥 FAILING HOOK: This hook will raise an exception")
        raise ValueError("Simulated hook failure for demo purposes")
    
    async def resilient_hook(context: HookContext):
        print("💪 RESILIENT HOOK: This hook continues despite other failures")
        return {"status": "resilient", "survived_failure": True}
    
    async def recovery_hook(context: HookContext):
        print("🔧 RECOVERY HOOK: Performing cleanup after failures")
        return {"status": "recovery", "cleanup_performed": True}
    
    # Register hooks
    hook_ids = []
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=failing_hook,
        priority=100,
        source_type="demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=resilient_hook,
        priority=200,
        source_type="demo"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=recovery_hook,
        priority=300,
        source_type="demo"
    ))
    
    try:
        print(f"\n✅ Registered {len(hook_ids)} error handling demo hooks")
        
        # Create ChatOrchestrator
        chat_orchestrator = ChatOrchestrator()
        
        # Create demo request
        request = ChatRequest(
            message="Test error handling resilience",
            user_id="error_demo_user",
            conversation_id="error_demo",
            stream=False,
            include_context=False
        )
        
        print(f"\n📨 Processing error handling demo...")
        print("   Note: One hook will fail, but processing should continue")
        
        # Mock processing
        with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                response="Error handling demo completed! The system remained resilient despite hook failures.",
                parsed_message=None,
                embeddings=None,
                context=None,
                used_fallback=False
            )
            
            # Process the message - should not raise exception
            response = await chat_orchestrator._process_traditional(request, ProcessingContext())
            
            print(f"\n✅ Error handling demo completed successfully!")
            print(f"   Message processing succeeded despite hook failure")
            print(f"   Response: {response.response[:80]}...")
            print(f"   Successful hooks: {response.metadata.get('pre_hooks_executed', 0)}")
            print("   🎯 System demonstrated resilience to hook failures!")
            
    finally:
        # Clean up
        for hook_id in hook_ids:
            await hook_manager.unregister_hook(hook_id)
        print(f"\n🧹 Cleaned up {len(hook_ids)} error handling demo hooks")


async def demo_hook_system_stats():
    """Demonstrate hook system statistics and monitoring."""
    print("\n" + "="*60)
    print("DEMO: Hook System Statistics and Monitoring")
    print("="*60)
    
    hook_manager = get_hook_manager()
    
    # Show initial stats
    initial_stats = hook_manager.get_summary()
    print(f"\n📊 Initial Hook System Stats:")
    print(f"   Enabled: {initial_stats['enabled']}")
    print(f"   Total hooks: {initial_stats['total_hooks']}")
    print(f"   Hook types: {initial_stats['hook_types']}")
    print(f"   Source types: {initial_stats['source_types']}")
    
    # Register some demo hooks for stats
    async def stats_hook_1(context: HookContext):
        return {"stats": "demo_1"}
    
    async def stats_hook_2(context: HookContext):
        return {"stats": "demo_2"}
    
    hook_ids = []
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.PRE_MESSAGE,
        handler=stats_hook_1,
        source_type="stats_demo",
        source_name="demo_1"
    ))
    
    hook_ids.append(await hook_manager.register_hook(
        hook_type=HookTypes.POST_MESSAGE,
        handler=stats_hook_2,
        source_type="stats_demo",
        source_name="demo_2"
    ))
    
    try:
        # Show updated stats
        updated_stats = hook_manager.get_summary()
        print(f"\n📈 Updated Hook System Stats:")
        print(f"   Total hooks: {updated_stats['total_hooks']} (+{updated_stats['total_hooks'] - initial_stats['total_hooks']})")
        print(f"   Hook types: {updated_stats['hook_types']}")
        print(f"   Source types: {updated_stats['source_types']}")
        
        # Show hook details
        all_hooks = hook_manager.get_all_hooks()
        demo_hooks = [h for h in all_hooks if h.source_type == "stats_demo"]
        
        print(f"\n🔍 Demo Hook Details:")
        for hook in demo_hooks:
            print(f"   Hook ID: {hook.id}")
            print(f"   Type: {hook.hook_type}")
            print(f"   Priority: {hook.priority}")
            print(f"   Source: {hook.source_type}/{hook.source_name}")
            print(f"   Enabled: {hook.enabled}")
            print()
        
        # Show execution stats
        execution_stats = hook_manager.get_execution_stats()
        print(f"📊 Execution Statistics:")
        if execution_stats:
            for stat_name, count in execution_stats.items():
                print(f"   {stat_name}: {count}")
        else:
            print("   No execution statistics available yet")
        
    finally:
        # Clean up
        for hook_id in hook_ids:
            await hook_manager.unregister_hook(hook_id)
        
        # Show final stats
        final_stats = hook_manager.get_summary()
        print(f"\n📉 Final Hook System Stats:")
        print(f"   Total hooks: {final_stats['total_hooks']} (back to {initial_stats['total_hooks']})")
        print("   🧹 Demo hooks cleaned up successfully!")


async def main():
    """Run all hook system demonstrations."""
    print("🚀 AG-UI + CopilotKit Chat Enhancement Hook System Demo")
    print("=" * 60)
    print("This demo showcases the hook capabilities added to Karen's chat system")
    print("for the AG-UI + CopilotKit integration.")
    
    try:
        # Run all demonstrations
        await demo_basic_hook_integration()
        await demo_hook_priority_and_conditions()
        await demo_hook_error_handling()
        await demo_hook_system_stats()
        
        print("\n" + "="*60)
        print("🎉 All Hook System Demonstrations Completed Successfully!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✅ Hook registration and execution during chat processing")
        print("✅ Priority-based hook ordering")
        print("✅ Conditional hook execution")
        print("✅ Error handling and system resilience")
        print("✅ Hook system monitoring and statistics")
        print("✅ Clean hook lifecycle management")
        
        print("\nThe hook system is ready for AG-UI and CopilotKit integration!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution failed")


if __name__ == "__main__":
    asyncio.run(main())