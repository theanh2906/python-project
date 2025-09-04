"""
Topics Panel Module

This module contains the UI panel for Kafka topics management.
It provides controls for creating, deleting, and listing Kafka topics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List
import logging


class TopicsPanel:
    """
    UI panel for Kafka topics management.
    
    This panel provides:
    - List existing topics
    - Create new topics with custom parameters
    - Delete selected topics
    - Refresh topics list
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the topics panel.
        
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
        self.topics_listbox = None
        self.topic_name_var = tk.StringVar()
        self.partitions_var = tk.StringVar(value="1")
        self.replication_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="Ready")
        
        # Control buttons
        self.create_button = None
        self.delete_button = None
        self.refresh_button = None
        
        # Create the UI
        self._create_ui()
        
        # Initial state
        self._update_button_states()
        
        self.logger.info("Topics Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the topics panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Topics Management", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create horizontal layout
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Topics list
        self._create_topics_list_section(content_frame)
        
        # Right side - Topic operations
        self._create_operations_section(content_frame)
        
        # Bottom - Status
        self._create_status_section(main_container)
    
    def _create_topics_list_section(self, parent: ttk.Frame) -> None:
        """
        Create the topics list section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Left frame for topics list
        left_frame = ttk.LabelFrame(parent, text="Existing Topics", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Topics listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox
        self.topics_listbox = tk.Listbox(
            listbox_frame,
            font=('Consolas', 10),
            selectmode=tk.SINGLE
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.topics_listbox.yview)
        self.topics_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Pack listbox components
        self.topics_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.topics_listbox.bind('<<ListboxSelect>>', self._on_topic_select)
        
        # Refresh button
        refresh_frame = ttk.Frame(left_frame)
        refresh_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_button = ttk.Button(
            refresh_frame,
            text="Refresh Topics",
            command=self._refresh_topics
        )
        self.refresh_button.pack(side=tk.LEFT)
        
        # Topics count label
        self.topics_count_label = ttk.Label(refresh_frame, text="Topics: 0")
        self.topics_count_label.pack(side=tk.RIGHT)
    
    def _create_operations_section(self, parent: ttk.Frame) -> None:
        """
        Create the topic operations section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Right frame for operations
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Create topic section
        self._create_create_topic_section(right_frame)
        
        # Delete topic section
        self._create_delete_topic_section(right_frame)
        
        # Topic details section
        self._create_topic_details_section(right_frame)
    
    def _create_create_topic_section(self, parent: ttk.Frame) -> None:
        """
        Create the create topic section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Create topic frame
        create_frame = ttk.LabelFrame(parent, text="Create New Topic", padding=10)
        create_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Topic name
        ttk.Label(create_frame, text="Topic Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        topic_name_entry = ttk.Entry(create_frame, textvariable=self.topic_name_var, width=25)
        topic_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        
        # Partitions
        ttk.Label(create_frame, text="Partitions:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        partitions_spinbox = ttk.Spinbox(
            create_frame,
            from_=1,
            to=100,
            textvariable=self.partitions_var,
            width=23
        )
        partitions_spinbox.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        
        # Replication factor
        ttk.Label(create_frame, text="Replication Factor:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        replication_spinbox = ttk.Spinbox(
            create_frame,
            from_=1,
            to=10,
            textvariable=self.replication_var,
            width=23
        )
        replication_spinbox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 10))
        
        # Create button
        self.create_button = ttk.Button(
            create_frame,
            text="Create Topic",
            command=self._create_topic,
            style="Success.TButton"
        )
        self.create_button.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # Configure grid weights
        create_frame.columnconfigure(1, weight=1)
    
    def _create_delete_topic_section(self, parent: ttk.Frame) -> None:
        """
        Create the delete topic section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Delete topic frame
        delete_frame = ttk.LabelFrame(parent, text="Delete Topic", padding=10)
        delete_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Selected topic label
        self.selected_topic_label = ttk.Label(
            delete_frame,
            text="No topic selected",
            font=('Arial', 9, 'italic'),
            foreground="gray"
        )
        self.selected_topic_label.pack(pady=(0, 10))
        
        # Delete button
        self.delete_button = ttk.Button(
            delete_frame,
            text="Delete Selected Topic",
            command=self._delete_topic,
            style="Danger.TButton"
        )
        self.delete_button.pack()
        
        # Warning label
        warning_label = ttk.Label(
            delete_frame,
            text="⚠️ Deletion is permanent!",
            font=('Arial', 8),
            foreground="red"
        )
        warning_label.pack(pady=(5, 0))
    
    def _create_topic_details_section(self, parent: ttk.Frame) -> None:
        """
        Create the topic details section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Details frame
        details_frame = ttk.LabelFrame(parent, text="Topic Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Details text area
        self.details_text = tk.Text(
            details_frame,
            height=10,
            width=30,
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
        self._update_details_text("Select a topic to view details.")
    
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
    
    def _refresh_topics(self) -> None:
        """
        Refresh the topics list in a separate thread.
        """
        if not self.kafka_manager:
            self._set_status("Kafka manager not initialized")
            return
        
        # Show progress
        self._set_operation_in_progress(True)
        self._set_status("Refreshing topics...")
        
        # Refresh in background thread
        thread = threading.Thread(target=self._refresh_topics_worker, daemon=True)
        thread.start()
    
    def _refresh_topics_worker(self) -> None:
        """
        Worker thread for refreshing topics.
        """
        try:
            success, topics, message = self.kafka_manager.list_topics()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_refresh_result, success, topics, message)
            
        except Exception as e:
            error_msg = f"Error refreshing topics: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_refresh_result, False, [], error_msg)
    
    def _handle_refresh_result(self, success: bool, topics: List[str], message: str) -> None:
        """
        Handle the result of topics refresh operation.
        
        Args:
            success (bool): Whether the operation was successful
            topics (List[str]): List of topics
            message (str): Result message
        """
        self._set_operation_in_progress(False)
        
        if success:
            self._update_topics_list(topics)
            self._set_status(message)
        else:
            self._set_status(f"Error: {message}")
            messagebox.showerror("Error", message)
    
    def _update_topics_list(self, topics: List[str]) -> None:
        """
        Update the topics listbox with new topics.
        
        Args:
            topics (List[str]): List of topic names
        """
        # Clear current list
        self.topics_listbox.delete(0, tk.END)
        
        # Add topics
        for topic in sorted(topics):
            self.topics_listbox.insert(tk.END, topic)
        
        # Update count
        self.topics_count_label.config(text=f"Topics: {len(topics)}")
        
        # Update button states
        self._update_button_states()
    
    def _create_topic(self) -> None:
        """
        Create a new topic in a separate thread.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized")
            return
        
        # Validate input
        topic_name = self.topic_name_var.get().strip()
        if not topic_name:
            messagebox.showerror("Error", "Topic name cannot be empty")
            return
        
        try:
            partitions = int(self.partitions_var.get())
            replication_factor = int(self.replication_var.get())
        except ValueError:
            messagebox.showerror("Error", "Partitions and replication factor must be valid numbers")
            return
        
        if partitions < 1:
            messagebox.showerror("Error", "Partitions must be at least 1")
            return
        
        if replication_factor < 1:
            messagebox.showerror("Error", "Replication factor must be at least 1")
            return
        
        # Show progress
        self._set_operation_in_progress(True)
        self._set_status(f"Creating topic '{topic_name}'...")
        
        # Create topic in background thread
        thread = threading.Thread(
            target=self._create_topic_worker,
            args=(topic_name, partitions, replication_factor),
            daemon=True
        )
        thread.start()
    
    def _create_topic_worker(self, topic_name: str, partitions: int, replication_factor: int) -> None:
        """
        Worker thread for creating a topic.
        
        Args:
            topic_name (str): Name of the topic to create
            partitions (int): Number of partitions
            replication_factor (int): Replication factor
        """
        try:
            success, message = self.kafka_manager.create_topic(topic_name, partitions, replication_factor)
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_create_result, success, message, topic_name)
            
        except Exception as e:
            error_msg = f"Error creating topic: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_create_result, False, error_msg, topic_name)
    
    def _handle_create_result(self, success: bool, message: str, topic_name: str) -> None:
        """
        Handle the result of topic creation operation.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Result message
            topic_name (str): Name of the topic that was created
        """
        self._set_operation_in_progress(False)
        
        if success:
            messagebox.showinfo("Success", message)
            self._set_status(f"Topic '{topic_name}' created successfully")
            
            # Clear form
            self.topic_name_var.set("")
            self.partitions_var.set("1")
            self.replication_var.set("1")
            
            # Refresh topics list
            self._refresh_topics()
        else:
            messagebox.showerror("Error", message)
            self._set_status(f"Failed to create topic: {message}")
    
    def _delete_topic(self) -> None:
        """
        Delete the selected topic in a separate thread.
        """
        if not self.kafka_manager:
            messagebox.showerror("Error", "Kafka manager not initialized")
            return
        
        # Get selected topic
        selection = self.topics_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No topic selected")
            return
        
        topic_name = self.topics_listbox.get(selection[0])
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete topic '{topic_name}'?\n\n"
            "This action cannot be undone and will permanently remove all messages in the topic."
        )
        
        if not result:
            return
        
        # Show progress
        self._set_operation_in_progress(True)
        self._set_status(f"Deleting topic '{topic_name}'...")
        
        # Delete topic in background thread
        thread = threading.Thread(target=self._delete_topic_worker, args=(topic_name,), daemon=True)
        thread.start()
    
    def _delete_topic_worker(self, topic_name: str) -> None:
        """
        Worker thread for deleting a topic.
        
        Args:
            topic_name (str): Name of the topic to delete
        """
        try:
            success, message = self.kafka_manager.delete_topic(topic_name)
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_delete_result, success, message, topic_name)
            
        except Exception as e:
            error_msg = f"Error deleting topic: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_delete_result, False, error_msg, topic_name)
    
    def _handle_delete_result(self, success: bool, message: str, topic_name: str) -> None:
        """
        Handle the result of topic deletion operation.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Result message
            topic_name (str): Name of the topic that was deleted
        """
        self._set_operation_in_progress(False)
        
        if success:
            messagebox.showinfo("Success", message)
            self._set_status(f"Topic '{topic_name}' deleted successfully")
            
            # Refresh topics list
            self._refresh_topics()
        else:
            messagebox.showerror("Error", message)
            self._set_status(f"Failed to delete topic: {message}")
    
    def _on_topic_select(self, event) -> None:
        """
        Handle topic selection in the listbox.
        
        Args:
            event: Selection event
        """
        try:
            selection = self.topics_listbox.curselection()
            if selection:
                topic_name = self.topics_listbox.get(selection[0])
                self.selected_topic_label.config(
                    text=f"Selected: {topic_name}",
                    foreground="black",
                    font=('Arial', 9, 'normal')
                )
                
                # Update topic details
                self._update_topic_details(topic_name)
            else:
                self.selected_topic_label.config(
                    text="No topic selected",
                    foreground="gray",
                    font=('Arial', 9, 'italic')
                )
                self._update_details_text("Select a topic to view details.")
            
            # Update button states
            self._update_button_states()
            
        except Exception as e:
            self.logger.error(f"Error handling topic selection: {e}")
    
    def _update_topic_details(self, topic_name: str) -> None:
        """
        Update the topic details display.
        
        Args:
            topic_name (str): Name of the selected topic
        """
        try:
            # For now, show basic information
            # In a full implementation, you would query topic metadata
            details = [
                f"Topic: {topic_name}",
                "",
                "Basic Information:",
                f"• Name: {topic_name}",
                f"• Type: User Topic",
                "",
                "Note: Detailed topic metadata",
                "requires additional Kafka Admin",
                "API calls and will be implemented",
                "in future versions."
            ]
            
            self._update_details_text("\n".join(details))
            
        except Exception as e:
            self.logger.error(f"Error updating topic details: {e}")
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
            
            # Delete button requires both server running and topic selected
            selection = self.topics_listbox.curselection()
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
        
        # Auto-refresh topics if server is running
        if kafka_manager and kafka_manager.is_server_running():
            self._refresh_topics()
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        self._refresh_topics()