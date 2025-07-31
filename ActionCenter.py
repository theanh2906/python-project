import subprocess
import threading
import tkinter as tk

import customtkinter as ctk

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class ShellCommandActionTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Shell Command Action Tool")
        self.geometry("600x400")
        self.minsize(600, 400)

        # Sample commands dictionary
        self.commands = [
            {
                "name": "Forget Wifi",
                "command": "netsh wlan delete profile name=*"
            },
            {
                "name": "Connect SDP",
                "command": "start https://launcher.myapps.microsoft.com/api/signin/87fb2afc-e944-4189-a264-0afcc82593a3?tenantId=58122277-edf8-4048-96c4-ec80d30669b8"
            },
            {
                "name": "App Uninstallation",
                "command": 'Start-Process appwiz.cpl'
            },
            {
                "name": "Open Environment Variables",
                "command": "Start-Process 'C:\\Windows\\System32\\SystemPropertiesAdvanced.exe'"
            },
            {
                "name": "Open Services",
                "command": 'Start-Process services.msc'
            },
            {
                "name": "Copy Kiosk License",
                "command": 'Set-Clipboard 8yL8-CGy9-1Liq-tktH-7z9K-pDw1-ZmoV-9jfF'
            },
            {
                "name": "Open WebMC",
                "command": 'start http://localhost:8009/'
            },
            {
                "name": "Open MDCore",
                "command": 'start http://localhost:8009/'
            },
            {
                "name": "Reset OOBE",
                "command": 'D:\SKO_reset\\SKO_reset.bat'
            }
        ]

        # Create UI elements
        self.create_ui()

    def create_ui(self):
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create top frame for buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create status label
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", anchor="center")
        self.status_label.pack(fill=tk.X, padx=10, pady=10)

        # Create buttons for each command
        self.create_command_buttons()

    def create_command_buttons(self):
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Create a button for each command
        for i, cmd in enumerate(self.commands):
            button = ctk.CTkButton(
                self.button_frame,
                text=cmd["name"],
                command=lambda c=cmd: self.execute_command(c),
                width=120,
                height=35
            )
            button.grid(row=i // 4, column=i % 4, padx=4, pady=4, sticky="ew")

        # Configure grid columns to be equally sized
        for i in range(5):
            self.button_frame.grid_columnconfigure(i, weight=1)

    def execute_command(self, command_dict):
        # Update status label
        self.status_label.configure(text=f"Executing: {command_dict['name']}...")
        self.status_label.configure(text_color="white")

        # Disable all buttons
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state=tk.DISABLED)

        # Execute command in a separate thread
        thread = threading.Thread(
            target=self.run_command,
            args=(command_dict,)
        )
        thread.daemon = True
        thread.start()

    def run_command(self, command_dict):
        command = command_dict["command"]
        try:
            # Execute the command using PowerShell
            process = subprocess.Popen(
                ["powershell", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Wait for the command to complete
            stdout, stderr = process.communicate()

            # Check the return code
            if process.returncode == 0:
                self.update_status(f"Successfully executed: {command_dict['name']}", "green")
            else:
                self.update_status(f"Failed to execute: {command_dict['name']}\nError: {stderr.strip()}", "red")

        except Exception as e:
            self.update_status(f"An error occurred: {e}", "red")

        finally:
            # Re-enable all buttons
            self.after(0, self.enable_buttons)

    def update_status(self, message, color):
        self.status_label.configure(text=message, text_color=color)

    def enable_buttons(self):
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state=tk.NORMAL)


if __name__ == "__main__":
    app = ShellCommandActionTool()
    app.mainloop()
