"""
Producer Consumer Module

This module handles Kafka producer and consumer simulation with real-time message handling.
It provides classes for simulating producers and consumers with threading support to prevent GUI freezing.
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError
import queue


class KafkaProducerSimulator:
    """
    Simulates a Kafka producer with support for manual and automated message sending.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the producer simulator.
        
        Args:
            bootstrap_servers (str): Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.is_running = False
        self.auto_generate = False
        self.auto_interval = 5  # seconds
        self.producer_thread = None
        self.message_callback = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize producer
        self._init_producer()
    
    def _init_producer(self) -> None:
        """
        Initialize Kafka producer with configuration.
        """
        try:
            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'client.id': 'kafka-tool-producer',
                'acks': 'all',
                'retries': 3,
                'retry.backoff.ms': 100,
                'delivery.timeout.ms': 30000
            }
            self.producer = Producer(conf)
            self.logger.info("Kafka Producer initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka Producer: {e}")
            self.producer = None
    
    def set_message_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for message updates.
        
        Args:
            callback: Function to call with message updates
        """
        self.message_callback = callback
    
    def _log_message(self, message: str) -> None:
        """
        Log message and call callback if set.
        
        Args:
            message (str): Message to log
        """
        self.logger.info(message)
        if self.message_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] PRODUCER: {message}"
            self.message_callback(formatted_message)
    
    def _delivery_callback(self, err, msg):
        """
        Callback for message delivery confirmation.
        
        Args:
            err: Error if delivery failed
            msg: Message object
        """
        if err is not None:
            error_msg = f"Message delivery failed: {err}"
            self._log_message(error_msg)
        else:
            success_msg = f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            self._log_message(success_msg)
    
    def send_message(self, topic: str, message: str, key: Optional[str] = None) -> bool:
        """
        Send a single message to the specified topic.
        
        Args:
            topic (str): Target topic
            message (str): Message content
            key (Optional[str]): Message key
        
        Returns:
            bool: True if message was queued successfully
        """
        try:
            if not self.producer:
                self._log_message("Producer not initialized")
                return False
            
            # Prepare message
            message_value = message.encode('utf-8')
            message_key = key.encode('utf-8') if key else None
            
            # Send message
            self.producer.produce(
                topic=topic,
                value=message_value,
                key=message_key,
                callback=self._delivery_callback
            )
            
            # Trigger delivery
            self.producer.poll(0)
            
            self._log_message(f"Message queued for topic '{topic}': {message[:100]}...")
            return True
            
        except KafkaException as e:
            error_msg = f"Kafka error sending message: {str(e)}"
            self._log_message(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            self._log_message(error_msg)
            return False
    
    def start_auto_producer(self, topic: str, interval: int = 5) -> bool:
        """
        Start automatic message generation.
        
        Args:
            topic (str): Target topic
            interval (int): Interval between messages in seconds
        
        Returns:
            bool: True if started successfully
        """
        try:
            if self.is_running:
                self._log_message("Auto producer is already running")
                return False
            
            if not self.producer:
                self._log_message("Producer not initialized")
                return False
            
            self.is_running = True
            self.auto_generate = True
            self.auto_interval = interval
            
            # Start producer thread
            self.producer_thread = threading.Thread(
                target=self._auto_producer_worker,
                args=(topic,),
                daemon=True
            )
            self.producer_thread.start()
            
            self._log_message(f"Auto producer started for topic '{topic}' with {interval}s interval")
            return True
            
        except Exception as e:
            error_msg = f"Error starting auto producer: {str(e)}"
            self._log_message(error_msg)
            return False
    
    def stop_producer(self) -> bool:
        """
        Stop the producer (both manual and auto modes).
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            self.is_running = False
            self.auto_generate = False
            
            # Wait for thread to finish
            if self.producer_thread and self.producer_thread.is_alive():
                self.producer_thread.join(timeout=5)
            
            # Flush remaining messages
            if self.producer:
                self.producer.flush(timeout=10)
            
            self._log_message("Producer stopped")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping producer: {str(e)}"
            self._log_message(error_msg)
            return False
    
    def _auto_producer_worker(self, topic: str) -> None:
        """
        Worker thread for automatic message generation.
        
        Args:
            topic (str): Target topic
        """
        message_count = 0
        
        while self.is_running and self.auto_generate:
            try:
                # Generate sample message
                message_count += 1
                timestamp = datetime.now().isoformat()
                message_data = {
                    "id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "message_number": message_count,
                    "data": f"Auto-generated message #{message_count}",
                    "source": "kafka-tool-simulator"
                }
                
                message_json = json.dumps(message_data, indent=2)
                
                # Send message
                self.send_message(topic, message_json, key=f"auto-{message_count}")
                
                # Wait for next interval
                time.sleep(self.auto_interval)
                
            except Exception as e:
                error_msg = f"Error in auto producer worker: {str(e)}"
                self._log_message(error_msg)
                time.sleep(1)  # Brief pause before retrying
    
    def is_producer_running(self) -> bool:
        """
        Check if producer is currently running.
        
        Returns:
            bool: True if producer is running
        """
        return self.is_running


