import sys
from pathlib import Path

# Ensure backend root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.disease_service import predict_disease


def test_predict_disease_valid_image():

    # Sample leaf image from dataset
    img_path = Path("datasets/plantvillage/Tomato/Tomato___Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B 8389.JPG")
    if not img_path.exists():
        img_path = Path(__file__).resolve().parent.parent.parent / img_path

    result = predict_disease(img_path)
    assert isinstance(result, dict)
    assert "disease" in result
    assert "confidence" in result
    assert isinstance(result["disease"], str)
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 100.0


def test_predict_disease_invalid_path():
    try:
        predict_disease("non_existent_leaf_image_12345.jpg")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "does not exist" in str(e)


def test_predict_disease_empty_bytes():
    try:
        predict_disease(b"")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()



if __name__ == "__main__":
    test_predict_disease_valid_image()
    test_predict_disease_invalid_path()
    test_predict_disease_empty_bytes()
    print("All disease service tests passed!")
