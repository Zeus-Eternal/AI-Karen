"""
Demo script for the autonomous training scheduler manager.

This script demonstrates the comprehensive cron-based scheduling system for autonomous
learning cycles, including schedule creation, configuration, monitoring, and notifications.
"""

import asyncio
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from ai_karen_engine.core.response.scheduler_manager import (
    SchedulerManager, AutonomousConfig, NotificationConfig, SafetyControls,
    NotificationType, SafetyLevel
)
from ai_karen_engine.core.response.autonomous_learner import (
    AutonomousLearner, LearningCycleResult, TrainingStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_autonomous_learner():
    """Create a mock autonomous learner for demonstration."""
    learner = Mock(spec=AutonomousLearner)
    
    # Mock successful learning cycle
    result = LearningCycleResult(
        cycle_id="demo-cycle-123",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        status=TrainingStatus.COMPLETED,
        data_collected=250,
        examples_created=200,
        training_time=120.5,
        model_improved=True,
        rollback_performed=False
    )
    
    learner.trigger_learning_cycle = AsyncMock(return_value=result)
    return learner


def create_mock_memory_service():
    """Create a mock memory service for demonstration."""
    service = Mock()
    service.store_web_ui_memory = AsyncMock()
    service.query_memories = AsyncMock(return_value=[])
    return service


async def demonstrate_basic_scheduling():
    """Demonstrate basic scheduling functionality."""
    print("\n" + "="*60)
    print("AUTONOMOUS TRAINING SCHEDULER DEMO")
    print("="*60)
    
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        
        # Initialize components
        autonomous_learner = create_mock_autonomous_learner()
        memory_service = create_mock_memory_service()
        
        # Create scheduler manager
        scheduler = SchedulerManager(
            autonomous_learner=autonomous_learner,
            memory_service=memory_service,
            storage_path=storage_path
        )
        
        print(f"\n1. Created scheduler manager with storage at: {storage_path}")
        
        # Create autonomous configuration
        config = AutonomousConfig(
            enabled=True,
            training_schedule="0 2 * * *",  # Daily at 2 AM
            timezone="UTC",
            min_data_threshold=100,
            quality_threshold=0.7,
            validation_threshold=0.85,
            safety_controls=SafetyControls(
                level=SafetyLevel.MODERATE,
                min_data_threshold=100,
                max_data_threshold=10000,
                quality_threshold=0.7,
                max_training_time_minutes=60,
                validation_threshold=0.85,
                rollback_on_degradation=True,
                max_memory_usage_mb=2048,
                max_cpu_usage_percent=80.0,
                max_consecutive_failures=3,
                failure_cooldown_hours=24,
                backup_before_training=True,
                max_backup_retention_days=30
            ),
            notifications=NotificationConfig(
                enabled=True,
                types=[NotificationType.LOG, NotificationType.MEMORY],
                memory_tenant_id="demo-tenant",
                memory_importance_score=8
            ),
            max_training_time=3600,
            backup_models=True,
            auto_rollback=True
        )
        
        print("\n2. Created autonomous configuration:")
        print(f"   - Schedule: {config.training_schedule} (Daily at 2 AM)")
        print(f"   - Safety Level: {config.safety_controls.level.value}")
        print(f"   - Notifications: {[t.value for t in config.notifications.types]}")
        print(f"   - Quality Threshold: {config.quality_threshold}")
        print(f"   - Validation Threshold: {config.validation_threshold}")
        
        # Create training schedules
        try:
            schedule_id1 = scheduler.create_training_schedule(
                tenant_id="demo-tenant-1",
                name="Daily Training Schedule",
                cron_expression="0 2 * * *",
                config=config,
                description="Daily autonomous training at 2 AM"
            )
            print(f"\n3. Created daily training schedule: {schedule_id1}")
            
            # Create weekly schedule
            weekly_config = AutonomousConfig(
                enabled=True,
                training_schedule="0 3 * * 0",  # Weekly on Sunday at 3 AM
                timezone="UTC",
                min_data_threshold=500,
                quality_threshold=0.8,
                validation_threshold=0.9,
                safety_controls=SafetyControls(level=SafetyLevel.STRICT),
                notifications=NotificationConfig(
                    enabled=True,
                    types=[NotificationType.LOG, NotificationType.MEMORY],
                    memory_tenant_id="demo-tenant-2"
                )
            )
            
            schedule_id2 = scheduler.create_training_schedule(
                tenant_id="demo-tenant-2",
                name="Weekly Deep Training",
                cron_expression="0 3 * * 0",
                config=weekly_config,
                description="Weekly comprehensive training on Sundays"
            )
            print(f"4. Created weekly training schedule: {schedule_id2}")
            
        except Exception as e:
            print(f"   Note: Schedule creation failed (croniter may not be available): {e}")
            print("   This is expected in environments without croniter installed.")
            return
        
        # List all schedules
        schedules = scheduler.list_schedules()
        print(f"\n5. Total schedules created: {len(schedules)}")
        for schedule in schedules:
            print(f"   - {schedule['name']} ({schedule['schedule_id'][:8]}...)")
            print(f"     Status: {schedule['status']}")
            print(f"     Cron: {schedule['cron_expression']}")
            print(f"     Next run: {schedule['next_run']}")
        
        # Get detailed status
        status1 = scheduler.get_schedule_status(schedule_id1)
        if status1:
            print(f"\n6. Detailed status for '{status1['name']}':")
            print(f"   - Schedule ID: {status1['schedule_id']}")
            print(f"   - Status: {status1['status']}")
            print(f"   - Total runs: {status1['total_runs']}")
            print(f"   - Successful runs: {status1['successful_runs']}")
            print(f"   - Failed runs: {status1['failed_runs']}")
            print(f"   - Is running: {status1['is_running']}")
        
        # Demonstrate schedule management
        print(f"\n7. Demonstrating schedule management:")
        
        # Pause schedule
        success = scheduler.pause_schedule(schedule_id1)
        print(f"   - Paused schedule: {success}")
        
        # Check status after pause
        status = scheduler.get_schedule_status(schedule_id1)
        print(f"   - Status after pause: {status['status'] if status else 'Not found'}")
        
        # Resume schedule
        success = scheduler.resume_schedule(schedule_id1)
        print(f"   - Resumed schedule: {success}")
        
        # Update schedule
        success = scheduler.update_schedule(
            schedule_id1,
            name="Updated Daily Training",
            description="Updated description for daily training"
        )
        print(f"   - Updated schedule: {success}")
        
        # Verify update
        status = scheduler.get_schedule_status(schedule_id1)
        print(f"   - New name: {status['name'] if status else 'Not found'}")
        
        # Demonstrate scheduler lifecycle
        print(f"\n8. Demonstrating scheduler lifecycle:")
        
        # Start scheduler
        print("   - Starting scheduler...")
        await scheduler.start_scheduler()
        print(f"   - Scheduler running: {scheduler.running}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Get overall status
        total_schedules = len(scheduler.schedules)
        active_schedules = sum(1 for s in scheduler.schedules.values() 
                              if s.status.value == "active")
        running_tasks = len(scheduler.running_tasks)
        
        print(f"   - Total schedules: {total_schedules}")
        print(f"   - Active schedules: {active_schedules}")
        print(f"   - Running tasks: {running_tasks}")
        
        # Stop scheduler
        print("   - Stopping scheduler...")
        await scheduler.stop_scheduler()
        print(f"   - Scheduler running: {scheduler.running}")
        
        # Demonstrate persistence
        print(f"\n9. Demonstrating schedule persistence:")
        
        # Create new scheduler with same storage
        new_scheduler = SchedulerManager(
            autonomous_learner=autonomous_learner,
            memory_service=memory_service,
            storage_path=storage_path
        )
        
        loaded_schedules = new_scheduler.list_schedules()
        print(f"   - Loaded {len(loaded_schedules)} schedules from storage")
        for schedule in loaded_schedules:
            print(f"     * {schedule['name']}")
        
        # Clean up - delete schedules
        print(f"\n10. Cleaning up schedules:")
        for schedule_id in [schedule_id1, schedule_id2]:
            success = scheduler.delete_schedule(schedule_id)
            print(f"    - Deleted schedule {schedule_id[:8]}...: {success}")
        
        final_count = len(scheduler.list_schedules())
        print(f"    - Final schedule count: {final_count}")


async def demonstrate_safety_controls():
    """Demonstrate safety control functionality."""
    print("\n" + "="*60)
    print("SAFETY CONTROLS DEMONSTRATION")
    print("="*60)
    
    # Create scheduler with mock components
    with tempfile.TemporaryDirectory() as temp_dir:
        autonomous_learner = create_mock_autonomous_learner()
        memory_service = create_mock_memory_service()
        
        scheduler = SchedulerManager(
            autonomous_learner=autonomous_learner,
            memory_service=memory_service,
            storage_path=Path(temp_dir)
        )
        
        print("\n1. Safety Control Levels:")
        for level in SafetyLevel:
            print(f"   - {level.value.upper()}: {level.value} safety checks")
        
        # Demonstrate different safety configurations
        safety_configs = {
            "Strict": SafetyControls(
                level=SafetyLevel.STRICT,
                min_data_threshold=500,
                max_data_threshold=5000,
                quality_threshold=0.9,
                max_training_time_minutes=30,
                validation_threshold=0.95,
                rollback_on_degradation=True,
                max_memory_usage_mb=1024,
                max_cpu_usage_percent=60.0,
                max_consecutive_failures=1,
                failure_cooldown_hours=48
            ),
            "Moderate": SafetyControls(
                level=SafetyLevel.MODERATE,
                min_data_threshold=100,
                max_data_threshold=10000,
                quality_threshold=0.7,
                max_training_time_minutes=60,
                validation_threshold=0.85,
                rollback_on_degradation=True,
                max_memory_usage_mb=2048,
                max_cpu_usage_percent=80.0,
                max_consecutive_failures=3,
                failure_cooldown_hours=24
            ),
            "Permissive": SafetyControls(
                level=SafetyLevel.PERMISSIVE,
                min_data_threshold=50,
                max_data_threshold=50000,
                quality_threshold=0.5,
                max_training_time_minutes=120,
                validation_threshold=0.7,
                rollback_on_degradation=False,
                max_memory_usage_mb=4096,
                max_cpu_usage_percent=95.0,
                max_consecutive_failures=5,
                failure_cooldown_hours=12
            )
        }
        
        print("\n2. Safety Configuration Examples:")
        for name, config in safety_configs.items():
            print(f"\n   {name.upper()} Configuration:")
            print(f"   - Data threshold: {config.min_data_threshold}-{config.max_data_threshold}")
            print(f"   - Quality threshold: {config.quality_threshold}")
            print(f"   - Max training time: {config.max_training_time_minutes} minutes")
            print(f"   - Validation threshold: {config.validation_threshold}")
            print(f"   - Max memory: {config.max_memory_usage_mb} MB")
            print(f"   - Max CPU: {config.max_cpu_usage_percent}%")
            print(f"   - Max failures: {config.max_consecutive_failures}")
            print(f"   - Cooldown: {config.failure_cooldown_hours} hours")
            print(f"   - Auto rollback: {config.rollback_on_degradation}")
        
        # Demonstrate resource monitoring
        print("\n3. Resource Monitoring:")
        resource_monitor = scheduler.resource_monitor
        
        try:
            usage = await resource_monitor.get_current_usage()
            print(f"   - Current memory usage: {usage['memory_mb']:.1f} MB ({usage['memory_percent']:.1f}%)")
            print(f"   - Current CPU usage: {usage['cpu_percent']:.1f}%")
        except Exception as e:
            print(f"   - Resource monitoring unavailable: {e}")
            print("   - This is expected if psutil is not installed")


async def demonstrate_notifications():
    """Demonstrate notification system."""
    print("\n" + "="*60)
    print("NOTIFICATION SYSTEM DEMONSTRATION")
    print("="*60)
    
    # Create notification manager
    memory_service = create_mock_memory_service()
    from ai_karen_engine.core.response.scheduler_manager import NotificationManager
    
    notification_manager = NotificationManager(memory_service)
    
    print("\n1. Available Notification Types:")
    for notification_type in NotificationType:
        print(f"   - {notification_type.value.upper()}")
    
    # Demonstrate different notification configurations
    configs = {
        "Log Only": NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG]
        ),
        "Memory Storage": NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG, NotificationType.MEMORY],
            memory_tenant_id="demo-tenant",
            memory_importance_score=8
        ),
        "Email Notifications": NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG, NotificationType.EMAIL],
            email_smtp_host="smtp.example.com",
            email_smtp_port=587,
            email_username="karen@example.com",
            email_recipients=["admin@example.com", "ops@example.com"],
            email_use_tls=True
        ),
        "Webhook Integration": NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG, NotificationType.WEBHOOK],
            webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            webhook_headers={"Content-Type": "application/json"},
            webhook_timeout=30
        ),
        "All Channels": NotificationConfig(
            enabled=True,
            types=[NotificationType.LOG, NotificationType.MEMORY, 
                   NotificationType.EMAIL, NotificationType.WEBHOOK],
            memory_tenant_id="demo-tenant",
            memory_importance_score=9,
            email_smtp_host="smtp.example.com",
            email_recipients=["admin@example.com"],
            webhook_url="https://example.com/webhook"
        )
    }
    
    print("\n2. Notification Configuration Examples:")
    for name, config in configs.items():
        print(f"\n   {name.upper()}:")
        print(f"   - Enabled: {config.enabled}")
        print(f"   - Types: {[t.value for t in config.types]}")
        if NotificationType.EMAIL in config.types:
            print(f"   - Email SMTP: {config.email_smtp_host}:{config.email_smtp_port}")
            print(f"   - Email recipients: {len(config.email_recipients)}")
        if NotificationType.WEBHOOK in config.types:
            print(f"   - Webhook URL: {config.webhook_url}")
        if NotificationType.MEMORY in config.types:
            print(f"   - Memory tenant: {config.memory_tenant_id}")
            print(f"   - Importance score: {config.memory_importance_score}")
    
    # Demonstrate sending notifications
    print("\n3. Sending Test Notifications:")
    
    test_events = [
        ("training_started", "Training Started", "Autonomous training cycle has begun"),
        ("training_completed", "Training Completed", "Training completed successfully with model improvements"),
        ("training_failed", "Training Failed", "Training cycle failed due to validation errors"),
        ("schedule_paused", "Schedule Paused", "Training schedule has been paused by administrator")
    ]
    
    # Use log-only config for demo
    log_config = configs["Log Only"]
    
    for event_type, title, message in test_events:
        print(f"   - Sending {event_type} notification...")
        try:
            await notification_manager.send_notification(
                log_config,
                event_type,
                title,
                message,
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "demo": True,
                    "event_data": {"success": event_type != "training_failed"}
                }
            )
            print(f"     ✓ Sent successfully")
        except Exception as e:
            print(f"     ✗ Failed: {e}")


