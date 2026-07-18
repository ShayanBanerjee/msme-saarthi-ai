"""Image generation adapter tests."""

import asyncio
import base64

import httpx

from app.agents.chat.image_provider import OpenAIImageGenerationProvider


def test_image_provider_returns_validated_data_url_and_adds_safety_context() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request=request, payload=request.read().decode())
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(b"synthetic-webp").decode()}]},
        )

    provider = OpenAIImageGenerationProvider(
        api_key="synthetic-key",
        model="gpt-image-2",
        base_url="https://api.example.test/v1",
        timeout_seconds=20,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(provider.generate("A food-processing workshop"))

    assert result.startswith("data:image/webp;base64,")
    assert "government emblems" in str(captured["payload"])
    assert "A food-processing workshop" in str(captured["payload"])


def test_image_provider_rejects_invalid_provider_data() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json={"data": [{"b64_json": "not base64!"}]})

    provider = OpenAIImageGenerationProvider(
        api_key="synthetic-key",
        model="gpt-image-2",
        base_url="https://api.example.test/v1",
        timeout_seconds=20,
        transport=httpx.MockTransport(handler),
    )

    try:
        asyncio.run(provider.generate("A valid prompt"))
    except RuntimeError as exc:
        assert str(exc) == "image generation returned invalid data"
    else:
        raise AssertionError("invalid image data should fail closed")
