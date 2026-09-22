from PIL import Image


def preprocess_image(image_path: str):
    image = Image.open(image_path)
    return image.resize((224, 224))
