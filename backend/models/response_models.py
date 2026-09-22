from pydantic import BaseModel


class PredictionResponse(BaseModel):
    disease: str
    confidence: float
    recommendation: str


class GenericResponse(BaseModel):
    message: str
