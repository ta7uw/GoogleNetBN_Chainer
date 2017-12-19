import numpy as np
from PIL import Image


def resize(image, insize):
    """
    Resize image from original size to size for training
    """
    image = image[:3, ...].astype(np.uint8)
    image = image.transpose(1, 2, 0)
    image = Image.fromarray(image)
    image = image.resize((insize, insize), Image.BICUBIC)

    return np.asarray(image).transpose(2, 0, 1)
