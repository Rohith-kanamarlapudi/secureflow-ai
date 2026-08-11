from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": settings.ENV,
    }