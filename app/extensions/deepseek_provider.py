"""Official DeepSeek vision provider for hcaptcha-challenger's ChatProvider protocol."""

import asyncio
import base64
import json
import mimetypes
import time
from pathlib import Path
from typing import Any, TypeVar

import httpx
from loguru import logger
from pydantic import BaseModel, ValidationError

ResponseT = TypeVar("ResponseT", bound=BaseModel)
API_ENDPOINT = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"  # Official alias for DeepSeek-V4.1-Flash-1017 (2026-11-04).


def _schema_example(schema: dict, definitions: dict) -> Any:
    """Give JSON mode a shape example, including referenced Pydantic definitions."""
    if "$ref" in schema:
        return _schema_example(definitions[schema["$ref"].rsplit("/", 1)[-1]], definitions)
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        return _schema_example(schema["anyOf"][0], definitions)
    kind = schema.get("type")
    if kind == "object":
        return {
            name: _schema_example(value, definitions)
            for name, value in schema.get("properties", {}).items()
            if name in schema.get("required", [])
        }
    if kind == "array":
        return [_schema_example(schema["items"], definitions)] * max(1, schema.get("minItems", 1))
    return {"string": "answer", "integer": 500, "number": 500, "boolean": True}.get(kind)


class DeepSeekProvider:
    def __init__(self, settings: Any):
        self._settings = settings
        self._response: dict | None = None

    async def generate_with_images(
        self,
        *,
        images: list[Path],
        response_schema: type[ResponseT],
        user_prompt: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> ResponseT:
        if error := self._settings.llm_configuration_error:
            raise RuntimeError(error)
        schema = response_schema.model_json_schema()
        system = "\n\n".join(
            part
            for part in (
                description,
                "Return one JSON object containing the actual answer. Do not return a schema. "
                "Follow this JSON Schema: " + json.dumps(schema, ensure_ascii=False),
                "Example of the required JSON shape (replace every example value with your "
                "answer): " + json.dumps(_schema_example(schema, schema.get("$defs", {}))),
            )
            if part
        )
        content = []
        for image in images:
            path = Path(image)
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}
            )
        content.append({"type": "text", "text": user_prompt or "Answer the image instruction."})
        spatial = bool(set(schema.get("properties", {})) & {"points", "paths"})
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "enabled" if spatial else "disabled"},
            "max_tokens": 8192 if spatial else 1024,
        }
        if spatial:
            payload["reasoning_effort"] = "low"
        timeout = self._settings.DEEPSEEK_REQUEST_TIMEOUT_SECONDS
        headers = {"Authorization": f"Bearer {self._settings.DEEPSEEK_API_KEY.get_secret_value()}"}
        self._response = None
        # Only transient failures are retried. Authentication, credit and model errors stop here.
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=15)) as client:
            for attempt in range(1, 3):
                started = time.monotonic()
                try:
                    async with asyncio.timeout(timeout):
                        response = await client.post(API_ENDPOINT, headers=headers, json=payload)
                    if response.is_error:
                        status = response.status_code
                        request_id = response.headers.get("x-request-id", "unknown")
                        if status != 429 and status < 500:
                            raise RuntimeError(
                                f"DeepSeek API HTTP {status} (request_id={request_id}); "
                                "check DEEPSEEK_API_KEY, account balance and model access"
                            )
                        raise ValueError(f"DeepSeek API HTTP {status} (request_id={request_id})")
                    data = response.json()
                    choices = data.get("choices") or []
                    if not choices:
                        raise ValueError("DeepSeek returned no completion choices")
                    choice = choices[0]
                    if choice.get("finish_reason") != "stop":
                        raise ValueError(
                            f"DeepSeek completion incomplete: {choice.get('finish_reason')}"
                        )
                    text = (choice.get("message", {}).get("content") or "").strip()
                    if not text:
                        raise ValueError("DeepSeek JSON output is blank")
                    parsed = response_schema.model_validate_json(text, strict=True)
                    self._response = {
                        "model": data.get("model", MODEL),
                        "parsed": parsed.model_dump(mode="json"),
                        "usage": data.get("usage") or {},
                    }
                    logger.info(
                        "DeepSeek response | schema={} | attempt={} | seconds={:.1f} | tokens={}",
                        response_schema.__name__,
                        attempt,
                        time.monotonic() - started,
                        self._response["usage"].get("total_tokens", "unknown"),
                    )
                    return parsed
                except (httpx.RequestError, TimeoutError, ValueError) as err:
                    # Avoid logging raw response bodies (or embedded credentials in transport URLs).
                    reason = (
                        "invalid JSON/schema"
                        if isinstance(err, ValidationError)
                        else str(err) if type(err) is ValueError else type(err).__name__
                    )
                    if attempt == 2:
                        raise RuntimeError(
                            f"DeepSeek request failed after 2 attempts ({reason}); "
                            "inspect API status, network and output token limit"
                        ) from None
                    logger.warning(
                        "DeepSeek transient failure | attempt={} | reason={}", attempt, reason
                    )
                    await asyncio.sleep(1)
        raise RuntimeError("DeepSeek provider exhausted its request budget")

    def cache_response(self, path: Path) -> None:
        if self._response is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self._response, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as err:
            logger.warning("Unable to cache DeepSeek response | error_type={}", type(err).__name__)


def install_deepseek_provider(settings: Any) -> None:
    # hcaptcha-challenger 0.19 exposes provider injection but AgentV does not forward it.
    # Change only its default factory; Google SDK clients and explicit custom providers are untouched.
    from hcaptcha_challenger.tools.internal.base import Reasoner

    def create_provider(reasoner):
        return DeepSeekProvider(settings)

    Reasoner._create_default_provider = create_provider
    logger.info("Official DeepSeek provider active | model={}", MODEL)
