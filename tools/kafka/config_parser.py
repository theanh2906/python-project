"""
Configuration Parser Module

This module handles parsing and managing Kafka server.properties configuration files.
It provides functionality to read, parse, validate, and display Kafka configuration settings.
"""

import configparser
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re


class KafkaConfigParser:
    """
    Parses and manages Kafka server.properties configuration files.
    
    This class provides methods for:
    - Reading and parsing server.properties files
    - Detecting Kafka mode (Zookeeper vs KRaft)
    - Extracting key configuration parameters
    - Validating configuration settings
    - Formatting configuration for display
    """
    
    def __init__(self, kafka_folder: str):
        """
        Initialize the configuration parser.
        
        Args:
            kafka_folder (str): Path to Kafka installation directory
        """
        self.kafka_folder = Path(kafka_folder)
        self.config_file = self.kafka_folder / "config" / "server.properties"
        self.config_data = {}
        self.is_kraft_mode = False
        self.raw_config = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.reload_config()
    
    def reload_config(self) -> Tuple[bool, str]:
        """
        Reload configuration from server.properties file.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.config_file.exists():
                error_msg = f"Configuration file not found: {self.config_file}"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Read raw file content for custom parsing
            with open(self.config_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Parse configuration
            self.config_data = self._parse_properties_file(raw_content)
            
            # Detect Kafka mode
            self._detect_kafka_mode()
            
            # Store raw config for reference
            self.raw_config = raw_content
            
            success_msg = f"Configuration loaded successfully from {self.config_file}"
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error loading configuration: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _parse_properties_file(self, content: str) -> Dict[str, str]:
        """
        Parse properties file content manually to handle Kafka-specific format.
        
        Args:
            content (str): Raw file content
        
        Returns:
            Dict[str, str]: Parsed configuration key-value pairs
        """
        config = {}
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Handle key=value pairs
            if '=' in line:
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove inline comments
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    config[key] = value
                    
                except ValueError:
                    self.logger.warning(f"Could not parse line {line_num}: {line}")
                    continue
        
        return config
    
    def _detect_kafka_mode(self) -> None:
        """
        Detect if Kafka is configured for KRaft mode or Zookeeper mode.
        """
        kraft_indicators = [
            'process.roles',
            'node.id',
            'controller.quorum.voters',
            'controller.listener.names'
        ]
        
        self.is_kraft_mode = any(key in self.config_data for key in kraft_indicators)
        
        mode = "KRaft" if self.is_kraft_mode else "Zookeeper"
        self.logger.info(f"Detected Kafka mode: {mode}")
    
    def get_kafka_mode(self) -> str:
        """
        Get the detected Kafka mode.
        
        Returns:
            str: "KRaft" or "Zookeeper"
        """
        return "KRaft" if self.is_kraft_mode else "Zookeeper"
    
    def get_all_config(self) -> Dict[str, str]:
        """
        Get all configuration key-value pairs.
        
        Returns:
            Dict[str, str]: All configuration settings
        """
        return self.config_data.copy()
    
    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific configuration value.
        
        Args:
            key (str): Configuration key
            default (Optional[str]): Default value if key not found
        
        Returns:
            Optional[str]: Configuration value or default
        """
        return self.config_data.get(key, default)
    
    def get_key_config_info(self) -> Dict[str, Any]:
        """
        Get key configuration information formatted for display.
        
        Returns:
            Dict[str, Any]: Key configuration information
        """
        info = {
            'kafka_mode': self.get_kafka_mode(),
            'config_file_path': str(self.config_file),
            'total_settings': len(self.config_data)
        }
        
        # Common settings
        common_keys = [
            'broker.id',
            'listeners',
            'advertised.listeners',
            'log.dirs',
            'num.network.threads',
            'num.io.threads',
            'socket.send.buffer.bytes',
            'socket.receive.buffer.bytes',
            'socket.request.max.bytes',
            'num.partitions',
            'num.recovery.threads.per.data.dir',
            'offsets.topic.replication.factor',
            'transaction.state.log.replication.factor',
            'transaction.state.log.min.isr',
            'log.retention.hours',
            'log.retention.bytes',
            'log.segment.bytes',
            'log.retention.check.interval.ms',
            'group.initial.rebalance.delay.ms'
        ]
        
        # Zookeeper-specific settings
        zookeeper_keys = [
            'zookeeper.connect',
            'zookeeper.connection.timeout.ms'
        ]
        
        # KRaft-specific settings
        kraft_keys = [
            'process.roles',
            'node.id',
            'controller.quorum.voters',
            'controller.listener.names',
            'log.dirs'
        ]
        
        # Extract common settings
        info['common_settings'] = {}
        for key in common_keys:
            value = self.get_config_value(key)
            if value is not None:
                info['common_settings'][key] = value
        
        # Extract mode-specific settings
        if self.is_kraft_mode:
            info['kraft_settings'] = {}
            for key in kraft_keys:
                value = self.get_config_value(key)
                if value is not None:
                    info['kraft_settings'][key] = value
        else:
            info['zookeeper_settings'] = {}
            for key in zookeeper_keys:
                value = self.get_config_value(key)
                if value is not None:
                    info['zookeeper_settings'][key] = value
        
        return info
    
    def get_formatted_config(self) -> str:
        """
        Get formatted configuration for display in text area.
        
        Returns:
            str: Formatted configuration text
        """
        if not self.config_data:
            return "No configuration loaded"
        
        lines = []
        lines.append(f"Kafka Configuration ({self.get_kafka_mode()} Mode)")
        lines.append("=" * 50)
        lines.append(f"Configuration File: {self.config_file}")
        lines.append(f"Total Settings: {len(self.config_data)}")
        lines.append("")
        
        # Get key info
        key_info = self.get_key_config_info()
        
        # Display common settings
        if 'common_settings' in key_info and key_info['common_settings']:
            lines.append("COMMON SETTINGS:")
            lines.append("-" * 20)
            for key, value in key_info['common_settings'].items():
                lines.append(f"{key} = {value}")
            lines.append("")
        
        # Display mode-specific settings
        if self.is_kraft_mode and 'kraft_settings' in key_info:
            lines.append("KRAFT MODE SETTINGS:")
            lines.append("-" * 20)
            for key, value in key_info['kraft_settings'].items():
                lines.append(f"{key} = {value}")
            lines.append("")
        elif not self.is_kraft_mode and 'zookeeper_settings' in key_info:
            lines.append("ZOOKEEPER MODE SETTINGS:")
            lines.append("-" * 25)
            for key, value in key_info['zookeeper_settings'].items():
                lines.append(f"{key} = {value}")
            lines.append("")
        
        # Display other settings
        displayed_keys = set()
        if 'common_settings' in key_info:
            displayed_keys.update(key_info['common_settings'].keys())
        if 'kraft_settings' in key_info:
            displayed_keys.update(key_info['kraft_settings'].keys())
        if 'zookeeper_settings' in key_info:
            displayed_keys.update(key_info['zookeeper_settings'].keys())
        
        other_settings = {k: v for k, v in self.config_data.items() if k not in displayed_keys}
        
        if other_settings:
            lines.append("OTHER SETTINGS:")
            lines.append("-" * 15)
            for key, value in sorted(other_settings.items()):
                lines.append(f"{key} = {value}")
        
        return "\n".join(lines)
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check for required settings
            if self.is_kraft_mode:
                required_kraft_keys = ['process.roles', 'node.id', 'log.dirs']
                for key in required_kraft_keys:
                    if not self.get_config_value(key):
                        issues.append(f"Missing required KRaft setting: {key}")
            else:
                required_zk_keys = ['broker.id', 'log.dirs', 'zookeeper.connect']
                for key in required_zk_keys:
                    if not self.get_config_value(key):
                        issues.append(f"Missing required Zookeeper setting: {key}")
            
            # Validate log.dirs
            log_dirs = self.get_config_value('log.dirs')
            if log_dirs:
                for log_dir in log_dirs.split(','):
                    log_dir = log_dir.strip()
                    if not os.path.exists(log_dir):
                        issues.append(f"Log directory does not exist: {log_dir}")
            
            # Validate numeric settings
            numeric_settings = {
                'broker.id': int,
                'node.id': int,
                'num.partitions': int,
                'num.network.threads': int,
                'num.io.threads': int,
                'log.retention.hours': int,
                'offsets.topic.replication.factor': int
            }
            
            for key, expected_type in numeric_settings.items():
                value = self.get_config_value(key)
                if value is not None:
                    try:
                        expected_type(value)
                    except ValueError:
                        issues.append(f"Invalid {expected_type.__name__} value for {key}: {value}")
            
            # Validate listeners format
            listeners = self.get_config_value('listeners')
            if listeners:
                listener_pattern = re.compile(r'^[A-Z_]+://[^:]+:\d+$')
                for listener in listeners.split(','):
                    listener = listener.strip()
                    if not listener_pattern.match(listener):
                        issues.append(f"Invalid listener format: {listener}")
            
            is_valid = len(issues) == 0
            
            if is_valid:
                self.logger.info("Configuration validation passed")
            else:
                self.logger.warning(f"Configuration validation found {len(issues)} issues")
            
            return is_valid, issues
            
        except Exception as e:
            error_msg = f"Error during configuration validation: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def get_bootstrap_servers(self) -> str:
        """
        Extract bootstrap servers from configuration.
        
        Returns:
            str: Bootstrap servers string
        """
        # Try to get from listeners first
        listeners = self.get_config_value('listeners')
        if listeners:
            # Parse listeners to extract bootstrap servers
            bootstrap_list = []
            for listener in listeners.split(','):
                listener = listener.strip()
                if '://' in listener:
                    # Extract host:port from protocol://host:port
                    host_port = listener.split('://', 1)[1]
                    bootstrap_list.append(host_port)
            
            if bootstrap_list:
                return ','.join(bootstrap_list)
        
        # Try advertised.listeners
        advertised = self.get_config_value('advertised.listeners')
        if advertised:
            bootstrap_list = []
            for listener in advertised.split(','):
                listener = listener.strip()
                if '://' in listener:
                    host_port = listener.split('://', 1)[1]
                    bootstrap_list.append(host_port)
            
            if bootstrap_list:
                return ','.join(bootstrap_list)
        
        # Default fallback
        return "localhost:9092"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the configuration for quick overview.
        
        Returns:
            Dict[str, Any]: Configuration summary
        """
        summary = {
            'kafka_mode': self.get_kafka_mode(),
            'config_file': str(self.config_file),
            'config_exists': self.config_file.exists(),
            'total_settings': len(self.config_data),
            'bootstrap_servers': self.get_bootstrap_servers()
        }
        
        # Add key settings
        key_settings = [
            'broker.id', 'node.id', 'log.dirs', 'num.partitions',
            'log.retention.hours', 'zookeeper.connect', 'process.roles'
        ]
        
        summary['key_settings'] = {}
        for key in key_settings:
            value = self.get_config_value(key)
            if value is not None:
                summary['key_settings'][key] = value
        
        # Validation status
        is_valid, issues = self.validate_config()
        summary['is_valid'] = is_valid
        summary['validation_issues'] = issues
        
        return summary
    
    def search_config(self, search_term: str) -> Dict[str, str]:
        """
        Search for configuration keys or values containing the search term.
        
        Args:
            search_term (str): Term to search for
        
        Returns:
            Dict[str, str]: Matching configuration entries
        """
        if not search_term:
            return {}
        
        search_term = search_term.lower()
        matches = {}
        
        for key, value in self.config_data.items():
            if (search_term in key.lower() or 
                search_term in value.lower()):
                matches[key] = value
        
        return matches
    
    def get_raw_config(self) -> str:
        """
        Get the raw configuration file content.
        
        Returns:
            str: Raw configuration content
        """
        return self.raw_config or ""
    
    def backup_config(self, backup_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a backup of the current configuration file.
        
        Args:
            backup_path (Optional[str]): Custom backup path
        
        Returns:
            Tuple[bool, str]: (success, backup_file_path_or_error_message)
        """
        try:
            if not self.config_file.exists():
                return False, "Configuration file does not exist"
            
            if backup_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config_file}.backup_{timestamp}"
            
            backup_file = Path(backup_path)
            
            # Copy configuration file
            import shutil
            shutil.copy2(self.config_file, backup_file)
            
            success_msg = f"Configuration backed up to: {backup_file}"
            self.logger.info(success_msg)
            return True, str(backup_file)
            
        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg