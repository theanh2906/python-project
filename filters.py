"""
Image filtering using PIL filters.

This module provides functions for applying various PIL filters to images
and displaying the results.
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
from PIL import Image, ImageFilter

from image_utils import display_multiple_images, display_comparison


def apply_pil_filters(image_path: str, display_result: bool = True) -> Dict[str, Image.Image]:
    """
    Apply various PIL filters to an image and optionally display the results.

    Args:
        image_path: Path to the input image
        display_result: Whether to display the filtered images

    Returns:
        Dictionary mapping filter names to filtered images
    """
    # Load the image
    img = Image.open(image_path)
    if img.mode == 'P':
        img = img.convert('RGB')

    # Apply filters
    filtered_images = {
        "Original": img,
        "Blurred": img.filter(ImageFilter.BLUR),
        "Contour": img.filter(ImageFilter.CONTOUR),
        "Detail": img.filter(ImageFilter.DETAIL),
        "Edge Enhance": img.filter(ImageFilter.EDGE_ENHANCE),
        "Edge Enhance More": img.filter(ImageFilter.EDGE_ENHANCE_MORE),
        "Emboss": img.filter(ImageFilter.EMBOSS),
        "Find Edges": img.filter(ImageFilter.FIND_EDGES),
        "Sharpen": img.filter(ImageFilter.SHARPEN),
        "Smooth": img.filter(ImageFilter.SMOOTH),
        "Smooth More": img.filter(ImageFilter.SMOOTH_MORE),
        "Gaussian Blur": img.filter(ImageFilter.GaussianBlur(radius=10))
    }

    # Display the results if requested
    if display_result:
        # Convert PIL images to numpy arrays for display
        images = [np.array(img) for img in filtered_images.values()]
        titles = list(filtered_images.keys())

        # Display the images in a grid
        display_multiple_images(images, titles)

    return filtered_images


def apply_single_filter(
        image_path: str, 
        filter_name: str, 
        output_path: Optional[str] = None,
        display_result: bool = True
) -> Image.Image:
    """
    Apply a single PIL filter to an image.

    Args:
        image_path: Path to the input image
        filter_name: Name of the filter to apply
        output_path: Path to save the filtered image (optional)
        display_result: Whether to display the result

    Returns:
        Filtered image
    """
    # Load the image
    img = Image.open(image_path)
    if img.mode == 'P':
        img = img.convert('RGB')

    # Apply the specified filter
    filter_map = {
        "blur": ImageFilter.BLUR,
        "contour": ImageFilter.CONTOUR,
        "detail": ImageFilter.DETAIL,
        "edge_enhance": ImageFilter.EDGE_ENHANCE,
        "edge_enhance_more": ImageFilter.EDGE_ENHANCE_MORE,
        "emboss": ImageFilter.EMBOSS,
        "find_edges": ImageFilter.FIND_EDGES,
        "sharpen": ImageFilter.SHARPEN,
        "smooth": ImageFilter.SMOOTH,
        "smooth_more": ImageFilter.SMOOTH_MORE,
        "gaussian_blur": ImageFilter.GaussianBlur(radius=10)
    }

    filter_name_lower = filter_name.lower()
    if filter_name_lower not in filter_map:
        raise ValueError(f"Unsupported filter: {filter_name}. Available filters: {', '.join(filter_map.keys())}")

    filtered_img = img.filter(filter_map[filter_name_lower])

    # Display the result if requested
    if display_result:
        # Convert PIL images to numpy arrays for display
        display_comparison(np.array(img), np.array(filtered_img), "Original", f"Filtered ({filter_name})")

    # Save the result if an output path is provided
    if output_path:
        filtered_img.save(output_path)

    return filtered_img


if __name__ == "__main__":
    # Example usage
    # Apply all filters and display them
    apply_pil_filters("images/image.jpg")

    # Apply a single filter
    apply_single_filter(
        "images/image.jpg",
        filter_name="sharpen",
        output_path="images/sharpen_pil.jpg"
    )
