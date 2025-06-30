"""
Utility functions for image loading, saving, and display.

This module provides common functionality for working with images across
the image processing package.
"""

from typing import Tuple, Optional, Union
import os

import cv2
import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def load_image(image_path: str, as_grayscale: bool = False) -> np.ndarray:
    """
    Load an image from a file path.
    
    Args:
        image_path: Path to the image file
        as_grayscale: Whether to load the image as grayscale
        
    Returns:
        Image as a numpy array
        
    Raises:
        ValueError: If the image cannot be loaded
    """
    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")
        
    try:
        if as_grayscale:
            image = iio.imread(image_path, mode="L")
        else:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    except Exception as e:
        raise ValueError(f"Error loading image {image_path}: {str(e)}")


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Save an image to the specified file path.
    
    Args:
        image: The image to save as a numpy array
        output_path: The file path where the image will be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        success = iio.imwrite(output_path, image, plugin='tifffile')
        if success:
            print(f"Image successfully saved to {output_path}")
            return True
        else:
            print(f"Error: Unable to save the image to {output_path}")
            return False
    except Exception as e:
        print(f"Error saving image to {output_path}: {str(e)}")
        return False


def display_comparison(original: np.ndarray, processed: np.ndarray,
                       original_title: str = "Original", 
                       processed_title: str = "Processed", 
                       subplot_figsize: Tuple[int, int] = (12, 6)) -> None:
    """
    Display original and processed images side by side.
    
    Args:
        original: Original image as numpy array
        processed: Processed image as numpy array
        original_title: Title for the original image
        processed_title: Title for the processed image
        subplot_figsize: Figure size for the subplot
    """
    plt.figure(figsize=subplot_figsize)

    plt.subplot(1, 2, 1)
    plt.title(original_title)
    plt.imshow(original)
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.title(processed_title)
    plt.imshow(processed)
    plt.axis('off')

    plt.tight_layout()
    plt.show()


def display_multiple_images(images: list, titles: list, 
                           rows: int = None, cols: int = None,
                           figsize: Tuple[int, int] = (15, 15)) -> None:
    """
    Display multiple images in a grid.
    
    Args:
        images: List of images to display
        titles: List of titles for each image
        rows: Number of rows in the grid (calculated automatically if None)
        cols: Number of columns in the grid (calculated automatically if None)
        figsize: Figure size
    """
    n_images = len(images)
    if n_images == 0:
        return
        
    if rows is None and cols is None:
        # Calculate a reasonable grid size
        cols = min(4, n_images)
        rows = (n_images + cols - 1) // cols
    elif rows is None:
        rows = (n_images + cols - 1) // cols
    elif cols is None:
        cols = (n_images + rows - 1) // rows
        
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    
    if rows * cols == 1:
        axes = np.array([axes])
    
    axes = axes.flatten()
    
    for i, (image, title) in enumerate(zip(images, titles)):
        if i < len(axes):
            axes[i].imshow(image)
            axes[i].set_title(title)
            axes[i].axis("off")
    
    # Hide any unused subplots
    for i in range(n_images, len(axes)):
        axes[i].axis("off")
        
    plt.tight_layout()
    plt.show()