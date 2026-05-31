"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import get_settings
from app.core.exception import register_exception_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    yield
    print(f"👋 {settings.APP_NAME} 已关闭")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} API is running",
        "version": settings.APP_VERSION,
    }
