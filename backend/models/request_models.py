from pydantic import BaseModel


class DiseasePredictionRequest(BaseModel):
    image_url: str | None = None


class CropRecommendationRequest(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
