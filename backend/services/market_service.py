class MarketService:
    def __init__(self):
        self.name = "market"

    def get_insights(self, commodity: str):
        return {"commodity": commodity, "message": "Market service placeholder"}
