from typing import Tuple

import cv2
import imageio.v3 as iio
from utils import display_comparison
import numpy as np

# Constants for image processing
GAUSSIAN_BLUR_KERNEL_SIZE: int = 7
SHARPENING_AMOUNT: float = 1.5
NOISE_THRESHOLD: int = 10
SUBPLOT_FIGSIZE: Tuple[int, int] = (12, 6)


def load_and_convert_image(image_path: str) -> np.ndarray:
    """Load an image and convert it from BGR to RGB color space."""
    image = cv2.imread(image_path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def apply_unsharp_mask(
        image_path: str,
        output_path: str,
        save_result: bool = False,
        blur_kernel_size: int = GAUSSIAN_BLUR_KERNEL_SIZE,
        sharpening_amount: float = SHARPENING_AMOUNT,
        threshold: int = NOISE_THRESHOLD
) -> np.ndarray:
    """
    Apply unsharp mask filtering to enhance image details.

    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        save_result: Whether to save the processed image
        blur_kernel_size: Size of Gaussian blur kernel (must be odd)
        sharpening_amount: Intensity of sharpening effect
        threshold: Minimum difference for sharpening to reduce noise

    Returns:
        Processed image array
    """
    # Load and prepare image
    image = load_and_convert_image(image_path)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(image, (blur_kernel_size, blur_kernel_size), 0)

    # Calculate and apply unsharp mask
    mask = cv2.subtract(image, blurred)
    sharp = cv2.addWeighted(image, 1.0 + sharpening_amount, blurred, -sharpening_amount, 0)

    # Apply a threshold to reduce noise
    low_contrast_mask = np.absolute(image - blurred).max(axis=2) < threshold
    sharp[low_contrast_mask] = image[low_contrast_mask]

    # Visualize results
    display_comparison(image, sharp, "Original", "Sharpened (Unsharp Mask)", SUBPLOT_FIGSIZE)

    # Save if requested
    if save_result:
        iio.imwrite(output_path, sharp, plugin='tifffile')

    return sharp


# Example usage
if __name__ == "__main__":
    apply_unsharp_mask("images/image.jpg", "images/sharpened.jpg")
