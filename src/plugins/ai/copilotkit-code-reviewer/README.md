# CopilotKit Code Reviewer Plugin

Provides AI-assisted code reviews powered by CopilotKit. The plugin analyzes source code across multiple categories such as security, performance, and maintainability.

## Usage

Invoke the plugin via the plugin service with the `review_code` intent:

```json
{
  "code": "def foo():\n    return 42",
  "language": "python",
  "review_scope": ["security", "performance"],
  "user_context": {"user_id": "u123", "tenant_id": "t456"}
}
```

The handler returns an overall score, findings list, and a formatted Markdown report.

## Memory Integration

After generating a review report the plugin stores the formatted report and summary metadata in the unified memory service. Entries are tagged with `code_review` and `copilotkit` and include fields such as overall score, findings count, and reviewed categories. The memory store requires `user_id` and `tenant_id` in the `user_context`.

## Configuration

- **Permissions**: requires write access to memory backends (Postgres and Milvus).
- **Dependencies**: relies on `ai_karen_engine` and `copilotkit` packages.
- **Supported Languages**: Python, JavaScript/TypeScript, Java, C++, Rust, Go, PHP, Ruby.
