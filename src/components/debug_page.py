"""
Debugging Page Component - BMS IC command interface
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit
)
from src.utils.message_box import StyledMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class DebugPage(QWidget):
    """Debugging page for sending commands to BMS IC"""
    
    # Signals
    command_sent = pyqtSignal(bytes)  # Emits command bytes
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the debugging page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Debugging Page")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "This page allows you to send debugging commands directly to the BMS IC.\n"
            "Enter command bytes in hexadecimal format (e.g., 01 02 03 04)."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        # Command section
        command_group = QGroupBox("Command")
        command_layout = QVBoxLayout(command_group)
        
        command_label = QLabel("Enter Command (Hex bytes, space-separated):")
        command_layout.addWidget(command_label)
        
        self.command_edit = QTextEdit()
        self.command_edit.setPlaceholderText("Example: 01 02 03 04")
        self.command_edit.setMaximumHeight(100)
        command_layout.addWidget(self.command_edit)
        
        # Send button
        send_layout = QHBoxLayout()
        send_layout.addStretch()
        self.send_btn = QPushButton("Send Command")
        self.send_btn.clicked.connect(self.send_command)
        send_layout.addWidget(self.send_btn)
        send_layout.addStretch()
        command_layout.addLayout(send_layout)
        
        layout.addWidget(command_group)
        
        # Response section
        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout(response_group)
        
        response_label = QLabel("Response from BMS IC:")
        response_layout.addWidget(response_label)
        
        self.response_edit = QTextEdit()
        self.response_edit.setReadOnly(True)
        self.response_edit.setPlaceholderText("Response will appear here...")
        response_layout.addWidget(self.response_edit)
        
        # Clear button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        clear_btn = QPushButton("Clear Response")
        clear_btn.clicked.connect(self.clear_response)
        clear_layout.addWidget(clear_btn)
        clear_layout.addStretch()
        response_layout.addLayout(clear_layout)
        
        layout.addWidget(response_group)
        
        layout.addStretch()
        
    def send_command(self):
        """Send command to BMS IC"""
        command_text = self.command_edit.toPlainText().strip()
        
        if not command_text:
            StyledMessageBox.warning(self, "No Command", "Please enter a command.")
            return
        
        try:
            # Parse hexadecimal bytes
            hex_bytes = command_text.split()
            command_bytes = bytes([int(byte, 16) for byte in hex_bytes])
            
            # Emit signal with command bytes
            self.command_sent.emit(command_bytes)
            
        except ValueError as e:
            StyledMessageBox.critical(
                self,
                "Invalid Command",
                f"Invalid hexadecimal format: {str(e)}\n\n"
                "Please enter space-separated hexadecimal bytes (e.g., 01 02 03 04)"
            )
        except Exception as e:
            StyledMessageBox.critical(self, "Error", f"Failed to send command: {str(e)}")
    
    def display_response(self, response_bytes: bytes):
        """Display response from BMS IC"""
        if response_bytes:
            # Format as hexadecimal
            hex_string = ' '.join([f'{b:02X}' for b in response_bytes])
            self.response_edit.append(f"Response: {hex_string}\n")
        else:
            self.response_edit.append("No response received or timeout.\n")
        
        # Auto-scroll to bottom
        scrollbar = self.response_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_response(self):
        """Clear response display"""
        self.response_edit.clear()

