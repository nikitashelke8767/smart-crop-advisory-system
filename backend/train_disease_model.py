"""
Production-Ready TensorFlow Training Script for Crop Disease Detection.

Model Architecture: MobileNetV2 (Transfer Learning)
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
    Resolves the dataset directory path, automatically navigating to a subfolder
    (e.g., 'Tomato') if class folders are nested inside it.
    """
    base_dir = Path(base_dir).resolve()
    if not base_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found at {base_dir}")

    # Check subdirectories
    subdirs = [d for d in base_dir.iterdir() if d.is_dir()]

    # If subdirectories contain image files directly, base_dir is the dataset root
    has_direct_images = any(
        any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in d.iterdir() if f.is_file())
        for d in subdirs
    )

    if not has_direct_images:
        # Check one level deeper (e.g., datasets/plantvillage/Tomato)
        for subdir in subdirs:
            child_subdirs = [d for d in subdir.iterdir() if d.is_dir()]
            child_has_images = any(
                any(f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] for f in c.iterdir() if f.is_file())
                for c in child_subdirs
            )
            if child_has_images:
                return subdir

    return base_dir



def build_disease_model(
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    num_classes: int = 10,
    learning_rate: float = 0.001,
) -> tf.keras.Model:
    """
    Builds a MobileNetV2 transfer learning model for crop disease classification.

    Architecture:
    1. MobileNetV2 base (pretrained on ImageNet, frozen)
    2. GlobalAveragePooling2D
    3. Dense(128, activation='relu')
    4. Dropout(0.3)
    5. Dense(num_classes, activation='softmax')
    """
    # Load pretrained MobileNetV2 base
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )

    # Freeze base layers
    base_model.trainable = False

    # Construct classification head
    inputs = tf.keras.Input(shape=input_shape, name="input_image")
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = tf.keras.layers.Dense(128, activation="relu", name="dense_128")(x)
    x = tf.keras.layers.Dropout(0.3, name="dropout_0.3")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="output_classification")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="MobileNetV2_Disease_Model")

    # Compile model
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def plot_training_history(history: tf.keras.callbacks.History, output_plot_path: Path) -> None:
    """
    Generates and saves Training & Validation Accuracy and Loss plots.
    """
    acc = history.history.get("accuracy", [])
    val_acc = history.history.get("val_accuracy", [])
    loss = history.history.get("loss", [])
    val_loss = history.history.get("val_loss", [])
    epochs_range = range(1, len(acc) + 1)

    plt.figure(figsize=(12, 5))

    # Accuracy Plot
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label="Training Accuracy", marker="o")
    plt.plot(epochs_range, val_acc, label="Validation Accuracy", marker="s")
    plt.title("Training and Validation Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right")

    # Loss Plot
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label="Training Loss", marker="o")
    plt.plot(epochs_range, val_loss, label="Validation Loss", marker="s")
    plt.title("Training and Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper right")

    plt.tight_layout()
    output_plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, dpi=300)
    plt.close()
    print(f"[INFO] Training plots saved to: {output_plot_path}")


def train_disease_model(
    dataset_dir: str = "datasets/plantvillage/",
    output_dir: str = "trained_models/disease_model/",
    target_size: Tuple[int, int] = (224, 224),
    batch_size: int = 32,
    epochs: int = 15,
    validation_split: float = 0.2,
) -> Tuple[tf.keras.Model, Dict[str, float]]:
    """
    Full training pipeline for plant disease detection.

    Steps:
    1. Resolve dataset directory and create train/val generators with augmentation.
    2. Build & compile MobileNetV2 transfer learning model.
    3. Train using EarlyStopping, ModelCheckpoint, and ReduceLROnPlateau.
    4. Save model (.h5) and class names (.json).
    5. Generate accuracy/loss plots and display final validation accuracy.
    """
    project_root = BACKEND_DIR.parent
    raw_dataset_path = (project_root / dataset_dir).resolve() if not Path(dataset_dir).is_absolute() else Path(dataset_dir)
    resolved_dataset_path = resolve_dataset_dir(raw_dataset_path)

    out_path = (project_root / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    model_file_path = out_path / "disease_model.h5"
    class_names_path = out_path / "class_names.json"
    plot_file_path = out_path / "accuracy_loss_plot.png"

    print("=" * 80)
    print("STARTING PLANT DISEASE MODEL TRAINING")
    print(f"Dataset Path   : {resolved_dataset_path}")
    print(f"Output Directory: {out_path}")
    print(f"Image Dimensions: {target_size}")
    print(f"Batch Size      : {batch_size}")
    print(f"Epochs          : {epochs}")
    print("=" * 80)

    # 1. Create data generators with augmentation
    train_gen, val_gen = create_data_generators(
        data_dir=resolved_dataset_path,
        target_size=target_size,
        batch_size=batch_size,
        validation_split=validation_split,
        shuffle=True,
        rotation_range=20.0,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=(0.8, 1.2),
    )

    class_indices = train_gen.class_indices
    class_names = list(class_indices.keys())
    num_classes = len(class_names)
    print(f"[INFO] Found {num_classes} classes: {class_names}")

    # Save class names JSON
    with open(class_names_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=4)
    print(f"[INFO] Saved class names to: {class_names_path}")

    # 2. Build MobileNetV2 transfer learning model
    model = build_disease_model(
        input_shape=(target_size[0], target_size[1], 3),
        num_classes=num_classes,
        learning_rate=0.001,
    )
    model.summary()

    # 3. Define Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(model_file_path),
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.2,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    # 4. Train Model
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=callbacks,
    )

    # 5. Save model explicitly (ensures best model saved even if checkpoint updated)
    model.save(str(model_file_path))
    print(f"[INFO] Model successfully saved to: {model_file_path}")

    # 6. Generate accuracy and loss plots
    plot_training_history(history, plot_file_path)

    # 7. Evaluate final performance on validation set
    print("\n[INFO] Evaluating final model on validation dataset...")
    val_metrics = model.evaluate(val_gen, verbose=1)
    val_loss, val_acc = val_metrics[0], val_metrics[1]

    print("\n" + "=" * 80)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print(f"Final Validation Loss    : {val_loss:.4f}")
    print(f"Final Validation Accuracy: {val_acc * 100:.2f}%")
    print("=" * 80)

    return model, {"val_loss": float(val_loss), "val_accuracy": float(val_acc)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MobileNetV2 Disease Classifier")
    parser.add_argument("--dataset_dir", type=str, default="datasets/plantvillage/", help="Path to dataset directory")
    parser.add_argument("--output_dir", type=str, default="trained_models/disease_model/", help="Path to output directory")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    args = parser.parse_args()

    train_disease_model(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        epochs=args.epochs,
    )
