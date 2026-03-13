"""Basic usage example for the worker agent."""

from src.agents.worker_agent.handler import WorkerAgentHandler


def main():
    """Demonstrate basic usage of the worker agent."""
    # Create a handler instance
    handler = WorkerAgentHandler()
    
    # Define a sample task
    task = {
        "type": "data_processing",
        "data": {
            "input": "sample data",
            "operation": "transform"
        },
        "priority": 5
    }
    
    # Process the task
    result = handler.process_task(task)
    print(f"Task result: {result}")
    
    # Get agent information
    info = handler.get_info()
    print(f"Agent info: {info}")


if __name__ == "__main__":
    main()