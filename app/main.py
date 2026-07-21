from fastapi import FastAPI


app = FastAPI(title="AI GitHub Engineering Assistant")


@app.get("/health")
async def health() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}
