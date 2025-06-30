# Image Processing & Utilities

A comprehensive Python toolkit for image processing, file encryption, directory inspection, media cutting, and more. This package provides both command-line and GUI tools for a wide range of tasks.

## Features

### Image Processing
- **Edge Detection**: Canny algorithm with customizable blur and thresholds.
- **Image Sharpening**: Unsharp Mask, OpenCV kernel, and TensorFlow-based sharpening.
- **Image Filtering**: Apply PIL filters (Blur, Contour, Detail, Emboss, Find Edges, Sharpen, Smooth, Gaussian Blur, and more).
- **Interactive Mode**: Menu-driven interface for easy image processing.

### Utilities & Tools
- **File Encryptor/Hasher**: GUI tool to hash or encode files (MD5, SHA1, SHA256, SHA512, Base64) and export results.
- **Directory Inspector**: Analyze and summarize directory contents.
- **Media Cutter**: GUI tool for cutting and processing video/audio files with a modern interface.
- **Image Resizer**: Batch resize images from the command line or GUI.
- **Web Crawler**: Simple HTML crawler for extracting and saving web content.
- **Lunar Calendar**: Modern calendar application with lunar year support and multiple view modes.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/image-processing.git
cd image-processing

# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS

# Install the package
pip install -e .
```

## Usage

### Command Line

```bash
# Run the main demo
python main.py

# Interactive menu
python main.py --interactive

# Edge detection
python main.py --input images/image.jpg --output output/edges.jpg edge

# Sharpening
python main.py --input images/image.jpg --output output/sharp.jpg sharpen --method unsharp_mask

# Filtering
python main.py --input images/image.jpg --output output/filtered.jpg filter --filter-name find_edges
```

### Python API

```python
from edge_detection import detect_edges
from sharpening import sharpen_image
from filters import apply_single_filter
from image_utils import load_image, save_image

# Example: Edge detection
detect_edges("images/image.jpg", output_path="output/edges.jpg", method="canny")
```

### GUI Tools

- **File Encryptor**: `python tools/file_encryptor.py`
- **Directory Inspector**: `python directory_inspector.py`
- **Media Cutter**: `python media-processing/media_cutter.py`
- **Image Resizer**: `python image-resizer.py`
- **Lunar Calendar**: `python tools/lunar_calendar.py`

## Module Structure

- `main.py`: CLI and interactive menu
- `image_utils.py`: Image I/O and display
- `edge_detection.py`, `canny_edge_detector.py`: Edge detection
- `sharpening.py`, `unsharp_mark_kernel.py`: Sharpening algorithms
- `filters.py`: PIL filter management
- `image_processing.py`: Core processing logic
- `utils.py`: General utilities
- `tools/`: Extra utilities (encryption, web crawling, etc.)
- `media-processing/`: Media cutting and processing tools

## Dependencies

- OpenCV, NumPy, Matplotlib, Pillow, TensorFlow, SciPy, imageio, customtkinter, pygame

## License

MIT
