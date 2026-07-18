"""Explicit image-generation adapter for user-requested business visuals."""

import base64
import binascii
from typing import Protocol

import httpx


class ImageGenerationProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Return a browser-ready image data URL."""
        ...


class OpenAIImageGenerationProvider:
    """Small Image API adapter; generated images never become RAG evidence."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def generate(self, prompt: str) -> str:
        safe_prompt = (
            "Create a polished, realistic business visual for an Indian MSME founder. "
            "Do not include government emblems, official logos, certificates, claims of "
            "eligibility, or legible text. User request: "
            f"{prompt}"
        )
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"{self._base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "prompt": safe_prompt,
                        "size": "1024x1024",
                        "quality": "low",
                        "output_format": "webp",
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("image generation failed") from exc

        try:
            encoded = payload["data"][0]["b64_json"]
            if not isinstance(encoded, str):
                raise TypeError
            decoded = base64.b64decode(encoded, validate=True)
        except (KeyError, IndexError, TypeError, binascii.Error) as exc:
            raise RuntimeError("image generation returned invalid data") from exc
        if not decoded or len(decoded) > 15_000_000:
            raise RuntimeError("image generation returned invalid data")
        return f"data:image/webp;base64,{encoded}"
