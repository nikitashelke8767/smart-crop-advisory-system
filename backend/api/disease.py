from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/disease", tags=["disease"])


@router.post("/predict")
async def predict_disease(image: UploadFile = File(...)):
    return {
        "message": "Disease prediction endpoint is ready",
        "filename": image.filename,
    }
