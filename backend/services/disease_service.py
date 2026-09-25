"""
Crop Disease Prediction Service Module.

Loads fine-tuned MobileNetV2 disease detection model and class names.
Provides single-image disease prediction reusable by FastAPI endpoints.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import tensorflow as tf

# Configure logger
try:
    from utils.logger import logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("smart_crop_disease_service")

# Import image preprocessing utility
from utils.image_preprocessing import preprocess_image

# Resolve base paths
SERVICE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SERVICE_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DEFAULT_MODEL_V2_PATH = PROJECT_ROOT / "trained_models" / "disease_model" / "disease_model_v2.h5"
DEFAULT_MODEL_V1_PATH = PROJECT_ROOT / "trained_models" / "disease_model" / "disease_model.h5"
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "trained_models" / "disease_model" / "class_names.json"


class DiseaseService:
    """
    Singleton-style service class for crop disease prediction.
    Caches loaded TensorFlow model and class names in memory.
    """

    _instance: Optional["DiseaseService"] = None

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        class_names_path: Optional[Union[str, Path]] = None,
    ):
        self.model_path = self._resolve_model_path(model_path)
        self.class_names_path = Path(class_names_path) if class_names_path else DEFAULT_CLASS_NAMES_PATH

        self.model: Optional[tf.keras.Model] = None
        self.class_names: List[str] = []

        self._load_artifacts()

    def _resolve_model_path(self, user_model_path: Optional[Union[str, Path]]) -> Path:
        """
        Resolves model file path, prioritizing disease_model_v2.h5 over disease_model.h5.
        """
        if user_model_path:
            p = Path(user_model_path).resolve()
            if p.exists():
                return p
            raise FileNotFoundError(f"Specified model file not found at: {p}")

        if DEFAULT_MODEL_V2_PATH.exists():
            return DEFAULT_MODEL_V2_PATH
        elif DEFAULT_MODEL_V1_PATH.exists():
            return DEFAULT_MODEL_V1_PATH
        else:
            raise FileNotFoundError(
                f"No trained disease model found at {DEFAULT_MODEL_V2_PATH} or {DEFAULT_MODEL_V1_PATH}"
            )

    def _load_artifacts(self) -> None:
        """
        Loads model and class names JSON into memory.
        """
        logger.info(f"[DiseaseService] Loading model from: {self.model_path}")
        try:
            self.model = tf.keras.models.load_model(str(self.model_path))
            logger.info("[DiseaseService] Model loaded successfully.")
        except Exception as e:
            logger.error(f"[DiseaseService] Failed to load model binary: {e}")
            raise RuntimeError(f"Could not load TensorFlow model from {self.model_path}: {e}")

        logger.info(f"[DiseaseService] Loading class names from: {self.class_names_path}")
        if not self.class_names_path.exists():
            logger.error(f"[DiseaseService] Class names JSON file not found at {self.class_names_path}")
            raise FileNotFoundError(f"Class names file not found at {self.class_names_path}")

        try:
            with open(self.class_names_path, "r", encoding="utf-8") as f:
                self.class_names = json.load(f)
            logger.info(f"[DiseaseService] Loaded {len(self.class_names)} classes.")
        except Exception as e:
            logger.error(f"[DiseaseService] Failed to read class names JSON: {e}")
            raise RuntimeError(f"Could not load class names from {self.class_names_path}: {e}")

    def predict_disease(self, image_input: Union[str, Path, bytes, Any]) -> Dict[str, Any]:
        """
        Predicts crop disease for a single image input.

        Args:
            image_input: File path (str/Path), raw bytes, PIL Image, or numpy array.

        Returns:
            Dict[str, Any]: {
                "disease": "Tomato___Late_blight",
                "confidence": 98.7
            }
        """
        if image_input is None:
            logger.error("[DiseaseService] Input image is None.")
            raise ValueError("Invalid image input: Input cannot be None.")

        # Handle string/Path existence check
        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            if not img_path.exists() or not img_path.is_file():
                logger.error(f"[DiseaseService] Image file not found: {img_path}")
                raise ValueError(f"Image file does not exist or is invalid: {img_path}")

        # Handle empty bytes
        if isinstance(image_input, bytes) and len(image_input) == 0:
            logger.error("[DiseaseService] Received empty byte string.")
            raise ValueError("Invalid image input: Provided image bytes are empty.")

        logger.info("[DiseaseService] Preprocessing image input...")
        try:
            processed_tensor = preprocess_image(
                image_input,
                target_size=(224, 224),
                normalize=True,
                expand_batch_dim=True,
                augment=False,
            )
        except Exception as e:
            logger.error(f"[DiseaseService] Image preprocessing failed: {e}")
            raise ValueError(f"Invalid or corrupted image input: {e}")

        logger.info("[DiseaseService] Running model prediction...")
        try:
            predictions = self.model.predict(processed_tensor, verbose=0)
            pred_probs = predictions[0]

            top_idx = int(np.argmax(pred_probs))
            confidence_percentage = round(float(pred_probs[top_idx]) * 100.0, 1)

            disease_name = self.class_names[top_idx]

            result = {
                "disease": disease_name,
                "confidence": confidence_percentage,
            }

            logger.info(f"[DiseaseService] Prediction success: {disease_name} ({confidence_percentage}%)")
            return result

        except Exception as e:
            logger.error(f"[DiseaseService] Model inference failed: {e}")
            raise RuntimeError(f"Error executing disease model prediction: {e}")


# Singleton service instance for FastAPI reusability
_disease_service_instance: Optional[DiseaseService] = None


def get_disease_service() -> DiseaseService:
    """
    Returns or initializes singleton DiseaseService instance.
    """
    global _disease_service_instance
    if _disease_service_instance is None:
        _disease_service_instance = DiseaseService()
    return _disease_service_instance


def predict_disease(image_path: Union[str, Path, bytes, Any]) -> Dict[str, Any]:
    """
    Standalone function interface for single-image disease prediction.
    Reusable directly by FastAPI endpoint handlers.

    Usage:
        result = predict_disease("path/to/leaf.jpg")
        # Returns: {"disease": "Tomato___Late_blight", "confidence": 98.7}
    """
    service = get_disease_service()
    return service.predict_disease(image_path)
