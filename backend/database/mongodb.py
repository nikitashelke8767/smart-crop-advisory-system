class MongoDBConnection:
    def __init__(self, uri: str | None = None):
        self.uri = uri

    def connect(self):
        return {"status": "not_configured", "message": "MongoDB connection placeholder"}
