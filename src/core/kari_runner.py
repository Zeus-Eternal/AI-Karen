def run_kari_core(prompt: str, provider: str, model: str) -> str:
    """Generate text using a transformers pipeline, safely handling args."""
    from transformers import pipeline

    pipe = pipeline("text-generation", model=model, device=0)

    valid_args = set(pipe.model.generation_config.to_diff_dict().keys())
    gen_args = {"max_new_tokens": 250}
    if "temperature" in valid_args:
        gen_args["temperature"] = 0.7

    result = pipe(prompt, **gen_args)
    return result[0]["generated_text"]
