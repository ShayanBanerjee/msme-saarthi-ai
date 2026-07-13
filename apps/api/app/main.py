"""FastAPI application factory and default ASGI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.database import Base, create_database
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware, TrustedOriginMiddleware
from app.features.auth.crypto import CredentialProtector, DataCipher
from app.features.auth.repository import SqlAlchemyAuthRepository
from app.features.auth.router import router as auth_router
from app.features.auth.service import AuthService
from app.features.chat import create_default_chat_service
from app.features.chat.router import router as chat_router
from app.features.health.router import router as health_router
from app.retrieval.embedding import DeterministicHashEmbeddingProvider
from app.retrieval.opensearch import HttpOpenSearchClient, OpenSearchHybridRetriever


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application instance with explicit, testable dependencies."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    logger = get_logger(__name__)
    engine = None
    session_factory = None
    search_client = None
    auth_service = None
    if resolved_settings.database_url and resolved_settings.data_encryption_key:
        engine, session_factory = create_database(resolved_settings.database_url)
        cipher = DataCipher(
            key_base64=resolved_settings.data_encryption_key.get_secret_value(),
            key_version=resolved_settings.data_encryption_key_version,
        )
        auth_service = AuthService(
            repository=SqlAlchemyAuthRepository(session_factory),
            cipher=cipher,
            credentials=CredentialProtector(),
            idle_minutes=resolved_settings.session_idle_minutes,
            absolute_hours=resolved_settings.session_absolute_hours,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("application_started", extra={"environment": resolved_settings.environment})
        if engine is not None and resolved_settings.environment == "test":
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
        yield
        if engine is not None:
            await engine.dispose()
        if search_client is not None:
            await search_client.aclose()
        logger.info("application_stopped")

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.auth_service = auth_service
    application.state.database_engine = engine
    retriever = None
    if resolved_settings.retrieval_provider == "opensearch":
        search_client = httpx.AsyncClient(timeout=10.0)
        retriever = OpenSearchHybridRetriever(
            client=HttpOpenSearchClient(
                client=search_client,
                base_url=resolved_settings.opensearch_url,
            ),
            embedder=DeterministicHashEmbeddingProvider(),
            index=resolved_settings.opensearch_index,
        )
    chat_service, chat_repository = create_default_chat_service(
        settings=resolved_settings,
        session_factory=session_factory,
        retriever_override=retriever,
    )
    application.state.chat_service = chat_service
    application.state.chat_repository = chat_repository
    application.add_middleware(
        CorrelationIdMiddleware, header_name=resolved_settings.request_id_header
    )
    application.add_middleware(TrustedOriginMiddleware, allowed_origin=resolved_settings.web_origin)
    register_exception_handlers(application)
    application.include_router(health_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(auth_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(chat_router, prefix=resolved_settings.api_v1_prefix)
    return application


app = create_app()
