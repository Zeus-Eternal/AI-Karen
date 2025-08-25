# OpenAI Customer Service Plugin

The `openai_llm` plugin allows Kari to delegate text generation to OpenAI models. This can power customer service responses when local models are insufficient.

## Configuration

1. Install the `openai` Python package.
2. Set the `OPENAI_API_KEY` environment variable.
3. Enable the plugin in `plugins/openai_llm/plugin_manifest.json`.

## Usage

Send a chat request with a prompt and the plugin will return the model's reply.

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"text": "draft a refund policy"}' http://localhost:8000/chat
```

For advanced scenarios you may specify the model and token limit in the plugin parameters.

## Security

API keys are stored in environment variables only. Do not commit them to the repository.
