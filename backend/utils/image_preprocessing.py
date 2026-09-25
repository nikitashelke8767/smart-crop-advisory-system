"""
Image Preprocessing and Data Augmentation Utility Module.

Provides reusable utilities to load, resize, convert RGB, normalize,
and augment images for deep learning workflows using TensorFlow and Keras.
"""

import io
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator


def get_augmentation_pipeline(
    rotation_factor: float = 0.15,
    zoom_factor: float = 0.15,
    brightness_factor: float = 0.2,
    horizontal_flip: bool = True,
) -> tf.keras.Sequential:
    """
    Creates a Keras Sequential model composed of image augmentation layers.

    Augmentations included:
    - Random Rotation
    - Horizontal Flip
    - Random Zoom
    - Random Brightness Adjustment

    Args:
        rotation_factor: Range as a fraction of 2pi [-factor, factor].
        zoom_factor: Range for random height and width zoom.
        brightness_factor: Range for random brightness adjustment.
        horizontal_flip: Boolean indicating whether to enable horizontal flip.

    Returns:
        tf.keras.Sequential: Keras sequential pipeline of augmentation layers.
    """
    augmentation_layers = []

    if horizontal_flip:
        augmentation_layers.append(layers.RandomFlip("horizontal"))

    if rotation_factor > 0:
        augmentation_layers.append(layers.RandomRotation(factor=rotation_factor))

    if zoom_factor > 0:
        augmentation_layers.append(
            layers.RandomZoom(height_factor=zoom_factor, width_factor=zoom_factor)
        )

    if brightness_factor > 0:
        augmentation_layers.append(
            layers.RandomBrightness(factor=brightness_factor, value_range=(0.0, 1.0))
        )

    return tf.keras.Sequential(augmentation_layers, name="image_augmentation_pipeline")


def _single_image_to_tensor(
    image_input: Union[str, Path, bytes, Image.Image, np.ndarray, tf.Tensor]
) -> tf.Tensor:
    """
    Internal helper to convert various image input formats into a 3D float32 tf.Tensor (H, W, 3).
    Ensures RGB channel conversion.
    """
    if isinstance(image_input, (str, Path)):
        file_bytes = tf.io.read_file(str(image_input))
        tensor = tf.io.decode_image(file_bytes, channels=3, expand_animations=False)
    elif isinstance(image_input, bytes):
        tensor = tf.io.decode_image(image_input, channels=3, expand_animations=False)
    elif isinstance(image_input, Image.Image):
        rgb_img = image_input.convert("RGB")
        tensor = tf.convert_to_tensor(np.array(rgb_img), dtype=tf.uint8)
    elif isinstance(image_input, (np.ndarray, tf.Tensor)):
        tensor = tf.convert_to_tensor(image_input)
        # Ensure 3D shape
        if len(tensor.shape) == 2:
            tensor = tf.expand_dims(tensor, axis=-1)
        
        if tensor.shape[-1] == 1:
            tensor = tf.image.grayscale_to_rgb(tensor)
        elif tensor.shape[-1] == 4:
            # RGBA to RGB
            tensor = tensor[..., :3]
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # Ensure shape rank is 3 (H, W, C)
    if len(tensor.shape) == 4 and tensor.shape[0] == 1:
        tensor = tf.squeeze(tensor, axis=0)

    return tensor


def preprocess_image(
    image_input: Union[
        str,
        Path,
        bytes,
        Image.Image,
        np.ndarray,
        tf.Tensor,
        List[Union[str, Path, bytes, Image.Image, np.ndarray, tf.Tensor]],
    ],
    target_size: Tuple[int, int] = (224, 224),
    normalize: bool = True,
    expand_batch_dim: bool = True,
    augment: bool = False,
    augmentation_pipeline: Optional[tf.keras.layers.Layer] = None,
) -> tf.Tensor:
    """
    Loads, converts to RGB, resizes, normalizes, and optionally augments single images or batches.

    Requirements addressed:
    1. Load image (supports filepath, bytes, PIL, numpy, tf.Tensor).
    2. Resize to 224x224 (or custom target_size).
    3. Convert to RGB (3 channels).
    4. Normalize pixel values between 0 and 1.
    5. Support batch processing (list of inputs or 4D tensor/array).
    6. Include image augmentation (Rotation, Horizontal Flip, Zoom, Brightness).

    Args:
        image_input: Single image or list of images in supported formats.
        target_size: Tuple (height, width) for target output resolution. Default (224, 224).
        normalize: Whether to scale pixel values to [0.0, 1.0]. Default True.
        expand_batch_dim: If processing a single image, whether to return shape (1, H, W, C). Default True.
        augment: Whether to apply data augmentation. Default False.
        augmentation_pipeline: Custom Keras augmentation layer/sequential model. If None and augment=True,
                               uses default get_augmentation_pipeline().

    Returns:
        tf.Tensor: Processed float32 image tensor of shape (B, target_h, target_w, 3) or (target_h, target_w, 3).
    """
    is_batch_input = False
    images_list = []

    if isinstance(image_input, list):
        is_batch_input = True
        images_list = image_input
    elif isinstance(image_input, (np.ndarray, tf.Tensor)) and len(image_input.shape) == 4:
        is_batch_input = True
        images_list = [image_input[i] for i in range(image_input.shape[0])]
    else:
        images_list = [image_input]

    processed_tensors = []
    for img in images_list:
        # 1. Load & convert to 3-channel RGB tensor
        raw_tensor = _single_image_to_tensor(img)

        # Cast to float32 for resizing and precision
        float_tensor = tf.cast(raw_tensor, dtype=tf.float32)

        # 2. Resize image
        resized_tensor = tf.image.resize(float_tensor, size=target_size)

        # 3. Normalize pixel values between 0 and 1 if requested
        if normalize:
            # Check if tensor values are scaled up to 255
            max_val = tf.reduce_max(resized_tensor)
            if max_val > 1.0:
                resized_tensor = resized_tensor / 255.0

        processed_tensors.append(resized_tensor)

    # Stack into batch tensor (B, H, W, 3)
    batch_tensor = tf.stack(processed_tensors, axis=0)

    # 4. Optional Augmentation using Keras preprocessing layers
    if augment:
        if augmentation_pipeline is None:
            augmentation_pipeline = get_augmentation_pipeline()
        batch_tensor = augmentation_pipeline(batch_tensor, training=True)

    # Handle output batch dimension formatting
    if not is_batch_input and not expand_batch_dim:
        return tf.squeeze(batch_tensor, axis=0)

    return batch_tensor


