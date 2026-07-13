"""HTTP middleware shared across features."""

from uuid import UUID, uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TrustedOriginMiddleware:
    """Reject browser cross-origin mutations for cookie-authenticated APIs."""

    def __init__(self, app: ASGIApp, allowed_origin: str) -> None:
        self.app = app
        self.allowed_origin = allowed_origin.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("method") not in {"GET", "HEAD", "OPTIONS"}:
            origin = dict(scope.get("headers", [])).get(b"origin")
            if origin is not None and origin != self.allowed_origin:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [(b"content-type", b"application/problem+json")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": (
                            b'{"title":"Forbidden origin","status":403,'
                            b'"code":"forbidden_origin"}'
                        ),
                    }
                )
                return
        await self.app(scope, receive, send)


class CorrelationIdMiddleware:
    """Propagate a valid request identifier or generate a new opaque UUID."""

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.lower().encode("ascii")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._request_id(scope)
        scope.setdefault("state", {})["correlation_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers[self.header_name] = request_id
            await send(message)

        await self.app(scope, receive, send_with_request_id)

    def _request_id(self, scope: Scope) -> str:
        raw_headers = dict(scope.get("headers", []))
        candidate = raw_headers.get(self.header_name_bytes, b"").decode("ascii", errors="ignore")
        try:
            return str(UUID(candidate))
        except ValueError:
            return str(uuid4())
