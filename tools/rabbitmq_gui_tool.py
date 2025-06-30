from tkinter import messagebox

import customtkinter as ctk
import pika


class RabbitMQTestTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RabbitMQ Test Tool")
        self.geometry("400x400")
        self.connection = None
        self.channel = None
        self._build_gui()

    def _build_gui(self):
        # Create a main frame with two columns
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Host
        self.host_label = ctk.CTkLabel(main_frame, text="Host:")
        self.host_label.grid(row=0, column=0, sticky="e", pady=(20, 0), padx=(0, 5))
        self.host_entry = ctk.CTkEntry(main_frame)
        self.host_entry.insert(0, "localhost")
        self.host_entry.grid(row=0, column=1, sticky="w", pady=(20, 0))
        # Port
        self.port_label = ctk.CTkLabel(main_frame, text="Port:")
        self.port_label.grid(row=1, column=0, sticky="e", padx=(0, 5))
        self.port_entry = ctk.CTkEntry(main_frame)
        self.port_entry.insert(0, "5672")
        self.port_entry.grid(row=1, column=1, sticky="w")
        # Username
        self.user_label = ctk.CTkLabel(main_frame, text="Username:")
        self.user_label.grid(row=2, column=0, sticky="e", padx=(0, 5))
        self.user_entry = ctk.CTkEntry(main_frame)
        self.user_entry.insert(0, "guest")
        self.user_entry.grid(row=2, column=1, sticky="w")
        # Password
        self.pass_label = ctk.CTkLabel(main_frame, text="Password:")
        self.pass_label.grid(row=3, column=0, sticky="e", padx=(0, 5))
        self.pass_entry = ctk.CTkEntry(main_frame, show="*")
        self.pass_entry.insert(0, "guest")
        self.pass_entry.grid(row=3, column=1, sticky="w")
        # Queue
        self.queue_label = ctk.CTkLabel(main_frame, text="Queue Name:")
        self.queue_label.grid(row=4, column=0, sticky="e", padx=(0, 5))
        self.queue_entry = ctk.CTkEntry(main_frame)
        self.queue_entry.insert(0, "test_queue")
        self.queue_entry.grid(row=4, column=1, sticky="w")
        # Connect Button
        self.connect_btn = ctk.CTkButton(main_frame, text="Connect", command=self.connect_rabbitmq)
        self.connect_btn.grid(row=5, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        # Send Message
        self.send_btn = ctk.CTkButton(main_frame, text="Send Test Message", command=self.send_message, state="disabled")
        self.send_btn.grid(row=6, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        # Receive Message
        self.recv_btn = ctk.CTkButton(main_frame, text="Receive Message", command=self.receive_message, state="disabled")
        self.recv_btn.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="Status: Not connected")
        self.status_label.grid(row=8, column=0, columnspan=2, pady=(20, 0), sticky="ew")

    def connect_rabbitmq(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        user = self.user_entry.get()
        password = self.pass_entry.get()
        queue = self.queue_entry.get()
        try:
            credentials = pika.PlainCredentials(user, password)
            params = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=queue, durable=True)
            self.status_label.configure(text="Status: Connected")
            self.send_btn.configure(state="normal")
            self.recv_btn.configure(state="normal")
        except Exception as e:
            self.status_label.configure(text=f"Status: Connection failed")
            messagebox.showerror("Connection Error", str(e))

    def send_message(self):
        queue = self.queue_entry.get()
        try:
            self.channel.basic_publish(exchange='', routing_key=queue, body='Test Message')
            self.status_label.configure(text="Status: Message sent")
        except Exception as e:
            self.status_label.configure(text="Status: Send failed")
            messagebox.showerror("Send Error", str(e))

    def receive_message(self):
        queue = self.queue_entry.get()
        try:
            method_frame, header_frame, body = self.channel.basic_get(queue=queue, auto_ack=True)
            if method_frame:
                self.status_label.configure(text=f"Received: {body.decode()}")
            else:
                self.status_label.configure(text="No message in queue")
        except Exception as e:
            self.status_label.configure(text="Status: Receive failed")
            messagebox.showerror("Receive Error", str(e))

if __name__ == "__main__":
    app = RabbitMQTestTool()
    app.mainloop()

