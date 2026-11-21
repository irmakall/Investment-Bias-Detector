"""Gemini call for one note (REQ-011). All Gemini-specific code lives here (NFR-008).

Usage (quick manual check):
    export GEMINI_API_KEY=...            # from Google AI Studio, never committed
    export GEMINI_MODEL=...              # exact model ID copied from AI Studio
    python -m src.llm.gemini "Down 30% but not selling until I'm back to even."

analyze() never raises. It returns either
    {"result": {...Analysis fields...}, **meta}   or   {"error": "...", **meta}
so a failed note never stops an eval run (NFR-009).
"""

import json
import os
import sys
import time

from google import genai
from google.genai import types
from pydantic import ValidationError

from src.data.split import SEED
from src.llm.prompt import SYSTEM_PROMPT, build_user_message
from src.llm.schema import Analysis

MAX_ATTEMPTS = 2   # first try + one retry (REQ-011)
TIMEOUT_MS = 60_000   # a call that takes longer than this is reported as an error instead of hanging


def get_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY (Google AI Studio -> API keys).")
    # One HTTP attempt per call: our own loop decides about retries, so a 429 shows up
    # as an error at once instead of silent backoff waits inside the SDK.
    options = types.HttpOptions(timeout=TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=1))
    return genai.Client(api_key=key, http_options=options)


def get_model() -> str:
    """The model ID comes from the environment: Gemini model names change often."""
    model = os.environ.get("GEMINI_MODEL")
    if not model:
        raise RuntimeError("Set GEMINI_MODEL to the exact model ID shown in Google AI Studio.")
    return model


def build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0,                       # as deterministic as the API allows (NFR-002)
        seed=SEED,
        response_mime_type="application/json",
        response_schema=Analysis,            # the SDK sends Analysis' JSON schema to Gemini
    )


def analyze(text: str, client=None, model: str | None = None) -> dict:
    """Analyze one note. On invalid output, retry once with the validation error as feedback.

    Why feedback instead of a plain retry: with temperature 0, sending the exact same
    request again would most likely return the exact same invalid answer.
    """
    client = client or get_client()
    model = model or get_model()
    config = build_config()
    contents = [types.Content(role="user", parts=[types.Part(text=build_user_message(text))])]
    meta = {"model": model, "attempts": 0, "latency_s": 0.0, "input_tokens": 0, "output_tokens": 0}
    last_error = ""

    for _ in range(MAX_ATTEMPTS):
        meta["attempts"] += 1
        start = time.perf_counter()
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:                          # network, quota (429), bad model ID ...
            meta["latency_s"] += time.perf_counter() - start
            return {"error": f"API call failed: {type(e).__name__}: {e}", **meta}
        meta["latency_s"] += time.perf_counter() - start

        usage = response.usage_metadata
        if usage:
            meta["input_tokens"] += usage.prompt_token_count or 0
            meta["output_tokens"] += (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)

        raw = response.text or ""
        try:
            return {"result": Analysis.model_validate_json(raw).model_dump(), **meta}
        except ValidationError as e:
            last_error = str(e)
            contents += [
                types.Content(role="model", parts=[types.Part(text=raw)]),
                types.Content(role="user", parts=[types.Part(
                    text=f"Your answer was invalid:\n{last_error}\nReturn a corrected JSON object.")]),
            ]

    return {"error": f"Invalid output after {MAX_ATTEMPTS} attempts: {last_error}", **meta}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python -m src.llm.gemini "note text"')
    print(json.dumps(analyze(sys.argv[1]), indent=2))
