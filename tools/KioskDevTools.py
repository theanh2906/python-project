import tkinter as tk

import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

class KioskDevTools(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kiosk Dev Tools")
        self.geometry("800x600")
        self.create_ui()
    def create_ui(self):
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create info frame
        self.info_frame = ctk.CTkFrame(self.main_frame)
        self.info_frame.pack(pady=10, padx=10, fill=tk.BOTH)

        # Create info label
        self.info_label = ctk.CTkLabel(self.info_frame, text="Kiosk Dev Tools", font=("Arial", 24))
        self.info_label.pack(pady=10)

        # Create table frame to show information
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        data = [
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
            }
        ]
        self.create_table(data)

    def create_table(self, data: list):
        # Clear previous table if exists
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Create table headers
        headers = list(data[0].keys()) if data else []
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(self.table_frame, text=header, font=("Consolas", 14, "bold"))
            label.grid(row=0, column=i, padx=10, pady=5)

        # Populate table with data
        for i, item in enumerate(data):
            name_label = ctk.CTkLabel(self.table_frame, text=item["name"], font=("Arial", 12))
            name_label.grid(row=i + 1, column=0, padx=10, pady=5)

            command_label = ctk.CTkLabel(self.table_frame, text=item["command"], font=("Arial", 12))
            command_label.grid(row=i + 1, column=1, padx=10, pady=5)


if __name__ == "__main__":
    app = KioskDevTools()
    app.mainloop()