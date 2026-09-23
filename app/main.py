"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Demo 启动时自动建表；生产环境应使用 Alembic migration。
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Enterprise HR Agent", version="1.0.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
