class WeatherService:
    def __init__(self):
        self.name = "weather"

    def get_forecast(self, location: str):
        return {"location": location, "message": "Weather service placeholder"}
