"""
Image sharpening algorithms.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from image_utils import load_image, save_image, display_comparison

def sharpen_image(image_path: str, 
                  output_path: str = None, 
                  method: str = "unsharp_mask",
                  blur_kernel_size: int = 7,
                  sharpening_amount: float = 1.5,
                  threshold: int = 10,
                  display_result: bool = True):
    """
    Sharpen an image using the specified method.
    """
    image = load_image(image_path)
    
    if method == "unsharp_mask":
        # Unsharp masking: original + amount * (original - blurred)
        blurred = gaussian_filter(image, sigma=blur_kernel_size/6.0)
        sharpened = image + sharpening_amount * (image.astype(float) - blurred.astype(float))
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    else:
        # Default fallback
        sharpened = image
        
    if display_result:
        display_comparison(image, sharpened, "Original", f"Sharpened ({method})")
        
    if output_path:
        save_image(sharpened, output_path)
        
    return sharpened
