from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/")
def get_weather():
    return {"message": "Weather data endpoint is ready"}
