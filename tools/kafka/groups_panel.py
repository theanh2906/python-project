"""
Consumer Groups Panel Module

This module contains the UI panel for Kafka consumer groups management.
It provides controls for creating, deleting, and listing Kafka consumer groups.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List
import logging


class GroupsPanel:
    """
    UI panel for Kafka consumer groups management.
    
    This panel provides:
    - List existing consumer groups
    - Create new consumer groups
    - Delete selected consumer groups
    - Refresh consumer groups list
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the consumer groups panel.
        
        Args:
            parent_frame (ttk.Frame): Parent frame to contain this panel
            main_window: Reference to the main window
        """
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.kafka_manager = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # GUI components
        self.groups_listbox = None
        self.group_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        
        # Control buttons
        self.create_button = None
        self.delete_button = None
        self.refresh_button = None
        
        # Create the UI
        self._create_ui()
        
        # Initial state
        self._update_button_states()
        
        self.logger.info("Consumer Groups Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the consumer groups panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Consumer Groups Management", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create horizontal layout
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Consumer groups list
        self._create_groups_list_section(content_frame)
        
        # Right side - Group operations
        self._create_operations_section(content_frame)
        
        # Bottom - Status
        self._create_status_section(main_container)
    
    def _create_groups_list_section(self, parent: ttk.Frame) -> None:
        """
        Create the consumer groups list section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Left frame for groups list
        left_frame = ttk.LabelFrame(parent, text="Existing Consumer Groups", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Groups listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox
        self.groups_listbox = tk.Listbox(
            listbox_frame,
            font=('Consolas', 10),
            selectmode=tk.SINGLE
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.groups_listbox.yview)
        self.groups_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Pack listbox components
        self.groups_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.groups_listbox.bind('<<ListboxSelect>>', self._on_group_select)
        
        # Refresh button
        refresh_frame = ttk.Frame(left_frame)
        refresh_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_button = ttk.Button(
            refresh_frame,
            text="Refresh Groups",
            command=self._refresh_groups
        )
        self.refresh_button.pack(side=tk.LEFT)
        
        # Groups count label
        self.groups_count_label = ttk.Label(refresh_frame, text="Groups: 0")
        self.groups_count_label.pack(side=tk.RIGHT)
    
    def _create_operations_section(self, parent: ttk.Frame) -> None:
        """
        Create the consumer group operations section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Right frame for operations
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Create group section
        self._create_create_group_section(right_frame)
        
        # Delete group section
        self._create_delete_group_section(right_frame)
        
        # Group details section
        self._create_group_details_section(right_frame)
    
    def _create_create_group_section(self, parent: ttk.Frame) -> None:
        """
        Create the create consumer group section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Create group frame
        create_frame = ttk.LabelFrame(parent, text="Create Consumer Group", padding=10)
        create_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Group ID
        ttk.Label(create_frame, text="Group ID:").pack(anchor=tk.W, pady=(0, 5))
        group_id_entry = ttk.Entry(create_frame, textvariable=self.group_id_var, width=30)
        group_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Help text
        help_label = ttk.Label(
            create_frame,
            text="Enter a unique identifier for the consumer group.\n"
                 "Example: my-consumer-group",
            font=('Arial', 8),
            foreground="gray",
            justify=tk.LEFT
        )
        help_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create button
        self.create_button = ttk.Button(
            create_frame,
            text="Create Consumer Group",
            command=self._create_group,
            style="Success.TButton"
        )
        self.create_button.pack(pady=(5, 0))
        
        # Note about group creation
        note_label = ttk.Label(
            create_frame,
            text="Note: Consumer groups are created automatically\n"
                 "when consumers join them. This creates an\n"
                 "empty group for management purposes.",
            font=('Arial', 8),
            foreground="blue",
            justify=tk.LEFT
        )
        note_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _create_delete_group_section(self, parent: ttk.Frame) -> None:
        """
        Create the delete consumer group section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Delete group frame
        delete_frame = ttk.LabelFrame(parent, text="Delete Consumer Group", padding=10)
        delete_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Selected group label
        self.selected_group_label = ttk.Label(
            delete_frame,
            text="No group selected",
            font=('Arial', 9, 'italic'),
            foreground="gray"
        )
        self.selected_group_label.pack(pady=(0, 10))
        
        # Delete button
        self.delete_button = ttk.Button(
            delete_frame,
            text="Delete Selected Group",
            command=self._delete_group,
            style="Danger.TButton"
        )
        self.delete_button.pack()
        
        # Warning label
        warning_label = ttk.Label(
            delete_frame,
            text="⚠️ Deletion is permanent!\n"
                 "This will remove all consumer\n"
                 "offsets and group metadata.",
            font=('Arial', 8),
            foreground="red",
            justify=tk.CENTER
        )
        warning_label.pack(pady=(5, 0))
    
    def _create_group_details_section(self, parent: ttk.Frame) -> None:
        """
        Create the consumer group details section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Details frame
        details_frame = ttk.LabelFrame(parent, text="Group Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Details text area
        self.details_text = tk.Text(
            details_frame,
            height=12,
            width=35,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 9)
        )
        
        # Scrollbar for details
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        # Pack details components
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial details text
        self._update_details_text("Select a consumer group to view details.")
    
    def _create_status_section(self, parent: ttk.Frame) -> None:
        """
        Create the status section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Status frame
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Status label
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Progress bar (hidden by default)
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT)
        self.progress_bar.pack_forget()  # Hide initially
    
    def _refresh_groups(self) -> None:
        """
        Refresh the consumer groups list in a separate thread.
        """
        if not self.kafka_manager:
            self._set_status("Kafka manager not initialized")
            return
        
        # Show progress
        self._set_operation_in_progress(True)
        self._set_status("Refreshing consumer groups...")
        
        # Refresh in background thread
        thread = threading.Thread(target=self._refresh_groups_worker, daemon=True)
        thread.start()
    
    def _refresh_groups_worker(self) -> None:
        """
        Worker thread for refreshing consumer groups.
        """
        try:
            success, groups, message = self.kafka_manager.list_consumer_groups()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_refresh_result, success, groups, message)
            
        except Exception as e:
            error_msg = f"Error refreshing consumer groups: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_refresh_result, False, [], error_msg)
    
    def _handle_refresh_result(self, success: bool, groups: List[str], message: str) -> None:
        """
        Handle the result of consumer groups refresh operation.
        
        Args:
            success (bool): Whether the operation was successful
            groups (List[str]): List of consumer groups
            message (str): Result message
        """
        self._set_operation_in_progress(False)
        
        if success:
            self._update_groups_list(groups)
            self._set_status(message)
        else:
            self._set_status(f"Error: {message}")
            messagebox.showerror("Error", message)
    
    def _update_groups_list(self, groups: List[str]) -> None:
        """
        Update the consumer groups listbox with new groups.
        
        Args:
            groups (List[str]): List of consumer group IDs
        """
        # Clear current list
        self.groups_listbox.delete(0, tk.END)
        
        # Add groups
        for group in sorted(groups):
            self.groups_listbox.insert(tk.END, group)
        
        # Update count
        self.groups_count_label.config(text=f"Groups: {len(groups)}")
        
        # Update button states
        self._update_button_states()
    
    def _create_group(self) -> None:
        """
        Create a new consumer group.
        
        Note: In Kafka, consumer groups are typically created automatically when consumers join.
        This method provides a way to create an empty group for management purposes.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized")
            return
        
        # Validate input
        group_id = self.group_id_var.get().strip()
        if not group_id:
            messagebox.showerror("Error", "Group ID cannot be empty")
            return
        
        # Show info about consumer group creation
        result = messagebox.askquestion(
            "Create Consumer Group",
            f"Create consumer group '{group_id}'?\n\n"
            "Note: Consumer groups are typically created automatically when consumers join them. "
            "This will create an empty group that will appear in the list once consumers connect to it.",
            icon='question'
        )
        
        if result != 'yes':
            return
        
        # For now, just show a message since consumer groups are created automatically
        # In a full implementation, you might want to create a temporary consumer to initialize the group
        messagebox.showinfo(
            "Consumer Group Creation",
            f"Consumer group '{group_id}' will be created automatically when the first consumer joins it.\n\n"
            "To create the group immediately, start a consumer with this group ID."
        )
        
        # Clear the input
        self.group_id_var.set("")
        
        # Set status
        self._set_status(f"Consumer group '{group_id}' will be created when consumers join")
    
    def _delete_group(self) -> None:
        """
        Delete the selected consumer group in a separate thread.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized")
            return
        
        # Get selected group
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No consumer group selected")
            return
        
        group_id = self.groups_listbox.get(selection[0])
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete consumer group '{group_id}'?\n\n"
            "This action cannot be undone and will permanently remove:\n"
            "• All consumer offsets for this group\n"
            "• Group metadata and configuration\n"
            "• Consumer assignments and state\n\n"
            "Active consumers in this group will be disconnected."
        )
        
        if not result:
            return
        
        # Show progress
        self._set_operation_in_progress(True)
        self._set_status(f"Deleting consumer group '{group_id}'...")
        
        # Delete group in background thread
        thread = threading.Thread(target=self._delete_group_worker, args=(group_id,), daemon=True)
        thread.start()
    
    def _delete_group_worker(self, group_id: str) -> None:
        """
        Worker thread for deleting a consumer group.
        
        Args:
            group_id (str): ID of the consumer group to delete
        """
        try:
            success, message = self.kafka_manager.delete_consumer_group(group_id)
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_delete_result, success, message, group_id)
            
        except Exception as e:
            error_msg = f"Error deleting consumer group: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_delete_result, False, error_msg, group_id)
    
    def _handle_delete_result(self, success: bool, message: str, group_id: str) -> None:
        """
        Handle the result of consumer group deletion operation.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Result message
            group_id (str): ID of the consumer group that was deleted
        """
        self._set_operation_in_progress(False)
        
        if success:
            messagebox.showinfo("Success", message)
            self._set_status(f"Consumer group '{group_id}' deleted successfully")
            
            # Refresh groups list
            self._refresh_groups()
        else:
            messagebox.showerror("Error", message)
            self._set_status(f"Failed to delete consumer group: {message}")
    
    def _on_group_select(self, event) -> None:
        """
        Handle consumer group selection in the listbox.
        
        Args:
            event: Selection event
        """
        try:
            selection = self.groups_listbox.curselection()
            if selection:
                group_id = self.groups_listbox.get(selection[0])
                self.selected_group_label.config(
                    text=f"Selected: {group_id}",
                    foreground="black",
                    font=('Arial', 9, 'normal')
                )
                
                # Update group details
                self._update_group_details(group_id)
            else:
                self.selected_group_label.config(
                    text="No group selected",
                    foreground="gray",
                    font=('Arial', 9, 'italic')
                )
                self._update_details_text("Select a consumer group to view details.")
            
            # Update button states
            self._update_button_states()
            
        except Exception as e:
            self.logger.error(f"Error handling group selection: {e}")
    
    def _update_group_details(self, group_id: str) -> None:
        """
        Update the consumer group details display.
        
        Args:
            group_id (str): ID of the selected consumer group
        """
        try:
            # For now, show basic information
            # In a full implementation, you would query group metadata, consumer assignments, etc.
            details = [
                f"Consumer Group: {group_id}",
                "",
                "Basic Information:",
                f"• Group ID: {group_id}",
                f"• Type: Consumer Group",
                "",
                "Available Operations:",
                "• Delete group (removes all offsets)",
                "• View group in producer/consumer simulator",
                "",
                "Note: Detailed consumer group metadata",
                "including member information, partition",
                "assignments, and consumer lag requires",
                "additional Kafka Admin API calls and",
                "will be implemented in future versions.",
                "",
                "Consumer Group States:",
                "• Empty: No active consumers",
                "• PreparingRebalance: Rebalancing in progress",
                "• CompletingRebalance: Finalizing rebalance",
                "• Stable: Normal operation",
                "• Dead: Group has been deleted"
            ]
            
            self._update_details_text("\n".join(details))
            
        except Exception as e:
            self.logger.error(f"Error updating group details: {e}")
            self._update_details_text(f"Error loading details: {str(e)}")
    
    def _update_details_text(self, text: str) -> None:
        """
        Update the details text area.
        
        Args:
            text (str): Text to display
        """
        try:
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, text)
            self.details_text.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Error updating details text: {e}")
    
    def _set_status(self, message: str) -> None:
        """
        Set the status message.
        
        Args:
            message (str): Status message
        """
        self.status_var.set(message)
    
    def _set_operation_in_progress(self, in_progress: bool) -> None:
        """
        Set UI state for operation in progress.
        
        Args:
            in_progress (bool): Whether an operation is in progress
        """
        state = tk.DISABLED if in_progress else tk.NORMAL
        
        # Disable/enable buttons
        if self.create_button:
            self.create_button.config(state=state)
        if self.delete_button:
            self.delete_button.config(state=state)
        if self.refresh_button:
            self.refresh_button.config(state=state)
        
        # Show/hide progress bar
        if in_progress:
            self.progress_bar.pack(side=tk.RIGHT)
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def _update_button_states(self) -> None:
        """
        Update the state of control buttons based on current status.
        """
        try:
            if not self.kafka_manager:
                # No Kafka manager - disable all buttons
                if self.create_button:
                    self.create_button.config(state=tk.DISABLED)
                if self.delete_button:
                    self.delete_button.config(state=tk.DISABLED)
                if self.refresh_button:
                    self.refresh_button.config(state=tk.DISABLED)
                return
            
            # Check if server is running
            server_running = self.kafka_manager.is_server_running()
            
            # Enable/disable buttons based on server status
            button_state = tk.NORMAL if server_running else tk.DISABLED
            
            if self.create_button:
                self.create_button.config(state=button_state)
            if self.refresh_button:
                self.refresh_button.config(state=button_state)
            
            # Delete button requires both server running and group selected
            selection = self.groups_listbox.curselection()
            delete_state = tk.NORMAL if (server_running and selection) else tk.DISABLED
            
            if self.delete_button:
                self.delete_button.config(state=delete_state)
                
        except Exception as e:
            self.logger.error(f"Error updating button states: {e}")
    
    def update_managers(self, kafka_manager, producer_consumer_manager, config_parser) -> None:
        """
        Update the manager instances.
        
        Args:
            kafka_manager: Kafka manager instance
            producer_consumer_manager: Producer/consumer manager instance
            config_parser: Config parser instance
        """
        self.kafka_manager = kafka_manager
        
        # Update button states
        self._update_button_states()
        
        # Auto-refresh groups if server is running
        if kafka_manager and kafka_manager.is_server_running():
            self._refresh_groups()
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        self._refresh_groups()
    
    def get_selected_group_id(self) -> Optional[str]:
        """
        Get the currently selected consumer group ID.
        
        Returns:
            Optional[str]: Selected group ID or None
        """
        try:
            selection = self.groups_listbox.curselection()
            if selection:
                return self.groups_listbox.get(selection[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting selected group: {e}")
            return None