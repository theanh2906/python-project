"""
Edge detection algorithms for image processing.

This module provides implementations of various edge detection algorithms
including Canny edge detection.
"""

from typing import Optional

import numpy as np
from image_utils import load_image, save_image, display_comparison
from scipy.ndimage import convolve, gaussian_filter


def canny_edge_detector(image: np.ndarray, 
                        blur: float = 1.0, 
                        high_threshold: int = 91, 
                        low_threshold: int = 31) -> np.ndarray:
    """
    Apply Canny edge detection algorithm to an image.
    
    Args:
        image: Input image as numpy array
        blur: Gaussian blur sigma value
        high_threshold: High threshold for edge detection
        low_threshold: Low threshold for edge detection
        
    Returns:
        Binary edge map as numpy array
    """
    # Convert to float to prevent clipping values
    image = np.array(image, dtype=float)

    # Gaussian blur to reduce noise
    blurred = gaussian_filter(image, blur)

    # Use sobel filters to get horizontal and vertical gradients
    gradient_h = convolve(blurred, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    gradient_v = convolve(blurred, [[1, 2, 1], [0, 0, 0], [-1, -2, -1]])

    # Get gradient magnitude and direction
    gradient = np.power(np.power(gradient_h, 2.0) + np.power(gradient_v, 2.0), 0.5)
    theta = np.arctan2(gradient_v, gradient_h)
    # Quantize direction into 4 directions (0, 45, 90, 135 degrees)
    theta_quantized = (np.round(theta * (5.0 / np.pi)) + 5) % 5

    # Non-maximum suppression
    gradient_suppressed = gradient.copy()
    for r in range(image.shape[0]):
        for c in range(image.shape[1]):
            # Suppress pixels at the image edge
            if r == 0 or r == image.shape[0] - 1 or c == 0 or c == image.shape[1] - 1:
                gradient_suppressed[r, c] = 0
                continue
                
            tq = theta_quantized[r, c] % 4

            if tq == 0:  # 0 is E-W (horizontal)
                if gradient[r, c] <= gradient[r, c-1] or gradient[r, c] <= gradient[r, c+1]:
                    gradient_suppressed[r, c] = 0
            elif tq == 1:  # 1 is NE-SW
                if gradient[r, c] <= gradient[r-1, c+1] or gradient[r, c] <= gradient[r+1, c-1]:
                    gradient_suppressed[r, c] = 0
            elif tq == 2:  # 2 is N-S (vertical)
                if gradient[r, c] <= gradient[r-1, c] or gradient[r, c] <= gradient[r+1, c]:
                    gradient_suppressed[r, c] = 0
            elif tq == 3:  # 3 is NW-SE
                if gradient[r, c] <= gradient[r-1, c-1] or gradient[r, c] <= gradient[r+1, c+1]:
                    gradient_suppressed[r, c] = 0

    # Double threshold
    strong_edges = (gradient_suppressed > high_threshold)

    # Strong has value 2, weak has value 1
    thresholded_edges = np.array(strong_edges, dtype=np.uint8) + (gradient_suppressed > low_threshold)

    # Tracing edges with hysteresis
    # Find weak edge pixels near strong edge pixels
    final_edges = strong_edges.copy()
    current_pixels = []
    
    for r in range(1, image.shape[0] - 1):
        for c in range(1, image.shape[1] - 1):
            if thresholded_edges[r, c] != 1:
                continue  # Not a weak pixel

            # Get 3x3 patch
            local_patch = thresholded_edges[r-1:r+2, c-1:c+2]
            patch_max = local_patch.max()
            if patch_max == 2:
                current_pixels.append((r, c))
                final_edges[r, c] = 1

    # Extend strong edges based on current pixels
    while len(current_pixels) > 0:
        new_pixels = []
        for r, c in current_pixels:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0:
                        continue
                    r2 = r + dr
                    c2 = c + dc
                    if thresholded_edges[r2, c2] == 1 and final_edges[r2, c2] == 0:
                        # Copy this weak pixel to final result
                        new_pixels.append((r2, c2))
                        final_edges[r2, c2] = 1
        current_pixels = new_pixels

    return final_edges


def detect_edges(image_path: str, 
                output_path: Optional[str] = None,
                method: str = "canny",
                blur: float = 1.0,
                high_threshold: int = 91,
                low_threshold: int = 31,
                display_result: bool = True) -> np.ndarray:
    """
    Detect edges in an image using the specified method.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the output image (optional)
        method: Edge detection method ('canny' is currently the only supported method)
        blur: Gaussian blur sigma value
        high_threshold: High threshold for edge detection
        low_threshold: Low threshold for edge detection
        display_result: Whether to display the result
        
    Returns:
        Edge map as numpy array
    """
    # Load the image
    image = load_image(image_path, as_grayscale=True)
    
    # Apply edge detection
    if method.lower() == "canny":
        edges = canny_edge_detector(
            image, 
            blur=blur, 
            high_threshold=high_threshold, 
            low_threshold=low_threshold
        )
    else:
        raise ValueError(f"Unsupported edge detection method: {method}")
    
    # Display the result if requested
    if display_result:
        display_comparison(image, edges, "Original", f"{method.capitalize()} Edges")
    
    # Save the result if an output path is provided
    if output_path:
        save_image(edges, output_path)
    
    return edges


if __name__ == "__main__":
    # Example usage
    detect_edges(
        "../images/background_landscape.png",
        output_path="images/edges.jpg",
        method="canny",
        blur=1.0,
        high_threshold=91,
        low_threshold=31
    )