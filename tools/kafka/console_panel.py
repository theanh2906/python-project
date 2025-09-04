"""
Console Panel Module

This module contains the UI panel for displaying real-time console logs.
It provides a scrollable text area for viewing application logs with filtering and export capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from datetime import datetime
from typing import Optional, List
import logging


class ConsolePanel:
    """
    UI panel for displaying real-time console logs.
    
    This panel provides:
    - Real-time log display with auto-scrolling
    - Log level filtering
    - Search functionality
    - Clear and export capabilities
    - Automatic log refresh
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the console panel.
        
        Args:
            parent_frame (ttk.Frame): Parent frame to contain this panel
            main_window: Reference to the main window
        """
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.app_logger = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # GUI components
        self.console_text = None
        self.search_var = tk.StringVar()
        self.log_level_var = tk.StringVar(value="ALL")
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready")
        
        # Control buttons
        self.clear_button = None
        self.export_button = None
        self.refresh_button = None
        self.search_button = None
        
        # Log management
        self.max_lines = 1000  # Maximum lines to keep in console
        self.current_line_count = 0
        self.last_search_index = "1.0"
        
        # Create the UI
        self._create_ui()
        
        # Start auto-refresh
        self._start_auto_refresh()
        
        self.logger.info("Console Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the console panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Console Logs", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Controls section
        self._create_controls_section(main_container)
        
        # Console display section
        self._create_console_section(main_container)
        
        # Status section
        self._create_status_section(main_container)
    
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
        search_entry.bind('<Return>', lambda e: self._search_logs())
        
        self.search_button = ttk.Button(search_frame, text="Find", command=self._search_logs)
        self.search_button.pack(side=tk.LEFT)
        
        # Log level filter
        filter_frame = ttk.Frame(left_controls)
        filter_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(filter_frame, text="Level:").pack(side=tk.LEFT)
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10
        )
        level_combo.pack(side=tk.LEFT, padx=(5, 0))
        level_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_logs())
        
        # Right side controls
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side=tk.RIGHT)
        
        # Auto-scroll checkbox
        auto_scroll_check = ttk.Checkbutton(
            right_controls,
            text="Auto-scroll",
            variable=self.auto_scroll_var
        )
        auto_scroll_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # Control buttons
        self.refresh_button = ttk.Button(right_controls, text="Refresh", command=self._refresh_logs)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = ttk.Button(right_controls, text="Clear", command=self._clear_console)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_button = ttk.Button(right_controls, text="Export", command=self._export_logs)
        self.export_button.pack(side=tk.LEFT)
    
    def _create_console_section(self, parent: ttk.Frame) -> None:
        """
        Create the console display section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Console frame
        console_frame = ttk.LabelFrame(parent, text="Log Output", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Console text area with scrollbar
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            state=tk.DISABLED,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different log levels
        self._configure_text_tags()
        
        # Bind mouse events
        self.console_text.bind('<Button-3>', self._show_context_menu)  # Right-click
    
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
        
        # Line count label
        self.line_count_label = ttk.Label(status_frame, text="Lines: 0")
        self.line_count_label.pack(side=tk.RIGHT)
        
        # Log level indicator
        self.log_level_label = ttk.Label(status_frame, text="Showing: ALL")
        self.log_level_label.pack(side=tk.RIGHT, padx=(10, 10))
    
    def _configure_text_tags(self) -> None:
        """
        Configure text tags for different log levels with colors.
        """
        # Configure tags for different log levels
        self.console_text.tag_configure("DEBUG", foreground="#888888")      # Gray
        self.console_text.tag_configure("INFO", foreground="#00FF00")       # Green
        self.console_text.tag_configure("WARNING", foreground="#FFFF00")    # Yellow
        self.console_text.tag_configure("ERROR", foreground="#FF0000")      # Red
        self.console_text.tag_configure("CRITICAL", foreground="#FF00FF")   # Magenta
        self.console_text.tag_configure("PRODUCER", foreground="#00FFFF")   # Cyan
        self.console_text.tag_configure("CONSUMER", foreground="#FFA500")   # Orange
        self.console_text.tag_configure("SEARCH", background="#FFFF00", foreground="#000000")  # Highlight
    
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
            context_menu.add_command(label="Clear Console", command=self._clear_console)
            context_menu.add_command(label="Export Logs", command=self._export_logs)
            
            # Show menu
            context_menu.tk_popup(event.x_root, event.y_root)
            
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _copy_selection(self) -> None:
        """
        Copy selected text to clipboard.
        """
        try:
            if self.console_text.tag_ranges(tk.SEL):
                selected_text = self.console_text.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.parent_frame.clipboard_clear()
                self.parent_frame.clipboard_append(selected_text)
                self._set_status("Selected text copied to clipboard")
        except tk.TclError:
            self._set_status("No text selected")
        except Exception as e:
            self.logger.error(f"Error copying selection: {e}")
    
    def _select_all(self) -> None:
        """
        Select all text in the console.
        """
        try:
            self.console_text.tag_add(tk.SEL, "1.0", tk.END)
            self.console_text.mark_set(tk.INSERT, "1.0")
            self.console_text.see(tk.INSERT)
            self._set_status("All text selected")
        except Exception as e:
            self.logger.error(f"Error selecting all text: {e}")
    
    def _search_logs(self) -> None:
        """
        Search for text in the console logs.
        """
        try:
            search_term = self.search_var.get().strip()
            if not search_term:
                messagebox.showwarning("Search", "Please enter a search term")
                return
            
            # Clear previous search highlights
            self.console_text.tag_remove("SEARCH", "1.0", tk.END)
            
            # Search from current position
            start_pos = self.last_search_index
            pos = self.console_text.search(search_term, start_pos, tk.END, nocase=True)
            
            if pos:
                # Highlight found text
                end_pos = f"{pos}+{len(search_term)}c"
                self.console_text.tag_add("SEARCH", pos, end_pos)
                self.console_text.see(pos)
                self.console_text.mark_set(tk.INSERT, pos)
                
                # Update search position for next search
                self.last_search_index = end_pos
                
                self._set_status(f"Found '{search_term}' at {pos}")
            else:
                # Search from beginning if not found
                pos = self.console_text.search(search_term, "1.0", self.last_search_index, nocase=True)
                if pos:
                    end_pos = f"{pos}+{len(search_term)}c"
                    self.console_text.tag_add("SEARCH", pos, end_pos)
                    self.console_text.see(pos)
                    self.console_text.mark_set(tk.INSERT, pos)
                    self.last_search_index = end_pos
                    self._set_status(f"Found '{search_term}' at {pos} (wrapped)")
                else:
                    self._set_status(f"'{search_term}' not found")
                    self.last_search_index = "1.0"
            
        except Exception as e:
            self.logger.error(f"Error searching logs: {e}")
            self._set_status("Error during search")
    
    def _filter_logs(self) -> None:
        """
        Filter logs by selected level.
        """
        try:
            level = self.log_level_var.get()
            self.log_level_label.config(text=f"Showing: {level}")
            
            if level == "ALL":
                self._set_status("Showing all log levels")
            else:
                self._set_status(f"Filtering logs by {level} level")
            
            # Refresh logs with filter
            self._refresh_logs()
            
        except Exception as e:
            self.logger.error(f"Error filtering logs: {e}")
    
    def _refresh_logs(self) -> None:
        """
        Refresh the console logs display.
        """
        try:
            if not self.main_window:
                return
            
            # Get logger instance from main window
            app_logger = getattr(self.main_window, 'app_logger', None)
            if not app_logger:
                self._set_status("Logger not available")
                return
            
            # Get recent log messages
            messages = app_logger.get_log_messages(100)  # Get last 100 messages
            
            if messages:
                # Clear current display
                self.console_text.config(state=tk.NORMAL)
                self.console_text.delete(1.0, tk.END)
                
                # Add messages with filtering
                level_filter = self.log_level_var.get()
                displayed_count = 0
                
                for message in messages:
                    if self._should_display_message(message, level_filter):
                        self._add_log_message(message)
                        displayed_count += 1
                
                self.console_text.config(state=tk.DISABLED)
                
                # Update status
                if level_filter == "ALL":
                    self._set_status(f"Refreshed: {displayed_count} log messages")
                else:
                    self._set_status(f"Refreshed: {displayed_count} {level_filter} messages")
                
                # Auto-scroll to bottom if enabled
                if self.auto_scroll_var.get():
                    self.console_text.see(tk.END)
            else:
                self._set_status("No log messages available")
            
        except Exception as e:
            self.logger.error(f"Error refreshing logs: {e}")
            self._set_status("Error refreshing logs")
    
    def _should_display_message(self, message: str, level_filter: str) -> bool:
        """
        Check if a message should be displayed based on the level filter.
        
        Args:
            message (str): Log message
            level_filter (str): Selected level filter
        
        Returns:
            bool: True if message should be displayed
        """
        if level_filter == "ALL":
            return True
        
        # Check if message contains the selected level
        return level_filter in message.upper()
    
    def _add_log_message(self, message: str) -> None:
        """
        Add a log message to the console with appropriate formatting.
        
        Args:
            message (str): Log message to add
        """
        try:
            # Determine message type and apply appropriate tag
            tag = None
            if "DEBUG" in message:
                tag = "DEBUG"
            elif "INFO" in message:
                tag = "INFO"
            elif "WARNING" in message:
                tag = "WARNING"
            elif "ERROR" in message:
                tag = "ERROR"
            elif "CRITICAL" in message:
                tag = "CRITICAL"
            elif "PRODUCER" in message:
                tag = "PRODUCER"
            elif "CONSUMER" in message:
                tag = "CONSUMER"
            
            # Insert message with tag
            start_pos = self.console_text.index(tk.END)
            self.console_text.insert(tk.END, message + "\n")
            
            if tag:
                end_pos = self.console_text.index(tk.END + "-1c")
                self.console_text.tag_add(tag, start_pos, end_pos)
            
            # Update line count
            self.current_line_count += 1
            self.line_count_label.config(text=f"Lines: {self.current_line_count}")
            
            # Limit number of lines to prevent memory issues
            if self.current_line_count > self.max_lines:
                # Remove oldest lines
                lines_to_remove = self.current_line_count - self.max_lines
                self.console_text.delete("1.0", f"{lines_to_remove + 1}.0")
                self.current_line_count = self.max_lines
                self.line_count_label.config(text=f"Lines: {self.current_line_count}")
            
        except Exception as e:
            self.logger.error(f"Error adding log message: {e}")
    
    def _clear_console(self) -> None:
        """
        Clear the console display.
        """
        try:
            result = messagebox.askyesno(
                "Clear Console",
                "Are you sure you want to clear the console?\n\nThis will only clear the display, not the log files."
            )
            
            if result:
                self.console_text.config(state=tk.NORMAL)
                self.console_text.delete(1.0, tk.END)
                self.console_text.config(state=tk.DISABLED)
                
                # Reset counters
                self.current_line_count = 0
                self.line_count_label.config(text="Lines: 0")
                self.last_search_index = "1.0"
                
                self._set_status("Console cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing console: {e}")
            self._set_status("Error clearing console")
    
    def _export_logs(self) -> None:
        """
        Export console logs to a file.
        """
        try:
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                title="Export Console Logs",
                defaultextension=".log",
                filetypes=[
                    ("Log files", "*.log"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # Get all text from console
                self.console_text.config(state=tk.NORMAL)
                content = self.console_text.get(1.0, tk.END)
                self.console_text.config(state=tk.DISABLED)
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Kafka Tool Console Export\n")
                    f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Log Level Filter: {self.log_level_var.get()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(content)
                
                self._set_status(f"Console logs exported to: {file_path}")
                messagebox.showinfo("Export Complete", f"Console logs exported successfully to:\n{file_path}")
            
        except Exception as e:
            error_msg = f"Error exporting logs: {str(e)}"
            self.logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Export Error", error_msg)
    
    def _start_auto_refresh(self) -> None:
        """
        Start automatic refresh of console logs.
        """
        def auto_refresh():
            try:
                # Only refresh if auto-scroll is enabled (indicates user wants real-time updates)
                if self.auto_scroll_var.get():
                    self.update_console()
                
                # Schedule next refresh
                self.parent_frame.after(2000, auto_refresh)  # Refresh every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error in auto refresh: {e}")
                # Continue auto-refresh even if there's an error
                self.parent_frame.after(5000, auto_refresh)  # Retry in 5 seconds
        
        # Start auto-refresh
        self.parent_frame.after(1000, auto_refresh)  # Start after 1 second
    
    def update_console(self) -> None:
        """
        Update the console with new log messages.
        This method is called by the main window's update thread.
        """
        try:
            if not self.main_window:
                return
            
            # Get logger instance from main window
            app_logger = getattr(self.main_window, 'app_logger', None)
            if not app_logger:
                return
            
            # Get new log messages
            messages = app_logger.get_log_messages(10)  # Get last 10 messages
            
            if messages:
                self.console_text.config(state=tk.NORMAL)
                
                level_filter = self.log_level_var.get()
                new_messages_count = 0
                
                for message in messages:
                    if self._should_display_message(message, level_filter):
                        self._add_log_message(message)
                        new_messages_count += 1
                
                self.console_text.config(state=tk.DISABLED)
                
                # Auto-scroll to bottom if enabled and new messages were added
                if self.auto_scroll_var.get() and new_messages_count > 0:
                    self.console_text.see(tk.END)
            
        except Exception as e:
            self.logger.error(f"Error updating console: {e}")
    
    def clear_console(self) -> None:
        """
        Public method to clear console (called from main window).
        """
        self._clear_console()
    
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
        # Console panel doesn't need these managers directly
        pass
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        self._refresh_logs()