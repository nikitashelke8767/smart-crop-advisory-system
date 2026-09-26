from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from backend.config import settings
    from backend.api import disease, weather, fertilizer, crop, market, auth
except ImportError:
    from config import settings
    from api import disease, weather, fertilizer, crop, market, auth

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Allow Flutter Web (and any origin in dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(disease.router, prefix=settings.api_prefix)
app.include_router(weather.router, prefix=settings.api_prefix)
app.include_router(fertilizer.router, prefix=settings.api_prefix)
app.include_router(crop.router, prefix=settings.api_prefix)
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)


@app.get("/")
@app.get("/health")
@app.get(f"{settings.api_prefix}/health")
def health_check():
    return {
        "status": "ok",
        "message": "Smart Crop Advisory System API is running"
    }

