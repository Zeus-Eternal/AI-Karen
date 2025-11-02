# Hook Workflow Demo Plugin

This plugin demonstrates the advanced hook-based workflow capabilities of the AI Karen plugin system. It showcases how hooks can be integrated into plugin execution to provide enhanced functionality, monitoring, and error handling.

## Features

### Hook Integration
- **Pre-execution Hooks**: Parameter validation and safety checks
- **Step-level Hooks**: Individual step monitoring and analysis
- **Post-execution Hooks**: Workflow summary and performance analysis
- **Error Handling Hooks**: Intelligent error recovery and suggestions

### Workflow Orchestration
- Sequential step execution with configurable delays
- Comprehensive step result tracking
- Performance metrics and analysis
- Error simulation for testing hook functionality

### Monitoring and Analytics
- Real-time step execution monitoring
- Resource usage tracking
- Performance scoring and recommendations
- Comprehensive logging and metrics collection

## Usage

### Basic Usage

```python
# Execute basic hook workflow demo
result = await plugin_manager.run_plugin(
    "hook_workflow_demo",
    {
        "workflow_steps": ["initialize", "process", "finalize"],
        "enable_hooks": True,
        "delay_seconds": 1
    },
    user_context
)
```

### Advanced Configuration

```python
# Execute with custom configuration
result = await plugin_manager.run_plugin(
    "hook_workflow_demo",
    {
        "workflow_steps": [
            "data_validation",
            "preprocessing", 
            "analysis",
            "postprocessing",
            "reporting"
        ],
        "enable_hooks": True,
        "simulate_error": False,
        "delay_seconds": 0.5
    },
    user_context
)
```

### Error Simulation

```python
# Test error handling hooks
result = await plugin_manager.run_plugin(
    "hook_workflow_demo",
    {
        "workflow_steps": ["step1", "step2", "failing_step"],
        "enable_hooks": True,
        "simulate_error": True,
        "delay_seconds": 0
    },
    user_context
)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_steps` | List[str] | `["step1", "step2", "step3"]` | List of workflow steps to execute |
| `enable_hooks` | bool | `true` | Whether to demonstrate hook functionality |
| `simulate_error` | bool | `false` | Whether to simulate an error in the last step |
| `delay_seconds` | float | `1` | Delay between steps for demonstration purposes |

## Response Format

### Successful Execution

```json
{
  "success": true,
  "workflow_name": "hook_workflow_demo",
  "total_steps": 3,
  "completed_steps": 3,
  "execution_time_seconds": 3.0,
  "step_results": [
    {
      "step_name": "step1",
      "step_number": 1,
      "status": "completed",
      "start_time": "2024-01-01T12:00:00",
      "end_time": "2024-01-01T12:00:01",
      "data": {
        "processed_items": 10,
        "step_type": "demo_step",
        "hook_integration": true
      },
      "hook_result": {
        "hook_type": "step_processing",
        "analysis": {
          "step_name": "step1",
          "performance_score": 20,
          "resource_usage": {
            "memory_mb": 5.0,
            "cpu_percent": 1.0
          },
          "recommendations": ["Step performance is optimal"]
        }
      }
    }
  ],
  "hook_demonstrations": {
    "pre_execution_hook": true,
    "step_hooks": true,
    "post_execution_hook": true,
    "post_execution_result": {
      "hook_type": "post_execution",
      "summary": {
        "total_steps": 3,
        "total_items_processed": 60,
        "total_execution_time_seconds": 3.0,
        "average_items_per_second": 20.0,
        "workflow_efficiency": "medium"
      },
      "insights": [
        "Workflow processing rate is excellent"
      ]
    }
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Simulated error in step: failing_step",
  "error_type": "ValueError",
  "partial_results": [...],
  "hook_demonstrations": {
    "error_handling_hook": true,
    "error_handling_result": {
      "hook_type": "error_handling",
      "error_analysis": {
        "error_type": "ValueError",
        "error_message": "Simulated error in step: failing_step",
        "error_category": "simulation",
        "severity": "medium"
      },
      "recovery_suggestions": [
        "Validate input parameters before execution",
        "Check data types and value ranges",
        "Review workflow step configuration",
        "Disable error simulation for normal operation"
      ],
      "auto_recovery_possible": true
    }
  },
  "recovery_suggestions": [
    "Check workflow step parameters",
    "Verify system resources are available",
    "Review hook configuration",
    "Enable detailed logging for debugging"
  ]
}
```

