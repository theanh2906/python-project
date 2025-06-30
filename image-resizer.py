import os
import time
import tkinter as tk  # Keep tk for standard widgets like Canvas, messagebox, filedialog
from tkinter import filedialog, messagebox
from typing import Optional, Tuple

import customtkinter as ctk  # Import customtkinter
from PIL import Image, ImageTk

# --- Constants ---
WINDOW_TITLE = "Image Resizer"
DEFAULT_WINDOW_GEOMETRY = "1280x720"
# Background colors etc. are largely handled by CTk theme now,
# but we can keep some for specific standard widgets or padding frames.
BACKGROUND_COLOR = "#f5f5f5" # Used by standard tk.Canvas


DEFAULT_PERCENTAGE = "50"
DEFAULT_RESIZE_MODE = "percentage"

# File type filters for dialogs (standard tkinter, unchanged)
IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
    ("All files", "*.*")
]
SAVE_FILETYPES = [
    ("JPEG files", "*.jpg"),
    ("PNG files", "*.png"),
    ("All files", "*.*")
]

# --- Image Processing Helper (Unchanged) ---
class ImageResizer:
    """Handles the core image resizing logic."""

    def resize_image(
            self,
            input_path: str,
            output_path: Optional[str],
            resize_mode: str,
            percentage: Optional[str] = None,
            width: Optional[str] = None,
            height: Optional[str] = None,
            maintain_aspect: bool = True
    ) -> Tuple[int, int, int, int, str]:
        """
        Resizes an image based on provided parameters.

        Args:
            input_path: Path to the input image file.
            output_path: Path to save the output image. If None, generates one.
            resize_mode: 'percentage' or 'dimensions'.
            percentage: Percentage value (as string) if mode is 'percentage'.
            width: Target width (as string) if mode is 'dimensions'.
            height: Target height (as string) if mode is 'dimensions'.
            maintain_aspect: Whether to maintain aspect ratio if mode is 'dimensions'.

        Returns:
            A tuple: (original_width, original_height, new_width, new_height, actual_output_path)

        Raises:
            ValueError: If input parameters are invalid.
            FileNotFoundError: If input file does not exist.
            IOError: If image processing fails.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            img = Image.open(input_path)
            orig_width, orig_height = img.size
        except Exception as e:
            raise IOError(f"Could not open image file: {e}")

        new_width, new_height = None, None

        if resize_mode == "percentage":
            if percentage is None:
                raise ValueError("Percentage value is required for percentage mode.")
            try:
                percent_val = float(percentage)
                if percent_val <= 0:
                    raise ValueError("Percentage must be greater than 0.")
                new_width = int(orig_width * percent_val / 100)
                new_height = int(orig_height * percent_val / 100)
            except ValueError:
                raise ValueError("Invalid percentage value.")

        elif resize_mode == "dimensions":
            width_val: Optional[int] = None
            height_val: Optional[int] = None

            try:
                if width and width.strip():
                    width_val = int(width.strip())
                    if width_val <= 0:
                        raise ValueError("Width must be greater than 0.")
                if height and height.strip():
                    height_val = int(height.strip())
                    if height_val <= 0:
                        raise ValueError("Height must be greater than 0.")
            except ValueError:
                raise ValueError("Invalid dimension value (width or height must be integers).")

            if width_val is None and height_val is None:
                raise ValueError("Please provide at least one dimension (width or height).")

            if maintain_aspect:
                if width_val is not None and height_val is None:
                    new_width = width_val
                    new_height = int(width_val * orig_height / orig_width)
                elif height_val is not None and width_val is None:
                    new_height = height_val
                    new_width = int(new_height * orig_width / orig_height)
                elif width_val is not None and height_val is not None:
                    # If both provided, resize to fit within these dimensions while maintaining aspect ratio
                    ratio_w = width_val / orig_width
                    ratio_h = height_val / orig_height
                    if ratio_w < ratio_h:
                        new_width = width_val
                        new_height = int(orig_height * ratio_w)
                    else:
                        new_height = height_val
                        new_width = int(orig_width * ratio_h)
            else:
                # No aspect ratio maintenance, just use provided values, defaulting to original if None
                new_width = width_val if width_val is not None else orig_width
                new_height = height_val if height_val is not None else orig_height

        else:
            raise ValueError(f"Unknown resize mode: {resize_mode}")

        # Ensure valid dimensions result
        if new_width <= 0 or new_height <= 0:
            raise ValueError("Calculated dimensions are invalid.")


        # Determine output path if not specified
        actual_output_path = output_path
        if not actual_output_path:
            directory = os.path.dirname(input_path) if os.path.dirname(input_path) else "."
            filename, ext = os.path.splitext(os.path.basename(input_path))
            timestamp = int(time.time())
            actual_output_path = os.path.join(directory, f"{filename}_resized_{timestamp}{ext if ext else '.jpg'}")

        try:
            # Use LANCZOS filter which is good for downsizing
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Ensure the output directory exists
            output_dir = os.path.dirname(actual_output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            resized_img.save(actual_output_path)
        except Exception as e:
            raise IOError(f"Could not save resized image: {e}")

        return orig_width, orig_height, new_width, new_height, actual_output_path


# --- GUI Application (Refactored to CustomTkinter) ---
class ImageResizerGUI:
    def __init__(self):
        self._setup_window()
        self._init_variables()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()

        self.image_resizer = ImageResizer() # Instance of the helper class

    def _setup_window(self):
        """Sets up the main application window using CustomTkinter."""
        ctk.set_appearance_mode("System") # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue") # Themes: "blue" (default), "dark-blue", "green"

        self.window = ctk.CTk() # Use CTk root window
        self.window.title(WINDOW_TITLE)
        self.window.geometry(DEFAULT_WINDOW_GEOMETRY)

    def _init_variables(self):
        """Initializes control variables."""
        self.input_path: str = ""
        self.output_path: str = ""
        self.resize_mode = tk.StringVar(value=DEFAULT_RESIZE_MODE) # Tkinter variable still works
        self.percentage_var = tk.StringVar(value=DEFAULT_PERCENTAGE) # Tkinter variable still works
        self.width_var = tk.StringVar(value="")
        self.height_var = tk.StringVar(value="")
        self.maintain_aspect = tk.BooleanVar(value=True) # Tkinter variable still works
        self.preview_photo: Optional[ImageTk.PhotoImage] = None # Keep a reference

    def _create_widgets(self):
        """Creates all the main widgets and frames using CustomTkinter."""
        # Add a top banner
        self.banner_frame = ctk.CTkFrame(self.window, corner_radius=0)
        ctk.CTkLabel(self.banner_frame, text=WINDOW_TITLE,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Create main container frames
        self.outer_frame = ctk.CTkFrame(self.window)
        self.left_frame = ctk.CTkFrame(self.outer_frame)
        self.right_frame = ctk.CTkFrame(self.outer_frame)

        # Use CTkScrollableFrame for the left panel content
        self.scrollable_left_content_frame = ctk.CTkScrollableFrame(self.left_frame, label_text="Settings")

        # --- Widgets inside scrollable_left_content_frame ---

        # File selection frame title and frame
        self.file_frame_title = ctk.CTkLabel(self.scrollable_left_content_frame, text="File Selection",
                                             font=ctk.CTkFont(size=11, weight="bold"))
        self.file_frame = ctk.CTkFrame(self.scrollable_left_content_frame, fg_color="transparent")

        # Input file selection
        input_file_frame = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        ctk.CTkLabel(input_file_frame, text="Input Image:").pack(side="left", pady=5)
        self.input_label = ctk.CTkLabel(input_file_frame, text="No file selected", width=200, anchor="w")
        self.input_label.pack(side="left", padx=10, fill="x", expand=True, pady=5)
        ctk.CTkButton(input_file_frame, text="Browse...", command=self.browse_input, width=80).pack(side="right", pady=5)
        input_file_frame.pack(fill="x")

        # Output file selection
        output_file_frame = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        ctk.CTkLabel(output_file_frame, text="Output Image:").pack(side="left", pady=5)
        self.output_label = ctk.CTkLabel(output_file_frame, text="Auto-generated", width=200, anchor="w")
        self.output_label.pack(side="left", padx=10, fill="x", expand=True, pady=5)
        ctk.CTkButton(output_file_frame, text="Browse...", command=self.browse_output, width=80).pack(side="right", pady=5)
        output_file_frame.pack(fill="x")

        # Options frame title and frame
        self.options_frame_title = ctk.CTkLabel(self.scrollable_left_content_frame, text="Resize Options",
                                                font=ctk.CTkFont(size=11, weight="bold"))
        self.options_frame = ctk.CTkFrame(self.scrollable_left_content_frame, fg_color="transparent")

        # Resize mode selection
        mode_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        ctk.CTkRadioButton(mode_frame, text="Resize by Percentage", variable=self.resize_mode,
                           value="percentage", command=self.update_options).pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(mode_frame, text="Resize by Dimensions", variable=self.resize_mode,
                           value="dimensions", command=self.update_options).pack(side="left", padx=10, pady=5)
        mode_frame.pack(fill="x")

        # Options container (holds percentage or dimension widgets)
        self.options_container = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.options_container.pack(fill="x", pady=10)

        # Process button frame (placed below scrollable frame in layout)
        self.button_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        process_btn = ctk.CTkButton(self.button_frame, text="Resize Image", command=self.process_image)
        process_btn.pack(side="right")

        # --- Widgets inside right_frame (for preview) ---
        # Preview frame title and frame
        self.preview_frame_title = ctk.CTkLabel(self.right_frame, text="Preview",
                                                font=ctk.CTkFont(size=11, weight="bold"))
        self.preview_frame_content = ctk.CTkFrame(self.right_frame, fg_color="transparent") # Frame to hold the canvas

        # Keep tk.Canvas for preview rendering
        self.preview_canvas = tk.Canvas(self.preview_frame_content, bg=BACKGROUND_COLOR, bd=0, highlightthickness=0)
        self.preview_canvas.pack(fill="both", expand=True)


    def _setup_layout(self):
        """Arranges the main frames using pack."""
        self.banner_frame.pack(fill="x")

        # Outer frame holds left (scrollable) and right (preview)
        self.outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left and Right frames within outer_frame
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Arrange content within the left_frame: ScrollableFrame and ButtonFrame
        self.scrollable_left_content_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10) # Added padx here
        self.button_frame.pack(fill="x", pady=10, padx=10) # Added padx here


        # Arrange content within scrollable_left_content_frame: Titles and Frames
        self.file_frame_title.pack(anchor="w", pady=(10, 0)) # Removed padx here, using scrollable frame's padx
        self.file_frame.pack(fill="x", pady=5) # Removed padx here

        self.options_frame_title.pack(anchor="w", pady=(10, 0)) # Removed padx here
        self.options_frame.pack(fill="x", pady=5) # Removed padx here

        # Arrange content within the right_frame: Preview Title and Canvas Frame
        self.preview_frame_title.pack(anchor="w", padx=10, pady=(0, 5))
        self.preview_frame_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initialize options view
        self.update_options()


    def _bind_events(self):
        """Binds events for canvas resizing."""
        # Canvas configure binding is still needed for the preview canvas to know its size
        self.preview_canvas.bind('<Configure>', self._on_preview_canvas_configure)
        # Mouse wheel scrolling on CTkScrollableFrame is handled automatically.

    def _on_preview_canvas_configure(self, event):
        """Triggers a preview update when the preview canvas size changes."""
        if self.input_path:
            # Use window.after to avoid potential issues during resize events
            self.window.after(10, self.update_preview)


    def create_percentage_options(self):
        """Creates widgets for percentage-based resizing using CustomTkinter."""
        for widget in self.options_container.winfo_children():
            widget.destroy()

        frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        frame.pack(fill="x")

        ctk.CTkLabel(frame, text="Resize to:").pack(side="left", padx=(0, 10), pady=5)

        percentage_entry = ctk.CTkEntry(frame, textvariable=self.percentage_var, width=60)
        percentage_entry.pack(side="left", pady=5)

        ctk.CTkLabel(frame, text="% of original size").pack(side="left", padx=5, pady=5)

        # Quick preset buttons
        presets_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        presets_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(presets_frame, text="Quick presets:").pack(side="left", padx=(0, 10), pady=5)

        for preset_text in ["25%", "50%", "75%", "100%"]:
            value = preset_text.replace("%", "")
            ctk.CTkButton(presets_frame, text=preset_text, width=60,
                          command=lambda v=value: self.percentage_var.set(v)).pack(side="left", padx=5, pady=5)


    def create_dimension_options(self):
        """Creates widgets for dimension-based resizing using CustomTkinter."""
        for widget in self.options_container.winfo_children():
            widget.destroy()

        # Width entry
        width_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        ctk.CTkLabel(width_frame, text="Width:").pack(side="left", padx=(0, 10), pady=5)
        width_entry = ctk.CTkEntry(width_frame, textvariable=self.width_var, width=80)
        width_entry.pack(side="left", pady=5)
        ctk.CTkLabel(width_frame, text="pixels").pack(side="left", padx=5, pady=5)
        width_frame.pack(fill="x")

        # Height entry
        height_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        ctk.CTkLabel(height_frame, text="Height:").pack(side="left", padx=(0, 10), pady=5)
        height_entry = ctk.CTkEntry(height_frame, textvariable=self.height_var, width=80)
        height_entry.pack(side="left", pady=5)
        ctk.CTkLabel(height_frame, text="pixels").pack(side="left", padx=5, pady=5)
        height_frame.pack(fill="x")

        # Maintain aspect ratio
        aspect_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        ctk.CTkCheckBox(aspect_frame, text="Maintain aspect ratio",
                        variable=self.maintain_aspect).pack(side="left", pady=5)
        aspect_frame.pack(fill="x", pady=5)


    def update_options(self):
        """Switches between percentage and dimension options view."""
        if self.resize_mode.get() == "percentage":
            self.create_percentage_options()
        else:
            self.create_dimension_options()

    def browse_input(self):
        """Opens file dialog to select input image."""
        input_path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=IMAGE_FILETYPES)
        if input_path:
            self.input_path = input_path
            self.input_label.configure(text=os.path.basename(self.input_path))
            self.output_path = ""
            self.output_label.configure(text="Auto-generated")
            self.update_preview()

    def browse_output(self):
        """Opens file dialog to select output path."""
        initial_file = ""
        if self.input_path:
            filename, ext = os.path.splitext(os.path.basename(self.input_path))
            initial_file = f"{filename}_resized{ext if ext else '.jpg'}"

        output_path = filedialog.asksaveasfilename(
            title="Save Output As",
            defaultextension=".jpg",
            initialfile=initial_file,
            filetypes=SAVE_FILETYPES
        )
        if output_path:
            self.output_path = output_path
            self.output_label.configure(text=os.path.basename(self.output_path))
        else:
            if not self.output_path:
                self.output_label.configure(text="Auto-generated")


    def update_preview(self):
        """Updates the image preview on the canvas."""
        if not self.input_path:
            self.preview_canvas.delete("all")
            self.preview_photo = None
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                self.preview_canvas.create_text(
                    canvas_width // 2,
                    canvas_height // 2,
                    text="Image preview will appear here",
                    anchor="center",
                    fill="black"
                )
            return

        try:
            img = Image.open(self.input_path)
            orig_width, orig_height = img.size

            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                print("Canvas not ready for preview...")
                return

            max_preview_width = canvas_width - 20
            max_preview_height = canvas_height - 20

            max_preview_width = max(1, max_preview_width)
            max_preview_height = max(1, max_preview_height)


            img_copy = img.copy()
            img_copy.thumbnail((max_preview_width, max_preview_height))

            photo = ImageTk.PhotoImage(img_copy)
            self.preview_photo = photo

            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo,
                anchor="center"
            )

            size_text = f"Original: {orig_width} × {orig_height} pixels"
            self.preview_canvas.create_text(10, 10, text=size_text, anchor="nw", fill="black")

        except FileNotFoundError:
            messagebox.showerror("Preview Error", "Input file not found.")
            self.input_path = ""
            self.input_label.configure(text="No file selected")
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Preview Error", f"Could not load or preview image: {str(e)}")


    def process_image(self):
        """Gathers parameters and triggers image resizing."""
        if not self.input_path:
            messagebox.showerror("Error", "Please select an input image.")
            return

        resize_mode = self.resize_mode.get()
        percentage = self.percentage_var.get() if resize_mode == "percentage" else None
        width = self.width_var.get() if resize_mode == "dimensions" else None
        height = self.height_var.get() if resize_mode == "dimensions" else None
        maintain_aspect = self.maintain_aspect.get() if resize_mode == "dimensions" else True

        try:
            orig_width, orig_height, new_width, new_height, actual_output_path = self.image_resizer.resize_image(
                input_path=self.input_path,
                output_path=self.output_path if self.output_path else None,
                resize_mode=resize_mode,
                percentage=percentage,
                width=width,
                height=height,
                maintain_aspect=maintain_aspect
            )

            self.output_path = actual_output_path
            self.output_label.configure(text=os.path.basename(self.output_path))

            try:
                original_size = os.path.getsize(self.input_path)
                resized_size = os.path.getsize(self.output_path)
                if original_size > 0:
                    reduction = 100 - (resized_size / original_size * 100)
                    size_reduction_text = f"File size reduced by: {reduction:.1f}%\n\n"
                else:
                    size_reduction_text = "File size comparison not available.\n\n"
            except Exception:
                size_reduction_text = "File size comparison not available.\n\n"


            message = (f"Image resized successfully!\n\n"
                       f"Original: {orig_width} × {orig_height} pixels\n"
                       f"Resized: {new_width} × {new_height} pixels\n"
                       f"{size_reduction_text}"
                       f"Saved to: {self.output_path}")
            messagebox.showinfo("Success", message)

        except (ValueError, FileNotFoundError, IOError) as e:
            messagebox.showerror("Error", f"Could not resize image: {str(e)}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")


    def run(self):
        """Starts the Tkinter main loop."""
        self.window.mainloop()


# --- Application Entry Point ---
def main():
    """Main function to create and run the GUI application."""
    app = ImageResizerGUI()
    app.run()

if __name__ == "__main__":
    main()