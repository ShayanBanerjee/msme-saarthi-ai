"""Provider-native Responses SSE adapter tests."""

import asyncio
import json

import httpx

from app.agents.chat.provider import LLMGenerationRequest, OpenAIResponsesProvider


def test_openai_adapter_yields_native_text_deltas() -> None:
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload["stream"] is True
            stream = (
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"First "}\n\n'
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"delta"}\n\n'
                'event: response.completed\n'
                'data: {"type":"response.completed"}\n\n'
            )
            return httpx.Response(200, text=stream, headers={"content-type": "text/event-stream"})

        provider = OpenAIResponsesProvider(
            api_key="synthetic-key",
            model="synthetic-model",
            base_url="https://api.example.invalid/v1",
            timeout_seconds=5,
            transport=httpx.MockTransport(handler),
        )
        deltas = [
            delta
            async for delta in provider.stream(
                LLMGenerationRequest(
                    user_message="Synthetic streaming request",
                    prompt_version="synthetic.v1",
                )
            )
        ]

        assert deltas == ["First ", "delta"]

    asyncio.run(scenario())
