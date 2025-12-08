"""
Sidebar component for navigation between pages
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class Sidebar(QWidget):
    """Left sidebar for page navigation"""
    
    page_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("BMS Monitor V2")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("padding: 10px; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Page list
        self.page_list = QListWidget()
        self.page_list.setMinimumWidth(220)
        self.page_list.setMaximumWidth(320)
        self.page_list.setAlternatingRowColors(True)
        self.page_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.page_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Set item height for better spacing
        self.page_list.setStyleSheet("""
            QListWidget {
                border: 2px solid rgb(2, 44, 34);
                border-radius: 8px;
                padding: 5px;
                background-color: rgb(15, 35, 30);
            }
            QListWidget::item {
                padding: 12px 8px;
                margin: 2px;
                border-radius: 6px;
                border: 1px solid transparent;
            }
            QListWidget::item:selected {
                background-color: rgb(34, 139, 34);
                color: rgb(20, 20, 20);
                border: 1px solid rgb(50, 205, 50);
            }
            QListWidget::item:hover {
                background-color: rgb(25, 45, 40);
                border: 1px solid rgb(34, 139, 34);
            }
        """)
        
        # Add page items
        pages = [
            ("Master", "Main BMS control and monitoring"),
            ("Graph/Plotting", "Data visualization and logging"),
            ("Balancing", "Cell balancing control"),
            ("Debugging", "BMS IC command interface"),
            ("Console", "BMS communication and application logs")
        ]
        
        for page_name, description in pages:
            item = QListWidgetItem(page_name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setToolTip(description)
            self.page_list.addItem(item)
        
        # Set first item as selected
        self.page_list.setCurrentRow(0)
        
        # Connect selection change
        self.page_list.currentItemChanged.connect(self.on_page_selected)
        
        layout.addWidget(self.page_list)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Status section
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.Box)
        status_frame.setStyleSheet("""
            QFrame {
                border: 2px solid rgb(2, 44, 34);
                border-radius: 8px;
                background-color: rgb(15, 35, 30);
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 15, 15, 15)
        status_layout.setSpacing(10)
        
        status_title = QLabel("Status")
        status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_title_font = QFont()
        status_title_font.setBold(True)
        status_title_font.setPointSize(12)
        status_title.setFont(status_title_font)
        status_title.setStyleSheet("color: rgb(50, 205, 50); padding: 5px;")
        status_layout.addWidget(status_title)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 8px; color: rgb(240, 248, 255);")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
    def on_page_selected(self, current, previous):
        """Handle page selection"""
        if current:
            page_name = current.text()
            self.page_changed.emit(page_name)
            self.update_status(f"Active Page: {page_name}")
    
    def update_status(self, message: str):
        """Update status message"""
        self.status_label.setText(message)
    
    def set_active_page(self, page_name: str):
        """Set the active page programmatically"""
        for i in range(self.page_list.count()):
            item = self.page_list.item(i)
            if item.text() == page_name:
                self.page_list.setCurrentItem(item)
                break

