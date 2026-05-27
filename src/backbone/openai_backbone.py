"""OpenAI API backbone (GPT-4o)."""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from src.backbone.base_backbone import BaseBackbone
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class OpenAIBackbone(BaseBackbone):
    """GPT-4o via OpenAI SDK with exponential backoff retries."""

    def __init__(self, model_name: str = "gpt-4o", max_retries: int = 3) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to your environment or create a .env file from .env.example."
            )
        self.model_name = model_name
        self.max_retries = max_retries
        self.client = OpenAI(api_key=api_key)

    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 4096,
        top_p: float | None = None,
        top_k: int | None = None,
        repetition_penalty: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        seed: int | None = None,
    ) -> str:
        delay = 2.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if top_p is not None:
                    payload["top_p"] = top_p
                if presence_penalty is not None:
                    payload["presence_penalty"] = presence_penalty
                if frequency_penalty is not None:
                    payload["frequency_penalty"] = frequency_penalty
                if seed is not None:
                    payload["seed"] = seed

                response = self.client.chat.completions.create(
                    **payload
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                # Some GPT-4o runtimes only accept max_completion_tokens.
                if "max_completion_tokens" in str(exc):
                    token_payload = dict(payload)
                    token_payload.pop("max_tokens", None)
                    token_payload["max_completion_tokens"] = max_tokens
                    response = self.client.chat.completions.create(**token_payload)
                    return response.choices[0].message.content or ""
                last_exc = exc
                logger.warning("OpenAI call failed (attempt %s): %s", attempt + 1, exc)
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"OpenAI completion failed after {self.max_retries} attempts") from last_exc