class KafkaConsumerSimulator:
    """
    Simulates a Kafka consumer with real-time message consumption.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the consumer simulator.
        
        Args:
            bootstrap_servers (str): Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.is_running = False
        self.consumer_thread = None
        self.message_callback = None
        self.current_topic = None
        self.current_group_id = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def set_message_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for message updates.
        
        Args:
            callback: Function to call with message updates
        """
        self.message_callback = callback
    
    def _log_message(self, message: str) -> None:
        """
        Log message and call callback if set.
        
        Args:
            message (str): Message to log
        """
        self.logger.info(message)
        if self.message_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] CONSUMER: {message}"
            self.message_callback(formatted_message)
    
    def _init_consumer(self, group_id: str) -> bool:
        """
        Initialize Kafka consumer with configuration.
        
        Args:
            group_id (str): Consumer group ID
        
        Returns:
            bool: True if initialized successfully
        """
        try:
            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': group_id,
                'client.id': 'kafka-tool-consumer',
                'auto.offset.reset': 'latest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 1000,
                'session.timeout.ms': 30000,
                'heartbeat.interval.ms': 10000
            }
            self.consumer = Consumer(conf)
            self.logger.info(f"Kafka Consumer initialized for group '{group_id}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka Consumer: {e}")
            self.consumer = None
            return False
    
    def start_consumer(self, topic: str, group_id: str) -> bool:
        """
        Start consuming messages from the specified topic.
        
        Args:
            topic (str): Topic to consume from
            group_id (str): Consumer group ID
        
        Returns:
            bool: True if started successfully
        """
        try:
            if self.is_running:
                self._log_message("Consumer is already running")
                return False
            
            # Initialize consumer
            if not self._init_consumer(group_id):
                self._log_message("Failed to initialize consumer")
                return False
            
            self.current_topic = topic
            self.current_group_id = group_id
            self.is_running = True
            
            # Subscribe to topic
            self.consumer.subscribe([topic])
            
            # Start consumer thread
            self.consumer_thread = threading.Thread(
                target=self._consumer_worker,
                daemon=True
            )
            self.consumer_thread.start()
            
            self._log_message(f"Consumer started for topic '{topic}' in group '{group_id}'")
            return True
            
        except Exception as e:
            error_msg = f"Error starting consumer: {str(e)}"
            self._log_message(error_msg)
            return False
    
    def stop_consumer(self) -> bool:
        """
        Stop the consumer.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            self.is_running = False
            
            # Close consumer
            if self.consumer:
                self.consumer.close()
                self.consumer = None
            
            # Wait for thread to finish
            if self.consumer_thread and self.consumer_thread.is_alive():
                self.consumer_thread.join(timeout=5)
            
            self._log_message("Consumer stopped")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping consumer: {str(e)}"
            self._log_message(error_msg)
            return False
    
    def _consumer_worker(self) -> None:
        """
        Worker thread for message consumption.
        """
        message_count = 0
        
        while self.is_running:
            try:
                if not self.consumer:
                    break
                
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition - not an error
                        continue
                    else:
                        error_msg = f"Consumer error: {msg.error()}"
                        self._log_message(error_msg)
                        continue
                
                # Process message
                message_count += 1
                
                # Decode message
                key = msg.key().decode('utf-8') if msg.key() else None
                value = msg.value().decode('utf-8') if msg.value() else None
                
                # Format message info
                message_info = (
                    f"Message #{message_count} received from topic '{msg.topic()}' "
                    f"[partition: {msg.partition()}, offset: {msg.offset()}]"
                )
                
                if key:
                    message_info += f"\nKey: {key}"
                
                if value:
                    # Try to format JSON for better readability
                    try:
                        parsed_json = json.loads(value)
                        formatted_value = json.dumps(parsed_json, indent=2)
                        message_info += f"\nValue:\n{formatted_value}"
                    except json.JSONDecodeError:
                        # Not JSON, display as plain text
                        message_info += f"\nValue: {value}"
                
                self._log_message(message_info)
                
            except Exception as e:
                if self.is_running:  # Only log if we're still supposed to be running
                    error_msg = f"Error in consumer worker: {str(e)}"
                    self._log_message(error_msg)
                    time.sleep(1)  # Brief pause before retrying
    
    def is_consumer_running(self) -> bool:
        """
        Check if consumer is currently running.
        
        Returns:
            bool: True if consumer is running
        """
        return self.is_running
    
    def get_consumer_info(self) -> Dict[str, Any]:
        """
        Get current consumer information.
        
        Returns:
            Dict[str, Any]: Consumer information
        """
        return {
            'is_running': self.is_running,
            'topic': self.current_topic,
            'group_id': self.current_group_id,
            'bootstrap_servers': self.bootstrap_servers
        }


class ProducerConsumerManager:
    """
    Manages both producer and consumer simulators.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the manager.
        
        Args:
            bootstrap_servers (str): Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducerSimulator(bootstrap_servers)
        self.consumer = KafkaConsumerSimulator(bootstrap_servers)
        self.message_queue = queue.Queue()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set callbacks to collect messages
        self.producer.set_message_callback(self._add_message_to_queue)
        self.consumer.set_message_callback(self._add_message_to_queue)
    
    def _add_message_to_queue(self, message: str) -> None:
        """
        Add message to the queue for GUI consumption.
        
        Args:
            message (str): Message to add
        """
        try:
            self.message_queue.put_nowait(message)
        except queue.Full:
            # Queue is full, remove oldest message and add new one
            try:
                self.message_queue.get_nowait()
                self.message_queue.put_nowait(message)
            except queue.Empty:
                pass
    
    def get_messages(self) -> List[str]:
        """
        Get all pending messages from the queue.
        
        Returns:
            List[str]: List of messages
        """
        messages = []
        try:
            while True:
                message = self.message_queue.get_nowait()
                messages.append(message)
        except queue.Empty:
            pass
        return messages
    
    def get_producer(self) -> KafkaProducerSimulator:
        """
        Get the producer simulator.
        
        Returns:
            KafkaProducerSimulator: Producer instance
        """
        return self.producer
    
    def get_consumer(self) -> KafkaConsumerSimulator:
        """
        Get the consumer simulator.
        
        Returns:
            KafkaConsumerSimulator: Consumer instance
        """
        return self.consumer
    
    def stop_all(self) -> None:
        """
        Stop both producer and consumer.
        """
        try:
            self.producer.stop_producer()
            self.consumer.stop_consumer()
            self.logger.info("All producer/consumer operations stopped")
        except Exception as e:
            self.logger.error(f"Error stopping producer/consumer: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of both producer and consumer.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'producer_running': self.producer.is_producer_running(),
            'consumer_running': self.consumer.is_consumer_running(),
            'consumer_info': self.consumer.get_consumer_info(),
            'bootstrap_servers': self.bootstrap_servers
        }