def create_data_generators(
    data_dir: Union[str, Path],
    target_size: Tuple[int, int] = (224, 224),
    batch_size: int = 32,
    validation_split: float = 0.2,
    class_mode: str = "categorical",
    shuffle: bool = True,
    seed: int = 42,
    rotation_range: float = 20.0,
    horizontal_flip: bool = True,
    zoom_range: float = 0.15,
    brightness_range: Optional[Tuple[float, float]] = (0.8, 1.2),
    use_tf_dataset: bool = False,
) -> Tuple[Any, Any]:
    """
    Creates training and validation data generators with data augmentation and normalization.

    Args:
        data_dir: Directory path containing class subdirectories.
        target_size: Target image dimensions (height, width). Default (224, 224).
        batch_size: Batch size for training and validation. Default 32.
        validation_split: Fraction of images reserved for validation. Default 0.2.
        class_mode: Type of label arrays returned ('categorical', 'binary', 'sparse', etc.).
        shuffle: Whether to shuffle data batches. Default True.
        seed: Random seed for reproducible dataset splitting.
        rotation_range: Degree range for random rotations.
        horizontal_flip: Enable random horizontal flip.
        zoom_range: Range for random zoom.
        brightness_range: Tuple of (min_brightness, max_brightness) scale.
        use_tf_dataset: If True, returns tf.data.Dataset objects with Keras preprocessing layers.
                        If False, returns Keras ImageDataGenerators.

    Returns:
        Tuple containing (train_generator/dataset, val_generator/dataset).
    """
    data_dir = str(data_dir)

    if use_tf_dataset:
        # Load dataset using tf.keras.utils.image_dataset_from_directory
        train_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            validation_split=validation_split,
            subset="training",
            seed=seed,
            image_size=target_size,
            batch_size=batch_size,
            label_mode=class_mode if class_mode != "categorical" else "categorical",
            shuffle=shuffle,
        )

        val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            validation_split=validation_split,
            subset="validation",
            seed=seed,
            image_size=target_size,
            batch_size=batch_size,
            label_mode=class_mode if class_mode != "categorical" else "categorical",
            shuffle=False,
        )

        # Normalization layer
        rescale_layer = layers.Rescaling(1.0 / 255.0)
        aug_pipeline = get_augmentation_pipeline(
            rotation_factor=rotation_range / 360.0,
            zoom_factor=zoom_range,
            brightness_factor=0.2 if brightness_range else 0.0,
            horizontal_flip=horizontal_flip,
        )

        # Map normalization and augmentation
        train_ds = train_ds.map(
            lambda x, y: (aug_pipeline(rescale_layer(x), training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE,
        )
        val_ds = val_ds.map(
            lambda x, y: (rescale_layer(x), y),
            num_parallel_calls=tf.data.AUTOTUNE,
        )

        return train_ds.prefetch(tf.data.AUTOTUNE), val_ds.prefetch(tf.data.AUTOTUNE)

    # Standard Keras ImageDataGenerator
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        rotation_range=rotation_range,
        horizontal_flip=horizontal_flip,
        zoom_range=zoom_range,
        brightness_range=brightness_range,
        validation_split=validation_split,
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=validation_split,
    )

    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=target_size,
        batch_size=batch_size,
        class_mode=class_mode,
        subset="training",
        shuffle=shuffle,
        seed=seed,
    )

    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=target_size,
        batch_size=batch_size,
        class_mode=class_mode,
        subset="validation",
        shuffle=False,
        seed=seed,
    )

    return train_generator, val_generator
