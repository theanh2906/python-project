"""
Kafka Tool Main Entry Point

This is the main entry point for the Kafka Tool application.
It initializes the application and starts the GUI.
"""

import logging
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import the main window
from main_window import KafkaToolMainWindow
from logger import setup_logging


def setup_application_environment():
    """
    Set up the application environment and paths.
    """
    # Get the application root directory
    app_root = Path(__file__).parent.parent
    
    # Ensure required directories exist
    directories = [
        app_root / "logs",
        app_root / "config",
        app_root / "assets" / "icons",
        app_root / "assets" / "themes"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return app_root


def main():
    """
    Main entry point for the Kafka Tool application.
    """
    try:
        # Set up application environment
        app_root = setup_application_environment()
        
        # Set up logging
        log_dir = app_root / "logs"
        app_logger = setup_logging(str(log_dir), "INFO")
        
        # Log application startup
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("Kafka Tool Application Starting")
        logger.info(f"Application Root: {app_root}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info("=" * 60)
        
        # Create and run the main application
        app = KafkaToolMainWindow()
        
        logger.info("Main window created successfully")
        logger.info("Starting application main loop...")
        
        # Start the application
        app.run()
        
        logger.info("Application main loop ended")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        # Log the error
        if 'logger' in locals():
            logger.error(f"Fatal error in main application: {e}")
            logger.exception("Full traceback:")
        else:
            print(f"Fatal error before logging setup: {e}")
            import traceback
            traceback.print_exc()
        
        # Show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            error_msg = (
                f"A fatal error occurred while starting the Kafka Tool:\n\n"
                f"{str(e)}\n\n"
                f"Please check the log files for more details."
            )
            
            messagebox.showerror("Kafka Tool - Fatal Error", error_msg)
            
        except Exception:
            # If we can't show a dialog, just print to console
            print(f"Fatal error: {e}")
        
        sys.exit(1)
    
    finally:
        # Clean shutdown
        if 'logger' in locals():
            logger.info("Kafka Tool Application Shutdown")
            logger.info("=" * 60)


if __name__ == "__main__":
    main()