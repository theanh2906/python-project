import os
import platform
import shutil
import subprocess
import threading
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
from customtkinter import ThemeManager  # To get theme colors


# --- Core Logic (Improved Efficiency) ---
def get_directory_items_improved(base_path, status_callback=None):
    """
    Gets items directly under base_path and calculates folder sizes efficiently.

    Args:
        base_path (str): The directory path to inspect.
        status_callback (callable, optional): Function to call with status updates.

    Returns:
        list: A list of tuples: (name, size, type, path).
              Returns None if base_path is invalid or inaccessible.
    """
    items = []
    folder_sizes = {}  # Store calculated sizes {path: size}
    permission_errors = []  # Collect permission errors

    def onerror(os_error):
        # Custom error handler for os.walk to report errors without stopping
        print(f"PermissionError accessing: {os_error.filename} - {os_error.strerror}")
        permission_errors.append(os_error.filename)
        if status_callback:
            # Update status briefly about permission issue
            status_callback(f"Permission denied: {os.path.basename(os_error.filename)}...")

    try:
        # Check if path is valid and accessible before walking
        if not os.path.isdir(base_path):
            if status_callback: status_callback(f"Error: Path not found or not a directory: {base_path}")
            return None
        # Attempt a listing to check permissions early
        os.listdir(base_path)

        if status_callback: status_callback(f"Scanning: {base_path}...")

        # Use topdown=False to calculate directory sizes after their contents
        for root, dirs, files in os.walk(base_path, topdown=False, onerror=onerror):
            current_dir_size = 0

            # Calculate size of files in the current directory
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    # Check if it's a symbolic link, skip if broken
                    if os.path.islink(file_path) and not os.path.exists(file_path):
                        print(f"Skipping broken link: {file_path}")
                        if root == base_path:
                            items.append((f, -2, "LINK (Broken)", file_path))  # Indicate broken link
                        continue

                    file_size = os.path.getsize(file_path)
                    current_dir_size += file_size
                    # If the file is directly in the base_path, add it to items
                    if root == base_path:
                        item_type = "LINK" if os.path.islink(file_path) else "FILE"
                        items.append((f, file_size, item_type, file_path))
                except OSError as e:
                    print(f"Could not get size for file: {file_path} - {e}")
                    # Optionally add file with size 0 or -1 to indicate error
                    if root == base_path:
                        items.append((f, -1, "FILE (Error)", file_path))  # Indicate error with -1

            # Add sizes of subdirectories already calculated
            for d in dirs:
                dir_path = os.path.join(root, d)
                sub_dir_size = folder_sizes.get(dir_path, 0)  # Get calculated size
                current_dir_size += sub_dir_size
                # If the folder is directly in the base_path, add it to items
                if root == base_path:
                    item_type = "FOLDER_LINK" if os.path.islink(dir_path) else "FOLDER"
                    items.append((d, sub_dir_size, item_type, dir_path))

            # Store the total size of the current directory
            folder_sizes[root] = current_dir_size

        if status_callback:
            final_msg = "Scan complete."
            if permission_errors:
                final_msg += f" ({len(permission_errors)} permission error(s))"
            status_callback(final_msg)
        return items

    except FileNotFoundError:
        if status_callback: status_callback(f"Error: Path not found: {base_path}")
        messagebox.showerror("Error", f"The specified directory does not exist:\n{base_path}")
        return None
    except PermissionError:
        if status_callback: status_callback(f"Error: Permission denied for: {base_path}")
        messagebox.showerror("Error", f"Permission denied to access:\n{base_path}")
        return None
    except Exception as e:
        if status_callback: status_callback(f"An unexpected error occurred: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        return None


def format_size(size_bytes):
    """Formats size in bytes to a more readable format (KB, MB, GB)."""
    if size_bytes == -1:
        return "N/A (Error)"
    if size_bytes == -2:
        return "N/A (Broken Link)"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.1f} GB"


