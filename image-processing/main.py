"""
Main entry point for the image processing application GUI.
"""

import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from sharpening import sharpen_image

from edge_detection import detect_edges
from filters import apply_pil_filters, apply_single_filter


class ImageProcessingGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image Processing Tool")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')

        style = ttk.Style()
        style.configure('TLabelframe', background='#f0f0f0')
        style.configure('TLabelframe.Label', font=('Helvetica', 10, 'bold'))
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('TRadiobutton', font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 10))

        self.input_path = None
        self.output_path = None

        # Main container
        main_container = ttk.Frame(self.window, padding="20")
        main_container.pack(fill="both", expand=True)

        # Input frame
        input_frame = ttk.LabelFrame(main_container, text="Input Image", padding=15)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.input_label = ttk.Label(input_frame, text="No image selected")
        self.input_label.pack(side="left", padx=5)

        browse_btn = ttk.Button(input_frame, text="Browse", command=self.browse_input)
        browse_btn.pack(side="right")

        # Output frame  
        output_frame = ttk.LabelFrame(main_container, text="Output Path", padding=15)
        output_frame.pack(fill="x", padx=10, pady=5)

        self.output_label = ttk.Label(output_frame, text="Default: output/timestamp.jpg")
        self.output_label.pack(side="left", padx=5)

        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="right")

        # Processing options frame
        options_frame = ttk.LabelFrame(main_container, text="Processing Options", padding=15)
        options_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Radio buttons container
        radio_frame = ttk.Frame(options_frame)
        radio_frame.pack(fill="x", padx=5, pady=5)

        # Processing type selection with better spacing
        self.process_type = tk.StringVar(value="edge")
        for text, value in [("Edge Detection", "edge"),
                            ("Image Sharpening", "sharpen"),
                            ("Apply Filters", "filter")]:
            rb = ttk.Radiobutton(radio_frame, text=text, value=value,
                                 variable=self.process_type, command=self.update_options)
            rb.pack(side="left", padx=20)

        # Options container frame with scrollbar
        container_frame = ttk.Frame(options_frame)
        container_frame.pack(fill="both", expand=True, pady=10)

        canvas = tk.Canvas(container_frame)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        self.options_container = ttk.Frame(canvas)

        self.options_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.options_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollable area
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Initialize edge detection options (default)
        self.create_edge_options()

        # Process button 
        process_btn = ttk.Button(main_container, text="Process Image", command=self.process_image)
        process_btn.pack(pady=15)

    def create_edge_options(self):
        for widget in self.options_container.winfo_children():
            widget.destroy()

        # Create frames for better organization
        method_frame = ttk.LabelFrame(self.options_container, text="Edge Detection Method", padding=10)
        method_frame.pack(fill="x", padx=20, pady=5)

        params_frame = ttk.LabelFrame(self.options_container, text="Parameters", padding=10)
        params_frame.pack(fill="x", padx=20, pady=5)

        self.edge_method = tk.StringVar(value="canny")
        ttk.Radiobutton(method_frame, text="Canny Edge Detection", value="canny",
                        variable=self.edge_method).pack(padx=10, pady=5)

        # Parameters with better layout
        # Create entry widgets first
        self.edge_blur = ttk.Entry(params_frame)
        self.edge_high = ttk.Entry(params_frame)
        self.edge_low = ttk.Entry(params_frame)

        # Then use them in the param_entries list
        param_entries = [
            ("Blur:", "1.0", self.edge_blur),
            ("High Threshold:", "91", self.edge_high),
            ("Low Threshold:", "31", self.edge_low)
        ]

        for label_text, default_val, entry in param_entries:
            frame = ttk.Frame(params_frame)
            frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(frame, text=label_text).pack(side="left", padx=(0, 10))
            entry.pack(side="right", padx=5)
            entry.insert(0, default_val)

    def create_sharpen_options(self):
        for widget in self.options_container.winfo_children():
            widget.destroy()

        # Method selection frame
        method_frame = ttk.LabelFrame(self.options_container, text="Sharpening Method", padding=10)
        method_frame.pack(fill="x", padx=20, pady=5)

        self.sharpen_method = tk.StringVar(value="unsharp_mask")
        methods = [("Unsharp Mask", "unsharp_mask"),
                   ("OpenCV", "cv2"),
                   ("TensorFlow", "tensorflow")]

        for text, value in methods:
            ttk.Radiobutton(method_frame, text=text, value=value,
                            variable=self.sharpen_method).pack(padx=10, pady=2)

        # Parameters frame
        params_frame = ttk.LabelFrame(self.options_container, text="Parameters", padding=10)
        params_frame.pack(fill="x", padx=20, pady=5)

        # Create entry widgets first
        self.kernel_size = ttk.Entry(params_frame)
        self.sharpen_amount = ttk.Entry(params_frame)
        self.sharpen_threshold = ttk.Entry(params_frame)

        param_entries = [
            ("Blur Kernel Size:", "7", self.kernel_size),
            ("Sharpening Amount:", "1.5", self.sharpen_amount),
            ("Threshold:", "10", self.sharpen_threshold)
        ]

        for label_text, default_val, entry in param_entries:
            frame = ttk.Frame(params_frame)
            frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(frame, text=label_text).pack(side="left", padx=(0, 10))
            entry.pack(side="right", padx=5)
            entry.insert(0, default_val)

    def create_filter_options(self):
        for widget in self.options_container.winfo_children():
            widget.destroy()

        filter_frame = ttk.LabelFrame(self.options_container, text="Filter Selection", padding=10)
        filter_frame.pack(fill="x", padx=20, pady=5)

        self.filter_choice = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All Filters", value="all",
                        variable=self.filter_choice).pack(padx=10, pady=5)

        filters = ["BLUR", "CONTOUR", "DETAIL", "EDGE_ENHANCE", "EDGE_ENHANCE_MORE",
                   "EMBOSS", "FIND_EDGES", "SHARPEN", "SMOOTH", "SMOOTH_MORE"]

        # Create grid of filter options
        for i, f in enumerate(filters):
            row = (i // 2) + 1
            col = i % 2
            ttk.Radiobutton(filter_frame, text=f, value=f.lower(),
                            variable=self.filter_choice).grid(row=row, column=col,
                                                              padx=20, pady=5, sticky="w")

    def update_options(self):
        process_type = self.process_type.get()
        if process_type == "edge":
            self.create_edge_options()
        elif process_type == "sharpen":
            self.create_sharpen_options()
        else:  # filter
            self.create_filter_options()

    def browse_input(self):
        self.input_path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if self.input_path:
            self.input_label.config(text=os.path.basename(self.input_path))

    def browse_output(self):
        self.output_path = filedialog.asksaveasfilename(
            title="Save Output As",
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")])
        if self.output_path:
            self.output_label.config(text=os.path.basename(self.output_path))

    def process_image(self):
        if not self.input_path:
            messagebox.showerror("Error", "Please select an input image")
            return

        if not self.output_path:
            timestamp = int(time.time())
            self.output_path = os.path.join("../output", f"{timestamp}.jpg")
            os.makedirs("../output", exist_ok=True)

        process_type = self.process_type.get()

        try:
            if process_type == "edge":
                detect_edges(
                    self.input_path,
                    output_path=self.output_path,
                    method=self.edge_method.get(),
                    blur=float(self.edge_blur.get()),
                    high_threshold=int(self.edge_high.get()),
                    low_threshold=int(self.edge_low.get())
                )

            elif process_type == "sharpen":
                sharpen_image(
                    self.input_path,
                    output_path=self.output_path,
                    method=self.sharpen_method.get(),
                    blur_kernel_size=int(self.kernel_size.get()),
                    sharpening_amount=float(self.sharpen_amount.get()),
                    threshold=int(self.sharpen_threshold.get())
                )

            else:  # filter
                if self.filter_choice.get() == "all":
                    apply_pil_filters(self.input_path)
                else:
                    apply_single_filter(
                        self.input_path,
                        filter_name=self.filter_choice.get(),
                        output_path=self.output_path
                    )

            messagebox.showinfo("Success", f"Image processed and saved to {self.output_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    app = ImageProcessingGUI()
    app.window.mainloop()


if __name__ == "__main__":
    main()
