import math
import os
import subprocess
import threading
import json
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk
import numpy as np
import cv2
from pathlib import Path
import time
import pygame  # Add pygame for audio playback


# --- Helper Functions ---

def format_time(seconds):
    """Converts seconds (float) to HH:MM:SS.ms string"""
    if seconds is None or seconds < 0:
        return "00:00:00.000"
    millisec = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hrs:02}:{mins:02}:{secs:02}.{millisec:03}"

def parse_time(time_str):
    """Converts HH:MM:SS.ms string to seconds (float)"""
    try:
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError("Invalid time format")
        hrs = int(parts[0])
        mins = int(parts[1])
        sec_parts = parts[2].split('.')
        secs = int(sec_parts[0])
        millisec = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        # Clamp milliseconds to 3 digits
        millisec_str = f"{millisec:03}"
        millisec = int(millisec_str[:3])

        total_seconds = float(hrs * 3600 + mins * 60 + secs + millisec / 1000.0)
        return total_seconds
    except Exception:
        # Return None or raise a more specific error if parsing fails
        return None

def get_media_duration(filepath, self):
    """Gets media duration in seconds using ffprobe"""
    command = [
        self.ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return duration
    except FileNotFoundError:
        messagebox.showerror("Error", "FFprobe not found. Please ensure FFmpeg (including ffprobe) is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error getting duration: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred getting duration: {e}")
        return None


# --- Main Application Class ---

class MediaCutterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Enhanced Media Cutter")
        self.state('zoomed')  # Start in fullscreen mode
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
        self.ffprobe_path = os.path.join(os.path.dirname(__file__), "ffprobe.exe")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize pygame for audio
        pygame.mixer.init()

        self.input_file = ""
        self.output_file = ""
        self.duration_seconds = 0.0
        self.start_seconds = 0.0
        self.end_seconds = 0.0
        self.recent_files = []
        self.load_recent_files()

        # --- Left Column (Preview and Timeline) ---
        self.left_column = ctk.CTkFrame(self)
        self.left_column.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(1, weight=1)

        # --- Preview Area ---
        self.preview_container = ctk.CTkFrame(self.left_column)
        self.preview_container.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.preview_container.grid_columnconfigure(0, weight=1)
        self.preview_container.grid_rowconfigure(1, weight=1)

        # Preview canvas with fixed size
        self.preview_canvas = ctk.CTkCanvas(self.preview_container, bg="black", width=854, height=480)
        self.preview_canvas.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Preview controls
        self.preview_controls = ctk.CTkFrame(self.preview_container)
        self.preview_controls.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.preview_controls.grid_columnconfigure(1, weight=1)

        self.preview_play_button = ctk.CTkButton(self.preview_controls, text="▶", width=30, command=self.toggle_preview)
        self.preview_play_button.grid(row=0, column=0, padx=5)

        self.preview_time_label = ctk.CTkLabel(self.preview_controls, text="00:00:00.000")
        self.preview_time_label.grid(row=0, column=1, padx=5)

        # --- Timeline with Two Knobs ---
        self.timeline_container = ctk.CTkFrame(self.left_column)
        self.timeline_container.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.timeline_container.grid_columnconfigure(0, weight=1)

        # Timeline canvas for custom slider
        self.timeline_canvas = ctk.CTkCanvas(self.timeline_container, height=60, bg="gray20")
        self.timeline_canvas.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.timeline_canvas.bind("<Configure>", self.draw_timeline)
        self.timeline_canvas.bind("<Button-1>", self.on_timeline_click)
        self.timeline_canvas.bind("<B1-Motion>", self.on_timeline_drag)

        # Time labels
        self.start_time_label = ctk.CTkLabel(self.timeline_container, text="00:00:00.000")
        self.start_time_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")

        self.end_time_label = ctk.CTkLabel(self.timeline_container, text="00:00:00.000")
        self.end_time_label.grid(row=1, column=0, padx=5, pady=2, sticky="e")

        # --- Right Column (Controls) ---
        self.right_column = ctk.CTkFrame(self)
        self.right_column.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_column.grid_columnconfigure(0, weight=1)

        # File Selection
        self.file_frame = ctk.CTkFrame(self.right_column)
        self.file_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)

        self.input_label = ctk.CTkLabel(self.file_frame, text="Input File:")
        self.input_label.grid(row=0, column=0, padx=5, pady=5)

        self.input_entry = ctk.CTkEntry(self.file_frame, placeholder_text="Select a video or audio file...", width=300)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.input_entry.configure(state="disabled")

        self.browse_input_button = ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_input, width=100)
        self.browse_input_button.grid(row=0, column=2, padx=5, pady=5)

        # Recent files dropdown
        self.recent_files_var = ctk.StringVar()
        self.recent_files_dropdown = ctk.CTkOptionMenu(
            self.file_frame,
            values=self.recent_files,
            command=self.load_recent_file,
            variable=self.recent_files_var,
            width=150
        )
        self.recent_files_dropdown.grid(row=0, column=3, padx=5, pady=5)

        # Output Settings
        self.output_frame = ctk.CTkFrame(self.right_column)
        self.output_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)

        self.output_label = ctk.CTkLabel(self.output_frame, text="Save As:")
        self.output_label.grid(row=0, column=0, padx=5, pady=5)

        self.output_entry = ctk.CTkEntry(self.output_frame, placeholder_text="Select output location...", width=300)
        self.output_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.output_entry.configure(state="disabled")

        self.browse_output_button = ctk.CTkButton(self.output_frame, text="Save As...", command=self.browse_output, width=100)
        self.browse_output_button.grid(row=0, column=2, padx=5, pady=5)
        self.browse_output_button.configure(state="disabled")

        # Format and Quality
        self.settings_frame = ctk.CTkFrame(self.right_column)
        self.settings_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.format_label = ctk.CTkLabel(self.settings_frame, text="Format:")
        self.format_label.grid(row=0, column=0, padx=5, pady=5)

        self.format_var = ctk.StringVar(value="Same as input")
        self.format_dropdown = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Same as input", "MP4", "MKV", "AVI", "MOV", "MP3", "WAV"],
            variable=self.format_var,
            width=150
        )
        self.format_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.quality_label = ctk.CTkLabel(self.settings_frame, text="Quality:")
        self.quality_label.grid(row=0, column=2, padx=5, pady=5)

        self.quality_slider = ctk.CTkSlider(self.settings_frame, from_=0, to=100)
        self.quality_slider.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        self.quality_slider.set(80)

        # Action Buttons
        self.button_frame = ctk.CTkFrame(self.right_column)
        self.button_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        self.cut_button = ctk.CTkButton(self.button_frame, text="Cut Media", command=self.start_cutting_thread, width=150)
        self.cut_button.grid(row=0, column=0, padx=5, pady=5)
        self.cut_button.configure(state="disabled")

        self.batch_button = ctk.CTkButton(self.button_frame, text="Batch Process", command=self.browse_batch_files, width=150)
        self.batch_button.grid(row=0, column=1, padx=5, pady=5)

        # Progress Bar
        self.progress_frame = ctk.CTkFrame(self.right_column)
        self.progress_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, padx=5, pady=5)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Status: Load a file to begin.", anchor="w", height=25)
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Preview state
        self.is_preview_playing = False
        self.preview_thread = None
        self.stop_preview = False
        self.audio_thread = None
        self.audio_position = 0
        self.last_preview_time = 0

        # Timeline state
        self.start_knob = None
        self.end_knob = None
        self.dragging_knob = None
        self.knob_radius = 8

    def load_recent_files(self):
        """Load recent files from config file"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".media_cutter_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.recent_files = config.get('recent_files', [])
        except Exception as e:
            print(f"Error loading recent files: {e}")

    def save_recent_files(self):
        """Save recent files to config file"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".media_cutter_config.json")
            config = {'recent_files': self.recent_files}
            with open(config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving recent files: {e}")

    def add_recent_file(self, filepath):
        """Add a file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:10]  # Keep only 10 most recent
        self.recent_files_dropdown.configure(values=self.recent_files)
        self.save_recent_files()

    def load_recent_file(self, filepath):
        """Load a file from recent files list"""
        if os.path.exists(filepath):
            self.input_file = filepath
            self.input_entry.configure(state="normal")
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.input_file)
            self.input_entry.configure(state="disabled")
            self.load_media_info()
            self.suggest_output_path()
            self.browse_output_button.configure(state="normal")

    def toggle_preview(self):
        """Toggle preview playback"""
        if not self.input_file:
            return

        if self.is_preview_playing:
            self.stop_preview = True
            self.is_preview_playing = False
            self.preview_play_button.configure(text="▶")
            pygame.mixer.music.stop()
        else:
            self.stop_preview = False
            self.is_preview_playing = True
            self.preview_play_button.configure(text="⏸")
            
            # Start video preview thread
            self.preview_thread = threading.Thread(target=self.preview_loop)
            self.preview_thread.daemon = True
            self.preview_thread.start()
            
            # Start audio playback
            self.audio_thread = threading.Thread(target=self.audio_loop)
            self.audio_thread.daemon = True
            self.audio_thread.start()

    def audio_loop(self):
        """Handles audio playback"""
        try:
            # Create a unique temporary file name
            temp_dir = os.path.join(os.path.dirname(__file__), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_audio = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.wav")
            
            # Extract audio to temporary file
            command = [
                self.ffmpeg_path,
                '-i', self.input_file,
                '-ss', str(self.start_seconds),
                '-t', str(self.end_seconds - self.start_seconds),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # WAV format
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite
                temp_audio
            ]
            subprocess.run(command, capture_output=True, check=True)
            
            # Play audio
            pygame.mixer.music.load(temp_audio)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and not self.stop_preview:
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.stop()
            try:
                os.remove(temp_audio)
            except Exception as e:
                print(f"Warning: Could not remove temporary audio file: {e}")
            
        except Exception as e:
            print(f"Audio playback error: {e}")
            try:
                if 'temp_audio' in locals():
                    os.remove(temp_audio)
            except:
                pass

    def preview_loop(self):
        """Main preview playback loop"""
        cap = cv2.VideoCapture(self.input_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_time = 1.0 / fps
        
        # Seek to start position
        cap.set(cv2.CAP_PROP_POS_MSEC, self.start_seconds * 1000)
        
        while not self.stop_preview and self.is_preview_playing:
            ret, frame = cap.read()
            if not ret:
                # Loop back to start if we reach the end
                cap.set(cv2.CAP_PROP_POS_MSEC, self.start_seconds * 1000)
                continue

            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            self.preview_time_label.configure(text=format_time(current_time))
            self.timeline_canvas.coords(self.start_knob, (current_time / self.duration_seconds) * 854 - 4, 28, current_time / self.duration_seconds * 854 + 4, 32)
            self.timeline_canvas.coords(self.end_knob, (self.end_seconds / self.duration_seconds) * 854 - 4, 28, (self.end_seconds / self.duration_seconds) * 854 + 4, 32)
            
            # Check if we've reached the end time
            if current_time >= self.end_seconds:
                cap.set(cv2.CAP_PROP_POS_MSEC, self.start_seconds * 1000)
                continue

            # Convert frame to RGB and resize
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (854, 480))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.preview_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.preview_canvas.photo = photo

            # Sleep for frame time
            time.sleep(frame_time)

        cap.release()

    def draw_timeline(self, event=None):
        """Draw the timeline with start and end knobs"""
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        # Clear canvas
        self.timeline_canvas.delete("all")
        
        # Draw timeline track
        track_height = 4
        track_y = height // 2 - track_height // 2
        self.timeline_canvas.create_rectangle(0, track_y, width, track_y + track_height, fill="gray50")
        
        # Draw knobs
        if self.duration_seconds > 0:
            start_x = (self.start_seconds / self.duration_seconds) * width
            end_x = (self.end_seconds / self.duration_seconds) * width
            
            # Draw selected range
            self.timeline_canvas.create_rectangle(start_x, track_y, end_x, track_y + track_height, fill="blue")
            
            # Draw knobs
            self.start_knob = self.timeline_canvas.create_oval(
                start_x - self.knob_radius, track_y - self.knob_radius,
                start_x + self.knob_radius, track_y + track_height + self.knob_radius,
                fill="white", outline="gray"
            )
            
            self.end_knob = self.timeline_canvas.create_oval(
                end_x - self.knob_radius, track_y - self.knob_radius,
                end_x + self.knob_radius, track_y + track_height + self.knob_radius,
                fill="white", outline="gray"
            )

    def on_timeline_click(self, event):
        """Handle timeline click events"""
        if not self.duration_seconds:
            return
            
        width = self.timeline_canvas.winfo_width()
        click_x = event.x
        
        # Check if clicking near a knob
        start_x = (self.start_seconds / self.duration_seconds) * width
        end_x = (self.end_seconds / self.duration_seconds) * width
        
        if abs(click_x - start_x) <= self.knob_radius:
            self.dragging_knob = "start"
        elif abs(click_x - end_x) <= self.knob_radius:
            self.dragging_knob = "end"
        else:
            # If clicking between knobs, move the nearest one
            if abs(click_x - start_x) < abs(click_x - end_x):
                self.dragging_knob = "start"
            else:
                self.dragging_knob = "end"
                
        self.update_timeline_from_click(click_x)

    def on_timeline_drag(self, event):
        """Handle timeline drag events"""
        if self.dragging_knob:
            self.update_timeline_from_click(event.x)

    def update_timeline_from_click(self, x):
        """Update timeline position from click/drag"""
        if not self.duration_seconds:
            return
            
        width = self.timeline_canvas.winfo_width()
        new_time = (x / width) * self.duration_seconds
        
        if self.dragging_knob == "start":
            self.start_seconds = max(0, min(new_time, self.end_seconds - 0.001))
            self.start_time_label.configure(text=format_time(self.start_seconds))
        else:
            self.end_seconds = min(self.duration_seconds, max(new_time, self.start_seconds + 0.001))
            self.end_time_label.configure(text=format_time(self.end_seconds))
            
        self.draw_timeline()
        self.update_preview_from_timeline(None)

    def update_preview_from_timeline(self, event):
        """Update preview when timeline is changed"""
        if not self.input_file:
            return
            
        # Stop current playback
        if self.is_preview_playing:
            self.stop_preview = True
            self.is_preview_playing = False
            pygame.mixer.music.stop()
            self.preview_play_button.configure(text="▶")
            
        # Update preview frame
        cap = cv2.VideoCapture(self.input_file)
        time_seconds = self.start_seconds if self.dragging_knob == "start" else self.end_seconds
        cap.set(cv2.CAP_PROP_POS_MSEC, time_seconds * 1000)
        
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (854, 480))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.preview_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.preview_canvas.photo = photo
            
            # Update time label
            self.preview_time_label.configure(text=format_time(time_seconds))
            
        cap.release()

    def load_media_info(self):
        """Gets duration and updates UI elements."""
        if not self.input_file:
            return

        duration = get_media_duration(self.input_file, self)

        if duration is not None:
            self.duration_seconds = duration
            self.status_bar.configure(text=f"Status: Loaded media. Duration: {format_time(self.duration_seconds)}")

            # Reset times and UI
            self.start_seconds = 0.0
            self.end_seconds = self.duration_seconds
            self.start_time_label.configure(text=format_time(self.start_seconds))
            self.end_time_label.configure(text=format_time(self.end_seconds))
            self.draw_timeline()

            self.cut_button.configure(state="normal")
            self.status_bar.configure(text="Status: Ready. Adjust start/end times.")
        else:
            self.duration_seconds = 0.0
            self.status_bar.configure(text="Status: Error loading media info.")
            self.cut_button.configure(state="disabled")

    def suggest_output_path(self):
        """Suggests a default output path based on the input file."""
        if not self.input_file:
            return
        try:
            input_dir = os.path.dirname(self.input_file)
            base_name, ext = os.path.splitext(os.path.basename(self.input_file))
            default_output = os.path.join(input_dir, f"{base_name}_output{ext}")
            self.output_file = default_output
            self.output_entry.configure(state="normal")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, self.output_file)
            self.output_entry.configure(state="disabled")
        except Exception as e:
            print(f"Error suggesting output path: {e}")

    def browse_output(self):
        """Opens file dialog to select output file path."""
        if not self.input_file:
            messagebox.showwarning("Warning", "Please select an input file first.")
            return

        # Get extension from input to suggest for output
        _, input_ext = os.path.splitext(self.input_file)
        if not input_ext: input_ext = ".mp4" # Default if input has no extension

        filepath = filedialog.asksaveasfilename(
            title="Save Cut Media As...",
            initialfile=os.path.basename(self.output_entry.get()), # Use current suggestion
            initialdir=os.path.dirname(self.output_entry.get()),  # Use current suggestion dir
            defaultextension=input_ext,
            filetypes=(("Matching Extension", f"*{input_ext}"),
                       ("All Files", "*.*"))
        )
        if filepath:
            self.output_file = filepath
            self.output_entry.configure(state="normal")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, self.output_file)
            self.output_entry.configure(state="disabled")

    def browse_input(self):
        """Opens file dialog to select input media file."""
        filepath = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=(("Media Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mp3 *.wav *.ogg *.aac *.flac"),
                       ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv"),
                       ("Audio Files", "*.mp3 *.wav *.ogg *.aac *.flac"),
                       ("All Files", "*.*"))
        )
        if filepath:
            self.input_file = filepath
            self.input_entry.configure(state="normal")
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.input_file)
            self.input_entry.configure(state="disabled")
            self.status_bar.configure(text="Status: Loading media info...")
            self.load_media_info()
            # Suggest default output path
            self.suggest_output_path()
            self.browse_output_button.configure(state="normal")

    def browse_batch_files(self):
        """Open file dialog for batch processing"""
        filepaths = filedialog.askopenfilenames(
            title="Select Media Files",
            filetypes=(("Media Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mp3 *.wav *.ogg *.aac *.flac"),
                       ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv"),
                       ("Audio Files", "*.mp3 *.wav *.ogg *.aac *.flac"),
                       ("All Files", "*.*"))
        )
        if filepaths:
            self.batch_process_files(filepaths)

    def batch_process_files(self, filepaths):
        """Process multiple files with the same settings"""
        if not filepaths:
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        total_files = len(filepaths)
        processed = 0

        for filepath in filepaths:
            try:
                self.progress_label.configure(text=f"Processing {os.path.basename(filepath)}...")
                self.progress_bar.set(processed / total_files)

                # Generate output path
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_format = self.format_var.get()
                if output_format == "Same as input":
                    ext = os.path.splitext(filepath)[1]
                else:
                    ext = f".{output_format.lower()}"
                output_path = os.path.join(output_dir, f"{base_name}_cut{ext}")

                # Run ffmpeg with current settings
                self.run_ffmpeg_cut(
                    filepath,
                    output_path,
                    self.start_seconds,
                    self.end_seconds
                )

                processed += 1
                self.progress_bar.set(processed / total_files)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {filepath}: {str(e)}")

        self.progress_label.configure(text="Batch processing completed")
        messagebox.showinfo("Success", f"Processed {processed} of {total_files} files")

    def run_ffmpeg_cut(self, input_path, output_path, start_time, end_time):
        """Run ffmpeg to cut the media file with progress tracking"""
        duration = end_time - start_time
        quality = int(self.quality_slider.get())

        # Build ffmpeg command with quality settings
        command = [
            self.ffmpeg_path,
            '-y',  # Overwrite output file
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264' if output_path.lower().endswith(('.mp4', '.mkv')) else 'copy',
            '-crf', str(31 - (quality * 0.3)),  # Convert quality (0-100) to CRF (0-51)
            '-c:a', 'aac' if output_path.lower().endswith(('.mp4', '.mkv')) else 'copy',
            output_path
        ]

        process = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if 'time=' in line:
                time_str = line.split('time=')[1].split()[0]
                current_time = parse_time(time_str)
                if current_time is not None:
                    progress = (current_time - start_time) / duration
                    self.progress_bar.set(min(1.0, max(0.0, progress)))

        if process.returncode != 0:
            raise Exception("FFmpeg process failed")

    def start_cutting_thread(self):
        """Validates input and starts the ffmpeg process in a separate thread."""
        if not self.validate_inputs():
            return

        self.set_ui_state("disabled")
        self.status_bar.configure(text="Status: Processing... please wait.")

        # Use the internal float values for precision
        start_t = self.start_seconds
        end_t = self.end_seconds

        # Create and start the processing thread
        thread = threading.Thread(
            target=self.run_ffmpeg_cut,
            args=(self.input_file, self.output_file, start_t, end_t),
            daemon=True # Allows closing app even if thread is running (use cautiously)
        )
        thread.start()

    def validate_inputs(self):
        """Checks if all inputs are valid before cutting."""
        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showerror("Error", "Invalid or missing input file.")
            return False

        if not self.output_file:
            # If output field is empty but input is valid, generate default
            self.suggest_output_path()
            if not self.output_file: # Still no output file (edge case)
                messagebox.showerror("Error", "Please specify an output file location.")
                return False

        # Update internal times from entries one last time
        self.update_timeline_from_click(0)

        if self.start_seconds >= self.end_seconds:
            messagebox.showerror("Error", f"Start time ({format_time(self.start_seconds)}) must be before end time ({format_time(self.end_seconds)}).")
            return False

        if self.start_seconds < 0 or self.end_seconds > self.duration_seconds:
            messagebox.showerror("Error", "Start or end time is outside the media duration.")
            return False

        return True

    def set_ui_state(self, state):
        """Enable/disable UI elements during processing."""
        self.browse_input_button.configure(state=state)
        self.browse_output_button.configure(state=state)
        self.cut_button.configure(state=state)
        self.timeline_canvas.configure(state=state)
        self.start_time_label.configure(state=state)
        self.end_time_label.configure(state=state)

    def __del__(self):
        """Cleanup when the application is closed"""
        try:
            # Stop any playing audio
            pygame.mixer.music.stop()
            
            # Clean up temporary directory
            temp_dir = os.path.join(os.path.dirname(__file__), "temp")
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
        except:
            pass


# --- Run the Application ---
if __name__ == "__main__":
    app = MediaCutterApp()
    app.mainloop()