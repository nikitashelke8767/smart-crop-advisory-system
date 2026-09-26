"""MongoDB Database Connection and Collection Accessors for Smart Crop Advisory System.

Provides reusable client and database connection management using pymongo
and environment variables.
"""

import logging
import os
from typing import Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Reusable MongoDB connection manager."""

    # Collection constants
    USERS_COLLECTION = "users"
    ADVISORY_COLLECTION = "advisory"
    DISEASE_PREDICTIONS_COLLECTION = "disease_predictions"

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
    ):
        """Initialize MongoDB configuration from arguments or environment variables.

        Args:
            uri: MongoDB connection URI string (optional).
            db_name: Target database name (optional).
        """
        self.uri = uri or os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
        self.db_name = (
            db_name
            or os.getenv("MONGODB_DB_NAME")
            or os.getenv("MONGO_DB_NAME")
            or "smart_crop_advisory"
        )
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> Database:
        """Establish connection to MongoDB and return the database instance.

        Returns:
            Database: The connected pymongo Database instance.
        """
        if self._client is None:
            try:
                logger.info("Connecting to MongoDB at %s...", self.uri.split("@")[-1])
                self._client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=int(os.getenv("MONGODB_TIMEOUT_MS", "5000")),
                )
                # Verify connection with ping
                self._client.admin.command("ping")
                logger.info("Successfully connected to MongoDB database: %s", self.db_name)
            except ConnectionFailure as e:
                logger.warning(
                    "MongoDB ping failed (%s). Client initialized, but server might be unreachable.",
                    e,
                )
            except PyMongoError as e:
                logger.error("MongoDB connection error: %s", e)
                raise

            self._db = self._client[self.db_name]

        return self._db

    def get_database(self) -> Database:
        """Get the active database instance, connecting if not already connected."""
        if self._db is None:
            return self.connect()
        return self._db

    def get_client(self) -> MongoClient:
        """Get the MongoClient instance, connecting if not already connected."""
        if self._client is None:
            self.connect()
        return self._client

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name from the current database."""
        db = self.get_database()
        return db[name]

    # Pre-configured collection accessors
    @property
    def users(self) -> Collection:
        """Access the 'users' collection."""
        return self.get_collection(self.USERS_COLLECTION)

    @property
    def advisory(self) -> Collection:
        """Access the 'advisory' collection."""
        return self.get_collection(self.ADVISORY_COLLECTION)

    @property
    def disease_predictions(self) -> Collection:
        """Access the 'disease_predictions' collection."""
        return self.get_collection(self.DISEASE_PREDICTIONS_COLLECTION)

    def get_users_collection(self) -> Collection:
        """Method helper for the 'users' collection."""
        return self.users

    def get_advisory_collection(self) -> Collection:
        """Method helper for the 'advisory' collection."""
        return self.advisory

    def get_disease_predictions_collection(self) -> Collection:
        """Method helper for the 'disease_predictions' collection."""
        return self.disease_predictions

    def health_check(self) -> dict:
        """Check MongoDB connectivity status.

        Returns:
            dict: Status summary of connection.
        """
        try:
            client = self.get_client()
            client.admin.command("ping")
            return {
                "status": "connected",
                "database": self.db_name,
                "message": "MongoDB is connected and reachable",
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "database": self.db_name,
                "error": str(e),
                "message": "MongoDB is unreachable",
            }

    def close(self) -> None:
        """Close the MongoDB client connection."""
        if self._client is not None:
            logger.info("Closing MongoDB connection.")
            self._client.close()
            self._client = None
            self._db = None


# Singleton instance for application-wide reuse
db_connection = MongoDBConnection()


# Convenience functions
def get_database() -> Database:
    """Dependency / helper to get database instance."""
    return db_connection.get_database()


def get_db() -> Database:
    """Alias for get_database()."""
    return db_connection.get_database()


def get_users_collection() -> Collection:
    """Helper to get users collection."""
    return db_connection.users


def get_advisory_collection() -> Collection:
    """Helper to get advisory collection."""
    return db_connection.advisory


def get_disease_predictions_collection() -> Collection:
    """Helper to get disease_predictions collection."""
    return db_connection.disease_predictions


def close_mongo_connection() -> None:
    """Helper to close default connection on shutdown."""
    db_connection.close()
