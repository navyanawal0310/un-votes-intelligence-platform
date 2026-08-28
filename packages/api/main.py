from fastapi import FastAPI

from packages.api.routes import router


app = FastAPI(
    title="UN Votes Intelligence Platform",
    version="1.0.0",
    description=(
        "Evidence-backed analytical API for "
        "UN voting intelligence."
    ),
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "un-votes-intelligence-platform",
        "version": "1.0.0",
    }


app.include_router(router)