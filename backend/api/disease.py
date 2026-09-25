"""
FastAPI Disease Prediction Router Module.

Provides endpoint:
POST /predict-disease

Uploads an image file and returns predicted plant disease and confidence score.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

# Ensure robust imports whether executing from backend or project root
try:
    from services.disease_service import predict_disease
    from utils.logger import logger
except ImportError:
    from backend.services.disease_service import predict_disease
    from backend.utils.logger import logger


router = APIRouter(tags=["disease"])

# Allowed image MIME types and file extensions
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


class DiseasePredictionResponse(BaseModel):
    """
    Response schema for plant disease prediction endpoint.
    """

    disease: str = Field(
        ...,
        description="Predicted crop disease class name",
        example="Tomato___Early_blight",
    )
    confidence: float = Field(
        ...,
        description="Prediction confidence percentage (0.0 to 100.0)",
        example=96.4,
    )


def validate_image_file(file: UploadFile, file_contents: bytes) -> None:
    """
    Validates uploaded file MIME type, extension, and byte payload.
    """
    # 1. Non-empty check
    if not file_contents or len(file_contents) == 0:
        logger.warning(f"[API /predict-disease] Empty file uploaded: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please provide a valid image.",
        )

    # 2. File size check
    if len(file_contents) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"[API /predict-disease] File size exceeds limit: {len(file_contents)} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed limit of 10MB.",
        )

    # 3. MIME type check
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"[API /predict-disease] Invalid Content-Type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Allowed formats: JPEG, PNG, WEBP, BMP.",
        )

    # 4. File extension check (fallback validation if content_type is generic application/octet-stream)
    filename = (file.filename or "").lower()
    if filename and "." in filename:
        ext = f".{filename.rsplit('.', 1)[-1]}"
        if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"[API /predict-disease] Invalid file extension: {ext}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: .jpg, .jpeg, .png, .webp, .bmp.",
            )


@router.post(
    "/predict-disease",
    response_model=DiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Plant Disease from Image Upload",
    description="Upload a leaf image file to receive predicted disease class and confidence percentage.",
)
@router.post(
    "/predict",
    response_model=DiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def predict_crop_disease(image: UploadFile = File(..., description="Leaf image file (JPEG, PNG, WEBP)")) -> Dict[str, Any]:
    """
    FastAPI endpoint handler for crop disease prediction.
    """
    logger.info(f"[API /predict-disease] Received request. Filename: '{image.filename}', Content-Type: '{image.content_type}'")

    try:
        # Read uploaded image bytes asynchronously
        contents = await image.read()
    except Exception as e:
        logger.error(f"[API /predict-disease] Failed to read uploaded file payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image payload: {str(e)}",
        )

    # Validate file payload
    validate_image_file(image, contents)

    # Execute disease model prediction
    try:
        result = predict_disease(contents)
        logger.info(f"[API /predict-disease] Success: {result['disease']} ({result['confidence']}%)")
        return result
    except ValueError as val_err:
        logger.warning(f"[API /predict-disease] Image processing error: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unreadable image file: {str(val_err)}",
        )
    except Exception as err:
        logger.error(f"[API /predict-disease] Internal prediction error: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the disease prediction.",
        )
