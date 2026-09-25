import sys
from pathlib import Path

# Ensure backend directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import tensorflow as tf
from utils.image_preprocessing import (
    preprocess_image,
    create_data_generators,
    get_augmentation_pipeline,
)



def test_preprocess_single_image_array():
    img_array = np.random.randint(0, 256, (300, 400, 3), dtype=np.uint8)
    processed = preprocess_image(
        img_array,
        target_size=(224, 224),
        normalize=True,
        expand_batch_dim=True,
    )
    assert processed.shape == (1, 224, 224, 3)
    assert processed.dtype == tf.float32
    assert tf.reduce_max(processed) <= 1.0
    assert tf.reduce_min(processed) >= 0.0


def test_preprocess_batch_images():
    img1 = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img2 = np.random.randint(0, 256, (150, 150, 3), dtype=np.uint8)
    batch = preprocess_image([img1, img2], target_size=(224, 224), normalize=True)
    assert batch.shape == (2, 224, 224, 3)


def test_augmentation_pipeline():
    aug = get_augmentation_pipeline(
        rotation_factor=0.1,
        zoom_factor=0.1,
        brightness_factor=0.1,
        horizontal_flip=True,
    )
    dummy_input = tf.random.uniform((2, 224, 224, 3), minval=0.0, maxval=1.0)
    augmented = aug(dummy_input)
    assert augmented.shape == (2, 224, 224, 3)


if __name__ == "__main__":
    test_preprocess_single_image_array()
    test_preprocess_batch_images()
    test_augmentation_pipeline()
    print("All image preprocessing tests passed successfully!")

