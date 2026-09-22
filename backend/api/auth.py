from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login():
    return {"message": "Authentication endpoint is ready"}
