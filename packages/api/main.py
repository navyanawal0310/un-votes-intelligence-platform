from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.api.routes import router


app = FastAPI(
    title="UN Votes Intelligence Platform",
    version="1.0.0",
    description=(
        "Evidence-backed analytical API for "
        "UN voting intelligence."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "un-votes-intelligence-platform",
        "version": "1.0.0",
    }


app.include_router(router)