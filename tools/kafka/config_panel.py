"""
Configuration Panel Module

This module contains the UI panel for displaying and managing Kafka configuration.
It provides controls for viewing server.properties, validating settings, and managing configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from datetime import datetime
from typing import Optional, Dict, Any
import logging


class ConfigPanel:
    """
    UI panel for Kafka configuration management.
    
    This panel provides:
    - Display of server.properties configuration
    - Configuration validation
    - Search functionality within configuration
    - Configuration backup and export
    - Real-time configuration reload
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the configuration panel.
        
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
        self.config_text = None
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.kafka_mode_var = tk.StringVar(value="Unknown")
        self.config_file_var = tk.StringVar(value="No configuration loaded")
        
        # Control buttons
        self.reload_button = None
        self.validate_button = None
        self.backup_button = None
        self.export_button = None
        self.search_button = None
        
        # Configuration data
        self.last_search_index = "1.0"
        self.validation_results = None
        
        # Create the UI
        self._create_ui()
        
        self.logger.info("Configuration Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the configuration panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Kafka Configuration", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Info section
        self._create_info_section(main_container)
        
        # Controls section
        self._create_controls_section(main_container)
        
        # Configuration display section
        self._create_config_section(main_container)
        
        # Status section
        self._create_status_section(main_container)
    
    def _create_info_section(self, parent: ttk.Frame) -> None:
        """
        Create the configuration info section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Info frame
        info_frame = ttk.LabelFrame(parent, text="Configuration Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Info grid
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        # Kafka mode
        ttk.Label(info_grid, text="Kafka Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.kafka_mode_label = ttk.Label(info_grid, textvariable=self.kafka_mode_var, font=('Arial', 10, 'bold'))
        self.kafka_mode_label.grid(row=0, column=1, sticky=tk.W)
        
        # Configuration file
        ttk.Label(info_grid, text="Config File:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.config_file_label = ttk.Label(info_grid, textvariable=self.config_file_var, font=('Consolas', 9))
        self.config_file_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Validation status
        ttk.Label(info_grid, text="Validation:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.validation_label = ttk.Label(info_grid, text="Not validated", foreground="orange")
        self.validation_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
    
    def _create_controls_section(self, parent: ttk.Frame) -> None:
        """
        Create the controls section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Controls frame
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side controls
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Search section
        search_frame = ttk.Frame(left_controls)
        search_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 5))
        search_entry.bind('<Return>', lambda e: self._search_config())
        
        self.search_button = ttk.Button(search_frame, text="Find", command=self._search_config)
        self.search_button.pack(side=tk.LEFT)
        
        # Right side controls
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side=tk.RIGHT)
        
        # Control buttons
        self.reload_button = ttk.Button(right_controls, text="Reload Config", command=self._reload_config)
        self.reload_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.validate_button = ttk.Button(right_controls, text="Validate", command=self._validate_config)
        self.validate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.backup_button = ttk.Button(right_controls, text="Backup", command=self._backup_config)
        self.backup_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_button = ttk.Button(right_controls, text="Export", command=self._export_config)
        self.export_button.pack(side=tk.LEFT)
    
    def _create_config_section(self, parent: ttk.Frame) -> None:
        """
        Create the configuration display section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Configuration frame
        config_frame = ttk.LabelFrame(parent, text="Configuration Content", padding=5)
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configuration text area with scrollbar
        self.config_text = scrolledtext.ScrolledText(
            config_frame,
            wrap=tk.NONE,  # No word wrap for configuration files
            font=('Consolas', 10),
            state=tk.DISABLED,
            bg='#f8f8f8',
            fg='black'
        )
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for syntax highlighting
        self._configure_text_tags()
        
        # Bind mouse events
        self.config_text.bind('<Button-3>', self._show_context_menu)  # Right-click
        
        # Initial message
        self._display_initial_message()
    
    def _create_status_section(self, parent: ttk.Frame) -> None:
        """
        Create the status section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Status frame
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        # Status label
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Settings count label
        self.settings_count_label = ttk.Label(status_frame, text="Settings: 0")
        self.settings_count_label.pack(side=tk.RIGHT)
    
    def _configure_text_tags(self) -> None:
        """
        Configure text tags for syntax highlighting.
        """
        # Configure tags for different elements
        self.config_text.tag_configure("COMMENT", foreground="#008000")      # Green for comments
        self.config_text.tag_configure("KEY", foreground="#0000FF")          # Blue for keys
        self.config_text.tag_configure("VALUE", foreground="#800080")        # Purple for values
        self.config_text.tag_configure("SECTION", foreground="#FF0000", font=('Consolas', 10, 'bold'))  # Red bold for sections
        self.config_text.tag_configure("SEARCH", background="#FFFF00", foreground="#000000")  # Highlight for search
        self.config_text.tag_configure("ERROR", background="#FFE4E1", foreground="#8B0000")   # Light red background for errors
    
    def _display_initial_message(self) -> None:
        """
        Display initial message when no configuration is loaded.
        """
        initial_message = """
Kafka Configuration Panel

This panel displays the contents of the Kafka server.properties file.

To get started:
1. Select a Kafka installation folder from the Server Control panel
2. The configuration will be automatically loaded and displayed here
3. Use the controls above to reload, validate, backup, or export the configuration

Features:
• Syntax highlighting for configuration files
• Configuration validation with detailed error reporting
• Search functionality to find specific settings
• Backup and export capabilities
• Real-time configuration reload

The configuration will be displayed here once a Kafka folder is selected.
        """
        
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, initial_message.strip())
        self.config_text.config(state=tk.DISABLED)
    
    def _show_context_menu(self, event) -> None:
        """
        Show context menu on right-click.
        
        Args:
            event: Mouse event
        """
        try:
            # Create context menu
            context_menu = tk.Menu(self.parent_frame, tearoff=0)
            context_menu.add_command(label="Copy", command=self._copy_selection)
            context_menu.add_command(label="Select All", command=self._select_all)
            context_menu.add_separator()
            context_menu.add_command(label="Reload Configuration", command=self._reload_config)
            context_menu.add_command(label="Validate Configuration", command=self._validate_config)
            context_menu.add_separator()
            context_menu.add_command(label="Export Configuration", command=self._export_config)
            
            # Show menu
            context_menu.tk_popup(event.x_root, event.y_root)
            
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _copy_selection(self) -> None:
        """
        Copy selected text to clipboard.
        """
        try:
            if self.config_text.tag_ranges(tk.SEL):
                selected_text = self.config_text.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.parent_frame.clipboard_clear()
                self.parent_frame.clipboard_append(selected_text)
                self._set_status("Selected text copied to clipboard")
        except tk.TclError:
            self._set_status("No text selected")
        except Exception as e:
            self.logger.error(f"Error copying selection: {e}")
    
    def _select_all(self) -> None:
        """
        Select all text in the configuration display.
        """
        try:
            self.config_text.tag_add(tk.SEL, "1.0", tk.END)
            self.config_text.mark_set(tk.INSERT, "1.0")
            self.config_text.see(tk.INSERT)
            self._set_status("All text selected")
        except Exception as e:
            self.logger.error(f"Error selecting all text: {e}")
    
    def _search_config(self) -> None:
        """
        Search for text in the configuration.
        """
        try:
            search_term = self.search_var.get().strip()
            if not search_term:
                messagebox.showwarning("Search", "Please enter a search term")
                return
            
            # Clear previous search highlights
            self.config_text.tag_remove("SEARCH", "1.0", tk.END)
            
            # Search from current position
            start_pos = self.last_search_index
            pos = self.config_text.search(search_term, start_pos, tk.END, nocase=True)
            
            if pos:
                # Highlight found text
                end_pos = f"{pos}+{len(search_term)}c"
                self.config_text.tag_add("SEARCH", pos, end_pos)
                self.config_text.see(pos)
                self.config_text.mark_set(tk.INSERT, pos)
                
                # Update search position for next search
                self.last_search_index = end_pos
                
                self._set_status(f"Found '{search_term}' at {pos}")
            else:
                # Search from beginning if not found
                pos = self.config_text.search(search_term, "1.0", self.last_search_index, nocase=True)
                if pos:
                    end_pos = f"{pos}+{len(search_term)}c"
                    self.config_text.tag_add("SEARCH", pos, end_pos)
                    self.config_text.see(pos)
                    self.config_text.mark_set(tk.INSERT, pos)
                    self.last_search_index = end_pos
                    self._set_status(f"Found '{search_term}' at {pos} (wrapped)")
                else:
                    self._set_status(f"'{search_term}' not found")
                    self.last_search_index = "1.0"
            
        except Exception as e:
            self.logger.error(f"Error searching configuration: {e}")
            self._set_status("Error during search")
    
    def _reload_config(self) -> None:
        """
        Reload the configuration from file.
        """
        if not self.config_parser:
            self._set_status("Configuration parser not available")
            return
        
        self._set_status("Reloading configuration...")
        
        # Reload in background thread
        thread = threading.Thread(target=self._reload_config_worker, daemon=True)
        thread.start()
    
    def _reload_config_worker(self) -> None:
        """
        Worker thread for reloading configuration.
        """
        try:
            success, message = self.config_parser.reload_config()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_reload_result, success, message)
            
        except Exception as e:
            error_msg = f"Error reloading configuration: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_reload_result, False, error_msg)
    
    def _handle_reload_result(self, success: bool, message: str) -> None:
        """
        Handle the result of configuration reload.
        
        Args:
            success (bool): Whether reload was successful
            message (str): Result message
        """
        if success:
            self._display_configuration()
            self._set_status("Configuration reloaded successfully")
        else:
            self._set_status(f"Failed to reload configuration: {message}")
            messagebox.showerror("Reload Error", message)
    
    def _validate_config(self) -> None:
        """
        Validate the current configuration.
        """
        if not self.config_parser:
            self._set_status("Configuration parser not available")
            return
        
        self._set_status("Validating configuration...")
        
        # Validate in background thread
        thread = threading.Thread(target=self._validate_config_worker, daemon=True)
        thread.start()
    
    def _validate_config_worker(self) -> None:
        """
        Worker thread for validating configuration.
        """
        try:
            is_valid, issues = self.config_parser.validate_config()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_validation_result, is_valid, issues)
            
        except Exception as e:
            error_msg = f"Error validating configuration: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_validation_result, False, [error_msg])
    
    def _handle_validation_result(self, is_valid: bool, issues: list) -> None:
        """
        Handle the result of configuration validation.
        
        Args:
            is_valid (bool): Whether configuration is valid
            issues (list): List of validation issues
        """
        self.validation_results = (is_valid, issues)
        
        if is_valid:
            self.validation_label.config(text="✓ Valid", foreground="green")
            self._set_status("Configuration validation passed")
            messagebox.showinfo("Validation Result", "Configuration is valid!")
        else:
            self.validation_label.config(text="✗ Invalid", foreground="red")
            self._set_status(f"Configuration validation failed: {len(issues)} issues found")
            
            # Show validation issues
            issues_text = "Configuration validation failed with the following issues:\n\n"
            for i, issue in enumerate(issues, 1):
                issues_text += f"{i}. {issue}\n"
            
            messagebox.showerror("Validation Failed", issues_text)
    
    def _backup_config(self) -> None:
        """
        Create a backup of the configuration file.
        """
        if not self.config_parser:
            self._set_status("Configuration parser not available")
            return
        
        try:
            success, backup_path = self.config_parser.backup_config()
            
            if success:
                self._set_status(f"Configuration backed up to: {backup_path}")
                messagebox.showinfo("Backup Created", f"Configuration backed up successfully to:\n{backup_path}")
            else:
                self._set_status(f"Backup failed: {backup_path}")
                messagebox.showerror("Backup Failed", backup_path)
                
        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            self.logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Backup Error", error_msg)
    
    def _export_config(self) -> None:
        """
        Export configuration to a file.
        """
        if not self.config_parser:
            self._set_status("Configuration parser not available")
            return
        
        try:
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".properties",
                filetypes=[
                    ("Properties files", "*.properties"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # Get formatted configuration
                formatted_config = self.config_parser.get_formatted_config()
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Kafka Configuration Export\n")
                    f.write(f"# Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Original file: {self.config_parser.config_file}\n")
                    f.write("#" + "=" * 50 + "\n\n")
                    f.write(formatted_config)
                
                self._set_status(f"Configuration exported to: {file_path}")
                messagebox.showinfo("Export Complete", f"Configuration exported successfully to:\n{file_path}")
            
        except Exception as e:
            error_msg = f"Error exporting configuration: {str(e)}"
            self.logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Export Error", error_msg)
    
    def _display_configuration(self) -> None:
        """
        Display the current configuration in the text area.
        """
        try:
            if not self.config_parser:
                return
            
            # Get formatted configuration
            formatted_config = self.config_parser.get_formatted_config()
            
            # Update display
            self.config_text.config(state=tk.NORMAL)
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, formatted_config)
            
            # Apply syntax highlighting
            self._apply_syntax_highlighting()
            
            self.config_text.config(state=tk.DISABLED)
            
            # Update info labels
            self.kafka_mode_var.set(self.config_parser.get_kafka_mode())
            self.config_file_var.set(str(self.config_parser.config_file))
            
            # Update settings count
            all_config = self.config_parser.get_all_config()
            self.settings_count_label.config(text=f"Settings: {len(all_config)}")
            
            # Reset validation status
            self.validation_label.config(text="Not validated", foreground="orange")
            self.validation_results = None
            
        except Exception as e:
            self.logger.error(f"Error displaying configuration: {e}")
            self._set_status("Error displaying configuration")
    
    def _apply_syntax_highlighting(self) -> None:
        """
        Apply syntax highlighting to the configuration text.
        """
        try:
            content = self.config_text.get(1.0, tk.END)
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line_start = f"{line_num}.0"
                line_end = f"{line_num}.end"
                
                # Highlight comments
                if line.strip().startswith('#'):
                    self.config_text.tag_add("COMMENT", line_start, line_end)
                
                # Highlight key=value pairs
                elif '=' in line and not line.strip().startswith('#'):
                    key_part, value_part = line.split('=', 1)
                    
                    # Highlight key
                    key_end = f"{line_start}+{len(key_part)}c"
                    self.config_text.tag_add("KEY", line_start, key_end)
                    
                    # Highlight value
                    value_start = f"{line_start}+{len(key_part) + 1}c"
                    self.config_text.tag_add("VALUE", value_start, line_end)
                
                # Highlight section headers (if any)
                elif line.strip().startswith('[') and line.strip().endswith(']'):
                    self.config_text.tag_add("SECTION", line_start, line_end)
            
        except Exception as e:
            self.logger.error(f"Error applying syntax highlighting: {e}")
    
    def _set_status(self, message: str) -> None:
        """
        Set the status message.
        
        Args:
            message (str): Status message
        """
        self.status_var.set(message)
    
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
        
        # Display configuration if available
        if config_parser:
            self._display_configuration()
        else:
            self._display_initial_message()
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        if self.config_parser:
            self._reload_config()
        else:
            self._set_status("No configuration parser available")
    
    def get_validation_results(self) -> Optional[tuple]:
        """
        Get the last validation results.
        
        Returns:
            Optional[tuple]: (is_valid, issues) or None if not validated
        """
        return self.validation_results