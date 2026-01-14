"""
Balancing Page Component - Cell balancing control
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGridLayout, QFrame,
    QComboBox, QScrollArea, QSizePolicy, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush


class BatteryWidget(QWidget):
    """Custom vertical battery indicator widget for balancing page with status dot"""
    
    def __init__(self, cell_num: int = 1):
        super().__init__()
        self.cell_num = cell_num
        self.voltage = 0.0
        self.percentage = 0
        self.is_balancing = False
        self.setMinimumSize(55, 115)
        self.setMaximumSize(80, 145)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background-color: transparent;")
    
    def set_voltage(self, voltage: float):
        """Set voltage and calculate percentage (0-5V range, 2V min useful)"""
        self.voltage = voltage
        # Calculate percentage: 2V = 0%, 5V = 100%
        if voltage <= 2.0:
            self.percentage = 0
        elif voltage >= 5.0:
            self.percentage = 100
        else:
            self.percentage = int(((voltage - 2.0) / 3.0) * 100)
        self.update()
    
    def set_balancing(self, is_balancing: bool):
        """Set balancing status"""
        self.is_balancing = is_balancing
        self.update()
    
    def paintEvent(self, event):
        """Draw the vertical battery with balancing status dot"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Scale battery dimensions based on widget size
        widget_width = self.width()
        widget_height = self.height()
        
        battery_width = min(35, int(widget_width * 0.6))
        battery_height = min(50, int(widget_height * 0.4))
        x = (widget_width - battery_width) // 2
        y = 3
        tip_height = 5
        tip_width = int(battery_width * 0.4)
        
        # Determine color based on voltage only (same for all cells)
        border_color = QColor(100, 100, 100)
        if self.voltage <= 2.0:
            fill_color = QColor(255, 50, 50)  # Red
            text_color = QColor(255, 100, 100)
        elif self.voltage <= 2.8:
            fill_color = QColor(255, 150, 50)  # Orange
            text_color = QColor(255, 200, 100)
        elif self.voltage <= 3.2:
            fill_color = QColor(255, 255, 50)  # Yellow
            text_color = QColor(255, 255, 100)
        else:
            fill_color = QColor(50, 255, 50)  # Green
            text_color = QColor(100, 255, 100)
        
        # Draw battery tip (positive terminal at top)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        tip_x = x + (battery_width - tip_width) // 2
        painter.drawRect(tip_x, y, tip_width, tip_height)
        
        # Draw battery body outline
        body_y = y + tip_height
        painter.drawRoundedRect(x, body_y, battery_width, battery_height, 4, 4)
        
        # Draw fill based on percentage (fills from bottom up)
        if self.percentage > 0:
            fill_height = int((battery_height - 4) * self.percentage / 100)
            fill_y = body_y + battery_height - 2 - fill_height
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawRoundedRect(x + 2, fill_y, battery_width - 4, fill_height, 2, 2)
        
        # Percentage inside battery
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        percent_text = f"{self.percentage}%"
        text_rect = painter.fontMetrics().boundingRect(percent_text)
        text_x = x + (battery_width - text_rect.width()) // 2
        text_y = body_y + battery_height // 2 + 4
        painter.drawText(text_x, text_y, percent_text)
        
        # Draw cell number below battery
        painter.setPen(QPen(text_color))
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        cell_text = f"C{self.cell_num}"
        text_rect = painter.fontMetrics().boundingRect(cell_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 14
        painter.drawText(text_x, text_y, cell_text)
        
        # Draw voltage below cell number
        font.setPointSize(8)
        painter.setFont(font)
        voltage_text = f"{self.voltage:.2f}V"
        text_rect = painter.fontMetrics().boundingRect(voltage_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 26
        painter.drawText(text_x, text_y, voltage_text)
        
        # Draw balancing status dot below voltage
        dot_y = body_y + battery_height + 34
        dot_radius = 6
        dot_x = widget_width // 2
        
        if self.is_balancing:
            # Green dot for balancing ON
            painter.setPen(QPen(QColor(50, 255, 50), 2))
            painter.setBrush(QBrush(QColor(50, 255, 50)))
        else:
            # Red dot for balancing OFF
            painter.setPen(QPen(QColor(255, 50, 50), 2))
            painter.setBrush(QBrush(QColor(255, 50, 50)))
        
        painter.drawEllipse(dot_x - dot_radius, dot_y, dot_radius * 2, dot_radius * 2)


class BalancingPage(QWidget):
    """Balancing page for cell balancing control"""
    
    # Signals
    balancing_changed = pyqtSignal(int, bool)  # device_id, enable
    balancing_sequence_changed = pyqtSignal(int, int)  # device_id, sequence
    request_balancing_status = pyqtSignal()  # Request to read balancing status from BMS
    
    def __init__(self):
        super().__init__()
        self.current_device_id = 1  # Master BMS
        self.balancing_enabled = False
        self.balancing_state = 0  # 16-bit state
        self.balancing_status = 0  # ON/OFF status (0x0000 or 0x0001)
        self.balancing_read_interval = 2  # Default 2 seconds
        
        # Timer for reading balancing status (only runs when balancing is enabled)
        self.balancing_timer = QTimer()
        self.balancing_timer.timeout.connect(self._request_balancing_status)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the balancing page UI"""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Cell Balancing Control")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Device selection (supports up to 35 slaves)
        device_group = QGroupBox("Device Selection")
        device_group.setMaximumHeight(70)
        device_layout = QHBoxLayout(device_group)
        device_layout.addWidget(QLabel("Select Device:"))
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        # Start with just master - slaves will be added dynamically
        self.device_combo.addItem("Master BMS", 1)
        self.device_combo.currentIndexChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_combo)
        
        self.num_slaves = 0  # Track current number of slaves
        
        device_layout.addStretch()
        layout.addWidget(device_group)
        
        # Top row: Mode, Pattern, and Control (compact)
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Balancing mode selection
        mode_group = QGroupBox("Balancing Mode")
        mode_group.setMaximumHeight(90)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(5)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        
        self.mode_button_group = QButtonGroup()
        
        single_cell_radio = QRadioButton("Single Cell")
        single_cell_radio.setChecked(True)
        self.mode_button_group.addButton(single_cell_radio, 1)
        mode_layout.addWidget(single_cell_radio)
        
        dual_cell_radio = QRadioButton("Dual Cell")
        self.mode_button_group.addButton(dual_cell_radio, 2)
        mode_layout.addWidget(dual_cell_radio)
        
        top_row.addWidget(mode_group)
        
        # Balancing pattern selection
        pattern_group = QGroupBox("Pattern")
        pattern_group.setMaximumHeight(90)
        pattern_layout = QVBoxLayout(pattern_group)
        pattern_layout.setSpacing(5)
        pattern_layout.setContentsMargins(10, 10, 10, 10)
        
        self.pattern_button_group = QButtonGroup()
        
        odd_radio = QRadioButton("Odd Cells")
        odd_radio.setChecked(True)
        self.pattern_button_group.addButton(odd_radio, 1)
        pattern_layout.addWidget(odd_radio)
        
        even_radio = QRadioButton("Even Cells")
        self.pattern_button_group.addButton(even_radio, 2)
        pattern_layout.addWidget(even_radio)
        
        top_row.addWidget(pattern_group)
        
        # Control buttons (horizontal)
        control_group = QGroupBox("Control")
        control_group.setMaximumHeight(90)
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(8)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        self.apply_btn = QPushButton("Apply Pattern")
        self.apply_btn.setMinimumHeight(30)
        self.apply_btn.clicked.connect(self.apply_balancing_pattern)
        control_layout.addWidget(self.apply_btn)
        
        # Single toggle button for Enable/Disable
        self.toggle_btn = QPushButton("Enable Balancing")
        self.toggle_btn.setMinimumHeight(30)
        self.toggle_btn.setMinimumWidth(130)
        self.toggle_btn.clicked.connect(self.toggle_balancing)
        self._update_toggle_button_style()
        control_layout.addWidget(self.toggle_btn)
        
        top_row.addWidget(control_group)
        
        # Read Frequency selector
        freq_group = QGroupBox("Status Read Freq")
        freq_group.setMaximumHeight(90)
        freq_group.setMaximumWidth(150)
        freq_layout = QHBoxLayout(freq_group)
        freq_layout.setSpacing(5)
        freq_layout.setContentsMargins(10, 10, 10, 10)
        
        self.freq_spinbox = QSpinBox()
        self.freq_spinbox.setRange(1, 60)
        self.freq_spinbox.setValue(2)
        self.freq_spinbox.setSuffix(" sec")
        self.freq_spinbox.setMinimumHeight(30)
        self.freq_spinbox.valueChanged.connect(self.on_frequency_changed)
        freq_layout.addWidget(self.freq_spinbox)
        
        top_row.addWidget(freq_group)
        top_row.addStretch()
        
        layout.addLayout(top_row)
        
        # Main visualization section: Battery Icons (left) + Temperature (right)
        viz_section = QHBoxLayout()
        viz_section.setSpacing(10)
        
        # Battery visualization with balancing status
        battery_group = QGroupBox("Cell Voltages & Balancing Status")
        battery_layout = QVBoxLayout(battery_group)
        battery_layout.setContentsMargins(5, 10, 5, 5)
        
        # Legend for balancing status
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(15)
        legend_layout.addStretch()
        
        # Green dot = ON
        green_dot = QLabel("●")
        green_dot.setStyleSheet("color: #32FF32; font-size: 16px;")
        legend_layout.addWidget(green_dot)
        green_label = QLabel("Balancing ON")
        green_label.setStyleSheet("color: #32FF32; font-size: 11px;")
        legend_layout.addWidget(green_label)
        
        legend_layout.addSpacing(20)
        
        # Red dot = OFF
        red_dot = QLabel("●")
        red_dot.setStyleSheet("color: #FF3232; font-size: 16px;")
        legend_layout.addWidget(red_dot)
        red_label = QLabel("Balancing OFF")
        red_label.setStyleSheet("color: #FF3232; font-size: 11px;")
        legend_layout.addWidget(red_label)
        
        legend_layout.addStretch()
        battery_layout.addLayout(legend_layout)
        
        battery_grid = QGridLayout()
        battery_grid.setSpacing(5)
        battery_grid.setContentsMargins(5, 5, 5, 5)
        self.battery_widgets = []
        
        # 8 batteries per row
        for i in range(16):
            battery = BatteryWidget(i + 1)
            self.battery_widgets.append(battery)
            row = i // 8
            col = i % 8
            battery_grid.addWidget(battery, row, col, Qt.AlignmentFlag.AlignCenter)
        
        battery_layout.addLayout(battery_grid)
        battery_layout.addStretch()
        viz_section.addWidget(battery_group, stretch=3)
        
        # Temperature section on the right - vertical layout with optimum space
        temp_group = QGroupBox("Temperatures")
        temp_group.setMinimumWidth(200)
        temp_group.setMaximumWidth(280)
        temp_layout = QVBoxLayout(temp_group)
        temp_layout.setSpacing(8)
        temp_layout.setContentsMargins(12, 12, 12, 12)
        
        self.temp_labels = []
        temp_colors = ['#FF4444', '#FF8844', '#FFFF44', '#44FFFF']
        temp_names = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4']
        
        for i in range(4):
            temp_frame = QFrame()
            temp_frame.setMinimumHeight(50)
            temp_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgb(30, 50, 45);
                    border: 2px solid {temp_colors[i]};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            temp_frame_layout = QHBoxLayout(temp_frame)
            temp_frame_layout.setSpacing(8)
            temp_frame_layout.setContentsMargins(10, 5, 10, 5)
            
            zone_label = QLabel(temp_names[i])
            zone_label.setStyleSheet(f"color: {temp_colors[i]}; font-weight: bold; font-size: 12px;")
            zone_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            temp_frame_layout.addWidget(zone_label)
            
            temp_frame_layout.addStretch()
            
            temp_value = QLabel("-- °C")
            temp_value.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
            temp_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            temp_frame_layout.addWidget(temp_value)
            
            self.temp_labels.append(temp_value)
            temp_layout.addWidget(temp_frame)
        
        # IC Die Temperatures (Die 1 and Die 2)
        die_temp_colors = ['#AA88FF', '#88AAFF']  # Purple shades for die temps
        die_temp_names = ['Die 1', 'Die 2']
        self.die_temp_labels = []
        
        for i in range(2):
            die_frame = QFrame()
            die_frame.setMinimumHeight(50)
            die_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgb(35, 35, 55);
                    border: 2px solid {die_temp_colors[i]};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            die_frame_layout = QHBoxLayout(die_frame)
            die_frame_layout.setSpacing(8)
            die_frame_layout.setContentsMargins(10, 5, 10, 5)
            
            die_label = QLabel(die_temp_names[i])
            die_label.setStyleSheet(f"color: {die_temp_colors[i]}; font-weight: bold; font-size: 12px;")
            die_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            die_frame_layout.addWidget(die_label)
            
            die_frame_layout.addStretch()
            
            die_value = QLabel("-- °C")
            die_value.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
            die_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            die_frame_layout.addWidget(die_value)
            
            self.die_temp_labels.append(die_value)
            temp_layout.addWidget(die_frame)
        
        temp_layout.addStretch()
        viz_section.addWidget(temp_group, stretch=1)
        
        layout.addLayout(viz_section, stretch=1)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def on_device_selection_changed(self, index: int):
        """Handle device selection change from combo box"""
        device_id = self.device_combo.itemData(index)
        self.current_device_id = device_id
        self.update_balancing_indicators()
    
    def update_slave_count(self, num_slaves: int):
        """Update the device combo box based on number of slaves configured"""
        if num_slaves == self.num_slaves:
            return  # No change
        
        current_device = self.device_combo.currentData()
        
        # Block signals to prevent triggering device_selection_changed during update
        self.device_combo.blockSignals(True)
        
        # Clear all items
        self.device_combo.clear()
        
        # Always add master
        self.device_combo.addItem("Master BMS", 1)
        
        # Add only the configured number of slaves
        for i in range(num_slaves):
            self.device_combo.addItem(f"Slave {i+1} (0x{i+2:02X})", i + 2)
        
        self.num_slaves = num_slaves
        
        # Restore selection if the device still exists
        index = self.device_combo.findData(current_device)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
        else:
            # Device no longer exists, reset to master
            self.device_combo.setCurrentIndex(0)
            self.current_device_id = 1
        
        self.device_combo.blockSignals(False)
    
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
        self._update_toggle_button_style()
        
        if self.balancing_enabled:
            # Start the balancing status read timer
            self._start_balancing_timer()
        else:
            # Stop the balancing status read timer
            self._stop_balancing_timer()
            # Set all cells to not balancing (red dots) when disabled
            self.balancing_state = 0
            self.update_balancing_indicators()
    
    def _update_toggle_button_style(self):
        """Update toggle button text and color based on balancing state"""
        if self.balancing_enabled:
            self.toggle_btn.setText("Disable Balancing")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(200, 50, 50);
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgb(220, 70, 70);
                }
            """)
        else:
            self.toggle_btn.setText("Enable Balancing")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(50, 150, 50);
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgb(70, 170, 70);
                }
            """)
    
    def on_frequency_changed(self, value: int):
        """Handle frequency change from spinbox"""
        self.balancing_read_interval = value
        # If timer is running, restart it with new interval
        if self.balancing_timer.isActive():
            self.balancing_timer.setInterval(value * 1000)
    
    def _start_balancing_timer(self):
        """Start the balancing status read timer"""
        interval_ms = self.balancing_read_interval * 1000
        self.balancing_timer.start(interval_ms)
        # Request immediately once when enabled
        self._request_balancing_status()
    
    def _stop_balancing_timer(self):
        """Stop the balancing status read timer"""
        self.balancing_timer.stop()
    
    def _request_balancing_status(self):
        """Emit signal to request balancing status from BMS"""
        self.request_balancing_status.emit()
    
    def update_balancing_state(self, state: int):
        """Update balancing state (cell-wise) from BMS"""
        self.balancing_state = state
        self.update_balancing_indicators()
    
    def update_balancing_enabled(self, enabled: bool):
        """Update balancing enabled status from BMS (Version 0.2)"""
        was_enabled = self.balancing_enabled
        self.balancing_enabled = enabled
        self._update_toggle_button_style()
        
        if enabled:
            # If BMS says balancing is on but our timer isn't running, start it
            if not self.balancing_timer.isActive():
                self._start_balancing_timer()
        else:
            # If BMS says balancing is off, stop the timer and clear indicators
            if self.balancing_timer.isActive():
                self._stop_balancing_timer()
            # Set all cells to not balancing (red dots) when disabled
            self.balancing_state = 0
            self.update_balancing_indicators()
    
    def update_balancing_indicators(self):
        """Update cell balancing indicators based on current state"""
        for i in range(16):
            # Check if bit i is set (cell i is balancing)
            is_balancing = (self.balancing_state >> i) & 1
            
            # Update battery widget balancing status
            if i < len(self.battery_widgets):
                self.battery_widgets[i].set_balancing(bool(is_balancing))
    
    def update_cell_voltages(self, voltages: list):
        """Update cell voltage values in battery widgets"""
        for i, battery in enumerate(self.battery_widgets):
            if i < len(voltages):
                battery.set_voltage(voltages[i])
            else:
                battery.set_voltage(0.0)
    
    def update_temperatures(self, temperatures: list, die_temperatures: list = None):
        """Update temperature values including die temperatures"""
        # Zone temperatures
        for i, label in enumerate(self.temp_labels):
            if i < len(temperatures):
                temp = temperatures[i]
                if temp > 45:
                    color = "#FF4444"
                elif temp > 35:
                    color = "#FFFF44"
                else:
                    color = "#44FF44"
                label.setText(f"{temp:.1f} °C")
                label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
            else:
                label.setText("-- °C")
                label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        
        # Die temperatures
        if die_temperatures and hasattr(self, 'die_temp_labels'):
            for i, label in enumerate(self.die_temp_labels):
                if i < len(die_temperatures):
                    die_temp = die_temperatures[i]
                    color = "#FF4444" if die_temp > 80 else ("#FFFF44" if die_temp > 60 else "#44FF44")
                    label.setText(f"{die_temp:.1f} °C")
                    label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
                else:
                    label.setText("-- °C")
                    label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
