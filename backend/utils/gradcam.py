"""
Grad-CAM (Gradient-weighted Class Activation Mapping) Visualization Module.

Generates visual heatmaps highlighting infected leaf regions for crop disease
predictions made by the fine-tuned MobileNetV2-based disease model.

Useful for:
  - Model explainability and debugging
  - Capstone / research presentations
  - Overlaying disease hotspots in the frontend UI

References:
  Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via
  Gradient-based Localization", ICCV 2017.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import tensorflow as tf

# ---------------------------------------------------------------------------
# Ensure backend root is on sys.path for direct-script execution
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.image_preprocessing import preprocess_image  # noqa: E402

# ---------------------------------------------------------------------------
# Class labels matching disease_model_v2.h5 (Tomato PlantVillage subset)
# ---------------------------------------------------------------------------
DISEASE_CLASS_LABELS: List[str] = [
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

# ---------------------------------------------------------------------------
# Default paths (relative to project root)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = BACKEND_DIR.parent
_DEFAULT_MODEL_V2 = _PROJECT_ROOT / "trained_models" / "disease_model" / "disease_model_v2.h5"
_DEFAULT_MODEL_V1 = _PROJECT_ROOT / "trained_models" / "disease_model" / "disease_model.h5"
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "trained_models" / "disease_model"


# ===========================================================================
# 1. Model Loading
# ===========================================================================

def load_disease_model(
    model_path: Optional[Union[str, Path]] = None,
) -> tf.keras.Model:
    """
    Loads the trained MobileNetV2-based disease classification model.

    Search priority:
      1. ``model_path`` argument (if provided and exists).
      2. ``trained_models/disease_model/disease_model_v2.h5``
      3. ``trained_models/disease_model/disease_model.h5``

    Args:
        model_path: Optional explicit path to a ``.h5`` or SavedModel file.

    Returns:
        tf.keras.Model: Loaded Keras model ready for inference.

    Raises:
        FileNotFoundError: If no model file is found at any search path.
    """
    candidates: List[Path] = []
    if model_path:
        candidates.append(Path(model_path).resolve())
    candidates.extend([_DEFAULT_MODEL_V2, _DEFAULT_MODEL_V1])

    for path in candidates:
        if path.exists():
            print(f"[INFO] Loading model from: {path}")
            return tf.keras.models.load_model(str(path))

    raise FileNotFoundError(
        "No trained disease model found. Searched:\n"
        + "\n".join(f"  - {p}" for p in candidates)
    )


# ===========================================================================
# 2. Last Convolutional Layer Detection
# ===========================================================================

def _find_last_conv_layer(model: tf.keras.Model) -> str:
    """
    Auto-detects the name of the last Conv2D (or activation) layer inside
    the MobileNetV2 backbone, or falls back to the top-level model.

    Args:
        model: The full Keras model.

    Returns:
        str: Layer name suitable for Grad-CAM gradient computation.

    Raises:
        ValueError: If no suitable layer is found.
    """
    # Check nested backbone first
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and (
            "mobilenet" in layer.name.lower() or "backbone" in layer.name.lower()
        ):
            last_conv: Optional[str] = None
            last_act: Optional[str] = None
            for sub in reversed(layer.layers):
                if isinstance(sub, tf.keras.layers.Conv2D) and last_conv is None:
                    last_conv = sub.name
                if (
                    isinstance(sub, tf.keras.layers.Activation)
                    or "relu" in sub.name.lower()
                ) and last_act is None:
                    last_act = sub.name
            target = last_conv or last_act
            if target:
                return target

    # Fallback: top-level Conv2D
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name

    raise ValueError(
        "Could not auto-detect a convolutional layer for Grad-CAM. "
        "Pass 'layer_name' explicitly."
    )


def _layer_in_model(model: tf.keras.Model, layer_name: str) -> bool:
    """Returns True if a layer with ``layer_name`` exists in ``model``."""
    return any(lyr.name == layer_name for lyr in model.layers)


# ===========================================================================
# 3. Grad-CAM Heatmap Generation
# ===========================================================================

def generate_gradcam_heatmap(
    model: tf.keras.Model,
    image_tensor: tf.Tensor,
    layer_name: Optional[str] = None,
    pred_index: Optional[int] = None,
) -> Tuple[np.ndarray, int, float]:
    """
    Computes a Grad-CAM heatmap for the given image tensor.

    Algorithm:
      1. Build a gradient model outputting (conv_feature_map, predictions).
      2. Record gradients of the target class score w.r.t. conv output.
      3. Pool gradients channel-wise (global average) → importance weights.
      4. Weight each feature-map channel by importance and sum.
      5. Apply ReLU and min-max normalise to [0, 1].

    Args:
        model:         Loaded Keras model.
        image_tensor:  Preprocessed float32 tensor of shape ``(1, 224, 224, 3)``.
        layer_name:    Target conv layer name. Auto-detected if ``None``.
        pred_index:    Class index to visualise. Uses argmax prediction if ``None``.

    Returns:
        Tuple of:
          - ``heatmap`` (np.ndarray, H×W float32, range [0, 1])
          - ``pred_index`` (int): Predicted class index.
          - ``confidence`` (float): Softmax score for the predicted class.
    """
    if layer_name is None:
        layer_name = _find_last_conv_layer(model)
        print(f"[INFO] Grad-CAM target layer auto-detected: '{layer_name}'")

    # Resolve backbone vs. flat architecture
    backbone: Optional[tf.keras.Model] = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and (
            "mobilenet" in layer.name.lower() or "backbone" in layer.name.lower()
        ):
            backbone = layer
            break

    if backbone is not None and _layer_in_model(backbone, layer_name):
        # ── Backbone + Head architecture ─────────────────────────────── #
        grad_model_base = tf.keras.Model(
            inputs=backbone.inputs,
            outputs=[backbone.get_layer(layer_name).output, backbone.output],
        )
        head_layers = [
            lyr for lyr in model.layers
            if lyr is not backbone
            and not isinstance(lyr, tf.keras.layers.InputLayer)
        ]

        with tf.GradientTape() as tape:
            conv_outputs, base_out = grad_model_base(image_tensor, training=False)
            tape.watch(conv_outputs)
            x = base_out
            for lyr in head_layers:
                x = lyr(x, training=False)
            predictions = x
            if pred_index is None:
                pred_index = int(tf.argmax(predictions[0]))
            class_score = predictions[:, pred_index]

        grads = tape.gradient(class_score, conv_outputs)

    else:
        # ── Flat architecture ─────────────────────────────────────────── #
        grad_model = tf.keras.Model(
            inputs=model.inputs,
            outputs=[model.get_layer(layer_name).output, model.output],
        )

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(image_tensor, training=False)
            if pred_index is None:
                pred_index = int(tf.argmax(predictions[0]))
            class_score = predictions[:, pred_index]

        grads = tape.gradient(class_score, conv_outputs)

    # Pool gradients channel-wise → per-channel importance weights
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Weighted sum of feature maps
    conv_map = conv_outputs[0]                          # (h, w, c)
    heatmap = conv_map @ pooled_grads[..., tf.newaxis]  # (h, w, 1)
    heatmap = tf.squeeze(heatmap)                       # (h, w)

    # ReLU: keep only positive activations
    heatmap = tf.maximum(heatmap, 0.0)

    # Min-max normalise to [0, 1]
    h_min = tf.reduce_min(heatmap)
    h_max = tf.reduce_max(heatmap)
    if h_max > h_min:
        heatmap = (heatmap - h_min) / (h_max - h_min)
    else:
        heatmap = tf.zeros_like(heatmap)

    confidence = float(tf.nn.softmax(predictions[0])[pred_index])

    return heatmap.numpy().astype(np.float32), pred_index, confidence


# ===========================================================================
# 4. Heatmap Overlay
# ===========================================================================

def _draw_label_banner(img: np.ndarray, text: str) -> None:
    """Draws a semi-transparent bottom banner with annotation text (in-place)."""
    h, w = img.shape[:2]
    banner_h = 36
    banner = img[h - banner_h:h, :].copy()
    cv2.rectangle(img, (0, h - banner_h), (w, h), (0, 0, 0), -1)
    img[h - banner_h:h] = cv2.addWeighted(img[h - banner_h:h], 0.35, banner, 0.65, 0)
    cv2.putText(
        img, text, (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
    )


def _append_colorbar(img: np.ndarray, colormap: int, bar_width: int = 24) -> np.ndarray:
    """Appends a vertical gradient colorbar strip to the right of ``img``."""
    h = img.shape[0]
    gradient = np.linspace(255, 0, h, dtype=np.uint8).reshape(h, 1)
    colorbar = cv2.applyColorMap(gradient, colormap)
    colorbar = np.repeat(colorbar, bar_width, axis=1)
    return np.hstack([img, colorbar])


def overlay_heatmap_on_image(
    original_image: Union[np.ndarray, str, Path],
    heatmap: np.ndarray,
    alpha: float = 0.55,
    beta: float = 0.45,
    colormap: int = cv2.COLORMAP_JET,
    add_colorbar: bool = True,
    label_text: Optional[str] = None,
    confidence: Optional[float] = None,
) -> np.ndarray:
    """
    Overlays a 2-D Grad-CAM heatmap onto the original BGR image.

    Steps:
      1. Read or copy the original image.
      2. Resize the heatmap to match image dimensions.
      3. Apply the chosen OpenCV colormap.
      4. Blend original + coloured heatmap via ``cv2.addWeighted``.
      5. Optionally annotate with a prediction label / confidence banner.
      6. Optionally append a vertical colorbar strip.

    Args:
        original_image: File path (str/Path) or BGR numpy array.
        heatmap:        2-D float32 array with values in [0, 1].
        alpha:          Weight of original image in blending (default 0.55).
        beta:           Weight of heatmap overlay in blending (default 0.45).
        colormap:       OpenCV colormap constant (default ``cv2.COLORMAP_JET``).
        add_colorbar:   Append a vertical colorbar strip when True.
        label_text:     Disease class label string for annotation.
        confidence:     Softmax confidence (0–1) shown alongside the label.

    Returns:
        np.ndarray: Blended BGR image (H × W × 3, uint8).
    """
    if isinstance(original_image, (str, Path)):
        img = cv2.imread(str(original_image))
        if img is None:
            raise ValueError(f"Could not load image from: {original_image}")
    else:
        img = original_image.copy()

    h, w = img.shape[:2]

    # Resize heatmap → image size
    resized_heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_CUBIC)

    # Convert to uint8 and apply colormap
    uint8_heatmap = np.uint8(255 * resized_heatmap)
    colored_heatmap = cv2.applyColorMap(uint8_heatmap, colormap)

    # Weighted blend
    overlay = cv2.addWeighted(img, alpha, colored_heatmap, beta, 0)

    # Optional label banner
    if label_text:
        conf_str = f"  ({confidence * 100:.1f}%)" if confidence is not None else ""
        annotation = label_text.replace("___", " › ").replace("_", " ") + conf_str
        _draw_label_banner(overlay, annotation)

    # Optional colorbar
    if add_colorbar:
        overlay = _append_colorbar(overlay, colormap)

    return overlay


# ===========================================================================
# 5. End-to-End Pipeline
# ===========================================================================

def generate_and_save_gradcam(
    image_path: Union[str, Path],
    output_path: Union[str, Path],
    model: Optional[tf.keras.Model] = None,
    model_path: Optional[Union[str, Path]] = None,
    layer_name: Optional[str] = None,
    pred_index: Optional[int] = None,
    alpha: float = 0.55,
    beta: float = 0.45,
    colormap: int = cv2.COLORMAP_JET,
    class_labels: Optional[List[str]] = None,
    add_colorbar: bool = True,
) -> Dict:
    """
    Full Grad-CAM pipeline:

    1. **Load** the trained MobileNetV2 disease model.
    2. **Preprocess** the input image to a ``(1, 224, 224, 3)`` float32 tensor.
    3. **Generate** the Grad-CAM heatmap highlighting infected leaf regions.
    4. **Overlay** the heatmap on the original image.
    5. **Save** the blended visualisation to disk.

    Args:
        image_path:   Path to the input leaf image.
        output_path:  Destination path for the Grad-CAM output image.
        model:        Pre-loaded Keras model (skips loading if provided).
        model_path:   Path to a ``.h5`` model file (used if ``model`` is None).
        layer_name:   Target conv layer for gradient computation. Auto-detected if None.
        pred_index:   Class index to visualise. Uses argmax prediction if None.
        alpha:        Weight of original image in blending.
        beta:         Weight of heatmap in blending.
        colormap:     OpenCV colormap (default ``cv2.COLORMAP_JET``).
        class_labels: List of class label strings. Defaults to DISEASE_CLASS_LABELS.
        add_colorbar: Whether to append a colorbar strip to the output image.

    Returns:
        dict with keys:
          - ``output_path`` (Path): Saved visualisation path.
          - ``pred_index`` (int): Predicted class index.
          - ``pred_label`` (str): Human-readable class label.
          - ``confidence`` (float): Softmax confidence score.
          - ``heatmap`` (np.ndarray): Raw 2-D heatmap array.
    """
    image_path = Path(image_path).resolve()
    output_path = Path(output_path).resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    labels = class_labels or DISEASE_CLASS_LABELS

    # Step 1: Load model
    if model is None:
        model = load_disease_model(model_path)

    # Step 2: Preprocess image
    tensor = preprocess_image(
        image_path,
        target_size=(224, 224),
        normalize=True,
        expand_batch_dim=True,
    )

    # Step 3: Generate heatmap
    heatmap, pred_idx, confidence = generate_gradcam_heatmap(
        model, tensor, layer_name=layer_name, pred_index=pred_index
    )

    pred_label = labels[pred_idx] if pred_idx < len(labels) else f"Class {pred_idx}"
    print(f"[INFO] Prediction : {pred_label}  (confidence: {confidence * 100:.2f}%)")

    # Step 4: Overlay heatmap
    overlay_img = overlay_heatmap_on_image(
        original_image=image_path,
        heatmap=heatmap,
        alpha=alpha,
        beta=beta,
        colormap=colormap,
        add_colorbar=add_colorbar,
        label_text=pred_label,
        confidence=confidence,
    )

    # Step 5: Save output image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(output_path), overlay_img)
    if not success:
        raise IOError(f"cv2.imwrite failed — could not save to: {output_path}")

    print(f"[INFO] Grad-CAM visualisation saved → {output_path}")

    return {
        "output_path": output_path,
        "pred_index": pred_idx,
        "pred_label": pred_label,
        "confidence": confidence,
        "heatmap": heatmap,
    }


# ===========================================================================
# 6. CLI Entry Point
# ===========================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Grad-CAM heatmap for the Smart Crop Advisory disease model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--image_path", type=str, required=True,
        help="Path to input leaf image (JPEG / PNG).",
    )
    parser.add_argument(
        "--output_path", type=str,
        default=str(_DEFAULT_OUTPUT_DIR / "gradcam_demo.jpg"),
        help="Destination path for the Grad-CAM output image.",
    )
    parser.add_argument(
        "--model_path", type=str, default=None,
        help="Path to the .h5 model file. Auto-detects disease_model_v2.h5 if omitted.",
    )
    parser.add_argument(
        "--layer_name", type=str, default=None,
        help="Target convolutional layer name for gradient computation.",
    )
    parser.add_argument(
        "--pred_index", type=int, default=None,
        help="Class index to visualise. Uses model's top prediction if omitted.",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.55,
        help="Blend weight for the original image (0.0–1.0).",
    )
    parser.add_argument(
        "--beta", type=float, default=0.45,
        help="Blend weight for the Grad-CAM heatmap overlay (0.0–1.0).",
    )
    parser.add_argument(
        "--no_colorbar", action="store_true",
        help="Disable the colorbar strip on the output image.",
    )

    args = parser.parse_args()

    result = generate_and_save_gradcam(
        image_path=args.image_path,
        output_path=args.output_path,
        model_path=args.model_path,
        layer_name=args.layer_name,
        pred_index=args.pred_index,
        alpha=args.alpha,
        beta=args.beta,
        add_colorbar=not args.no_colorbar,
    )

    print(
        f"\n✅  Done.\n"
        f"   Predicted class : {result['pred_label']}\n"
        f"   Confidence       : {result['confidence'] * 100:.2f}%\n"
        f"   Output saved to  : {result['output_path']}"
    )
