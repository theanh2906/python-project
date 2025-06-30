"""
Image sharpening algorithms for image processing.

This module provides implementations of various image sharpening techniques
including unsharp masking and kernel-based sharpening.
"""

import numpy as np
import cv2
import tensorflow as tf
from typing import Tuple, Optional, Union

from image_utils import load_image, save_image, display_comparison


# Constants
KERNEL_SIZE = 3
CHANNEL_COUNT = 3
IMAGE_SCALE = 256
GAUSSIAN_BLUR_KERNEL_SIZE = 7
SHARPENING_AMOUNT = 1.5
NOISE_THRESHOLD = 10


def create_sharpening_kernel_cv2() -> np.ndarray:
    """
    Create a simple 3x3 sharpening kernel for OpenCV.
    
    Returns:
        3x3 sharpening kernel as numpy array
    """
    return np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])


def create_sharpening_kernel_tf() -> np.ndarray:
    """
    Create a sharpening kernel for TensorFlow.
    
    Returns:
        Sharpening kernel as numpy array
    """
    kernel = np.zeros([KERNEL_SIZE, KERNEL_SIZE, CHANNEL_COUNT, CHANNEL_COUNT])
    center_value = 9.
    edge_value = -1.
    
    for i in range(KERNEL_SIZE):
        for j in range(KERNEL_SIZE):
            if i == 1 and j == 1:
                kernel[i, j, :, :] = center_value
            else:
                kernel[i, j, :, :] = edge_value
    return kernel


def sharpen_with_cv2(image: np.ndarray) -> np.ndarray:
    """
    Sharpen image using OpenCV implementation.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Sharpened image as numpy array
    """
    sharpening_kernel = create_sharpening_kernel_cv2()
    return cv2.filter2D(image, -1, sharpening_kernel)


def sharpen_with_tensorflow(image: np.ndarray) -> np.ndarray:
    """
    Sharpen image using TensorFlow implementation.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Sharpened image as numpy array
    """
    # Convert to float and normalize
    np_img = np.asarray(image, dtype='float32') / IMAGE_SCALE
    reshaped_img = np_img.reshape(1, *np_img.shape)

    kernel = create_sharpening_kernel_tf()
    
    # Use TensorFlow to apply the kernel
    tf.compat.v1.disable_eager_execution()
    x = tf.compat.v1.placeholder('float32', [1, None, None, CHANNEL_COUNT])
    w = tf.Variable(tf.cast(kernel, tf.float32))
    out = tf.nn.depthwise_conv2d(x, w, strides=[1, 1, 1, 1], padding='SAME')
    
    with tf.compat.v1.Session() as sess:
        sess.run(tf.compat.v1.global_variables_initializer())
        output = sess.run(out, feed_dict={x: reshaped_img})
        
    # Normalize the output
    max_value = np.amax(output)
    normalized = output / max_value
    normalized = (normalized * 255).round().astype(np.uint8)
    return np.squeeze(normalized)


def apply_unsharp_mask(
        image: np.ndarray,
        blur_kernel_size: int = GAUSSIAN_BLUR_KERNEL_SIZE,
        sharpening_amount: float = SHARPENING_AMOUNT,
        threshold: int = NOISE_THRESHOLD
) -> np.ndarray:
    """
    Apply unsharp mask filtering to enhance image details.

    Args:
        image: Input image as numpy array
        blur_kernel_size: Size of Gaussian blur kernel (must be odd)
        sharpening_amount: Intensity of sharpening effect
        threshold: Minimum difference for sharpening to reduce noise

    Returns:
        Sharpened image as numpy array
    """
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(image, (blur_kernel_size, blur_kernel_size), 0)

    # Calculate and apply unsharp mask
    mask = cv2.subtract(image, blurred)
    sharp = cv2.addWeighted(image, 1.0 + sharpening_amount, blurred, -sharpening_amount, 0)

    # Apply a threshold to reduce noise
    low_contrast_mask = np.absolute(image - blurred).max(axis=2) < threshold
    sharp[low_contrast_mask] = image[low_contrast_mask]

    return sharp


def sharpen_image(
        image_path: str,
        output_path: Optional[str] = None,
        method: str = "unsharp_mask",
        blur_kernel_size: int = GAUSSIAN_BLUR_KERNEL_SIZE,
        sharpening_amount: float = SHARPENING_AMOUNT,
        threshold: int = NOISE_THRESHOLD,
        display_result: bool = True
) -> np.ndarray:
    """
    Sharpen an image using the specified method.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the output image (optional)
        method: Sharpening method ('unsharp_mask', 'cv2', or 'tensorflow')
        blur_kernel_size: Size of Gaussian blur kernel for unsharp mask
        sharpening_amount: Intensity of sharpening effect for unsharp mask
        threshold: Minimum difference for sharpening to reduce noise
        display_result: Whether to display the result
        
    Returns:
        Sharpened image as numpy array
    """
    # Load the image
    image = load_image(image_path)
    
    # Apply sharpening
    if method.lower() == "unsharp_mask":
        sharpened = apply_unsharp_mask(
            image, 
            blur_kernel_size=blur_kernel_size,
            sharpening_amount=sharpening_amount,
            threshold=threshold
        )
    elif method.lower() == "cv2":
        sharpened = sharpen_with_cv2(image)
    elif method.lower() == "tensorflow":
        sharpened = sharpen_with_tensorflow(image)
    else:
        raise ValueError(f"Unsupported sharpening method: {method}")
    
    # Display the result if requested
    if display_result:
        display_comparison(image, sharpened, "Original", f"Sharpened ({method})")
    
    # Save the result if an output path is provided
    if output_path:
        save_image(sharpened, output_path)
    
    return sharpened


if __name__ == "__main__":
    # Example usage
    sharpen_image(
        "images/image.jpg",
        output_path="images/sharpened.jpg",
        method="unsharp_mask",
        blur_kernel_size=7,
        sharpening_amount=1.5,
        threshold=10
    )