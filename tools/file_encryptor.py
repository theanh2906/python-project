import base64
import hashlib
import json
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pygame

# Initialize pygame mixer for sound effects
try:
    pygame.mixer.init()
except pygame.error:
    print("Warning: pygame.mixer could not be initialized. Sound effects will be disabled.")

# Supported hashing algorithms
HASH_ALGOS = {
    'MD5': hashlib.md5,
    'SHA1': hashlib.sha1,
    'SHA256': hashlib.sha256,
    'SHA512': hashlib.sha512
}


class FileEncryptorGUI:
    def __init__(self):
        self._setup_window()
        self._init_variables()
        self._create_widgets()
        self._setup_layout()
        self._load_sounds()

    def _setup_window(self):
        """Sets up the main application window using CustomTkinter."""
        ctk.set_appearance_mode("Dark")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

        self.root = ctk.CTk()  # Use CTk root window
        self.root.title('File Encryptor/Hasher')
        self.root.geometry("500x600")

    def _init_variables(self):
        """Initializes control variables."""
        self.file_path = ''
        self.algo_var = ctk.StringVar(value='SHA256')
        self.mode_var = ctk.StringVar(value='Hash')  # New: Mode switch

    def _load_sounds(self):
        """Load sound effects for the application."""
        try:
            # Create sounds directory if it doesn't exist
            sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
            os.makedirs(sounds_dir, exist_ok=True)

            # Define sound file paths
            self.success_sound_path = os.path.join(sounds_dir, "success.wav")
            self.error_sound_path = os.path.join(sounds_dir, "error.wav")

            # Create default sound files if they don't exist
            if not os.path.exists(self.success_sound_path):
                self._create_default_sound(self.success_sound_path, frequency=440, duration=500)  # A4 note

            if not os.path.exists(self.error_sound_path):
                self._create_default_sound(self.error_sound_path, frequency=220, duration=500)  # A3 note

            # Load sounds
            self.success_sound = pygame.mixer.Sound(self.success_sound_path)
            self.error_sound = pygame.mixer.Sound(self.error_sound_path)
        except Exception as e:
            print(f"Failed to load sounds: {e}")

            # Create dummy sound objects that do nothing when played
            class DummySound:
                def play(self): pass

            self.success_sound = DummySound()
            self.error_sound = DummySound()

    def _create_default_sound(self, file_path, frequency=440, duration=500):
        """Create a simple WAV file with a sine wave tone."""
        import wave
        import struct
        import math

        # Parameters
        sample_rate = 44100  # CD quality
        num_samples = int(duration * (sample_rate / 1000.0))

        # Generate sine wave samples
        samples = []
        for i in range(num_samples):
            sample = 32767.0 * math.sin(2 * math.pi * frequency * i / sample_rate)
            samples.append(int(sample))

        # Create WAV file
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setparams((1, 2, sample_rate, num_samples, 'NONE', 'not compressed'))
            packed_samples = struct.pack('h' * len(samples), *samples)
            wav_file.writeframes(packed_samples)

    def _create_widgets(self):
        """Creates all the main widgets and frames using CustomTkinter."""
        # Add a top banner
        self.banner_frame = ctk.CTkFrame(self.root, corner_radius=0)
        ctk.CTkLabel(self.banner_frame, text="File Encryptor/Hasher",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Main content frame
        self.main_frame = ctk.CTkFrame(self.root)

        # File selection frame
        self.file_frame = ctk.CTkFrame(self.main_frame)
        ctk.CTkLabel(self.file_frame, text="File Selection:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # File selection row
        self.file_select_frame = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        ctk.CTkLabel(self.file_select_frame, text="Input File:").pack(side="left", padx=(10, 5))
        self.file_label = ctk.CTkLabel(self.file_select_frame, text="No file selected", width=200, anchor="w")
        self.file_label.pack(side="left", padx=5, fill="x", expand=True)
        self.browse_btn = ctk.CTkButton(self.file_select_frame, text="Browse...", command=self.browse_file, width=80)
        self.browse_btn.pack(side="right", padx=10)

        # Mode selection (Hash/Encode)
        self.mode_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ctk.CTkLabel(self.mode_frame, text="Mode:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.hash_radio = ctk.CTkRadioButton(self.mode_frame, text="Hash", variable=self.mode_var, value="Hash",
                                             command=self._on_mode_change)
        self.hash_radio.pack(side="left", padx=5)
        self.encode_radio = ctk.CTkRadioButton(self.mode_frame, text="Encode", variable=self.mode_var, value="Encode",
                                               command=self._on_mode_change)
        self.encode_radio.pack(side="left", padx=5)

        # Algorithm selection frame
        self.algo_frame = ctk.CTkFrame(self.main_frame)
        ctk.CTkLabel(self.algo_frame, text="Encryption Algorithm:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # Create radio buttons for each algorithm
        self.algo_buttons_frame = ctk.CTkFrame(self.algo_frame, fg_color="transparent")
        for i, algo in enumerate(HASH_ALGOS.keys()):
            ctk.CTkRadioButton(self.algo_buttons_frame, text=algo, variable=self.algo_var,
                               value=algo).pack(side="left", padx=10, pady=5)

        # Hash/Encoded output area
        self.output_area = ctk.CTkTextbox(self.main_frame, height=80, state="disabled")

        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.main_frame)
        self.encrypt_btn = ctk.CTkButton(self.action_frame, text="View Hash",
                                         command=self.hash_file,
                                         font=ctk.CTkFont(weight="bold"),
                                         height=40)
        self.copy_hash_btn = ctk.CTkButton(self.action_frame, text="Copy Hash", command=self.copy_hash, height=40)
        self.export_btn = ctk.CTkButton(self.action_frame, text="Encode & Export", command=self.encode_and_export,
                                        height=40)

        # Status frame
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready to encrypt files")
        self.status_label.pack(pady=10, padx=10)

    def _setup_layout(self):
        """Arranges the main frames using pack."""
        # Banner at the top
        self.banner_frame.pack(fill="x")

        # Main content frame
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # File selection section
        self.file_frame.pack(fill="x", pady=(0, 10))
        self.file_select_frame.pack(fill="x", pady=5)

        # Mode selection section
        self.mode_frame.pack(fill="x", pady=(0, 10))

        # Algorithm selection section
        self.algo_frame.pack(fill="x", pady=(10, 10))
        self.algo_buttons_frame.pack(fill="x", pady=5)

        # Hash/Encoded output area
        self.output_area.pack(fill="x", pady=(10, 0), padx=10)

        # Action buttons section
        self.action_frame.pack(fill="x", pady=(20, 10))
        self.encrypt_btn.pack(pady=10, padx=10, side="left", expand=True)
        self.copy_hash_btn.pack(pady=10, padx=10, side="left", expand=True)
        self.export_btn.pack(pady=10, padx=10, side="right", expand=True)

        # Status section at the bottom
        self.status_frame.pack(fill="x", side="bottom")

        self._on_mode_change()  # Set initial state

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "Hash":
            self.encrypt_btn.pack(side="left", padx=10, expand=True)
            self.encrypt_btn.configure(text="View Hash", state="normal")
            self.export_btn.pack_forget()
            self.copy_hash_btn.pack(side="right", padx=10, expand=True)
            self.output_area.configure(state="normal")
            self.output_area.delete("1.0", "end")
            self.output_area.insert("end", "Hash will be shown here.")
            self.output_area.configure(state="disabled")
        else:
            self.encrypt_btn.pack_forget()
            self.export_btn.pack(side="right", padx=10, expand=True)
            self.copy_hash_btn.pack_forget()

    def browse_file(self):
        filetypes = [('Text files', '*.txt'), ('JSON files', '*.json'), ('All files', '*.*')]
        path = filedialog.askopenfilename(title='Select file', filetypes=filetypes)
        if path:
            self.file_path = path
            self.file_label.configure(text=os.path.basename(path))
            self.status_label.configure(text=f"Selected: {os.path.basename(path)}")

    def hash_file(self):
        if not self.file_path:
            self.status_label.configure(text="Error: No file selected!")
            messagebox.showerror('Error', 'No file selected!')
            self.error_sound.play()
            return

        algo_name = self.algo_var.get()
        algo_func = HASH_ALGOS.get(algo_name)
        if not algo_func:
            self.status_label.configure(text="Error: Invalid algorithm selected!")
            messagebox.showerror('Error', 'Invalid algorithm selected!')
            return

        try:
            with open(self.file_path, 'rb') as f:
                data = f.read()
            # If JSON, pretty-print before hashing
            if self.file_path.lower().endswith('.json'):
                try:
                    obj = json.loads(data.decode('utf-8'))
                    data = json.dumps(obj, sort_keys=True, indent=2).encode('utf-8')
                except Exception:
                    pass  # If not valid JSON, hash as-is
            hash_obj = algo_func()
            hash_obj.update(data)
            digest = hash_obj.hexdigest()
            # Output file path
            base, _ = os.path.splitext(self.file_path)
            # Show hash in output area
            self.output_area.configure(state="normal")
            self.output_area.delete("1.0", "end")
            self.output_area.insert("end", digest)
            self.output_area.configure(state="disabled")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            messagebox.showerror('Error', f'Failed to hash file:\n{e}')

    def encode_and_export(self):
        if not self.file_path:
            self.status_label.configure(text="Error: No file selected!")
            messagebox.showerror('Error', 'No file selected!')
            return
        try:
            with open(self.file_path, 'rb') as f:
                data = f.read()
            encoded = base64.b64encode(data).decode('utf-8')
            base, _ = os.path.splitext(self.file_path)
            out_path = f"{base}.b64"
            with open(out_path, 'w') as out_f:
                out_f.write(encoded)
            self.status_label.configure(text=f"Encoded & exported: {os.path.basename(out_path)}")
            messagebox.showinfo('Success', f'File encoded and exported!\nOutput: {out_path}')
            # Show encoded content in output area
            self.output_area.configure(state="normal")
            self.output_area.delete("1.0", "end")
            self.output_area.insert("end", encoded[:500] + ('... (truncated)' if len(encoded) > 500 else ''))
            self.output_area.configure(state="disabled")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            messagebox.showerror('Error', f'Failed to encode file:\n{e}')

    def copy_hash(self):
        """Copies the hash to the clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.output_area.get("1.0", "end-1c"))
            self.status_label.configure(text="Hash copied to clipboard!")
            messagebox.showinfo('Success', 'Hash copied to clipboard!')
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            messagebox.showerror('Error', f'Failed to copy hash:\n{e}')

    def run(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()


if __name__ == '__main__':
    app = FileEncryptorGUI()
    app.run()
