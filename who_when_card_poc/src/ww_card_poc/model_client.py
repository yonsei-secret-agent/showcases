from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ww_card_poc.settings import Settings


@dataclass(frozen=True)
class ModelResponse:
    content: str
    model: str
    usage: dict[str, Any]
    finish_reason: str
    raw: dict[str, Any]


class ModelClientError(RuntimeError):
    pass


class ModelClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None = None,
        seed: int | None = None,
    ) -> ModelResponse:
        api = self.settings.api
        if not api.active_api_key:
            raise ModelClientError(f"Missing API key for active backend: {api.backend}.")

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if seed is not None:
            body["seed"] = seed
        if api.backend == "openrouter":
            provider_order = [
                provider.strip()
                for provider in api.openrouter_provider_order.split(",")
                if provider.strip()
            ]
            if provider_order:
                body["provider"] = {
                    "order": provider_order,
                    "allow_fallbacks": api.openrouter_allow_fallbacks,
                }

        headers = {
            "Authorization": f"Bearer {api.active_api_key}",
            "Content-Type": "application/json",
        }
        if api.backend == "openrouter":
            if api.openrouter_http_referer:
                headers["HTTP-Referer"] = api.openrouter_http_referer
            if api.openrouter_app_title:
                headers["X-Title"] = api.openrouter_app_title

        request = Request(
            f"{api.active_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        started = time.monotonic()
        try:
            with urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ModelClientError(f"HTTP {exc.code} from model backend: {error_body}") from exc
        except URLError as exc:
            raise ModelClientError(f"Could not reach model backend: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ModelClientError("Timed out waiting for model backend.") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise ModelClientError(f"Model backend returned no choices: {payload}")
        choice = choices[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "")
        raw_usage = payload.get("usage") or {}
        usage = dict(raw_usage) if isinstance(raw_usage, dict) else {}
        usage["latency_seconds"] = round(time.monotonic() - started, 3)
        return ModelResponse(
            content=content,
            model=str(payload.get("model") or model),
            usage=usage,
            finish_reason=str(choice.get("finish_reason") or ""),
            raw=payload,
        )
