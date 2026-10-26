import os
import time

import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# General-purpose text-generation model from OpenRouter's current free list.
DEFAULT_MODEL = "liquid/lfm-2.5-2.6b:free"
FALLBACK_MODELS = (
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "cohere/north-mini-code:free",
)


def ask_cloud_llm(prompt: str) -> tuple[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Cloud routing is not configured. Set OPENROUTER_API_KEY "
            "before proceeding."
        )

    configured_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    if configured_model in {
        "meta-llama/llama-3.3-8b-instruct:free",
        "openrouter/free",
    }:
        configured_model = DEFAULT_MODEL

    configured_fallbacks = tuple(
        model.strip()
        for model in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",")
        if model.strip()
    )
    models = tuple(dict.fromkeys(
        (configured_model,) + configured_fallbacks + FALLBACK_MODELS
    ))
    errors = []

    for index, model in enumerate(models):
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:5173",
                "X-Title": "PRISM Privacy-Aware LLM Router",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )

        if response.ok:
            data = response.json()
            choices = data.get("choices", [])
            if choices and choices[0].get("message", {}).get("content"):
                return choices[0]["message"]["content"], model
            errors.append(f"{model}: provider returned no answer")
            continue

        detail = response.text[:500]
        errors.append(f"{model}: HTTP {response.status_code}: {detail}")
        if response.status_code == 429 and index < len(models) - 1:
            time.sleep(1)
            continue
        if response.status_code != 429:
            break

    raise RuntimeError(
        "All configured cloud models failed. " + " | ".join(errors)
    )
