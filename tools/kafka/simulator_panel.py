"""
Simulator Panel Module

This module contains the UI panel for Kafka producer/consumer simulation.
It provides controls for simulating producers and consumers with real-time message handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from datetime import datetime
from typing import Optional, List
import logging


class SimulatorPanel:
    """
    UI panel for Kafka producer/consumer simulation.
    
    This panel provides:
    - Producer simulation with manual and automatic message sending
    - Consumer simulation with real-time message consumption
    - Topic and consumer group selection
    - Real-time message display
    """
    
    def __init__(self, parent_frame: ttk.Frame, main_window):
        """
        Initialize the simulator panel.
        
        Args:
            parent_frame (ttk.Frame): Parent frame to contain this panel
            main_window: Reference to the main window
        """
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.kafka_manager = None
        self.producer_consumer_manager = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # GUI components
        self.topic_var = tk.StringVar()
        self.consumer_group_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.auto_generate_var = tk.BooleanVar()
        self.auto_interval_var = tk.StringVar(value="5")
        self.status_var = tk.StringVar(value="Ready")
        
        # Control buttons
        self.start_producer_button = None
        self.stop_producer_button = None
        self.send_message_button = None
        self.start_consumer_button = None
        self.stop_consumer_button = None
        self.refresh_button = None
        
        # Dropdowns
        self.topic_combo = None
        self.group_combo = None
        
        # Message display
        self.messages_text = None
        
        # Create the UI
        self._create_ui()
        
        # Initial state
        self._update_button_states()
        
        self.logger.info("Simulator Panel initialized")
    
    def _create_ui(self) -> None:
        """
        Create the simulator panel UI components.
        """
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_container, text="Producer/Consumer Simulator", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create main layout
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Controls
        self._create_controls_section(content_frame)
        
        # Right side - Messages display
        self._create_messages_section(content_frame)
        
        # Bottom - Status
        self._create_status_section(main_container)
    
    def _create_controls_section(self, parent: ttk.Frame) -> None:
        """
        Create the controls section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Left frame for controls
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Configuration section
        self._create_config_section(left_frame)
        
        # Producer section
        self._create_producer_section(left_frame)
        
        # Consumer section
        self._create_consumer_section(left_frame)
    
    def _create_config_section(self, parent: ttk.Frame) -> None:
        """
        Create the configuration section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Configuration frame
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Topic selection
        ttk.Label(config_frame, text="Topic:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.topic_combo = ttk.Combobox(config_frame, textvariable=self.topic_var, width=25, state="readonly")
        self.topic_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        
        # Consumer group selection
        ttk.Label(config_frame, text="Consumer Group:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.group_combo = ttk.Combobox(config_frame, textvariable=self.consumer_group_var, width=25)
        self.group_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(
            config_frame,
            text="Refresh Topics & Groups",
            command=self._refresh_data
        )
        self.refresh_button.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Configure grid weights
        config_frame.columnconfigure(1, weight=1)
    
    def _create_producer_section(self, parent: ttk.Frame) -> None:
        """
        Create the producer section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Producer frame
        producer_frame = ttk.LabelFrame(parent, text="Producer", padding=10)
        producer_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Message input
        ttk.Label(producer_frame, text="Message:").pack(anchor=tk.W, pady=(0, 5))
        message_entry = ttk.Entry(producer_frame, textvariable=self.message_var, width=30)
        message_entry.pack(fill=tk.X, pady=(0, 10))
        message_entry.bind('<Return>', lambda e: self._send_message())
        
        # Send message button
        self.send_message_button = ttk.Button(
            producer_frame,
            text="Send Message",
            command=self._send_message
        )
        self.send_message_button.pack(pady=(0, 10))
        
        # Auto-generate section
        auto_frame = ttk.Frame(producer_frame)
        auto_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Auto-generate checkbox
        auto_check = ttk.Checkbutton(
            auto_frame,
            text="Auto-generate messages",
            variable=self.auto_generate_var,
            command=self._toggle_auto_generate
        )
        auto_check.pack(anchor=tk.W)
        
        # Interval setting
        interval_frame = ttk.Frame(auto_frame)
        interval_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(interval_frame, text="Interval (seconds):").pack(side=tk.LEFT)
        interval_spinbox = ttk.Spinbox(
            interval_frame,
            from_=1,
            to=60,
            textvariable=self.auto_interval_var,
            width=10
        )
        interval_spinbox.pack(side=tk.RIGHT)
        
        # Producer control buttons
        button_frame = ttk.Frame(producer_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_producer_button = ttk.Button(
            button_frame,
            text="Start Producer",
            command=self._start_producer,
            style="Success.TButton"
        )
        self.start_producer_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_producer_button = ttk.Button(
            button_frame,
            text="Stop Producer",
            command=self._stop_producer,
            style="Danger.TButton"
        )
        self.stop_producer_button.pack(side=tk.LEFT)
    
    def _create_consumer_section(self, parent: ttk.Frame) -> None:
        """
        Create the consumer section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Consumer frame
        consumer_frame = ttk.LabelFrame(parent, text="Consumer", padding=10)
        consumer_frame.pack(fill=tk.X)
        
        # Consumer info
        info_label = ttk.Label(
            consumer_frame,
            text="Consumer will subscribe to the selected topic\n"
                 "and consumer group. Messages will appear\n"
                 "in the messages panel on the right.",
            font=('Arial', 9),
            foreground="gray",
            justify=tk.LEFT
        )
        info_label.pack(pady=(0, 10))
        
        # Consumer control buttons
        button_frame = ttk.Frame(consumer_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_consumer_button = ttk.Button(
            button_frame,
            text="Start Consumer",
            command=self._start_consumer,
            style="Success.TButton"
        )
        self.start_consumer_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_consumer_button = ttk.Button(
            button_frame,
            text="Stop Consumer",
            command=self._stop_consumer,
            style="Danger.TButton"
        )
        self.stop_consumer_button.pack(side=tk.LEFT)
    
    def _create_messages_section(self, parent: ttk.Frame) -> None:
        """
        Create the messages display section.
        
        Args:
            parent (ttk.Frame): Parent frame
        """
        # Right frame for messages
        right_frame = ttk.LabelFrame(parent, text="Messages", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Messages text area
        self.messages_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            state=tk.DISABLED
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Control buttons for messages
        messages_button_frame = ttk.Frame(right_frame)
        messages_button_frame.pack(fill=tk.X)
        
        clear_button = ttk.Button(
            messages_button_frame,
            text="Clear Messages",
            command=self._clear_messages
        )
        clear_button.pack(side=tk.LEFT)
        
        # Message count label
        self.message_count_label = ttk.Label(messages_button_frame, text="Messages: 0")
        self.message_count_label.pack(side=tk.RIGHT)
        
        # Initialize message counter
        self.message_count = 0
    
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
        
        # Producer/Consumer status
        self.producer_status_label = ttk.Label(status_frame, text="Producer: Stopped")
        self.producer_status_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.consumer_status_label = ttk.Label(status_frame, text="Consumer: Stopped")
        self.consumer_status_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _refresh_data(self) -> None:
        """
        Refresh topics and consumer groups data.
        """
        if not self.kafka_manager:
            self._set_status("Kafka manager not initialized")
            return
        
        self._set_status("Refreshing topics and consumer groups...")
        
        # Refresh in background thread
        thread = threading.Thread(target=self._refresh_data_worker, daemon=True)
        thread.start()
    
    def _refresh_data_worker(self) -> None:
        """
        Worker thread for refreshing data.
        """
        try:
            # Get topics
            topics_success, topics, topics_msg = self.kafka_manager.list_topics()
            
            # Get consumer groups
            groups_success, groups, groups_msg = self.kafka_manager.list_consumer_groups()
            
            # Update UI in main thread
            self.parent_frame.after(0, self._handle_refresh_result, 
                                  topics_success, topics, groups_success, groups)
            
        except Exception as e:
            error_msg = f"Error refreshing data: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, self._handle_refresh_result, False, [], False, [])
    
    def _handle_refresh_result(self, topics_success: bool, topics: List[str], 
                             groups_success: bool, groups: List[str]) -> None:
        """
        Handle the result of data refresh operation.
        
        Args:
            topics_success (bool): Whether topics refresh was successful
            topics (List[str]): List of topics
            groups_success (bool): Whether groups refresh was successful
            groups (List[str]): List of consumer groups
        """
        if topics_success:
            # Update topics dropdown
            self.topic_combo['values'] = topics
            if topics and not self.topic_var.get():
                self.topic_var.set(topics[0])
        
        if groups_success:
            # Update consumer groups dropdown
            self.group_combo['values'] = groups
            if groups and not self.consumer_group_var.get():
                self.consumer_group_var.set(groups[0])
        
        if topics_success and groups_success:
            self._set_status(f"Refreshed: {len(topics)} topics, {len(groups)} consumer groups")
        else:
            self._set_status("Error refreshing data")
    
    def _send_message(self) -> None:
        """
        Send a single message.
        """
        if not self.producer_consumer_manager:
            messagebox.showerror("Error", "Producer/Consumer manager not initialized")
            return
        
        topic = self.topic_var.get().strip()
        message = self.message_var.get().strip()
        
        if not topic:
            messagebox.showerror("Error", "Please select a topic")
            return
        
        if not message:
            messagebox.showerror("Error", "Please enter a message")
            return
        
        # Send message in background thread
        thread = threading.Thread(target=self._send_message_worker, args=(topic, message), daemon=True)
        thread.start()
    
    def _send_message_worker(self, topic: str, message: str) -> None:
        """
        Worker thread for sending a message.
        
        Args:
            topic (str): Target topic
            message (str): Message to send
        """
        try:
            producer = self.producer_consumer_manager.get_producer()
            success = producer.send_message(topic, message)
            
            if success:
                # Clear message input in main thread
                self.parent_frame.after(0, lambda: self.message_var.set(""))
                self.parent_frame.after(0, lambda: self._set_status(f"Message sent to topic '{topic}'"))
            else:
                self.parent_frame.after(0, lambda: self._set_status("Failed to send message"))
                
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            self.logger.error(error_msg)
            self.parent_frame.after(0, lambda: self._set_status(error_msg))
    
    def _start_producer(self) -> None:
        """
        Start the producer (for auto-generation).
        """
        if not self.producer_consumer_manager:
            messagebox.showerror("Error", "Producer/Consumer manager not initialized")
            return
        
        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please select a topic")
            return
        
        if not self.auto_generate_var.get():
            messagebox.showinfo("Info", "Enable 'Auto-generate messages' to start the producer")
            return
        
        try:
            interval = int(self.auto_interval_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid interval value")
            return
        
        # Start auto producer
        producer = self.producer_consumer_manager.get_producer()
        success = producer.start_auto_producer(topic, interval)
        
        if success:
            self._set_status(f"Auto producer started for topic '{topic}'")
            self._update_producer_status()
        else:
            self._set_status("Failed to start auto producer")
    
    def _stop_producer(self) -> None:
        """
        Stop the producer.
        """
        if not self.producer_consumer_manager:
            return
        
        producer = self.producer_consumer_manager.get_producer()
        success = producer.stop_producer()
        
        if success:
            self._set_status("Producer stopped")
            self._update_producer_status()
        else:
            self._set_status("Failed to stop producer")
    
    def _start_consumer(self) -> None:
        """
        Start the consumer.
        """
        if not self.producer_consumer_manager:
            messagebox.showerror("Error", "Producer/Consumer manager not initialized")
            return
        
        topic = self.topic_var.get().strip()
        group_id = self.consumer_group_var.get().strip()
        
        if not topic:
            messagebox.showerror("Error", "Please select a topic")
            return
        
        if not group_id:
            messagebox.showerror("Error", "Please enter a consumer group ID")
            return
        
        # Start consumer
        consumer = self.producer_consumer_manager.get_consumer()
        success = consumer.start_consumer(topic, group_id)
        
        if success:
            self._set_status(f"Consumer started for topic '{topic}' in group '{group_id}'")
            self._update_consumer_status()
            
            # Start message polling
            self._start_message_polling()
        else:
            self._set_status("Failed to start consumer")
    
    def _stop_consumer(self) -> None:
        """
        Stop the consumer.
        """
        if not self.producer_consumer_manager:
            return
        
        consumer = self.producer_consumer_manager.get_consumer()
        success = consumer.stop_consumer()
        
        if success:
            self._set_status("Consumer stopped")
            self._update_consumer_status()
        else:
            self._set_status("Failed to stop consumer")
    
    def _toggle_auto_generate(self) -> None:
        """
        Toggle auto-generate messages setting.
        """
        if self.auto_generate_var.get():
            self._set_status("Auto-generate enabled - use Start Producer to begin")
        else:
            self._set_status("Auto-generate disabled")
            # Stop producer if running
            if self.producer_consumer_manager:
                producer = self.producer_consumer_manager.get_producer()
                if producer.is_producer_running():
                    producer.stop_producer()
                    self._update_producer_status()
    
    def _start_message_polling(self) -> None:
        """
        Start polling for messages from producer/consumer manager.
        """
        def poll_messages():
            try:
                if self.producer_consumer_manager:
                    messages = self.producer_consumer_manager.get_messages()
                    if messages:
                        for message in messages:
                            self._add_message_to_display(message)
                
                # Continue polling if consumer is running
                if (self.producer_consumer_manager and 
                    self.producer_consumer_manager.get_consumer().is_consumer_running()):
                    self.parent_frame.after(1000, poll_messages)  # Poll every second
                    
            except Exception as e:
                self.logger.error(f"Error polling messages: {e}")
        
        # Start polling
        poll_messages()
    
    def _add_message_to_display(self, message: str) -> None:
        """
        Add a message to the display area.
        
        Args:
            message (str): Message to display
        """
        try:
            self.messages_text.config(state=tk.NORMAL)
            self.messages_text.insert(tk.END, message + "\n")
            self.messages_text.see(tk.END)  # Auto-scroll to bottom
            self.messages_text.config(state=tk.DISABLED)
            
            # Update message count
            self.message_count += 1
            self.message_count_label.config(text=f"Messages: {self.message_count}")
            
        except Exception as e:
            self.logger.error(f"Error adding message to display: {e}")
    
    def _clear_messages(self) -> None:
        """
        Clear the messages display.
        """
        try:
            self.messages_text.config(state=tk.NORMAL)
            self.messages_text.delete(1.0, tk.END)
            self.messages_text.config(state=tk.DISABLED)
            
            # Reset message count
            self.message_count = 0
            self.message_count_label.config(text="Messages: 0")
            
            self._set_status("Messages cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing messages: {e}")
    
    def _update_producer_status(self) -> None:
        """
        Update the producer status display.
        """
        try:
            if self.producer_consumer_manager:
                producer = self.producer_consumer_manager.get_producer()
                if producer.is_producer_running():
                    self.producer_status_label.config(text="Producer: Running", foreground="green")
                else:
                    self.producer_status_label.config(text="Producer: Stopped", foreground="red")
            else:
                self.producer_status_label.config(text="Producer: Unknown", foreground="gray")
        except Exception as e:
            self.logger.error(f"Error updating producer status: {e}")
    
    def _update_consumer_status(self) -> None:
        """
        Update the consumer status display.
        """
        try:
            if self.producer_consumer_manager:
                consumer = self.producer_consumer_manager.get_consumer()
                if consumer.is_consumer_running():
                    self.consumer_status_label.config(text="Consumer: Running", foreground="green")
                else:
                    self.consumer_status_label.config(text="Consumer: Stopped", foreground="red")
            else:
                self.consumer_status_label.config(text="Consumer: Unknown", foreground="gray")
        except Exception as e:
            self.logger.error(f"Error updating consumer status: {e}")
    
    def _set_status(self, message: str) -> None:
        """
        Set the status message.
        
        Args:
            message (str): Status message
        """
        self.status_var.set(message)
    
    def _update_button_states(self) -> None:
        """
        Update the state of control buttons based on current status.
        """
        try:
            if not self.kafka_manager or not self.producer_consumer_manager:
                # No managers - disable all buttons
                buttons = [
                    self.send_message_button,
                    self.start_producer_button,
                    self.stop_producer_button,
                    self.start_consumer_button,
                    self.stop_consumer_button,
                    self.refresh_button
                ]
                
                for button in buttons:
                    if button:
                        button.config(state=tk.DISABLED)
                return
            
            # Check if server is running
            server_running = self.kafka_manager.is_server_running()
            
            # Enable/disable buttons based on server status
            button_state = tk.NORMAL if server_running else tk.DISABLED
            
            if self.send_message_button:
                self.send_message_button.config(state=button_state)
            if self.refresh_button:
                self.refresh_button.config(state=button_state)
            
            # Producer buttons
            producer = self.producer_consumer_manager.get_producer()
            producer_running = producer.is_producer_running()
            
            if self.start_producer_button:
                start_state = tk.NORMAL if (server_running and not producer_running) else tk.DISABLED
                self.start_producer_button.config(state=start_state)
            
            if self.stop_producer_button:
                stop_state = tk.NORMAL if (server_running and producer_running) else tk.DISABLED
                self.stop_producer_button.config(state=stop_state)
            
            # Consumer buttons
            consumer = self.producer_consumer_manager.get_consumer()
            consumer_running = consumer.is_consumer_running()
            
            if self.start_consumer_button:
                start_state = tk.NORMAL if (server_running and not consumer_running) else tk.DISABLED
                self.start_consumer_button.config(state=start_state)
            
            if self.stop_consumer_button:
                stop_state = tk.NORMAL if (server_running and consumer_running) else tk.DISABLED
                self.stop_consumer_button.config(state=stop_state)
                
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
        self.producer_consumer_manager = producer_consumer_manager
        
        # Update button states
        self._update_button_states()
        
        # Update status displays
        self._update_producer_status()
        self._update_consumer_status()
        
        # Auto-refresh data if server is running
        if kafka_manager and kafka_manager.is_server_running():
            self._refresh_data()
    
    def refresh(self) -> None:
        """
        Refresh the panel data.
        """
        self._refresh_data()
        self._update_producer_status()
        self._update_consumer_status()
    
    def get_selected_topic(self) -> Optional[str]:
        """
        Get the currently selected topic.
        
        Returns:
            Optional[str]: Selected topic or None
        """
        return self.topic_var.get().strip() or None
    
    def get_selected_consumer_group(self) -> Optional[str]:
        """
        Get the currently selected consumer group.
        
        Returns:
            Optional[str]: Selected consumer group or None
        """
        return self.consumer_group_var.get().strip() or None