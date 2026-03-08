"""
Balancing Page Component - Cell balancing control
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGridLayout, QFrame,
    QComboBox, QScrollArea, QSizePolicy, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush

from src.utils.message_box import StyledMessageBox


class BatteryWidget(QWidget):
    """Custom vertical battery indicator widget for balancing page.

    Visual indicators:
      - Blue border on battery body → cell is CONFIGURED for balancing (what you sent)
      - Green dot  → BMS REPORTS this cell is actually balancing
      - Red dot    → BMS REPORTS this cell is NOT balancing
    """

    COLOR_CONFIGURED = QColor(60, 140, 255)   # blue – "you asked for this"
    COLOR_BAL_ON     = QColor(50, 255, 50)     # green – BMS says ON
    COLOR_BAL_OFF    = QColor(255, 50, 50)     # red   – BMS says OFF

    def __init__(self, cell_num: int = 1):
        super().__init__()
        self.cell_num = cell_num
        self.voltage = 0.0
        self.percentage = 0
        self.is_balancing = False
        self.is_configured = False
        self.setMinimumSize(55, 115)
        self.setMaximumSize(80, 145)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background-color: transparent;")

    def set_voltage(self, voltage: float):
        """Set voltage and calculate percentage (0-5V range, 2V min useful)"""
        self.voltage = voltage
        if voltage <= 2.0:
            self.percentage = 0
        elif voltage >= 5.0:
            self.percentage = 100
        else:
            self.percentage = int(((voltage - 2.0) / 3.0) * 100)
        self.update()

    def set_balancing(self, is_balancing: bool):
        """Set BMS-reported balancing status (green/red dot)"""
        self.is_balancing = is_balancing
        self.update()

    def set_configured(self, configured: bool):
        """Set whether this cell was CONFIGURED for balancing (blue border)"""
        self.is_configured = configured
        self.update()

    def paintEvent(self, event):
        """Draw battery with configured-border and BMS-state dot"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        widget_width = self.width()
        widget_height = self.height()

        battery_width = min(35, int(widget_width * 0.6))
        battery_height = min(50, int(widget_height * 0.4))
        x = (widget_width - battery_width) // 2
        y = 3
        tip_height = 5
        tip_width = int(battery_width * 0.4)

        if self.voltage <= 2.0:
            fill_color = QColor(255, 50, 50)
            text_color = QColor(255, 100, 100)
        elif self.voltage <= 2.8:
            fill_color = QColor(255, 150, 50)
            text_color = QColor(255, 200, 100)
        elif self.voltage <= 3.2:
            fill_color = QColor(255, 255, 50)
            text_color = QColor(255, 255, 100)
        else:
            fill_color = QColor(50, 255, 50)
            text_color = QColor(100, 255, 100)

        # Battery border: blue if configured, grey otherwise
        border_color = self.COLOR_CONFIGURED if self.is_configured else QColor(100, 100, 100)
        border_width = 3 if self.is_configured else 2

        # Tip
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        tip_x = x + (battery_width - tip_width) // 2
        painter.drawRect(tip_x, y, tip_width, tip_height)

        # Body
        body_y = y + tip_height
        painter.drawRoundedRect(x, body_y, battery_width, battery_height, 4, 4)

        # Fill
        if self.percentage > 0:
            fill_height = int((battery_height - 4) * self.percentage / 100)
            fill_y = body_y + battery_height - 2 - fill_height
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawRoundedRect(x + 2, fill_y, battery_width - 4, fill_height, 2, 2)

        # Percentage text
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

        # Cell label
        painter.setPen(QPen(text_color))
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        cell_text = f"C{self.cell_num}"
        text_rect = painter.fontMetrics().boundingRect(cell_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 14
        painter.drawText(text_x, text_y, cell_text)

        # Voltage text
        font.setPointSize(8)
        painter.setFont(font)
        voltage_text = f"{self.voltage:.2f}V"
        text_rect = painter.fontMetrics().boundingRect(voltage_text)
        text_x = (widget_width - text_rect.width()) // 2
        text_y = body_y + battery_height + 26
        painter.drawText(text_x, text_y, voltage_text)

        # BMS-state dot (green = ON, red = OFF)
        dot_y = body_y + battery_height + 34
        dot_radius = 6
        dot_x = widget_width // 2

        dot_color = self.COLOR_BAL_ON if self.is_balancing else self.COLOR_BAL_OFF
        painter.setPen(QPen(dot_color, 2))
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(dot_x - dot_radius, dot_y, dot_radius * 2, dot_radius * 2)


class BalancingPage(QWidget):
    """Balancing page for cell balancing control"""
    
    # Signals
    balancing_changed = pyqtSignal(int, bool)  # device_id, enable
    balancing_sequence_changed = pyqtSignal(int, int)  # device_id, sequence
    request_balancing_status = pyqtSignal()

    BALANCING_MODE_ODD = 1
    BALANCING_MODE_EVEN = 2
    BALANCING_MODE_CUSTOM = 3
    
    def __init__(self):
        super().__init__()
        self.current_device_id = 1
        self.balancing_enabled = False
        self.balancing_state = 0
        self.balancing_status = 0
        self.balancing_read_interval = 2

        # Per-device UI state: {device_id: {'mode': int, 'custom_cells': [bool]*16}}
        self.device_ui_state = {}
        
        self.balancing_timer = QTimer()
        self.balancing_timer.timeout.connect(self._request_balancing_status)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the balancing page UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel("Cell Balancing Control")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Device selection
        device_group = QGroupBox("Device Selection")
        device_group.setMaximumHeight(70)
        device_layout = QHBoxLayout(device_group)
        device_layout.addWidget(QLabel("Select Device:"))
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        self.device_combo.addItem("Master BMS", 1)
        self.device_combo.currentIndexChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_combo)
        
        self.num_slaves = 0
        
        device_layout.addStretch()
        layout.addWidget(device_group)
        
        # Top row: Mode, Cell Selection, Control, Read Freq
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Balancing mode selection (Odd / Even / Custom)
        mode_group = QGroupBox("Balancing Mode")
        mode_group.setMaximumHeight(160)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(5)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        
        self.mode_button_group = QButtonGroup()
        
        odd_radio = QRadioButton("Odd Cells (C1,C3,C5,...)")
        odd_radio.setChecked(True)
        self.mode_button_group.addButton(odd_radio, self.BALANCING_MODE_ODD)
        mode_layout.addWidget(odd_radio)
        
        even_radio = QRadioButton("Even Cells (C2,C4,C6,...)")
        self.mode_button_group.addButton(even_radio, self.BALANCING_MODE_EVEN)
        mode_layout.addWidget(even_radio)
        
        custom_radio = QRadioButton("Custom Selection")
        self.mode_button_group.addButton(custom_radio, self.BALANCING_MODE_CUSTOM)
        mode_layout.addWidget(custom_radio)
        
        self.mode_button_group.idClicked.connect(self._on_mode_changed)
        
        top_row.addWidget(mode_group)
        
        # Cell selection checkboxes (2 rows x 8 columns)
        cell_group = QGroupBox("Cell Selection")
        cell_group.setMaximumHeight(160)
        cell_grid = QGridLayout(cell_group)
        cell_grid.setSpacing(4)
        cell_grid.setContentsMargins(8, 10, 8, 10)
        
        self.cell_checkboxes: list[QCheckBox] = []
        for i in range(16):
            cb = QCheckBox(f"C{i + 1}")
            cb.setEnabled(False)
            cb.setStyleSheet(self._checkbox_style(enabled=False))
            self.cell_checkboxes.append(cb)
            row = i // 8
            col = i % 8
            cell_grid.addWidget(cb, row, col)
        
        self._update_checkboxes_for_mode(self.BALANCING_MODE_ODD)
        
        top_row.addWidget(cell_group)
        
        # Control buttons + status
        control_group = QGroupBox("Control")
        control_group.setMaximumHeight(160)
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        self.apply_btn = QPushButton("Apply Config")
        self.apply_btn.setMinimumHeight(30)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 100, 180);
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgb(70, 120, 200);
            }
        """)
        self.apply_btn.clicked.connect(self.apply_balancing_config)
        control_layout.addWidget(self.apply_btn)
        
        self.toggle_btn = QPushButton("Enable Balancing")
        self.toggle_btn.setMinimumHeight(30)
        self.toggle_btn.setMinimumWidth(150)
        self.toggle_btn.clicked.connect(self.toggle_balancing)
        self._update_toggle_button_style()
        control_layout.addWidget(self.toggle_btn)
        
        self.config_status_label = QLabel("Config: Not applied")
        self.config_status_label.setStyleSheet(
            "color: rgb(150, 150, 150); font-size: 10px; padding: 2px;"
        )
        self.config_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.config_status_label.setWordWrap(True)
        control_layout.addWidget(self.config_status_label)
        
        top_row.addWidget(control_group)
        
        # Read frequency selector
        freq_group = QGroupBox("Status Read Freq")
        freq_group.setMaximumHeight(160)
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
        
        # Visualization section: Battery Icons (left) + Temperature (right)
        viz_section = QHBoxLayout()
        viz_section.setSpacing(10)
        
        battery_group = QGroupBox("Cell Voltages & Balancing Status")
        battery_layout = QVBoxLayout(battery_group)
        battery_layout.setContentsMargins(5, 10, 5, 5)
        
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        legend_layout.addStretch()

        blue_box = QLabel("▮")
        blue_box.setStyleSheet("color: #3C8CFF; font-size: 14px;")
        legend_layout.addWidget(blue_box)
        blue_label = QLabel("Configured (sent)")
        blue_label.setStyleSheet("color: #3C8CFF; font-size: 11px;")
        legend_layout.addWidget(blue_label)

        legend_layout.addSpacing(15)

        green_dot = QLabel("●")
        green_dot.setStyleSheet("color: #32FF32; font-size: 16px;")
        legend_layout.addWidget(green_dot)
        green_label = QLabel("BMS: ON")
        green_label.setStyleSheet("color: #32FF32; font-size: 11px;")
        legend_layout.addWidget(green_label)

        legend_layout.addSpacing(15)

        red_dot = QLabel("●")
        red_dot.setStyleSheet("color: #FF3232; font-size: 16px;")
        legend_layout.addWidget(red_dot)
        red_label = QLabel("BMS: OFF")
        red_label.setStyleSheet("color: #FF3232; font-size: 11px;")
        legend_layout.addWidget(red_label)

        legend_layout.addStretch()
        battery_layout.addLayout(legend_layout)
        
        battery_grid = QGridLayout()
        battery_grid.setSpacing(5)
        battery_grid.setContentsMargins(5, 5, 5, 5)
        self.battery_widgets = []
        
        for i in range(16):
            battery = BatteryWidget(i + 1)
            self.battery_widgets.append(battery)
            row = i // 8
            col = i % 8
            battery_grid.addWidget(battery, row, col, Qt.AlignmentFlag.AlignCenter)
        
        battery_layout.addLayout(battery_grid)
        battery_layout.addStretch()
        viz_section.addWidget(battery_group, stretch=3)
        
        # Temperature section
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
        
        # IC Die Temperatures
        die_temp_colors = ['#AA88FF', '#88AAFF']
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

    # ── Mode / cell-selection helpers ────────────────────────────────

    @staticmethod
    def _checkbox_style(enabled: bool) -> str:
        """Return stylesheet that keeps checked indicators clearly visible."""
        if enabled:
            return """
                QCheckBox { color: white; spacing: 4px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QCheckBox::indicator:unchecked {
                    border: 2px solid rgb(120,120,120);
                    border-radius: 3px;
                    background: rgb(40,40,40);
                }
                QCheckBox::indicator:checked {
                    border: 2px solid rgb(80,200,80);
                    border-radius: 3px;
                    background: rgb(50,180,50);
                    image: none;
                }
            """
        return """
            QCheckBox { color: rgb(180,180,180); spacing: 4px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:unchecked {
                border: 2px solid rgb(80,80,80);
                border-radius: 3px;
                background: rgb(35,35,35);
            }
            QCheckBox::indicator:checked {
                border: 2px solid rgb(60,160,60);
                border-radius: 3px;
                background: rgb(40,140,40);
                image: none;
            }
        """

    def _on_mode_changed(self, mode_id: int):
        """Handle balancing mode radio button change"""
        self._update_checkboxes_for_mode(mode_id)

    def _update_checkboxes_for_mode(self, mode_id: int):
        """Set checkbox checked-state and enabled-state based on mode."""
        is_custom = mode_id == self.BALANCING_MODE_CUSTOM
        style = self._checkbox_style(enabled=is_custom)

        if mode_id == self.BALANCING_MODE_ODD:
            for i, cb in enumerate(self.cell_checkboxes):
                cb.setEnabled(False)
                cb.setChecked(i % 2 == 0)  # bits 0,2,4,… → C1,C3,C5,…
                cb.setStyleSheet(style)
        elif mode_id == self.BALANCING_MODE_EVEN:
            for i, cb in enumerate(self.cell_checkboxes):
                cb.setEnabled(False)
                cb.setChecked(i % 2 == 1)  # bits 1,3,5,… → C2,C4,C6,…
                cb.setStyleSheet(style)
        elif mode_id == self.BALANCING_MODE_CUSTOM:
            state = self.device_ui_state.get(self.current_device_id, {})
            custom_cells = state.get('custom_cells', [False] * 16)
            for i, cb in enumerate(self.cell_checkboxes):
                cb.setEnabled(True)
                cb.setChecked(custom_cells[i])
                cb.setStyleSheet(style)

    def _get_selected_sequence(self) -> int:
        """Build 16-bit balancing sequence from current checkbox states."""
        sequence = 0
        for i, cb in enumerate(self.cell_checkboxes):
            if cb.isChecked():
                sequence |= (1 << i)
        return sequence

    def _find_adjacent_selected(self) -> list[tuple[int, int]]:
        """Return list of 1-indexed adjacent cell pairs that are both selected."""
        pairs = []
        for i in range(15):
            if self.cell_checkboxes[i].isChecked() and self.cell_checkboxes[i + 1].isChecked():
                pairs.append((i + 1, i + 2))
        return pairs

    # ── Per-device UI state ──────────────────────────────────────────

    def _save_current_device_state(self):
        """Persist the current mode + custom cells for the active device."""
        mode = self.mode_button_group.checkedId()
        entry = self.device_ui_state.setdefault(self.current_device_id, {})
        entry['mode'] = mode
        if mode == self.BALANCING_MODE_CUSTOM:
            entry['custom_cells'] = [cb.isChecked() for cb in self.cell_checkboxes]

    def _restore_device_state(self, device_id: int):
        """Restore UI to the stored state for *device_id* (defaults to Odd)."""
        state = self.device_ui_state.get(device_id, {})
        mode = state.get('mode', self.BALANCING_MODE_ODD)
        button = self.mode_button_group.button(mode)
        if button:
            button.setChecked(True)
        self._update_checkboxes_for_mode(mode)

    # ── Device selection ─────────────────────────────────────────────

    def on_device_selection_changed(self, index: int):
        """Handle device selection change from combo box"""
        self._save_current_device_state()

        device_id = self.device_combo.itemData(index)
        self.current_device_id = device_id

        self._restore_device_state(device_id)
        self.update_balancing_indicators()
    
    def update_slave_count(self, num_slaves: int):
        """Update the device combo box based on number of slaves configured"""
        if num_slaves == self.num_slaves:
            return
        
        current_device = self.device_combo.currentData()
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.addItem("Master BMS", 1)
        
        for i in range(num_slaves):
            self.device_combo.addItem(f"Slave {i+1} (0x{i+2:02X})", i + 2)
        
        self.num_slaves = num_slaves
        
        index = self.device_combo.findData(current_device)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
        else:
            self.device_combo.setCurrentIndex(0)
            self.current_device_id = 1
        
        self.device_combo.blockSignals(False)

    # ── Apply / Enable / Disable ─────────────────────────────────────

    def apply_balancing_config(self):
        """Validate cell selection and send the configuration sequence.

        This only sets the balancing *pattern* on the BMS – it does NOT
        enable balancing.  Use the Enable/Disable toggle for that.
        """
        adjacent = self._find_adjacent_selected()
        if adjacent:
            pairs_str = ", ".join(f"C{a}–C{b}" for a, b in adjacent)
            StyledMessageBox.warning(
                self,
                "Invalid Cell Selection",
                f"Continuous (adjacent) cells are selected:\n{pairs_str}\n\n"
                "No two adjacent cells may be selected for balancing.\n"
                "Please deselect one cell from each adjacent pair.",
            )
            return

        sequence = self._get_selected_sequence()
        if sequence == 0:
            StyledMessageBox.warning(
                self,
                "No Cells Selected",
                "Please select at least one cell before applying.",
            )
            return

        self._save_current_device_state()
        self.balancing_sequence_changed.emit(self.current_device_id, sequence)

    def notify_config_result(
        self, success: bool, sequence: int = 0, readback: int | None = None
    ):
        """Called by MainWindow after BMS communication to show apply result.

        Args:
            success:  True if the write command succeeded.
            sequence: 16-bit sequence that was sent to the BMS.
            readback: 16-bit value read back from the BMS (§3.8.4), or None.
        """
        if not success:
            self.config_status_label.setText("Config: FAILED to apply!")
            self.config_status_label.setStyleSheet(
                "color: rgb(255, 80, 80); font-size: 10px; font-weight: bold; padding: 2px;"
            )
            return

        # Show blue borders on the cells the user configured
        self.update_configured_cells(sequence)

        sent_cells = [f"C{i+1}" for i in range(16) if (sequence >> i) & 1]
        sent_str = ", ".join(sent_cells) if len(sent_cells) <= 8 else (
            ", ".join(sent_cells[:6]) + f" ... ({len(sent_cells)} cells)"
        )

        if readback is not None and readback != sequence:
            rb_cells = [f"C{i+1}" for i in range(16) if (readback >> i) & 1]
            rb_str = ", ".join(rb_cells) if rb_cells else "none"
            self.config_status_label.setText(
                f"Sent: {sent_str} (0x{sequence:04X})\n"
                f"BMS reports: {rb_str} (0x{readback:04X})"
            )
            self.config_status_label.setStyleSheet(
                "color: rgb(255, 200, 60); font-size: 10px; font-weight: bold; padding: 2px;"
            )
        else:
            self.config_status_label.setText(
                f"Applied: {sent_str}\n(0x{sequence:04X})"
            )
            self.config_status_label.setStyleSheet(
                "color: rgb(80, 255, 80); font-size: 10px; font-weight: bold; padding: 2px;"
            )

    def toggle_balancing(self):
        """Toggle balancing on/off with the current config"""
        self.balancing_enabled = not self.balancing_enabled
        self.balancing_changed.emit(self.current_device_id, self.balancing_enabled)
        self._update_toggle_button_style()
        
        if self.balancing_enabled:
            self._start_balancing_timer()
        else:
            self._stop_balancing_timer()
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

    # ── Timer / status reading ───────────────────────────────────────

    def on_frequency_changed(self, value: int):
        """Handle frequency change from spinbox"""
        self.balancing_read_interval = value
        if self.balancing_timer.isActive():
            self.balancing_timer.setInterval(value * 1000)
    
    def _start_balancing_timer(self):
        interval_ms = self.balancing_read_interval * 1000
        self.balancing_timer.start(interval_ms)
        self._request_balancing_status()
    
    def _stop_balancing_timer(self):
        self.balancing_timer.stop()
    
    def _request_balancing_status(self):
        self.request_balancing_status.emit()

    # ── External data updates ────────────────────────────────────────

    def update_balancing_state(self, state: int):
        """Update balancing state (cell-wise) from BMS"""
        self.balancing_state = state
        self.update_balancing_indicators()
    
    def update_balancing_enabled(self, enabled: bool):
        """Update balancing enabled status from BMS"""
        self.balancing_enabled = enabled
        self._update_toggle_button_style()
        
        if enabled:
            if not self.balancing_timer.isActive():
                self._start_balancing_timer()
        else:
            if self.balancing_timer.isActive():
                self._stop_balancing_timer()
            self.balancing_state = 0
            self.update_balancing_indicators()
    
    def update_balancing_indicators(self):
        """Update cell balancing indicators based on current BMS-reported state"""
        for i in range(16):
            is_balancing = (self.balancing_state >> i) & 1
            if i < len(self.battery_widgets):
                self.battery_widgets[i].set_balancing(bool(is_balancing))

    def update_configured_cells(self, sequence: int):
        """Mark cells that were configured for balancing (blue border).

        Args:
            sequence: 16-bit bitmask of cells the user sent to the BMS.
                      Pass 0 to clear all configured indicators.
        """
        for i in range(16):
            if i < len(self.battery_widgets):
                self.battery_widgets[i].set_configured(bool((sequence >> i) & 1))
    
    def update_cell_voltages(self, voltages: list):
        """Update cell voltage values in battery widgets"""
        for i, battery in enumerate(self.battery_widgets):
            if i < len(voltages):
                battery.set_voltage(voltages[i])
            else:
                battery.set_voltage(0.0)
    
    def update_temperatures(self, temperatures: list, die_temperatures: list = None):
        """Update temperature values including die temperatures"""
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
