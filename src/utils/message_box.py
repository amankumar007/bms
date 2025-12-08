"""
Custom styled message box utilities
"""

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class CenteredMessageBox(QMessageBox):
    """Custom QMessageBox that centers itself"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
    
    def showEvent(self, event):
        """Override showEvent to center the dialog"""
        super().showEvent(event)
        self._center_dialog()
    
    def _center_dialog(self):
        """Center the dialog relative to parent or screen"""
        # Get the actual size of the dialog after it's shown
        dialog_size = self.size()
        
        # Center on parent if available
        if self._parent and self._parent.isVisible():
            parent_geometry = self._parent.geometry()
            
            x = parent_geometry.x() + (parent_geometry.width() - dialog_size.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_size.height()) // 2
            
            # Ensure dialog is within screen bounds
            screen = QApplication.primaryScreen().geometry()
            x = max(0, min(x, screen.width() - dialog_size.width()))
            y = max(0, min(y, screen.height() - dialog_size.height()))
            
            self.move(x, y)
        else:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            
            x = (screen.width() - dialog_size.width()) // 2
            y = (screen.height() - dialog_size.height()) // 2
            
            self.move(x, y)
        
        # Also use a timer as backup to ensure centering
        QTimer.singleShot(50, self._center_dialog)


class StyledMessageBox:
    """Custom styled message box with rounded corners and centered positioning"""
    
    @staticmethod
    def information(parent, title: str, message: str):
        """Show styled information message box"""
        msg_box = CenteredMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply additional styling
        StyledMessageBox._apply_custom_styling(msg_box)
        
        return msg_box.exec()
    
    @staticmethod
    def warning(parent, title: str, message: str):
        """Show styled warning message box"""
        msg_box = CenteredMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply additional styling
        StyledMessageBox._apply_custom_styling(msg_box)
        
        return msg_box.exec()
    
    @staticmethod
    def critical(parent, title: str, message: str):
        """Show styled critical/error message box"""
        msg_box = CenteredMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply additional styling
        StyledMessageBox._apply_custom_styling(msg_box)
        
        return msg_box.exec()
    
    @staticmethod
    def question(parent, title: str, message: str, 
                 buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        """Show styled question message box"""
        msg_box = CenteredMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(buttons)
        
        # Apply additional styling
        StyledMessageBox._apply_custom_styling(msg_box)
        
        return msg_box.exec()
    
    @staticmethod
    def _apply_custom_styling(msg_box):
        """Apply additional custom styling to message box"""
        # Set font
        font = QFont()
        font.setPointSize(10)
        msg_box.setFont(font)
        
        # Additional style sheet for smoother appearance
        additional_style = """
        QMessageBox {
            border-radius: 12px;
        }
        
        QMessageBox QLabel#qt_msgbox_label {
            padding: 15px;
            border-radius: 8px;
        }
        
        QMessageBox QPushButton {
            border-radius: 8px;
            padding: 8px 16px;
            margin: 5px;
        }
        
        QMessageBox QPushButton:hover {
            border-radius: 10px;
        }
        """
        
        msg_box.setStyleSheet(msg_box.styleSheet() + additional_style)