## Hook System Integration

This plugin demonstrates how the AI Karen hook system enhances plugin functionality:

### Pre-execution Hooks
- Validate workflow parameters
- Check resource availability
- Verify user permissions
- Ensure system readiness

### Step-level Hooks
- Monitor individual step execution
- Track resource usage
- Analyze performance metrics
- Provide optimization recommendations

### Post-execution Hooks
- Generate workflow summaries
- Calculate performance statistics
- Provide insights and recommendations
- Update system metrics

### Error Handling Hooks
- Analyze error conditions
- Provide recovery suggestions
- Implement automatic recovery where possible
- Log error details for debugging

## Development and Testing

### Running Tests

```bash
# Test basic functionality
karen plugins test hook_workflow_demo --params '{"workflow_steps": ["test1", "test2"]}'

# Test error handling
karen plugins test hook_workflow_demo --params '{"simulate_error": true}'

# Test hook integration
karen plugins test hook_workflow_demo --params '{"enable_hooks": true, "delay_seconds": 0}'
```

### Debugging

```bash
# Enable debug logging
karen plugins debug hook_workflow_demo --params '{"workflow_steps": ["debug_step"]}' --verbose
```

## Integration Examples

### Workflow Orchestration

```python
from ai_karen_engine.plugin_orchestrator import get_plugin_orchestrator, WorkflowDefinition, WorkflowStep

# Create workflow using the orchestrator
orchestrator = get_plugin_orchestrator()

workflow = WorkflowDefinition(
    name="demo_workflow",
    description="Demonstration workflow with hooks",
    steps=[
        WorkflowStep(
            plugin_intent="hook_workflow_demo",
            params={
                "workflow_steps": ["init", "process"],
                "enable_hooks": True
            }
        )
    ]
)

await orchestrator.register_workflow(workflow)
execution = await orchestrator.execute_workflow(
    "demo_workflow",
    {"demo": True},
    user_context
)
```

### Custom Hook Registration

```python
from ai_karen_engine.plugin_manager import get_plugin_manager
from ai_karen_engine.hooks import HookTypes

plugin_manager = get_plugin_manager()

# Register custom hook for workflow monitoring
async def custom_workflow_monitor(context):
    workflow_data = context.data
    print(f"Monitoring workflow: {workflow_data.get('workflow_name')}")
    return {"monitored": True}

await plugin_manager.register_hook(
    HookTypes.PLUGIN_EXECUTION_START,
    custom_workflow_monitor,
    priority=25
)
```

## Best Practices

1. **Hook Design**: Design hooks to be lightweight and non-blocking
2. **Error Handling**: Always provide meaningful error messages and recovery suggestions
3. **Performance**: Monitor hook execution time to avoid performance impact
4. **Testing**: Test both successful and error scenarios
5. **Documentation**: Document hook behavior and integration points

## Troubleshooting

### Common Issues

1. **Hook Not Executing**: Verify hook manager is properly initialized
2. **Performance Issues**: Check hook execution time and optimize if needed
3. **Error Handling**: Ensure error hooks provide actionable recovery suggestions
4. **Parameter Validation**: Verify all required parameters are provided

### Debug Information

Enable debug logging to see detailed hook execution information:

```python
import logging
logging.getLogger("ai_karen_engine.hooks").setLevel(logging.DEBUG)
```

## License

This plugin is part of the AI Karen project and is licensed under the same terms as the main project.