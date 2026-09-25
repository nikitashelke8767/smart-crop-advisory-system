"""
API Integration Tests for FastAPI Disease Prediction Endpoint (POST /predict-disease).
"""

import sys
from pathlib import Path

# Ensure backend root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.disease import router

# Initialize FastAPI app with disease router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_predict_disease_api_success():
    # Sample leaf image from dataset
    img_path = Path("datasets/plantvillage/Tomato/Tomato___Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B 8389.JPG")
    if not img_path.exists():
        img_path = Path(__file__).resolve().parent.parent.parent / img_path

    assert img_path.exists(), f"Test image not found at {img_path}"

    with open(img_path, "rb") as f:
        files = {"image": ("test_leaf.jpg", f, "image/jpeg")}
        response = client.post("/predict-disease", files=files)

    print("API Response Status Code:", response.status_code)
    print("API Response Body:", response.json())

    assert response.status_code == 200
    data = response.json()
    assert "disease" in data
    assert "confidence" in data
    assert isinstance(data["disease"], str)
    assert isinstance(data["confidence"], float)
    assert 0.0 <= data["confidence"] <= 100.0


def test_predict_disease_api_empty_file():
    files = {"image": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/predict-disease", files=files)
    print("Empty file API response status:", response.status_code)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_predict_disease_api_unsupported_mime():
    files = {"image": ("test.txt", b"Hello World text file", "text/plain")}
    response = client.post("/predict-disease", files=files)
    print("Unsupported MIME API response status:", response.status_code)
    assert response.status_code == 415
    assert "unsupported" in response.json()["detail"].lower()


if __name__ == "__main__":
    test_predict_disease_api_success()
    test_predict_disease_api_empty_file()
    test_predict_disease_api_unsupported_mime()
    print("All FastAPI disease endpoint integration tests passed successfully!")
