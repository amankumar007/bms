"""
Console Page Component - Display BMS communication and application logs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QTabWidget, QFileDialog
)
from src.utils.message_box import StyledMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor
from datetime import datetime
from pathlib import Path
import os
import platform
import subprocess


class LogHandler(QObject):
    """Custom log handler that emits signals for Qt"""
    log_received = pyqtSignal(str, str)  # level, message
    
    def emit(self, record):
        """Emit log record as signal"""
        level = record.levelname
        message = record.getMessage()
        self.log_received.emit(level, message)


class ConsolePage(QWidget):
    """Console page for displaying BMS communication and application logs"""
    
    def __init__(self):
        super().__init__()
        self.bms_logs = []
        self.app_logs = []
        self.max_log_lines = 1000  # Maximum lines to keep in memory
        self.setup_ui()
        
        # Timer to check for log file updates
        self.log_file_timer = QTimer()
        self.log_file_timer.timeout.connect(self.update_from_log_files)
        self.log_file_timer.start(1000)  # Check every second
        
    def setup_ui(self):
        """Setup the console page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Console & Logs")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget for different log views
        self.tab_widget = QTabWidget()
        
        # BMS Communication Log Tab
        bms_tab = QWidget()
        bms_layout = QVBoxLayout(bms_tab)
        bms_layout.setContentsMargins(10, 10, 10, 10)
        
        bms_controls = QHBoxLayout()
        bms_controls.addWidget(QLabel("BMS Communication Log:"))
        clear_bms_btn = QPushButton("Clear")
        clear_bms_btn.clicked.connect(self.clear_bms_logs)
        bms_controls.addWidget(clear_bms_btn)
        bms_controls.addStretch()
        bms_layout.addLayout(bms_controls)
        
        self.bms_log_edit = QTextEdit()
        self.bms_log_edit.setReadOnly(True)
        self.bms_log_edit.setFont(QFont("Courier", 9))
        self.bms_log_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgb(0, 0, 0);
                color: rgb(0, 255, 0);
                border: 2px solid rgb(2, 44, 34);
            }
        """)
        bms_layout.addWidget(self.bms_log_edit)
        
        self.tab_widget.addTab(bms_tab, "BMS Communication")
        
        # Application Log Tab
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)
        app_layout.setContentsMargins(10, 10, 10, 10)
        
        app_controls = QHBoxLayout()
        app_controls.addWidget(QLabel("Application Log:"))
        clear_app_btn = QPushButton("Clear")
        clear_app_btn.clicked.connect(self.clear_app_logs)
        app_controls.addWidget(clear_app_btn)
        app_controls.addStretch()
        app_layout.addLayout(app_controls)
        
        self.app_log_edit = QTextEdit()
        self.app_log_edit.setReadOnly(True)
        self.app_log_edit.setFont(QFont("Courier", 9))
        self.app_log_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgb(0, 0, 0);
                color: rgb(0, 255, 0);
                border: 2px solid rgb(2, 44, 34);
            }
        """)
        app_layout.addWidget(self.app_log_edit)
        
        self.tab_widget.addTab(app_tab, "Application Log")
        
        layout.addWidget(self.tab_widget)
        
        # Controls
        controls_group = QGroupBox("Log Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.auto_scroll_checkbox = QPushButton("Auto-scroll: ON")
        self.auto_scroll_checkbox.setCheckable(True)
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.clicked.connect(self.toggle_auto_scroll)
        controls_layout.addWidget(self.auto_scroll_checkbox)
        
        open_log_btn = QPushButton("Open Log Folder")
        open_log_btn.clicked.connect(self.open_log_folder)
        controls_layout.addWidget(open_log_btn)
        
        refresh_btn = QPushButton("Refresh from Files")
        refresh_btn.clicked.connect(self.refresh_from_files)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
    def add_bms_log(self, level: str, message: str):
        """Add BMS communication log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.bms_logs.append(log_entry)
        
        # Limit log size
        if len(self.bms_logs) > self.max_log_lines:
            self.bms_logs = self.bms_logs[-self.max_log_lines:]
        
        # Update display
        self.bms_log_edit.append(log_entry)
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.bms_log_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def add_app_log(self, level: str, message: str):
        """Add application log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.app_logs.append(log_entry)
        
        # Limit log size
        if len(self.app_logs) > self.max_log_lines:
            self.app_logs = self.app_logs[-self.max_log_lines:]
        
        # Update display
        self.app_log_edit.append(log_entry)
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.app_log_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_bms_logs(self):
        """Clear BMS communication logs"""
        self.bms_log_edit.clear()
        self.bms_logs.clear()
        self.add_bms_log("INFO", "BMS communication log cleared")
    
    def clear_app_logs(self):
        """Clear application logs"""
        self.app_log_edit.clear()
        self.app_logs.clear()
        self.add_app_log("INFO", "Application log cleared")
    
    def toggle_auto_scroll(self):
        """Toggle auto-scroll mode"""
        if self.auto_scroll_checkbox.isChecked():
            self.auto_scroll_checkbox.setText("Auto-scroll: ON")
        else:
            self.auto_scroll_checkbox.setText("Auto-scroll: OFF")
    
    def open_log_folder(self):
        """Open log folder in file manager"""
        log_dir = Path("logs")
        if log_dir.exists():
            system = platform.system()
            if system == "Windows":
                os.startfile(str(log_dir))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(log_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(log_dir)])
        else:
            StyledMessageBox.information(self, "Log Folder", "Log folder does not exist yet.")
    
    def refresh_from_files(self):
        """Refresh logs from log files"""
        self.update_from_log_files()
        StyledMessageBox.information(self, "Refresh", "Logs refreshed from files.")
    
    def update_from_log_files(self):
        """Update logs from log files"""
        from src.utils.logger import get_logger
        logger = get_logger()
        
        # Update BMS logs
        bms_log_file = logger.get_log_file_path("bms")
        if bms_log_file and os.path.exists(bms_log_file):
            try:
                with open(bms_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Show last 100 lines
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    if recent_lines:
                        # Only update if content changed
                        current_text = self.bms_log_edit.toPlainText()
                        new_text = ''.join(recent_lines)
                        if new_text != current_text:
                            self.bms_log_edit.setPlainText(new_text)
                            if self.auto_scroll_checkbox.isChecked():
                                scrollbar = self.bms_log_edit.verticalScrollBar()
                                scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                pass  # Silently fail if file is locked
        
        # Update app logs
        app_log_file = logger.get_log_file_path("app")
        if app_log_file and os.path.exists(app_log_file):
            try:
                with open(app_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Show last 100 lines
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    if recent_lines:
                        # Only update if content changed
                        current_text = self.app_log_edit.toPlainText()
                        new_text = ''.join(recent_lines)
                        if new_text != current_text:
                            self.app_log_edit.setPlainText(new_text)
                            if self.auto_scroll_checkbox.isChecked():
                                scrollbar = self.app_log_edit.verticalScrollBar()
                                scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                pass  # Silently fail if file is locked

