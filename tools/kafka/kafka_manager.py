"""
Kafka Manager Module

This module handles Kafka server operations, topic management, and consumer group management.
It provides a KafkaManager class that interfaces with Kafka using the Confluent Kafka Python library.
"""

import os
import subprocess
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource
from confluent_kafka import KafkaException, KafkaError
import configparser


class KafkaManager:
    """
    Manages Kafka server operations, topics, and consumer groups.
    
    This class provides methods for:
    - Starting and stopping Kafka server
    - Managing topics (create, delete, list)
    - Managing consumer groups (create, delete, list)
    - Checking server status
    """
    
    def __init__(self, kafka_folder: str, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize KafkaManager with Kafka installation folder and bootstrap servers.
        
        Args:
            kafka_folder (str): Path to Kafka installation directory
            bootstrap_servers (str): Kafka bootstrap servers (default: localhost:9092)
        """
        self.kafka_folder = Path(kafka_folder)
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = None
        self.server_process = None
        self.is_kraft_mode = False
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate Kafka folder
        self._validate_kafka_folder()
        
        # Detect Kafka mode (Zookeeper vs KRaft)
        self._detect_kafka_mode()
        
        # Initialize admin client
        self._init_admin_client()
    
    def _validate_kafka_folder(self) -> None:
        """
        Validate that the Kafka folder contains required files.
        
        Raises:
            FileNotFoundError: If required Kafka files are not found
        """
        required_files = [
            "bin/windows/kafka-server-start.bat",
            "bin/windows/kafka-server-stop.bat",
            "config/server.properties"
        ]
        
        for file_path in required_files:
            full_path = self.kafka_folder / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"Required Kafka file not found: {full_path}")
        
        self.logger.info(f"Kafka folder validation successful: {self.kafka_folder}")
    
    def _detect_kafka_mode(self) -> None:
        """
        Detect if Kafka is running in KRaft mode or Zookeeper mode.
        """
        try:
            config_path = self.kafka_folder / "config" / "server.properties"
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Check for KRaft-specific configurations
            kraft_indicators = [
                'process.roles',
                'node.id',
                'controller.quorum.voters'
            ]
            
            for section in config.sections():
                for key, _ in config.items(section):
                    if key in kraft_indicators:
                        self.is_kraft_mode = True
                        break
                if self.is_kraft_mode:
                    break
            
            # Also check in DEFAULT section
            if not self.is_kraft_mode:
                for key in kraft_indicators:
                    if key in config['DEFAULT']:
                        self.is_kraft_mode = True
                        break
            
            mode = "KRaft" if self.is_kraft_mode else "Zookeeper"
            self.logger.info(f"Detected Kafka mode: {mode}")
            
        except Exception as e:
            self.logger.warning(f"Could not detect Kafka mode: {e}. Assuming Zookeeper mode.")
            self.is_kraft_mode = False
    
    def _init_admin_client(self) -> None:
        """
        Initialize Kafka Admin Client for topic and consumer group operations.
        """
        try:
            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'client.id': 'kafka-tool-admin'
            }
            self.admin_client = AdminClient(conf)
            self.logger.info("Kafka Admin Client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka Admin Client: {e}")
            self.admin_client = None
    
    def start_server(self) -> Tuple[bool, str]:
        """
        Start the Kafka server.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if self.is_server_running():
                return False, "Kafka server is already running"
            
            # Prepare start command
            start_script = self.kafka_folder / "bin" / "windows" / "kafka-server-start.bat"
            config_file = self.kafka_folder / "config" / "server.properties"
            
            cmd = [str(start_script), str(config_file)]
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(self.kafka_folder),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if server started successfully
            if self.is_server_running():
                self.logger.info("Kafka server started successfully")
                return True, "Kafka server started successfully"
            else:
                return False, "Failed to start Kafka server"
                
        except Exception as e:
            error_msg = f"Error starting Kafka server: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def stop_server(self) -> Tuple[bool, str]:
        """
        Stop the Kafka server.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_server_running():
                return False, "Kafka server is not running"
            
            # Prepare stop command
            stop_script = self.kafka_folder / "bin" / "windows" / "kafka-server-stop.bat"
            
            # Execute stop command
            result = subprocess.run(
                [str(stop_script)],
                cwd=str(self.kafka_folder),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Terminate server process if it exists
            if self.server_process:
                try:
                    self.server_process.terminate()
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                finally:
                    self.server_process = None
            
            # Wait a moment for server to stop
            time.sleep(2)
            
            if not self.is_server_running():
                self.logger.info("Kafka server stopped successfully")
                return True, "Kafka server stopped successfully"
            else:
                return False, "Failed to stop Kafka server completely"
                
        except subprocess.TimeoutExpired:
            error_msg = "Timeout while stopping Kafka server"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error stopping Kafka server: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def is_server_running(self) -> bool:
        """
        Check if Kafka server is running by attempting to connect.
        
        Returns:
            bool: True if server is running, False otherwise
        """
        try:
            if not self.admin_client:
                return False
            
            # Try to get cluster metadata with a short timeout
            metadata = self.admin_client.list_topics(timeout=5)
            return True
            
        except KafkaException as e:
            if e.args[0].code() == KafkaError._TIMED_OUT:
                return False
            return False
        except Exception:
            return False
    
    def get_server_status(self) -> str:
        """
        Get current server status as a string.
        
        Returns:
            str: Server status ("Running" or "Stopped")
        """
        return "Running" if self.is_server_running() else "Stopped"
    
    def list_topics(self) -> Tuple[bool, List[str], str]:
        """
        List all topics in the Kafka cluster.
        
        Returns:
            Tuple[bool, List[str], str]: (success, topics_list, message)
        """
        try:
            if not self.admin_client:
                return False, [], "Admin client not initialized"
            
            if not self.is_server_running():
                return False, [], "Kafka server is not running"
            
            metadata = self.admin_client.list_topics(timeout=10)
            topics = list(metadata.topics.keys())
            
            # Filter out internal topics
            user_topics = [topic for topic in topics if not topic.startswith('__')]
            
            self.logger.info(f"Retrieved {len(user_topics)} topics")
            return True, user_topics, f"Found {len(user_topics)} topics"
            
        except KafkaException as e:
            error_msg = f"Kafka error listing topics: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Error listing topics: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
    
    def create_topic(self, topic_name: str, num_partitions: int = 1, replication_factor: int = 1) -> Tuple[bool, str]:
        """
        Create a new Kafka topic.
        
        Args:
            topic_name (str): Name of the topic to create
            num_partitions (int): Number of partitions (default: 1)
            replication_factor (int): Replication factor (default: 1)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.admin_client:
                return False, "Admin client not initialized"
            
            if not self.is_server_running():
                return False, "Kafka server is not running"
            
            # Validate topic name
            if not topic_name or not topic_name.strip():
                return False, "Topic name cannot be empty"
            
            # Create topic
            new_topic = NewTopic(
                topic=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            
            # Execute topic creation
            futures = self.admin_client.create_topics([new_topic], validate_only=False)
            
            # Wait for operation to complete
            for topic, future in futures.items():
                try:
                    future.result(timeout=10)
                    success_msg = f"Topic '{topic_name}' created successfully"
                    self.logger.info(success_msg)
                    return True, success_msg
                except KafkaException as e:
                    if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                        error_msg = f"Topic '{topic_name}' already exists"
                    else:
                        error_msg = f"Failed to create topic '{topic_name}': {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
            
        except Exception as e:
            error_msg = f"Error creating topic '{topic_name}': {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def delete_topic(self, topic_name: str) -> Tuple[bool, str]:
        """
        Delete a Kafka topic.
        
        Args:
            topic_name (str): Name of the topic to delete
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.admin_client:
                return False, "Admin client not initialized"
            
            if not self.is_server_running():
                return False, "Kafka server is not running"
            
            if not topic_name or not topic_name.strip():
                return False, "Topic name cannot be empty"
            
            # Execute topic deletion
            futures = self.admin_client.delete_topics([topic_name])
            
            # Wait for operation to complete
            for topic, future in futures.items():
                try:
                    future.result(timeout=10)
                    success_msg = f"Topic '{topic_name}' deleted successfully"
                    self.logger.info(success_msg)
                    return True, success_msg
                except KafkaException as e:
                    if e.args[0].code() == KafkaError.UNKNOWN_TOPIC_OR_PARTITION:
                        error_msg = f"Topic '{topic_name}' does not exist"
                    else:
                        error_msg = f"Failed to delete topic '{topic_name}': {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
            
        except Exception as e:
            error_msg = f"Error deleting topic '{topic_name}': {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def list_consumer_groups(self) -> Tuple[bool, List[str], str]:
        """
        List all consumer groups in the Kafka cluster.
        
        Returns:
            Tuple[bool, List[str], str]: (success, groups_list, message)
        """
        try:
            if not self.admin_client:
                return False, [], "Admin client not initialized"
            
            if not self.is_server_running():
                return False, [], "Kafka server is not running"
            
            # List consumer groups
            result = self.admin_client.list_consumer_groups(timeout=10)
            groups = [group.group_id for group in result.valid]
            
            self.logger.info(f"Retrieved {len(groups)} consumer groups")
            return True, groups, f"Found {len(groups)} consumer groups"
            
        except KafkaException as e:
            error_msg = f"Kafka error listing consumer groups: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Error listing consumer groups: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
    
    def delete_consumer_group(self, group_id: str) -> Tuple[bool, str]:
        """
        Delete a consumer group.
        
        Args:
            group_id (str): ID of the consumer group to delete
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.admin_client:
                return False, "Admin client not initialized"
            
            if not self.is_server_running():
                return False, "Kafka server is not running"
            
            if not group_id or not group_id.strip():
                return False, "Consumer group ID cannot be empty"
            
            # Execute consumer group deletion
            futures = self.admin_client.delete_consumer_groups([group_id])
            
            # Wait for operation to complete
            for group, future in futures.items():
                try:
                    future.result(timeout=10)
                    success_msg = f"Consumer group '{group_id}' deleted successfully"
                    self.logger.info(success_msg)
                    return True, success_msg
                except KafkaException as e:
                    error_msg = f"Failed to delete consumer group '{group_id}': {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
            
        except Exception as e:
            error_msg = f"Error deleting consumer group '{group_id}': {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_cluster_info(self) -> Dict[str, any]:
        """
        Get basic cluster information.
        
        Returns:
            Dict[str, any]: Cluster information
        """
        info = {
            'kafka_folder': str(self.kafka_folder),
            'bootstrap_servers': self.bootstrap_servers,
            'kafka_mode': 'KRaft' if self.is_kraft_mode else 'Zookeeper',
            'server_status': self.get_server_status(),
            'admin_client_ready': self.admin_client is not None
        }
        
        if self.is_server_running():
            try:
                success, topics, _ = self.list_topics()
                info['topic_count'] = len(topics) if success else 0
                
                success, groups, _ = self.list_consumer_groups()
                info['consumer_group_count'] = len(groups) if success else 0
            except:
                info['topic_count'] = 0
                info['consumer_group_count'] = 0
        else:
            info['topic_count'] = 0
            info['consumer_group_count'] = 0
        
        return info