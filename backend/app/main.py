from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.config import settings
from app.database.session import get_session_factory


def create_app() -> FastAPI:
    application = FastAPI(title="Document Copilot")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Vercel-AI-UI-Message-Stream"],
    )

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"service": "document-copilot", "health": "/health", "docs": "/docs"}

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready")
    async def health_ready() -> dict[str, str]:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}

    application.include_router(auth_router)
    application.include_router(chat_router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True)
