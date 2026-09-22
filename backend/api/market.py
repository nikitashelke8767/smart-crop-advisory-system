from fastapi import APIRouter

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/")
def get_market_data():
    return {"message": "Market insights endpoint is ready"}