def open_explorer(path):
    """Opens the file explorer to the specified path."""
    try:
        if platform.system() == "Windows":
            # Use os.startfile on Windows for better handling of paths
            # Ensure the path exists before trying to open
            if os.path.isdir(path):
                os.startfile(path)
            elif os.path.isfile(path):
                # Select the file in the explorer
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
            else:
                messagebox.showwarning("Open Path", f"Path does not exist or is not accessible:\n{path}")
        elif platform.system() == "Darwin":  # macOS
            # Check if path exists
            if os.path.exists(path):
                subprocess.run(['open', path if os.path.isdir(path) else os.path.dirname(path)])
            else:
                messagebox.showwarning("Open Path", f"Path does not exist or is not accessible:\n{path}")
        else:  # Linux and other Unix-like
            # Check if path exists
            if os.path.exists(path):
                # Use xdg-open for broad compatibility
                subprocess.run(['xdg-open', path if os.path.isdir(path) else os.path.dirname(path)])
            else:
                messagebox.showwarning("Open Path", f"Path does not exist or is not accessible:\n{path}")
    except FileNotFoundError:
        messagebox.showerror("Error", "Could not find the file explorer command (e.g., explorer, open, xdg-open).")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open path:\n{path}\n\nError: {e}")
        print(f"Error opening path {path}: {e}")


# --- GUI Application ---

class DirectoryInspectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Directory Inspector")
        self.geometry("1200x800")  # Increased size for better visibility
        self.resizable(True, True)  # Allow window resizing

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.current_items = []
        self.scan_thread = None
        self.path_history = {}
        self.current_path = ""
        self.sort_ascending = False  # Default: descending for size, ascending for name

        # --- Configure grid layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Make the results frame expand

        # --- Top Frame (Directory Selection) ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.dir_label = ctk.CTkLabel(self.top_frame, text="Directory:")
        self.dir_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.dir_entry_var = ctk.StringVar()
        self.dir_entry = ctk.CTkEntry(self.top_frame, textvariable=self.dir_entry_var, state='disabled')
        self.dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browse_button = ctk.CTkButton(self.top_frame, text="Browse...", command=self.browse_directory, width=80)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Breadcrumb Frame ---
        self.breadcrumb_frame = ctk.CTkFrame(self)
        self.breadcrumb_frame.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.breadcrumb_frame.grid_columnconfigure(0, weight=1)

        self.breadcrumb_var = ctk.StringVar(value="← Select a directory using 'Browse...'")
        self.breadcrumb_label = ctk.CTkLabel(self.breadcrumb_frame, textvariable=self.breadcrumb_var,
                                             anchor="w", padx=10)
        self.breadcrumb_label.grid(row=0, column=0, sticky="ew", pady=5)

        # --- Controls Frame ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        self.controls_frame.grid_columnconfigure(7, weight=1)  # Push status/progress to the right

        # Navigation buttons
        self.back_button = ctk.CTkButton(self.controls_frame, text="⬆️ Up",
                                         command=self.go_to_parent_folder, width=60)
        self.back_button.grid(row=0, column=0, padx=(5, 10), pady=5)
        self.back_button.configure(state="disabled")

        # Scan button
        self.scan_button = ctk.CTkButton(self.controls_frame, text="Scan", command=self.start_scan, width=70)
        self.scan_button.grid(row=0, column=1, padx=0, pady=5)

        # File operations buttons
        self.delete_file_button = ctk.CTkButton(self.controls_frame, text="Delete File",
                                               command=self.delete_file, width=80)
        self.delete_file_button.grid(row=0, column=2, padx=5, pady=5)
        self.delete_file_button.configure(state="disabled")

        self.delete_folder_button = ctk.CTkButton(self.controls_frame, text="Delete Folder",
                                                 command=self.delete_folder, width=80)
        self.delete_folder_button.grid(row=0, column=3, padx=5, pady=5)
        self.delete_folder_button.configure(state="disabled")

        self.create_folder_button = ctk.CTkButton(self.controls_frame, text="Create Folder",
                                                 command=self.create_folder, width=80)
        self.create_folder_button.grid(row=0, column=4, padx=5, pady=5)

        # Sort controls
        self.sort_label = ctk.CTkLabel(self.controls_frame, text="Sort by:")
        self.sort_label.grid(row=0, column=5, padx=(15, 2), pady=5)

        self.sort_var = ctk.StringVar(value="name")
        self.sort_name_radio = ctk.CTkRadioButton(self.controls_frame, text="Name", variable=self.sort_var,
                                                  value="name", command=self.sort_and_display)
        self.sort_name_radio.grid(row=0, column=6, padx=2, pady=5)
        self.sort_size_radio = ctk.CTkRadioButton(self.controls_frame, text="Size", variable=self.sort_var,
                                                  value="size", command=self.sort_and_display)
        self.sort_size_radio.grid(row=0, column=7, padx=2, pady=5)

        # Sort direction button
        self.sort_direction_button = ctk.CTkButton(self.controls_frame, text="⬇", width=30,
                                                   command=self.toggle_sort_direction)
        self.sort_direction_button.grid(row=0, column=8, padx=(5, 10), pady=5)
        self._update_sort_direction_button()

        # --- Status and Progress ---
        self.status_progress_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.status_progress_frame.grid(row=0, column=9, padx=(10, 5), pady=0, sticky="ew")
        self.status_progress_frame.grid_columnconfigure(0, weight=1)

        self.status_label_var = ctk.StringVar(value="Ready.")
        self.status_label = ctk.CTkLabel(self.status_progress_frame, textvariable=self.status_label_var, anchor="w")
        self.status_label.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.status_progress_frame, height=10, width=150)
        self.progress_bar.set(0)

        # --- Results Frame ---
        self.results_outer_frame = ctk.CTkFrame(self)
        self.results_outer_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.results_outer_frame.grid_rowconfigure(1, weight=1)
        self.results_outer_frame.grid_columnconfigure(0, weight=1)

        # Header Row
        self.header_frame = ctk.CTkFrame(self.results_outer_frame, fg_color="transparent", corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 2))
        self.header_frame.grid_columnconfigure(0, weight=2, minsize=150)  # Name
        self.header_frame.grid_columnconfigure(1, weight=1, minsize=100)  # Type
        self.header_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Size
        self.header_frame.grid_columnconfigure(3, weight=4, minsize=200)  # Path

        ctk.CTkLabel(self.header_frame, text="Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.header_frame, text="Type", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.header_frame, text="Size", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="e", padx=5)
        ctk.CTkLabel(self.header_frame, text="Path", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, sticky="w", padx=5)

        # Scrollable Frame for results
        self.results_frame = ctk.CTkScrollableFrame(self.results_outer_frame, label_text="Contents", corner_radius=0)
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.results_frame.grid_columnconfigure(0, weight=2)  # Name
        self.results_frame.grid_columnconfigure(1, weight=1)  # Type
        self.results_frame.grid_columnconfigure(2, weight=1)  # Size
        self.results_frame.grid_columnconfigure(3, weight=4)  # Path

    def delete_file(self):
        selected = self.get_selected_item()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file to delete")
            return

        name, size, item_type, path = selected
        if item_type != "FILE":
            messagebox.showwarning("Warning", "Please select a file, not a folder")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {name}?"):
            try:
                os.remove(path)
                self.update_status(f"Deleted file: {name}")
                self.start_scan()  # Refresh the view
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

    def delete_folder(self):
        selected = self.get_selected_item()
        if not selected:
            messagebox.showwarning("Warning", "Please select a folder to delete")
            return

        name, size, item_type, path = selected
        if item_type != "FOLDER":
            messagebox.showwarning("Warning", "Please select a folder, not a file")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {name} and all its contents?"):
            try:
                shutil.rmtree(path)
                self.update_status(f"Deleted folder: {name}")
                self.start_scan()  # Refresh the view
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder: {str(e)}")

    def create_folder(self):
        if not self.current_path:
            messagebox.showwarning("Warning", "Please select a directory first")
            return

        folder_name = simpledialog.askstring("Create Folder", "Enter folder name:")
        if folder_name:
            try:
                os.makedirs(os.path.join(self.current_path, folder_name), exist_ok=True)
                self.update_status(f"Created folder: {folder_name}")
                self.start_scan()  # Refresh the view
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {str(e)}")

    def get_selected_item(self):
        """Returns the currently selected item's details."""
        if not self.current_items:
            return None

        # Get the selected row index from the results frame
        selected_widgets = self.results_frame.winfo_children()
        for i, widget in enumerate(selected_widgets):
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "transparent":
                return self.current_items[i]
        return None

    def browse_directory(self):
        """Opens directory selection dialog and updates entry."""
        path = filedialog.askdirectory(initialdir=self.current_path or os.path.expanduser("~"))
        if path:
            self.dir_entry_var.set(path)
            self.status_label_var.set(f"Selected: {path}. Click Scan.")
            self.current_items = []
            self.update_results_display()
            self.current_path = ""  # Reset until scan confirms
            self.update_breadcrumb()
            self.back_button.configure(state="disabled")  # Disable until scan
            self._update_file_operation_buttons()

    def update_status(self, message):
        """Updates the status label (thread-safe)."""
        self.after(0, self.status_label_var.set, message)

    def update_breadcrumb(self):
        """Updates the breadcrumb with the current path."""
        if not self.current_path or not os.path.exists(self.current_path):
            self.breadcrumb_var.set("← Select a directory using 'Browse...'")
            return

        # Normalize path for display
        display_path = os.path.normpath(self.current_path)
        # Limit length if too long
        max_len = 100
        if len(display_path) > max_len:
            parts = display_path.split(os.sep)
            if len(parts) > 3:
                # Show root, ellipsis, last two parts
                display_path = os.sep.join([parts[0], "...", parts[-2], parts[-1]])
            else:  # Just truncate if structure is shallow
                display_path = display_path[:max_len - 3] + "..."

        self.breadcrumb_var.set(f"Current: {display_path}")

    def go_to_parent_folder(self):
        """Navigate to the parent folder of the current directory."""
        if not self.current_path:
            return

        parent_path = os.path.dirname(self.current_path)
        # Check if parent exists and is different from current (avoid getting stuck at root)
        if parent_path != self.current_path and os.path.isdir(parent_path):
            self.navigate_to_folder(parent_path)
        else:
            self.status_label_var.set("Already at the top level.")
            self.back_button.configure(state="disabled")

    def navigate_to_folder(self, folder_path):
        """Navigate to the specified folder path (scan if not cached)."""
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", f"Cannot navigate: Not a valid directory.\n{folder_path}")
            return

        self.current_path = os.path.normpath(folder_path)  # Normalize
        self.dir_entry_var.set(self.current_path)  # Update entry box
        self.update_breadcrumb()

        # Update back button state
        parent_of_target = os.path.dirname(self.current_path)
        can_go_back = parent_of_target != self.current_path and os.path.isdir(parent_of_target)
        self.back_button.configure(state="normal" if can_go_back else "disabled")

        # Check cache
        if folder_path in self.path_history:
            self.current_items = self.path_history[folder_path]
            self.sort_and_display()
            self.update_status(
                f"Loaded {len(self.current_items)} items from cache for {os.path.basename(folder_path)}.")
        else:
            # Scan the new folder
            self.start_scan()  # This will also update current_path and breadcrumb

    def _set_controls_state(self, state):
        """Enable/disable controls during scan. state='disabled' or 'normal'"""
        self.scan_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.back_button.configure(state=state if self.back_button.cget(
            "state") != "disabled" else "disabled")  # Keep disabled if it was already
        self.sort_name_radio.configure(state=state)
        self.sort_size_radio.configure(state=state)
        self.sort_direction_button.configure(state=state)
        self._update_file_operation_buttons()

    def _update_file_operation_buttons(self):
        """Update the state of file operation buttons based on current selection."""
        selected = self.get_selected_item()
        if selected:
            name, size, item_type, path = selected
            self.delete_file_button.configure(state="normal" if item_type == "FILE" else "disabled")
            self.delete_folder_button.configure(state="normal" if item_type == "FOLDER" else "disabled")
        else:
            self.delete_file_button.configure(state="disabled")
            self.delete_folder_button.configure(state="disabled")

    def start_scan(self):
        path = self.dir_entry_var.get()
        if not path:
            messagebox.showwarning("Warning", "Please select a directory to scan.")
            return
        self.status_label_var.set("Scanning...")
        self.progress_bar.set(0)
        self._clear_results()
        def scan():
            items = get_directory_items_improved(path, status_callback=self.update_status)
            self.current_items = items if items else []
            self.sort_and_display()
            self.status_label_var.set("Scan complete.")
            self.progress_bar.set(1)
        threading.Thread(target=scan, daemon=True).start()

    def run_scan_thread(self, base_path):
        """The actual scanning logic run in the background thread."""
        items = None
        error_occurred = False
        try:
            items = get_directory_items_improved(base_path, status_callback=self.update_status)
            if items is not None:
                self.current_items = items
                self.path_history[base_path] = items  # Cache results
                # Schedule GUI update back on the main thread
                self.after(0, self.sort_and_display)
            else:
                # Error handled within get_directory_items_improved
                error_occurred = True
                self.current_items = []
                self.after(0, self.update_results_display)  # Clear display on error
        except Exception as e:
            error_occurred = True
            print(f"Error in scan thread: {e}")
            self.after(0, self.update_status, f"Error during scan: {e}")
            self.after(0, lambda: messagebox.showerror("Scan Error",
                                                       f"An unexpected error occurred during scanning:\n{e}"))
        finally:
            # --- Stop Loading State (using self.after for thread safety) ---
            def finalize_ui():
                self.progress_bar.stop()
                self.progress_bar.grid_remove()  # Hide progress bar
                self.scan_button.configure(text="Scan")
                self._set_controls_state("normal")  # Re-enable controls

                # Set final status message
                if not error_occurred and items is not None:
                    perm_errors = getattr(items, '_permission_errors', 0)  # Check if we added this attribute
                    msg = f"Scan complete. Found {len(self.current_items)} items."
                    if perm_errors > 0:
                        msg += f" ({perm_errors} permission errors)"
                    self.update_status(msg)
                elif not error_occurred and items is None and os.path.isdir(base_path):
                    # Path valid, but scan returned None (likely internal permission error during walk)
                    self.update_status("Scan finished. Check console for permission errors.")
                elif error_occurred:
                    # Status already set by error handlers or update_status callback
                    pass
                else:  # Path was invalid from the start
                    self.update_status("Ready.")  # Reset status

            self.after(0, finalize_ui)
            # ---

    def toggle_sort_direction(self):
        """Toggles the sort direction and updates the button."""
        self.sort_ascending = not self.sort_ascending
        self._update_sort_direction_button()
        self.sort_and_display()

    def _update_sort_direction_button(self):
        """Updates the sort direction button text (arrow)."""
        arrow = "⬆" if self.sort_ascending else "⬇"
        self.sort_direction_button.configure(text=arrow)

    def _clear_results(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def _display_items(self, items):
        self._clear_results()
        import datetime
        font = ctk.CTkFont(family="Consolas", size=12)
        for idx, (name, size, item_type, path) in enumerate(items):
            # Name as clickable link if folder
            if item_type.startswith("FOLDER"):
                name_label = ctk.CTkLabel(self.results_frame, text=name, font=font, anchor="w", text_color="#0078D7", cursor="hand2")
                # Use default argument in lambda to capture current path
                name_label.bind("<Button-1>", lambda e, p=path: self.navigate_to_folder(p))
            else:
                name_label = ctk.CTkLabel(self.results_frame, text=name, font=font, anchor="w")
            name_label.grid(row=idx, column=0, sticky="ew", padx=5, pady=1)
            type_label = ctk.CTkLabel(self.results_frame, text=item_type, font=font, anchor="w")
            type_label.grid(row=idx, column=1, sticky="ew", padx=5, pady=1)
            size_label = ctk.CTkLabel(self.results_frame, text=format_size(size), font=font, anchor="e")
            size_label.grid(row=idx, column=2, sticky="ew", padx=5, pady=1)
            path_label = ctk.CTkLabel(self.results_frame, text=path, font=font, anchor="w")
            path_label.grid(row=idx, column=3, sticky="ew", padx=5, pady=1)
            # Modified date
            if len(items[idx]) > 4:
                mtime = items[idx][4]
                mod_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                mod_label = ctk.CTkLabel(self.results_frame, text=mod_str, font=font, anchor="w")
                mod_label.grid(row=idx, column=4, sticky="ew", padx=5, pady=1)

    def sort_and_display(self):
        if not self.current_items:
            return
        key = self.sort_var.get()
        reverse = not self.sort_ascending if key == "size" else self.sort_ascending
        if key == "name":
            sorted_items = sorted(self.current_items, key=lambda x: x[0].lower(), reverse=reverse)
        else:
            sorted_items = sorted(self.current_items, key=lambda x: x[1], reverse=reverse)
        self._display_items(sorted_items)

    def update_results_display(self):
        """Clears and redraws the items in the results frame."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.current_items:
            no_items_label = ctk.CTkLabel(self.results_frame,
                                          text="Directory is empty or contains no accessible items.", text_color="gray")
            no_items_label.grid(row=0, column=0, columnspan=4, pady=20, padx=10, sticky="w")
            return

        # Get the theme's hyperlink color for clickable items
        try:
            # Attempt to get the standard blue link color used in themes
            link_color = ThemeManager.theme["CTkButton"]["fg_color"]
            if isinstance(link_color, (list, tuple)):  # Handle light/dark mode tuple
                link_color = link_color[0] if ctk.get_appearance_mode() == "Light" else link_color[1]
        except:
            link_color = "#0078D7"  # Fallback blue

        text_color = ThemeManager.theme["CTkLabel"]["text_color"]
        if isinstance(text_color, (list, tuple)):
            text_color = text_color[0] if ctk.get_appearance_mode() == "Light" else text_color[1]

        dim_text_color = "gray60"  # For less important text like path

        for i, (name, size, item_type, path) in enumerate(self.current_items):
            # Truncate long names/paths for display
            display_name = name if len(name) < 45 else name[:42] + "..."
            # Show more of the end of the path
            display_path_full = os.path.normpath(path)
            display_path = display_path_full if len(display_path_full) < 65 else "..." + display_path_full[-(65 - 3):]

            # Create a frame for each item
            item_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
            item_frame.grid(row=i, column=0, columnspan=4, sticky="ew", padx=0, pady=1)
            item_frame.grid_columnconfigure(0, weight=2)  # Name
            item_frame.grid_columnconfigure(1, weight=1)  # Type
            item_frame.grid_columnconfigure(2, weight=1)  # Size
            item_frame.grid_columnconfigure(3, weight=4)  # Path

            # Create labels
            name_label = ctk.CTkLabel(item_frame, text=display_name, anchor="w", cursor="")
            type_label = ctk.CTkLabel(item_frame, text=item_type, anchor="w", cursor="")
            size_label = ctk.CTkLabel(item_frame, text=format_size(size), anchor="e")
            path_label = ctk.CTkLabel(item_frame, text=display_path, anchor="w", text_color=dim_text_color,
                                      cursor="hand2")

            # Grid the labels
            name_label.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
            type_label.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
            size_label.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
            path_label.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

            # Make items clickable
            if item_type.startswith("FOLDER"):  # Catches FOLDER and FOLDER_LINK
                name_label.configure(text_color=link_color, cursor="hand2")
                type_label.configure(cursor="hand2")
                name_label.bind("<Button-1>", lambda e, p=path: self.navigate_to_folder(p))
                type_label.bind("<Button-1>", lambda e, p=path: self.navigate_to_folder(p))

            # Make path clickable to open in explorer
            path_label.configure(text_color=link_color)
            path_label.bind("<Button-1>", lambda e, p=path: open_explorer(p))

            # Add selection highlight
            item_frame.bind("<Button-1>", lambda e, f=item_frame: self.select_item(f))
            for child in item_frame.winfo_children():
                child.bind("<Button-1>", lambda e, f=item_frame: self.select_item(f))

    def select_item(self, item_frame):
        """Handles item selection in the results display."""
        # Clear previous selection
        for widget in self.results_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color="transparent")

        # Highlight selected item
        item_frame.configure(fg_color=ThemeManager.theme["CTkButton"]["hover_color"])

        # Update file operation buttons
        self._update_file_operation_buttons()


if __name__ == "__main__":
    app = DirectoryInspectorApp()
    app.mainloop()

