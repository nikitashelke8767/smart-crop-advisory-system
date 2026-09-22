from fastapi import APIRouter

router = APIRouter(prefix="/crop", tags=["crop"])


@router.get("/")
def get_crop_recommendation():
    return {"message": "Crop recommendation endpoint is ready"}
