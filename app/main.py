from fastapi import FastAPI

from app.api.pull_requests import router as pull_requests_router


app = FastAPI(title="AI GitHub Engineering Assistant")
app.include_router(pull_requests_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return the service health status."""
    return {
        "status": "ok",
        "service": "ai-github-engineering-assistant",
    }
