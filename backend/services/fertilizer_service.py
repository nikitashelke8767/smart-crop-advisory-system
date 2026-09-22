class FertilizerService:
    def __init__(self):
        self.name = "fertilizer"

    def get_recommendation(self, crop: str, soil: str):
        return {"crop": crop, "soil": soil, "message": "Fertilizer service placeholder"}
