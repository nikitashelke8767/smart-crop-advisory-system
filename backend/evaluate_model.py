"""
Production-Ready Model Evaluation Script for Crop Disease Model.

Evaluates trained MobileNetV2 v2 model (disease_model_v2.h5) on validation dataset.
Generates:
- Confusion Matrix (Plot & Text Matrix)
- Classification Report (Precision, Recall, F1-Score per class)
- Macro & Weighted Precision, Recall, F1 Scores
- Saves report to docs/reports/model_evaluation.txt
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

# Ensure backend root directory is in sys.path for internal imports
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.image_preprocessing import create_data_generators


def resolve_dataset_dir(base_dir: Path) -> Path:
    """
    Resolves dataset directory path, navigating to subfolder if nested.
    """
    base_dir = Path(base_dir).resolve()
    if not base_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found at {base_dir}")

    subdirs = [d for d in base_dir.iterdir() if d.is_dir()]

    has_direct_images = any(
        any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in d.iterdir() if f.is_file())
        for d in subdirs
    )

    if not has_direct_images:
        for subdir in subdirs:
            child_subdirs = [d for d in subdir.iterdir() if d.is_dir()]
            child_has_images = any(
                any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in c.iterdir() if f.is_file())
                for c in child_subdirs
            )
            if child_has_images:
                return subdir

    return base_dir


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list,
    output_path: Path,
    title: str = "Confusion Matrix - Fine-Tuned Disease Model (v2)",
) -> None:
    """
    Generates and saves a styled Confusion Matrix heatmap using Seaborn & Matplotlib.
    """
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True,
        linewidths=0.5,
    )
    plt.title(title, fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Predicted Class", fontsize=12, labelpad=10)
    plt.ylabel("True Class", fontsize=12, labelpad=10)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[INFO] Confusion Matrix heatmap saved to: {output_path}")


def evaluate_model(
    model_path: str = "trained_models/disease_model/disease_model_v2.h5",
    dataset_dir: str = "datasets/plantvillage/",
    report_output_path: str = "docs/reports/model_evaluation.txt",
    target_size: Tuple[int, int] = (224, 224),
    batch_size: int = 32,
    validation_split: float = 0.2,
) -> str:
    """
    Full evaluation workflow:
    1. Loads fine-tuned model (disease_model_v2.h5).
    2. Runs predictions on validation set (shuffle=False).
    3. Computes Confusion Matrix, Precision, Recall, F1 Scores.
    4. Generates Seaborn confusion matrix heatmap.
    5. Formats and saves comprehensive evaluation report to docs/reports/model_evaluation.txt.
    """
    project_root = BACKEND_DIR.parent
    model_file_path = (project_root / model_path).resolve() if not Path(model_path).is_absolute() else Path(model_path)
    if not model_file_path.exists():
        raise FileNotFoundError(f"Model binary not found at {model_file_path}")

    raw_dataset_path = (project_root / dataset_dir).resolve() if not Path(dataset_dir).is_absolute() else Path(dataset_dir)
    resolved_dataset_path = resolve_dataset_dir(raw_dataset_path)

    report_file_path = (project_root / report_output_path).resolve() if not Path(report_output_path).is_absolute() else Path(report_output_path)
    report_file_path.parent.mkdir(parents=True, exist_ok=True)

    cm_plot_path = report_file_path.parent / "confusion_matrix.png"

    print("=" * 80)
    print("STARTING MODEL EVALUATION")
    print(f"Model Path    : {model_file_path}")
    print(f"Dataset Path  : {resolved_dataset_path}")
    print(f"Report Output : {report_file_path}")
    print("=" * 80)

    # 1. Create validation data generator (shuffle=False for aligned predictions)
    _, val_gen = create_data_generators(
        data_dir=resolved_dataset_path,
        target_size=target_size,
        batch_size=batch_size,
        validation_split=validation_split,
        shuffle=False,
    )

    class_indices = val_gen.class_indices
    class_names = list(class_indices.keys())
    y_true = val_gen.classes
    total_samples = len(y_true)

    print(f"[INFO] Evaluating {total_samples} validation samples across {len(class_names)} classes...")

    # 2. Load Model
    print(f"[INFO] Loading model from: {model_file_path}")
    model = tf.keras.models.load_model(str(model_file_path))

    # 3. Predict probabilities and get predicted class indices
    print("[INFO] Running inference on validation dataset...")
    y_pred_probs = model.predict(val_gen, verbose=1)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # 4. Calculate metrics
    accuracy = float(np.mean(y_true == y_pred))

    macro_precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_recall = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    weighted_precision = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_recall = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_true, y_pred)
    cls_report = classification_report(y_true, y_pred, target_names=class_names, digits=4)

    # 5. Plot confusion matrix
    plot_confusion_matrix(cm, class_names, cm_plot_path)

    # 6. Format text evaluation report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("             FINE-TUNED DISEASE MODEL EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Model File          : {model_file_path.name}")
    report_lines.append(f"Dataset Path        : {resolved_dataset_path}")
    report_lines.append(f"Total Validation    : {total_samples} samples")
    report_lines.append(f"Total Classes       : {len(class_names)}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("1. OVERALL EVALUATION METRICS SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Overall Accuracy    : {accuracy * 100:.2f}%")
    report_lines.append("")
    report_lines.append(f"Macro Precision     : {macro_precision * 100:.2f}%")
    report_lines.append(f"Macro Recall        : {macro_recall * 100:.2f}%")
    report_lines.append(f"Macro F1-Score      : {macro_f1 * 100:.2f}%")
    report_lines.append("")
    report_lines.append(f"Weighted Precision  : {weighted_precision * 100:.2f}%")
    report_lines.append(f"Weighted Recall     : {weighted_recall * 100:.2f}%")
    report_lines.append(f"Weighted F1-Score   : {weighted_f1 * 100:.2f}%")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("2. DETAILED CLASSIFICATION REPORT BY CLASS")
    report_lines.append("-" * 80)
    report_lines.append(cls_report)
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("3. CONFUSION MATRIX (TEXT REPRESENTATION)")
    report_lines.append("-" * 80)

    # Format text confusion matrix header
    header = f"{'True / Pred':<45} | " + " | ".join([f"C{i:<2}" for i in range(len(class_names))])
    report_lines.append(header)
    report_lines.append("-" * len(header))

    for idx, row in enumerate(cm):
        row_str = " | ".join([f"{val:4d}" for val in row])
        class_name_padded = f"C{idx}: {class_names[idx]}"[:45]
        report_lines.append(f"{class_name_padded:<45} | {row_str}")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF EVALUATION REPORT")
    report_lines.append("=" * 80)

    report_content = "\n".join(report_lines)

    # Save to file
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n[INFO] Model evaluation report successfully saved to: {report_file_path}")

    print("\n" + report_content)

    return report_content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Fine-Tuned Crop Disease Model")
    parser.add_argument("--model_path", type=str, default="trained_models/disease_model/disease_model_v2.h5", help="Path to fine-tuned .h5 model")
    parser.add_argument("--dataset_dir", type=str, default="datasets/plantvillage/", help="Path to dataset directory")
    parser.add_argument("--report_path", type=str, default="docs/reports/model_evaluation.txt", help="Path to output evaluation report file")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    args = parser.parse_args()

    evaluate_model(
        model_path=args.model_path,
        dataset_dir=args.dataset_dir,
        report_output_path=args.report_path,
        batch_size=args.batch_size,
    )
