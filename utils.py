import os
from typing import Tuple

import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np


def save_image(image, output_path):
    """
    Save an image to the specified file path.

    Parameters:
        image (numpy.ndarray): The image to save.
        output_path (str): The file path where the image will be saved.

    Returns:
        None
    """
    success = iio.imwrite(output_path, image, plugin='tifffile')
    if success:
        print(f"Image successfully saved to {output_path}")
    else:
        print(f"Error: Unable to save the image to {output_path}")


def display_comparison(original: np.ndarray, processed: np.ndarray,
                       original_title: str, processed_title: str, subplot_figsize: Tuple[int, int] = (12, 6)) -> None:
    """Display original and processed images side by side."""
    plt.figure(figsize=subplot_figsize)

    plt.subplot(1, 2, 1)
    plt.title(original_title)
    plt.imshow(original)
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.title(processed_title)
    plt.imshow(processed)
    plt.axis('off')

    plt.show()


def save_image_from_url(image_url: str, output_path: str) -> bool:
    """
    Save an image from a URL to the specified file path.

    Args:
        image_url: URL of the image to save
        output_path: Path to save the image

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Read and save the image
        image = iio.imread(image_url)
        iio.imwrite(output_path, image, plugin='tifffile')
        print(f"Image successfully saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving image from URL {image_url}: {str(e)}")
        return False
