"""
Main Window Module

This module contains the main GUI window for the Kafka Tool application.
It coordinates all the UI panels and manages the overall application interface.
"""

import logging
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from config_panel import ConfigPanel
from config_parser import KafkaConfigParser
from console_panel import ConsolePanel
from groups_panel import GroupsPanel
# Import backend modules
from kafka_manager import KafkaManager
from logger import setup_logging
from producer_consumer import ProducerConsumerManager
# Import UI panels
from server_panel import ServerPanel
from simulator_panel import SimulatorPanel
from topics_panel import TopicsPanel


class KafkaToolMainWindow:
    """
    Main window for the Kafka Tool application.
    
    This class manages the overall GUI layout and coordinates between different panels.
    It handles the main application logic and provides a unified interface for all Kafka operations.
    """
    
    def __init__(self):
        """
        Initialize the main window.
        """
        # Initialize logging first
        self.app_logger = setup_logging("logs", "INFO")
        self.logger = logging.getLogger(__name__)
        
        # Application state
        self.kafka_manager = None
        self.producer_consumer_manager = None
        self.config_parser = None
        self.kafka_folder = None
        self.bootstrap_servers = "localhost:9092"
        
        # GUI components
        self.root = None
        self.notebook = None
        self.status_bar = None
        self.menu_bar = None
        
        # UI Panels
        self.server_panel = None
        self.topics_panel = None
        self.groups_panel = None
        self.simulator_panel = None
        self.console_panel = None
        self.config_panel = None
        
        # Threading
        self.update_thread = None
        self.is_running = True
        
        # Initialize GUI
        self._create_gui()
        self._setup_menu()
        self._setup_status_bar()
        self._start_update_thread()
        
        self.logger.info("Kafka Tool Main Window initialized")
    
    def _create_gui(self) -> None:
        """
        Create the main GUI layout.
        """
        # Create main window
        self.root = tk.Tk()
        self.root.title("Kafka Tool - Professional Kafka Management")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Set window icon (if available)
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "kafka_tool.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Ignore if icon not found
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme
        
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create panels
        self._create_panels()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _create_panels(self) -> None:
        """
        Create all UI panels and add them to the notebook.
        """
        # Server Panel
        server_frame = ttk.Frame(self.notebook)
        self.server_panel = ServerPanel(server_frame, self)
        self.notebook.add(server_frame, text="Server Control")
        
        # Topics Panel
        topics_frame = ttk.Frame(self.notebook)
        self.topics_panel = TopicsPanel(topics_frame, self)
        self.notebook.add(topics_frame, text="Topics Management")
        
        # Consumer Groups Panel
        groups_frame = ttk.Frame(self.notebook)
        self.groups_panel = GroupsPanel(groups_frame, self)
        self.notebook.add(groups_frame, text="Consumer Groups")
        
        # Producer/Consumer Simulator Panel
        simulator_frame = ttk.Frame(self.notebook)
        self.simulator_panel = SimulatorPanel(simulator_frame, self)
        self.notebook.add(simulator_frame, text="Producer/Consumer")
        
        # Console Panel
        console_frame = ttk.Frame(self.notebook)
        self.console_panel = ConsolePanel(console_frame, self)
        self.notebook.add(console_frame, text="Console Logs")
        
        # Configuration Panel
        config_frame = ttk.Frame(self.notebook)
        self.config_panel = ConfigPanel(config_frame, self)
        self.notebook.add(config_frame, text="Configuration")
    
    def _setup_menu(self) -> None:
        """
        Set up the application menu bar.
        """
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Kafka Folder...", command=self._select_kafka_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Export Logs...", command=self._export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Clusters Menu
        clusters_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Clusters", menu=clusters_menu)
        clusters_menu.add_command(label="Add Cluster...", command=self._add_cluster)
        clusters_menu.add_command(label="Manage Clusters...", command=self._manage_clusters)
        
        # Tools Menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Refresh All", command=self.refresh_all)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Console", command=self._clear_console)
        tools_menu.add_command(label="Settings...", command=self._show_settings)
        
        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
    
    def _setup_status_bar(self) -> None:
        """
        Set up the status bar at the bottom of the window.
        """
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Connection status
        self.connection_label = ttk.Label(self.status_bar, text="Not Connected")
        self.connection_label.pack(side=tk.RIGHT, padx=5)
        
        # Separator
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # Server status
        self.server_status_label = ttk.Label(self.status_bar, text="Server: Unknown")
        self.server_status_label.pack(side=tk.RIGHT, padx=5)
    
    def _start_update_thread(self) -> None:
        """
        Start the background update thread for real-time updates.
        """
        self.update_thread = threading.Thread(target=self._update_worker, daemon=True)
        self.update_thread.start()
    
    def _update_worker(self) -> None:
        """
        Background worker for updating GUI components.
        """
        import time
        
        while self.is_running:
            try:
                # Update status bar
                self.root.after(0, self._update_status_bar)
                
                # Update console panel
                if self.console_panel:
                    self.root.after(0, self.console_panel.update_console)
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in update worker: {e}")
                time.sleep(5)  # Longer sleep on error
    
    def _update_status_bar(self) -> None:
        """
        Update the status bar with current information.
        """
        try:
            if self.kafka_manager:
                # Update server status
                server_status = self.kafka_manager.get_server_status()
                self.server_status_label.config(text=f"Server: {server_status}")
                
                # Update connection status
                if self.kafka_manager.is_server_running():
                    self.connection_label.config(text="Connected")
                else:
                    self.connection_label.config(text="Not Connected")
            else:
                self.server_status_label.config(text="Server: Unknown")
                self.connection_label.config(text="Not Connected")
                
        except Exception as e:
            self.logger.error(f"Error updating status bar: {e}")
    
    def _select_kafka_folder(self) -> None:
        """
        Open dialog to select Kafka installation folder.
        """
        folder = filedialog.askdirectory(
            title="Select Kafka Installation Folder",
            initialdir=os.path.expanduser("~")
        )
        
        if folder:
            self.set_kafka_folder(folder)
    
    def set_kafka_folder(self, folder_path: str) -> bool:
        """
        Set the Kafka installation folder and initialize managers.
        
        Args:
            folder_path (str): Path to Kafka installation folder
        
        Returns:
            bool: True if successful
        """
        try:
            self.kafka_folder = folder_path
            
            # Initialize Kafka manager
            self.kafka_manager = KafkaManager(folder_path, self.bootstrap_servers)
            
            # Initialize producer/consumer manager
            self.producer_consumer_manager = ProducerConsumerManager(self.bootstrap_servers)
            
            # Initialize config parser
            self.config_parser = KafkaConfigParser(folder_path)
            
            # Update all panels
            self._update_all_panels()
            
            # Update status
            self.set_status(f"Kafka folder set: {folder_path}")
            
            self.logger.info(f"Kafka folder set to: {folder_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error setting Kafka folder: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return False
    
    def _update_all_panels(self) -> None:
        """
        Update all panels with new Kafka manager instances.
        """
        panels = [
            self.server_panel,
            self.topics_panel,
            self.groups_panel,
            self.simulator_panel,
            self.config_panel
        ]
        
        for panel in panels:
            if panel and hasattr(panel, 'update_managers'):
                panel.update_managers(
                    self.kafka_manager,
                    self.producer_consumer_manager,
                    self.config_parser
                )
    
    def refresh_all(self) -> None:
        """
        Refresh all data in all panels.
        """
        try:
            self.set_status("Refreshing all data...")
            
            # Refresh each panel
            panels = [
                self.server_panel,
                self.topics_panel,
                self.groups_panel,
                self.simulator_panel,
                self.config_panel
            ]
            
            for panel in panels:
                if panel and hasattr(panel, 'refresh'):
                    panel.refresh()
            
            self.set_status("All data refreshed")
            self.logger.info("All panels refreshed")
            
        except Exception as e:
            error_msg = f"Error refreshing data: {str(e)}"
            self.logger.error(error_msg)
            self.set_status(error_msg)
    
    def set_status(self, message: str) -> None:
        """
        Set the status bar message.
        
        Args:
            message (str): Status message
        """
        if self.status_label:
            self.status_label.config(text=message)
    
    def get_kafka_manager(self) -> Optional[KafkaManager]:
        """
        Get the current Kafka manager instance.
        
        Returns:
            Optional[KafkaManager]: Kafka manager or None
        """
        return self.kafka_manager
    
    def get_producer_consumer_manager(self) -> Optional[ProducerConsumerManager]:
        """
        Get the current producer/consumer manager instance.
        
        Returns:
            Optional[ProducerConsumerManager]: Manager or None
        """
        return self.producer_consumer_manager
    
    def get_config_parser(self) -> Optional[KafkaConfigParser]:
        """
        Get the current config parser instance.
        
        Returns:
            Optional[KafkaConfigParser]: Config parser or None
        """
        return self.config_parser
    
    def _export_logs(self) -> None:
        """
        Export application logs to a file.
        """
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Logs",
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
            
            if file_path:
                success, message = self.app_logger.export_logs(file_path)
                if success:
                    messagebox.showinfo("Success", message)
                else:
                    messagebox.showerror("Error", message)
                    
        except Exception as e:
            error_msg = f"Error exporting logs: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _clear_console(self) -> None:
        """
        Clear the console panel.
        """
        if self.console_panel:
            self.console_panel.clear_console()
    
    def _add_cluster(self) -> None:
        """
        Show dialog to add a new cluster configuration.
        """
        # TODO: Implement cluster management dialog
        messagebox.showinfo("Info", "Cluster management feature coming soon!")
    
    def _manage_clusters(self) -> None:
        """
        Show dialog to manage existing cluster configurations.
        """
        # TODO: Implement cluster management dialog
        messagebox.showinfo("Info", "Cluster management feature coming soon!")
    
    def _show_settings(self) -> None:
        """
        Show application settings dialog.
        """
        # TODO: Implement settings dialog
        messagebox.showinfo("Info", "Settings dialog coming soon!")
    
    def _show_about(self) -> None:
        """
        Show about dialog.
        """
        about_text = """
Kafka Tool v1.0.0

Professional Kafka Management Tool for Windows

Features:
• Start/Stop Kafka Server
• Topics Management
• Consumer Groups Management
• Producer/Consumer Simulator
• Real-time Console Logs
• Configuration Display

Developed with Python and Tkinter
        """
        messagebox.showinfo("About Kafka Tool", about_text.strip())
    
    def _show_documentation(self) -> None:
        """
        Show documentation or open help.
        """
        # TODO: Implement documentation viewer or open web browser
        messagebox.showinfo("Info", "Documentation feature coming soon!")
    
    def _on_tab_changed(self, event) -> None:
        """
        Handle tab change events.
        
        Args:
            event: Tab change event
        """
        try:
            selected_tab = self.notebook.select()
            tab_text = self.notebook.tab(selected_tab, "text")
            self.logger.debug(f"Switched to tab: {tab_text}")
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")
    
    def _on_closing(self) -> None:
        """
        Handle application closing.
        """
        try:
            self.logger.info("Application closing...")
            
            # Stop update thread
            self.is_running = False
            
            # Stop producer/consumer operations
            if self.producer_consumer_manager:
                self.producer_consumer_manager.stop_all()
            
            # Close Kafka manager connections
            if self.kafka_manager:
                # Any cleanup needed for kafka manager
                pass
            
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            self.root.destroy()
    
    def run(self) -> None:
        """
        Start the main application loop.
        """
        try:
            self.logger.info("Starting Kafka Tool application")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in main application loop: {e}")
            raise


def main():
    """
    Main entry point for the application.
    """
    try:
        app = KafkaToolMainWindow()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()