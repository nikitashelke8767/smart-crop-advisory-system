"""
Verification Test Script for Crop Disease Prediction Service.

Automates single and multi-image disease prediction testing before API integration.
Prints:
- Image Path / Name
- True Disease Class
- Predicted Disease
- Confidence Score (%)
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Ensure backend root directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.disease_service import predict_disease


def find_sample_images(dataset_dir: Path, num_samples_per_class: int = 1) -> List[Tuple[Path, str]]:
    """
    Scans dataset directory to automatically find sample images from each class folder.

    Returns:
        List[Tuple[Path, str]]: List of (image_path, true_class_name) tuples.
    """
    dataset_dir = dataset_dir.resolve()
    if not dataset_dir.exists():
        print(f"[WARNING] Dataset path {dataset_dir} does not exist.")
        return []

    subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]

    # Handle nested subfolders (e.g., datasets/plantvillage/Tomato)
    has_direct_images = any(
        any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in d.iterdir() if f.is_file())
        for d in subdirs
    )

    if not has_direct_images:
        for subdir in subdirs:
            child_subdirs = [d for d in subdir.iterdir() if d.is_dir()]
            child_has_images = any(
                any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in c.iterdir() if c.is_file())
                for c in child_subdirs
            )
            if child_has_images:
                subdirs = child_subdirs
                break

    samples = []
    for class_dir in sorted(subdirs, key=lambda x: x.name):
        class_name = class_dir.name
        img_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]]
        for img_path in img_files[:num_samples_per_class]:
            samples.append((img_path, class_name))

    return samples


def test_single_image_prediction(sample_image_path: Path) -> dict:
    """
    Tests prediction on a single sample image and prints details.
    """
    print("=" * 80)
    print("SINGLE IMAGE PREDICTION TEST")
    print(f"Loading image: {sample_image_path}")
    print("=" * 80)

    result = predict_disease(sample_image_path)

    predicted_disease = result["disease"]
    confidence = result["confidence"]

    print(f"Predicted Disease : {predicted_disease}")
    print(f"Confidence        : {confidence:.1f}%\n")

    assert "disease" in result and "confidence" in result
    assert isinstance(predicted_disease, str)
    assert isinstance(confidence, float)

    return result


def test_multiple_images_automatically(dataset_dir: Path, max_samples: int = 10) -> List[dict]:
    """
    Automatically collects sample images across multiple classes and runs predictions.
    """
    samples = find_sample_images(dataset_dir, num_samples_per_class=1)
    if not samples:
        print("[WARNING] No dataset images found for multi-image testing.")
        return []

    samples = samples[:max_samples]

    print("=" * 95)
    print(f"AUTOMATED MULTI-IMAGE PREDICTION TEST ({len(samples)} Sample Images)")
    print("=" * 95)
    print(f"{'#':<3} | {'True Class':<35} | {'Predicted Disease':<35} | {'Confidence':<10}")
    print("-" * 95)

    results = []
    correct_matches = 0

    for idx, (img_path, true_class) in enumerate(samples, 1):
        try:
            res = predict_disease(img_path)
            pred_disease = res["disease"]
            confidence = res["confidence"]

            is_match = pred_disease == true_class
            if is_match:
                correct_matches += 1

            status_mark = "✓" if is_match else "✗"
            print(f"{idx:<3} | {true_class:<35} | {pred_disease:<35} | {confidence:>5.1f}% {status_mark}")

            results.append({
                "file": img_path.name,
                "true_class": true_class,
                "predicted_disease": pred_disease,
                "confidence": confidence,
                "match": is_match,
            })
        except Exception as e:
            print(f"{idx:<3} | {true_class:<35} | ERROR: {str(e):<35} | N/A")

    print("-" * 95)
    match_percentage = (correct_matches / len(samples)) * 100.0 if samples else 0.0
    print(f"Summary: {correct_matches}/{len(samples)} exact class matches ({match_percentage:.1f}% accuracy on sample test batch)")
    print("=" * 95 + "\n")

    return results


if __name__ == "__main__":
    dataset_path = PROJECT_ROOT / "datasets" / "plantvillage"

    # 1. Collect sample images
    sample_items = find_sample_images(dataset_path, num_samples_per_class=1)

    if sample_items:
        # Test 1: Single image prediction
        first_img, _ = sample_items[0]
        test_single_image_prediction(first_img)

        # Test 2: Multiple images automatically
        test_multiple_images_automatically(dataset_path, max_samples=10)
    else:
        print("[ERROR] Could not locate plantvillage dataset images for testing.")
