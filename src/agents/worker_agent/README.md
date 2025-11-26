# Worker Agent

The Worker Agent is a general-purpose agent for handling single-domain tasks within the Kari system.

## Overview

The Worker Agent is designed to execute tasks within a single domain, such as data processing or analysis. It follows the standard agent interface defined in the Kari architecture specification.

## Capabilities

- **Task Execution**: Execute tasks within a single domain
- **Data Processing**: Process data in various formats (JSON, XML, text)
- **Analysis**: Perform analysis on input data

## Agent Interface

The Worker Agent implements the standard agent interface:

```python
def initialize(context: dict) -> None
def execute(task: dict) -> dict
def finalize(result: dict) -> None
```

### Initialize

The `initialize` function is called when the agent is first loaded. It receives a context dictionary containing configuration and state information.

### Execute

The `execute` function is called to perform a task. It receives a task dictionary with the following structure:

```json
{
  "type": "data_processing|analysis",
  "data": {
    "input": "string",
    "parameters": {
      "format": "json|xml|text",
      "options": {}
    }
  },
  "priority": 1-10,
  "timeout": seconds
}
```

The function returns a result dictionary with the outcome of the task.

### Finalize

The `finalize` function is called when the agent is being unloaded. It receives the final result of the agent's operations.

## Task Types

### Data Processing

Processes input data according to the specified format and options.

**Example**:
```json
{
  "type": "data_processing",
  "data": {
    "input": "Sample data to process",
    "parameters": {
      "format": "json",
      "options": {
        "normalize": true
      }
    }
  }
}
```

### Analysis

Performs analysis on the input data.

**Example**:
```json
{
  "type": "analysis",
  "data": {
    "input": "Sample data to analyze",
    "parameters": {
      "format": "text",
      "options": {
        "depth": "detailed"
      }
    }
  }
}
```

## Configuration

The Worker Agent can be configured through the context passed to the `initialize` function:

```python
context = {
  "config": {
    "max_concurrent_tasks": 5,
    "default_timeout": 60,
    "log_level": "INFO"
  },
  "state": {
    "initialized": False
  }
}
```

## Testing

To run the tests for the Worker Agent:

```bash
cd src/agents/worker_agent
python -m pytest tests/
```

## Schema

The agent uses JSON Schema for task validation. The schema is defined in `schema/task.json`.

## Dependencies

The Worker Agent has no external dependencies beyond the Python standard library.

## Permissions

The Worker Agent requires the following permissions:
- `read`: Access to read data
- `execute`: Permission to execute tasks

## Resources

The Worker Agent typically requires:
- CPU: 1 core
- Memory: 1GB

## Examples

See the `examples/` directory for example usage of the Worker Agent.