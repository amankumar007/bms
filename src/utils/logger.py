"""
Advanced logging system with file rotation and archiving
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from logging.handlers import TimedRotatingFileHandler
import threading


class BMSLogger:
    """Advanced logger with hourly rotation and weekly archiving"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create day-wise folder structure
        self.current_day_dir = self.log_dir / datetime.now().strftime("%Y-%m-%d")
        self.current_day_dir.mkdir(exist_ok=True)
        
        # Setup loggers
        self.setup_loggers()
        
        # Start archiving thread
        self.archive_thread = threading.Thread(target=self.archive_old_logs, daemon=True)
        self.archive_thread.start()
    
    def setup_loggers(self):
        """Setup application and BMS loggers"""
        # Application logger
        self.app_logger = logging.getLogger('BMSApp')
        self.app_logger.setLevel(logging.DEBUG)
        self.app_logger.handlers.clear()
        
        # BMS communication logger
        self.bms_logger = logging.getLogger('BMSComm')
        self.bms_logger.setLevel(logging.DEBUG)
        self.bms_logger.handlers.clear()
        
        # Create handlers with hourly rotation
        app_handler = TimedRotatingFileHandler(
            filename=str(self.current_day_dir / "app.log"),
            when='H',  # Hourly
            interval=1,
            backupCount=24,  # Keep 24 hours of logs
            encoding='utf-8'
        )
        app_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                            datefmt='%Y-%m-%d %H:%M:%S')
        )
        
        bms_handler = TimedRotatingFileHandler(
            filename=str(self.current_day_dir / "bms_comm.log"),
            when='H',  # Hourly
            interval=1,
            backupCount=24,  # Keep 24 hours of logs
            encoding='utf-8'
        )
        bms_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                            datefmt='%Y-%m-%d %H:%M:%S')
        )
        
        self.app_logger.addHandler(app_handler)
        self.bms_logger.addHandler(bms_handler)
        
        # Also add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                            datefmt='%Y-%m-%d %H:%M:%S')
        )
        self.app_logger.addHandler(console_handler)
    
    def update_day_directory(self):
        """Update day directory if date changed"""
        new_day_dir = self.log_dir / datetime.now().strftime("%Y-%m-%d")
        if new_day_dir != self.current_day_dir:
            self.current_day_dir = new_day_dir
            self.current_day_dir.mkdir(exist_ok=True)
            self.setup_loggers()
    
    def log_app(self, level: str, message: str):
        """Log application message"""
        self.update_day_directory()
        log_func = getattr(self.app_logger, level.lower(), self.app_logger.info)
        log_func(message)
    
    def log_bms(self, level: str, message: str):
        """Log BMS communication message"""
        self.update_day_directory()
        log_func = getattr(self.bms_logger, level.lower(), self.bms_logger.info)
        log_func(message)
    
    def archive_old_logs(self):
        """Archive logs older than 7 days"""
        import time
        while True:
            try:
                self._perform_archiving()
            except Exception as e:
                self.app_logger.error(f"Error during archiving: {e}")
            # Check every hour
            time.sleep(3600)
    
    def _perform_archiving(self):
        """Perform the actual archiving operation"""
        archive_dir = self.log_dir / "archived"
        archive_dir.mkdir(exist_ok=True)
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Find all day directories
        for day_dir in self.log_dir.iterdir():
            if not day_dir.is_dir() or day_dir.name == "archived":
                continue
            
            try:
                # Parse date from directory name
                dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d")
                
                if dir_date < cutoff_date:
                    # Archive this directory
                    archive_subdir = archive_dir / day_dir.name
                    if archive_subdir.exists():
                        # Merge with existing archive
                        for file in day_dir.iterdir():
                            shutil.move(str(file), str(archive_subdir / file.name))
                        day_dir.rmdir()
                    else:
                        # Move entire directory
                        shutil.move(str(day_dir), str(archive_subdir))
                    
                    self.app_logger.info(f"Archived log directory: {day_dir.name}")
            except ValueError:
                # Not a date directory, skip
                continue
    
    def get_log_file_path(self, log_type: str = "app") -> str:
        """Get current log file path"""
        if log_type == "app":
            return str(self.current_day_dir / "app.log")
        elif log_type == "bms":
            return str(self.current_day_dir / "bms_comm.log")
        return ""


# Global logger instance
_logger_instance = None


def get_logger() -> BMSLogger:
    """Get global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BMSLogger()
    return _logger_instance

