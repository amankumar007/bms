"""
Horizontal Navigation Bar component for page navigation
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class NavBar(QWidget):
    """Horizontal navigation bar for page navigation"""
    
    page_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_page = "Master"
        self.buttons = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the navigation bar UI"""
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: rgb(20, 40, 35);
                border-bottom: 2px solid rgb(2, 44, 34);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Page buttons
        pages = [
            ("Master", "Main BMS control and monitoring"),
            ("Graph/Plotting", "Data visualization and logging"),
            ("Balancing", "Cell balancing control"),
            ("Debugging", "BMS IC command interface"),
            ("Console", "BMS communication and application logs"),
            ("Firmware Upgrade", "BMS firmware upgrade utility")
        ]
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        for page_name, tooltip in pages:
            btn = QPushButton(page_name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setMinimumWidth(120)
            btn.setFixedHeight(38)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(25, 50, 45);
                    color: rgb(200, 220, 200);
                    border: 1px solid rgb(2, 44, 34);
                    border-radius: 6px;
                    padding: 8px 15px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgb(35, 70, 60);
                    border: 1px solid rgb(34, 139, 34);
                }
                QPushButton:checked {
                    background-color: rgb(34, 139, 34);
                    color: rgb(15, 25, 20);
                    border: 2px solid rgb(50, 205, 50);
                }
            """)
            btn.clicked.connect(lambda checked, name=page_name: self.on_button_clicked(name))
            self.button_group.addButton(btn)
            self.buttons[page_name] = btn
            layout.addWidget(btn)
        
        # Set first button as checked
        self.buttons["Master"].setChecked(True)
        
        # Add stretch to push buttons to the left
        layout.addStretch()
        
        # Status label on the right
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgb(150, 200, 150);
                font-size: 12px;
                padding: 5px 10px;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.status_label)
    
    def on_button_clicked(self, page_name: str):
        """Handle button click"""
        if page_name != self.current_page:
            self.current_page = page_name
            self.page_changed.emit(page_name)
            self.update_status(f"Active: {page_name}")
    
    def update_status(self, message: str):
        """Update status message"""
        self.status_label.setText(message)
    
    def set_active_page(self, page_name: str):
        """Set the active page programmatically"""
        if page_name in self.buttons:
            self.buttons[page_name].setChecked(True)
            self.current_page = page_name

