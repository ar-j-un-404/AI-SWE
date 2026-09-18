from pathlib import Path
import time

import requests
from dotenv import dotenv_values
from openai import (
    OpenAI,
    RateLimitError,
    APIError,
    APITimeoutError,
    APIConnectionError,
)


ENV_PATH = Path(__file__).parent / ".env"
CONFIG = dotenv_values(ENV_PATH)

OPENROUTER_API_KEY = CONFIG.get(
    "OPENROUTER_API_KEY"
)

OPENROUTER_MODELS = [
    "poolside/laguna-xs-2.1:free",
    "poolside/laguna-s-2.1:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

OLLAMA_MODEL = "qwen3:4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

OPENROUTER_TIMEOUT = 90
OLLAMA_TIMEOUT = 600

OPENROUTER_MAX_TOKENS = 6000
OLLAMA_NUM_PREDICT = 2048


client = None

if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        timeout=OPENROUTER_TIMEOUT,
    )


def extract_text(response):
    if response is None:
        return None

    choices = getattr(
        response,
        "choices",
        None,
    )

    if not choices:
        return None

    message = getattr(
        choices[0],
        "message",
        None,
    )

    if message is None:
        return None

    content = getattr(
        message,
        "content",
        None,
    )

    if isinstance(
        content,
        str,
    ):
        content = content.strip()

        if content:
            return content

    if isinstance(
        content,
        list,
    ):
        parts = []

        for item in content:
            if isinstance(
                item,
                dict,
            ):
                text = item.get(
                    "text"
                )

            else:
                text = getattr(
                    item,
                    "text",
                    None,
                )

            if text:
                parts.append(
                    str(text)
                )

        combined = "\n".join(
            parts
        ).strip()

        if combined:
            return combined

    return None


def is_daily_rate_limit(
    error,
):
    error_text = str(
        error
    ).lower()

    return (
        "free-models-per-day"
        in error_text
        or "x-ratelimit-remaining"
        in error_text
        and "'0'" in error_text
    )


def call_openrouter_model(
    model,
    prompt,
):
    if client is None:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software engineer "
                    "working inside an autonomous coding agent. "
                    "Follow the requested output format exactly. "
                    "Do not add unnecessary commentary."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=OPENROUTER_MAX_TOKENS,
    )

    actual_model = getattr(
        response,
        "model",
        model,
    )

    print(
        f"OpenRouter model used: {actual_model}"
    )

    text = extract_text(
        response
    )

    if not text:
        raise ValueError(
            f"Model {actual_model} "
            "returned no text content."
        )

    return text


def check_ollama():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=10,
        )

        response.raise_for_status()

        return True

    except requests.RequestException:
        return False


def call_ollama(
    prompt,
):
    print(
        f"Trying local Ollama model: "
        f"{OLLAMA_MODEL}"
    )

    if not check_ollama():
        raise RuntimeError(
            "Ollama server is not reachable at "
            "http://localhost:11434. "
            "Start Ollama before running the AI SWE."
        )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": (
            "You are a senior software engineer "
            "working inside an autonomous coding agent.\n"
            "Follow the requested output format exactly.\n"
            "Do not add unnecessary commentary.\n\n"
            + prompt
        ),
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": OLLAMA_NUM_PREDICT,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )

        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        raise RuntimeError(
            f"Ollama model {OLLAMA_MODEL} "
            f"did not finish within "
            f"{OLLAMA_TIMEOUT} seconds."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        )

    except requests.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        )

    try:
        data = response.json()

    except ValueError:
        raise RuntimeError(
            "Ollama returned invalid JSON."
        )

    text = data.get(
        "response",
        "",
    )

    if not isinstance(
        text,
        str,
    ):
        text = str(
            text
        )

    text = text.strip()

    if not text:
        raise ValueError(
            f"Ollama model {OLLAMA_MODEL} "
            "returned no text content."
        )

    print(
        f"Local model used: {OLLAMA_MODEL}"
    )

    return text


def ask_llm(
    prompt,
    retries_per_model=1,
):
    if not isinstance(
        prompt,
        str,
    ):
        prompt = str(
            prompt
        )

    prompt = prompt.strip()

    if not prompt:
        raise ValueError(
            "LLM prompt cannot be empty."
        )

    last_error = None
    daily_limit_reached = False

    if client is not None:
        for model in OPENROUTER_MODELS:
            if daily_limit_reached:
                break

            for attempt in range(
                1,
                retries_per_model + 1,
            ):
                try:
                    print(
                        f"Trying {model} "
                        f"(attempt {attempt}/"
                        f"{retries_per_model})"
                    )

                    return call_openrouter_model(
                        model,
                        prompt,
                    )

                except RateLimitError as error:
                    last_error = error

                    print(
                        f"{model} is rate-limited."
                    )

                    if is_daily_rate_limit(
                        error
                    ):
                        daily_limit_reached = True

                        print(
                            "OpenRouter daily free quota "
                            "is exhausted."
                        )

                        break

                except APITimeoutError as error:
                    last_error = error

                    print(
                        f"{model} timed out."
                    )

                except APIConnectionError as error:
                    last_error = error

                    print(
                        f"{model} connection failed: "
                        f"{error}"
                    )

                except APIError as error:
                    last_error = error

                    print(
                        f"{model} API error: "
                        f"{error}"
                    )

                    if is_daily_rate_limit(
                        error
                    ):
                        daily_limit_reached = True

                        print(
                            "OpenRouter daily free quota "
                            "is exhausted."
                        )

                        break

                except Exception as error:
                    last_error = error

                    print(
                        f"{model} failed: "
                        f"{error}"
                    )

                if attempt < retries_per_model:
                    time.sleep(
                        1
                    )

    else:
        print(
            "OpenRouter API key not configured."
        )

    print(
        "Falling back to local Ollama..."
    )

    try:
        return call_ollama(
            prompt
        )

    except Exception as error:
        last_error = error

    raise RuntimeError(
        "All coding models failed, "
        "including local Ollama. "
        f"Last error: {last_error}"
    )


def test_openrouter():
    if client is None:
        print(
            "OpenRouter is not configured."
        )

        return

    print(
        "Testing OpenRouter..."
    )

    try:
        result = ask_llm(
            "Reply with exactly: working",
            retries_per_model=1,
        )

        print(
            result
        )

    except Exception as error:
        print(
            f"OpenRouter/Ollama test failed: "
            f"{error}"
        )


def test_ollama_only():
    print(
        "Testing Ollama directly..."
    )

    try:
        result = call_ollama(
            "Reply with exactly: working"
        )

        print(
            result
        )

    except Exception as error:
        print(
            f"Ollama test failed: {error}"
        )


if __name__ == "__main__":
    print(
        "=" * 60
    )

    print(
        "AI SWE LLM TEST"
    )

    print(
        "=" * 60
    )

    print()

    try:
        result = ask_llm(
            "Reply with exactly: coding model working",
            retries_per_model=1,
        )

        print()
        print(
            "=" * 60
        )

        print(
            "RESULT"
        )

        print(
            "=" * 60
        )

        print(
            result
        )

    except Exception as error:
        print()
        print(
            "=" * 60
        )

        print(
            "FAILED"
        )

        print(
            "=" * 60
        )

        print(
            error
        )