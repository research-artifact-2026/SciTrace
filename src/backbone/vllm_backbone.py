"""vLLM OpenAI-compatible backbone."""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from src.backbone.base_backbone import BaseBackbone
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class VLLMBackbone(BaseBackbone):
    """Local Llama/Qwen/DeepSeek models via vLLM OpenAI API."""

    def __init__(
        self,
        model_name: str,
        base_url: str | None = None,
        max_retries: int = 3,
        tensor_parallel_size: int = 2,
        quantization: str = "awq",
        dtype: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.tensor_parallel_size = tensor_parallel_size
        self.quantization = quantization
        self.dtype = dtype
        self.max_retries = max_retries
        resolved_base = base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        api_key = os.getenv("VLLM_API_KEY", "EMPTY")
        self.client = OpenAI(base_url=resolved_base, api_key=api_key)

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

                extra_body = {}
                if top_k is not None:
                    extra_body["top_k"] = top_k
                if repetition_penalty is not None:
                    extra_body["repetition_penalty"] = repetition_penalty
                if seed is not None:
                    extra_body["seed"] = seed
                if extra_body:
                    payload["extra_body"] = extra_body

                response = self.client.chat.completions.create(
                    **payload
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                last_exc = exc
                logger.warning("vLLM call failed (attempt %s): %s", attempt + 1, exc)
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"vLLM completion failed after {self.max_retries} attempts") from last_exc
