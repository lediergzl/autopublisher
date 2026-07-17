from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine
from app.core.middleware import audit_middleware

from app.users.models import Base
from app.telegram.models import TelegramSession  # noqa: F401 (registra tabla)
from app.communities.models import Community  # noqa: F401
from app.content.models import Post  # noqa: F401
from app.campaigns.models import Campaign, CampaignCommunity  # noqa: F401
from app.analytics.models import ActivityLog  # noqa: F401

from app.users.router import router as users_router
from app.telegram.router import router as telegram_router
from app.communities.router import router as communities_router
from app.content.router import router as content_router
from app.campaigns.router import router as campaigns_router
from app.analytics.router import router as analytics_router

app = FastAPI(title="AutoPublisher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar al dominio de la Mini App en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(audit_middleware)

app.include_router(users_router, prefix="/users")
app.include_router(telegram_router, prefix="/auth")
app.include_router(communities_router, prefix="/communities")
app.include_router(content_router, prefix="/posts")
app.include_router(campaigns_router, prefix="/campaigns")
app.include_router(analytics_router, prefix="/analytics")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}
