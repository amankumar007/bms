"""
Master Page Component - Main BMS monitoring and control page
Uses tabs for each BMS device (Master + Slaves)
Includes battery indicators for cell voltages
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox, QSpinBox, QGridLayout, QFrame,
    QTabWidget, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from typing import Optional, Dict


class BatteryWidget(QWidget):
    """Custom vertical battery indicator widget"""
    
    def __init__(self, cell_num: int = 1):
        super().__init__()
        self.cell_num = cell_num
        self.voltage = 0.0
        self.percentage = 0
        self.setFixedSize(90, 160)
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
    
    def paintEvent(self, event):
        """Draw the vertical battery"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Battery dimensions (vertical orientation)
        widget_width = self.width()
        battery_width = 50
        battery_height = 80
        x = (widget_width - battery_width) // 2
        y = 5
        tip_height = 8
        tip_width = 20
        
        # Determine color based on voltage
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
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        tip_x = x + (battery_width - tip_width) // 2
        painter.drawRect(tip_x, y, tip_width, tip_height)
        
        # Draw battery body outline
        body_y = y + tip_height
        painter.drawRoundedRect(x, body_y, battery_width, battery_height, 6, 6)
        
        # Draw fill based on percentage (fills from bottom up)
        if self.percentage > 0:
            fill_height = int((battery_height - 6) * self.percentage / 100)
            fill_y = body_y + battery_height - 3 - fill_height
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawRoundedRect(x + 3, fill_y, battery_width - 6, fill_height, 3, 3)
        
        # Percentage inside battery
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        percent_text = f"{self.percentage}%"
        text_rect = painter.fontMetrics().boundingRect(percent_text)
        text_x = x + (battery_width - text_rect.width()) // 2
        text_y = body_y + battery_height // 2 + 5
        painter.drawText(text_x, text_y, percent_text)
        
        # Draw cell number below battery
        painter.setPen(QPen(text_color))
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        cell_text = f"C{self.cell_num}"
        text_rect = painter.fontMetrics().boundingRect(cell_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 22
        painter.drawText(text_x, text_y, cell_text)
        
        # Draw voltage below cell number
        font.setPointSize(13)
        painter.setFont(font)
        voltage_text = f"{self.voltage:.2f}V"
        text_rect = painter.fontMetrics().boundingRect(voltage_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 42
        painter.drawText(text_x, text_y, voltage_text)


class MasterPage(QWidget):
    """Master page for BMS monitoring and control with tabbed BMS views"""
    
    # Signals
    connect_requested = pyqtSignal(str)  # Emits port name
    disconnect_requested = pyqtSignal()
    num_slaves_changed = pyqtSignal(int)
    num_cells_changed = pyqtSignal(int)
    refresh_ports_requested = pyqtSignal()
    
    MAX_SLAVES = 35
    
    def __init__(self):
        super().__init__()
        self.is_connected = False
        self.slave_tabs: Dict[int, QWidget] = {}
        self.slave_tab_indices: Dict[int, int] = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the master page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Top section: Connection and Configuration
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)
        
        # Connection section
        connection_group = QGroupBox("Connection")
        connection_layout = QVBoxLayout(connection_group)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("COM Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports_requested.emit)
        port_layout.addWidget(refresh_btn)
        connection_layout.addLayout(port_layout)
        
        # Connection button
        self.connect_btn = QPushButton("Connect to Master BMS")
        self.connect_btn.setFixedHeight(35)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        connection_layout.addWidget(self.connect_btn)
        
        top_layout.addWidget(connection_group)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Number of Slaves:"), 0, 0)
        self.num_slaves_spin = QSpinBox()
        self.num_slaves_spin.setRange(0, self.MAX_SLAVES)
        self.num_slaves_spin.setValue(0)
        self.num_slaves_spin.valueChanged.connect(self.on_num_slaves_changed)
        config_layout.addWidget(self.num_slaves_spin, 0, 1)
        
        config_layout.addWidget(QLabel("Number of Cells (Top BMS):"), 1, 0)
        self.num_cells_spin = QSpinBox()
        self.num_cells_spin.setRange(0, 16)
        self.num_cells_spin.setValue(16)
        self.num_cells_spin.valueChanged.connect(self.on_num_cells_changed)
        config_layout.addWidget(self.num_cells_spin, 1, 1)
        
        top_layout.addWidget(config_group)
        top_layout.addStretch()
        
        layout.addWidget(top_section)
        
        # BMS Data Tabs
        self.bms_tabs = QTabWidget()
        self.bms_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid rgb(2, 44, 34);
                border-radius: 8px;
                background-color: rgb(15, 35, 30);
            }
            QTabBar::tab {
                background-color: rgb(25, 50, 45);
                color: rgb(200, 220, 200);
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: rgb(34, 139, 34);
                color: rgb(15, 25, 20);
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgb(40, 80, 70);
            }
            QTabBar::scroller { width: 40px; }
        """)
        self.bms_tabs.setTabsClosable(False)
        self.bms_tabs.setMovable(False)
        self.bms_tabs.setUsesScrollButtons(True)
        
        # Create Master BMS tab
        self.master_tab = self._create_bms_tab("Master BMS", is_master=True)
        self.bms_tabs.addTab(self.master_tab, "Master BMS")
        
        layout.addWidget(self.bms_tabs)
    
    def _create_bms_tab(self, name: str, is_master: bool = False) -> QWidget:
        """Create a tab widget for displaying BMS data with battery indicators"""
        tab = QWidget()
        
        # Use scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        tab_layout = QVBoxLayout(content)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(10)
        
        # Title
        title = QLabel(name)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: rgb(50, 205, 50); padding: 5px;")
        tab_layout.addWidget(title)
        
        if is_master:
            # Pack voltage and current (only for master)
            pack_group = QGroupBox("Pack Data")
            pack_layout = QHBoxLayout(pack_group)
            
            tab.pack_voltage_label = QLabel("Pack Voltage: -- V")
            tab.pack_voltage_label.setStyleSheet("font-size: 16px; font-weight: bold; color: rgb(100, 255, 100);")
            pack_layout.addWidget(tab.pack_voltage_label)
            
            tab.pack_current_label = QLabel("Pack Current: -- A")
            tab.pack_current_label.setStyleSheet("font-size: 16px; font-weight: bold; color: rgb(255, 200, 100);")
            pack_layout.addWidget(tab.pack_current_label)
            pack_layout.addStretch()
            
            tab_layout.addWidget(pack_group)
        
        # Cell voltages with battery indicators
        voltage_group = QGroupBox("Cell Voltages (2V=0%, 5V=100%)")
        voltage_layout = QVBoxLayout(voltage_group)
        
        battery_grid = QGridLayout()
        battery_grid.setSpacing(10)
        battery_grid.setContentsMargins(10, 10, 10, 10)
        tab.battery_widgets = []
        
        # 8 batteries per row for vertical layout
        for i in range(16):
            battery = BatteryWidget(i + 1)
            tab.battery_widgets.append(battery)
            row = i // 8
            col = i % 8
            battery_grid.addWidget(battery, row, col, Qt.AlignmentFlag.AlignCenter)
        
        voltage_layout.addLayout(battery_grid)
        tab_layout.addWidget(voltage_group)
        
        # Temperatures
        temp_group = QGroupBox("Temperatures")
        temp_layout = QHBoxLayout(temp_group)
        
        tab.temp_labels = []
        temp_colors = ['#FF4444', '#FF8844', '#FFFF44', '#44FFFF']
        for i in range(4):
            temp_frame = QFrame()
            temp_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgb(30, 50, 45);
                    border: 2px solid {temp_colors[i]};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            temp_frame_layout = QVBoxLayout(temp_frame)
            
            zone_label = QLabel(f"Zone {i+1}")
            zone_label.setStyleSheet(f"color: {temp_colors[i]}; font-weight: bold;")
            zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            temp_frame_layout.addWidget(zone_label)
            
            temp_value = QLabel("-- °C")
            temp_value.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
            temp_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            temp_frame_layout.addWidget(temp_value)
            
            tab.temp_labels.append(temp_value)
            temp_layout.addWidget(temp_frame)
        
        temp_layout.addStretch()
        tab_layout.addWidget(temp_group)
        
        tab_layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        return tab
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        if self.is_connected:
            self.disconnect_requested.emit()
        else:
            port = self.port_combo.currentText()
            if port:
                self.connect_requested.emit(port)
    
    def on_num_slaves_changed(self, value: int):
        """Handle number of slaves changed - create/remove tabs"""
        self.num_slaves_changed.emit(value)
        self._update_slave_tabs(value)
    
    def _update_slave_tabs(self, num_slaves: int):
        """Update slave tabs based on number of slaves"""
        current_slave_count = len(self.slave_tabs)
        
        # Add new slave tabs
        for i in range(current_slave_count, num_slaves):
            slave_id = i + 2
            slave_name = f"Slave {i+1}"
            tab = self._create_bms_tab(slave_name, is_master=False)
            tab_index = self.bms_tabs.addTab(tab, slave_name)
            self.slave_tabs[slave_id] = tab
            self.slave_tab_indices[slave_id] = tab_index
        
        # Remove excess slave tabs
        for i in range(current_slave_count - 1, num_slaves - 1, -1):
            slave_id = i + 2
            if slave_id in self.slave_tabs:
                tab_index = self.slave_tab_indices.pop(slave_id)
                self.bms_tabs.removeTab(tab_index)
                del self.slave_tabs[slave_id]
                for sid, idx in self.slave_tab_indices.items():
                    if idx > tab_index:
                        self.slave_tab_indices[sid] = idx - 1
    
    def on_num_cells_changed(self, value: int):
        """Handle number of cells changed"""
        self.num_cells_changed.emit(value)
    
    def set_ports(self, ports: list):
        """Set available COM ports"""
        self.port_combo.clear()
        self.port_combo.addItems(ports)
    
    def set_connected(self, connected: bool):
        """Update connection status"""
        self.is_connected = connected
        if connected:
            self.connect_btn.setText("Disconnect from Master BMS")
            self.connect_btn.setStyleSheet("background-color: rgb(200, 50, 50);")
        else:
            self.connect_btn.setText("Connect to Master BMS")
            self.connect_btn.setStyleSheet("")
    
    def update_data(self, data: dict):
        """Update displayed data"""
        # Update Master BMS tab
        pack_voltage = data.get('pack_voltage', 0.0)
        pack_current = data.get('pack_current', 0.0)
        
        if hasattr(self.master_tab, 'pack_voltage_label'):
            self.master_tab.pack_voltage_label.setText(f"Pack Voltage: {pack_voltage:.3f} V")
        if hasattr(self.master_tab, 'pack_current_label'):
            self.master_tab.pack_current_label.setText(f"Pack Current: {pack_current:.3f} A")
        
        # Master cell voltages - update battery widgets
        master_voltages = data.get('master_cell_voltages', [])
        if hasattr(self.master_tab, 'battery_widgets'):
            for i, battery in enumerate(self.master_tab.battery_widgets):
                if i < len(master_voltages):
                    battery.set_voltage(master_voltages[i])
                else:
                    battery.set_voltage(0.0)
        
        # Master temperatures
        master_temps = data.get('master_temperatures', [])
        for i, label in enumerate(self.master_tab.temp_labels):
            if i < len(master_temps):
                temp = master_temps[i]
                if temp > 45:
                    color = "#FF4444"
                elif temp > 35:
                    color = "#FFFF44"
                else:
                    color = "#44FF44"
                label.setText(f"{temp:.1f} °C")
                label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
            else:
                label.setText("-- °C")
                label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        # Update slave tabs
        slave_data = data.get('slave_data', {})
        for slave_id, tab in self.slave_tabs.items():
            if slave_id in slave_data:
                slave_info = slave_data[slave_id]
                
                # Voltages - update battery widgets
                voltages = slave_info.get('voltages', [])
                if hasattr(tab, 'battery_widgets'):
                    for i, battery in enumerate(tab.battery_widgets):
                        if i < len(voltages):
                            battery.set_voltage(voltages[i])
                        else:
                            battery.set_voltage(0.0)
                
                # Temperatures
                temperatures = slave_info.get('temperatures', [])
                for i, label in enumerate(tab.temp_labels):
                    if i < len(temperatures):
                        temp = temperatures[i]
                        if temp > 45:
                            color = "#FF4444"
                        elif temp > 35:
                            color = "#FFFF44"
                        else:
                            color = "#44FF44"
                        label.setText(f"{temp:.1f} °C")
                        label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
                    else:
                        label.setText("-- °C")
                        label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
            else:
                # No data - reset to default
                if hasattr(tab, 'battery_widgets'):
                    for battery in tab.battery_widgets:
                        battery.set_voltage(0.0)
                for label in tab.temp_labels:
                    label.setText("-- °C")
                    label.setStyleSheet("font-size: 18px; font-weight: bold; color: #888;")
