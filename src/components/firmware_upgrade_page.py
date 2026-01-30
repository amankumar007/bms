"""
Firmware Upgrade Page Component
BMS Firmware upgrade utility v0.0
"""

import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from src.data.hid_connection import HIDConnection
from src.utils.logger import get_logger
from src.utils.message_box import StyledMessageBox


class FirmwareUpgradeThread(QThread):
    """Thread for firmware upgrade to avoid blocking UI"""
    
    progress = pyqtSignal(int)
    complete = pyqtSignal(bool, str)
    
    def __init__(self, hid_connection: HIDConnection, firmware_data: bytes):
        super().__init__()
        self.hid_connection = hid_connection
        self.firmware_data = firmware_data
    
    def run(self):
        """Run firmware upgrade in background thread"""
        success = self.hid_connection.upgrade_firmware(self.firmware_data)
        if success:
            self.complete.emit(True, "Firmware upgrade completed successfully")
        else:
            self.complete.emit(False, "Firmware upgrade failed")


class FirmwareUpgradePage(QWidget):
    """Firmware upgrade page with USB HID communication"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.setup_ui()
        
        # Initialize HID connection
        # Note: VID and PID should be configured using set_vid_pid() method
        # Example: self.set_vid_pid(0x1234, 0x5678)
        self.hid_connection = HIDConnection()
        self.hid_connection.connection_status_changed.connect(self.on_connection_status_changed)
        self.hid_connection.device_info_received.connect(self.on_device_info_received)
        self.hid_connection.upgrade_progress.connect(self.on_upgrade_progress)
        self.hid_connection.upgrade_complete.connect(self.on_upgrade_complete)
        
        # State
        self.firmware_file_path = ""
        self.firmware_data = None
        self.upgrade_thread = None
        
        # Start device discovery
        self.hid_connection.start_device_discovery()
        
        # Check for device periodically
        self.check_device_timer = self.hid_connection.discovery_timer
        
        # Auto-connect when device is found
        self.auto_connect_enabled = True
    
    def setup_ui(self):
        """Setup the firmware upgrade UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title bar
        title_layout = QHBoxLayout()
        title_label = QLabel("BMS - Firmware upgrade utility v0.0")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: rgb(240, 248, 255);")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: rgb(2, 44, 34);")
        main_layout.addWidget(separator)
        
        # Row 1: Status, Serial No, Software version
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        
        # Status
        status_label = QLabel("Status:")
        status_label.setFont(QFont("Arial", 12))
        status_label.setMinimumWidth(80)
        status_label.setStyleSheet("color: rgb(240, 248, 255);")
        row1_layout.addWidget(status_label)
        
        self.status_field = QLineEdit("Disconnected")
        self.status_field.setReadOnly(True)
        self.status_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.status_field.setMinimumWidth(150)
        row1_layout.addWidget(self.status_field)
        
        # Serial No
        serial_label = QLabel("Serial No#:")
        serial_label.setFont(QFont("Arial", 12))
        serial_label.setMinimumWidth(100)
        serial_label.setStyleSheet("color: rgb(240, 248, 255);")
        row1_layout.addWidget(serial_label)
        
        self.serial_field = QLineEdit()
        self.serial_field.setReadOnly(True)
        self.serial_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.serial_field.setMinimumWidth(150)
        row1_layout.addWidget(self.serial_field)
        
        # Software version section
        version_layout = QVBoxLayout()
        version_layout.setSpacing(5)
        
        new_version_label = QLabel("Software version")
        new_version_label.setFont(QFont("Arial", 12))
        new_version_label.setStyleSheet("color: rgb(240, 248, 255);")
        version_layout.addWidget(new_version_label)
        
        present_version_label = QLabel("Present S/W version")
        present_version_label.setFont(QFont("Arial", 12))
        present_version_label.setStyleSheet("color: rgb(240, 248, 255);")
        version_layout.addWidget(present_version_label)
        
        row1_layout.addLayout(version_layout)
        
        version_fields_layout = QVBoxLayout()
        version_fields_layout.setSpacing(5)
        
        self.new_version_field = QLineEdit()
        self.new_version_field.setReadOnly(True)
        self.new_version_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.new_version_field.setMinimumWidth(150)
        version_fields_layout.addWidget(self.new_version_field)
        
        self.present_version_field = QLineEdit()
        self.present_version_field.setReadOnly(True)
        self.present_version_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.present_version_field.setMinimumWidth(150)
        version_fields_layout.addWidget(self.present_version_field)
        
        row1_layout.addLayout(version_fields_layout)
        row1_layout.addStretch()
        
        main_layout.addLayout(row1_layout)
        
        # Row 2: File selection
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        
        file_label = QLabel("File selection:")
        file_label.setFont(QFont("Arial", 12))
        file_label.setMinimumWidth(100)
        file_label.setStyleSheet("color: rgb(240, 248, 255);")
        row2_layout.addWidget(file_label)
        
        self.file_path_field = QLineEdit()
        self.file_path_field.setReadOnly(True)
        self.file_path_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        row2_layout.addWidget(self.file_path_field)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFont(QFont("Arial", 12))
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(2, 44, 34);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(34, 139, 34);
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(34, 139, 34);
                border-color: rgb(50, 205, 50);
            }
            QPushButton:pressed {
                background-color: rgb(0, 25, 20);
            }
        """)
        self.browse_button.clicked.connect(self.on_browse_file)
        row2_layout.addWidget(self.browse_button)
        
        main_layout.addLayout(row2_layout)
        
        # Row 3: Upgrade status and button
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(20)
        
        upgrade_status_label = QLabel("Upgrade status:")
        upgrade_status_label.setFont(QFont("Arial", 12))
        upgrade_status_label.setMinimumWidth(120)
        upgrade_status_label.setStyleSheet("color: rgb(240, 248, 255);")
        row3_layout.addWidget(upgrade_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgb(15, 35, 30);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                text-align: center;
                color: rgb(240, 248, 255);
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: rgb(50, 205, 50);
                border-radius: 2px;
            }
        """)
        self.progress_bar.setFormat("%p%")
        row3_layout.addWidget(self.progress_bar)
        
        row3_layout.addStretch()
        
        self.upgrade_button = QPushButton("UPGRADE")
        self.upgrade_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.upgrade_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(2, 44, 34);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(34, 139, 34);
                border-radius: 4px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(34, 139, 34);
                border-color: rgb(50, 205, 50);
            }
            QPushButton:pressed {
                background-color: rgb(0, 25, 20);
            }
            QPushButton:disabled {
                background-color: rgb(15, 35, 30);
                border-color: rgb(25, 45, 40);
                color: rgb(100, 100, 100);
            }
        """)
        self.upgrade_button.setEnabled(False)
        self.upgrade_button.clicked.connect(self.on_upgrade_clicked)
        row3_layout.addWidget(self.upgrade_button)
        
        main_layout.addLayout(row3_layout)
        
        # Row 4: Notification
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(20)
        
        notification_label = QLabel("Notification:")
        notification_label.setFont(QFont("Arial", 12))
        notification_label.setMinimumWidth(100)
        notification_label.setStyleSheet("color: rgb(240, 248, 255);")
        row4_layout.addWidget(notification_label)
        
        self.notification_field = QLineEdit()
        self.notification_field.setReadOnly(True)
        self.notification_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(15, 35, 30);
                color: rgb(240, 248, 255);
                border: 2px solid rgb(2, 44, 34);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.notification_field.setText("Ready")
        row4_layout.addWidget(self.notification_field)
        
        main_layout.addLayout(row4_layout)
        
        main_layout.addStretch()
    
    def on_browse_file(self):
        """Handle file browse button click"""
        # Get default directory (current directory or firmware directory)
        default_dir = os.getcwd()
        if os.path.exists("firmware"):
            default_dir = "firmware"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware File",
            default_dir,
            "Firmware Files (*.bin *.hex *.fw);;All Files (*.*)"
        )
        
        if file_path:
            self.firmware_file_path = file_path
            self.file_path_field.setText(file_path)
            
            # Extract version from filename
            filename = os.path.basename(file_path)
            version = self.extract_version_from_filename(filename)
            if version:
                self.new_version_field.setText(version)
            else:
                self.new_version_field.setText("Unknown")
            
            # Read firmware file
            try:
                with open(file_path, 'rb') as f:
                    self.firmware_data = f.read()
                self.logger.log_app("INFO", f"Loaded firmware file: {file_path} ({len(self.firmware_data)} bytes)")
                self.update_notification("Firmware file loaded successfully")
                
                # Enable upgrade button if connected
                if self.hid_connection.is_connected:
                    self.upgrade_button.setEnabled(True)
            except Exception as e:
                self.logger.log_app("ERROR", f"Error reading firmware file: {e}")
                StyledMessageBox.critical(self, "File Error", f"Failed to read firmware file:\n{e}")
                self.firmware_data = None
                self.upgrade_button.setEnabled(False)
                self.update_notification("Improper file format.")
    
    def extract_version_from_filename(self, filename: str) -> str:
        """
        Extract version from filename
        Expected format: BM-xx.xx.xx or similar
        """
        # Try to find version pattern like xx.xx.xx or BM-xx.xx.xx
        patterns = [
            r'BM-(\d+\.\d+\.\d+)',  # BM-xx.xx.xx
            r'(\d+\.\d+\.\d+)',      # xx.xx.xx
            r'v?(\d+\.\d+\.\d+)',    # vxx.xx.xx
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        
        return ""
    
    def on_upgrade_clicked(self):
        """Handle upgrade button click"""
        if not self.hid_connection.is_connected:
            StyledMessageBox.warning(self, "Not Connected", "Please connect to device first")
            return
        
        if not self.firmware_data:
            StyledMessageBox.warning(self, "No Firmware", "Please select a firmware file first")
            return
        
        # Confirm upgrade
        reply = QMessageBox.question(
            self,
            "Confirm Upgrade",
            f"Are you sure you want to upgrade firmware?\n\n"
            f"Current version: {self.present_version_field.text()}\n"
            f"New version: {self.new_version_field.text()}\n\n"
            f"This process cannot be interrupted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_upgrade()
    
    def start_upgrade(self):
        """Start firmware upgrade process"""
        self.upgrade_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.update_notification("Firmware upgrade started.")
        
        # Create and start upgrade thread
        self.upgrade_thread = FirmwareUpgradeThread(self.hid_connection, self.firmware_data)
        self.upgrade_thread.progress.connect(self.on_upgrade_progress)
        self.upgrade_thread.complete.connect(self.on_upgrade_complete)
        self.upgrade_thread.start()
    
    def on_connection_status_changed(self, connected: bool):
        """Handle connection status change"""
        if connected:
            self.status_field.setText("Connected")
            self.status_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgb(15, 35, 30);
                    color: rgb(50, 205, 50);
                    border: 2px solid rgb(34, 139, 34);
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            # Request device info
            self.hid_connection.request_device_info()
            # Enable upgrade button if firmware is loaded
            if self.firmware_data:
                self.upgrade_button.setEnabled(True)
        else:
            self.status_field.setText("Disconnected")
            self.status_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgb(15, 35, 30);
                    color: rgb(255, 100, 100);
                    border: 2px solid rgb(2, 44, 34);
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            self.serial_field.setText("")
            self.present_version_field.setText("")
            self.upgrade_button.setEnabled(False)
    
    def on_device_info_received(self, serial_number: str, firmware_version: str):
        """Handle device info received"""
        self.serial_field.setText(serial_number)
        self.present_version_field.setText(firmware_version)
        self.logger.log_app("INFO", f"Device info: Serial={serial_number}, Version={firmware_version}")
    
    def on_upgrade_progress(self, progress: int):
        """Handle upgrade progress update"""
        self.progress_bar.setValue(progress)
        if progress > 0 and progress < 100:
            self.update_notification("Firmware upgrade is in progress.")
    
    def on_upgrade_complete(self, success: bool, message: str):
        """Handle upgrade completion"""
        self.upgrade_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            old_version = self.present_version_field.text()
            new_version = self.new_version_field.text()
            self.update_notification(f"Device is upgraded with firmware version {new_version}")
            self.logger.log_app("INFO", f"Firmware upgrade completed: {old_version} -> {new_version}")
            
            # Update present version
            self.present_version_field.setText(new_version)
            
            # Request updated device info
            if self.hid_connection.is_connected:
                self.hid_connection.request_device_info()
        else:
            self.update_notification("Communication is failed with device.")
            self.logger.log_app("ERROR", f"Firmware upgrade failed: {message}")
            StyledMessageBox.critical(self, "Upgrade Failed", message)
    
    def update_notification(self, message: str):
        """Update notification field"""
        self.notification_field.setText(message)
    
    def set_vid_pid(self, vid: int, pid: int):
        """Set Vendor ID and Product ID for device identification"""
        self.hid_connection.set_vid_pid(vid, pid)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.upgrade_thread and self.upgrade_thread.isRunning():
            self.upgrade_thread.terminate()
            self.upgrade_thread.wait()
        
        self.hid_connection.stop_device_discovery()
        self.hid_connection.disconnect()

