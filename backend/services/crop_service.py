class CropService:
    def __init__(self):
        self.name = "crop"

    def recommend(self, soil_data: dict):
        return {"soil_data": soil_data, "message": "Crop recommendation service placeholder"}
