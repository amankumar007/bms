"""
Balancing Page Component - Cell balancing control
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGridLayout, QFrame,
    QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class BalancingPage(QWidget):
    """Balancing page for cell balancing control"""
    
    # Signals
    balancing_changed = pyqtSignal(int, bool)  # device_id, enable
    balancing_sequence_changed = pyqtSignal(int, int)  # device_id, sequence
    
    def __init__(self):
        super().__init__()
        self.current_device_id = 1  # Master BMS
        self.balancing_enabled = False
        self.balancing_state = 0  # 16-bit state
        self.balancing_status = 0  # ON/OFF status (0x0000 or 0x0001)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the balancing page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Cell Balancing Control")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Device selection (supports up to 35 slaves)
        device_group = QGroupBox("Device Selection")
        device_layout = QHBoxLayout(device_group)
        device_layout.addWidget(QLabel("Select Device:"))
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        # Add master and all possible slaves
        self.device_combo.addItem("Master BMS", 1)
        for i in range(35):
            self.device_combo.addItem(f"Slave {i+1} (0x{i+2:02X})", i + 2)
        self.device_combo.currentIndexChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_combo)
        
        device_layout.addStretch()
        layout.addWidget(device_group)
        
        # Balancing mode selection
        mode_group = QGroupBox("Balancing Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup()
        
        single_cell_radio = QRadioButton("Single Cell Balancing")
        single_cell_radio.setChecked(True)
        self.mode_button_group.addButton(single_cell_radio, 1)
        mode_layout.addWidget(single_cell_radio)
        
        dual_cell_radio = QRadioButton("Dual Cell Balancing")
        self.mode_button_group.addButton(dual_cell_radio, 2)
        mode_layout.addWidget(dual_cell_radio)
        
        layout.addWidget(mode_group)
        
        # Balancing pattern selection
        pattern_group = QGroupBox("Balancing Pattern")
        pattern_layout = QVBoxLayout(pattern_group)
        
        self.pattern_button_group = QButtonGroup()
        
        odd_radio = QRadioButton("Odd Cells")
        odd_radio.setChecked(True)
        self.pattern_button_group.addButton(odd_radio, 1)
        pattern_layout.addWidget(odd_radio)
        
        even_radio = QRadioButton("Even Cells")
        self.pattern_button_group.addButton(even_radio, 2)
        pattern_layout.addWidget(even_radio)
        
        layout.addWidget(pattern_group)
        
        # Control buttons
        control_group = QGroupBox("Control")
        control_layout = QHBoxLayout(control_group)
        
        self.apply_btn = QPushButton("Apply Balancing Pattern")
        self.apply_btn.clicked.connect(self.apply_balancing_pattern)
        control_layout.addWidget(self.apply_btn)
        
        self.enable_btn = QPushButton("Enable Balancing")
        self.enable_btn.clicked.connect(self.toggle_balancing)
        control_layout.addWidget(self.enable_btn)
        
        self.disable_btn = QPushButton("Disable Balancing")
        self.disable_btn.clicked.connect(self.disable_balancing)
        control_layout.addWidget(self.disable_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # Cell balancing status
        status_group = QGroupBox("Cell Balancing Status")
        status_layout = QVBoxLayout(status_group)
        
        status_label = QLabel("Cell Status (Green = ON, Red = OFF):")
        status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_label)
        
        # Create cell status grid
        self.cell_status_grid = QGridLayout()
        self.cell_indicators = []
        self.cell_labels = []
        
        for i in range(16):
            # Indicator (colored label)
            indicator = QLabel("●")
            indicator.setStyleSheet("font-size: 24px; color: rgb(200, 50, 50);")  # Red by default
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cell_indicators.append(indicator)
            
            # Label
            label = QLabel(f"Cell {i+1}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cell_labels.append(label)
            
            # Layout
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(5, 5, 5, 5)
            cell_layout.addWidget(indicator)
            cell_layout.addWidget(label)
            
            row = i // 4
            col = i % 4
            self.cell_status_grid.addWidget(cell_widget, row, col)
        
        status_layout.addLayout(self.cell_status_grid)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def on_device_selection_changed(self, index: int):
        """Handle device selection change from combo box"""
        device_id = self.device_combo.itemData(index)
        self.current_device_id = device_id
        self.update_balancing_indicators()
    
    def apply_balancing_pattern(self):
        """Apply the selected balancing pattern"""
        mode = self.mode_button_group.checkedId()
        pattern = self.pattern_button_group.checkedId()
        
        sequence = 0
        
        if mode == 1:  # Single cell balancing
            if pattern == 1:  # Odd cells
                # Set bits for odd cells (0, 2, 4, 6, 8, 10, 12, 14)
                for i in range(0, 16, 2):
                    sequence |= (1 << i)
            else:  # Even cells
                # Set bits for even cells (1, 3, 5, 7, 9, 11, 13, 15)
                for i in range(1, 16, 2):
                    sequence |= (1 << i)
        else:  # Dual cell balancing
            if pattern == 1:  # Odd pairs
                # Set bits for odd pairs: (0,1), (4,5), (8,9), (12,13)
                for i in range(0, 16, 4):
                    sequence |= (1 << i)
                    sequence |= (1 << (i + 1))
            else:  # Even pairs
                # Set bits for even pairs: (2,3), (6,7), (10,11), (14,15)
                for i in range(2, 16, 4):
                    sequence |= (1 << i)
                    sequence |= (1 << (i + 1))
        
        self.balancing_sequence_changed.emit(self.current_device_id, sequence)
    
    def toggle_balancing(self):
        """Toggle balancing on/off"""
        self.balancing_enabled = not self.balancing_enabled
        self.balancing_changed.emit(self.current_device_id, self.balancing_enabled)
        
        if self.balancing_enabled:
            self.enable_btn.setText("Disable Balancing")
            self.enable_btn.setStyleSheet("background-color: rgb(200, 50, 50);")
        else:
            self.enable_btn.setText("Enable Balancing")
            self.enable_btn.setStyleSheet("")
    
    def disable_balancing(self):
        """Disable balancing"""
        self.balancing_enabled = False
        self.balancing_changed.emit(self.current_device_id, False)
        self.enable_btn.setText("Enable Balancing")
        self.enable_btn.setStyleSheet("")
    
    def update_balancing_state(self, state: int):
        """Update balancing state (cell-wise) from BMS"""
        self.balancing_state = state
        self.update_balancing_indicators()
    
    def update_balancing_enabled(self, enabled: bool):
        """Update balancing enabled status from BMS (Version 0.2)"""
        self.balancing_enabled = enabled
        if enabled:
            self.enable_btn.setText("Disable Balancing")
            self.enable_btn.setStyleSheet("background-color: rgb(200, 50, 50);")
        else:
            self.enable_btn.setText("Enable Balancing")
            self.enable_btn.setStyleSheet("")
    
    def update_balancing_indicators(self):
        """Update cell balancing indicators based on current state"""
        for i in range(16):
            # Check if bit i is set (cell i is balancing)
            is_balancing = (self.balancing_state >> i) & 1
            
            if is_balancing:
                # Green for ON
                self.cell_indicators[i].setStyleSheet("font-size: 24px; color: rgb(50, 205, 50);")
            else:
                # Red for OFF
                self.cell_indicators[i].setStyleSheet("font-size: 24px; color: rgb(200, 50, 50);")

