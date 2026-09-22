from fastapi import APIRouter

router = APIRouter(prefix="/fertilizer", tags=["fertilizer"])


@router.get("/")
def get_fertilizer_recommendation():
    return {"message": "Fertilizer recommendation endpoint is ready"}
