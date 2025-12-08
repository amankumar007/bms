#!/usr/bin/env python3
"""
BMS Monitor App V2 - Main Entry Point
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main_window import MainWindow
from src.utils.theme import apply_theme


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply custom theme
    apply_theme(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
