"""
Production-Ready Fine-Tuning Script for Crop Disease Model.

Model Architecture: Fine-tuned MobileNetV2 (Unfreezing top layers)
Dataset: PlantVillage (Tomato plant disease classes)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import tensorflow as tf

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


def unfreeze_last_n_layers(model: tf.keras.Model, n_layers: int = 30) -> tf.keras.Model:
    """
    Unfreezes the last `n_layers` of the MobileNetV2 base model.
    Keeps BatchNormalization layers frozen as per TensorFlow fine-tuning best practices.
    """
    base_model = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) or "mobilenet" in layer.name.lower():
            base_model = layer
            break

    if base_model is None:
        print(f"[WARNING] Base sub-model not found. Unfreezing last {n_layers} top-level layers.")
        for layer in model.layers[:-n_layers]:
            layer.trainable = False
        for layer in model.layers[-n_layers:]:
            if not isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = True
        return model

    # Unfreeze base model and freeze early layers
    base_model.trainable = True
    total_layers = len(base_model.layers)
    fine_tune_at = max(0, total_layers - n_layers)

    print(f"[INFO] MobileNetV2 total layers: {total_layers}")
    print(f"[INFO] Freezing first {fine_tune_at} layers; unfreezing last {n_layers} layers.")

    trainable_count = 0
    frozen_count = 0

    for i, layer in enumerate(base_model.layers):
        if i < fine_tune_at:
            layer.trainable = False
            frozen_count += 1
        else:
            # Keep BatchNormalization frozen during fine-tuning
            if isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = False
                frozen_count += 1
            else:
                layer.trainable = True
                trainable_count += 1

    print(f"[INFO] Base model layers: {trainable_count} trainable, {frozen_count} frozen.")
    return model


def plot_fine_tune_comparison(
    history: tf.keras.callbacks.History,
    baseline_acc: float,
    baseline_loss: float,
    output_plot_path: Path,
) -> None:
    """
    Plots training & validation accuracy and loss during fine-tuning compared against baseline.
    """
    acc = history.history.get("accuracy", [])
    val_acc = history.history.get("val_accuracy", [])
    loss = history.history.get("loss", [])
    val_loss = history.history.get("val_loss", [])
    epochs_range = range(1, len(acc) + 1)

    plt.figure(figsize=(14, 5))

    # Accuracy Comparison Plot
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label="Fine-Tune Train Accuracy", marker="o", color="#1f77b4")
    plt.plot(epochs_range, val_acc, label="Fine-Tune Val Accuracy", marker="s", color="#2ca02c")
    plt.axhline(
        y=baseline_acc,
        color="#d62728",
        linestyle="--",
        label=f"Baseline Val Accuracy ({baseline_acc * 100:.2f}%)",
    )
    plt.title("Fine-Tuning Accuracy Comparison")
    plt.xlabel("Fine-Tuning Epoch")
    plt.ylabel("Accuracy")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right")

    # Loss Comparison Plot
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label="Fine-Tune Train Loss", marker="o", color="#1f77b4")
    plt.plot(epochs_range, val_loss, label="Fine-Tune Val Loss", marker="s", color="#2ca02c")
    plt.axhline(
        y=baseline_loss,
        color="#d62728",
        linestyle="--",
        label=f"Baseline Val Loss ({baseline_loss:.4f})",
    )
    plt.title("Fine-Tuning Loss Comparison")
    plt.xlabel("Fine-Tuning Epoch")
    plt.ylabel("Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper right")

    plt.tight_layout()
    output_plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, dpi=300)
    plt.close()
    print(f"[INFO] Fine-tuning comparison plot saved to: {output_plot_path}")


def fine_tune_disease_model(
    model_path: str = "trained_models/disease_model/disease_model.h5",
    dataset_dir: str = "datasets/plantvillage/",
    output_dir: str = "trained_models/disease_model/",
    unfreeze_layers_count: int = 30,
    learning_rate: float = 1e-5,
    batch_size: int = 32,
    epochs: int = 10,
    validation_split: float = 0.2,
) -> Tuple[tf.keras.Model, Dict[str, float]]:
    """
    Fine-tuning workflow:
    1. Loads pretrained stage-1 model (disease_model.h5).
    2. Evaluates baseline validation accuracy and loss.
    3. Unfreezes the last `unfreeze_layers_count` (30) layers of MobileNetV2.
    4. Re-compiles with low learning rate (1e-5).
    5. Trains for `epochs` (5-10 epochs) with callbacks.
    6. Saves improved model to `disease_model_v2.h5`.
    7. Generates accuracy/loss comparison graphs.
    """
    project_root = BACKEND_DIR.parent
    model_file_path = (project_root / model_path).resolve() if not Path(model_path).is_absolute() else Path(model_path)
    if not model_file_path.exists():
        raise FileNotFoundError(f"Base model file not found at {model_file_path}")

    raw_dataset_path = (project_root / dataset_dir).resolve() if not Path(dataset_dir).is_absolute() else Path(dataset_dir)
    resolved_dataset_path = resolve_dataset_dir(raw_dataset_path)

    out_path = (project_root / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    v2_model_path = out_path / "disease_model_v2.h5"
    plot_file_path = out_path / "fine_tune_comparison.png"

    print("=" * 80)
    print("STARTING FINE-TUNING FOR PLANT DISEASE MODEL")
    print(f"Base Model Path   : {model_file_path}")
    print(f"Dataset Path      : {resolved_dataset_path}")
    print(f"Output Directory  : {out_path}")
    print(f"Unfrozen Layers   : {unfreeze_layers_count}")
    print(f"Learning Rate     : {learning_rate}")
    print(f"Epochs            : {epochs}")
    print("=" * 80)

    # 1. Load dataset generators
    train_gen, val_gen = create_data_generators(
        data_dir=resolved_dataset_path,
        target_size=(224, 224),
        batch_size=batch_size,
        validation_split=validation_split,
        shuffle=True,
        rotation_range=20.0,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=(0.8, 1.2),
    )

    # 2. Load pre-trained model
    print(f"[INFO] Loading baseline model from: {model_file_path}")
    model = tf.keras.models.load_model(str(model_file_path))

    # Evaluate baseline model performance
    print("[INFO] Evaluating baseline model on validation dataset...")
    baseline_metrics = model.evaluate(val_gen, verbose=1)
    baseline_loss, baseline_acc = float(baseline_metrics[0]), float(baseline_metrics[1])
    print(f"[BASELINE] Val Loss: {baseline_loss:.4f} | Val Accuracy: {baseline_acc * 100:.2f}%")

    # 3. Unfreeze last N layers
    model = unfreeze_last_n_layers(model, n_layers=unfreeze_layers_count)

    # 4. Re-compile model with low learning rate
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    # 5. Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(v2_model_path),
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-7,
            verbose=1,
        ),
    ]

    # 6. Fine-tune Training
    print(f"\n[INFO] Commencing fine-tuning for {epochs} epochs...")
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=callbacks,
    )

    # 7. Save fine-tuned model v2
    model.save(str(v2_model_path))
    print(f"[INFO] Fine-tuned model v2 saved to: {v2_model_path}")

    # 8. Plot comparison graphs
    plot_fine_tune_comparison(
        history=history,
        baseline_acc=baseline_acc,
        baseline_loss=baseline_loss,
        output_plot_path=plot_file_path,
    )

    # 9. Evaluate final fine-tuned model
    print("\n[INFO] Evaluating fine-tuned model on validation dataset...")
    final_metrics = model.evaluate(val_gen, verbose=1)
    final_loss, final_acc = float(final_metrics[0]), float(final_metrics[1])

    accuracy_improvement = (final_acc - baseline_acc) * 100

    print("\n" + "=" * 80)
    print("FINE-TUNING COMPLETED SUCCESSFULLY")
    print(f"Baseline Validation Accuracy  : {baseline_acc * 100:.2f}%")
    print(f"Fine-Tuned Validation Accuracy: {final_acc * 100:.2f}%")
    print(f"Accuracy Improvement Delta    : {'+' if accuracy_improvement >= 0 else ''}{accuracy_improvement:.2f}%")
    print(f"Baseline Validation Loss      : {baseline_loss:.4f}")
    print(f"Fine-Tuned Validation Loss    : {final_loss:.4f}")
    print(f"Fine-Tuned Model Saved At     : {v2_model_path}")
    print("=" * 80)

    return model, {
        "baseline_accuracy": baseline_acc,
        "baseline_loss": baseline_loss,
        "final_accuracy": final_acc,
        "final_loss": final_loss,
        "accuracy_improvement": accuracy_improvement,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune MobileNetV2 Crop Disease Model")
    parser.add_argument("--model_path", type=str, default="trained_models/disease_model/disease_model.h5", help="Path to base .h5 model")
    parser.add_argument("--dataset_dir", type=str, default="datasets/plantvillage/", help="Path to dataset directory")
    parser.add_argument("--output_dir", type=str, default="trained_models/disease_model/", help="Path to output directory")
    parser.add_argument("--unfreeze_layers", type=int, default=30, help="Number of last layers to unfreeze")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate for fine-tuning")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=10, help="Number of fine-tuning epochs")
    args = parser.parse_args()

    fine_tune_disease_model(
        model_path=args.model_path,
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        unfreeze_layers_count=args.unfreeze_layers,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        epochs=args.epochs,
    )
