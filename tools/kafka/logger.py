"""
Logger Module

This module provides custom logging setup for the Kafka Tool application.
It handles both console and file logging with proper formatting and rotation.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import queue
import threading


class KafkaToolLogger:
    """
    Custom logger for the Kafka Tool application.
    
    Provides:
    - Console logging with colored output
    - File logging with rotation
    - Real-time log capture for GUI display
    - Thread-safe logging operations
    """
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize the logger.
        
        Args:
            log_dir (str): Directory for log files
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_queue = queue.Queue(maxsize=1000)
        self.gui_handlers = []
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """
        Set up logging configuration with console and file handlers.
        """
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = self.log_dir / "kafka_tool.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Queue handler for GUI
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setLevel(self.log_level)
        queue_handler.setFormatter(file_formatter)
        root_logger.addHandler(queue_handler)
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info(f"Kafka Tool Logger initialized - Level: {logging.getLevelName(self.log_level)}")
        logger.info(f"Log directory: {self.log_dir.absolute()}")
    
    def get_log_messages(self, max_messages: int = 100) -> list:
        """
        Get recent log messages for GUI display.
        
        Args:
            max_messages (int): Maximum number of messages to return
        
        Returns:
            list: List of formatted log messages
        """
        messages = []
        try:
            while len(messages) < max_messages:
                try:
                    record = self.log_queue.get_nowait()
                    formatted_message = self._format_for_gui(record)
                    messages.append(formatted_message)
                except queue.Empty:
                    break
        except Exception as e:
            # Fallback message if there's an error
            messages.append(f"[ERROR] Failed to retrieve log messages: {e}")
        
        return messages
    
    def _format_for_gui(self, record: logging.LogRecord) -> str:
        """
        Format log record for GUI display.
        
        Args:
            record (logging.LogRecord): Log record to format
        
        Returns:
            str: Formatted message
        """
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname
        name = record.name.split('.')[-1]  # Get just the module name
        message = record.getMessage()
        
        return f"[{timestamp}] {level:8} {name:15} | {message}"
    
    def add_gui_handler(self, callback_func) -> None:
        """
        Add a GUI callback handler for real-time log updates.
        
        Args:
            callback_func: Function to call with new log messages
        """
        self.gui_handlers.append(callback_func)
    
    def remove_gui_handler(self, callback_func) -> None:
        """
        Remove a GUI callback handler.
        
        Args:
            callback_func: Function to remove
        """
        if callback_func in self.gui_handlers:
            self.gui_handlers.remove(callback_func)
    
    def set_log_level(self, level: str) -> None:
        """
        Change the logging level.
        
        Args:
            level (str): New logging level
        """
        try:
            new_level = getattr(logging, level.upper(), logging.INFO)
            self.log_level = new_level
            
            # Update all handlers
            root_logger = logging.getLogger()
            root_logger.setLevel(new_level)
            
            for handler in root_logger.handlers:
                handler.setLevel(new_level)
            
            logger = logging.getLogger(__name__)
            logger.info(f"Log level changed to: {level.upper()}")
            
        except AttributeError:
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid log level: {level}")
    
    def export_logs(self, export_path: Optional[str] = None) -> tuple:
        """
        Export current log file to a specified location.
        
        Args:
            export_path (Optional[str]): Path to export logs to
        
        Returns:
            tuple: (success, message)
        """
        try:
            log_file = self.log_dir / "kafka_tool.log"
            
            if not log_file.exists():
                return False, "Log file does not exist"
            
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"kafka_tool_logs_{timestamp}.log"
            
            export_file = Path(export_path)
            
            # Copy log file
            import shutil
            shutil.copy2(log_file, export_file)
            
            success_msg = f"Logs exported to: {export_file.absolute()}"
            logger = logging.getLogger(__name__)
            logger.info(success_msg)
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error exporting logs: {str(e)}"
            logger = logging.getLogger(__name__)
            logger.error(error_msg)
            return False, error_msg
    
    def clear_logs(self) -> tuple:
        """
        Clear the current log file.
        
        Returns:
            tuple: (success, message)
        """
        try:
            log_file = self.log_dir / "kafka_tool.log"
            
            if log_file.exists():
                # Truncate the log file
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("")
            
            # Clear the queue
            while not self.log_queue.empty():
                try:
                    self.log_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger = logging.getLogger(__name__)
            logger.info("Log file cleared")
            
            return True, "Logs cleared successfully"
            
        except Exception as e:
            error_msg = f"Error clearing logs: {str(e)}"
            logger = logging.getLogger(__name__)
            logger.error(error_msg)
            return False, error_msg
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the log files.
        
        Returns:
            Dict[str, Any]: Log statistics
        """
        stats = {
            'log_directory': str(self.log_dir.absolute()),
            'current_level': logging.getLevelName(self.log_level),
            'queue_size': self.log_queue.qsize(),
            'gui_handlers': len(self.gui_handlers)
        }
        
        # Get log file info
        log_file = self.log_dir / "kafka_tool.log"
        if log_file.exists():
            stat = log_file.stat()
            stats['log_file_size'] = stat.st_size
            stats['log_file_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        else:
            stats['log_file_size'] = 0
            stats['log_file_modified'] = None
        
        # Count backup files
        backup_files = list(self.log_dir.glob("kafka_tool.log.*"))
        stats['backup_files'] = len(backup_files)
        
        return stats


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """
        Format the log record with colors.
        
        Args:
            record: Log record to format
        
        Returns:
            str: Formatted and colored log message
        """
        # Get the original formatted message
        formatted = super().format(record)
        
        # Add colors if we're on a terminal that supports them
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            level_name = record.levelname
            color = self.COLORS.get(level_name, '')
            reset = self.COLORS['RESET']
            
            # Color the level name
            formatted = formatted.replace(
                level_name,
                f"{color}{level_name}{reset}"
            )
        
        return formatted


class QueueHandler(logging.Handler):
    """
    Custom handler that puts log records into a queue for GUI consumption.
    """
    
    def __init__(self, log_queue: queue.Queue):
        """
        Initialize the queue handler.
        
        Args:
            log_queue (queue.Queue): Queue to put log records into
        """
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        """
        Emit a log record by putting it in the queue.
        
        Args:
            record: Log record to emit
        """
        try:
            # Put record in queue, removing oldest if full
            try:
                self.log_queue.put_nowait(record)
            except queue.Full:
                # Remove oldest record and add new one
                try:
                    self.log_queue.get_nowait()
                    self.log_queue.put_nowait(record)
                except queue.Empty:
                    pass
        except Exception:
            # Silently ignore errors to prevent logging loops
            pass


# Global logger instance
_logger_instance = None


def get_logger() -> KafkaToolLogger:
    """
    Get the global logger instance.
    
    Returns:
        KafkaToolLogger: Global logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = KafkaToolLogger()
    return _logger_instance


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> KafkaToolLogger:
    """
    Set up logging for the application.
    
    Args:
        log_dir (str): Directory for log files
        log_level (str): Logging level
    
    Returns:
        KafkaToolLogger: Configured logger instance
    """
    global _logger_instance
    _logger_instance = KafkaToolLogger(log_dir, log_level)
    return _logger_instance


def get_module_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name (str): Module name (usually __name__)
    
    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(name)