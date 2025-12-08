"""
Theme utilities for the BMS Monitor App
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor


def apply_theme(app: QApplication):
    """Apply custom green-themed palette to the application"""
    
    # Define color palette
    primary_green = QColor(2, 44, 34)  # Main green color
    light_green = QColor(34, 139, 34)  # Lighter green for highlights
    dark_green = QColor(0, 25, 20)     # Darker green for backgrounds
    accent_green = QColor(50, 205, 50) # Bright green for accents
    text_light = QColor(240, 248, 255) # Light text
    text_dark = QColor(20, 20, 20)     # Dark text
    
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.ColorRole.Window, dark_green)
    palette.setColor(QPalette.ColorRole.WindowText, text_light)
    
    # Base colors (for input fields, etc.)
    palette.setColor(QPalette.ColorRole.Base, QColor(15, 35, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(25, 45, 40))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, text_light)
    palette.setColor(QPalette.ColorRole.BrightText, accent_green)
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, primary_green)
    palette.setColor(QPalette.ColorRole.ButtonText, text_light)
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, light_green)
    palette.setColor(QPalette.ColorRole.HighlightedText, text_dark)
    
    # Link colors
    palette.setColor(QPalette.ColorRole.Link, accent_green)
    palette.setColor(QPalette.ColorRole.LinkVisited, light_green)
    
    # Tooltip colors
    palette.setColor(QPalette.ColorRole.ToolTipBase, dark_green)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_light)
    
    app.setPalette(palette)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Apply dark theme stylesheet
    dark_stylesheet = """
    QMainWindow {
        background-color: rgb(0, 25, 20);
        color: rgb(240, 248, 255);
    }
    
    QWidget {
        background-color: rgb(0, 25, 20);
        color: rgb(240, 248, 255);
    }
    
    QPushButton {
        background-color: rgb(2, 44, 34);
        border: 2px solid rgb(34, 139, 34);
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        color: rgb(240, 248, 255);
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
    
    QTextEdit, QPlainTextEdit {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 4px;
        padding: 8px;
        color: rgb(240, 248, 255);
    }
    
    QTextEdit:focus, QPlainTextEdit:focus {
        border-color: rgb(50, 205, 50);
    }
    
    QListWidget {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 4px;
        color: rgb(240, 248, 255);
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid rgb(2, 44, 34);
    }
    
    QListWidget::item:selected {
        background-color: rgb(34, 139, 34);
        color: rgb(20, 20, 20);
    }
    
    QListWidget::item:hover {
        background-color: rgb(25, 45, 40);
    }
    
    QComboBox {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 4px;
        padding: 4px 8px;
        color: rgb(240, 248, 255);
    }
    
    QComboBox:focus {
        border-color: rgb(50, 205, 50);
    }
    
    QComboBox::drop-down {
        border: none;
        background-color: rgb(2, 44, 34);
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid rgb(240, 248, 255);
        margin-right: 5px;
    }
    
    QComboBox QAbstractItemView {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        selection-background-color: rgb(34, 139, 34);
        color: rgb(240, 248, 255);
    }
    
    QGroupBox {
        font-weight: bold;
        border: 2px solid rgb(2, 44, 34);
        border-radius: 8px;
        margin-top: 1ex;
        padding-top: 10px;
        color: rgb(240, 248, 255);
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: rgb(50, 205, 50);
    }
    
    QCheckBox {
        color: rgb(240, 248, 255);
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid rgb(2, 44, 34);
        border-radius: 3px;
        background-color: rgb(15, 35, 30);
    }
    
    QCheckBox::indicator:checked {
        background-color: rgb(50, 205, 50);
        border-color: rgb(50, 205, 50);
    }
    
    QCheckBox::indicator:hover {
        border-color: rgb(34, 139, 34);
    }
    
    QSlider::groove:horizontal {
        border: 1px solid rgb(2, 44, 34);
        height: 8px;
        background: rgb(15, 35, 30);
        border-radius: 4px;
    }
    
    QSlider::handle:horizontal {
        background: rgb(50, 205, 50);
        border: 2px solid rgb(34, 139, 34);
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }
    
    QSlider::handle:horizontal:hover {
        background: rgb(34, 139, 34);
    }
    
    QProgressBar {
        border: 2px solid rgb(2, 44, 34);
        border-radius: 5px;
        text-align: center;
        background-color: rgb(15, 35, 30);
        color: rgb(240, 248, 255);
    }
    
    QProgressBar::chunk {
        background-color: rgb(50, 205, 50);
        border-radius: 3px;
    }
    
    QMenuBar {
        background-color: rgb(2, 44, 34);
        color: rgb(240, 248, 255);
        border-bottom: 1px solid rgb(34, 139, 34);
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 8px 12px;
    }
    
    QMenuBar::item:selected {
        background-color: rgb(34, 139, 34);
    }
    
    QMenu {
        background-color: rgb(15, 35, 30);
        border: 1px solid rgb(2, 44, 34);
        color: rgb(240, 248, 255);
    }
    
    QMenu::item {
        padding: 8px 20px;
    }
    
    QMenu::item:selected {
        background-color: rgb(34, 139, 34);
    }
    
    QStatusBar {
        background-color: rgb(2, 44, 34);
        color: rgb(240, 248, 255);
        border-top: 1px solid rgb(34, 139, 34);
    }
    
    QTabWidget::pane {
        border: 2px solid rgb(2, 44, 34);
        background-color: rgb(15, 35, 30);
    }
    
    QTabBar::tab {
        background-color: rgb(2, 44, 34);
        border: 1px solid rgb(34, 139, 34);
        padding: 8px 16px;
        margin-right: 2px;
        color: rgb(240, 248, 255);
    }
    
    QTabBar::tab:selected {
        background-color: rgb(34, 139, 34);
        color: rgb(20, 20, 20);
    }
    
    QTabBar::tab:hover {
        background-color: rgb(25, 45, 40);
    }
    
    QLineEdit {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 4px;
        padding: 4px 8px;
        color: rgb(240, 248, 255);
    }
    
    QLineEdit:focus {
        border-color: rgb(50, 205, 50);
    }
    
    QSpinBox {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 4px;
        padding: 4px 8px;
        color: rgb(240, 248, 255);
    }
    
    QSpinBox:focus {
        border-color: rgb(50, 205, 50);
    }
    
    QLabel {
        color: rgb(240, 248, 255);
    }
    
    QMessageBox {
        background-color: rgb(15, 35, 30);
        border: 2px solid rgb(2, 44, 34);
        border-radius: 12px;
        color: rgb(240, 248, 255);
    }
    
    QMessageBox QLabel {
        color: rgb(240, 248, 255);
        background-color: transparent;
        padding: 10px;
        border-radius: 8px;
    }
    
    QMessageBox QPushButton {
        background-color: rgb(2, 44, 34);
        border: 2px solid rgb(34, 139, 34);
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        color: rgb(240, 248, 255);
        min-width: 80px;
        min-height: 30px;
    }
    
    QMessageBox QPushButton:hover {
        background-color: rgb(34, 139, 34);
        border-color: rgb(50, 205, 50);
        border-radius: 10px;
    }
    
    QMessageBox QPushButton:pressed {
        background-color: rgb(0, 25, 20);
        border-color: rgb(50, 205, 50);
        border-radius: 10px;
    }
    
    QMessageBox QPushButton:default {
        background-color: rgb(34, 139, 34);
        border: 2px solid rgb(50, 205, 50);
        border-radius: 8px;
    }
    
    QMessageBox QPushButton:default:hover {
        background-color: rgb(50, 205, 50);
        border-color: rgb(50, 205, 50);
        border-radius: 10px;
    }
    """
    
    app.setStyleSheet(dark_stylesheet)

