from pathlib import Path


class DiseaseService:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or str(Path("../models/disease_model"))

    def predict(self, image_bytes: bytes):
        return {
            "status": "placeholder",
            "message": "Disease prediction model integration will be added here",
        }
