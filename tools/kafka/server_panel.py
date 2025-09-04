"""
Server Panel Module

This module contains the UI panel for Kafka server start/stop operations.
It provides controls for selecting Kafka folder, starting/stopping server, and displaying server status.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from pathlib import Path
from typing import Optional
import logging


class ServerPanel:
    """
    UI panel for Kafka server operations.
    
    This panel provides:
    - Kafka folder selection
    - Server start/stop controls
    - Server status display
    - Configuration validation
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the server panel.
        
        Args:
            parent_frame (ttk.Frame): Parent frame to contain this panel
            main_window: Reference to the main window
        """
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.kafka_manager = None
        self.config_parser = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # GUI components
        self.kafka_folder_var = tk.StringVar()
        self.server_status_var = tk.StringVar(value="Unknown")
        self.kafka_mode_var = tk.StringVar(value="Unknown")
        
        # Control states
        self.start_button = None
        self.stop_button = None
        self.browse_button = None
        self.refresh_button = None
        
        # Create the UI
        self._create_ui()
        
        # Initial state
        self._update_button_states()
        
        self.logger.info("Server Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the server panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Kafka Server Control", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Kafka Folder Section
        self._create_folder_section(main_container)
        
        # Server Status Section
        self._create_status_section(main_container)
        
        # Server Control Section
        self._create_control_section(main_container)
        
        # Information Section
        self._create_info_section(main_container)
    
    def _create_folder_section(self, parent: ttk.Frame) -> None:
        """
        Create the Kafka folder selection section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Folder selection frame
        folder_frame = ttk.LabelFrame(parent, text="Kafka Installation", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Folder path display
        path_frame = ttk.Frame(folder_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="Kafka Folder:").pack(side=tk.LEFT)
        
        folder_entry = ttk.Entry(path_frame, textvariable=self.kafka_folder_var, state='readonly', width=60)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.browse_button = ttk.Button(path_frame, text="Browse...", command=self._browse_kafka_folder)
        self.browse_button.pack(side=tk.RIGHT)
        
        # Validation status
        self.validation_label = ttk.Label(folder_frame, text="No Kafka folder selected", foreground="orange")
        self.validation_label.pack(anchor=tk.W)
    
    def _create_status_section(self, parent: ttk.Frame) -> None:
        """
        Create the server status section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        # Server status
        ttk.Label(status_grid, text="Server Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.server_status_label = ttk.Label(status_grid, textvariable=self.server_status_var, font=('Arial', 10, 'bold'))
        self.server_status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Kafka mode
        ttk.Label(status_grid, text="Kafka Mode:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.kafka_mode_label = ttk.Label(status_grid, textvariable=self.kafka_mode_var)
        self.kafka_mode_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Bootstrap servers
        ttk.Label(status_grid, text="Bootstrap Servers:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.bootstrap_label = ttk.Label(status_grid, text="localhost:9092")
        self.bootstrap_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
    
    def _create_control_section(self, parent: ttk.Frame) -> None:
        """
        Create the server control section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Control frame
        control_frame = ttk.LabelFrame(parent, text="Server Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        # Start button
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Server", 
            command=self._start_server,
            style="Success.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop Server", 
            command=self._stop_server,
            style="Danger.TButton"
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(
            button_frame, 
            text="Refresh Status", 
            command=self._refresh_status
        )
        self.refresh_button.pack(side=tk.LEFT)
        
        # Progress bar (hidden by default)
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar.pack_forget()  # Hide initially
    
    def _create_info_section(self, parent: ttk.Frame) -> None:
        """
        Create the information section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Info frame
        info_frame = ttk.LabelFrame(parent, text="Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info text
        self.info_text = tk.Text(
            info_frame, 
            height=8, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            font=('Consolas', 9)
        )
        
        # Scrollbar for info text
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        # Pack info components
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial info text
        self._update_info_text("Select a Kafka installation folder to begin.")
    
    def _browse_kafka_folder(self) -> None:
        """
        Open dialog to browse for Kafka installation folder.
        """
        try:
            initial_dir = self.kafka_folder_var.get() or os.path.expanduser("~")
            
            folder = filedialog.askdirectory(
                title="Select Kafka Installation Folder",
                initialdir=initial_dir
            )
            
            if folder:
                self._set_kafka_folder(folder)
                
        except Exception as e:
            error_msg = f"Error browsing for Kafka folder: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _set_kafka_folder(self, folder_path: str) -> None:
        """
        Set the Kafka folder and validate it.
        
        Args:
            folder_path (str): Path to Kafka installation folder
        """
        try:
            self.kafka_folder_var.set(folder_path)
            
            # Notify main window
            if self.main_window:
                success = self.main_window.set_kafka_folder(folder_path)
                if success:
                    self._validate_kafka_folder()
                    self._update_button_states()
                    self._refresh_status()
                else:
                    self.kafka_folder_var.set("")
                    self._update_info_text("Invalid Kafka folder selected.")
            
        except Exception as e:
            error_msg = f"Error setting Kafka folder: {str(e)}"
            self.logger.error(error_msg)
            self.validation_label.config(text=error_msg, foreground="red")
    
    def _validate_kafka_folder(self) -> bool:
        """
        Validate the selected Kafka folder.
        
        Returns:
            bool: True if valid
        """
        try:
            folder_path = self.kafka_folder_var.get()
            if not folder_path:
                self.validation_label.config(text="No Kafka folder selected", foreground="orange")
                return False
            
            kafka_path = Path(folder_path)
            
            # Check required files
            required_files = [
                "bin/windows/kafka-server-start.bat",
                "bin/windows/kafka-server-stop.bat",
                "config/server.properties"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not (kafka_path / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                error_msg = f"Missing required files: {', '.join(missing_files)}"
                self.validation_label.config(text=error_msg, foreground="red")
                return False
            
            # Valid folder
            self.validation_label.config(text="✓ Valid Kafka installation", foreground="green")
            
            # Update info
            info_text = f"Kafka installation validated successfully.\nFolder: {folder_path}"
            self._update_info_text(info_text)
            
            return True
            
        except Exception as e:
            error_msg = f"Error validating Kafka folder: {str(e)}"
            self.logger.error(error_msg)
            self.validation_label.config(text=error_msg, foreground="red")
            return False
    
    def _start_server(self) -> None:
        """
        Start the Kafka server in a separate thread.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized. Please select a valid Kafka folder.")
            return
        
        # Disable buttons and show progress
        self._set_operation_in_progress(True)
        
        # Start server in background thread
        thread = threading.Thread(target=self._start_server_worker, daemon=True)
        thread.start()
    
    def _start_server_worker(self) -> None:
        """
        Worker thread for starting the server.
        """
        try:
            self.logger.info("Starting Kafka server...")
            success, message = self.kafka_manager.start_server()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_start_result, success, message)
            
        except Exception as e:
            error_msg = f"Error starting server: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_start_result, False, error_msg)
    
    def _handle_start_result(self, success: bool, message: str) -> None:
        """
        Handle the result of server start operation.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Result message
        """
        self._set_operation_in_progress(False)
        
        if success:
            messagebox.showinfo("Success", message)
            self._update_info_text(f"✓ {message}")
        else:
            messagebox.showerror("Error", message)
            self._update_info_text(f"✗ {message}")
        
        self._refresh_status()
    
    def _stop_server(self) -> None:
        """
        Stop the Kafka server in a separate thread.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized.")
            return
        
        # Confirm stop operation
        result = messagebox.askyesno(
            "Confirm Stop", 
            "Are you sure you want to stop the Kafka server?\n\nThis will disconnect all clients and stop message processing."
        )
        
        if not result:
            return
        
        # Disable buttons and show progress
        self._set_operation_in_progress(True)
        
        # Stop server in background thread
        thread = threading.Thread(target=self._stop_server_worker, daemon=True)
        thread.start()
    
    def _stop_server_worker(self) -> None:
        """
        Worker thread for stopping the server.
        """
        try:
            self.logger.info("Stopping Kafka server...")
            success, message = self.kafka_manager.stop_server()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_stop_result, success, message)
            
        except Exception as e:
            error_msg = f"Error stopping server: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_stop_result, False, error_msg)
    
    def _handle_stop_result(self, success: bool, message: str) -> None:
        """
        Handle the result of server stop operation.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Result message
        """
        self._set_operation_in_progress(False)
        
        if success:
            messagebox.showinfo("Success", message)
            self._update_info_text(f"✓ {message}")
        else:
            messagebox.showerror("Error", message)
            self._update_info_text(f"✗ {message}")
        
        self._refresh_status()
    
    def _refresh_status(self) -> None:
        """
        Refresh the server status display.
        """
        try:
            if self.kafka_manager:
                # Update server status
                status = self.kafka_manager.get_server_status()
                self.server_status_var.set(status)
                
                # Update status label color
                if status == "Running":
                    self.server_status_label.config(foreground="green")
                elif status == "Stopped":
                    self.server_status_label.config(foreground="red")
                else:
                    self.server_status_label.config(foreground="orange")
                
                # Update cluster info
                cluster_info = self.kafka_manager.get_cluster_info()
                
                # Update Kafka mode
                if self.config_parser:
                    mode = self.config_parser.get_kafka_mode()
                    self.kafka_mode_var.set(mode)
                
                # Update bootstrap servers
                bootstrap_servers = cluster_info.get('bootstrap_servers', 'localhost:9092')
                self.bootstrap_label.config(text=bootstrap_servers)
                
                # Update info text
                info_lines = [
                    f"Server Status: {status}",
                    f"Kafka Mode: {self.kafka_mode_var.get()}",
                    f"Bootstrap Servers: {bootstrap_servers}",
                    f"Topics: {cluster_info.get('topic_count', 0)}",
                    f"Consumer Groups: {cluster_info.get('consumer_group_count', 0)}"
                ]
                
                self._update_info_text("\n".join(info_lines))
                
            else:
                self.server_status_var.set("Unknown")
                self.server_status_label.config(foreground="gray")
                self.kafka_mode_var.set("Unknown")
                self.bootstrap_label.config(text="localhost:9092")
            
            # Update button states
            self._update_button_states()
            
        except Exception as e:
            error_msg = f"Error refreshing status: {str(e)}"
            self.logger.error(error_msg)
            self._update_info_text(f"Error: {error_msg}")
    
    def _update_button_states(self) -> None:
        """
        Update the state of control buttons based on current status.
        """
        try:
            if not self.kafka_manager:
                # No Kafka manager - disable all server control buttons
                if self.start_button:
                    self.start_button.config(state=tk.DISABLED)
                if self.stop_button:
                    self.stop_button.config(state=tk.DISABLED)
                return
            
            # Check server status
            is_running = self.kafka_manager.is_server_running()
            
            if self.start_button:
                self.start_button.config(state=tk.DISABLED if is_running else tk.NORMAL)
            
            if self.stop_button:
                self.stop_button.config(state=tk.NORMAL if is_running else tk.DISABLED)
                
        except Exception as e:
            self.logger.error(f"Error updating button states: {e}")
    
    def _set_operation_in_progress(self, in_progress: bool) -> None:
        """
        Set UI state for operation in progress.
        
        Args:
            in_progress (bool): Whether an operation is in progress
        """
        state = tk.DISABLED if in_progress else tk.NORMAL
        
        if self.start_button:
            self.start_button.config(state=state)
        if self.stop_button:
            self.stop_button.config(state=state)
        if self.browse_button:
            self.browse_button.config(state=state)
        
        if in_progress:
            self.progress_bar.pack(fill=tk.X, pady=(10, 0))
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def _update_info_text(self, text: str) -> None:
        """
        Update the information text area.
        
        Args:
            text (str): Text to display
        """
        try:
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, text)
            self.info_text.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Error updating info text: {e}")
    
    def update_managers(self, kafka_manager, producer_consumer_manager, config_parser) -> None:
        """
        Update the manager instances.
        
        Args:
            kafka_manager: Kafka manager instance
            producer_consumer_manager: Producer/consumer manager instance
            config_parser: Config parser instance
        """
        self.kafka_manager = kafka_manager
        self.config_parser = config_parser
        
        # Update folder display
        if kafka_manager:
            self.kafka_folder_var.set(str(kafka_manager.kafka_folder))
            self._validate_kafka_folder()
        
        # Refresh status
        self._refresh_status()
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        self._refresh_status()