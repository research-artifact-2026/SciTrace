"""Abstract LLM backbone interface."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseBackbone(ABC):
    """Base class for SciTrace LLM backends."""

    default_temperature: float = 0.0
    default_max_tokens: int = 4096

    def completion_kwargs(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, float | int]:
        return {
            "temperature": (
                self.default_temperature if temperature is None else temperature
            ),
            "max_tokens": self.default_max_tokens if max_tokens is None else max_tokens,
        }

    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Return raw completion string."""

    def complete_json(
        self,
        messages: list[dict],
        schema_class: Type[BaseModel] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Parse JSON from completion, optionally validating with Pydantic."""
        raw = self.complete(messages, **self.completion_kwargs(temperature, max_tokens))
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.error("JSON parse failed; raw output: %s", raw[:500])
            raise
        if schema_class is not None:
            try:
                return schema_class.model_validate(data).model_dump()
            except ValidationError as exc:
                logger.error("Schema validation failed: %s", exc)
                raise
        return data
