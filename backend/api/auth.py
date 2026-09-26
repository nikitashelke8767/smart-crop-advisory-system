"""Authentication API Router for Smart Crop Advisory System.

Handles user registration, login authentication, password verification,
and MongoDB user persistence.
"""

from datetime import datetime, timezone
import logging
import re
from typing import Optional
import bcrypt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

try:
    from backend.database.mongodb import get_users_collection
except ImportError:
    from database.mongodb import get_users_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MOBILE_REGEX = re.compile(r"^\+?[0-9]{10,14}$")


class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    name: str = Field(..., min_length=2, max_length=100, description="Full Name of the user")
    email: str = Field(..., description="Email address")
    mobile: str = Field(..., description="Mobile phone number")
    password: str = Field(..., min_length=6, max_length=128, description="Password")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format")
        return cleaned

    @field_validator("mobile")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        cleaned = re.sub(r"[\s\-]", "", value)
        if not MOBILE_REGEX.match(cleaned):
            raise ValueError("Invalid mobile number format. Must contain 10 to 14 digits")
        if cleaned.startswith("+91") and len(cleaned) == 13:
            cleaned = cleaned[3:]
        elif cleaned.startswith("0") and len(cleaned) == 11:
            cleaned = cleaned[1:]
        if len(cleaned) < 10:
            raise ValueError("Mobile number must have at least 10 digits")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value


class RegisterResponse(BaseModel):
    """Schema for successful registration response."""

    message: str


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format")
        return cleaned


class LoginResponse(BaseModel):
    """Schema for user login response."""

    message: str
    user_name: str


def hash_password(plain_password: str) -> str:
    """Hash password securely using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error("Error verifying password: %s", e)
        return False


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new farmer/user after validating email, phone, and uniqueness.",
)
def register(request: RegisterRequest):
    """Register a new user with hashed password into MongoDB."""
    try:
        users_col = get_users_collection()
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check MongoDB connection.",
        )

    # Check for duplicate email
    if users_col.find_one({"email": request.email}):
        logger.warning("Registration rejected: Duplicate email %s", request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Check for duplicate mobile
    if users_col.find_one({"mobile": request.mobile}):
        logger.warning("Registration rejected: Duplicate mobile %s", request.mobile)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number is already registered",
        )

    # Hash password using bcrypt
    hashed_pwd = hash_password(request.password)

    # Prepare user document
    user_doc = {
        "name": request.name,
        "email": request.email,
        "mobile": request.mobile,
        "password": hashed_pwd,
        "role": "farmer",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    try:
        users_col.insert_one(user_doc)
        logger.info("Successfully registered user with email: %s", request.email)
    except Exception as e:
        logger.error("Failed to insert user into MongoDB: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to a database error",
        )

    return {"message": "Registration successful"}


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticates user by email and password, returning confirmation and user name.",
)
def login(request: LoginRequest):
    """Authenticate a user using email and password."""
    try:
        users_col = get_users_collection()
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check MongoDB connection.",
        )

    # Find user by email
    user = users_col.find_one({"email": request.email})
    if not user:
        logger.warning("Login failed: User not found with email %s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    stored_password = user.get("password")
    if not stored_password or not verify_password(request.password, stored_password):
        logger.warning("Login failed: Incorrect password for email %s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_name = user.get("name", "Farmer")
    logger.info("Login successful for user: %s (%s)", user_name, request.email)

    return {
        "message": "Login successful",
        "user_name": user_name,
    }
