from fastapi import FastAPI
from backend.config import settings
from backend.api import disease, weather, fertilizer, crop, market, auth

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(disease.router, prefix=settings.api_prefix)
app.include_router(weather.router, prefix=settings.api_prefix)
app.include_router(fertilizer.router, prefix=settings.api_prefix)
app.include_router(crop.router, prefix=settings.api_prefix)
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)


@app.get("/")
def health_check():
    return {"message": "Smart Crop Advisory System API is running"}