async def demonstrate_cron_expressions():
    """Demonstrate cron expression examples."""
    print("\n" + "="*60)
    print("CRON EXPRESSION EXAMPLES")
    print("="*60)
    
    print("\n1. Cron Expression Format:")
    print("   minute hour day_of_month month day_of_week")
    print("   (0-59) (0-23) (1-31) (1-12) (0-7, 0=Sunday)")
    
    examples = {
        "0 2 * * *": "Daily at 2:00 AM",
        "0 */6 * * *": "Every 6 hours",
        "30 14 * * 1": "Every Monday at 2:30 PM",
        "0 9 1 * *": "First day of every month at 9:00 AM",
        "0 0 * * 0": "Every Sunday at midnight",
        "15 10 * * 1-5": "Weekdays at 10:15 AM",
        "0 22 * * 6": "Every Saturday at 10:00 PM",
        "0 */4 * * *": "Every 4 hours",
        "30 3 1,15 * *": "1st and 15th of month at 3:30 AM",
        "0 8-17 * * 1-5": "Every hour from 8 AM to 5 PM on weekdays"
    }
    
    print("\n2. Common Scheduling Examples:")
    for cron, description in examples.items():
        print(f"   {cron:<15} → {description}")
    
    print("\n3. Special Characters:")
    print("   *     → Any value")
    print("   */n   → Every n units")
    print("   a-b   → Range from a to b")
    print("   a,b,c → Specific values a, b, and c")
    
    print("\n4. Training Schedule Recommendations:")
    recommendations = {
        "Development": "0 2 * * *",      # Daily at 2 AM
        "Staging": "0 1 * * 0",          # Weekly on Sunday at 1 AM
        "Production": "0 3 * * 6",       # Weekly on Saturday at 3 AM
        "High-frequency": "0 */12 * * *", # Every 12 hours
        "Low-frequency": "0 4 1 * *"     # Monthly on 1st at 4 AM
    }
    
    for env, cron in recommendations.items():
        print(f"   {env:<15} → {cron}")


async def main():
    """Run all demonstrations."""
    try:
        await demonstrate_basic_scheduling()
        await demonstrate_safety_controls()
        await demonstrate_notifications()
        await demonstrate_cron_expressions()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Schedule creation and management")
        print("✓ Cron-based timing configuration")
        print("✓ Safety controls and resource monitoring")
        print("✓ Multi-channel notification system")
        print("✓ Schedule persistence and recovery")
        print("✓ Comprehensive error handling")
        print("✓ Admin-level security controls")
        
        print("\nNext Steps:")
        print("1. Install croniter for full cron support: pip install croniter")
        print("2. Configure SMTP settings for email notifications")
        print("3. Set up webhook endpoints for external integrations")
        print("4. Customize safety controls for your environment")
        print("5. Create production training schedules")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nThis may be due to missing dependencies (croniter, psutil)")
        print("Install with: pip install croniter psutil")


if __name__ == "__main__":
    asyncio.run(main())