"""
Main Window for BMS Monitor App V2
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStatusBar, QLabel, QFrame, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from src.components.nav_bar import NavBar
from src.components.master_page import MasterPage
from src.components.plot_page import PlotPage
from src.components.balancing_page import BalancingPage
from src.components.debug_page import DebugPage
from src.components.console_page import ConsolePage
from src.data.bms_connection import BMSConnection
from src.utils.logger import get_logger
from src.utils.message_box import StyledMessageBox


class MainWindow(QMainWindow):
    """Main application window with sidebar and content panels"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BMS Monitor App V2")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 700)  # Minimum window size
        
        # Initialize logger
        self.logger = get_logger()
        self.logger.log_app("INFO", "BMS Monitor App V2 starting...")
        
        # Initialize BMS connection
        self.bms_connection = BMSConnection()
        
        # Track current connection info
        self.current_port = ""
        self.num_slaves = 0
        self.num_cells = 0
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        self.setup_connections()
        
        # Refresh ports on startup
        self.refresh_ports()
        self.logger.log_app("INFO", "Application initialized successfully")
        
    def setup_ui(self):
        """Setup the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout (top bar + content)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create top status bar
        self.top_status_bar = self.create_top_status_bar()
        main_layout.addWidget(self.top_status_bar)
        
        # Create horizontal navigation bar (replaces sidebar)
        self.nav_bar = NavBar()
        self.nav_bar.page_changed.connect(self.on_page_changed)
        main_layout.addWidget(self.nav_bar)
        
        # Content area (full width for pages)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(0)
        
        # Page container (direct, no scroll - pages handle their own scrolling)
        self.page_container = QWidget()
        self.page_container_layout = QVBoxLayout(self.page_container)
        self.page_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create pages
        self.master_page = MasterPage()
        self.plot_page = PlotPage()
        self.balancing_page = BalancingPage()
        self.debug_page = DebugPage()
        self.console_page = ConsolePage()
        
        # Store all pages in a dictionary for easy access
        self.pages = {
            "Master": self.master_page,
            "Graph/Plotting": self.plot_page,
            "Balancing": self.balancing_page,
            "Debugging": self.debug_page,
            "Console": self.console_page
        }
        
        # Initially show master page
        self.current_page = self.master_page
        self.page_container_layout.addWidget(self.current_page)
        
        content_layout.addWidget(self.page_container)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
    
    def create_top_status_bar(self) -> QWidget:
        """Create the top status bar with global parameters"""
        status_widget = QWidget()
        status_widget.setFixedHeight(50)
        status_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(15, 35, 30);
                border-bottom: 2px solid rgb(2, 44, 34);
            }
            QLabel {
                color: rgb(240, 248, 255);
                font-size: 12px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("BMS Development Utility")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator1)
        
        # Number of slaves
        self.slaves_label = QLabel("No. of slaves: --")
        layout.addWidget(self.slaves_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator2)
        
        # Number of cells in top BMS
        self.cells_label = QLabel("No. of cells in top BMS: --")
        layout.addWidget(self.cells_label)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.VLine)
        separator3.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator3)
        
        # COM Port
        self.port_label = QLabel("COM Port: --")
        layout.addWidget(self.port_label)
        
        # Separator
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.Shape.VLine)
        separator4.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator4)
        
        # Connection status
        self.connection_status_label = QLabel("Disconnected")
        self.connection_status_label.setStyleSheet("color: rgb(255, 100, 100); font-weight: bold;")
        layout.addWidget(self.connection_status_label)
        
        # Separator
        separator5 = QFrame()
        separator5.setFrameShape(QFrame.Shape.VLine)
        separator5.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator5)
        
        # Recording controls
        self.start_record_btn = QPushButton("⏺ Start Recording")
        self.start_record_btn.setFixedHeight(35)
        self.start_record_btn.setEnabled(False)
        self.start_record_btn.setStyleSheet("QPushButton { color: #00ff00; }")
        layout.addWidget(self.start_record_btn)
        
        self.pause_record_btn = QPushButton("⏸ Pause")
        self.pause_record_btn.setFixedHeight(35)
        self.pause_record_btn.setEnabled(False)
        self.pause_record_btn.setStyleSheet("QPushButton { color: #ffff00; }")
        layout.addWidget(self.pause_record_btn)
        
        self.stop_record_btn = QPushButton("⏹ Stop")
        self.stop_record_btn.setFixedHeight(35)
        self.stop_record_btn.setEnabled(False)
        self.stop_record_btn.setStyleSheet("QPushButton { color: #ff0000; }")
        layout.addWidget(self.stop_record_btn)
        
        layout.addWidget(QLabel("Interval:"))
        self.logging_interval_combo = QComboBox()
        self.logging_interval_combo.addItems(["0.5 Hz", "1.0 Hz"])
        self.logging_interval_combo.setCurrentText("1.0 Hz")
        self.logging_interval_combo.setFixedHeight(35)
        self.logging_interval_combo.setEnabled(False)
        layout.addWidget(self.logging_interval_combo)
        
        # Separator
        separator6 = QFrame()
        separator6.setFrameShape(QFrame.Shape.VLine)
        separator6.setStyleSheet("color: rgb(2, 44, 34);")
        layout.addWidget(separator6)
        
        # File operations
        self.load_log_btn = QPushButton("Load Log")
        self.load_log_btn.setFixedHeight(35)
        self.load_log_btn.setEnabled(False)  # Disabled until connected
        layout.addWidget(self.load_log_btn)
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
        return status_widget
    
    def update_top_status_bar(self):
        """Update the top status bar with current values"""
        # Update slaves
        self.slaves_label.setText(f"No. of slaves: {self.num_slaves}")
        
        # Update cells
        self.cells_label.setText(f"No. of cells in top BMS: {self.num_cells}")
        
        # Update port
        if self.current_port:
            self.port_label.setText(f"COM Port: {self.current_port}")
        else:
            self.port_label.setText("COM Port: --")
        
        # Connection status is updated separately via on_connection_status_changed
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Master page connections
        self.master_page.connect_requested.connect(self.on_connect_requested)
        self.master_page.disconnect_requested.connect(self.on_disconnect_requested)
        self.master_page.num_slaves_changed.connect(self.on_num_slaves_changed)
        self.master_page.num_cells_changed.connect(self.on_num_cells_changed)
        self.master_page.refresh_ports_requested.connect(self.refresh_ports)
        
        # BMS connection signals
        self.bms_connection.data_received.connect(self.on_bms_data_received)
        self.bms_connection.connection_status_changed.connect(self.on_connection_status_changed)
        self.bms_connection.connection_error.connect(self.on_connection_error)
        
        # Connect console page to logger (via custom handler)
        self.setup_log_handlers()
        
        # Recording controls in top status bar
        self.start_record_btn.clicked.connect(self.on_start_recording)
        self.pause_record_btn.clicked.connect(self.on_pause_recording)
        self.stop_record_btn.clicked.connect(self.on_stop_recording)
        self.logging_interval_combo.currentTextChanged.connect(self.on_logging_interval_changed)
        self.load_log_btn.clicked.connect(self.on_load_log)
        
        # Plot page connections
        self.plot_page.recording_state_changed.connect(self.on_recording_state_changed)
        
        # Balancing page connections
        self.balancing_page.balancing_changed.connect(self.on_balancing_changed)
        self.balancing_page.balancing_sequence_changed.connect(self.on_balancing_sequence_changed)
        
        # Timer for updating balancing state
        self.balancing_update_timer = QTimer()
        self.balancing_update_timer.timeout.connect(self.update_balancing_states)
        self.balancing_update_timer.start(2000)  # Update every 2 seconds
        
        # Debug page connections
        self.debug_page.command_sent.connect(self.on_debug_command_sent)
        
    def setup_log_handlers(self):
        """Setup log handlers to forward logs to console page"""
        import logging
        
        # Create custom handler for console page
        class ConsoleLogHandler(logging.Handler):
            def __init__(self, console_page):
                super().__init__()
                self.console_page = console_page
            
            def emit(self, record):
                level = record.levelname
                message = self.format(record)
                if 'BMSComm' in record.name:
                    self.console_page.add_bms_log(level, message)
                else:
                    self.console_page.add_app_log(level, message)
        
        # Add handler to loggers
        console_handler = ConsoleLogHandler(self.console_page)
        console_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        
        # Get loggers and add handler
        app_logger = logging.getLogger('BMSApp')
        bms_logger = logging.getLogger('BMSComm')
        
        app_logger.addHandler(console_handler)
        bms_logger.addHandler(console_handler)
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = BMSConnection.get_available_ports()
        self.master_page.set_ports(ports)
        if ports:
            msg = f"Found {len(ports)} serial port(s)"
            self.status_bar.showMessage(msg)
            self.logger.log_app("INFO", msg)
        else:
            msg = "No serial ports found"
            self.status_bar.showMessage(msg)
            self.logger.log_app("WARNING", msg)
    
    def on_page_changed(self, page_name: str):
        """Handle page change from nav bar"""
        # Remove current page from container
        if self.current_page:
            self.page_container_layout.removeWidget(self.current_page)
            self.current_page.hide()
        
        # Show selected page
        if page_name in self.pages:
            self.current_page = self.pages[page_name]
            self.page_container_layout.addWidget(self.current_page)
            self.current_page.show()
            
            # Update status
            self.status_bar.showMessage(f"Active Page: {page_name}")
            self.nav_bar.update_status(f"Active: {page_name}")
    
    def on_connect_requested(self, port: str):
        """Handle connect request from master page"""
        try:
            # Extract just the port name (e.g., "COM3" from "COM3 - USB Serial Device")
            port_name = BMSConnection.extract_port_name(port)
            self.logger.log_app("INFO", f"Attempting to connect to {port_name}")
            self.current_port = port_name
            self.update_top_status_bar()
            if self.bms_connection.connect(port_name):
                self.master_page.set_connected(True)
                msg = f"Connected to {port}"
                self.status_bar.showMessage(msg)
                self.nav_bar.update_status(msg)
                self.logger.log_app("INFO", msg)
                
                # Apply pre-configured slaves and cells after connection
                if self.num_slaves > 0:
                    self.logger.log_app("INFO", f"Applying pre-configured slaves: {self.num_slaves}")
                    self.bms_connection.set_num_slaves(self.num_slaves)
                if self.num_cells > 0:
                    self.logger.log_app("INFO", f"Applying pre-configured cells: {self.num_cells}")
                    self.bms_connection.set_num_cells_top_bms(self.num_cells)
            else:
                error_msg = "Failed to connect to BMS"
                StyledMessageBox.critical(self, "Connection Error", error_msg)
                self.logger.log_app("ERROR", error_msg)
        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}"
            StyledMessageBox.critical(self, "Connection Error", error_msg)
            self.logger.log_app("ERROR", error_msg)
    
    def on_disconnect_requested(self):
        """Handle disconnect request from master page"""
        self.logger.log_app("INFO", "Disconnecting from BMS")
        self.bms_connection.disconnect()
        self.master_page.set_connected(False)
        self.current_port = ""
        self.update_top_status_bar()
        msg = "Disconnected from BMS"
        self.status_bar.showMessage(msg)
        self.nav_bar.update_status("Disconnected")
        self.logger.log_app("INFO", msg)
    
    def on_connection_status_changed(self, connected: bool):
        """Handle connection status change"""
        self.master_page.set_connected(connected)
        if connected:
            self.status_bar.showMessage("Connected to BMS")
            self.logger.log_app("INFO", "Connected to BMS successfully")
            self.connection_status_label.setText("Connected")
            self.connection_status_label.setStyleSheet("color: rgb(100, 255, 100); font-weight: bold;")
            # Enable recording controls
            self.start_record_btn.setEnabled(True)
            self.logging_interval_combo.setEnabled(True)
            self.load_log_btn.setEnabled(True)
        else:
            self.status_bar.showMessage("Disconnected from BMS")
            self.logger.log_app("INFO", "Disconnected from BMS")
            self.connection_status_label.setText("Disconnected")
            self.connection_status_label.setStyleSheet("color: rgb(255, 100, 100); font-weight: bold;")
            # Disable recording controls
            self.start_record_btn.setEnabled(False)
            self.pause_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(False)
            self.logging_interval_combo.setEnabled(False)
            self.load_log_btn.setEnabled(False)
            # Stop recording if active
            if self.plot_page.is_recording:
                self.plot_page.stop_recording()
    
    def on_connection_error(self, error: str):
        """Handle connection error"""
        # Check if this is an auto-disconnect due to too many failures
        if error == "AUTO_DISCONNECT":
            # Update UI to show disconnected state
            self.master_page.set_connected(False)
            self.status_bar.showMessage("Connection lost. Please reconnect.")
            # Show a single message about the disconnection
            StyledMessageBox.warning(
                self, 
                "Connection Lost", 
                "Connection to BMS was lost after multiple communication failures.\n\n"
                "Please check the connection and try connecting again."
            )
        else:
            # Only show error dialog for non-auto-disconnect errors (and only once)
            # Don't spam dialogs for every retry failure
            self.status_bar.showMessage(f"Communication error: {error}")
            self.logger.log_app("WARNING", f"Connection error: {error}")
    
    def on_num_slaves_changed(self, num_slaves: int):
        """Handle number of slaves changed"""
        old_num_slaves = self.num_slaves
        self.num_slaves = num_slaves
        self.update_top_status_bar()
        
        # Always update the bms_connection's num_slaves (even if not connected yet)
        old_bms_slaves = self.bms_connection.num_slaves
        self.bms_connection.num_slaves = num_slaves
        
        # Clear data for slaves that are no longer configured
        if num_slaves < old_bms_slaves:
            from src.protocol.modbus_rtu import ModbusRTU
            for slave_num in range(num_slaves + 1, old_bms_slaves + 1):
                slave_id = ModbusRTU.get_slave_device_id(slave_num)
                if slave_id in self.bms_connection.slave_data:
                    del self.bms_connection.slave_data[slave_id]
        
        # Update plot page slave tabs
        self.plot_page.update_slave_count(num_slaves)
        
        if self.bms_connection.is_connected:
            self.logger.log_app("INFO", f"Setting number of slaves to {num_slaves}")
            if self.bms_connection.set_num_slaves(num_slaves):
                msg = f"Number of slaves set to {num_slaves}"
                self.status_bar.showMessage(msg)
                self.logger.log_app("INFO", msg)
            else:
                error_msg = "Failed to set number of slaves"
                self.status_bar.showMessage(error_msg)
                self.logger.log_app("ERROR", error_msg)
        else:
            self.status_bar.showMessage(f"Slaves configured: {num_slaves} (will apply on connect)")
    
    def on_num_cells_changed(self, num_cells: int):
        """Handle number of cells changed"""
        self.num_cells = num_cells
        self.update_top_status_bar()
        if self.bms_connection.is_connected:
            self.logger.log_app("INFO", f"Setting number of cells to {num_cells}")
            if self.bms_connection.set_num_cells_top_bms(num_cells):
                msg = f"Number of cells set to {num_cells}"
                self.status_bar.showMessage(msg)
                self.logger.log_app("INFO", msg)
            else:
                error_msg = "Failed to set number of cells"
                self.logger.log_app("ERROR", error_msg)
    
    def on_bms_data_received(self, data: dict):
        """Handle BMS data received"""
        self.logger.log_app("DEBUG", 
            f"Received BMS data: V={data.get('pack_voltage', 0):.3f}V, "
            f"I={data.get('pack_current', 0):.3f}A, "
            f"cells={len(data.get('master_cell_voltages', []))}")
        
        # Update master page
        self.master_page.update_data(data)
        
        # Update plot page
        self.plot_page.add_data_point(data)
        
        # Update balancing page with voltage and temperature data
        current_device = self.balancing_page.current_device_id
        if current_device == 1:  # Master BMS
            voltages = data.get('master_cell_voltages', [])
            temperatures = data.get('master_temperatures', [])
            die_temps = data.get('master_die_temps', [])
        else:  # Slave BMS
            slave_data = data.get('slave_data', {})
            if current_device in slave_data:
                voltages = slave_data[current_device].get('voltages', [])
                temperatures = slave_data[current_device].get('temperatures', [])
                die_temps = slave_data[current_device].get('die_temps', [])
            else:
                voltages = []
                temperatures = []
                die_temps = []
        
        self.balancing_page.update_cell_voltages(voltages)
        self.balancing_page.update_temperatures(temperatures, die_temps)
        
        # Update status bar with latest voltage/current
        voltage = data.get('pack_voltage', 0.0)
        current = data.get('pack_current', 0.0)
        self.status_bar.showMessage(
            f"Connected | Pack: {voltage:.3f}V, {current:.3f}A"
        )
    
    def on_start_recording(self):
        """Handle start recording button"""
        self.plot_page.start_recording()
    
    def on_pause_recording(self):
        """Handle pause recording button"""
        self.plot_page.pause_recording()
    
    def on_stop_recording(self):
        """Handle stop recording button"""
        self.plot_page.stop_recording()
    
    def on_logging_interval_changed(self, text: str):
        """Handle logging interval change from top status bar"""
        self.plot_page.on_interval_changed(text)
    
    def on_load_log(self):
        """Handle load log from top status bar"""
        self.plot_page.load_log_file()
    
    def on_recording_state_changed(self, state: str, info: str = ""):
        """Handle recording state change from plot page"""
        if state == "recording":
            self.logger.log_app("INFO", f"Recording started - {info}")
            self.start_record_btn.setEnabled(False)
            self.pause_record_btn.setEnabled(True)
            self.stop_record_btn.setEnabled(True)
            self.start_record_btn.setStyleSheet("QPushButton { background-color: #004400; color: #00ff00; }")
        elif state == "paused":
            self.logger.log_app("INFO", "Recording paused")
            self.start_record_btn.setEnabled(True)
            self.start_record_btn.setText("⏺ Resume")
            self.pause_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(True)
            self.start_record_btn.setStyleSheet("QPushButton { color: #ffff00; }")
        elif state == "stopped":
            self.logger.log_app("INFO", f"Recording stopped - saved to {info}")
            self.start_record_btn.setEnabled(True)
            self.start_record_btn.setText("⏺ Start Recording")
            self.pause_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(False)
            self.start_record_btn.setStyleSheet("QPushButton { color: #00ff00; }")
    
    def on_balancing_changed(self, device_id: int, enable: bool):
        """Handle balancing enable/disable"""
        if self.bms_connection.is_connected:
            success = self.bms_connection.set_balancing(device_id, enable)
            if success:
                status = "enabled" if enable else "disabled"
                self.status_bar.showMessage(f"Balancing {status} for device {device_id}")
            else:
                StyledMessageBox.warning(self, "Balancing Error", "Failed to set balancing state")
    
    def on_balancing_sequence_changed(self, device_id: int, sequence: int):
        """Handle balancing sequence change"""
        if self.bms_connection.is_connected:
            success = self.bms_connection.set_balancing_sequence(device_id, sequence)
            if success:
                self.status_bar.showMessage(f"Balancing sequence set for device {device_id}")
            else:
                StyledMessageBox.warning(self, "Balancing Error", "Failed to set balancing sequence")
        
        # Update balancing state display
        if self.bms_connection.is_connected:
            state = self.bms_connection.read_balancing_state(device_id)
            if state is not None:
                self.balancing_page.update_balancing_state(state)
    
    def on_debug_command_sent(self, command_bytes: bytes):
        """Handle debug command sent"""
        if not self.bms_connection.is_connected:
            StyledMessageBox.warning(self, "Not Connected", "Please connect to BMS first")
            return
        
        response = self.bms_connection.send_debug_command(command_bytes)
        self.debug_page.display_response(response)
        
        if response:
            self.status_bar.showMessage("Debug command sent successfully")
        else:
            self.status_bar.showMessage("Debug command failed or timeout")
    
    def update_balancing_states(self):
        """Update balancing states for all devices"""
        if not self.bms_connection.is_connected:
            return
        
        # Update current device's balancing state
        current_device = self.balancing_page.current_device_id
        
        # Read balancing status (ON/OFF) - Version 0.2
        status = self.bms_connection.read_balancing_status(current_device)
        if status is not None:
            self.balancing_page.update_balancing_enabled(status == 0x0001)
        
        # Read balancing state (cell-wise) - Version 0.2
        state = self.bms_connection.read_balancing_state(current_device)
        if state is not None:
            self.balancing_page.update_balancing_state(state)
    
    def closeEvent(self, event):
        """Handle application close event - cleanup all resources"""
        self.logger.log_app("INFO", "Application closing...")
        
        try:
            # Stop balancing update timer
            if hasattr(self, 'balancing_update_timer'):
                self.balancing_update_timer.stop()
                self.logger.log_app("DEBUG", "Balancing timer stopped")
            
            # Cleanup plot page (stops timer, saves log file)
            if hasattr(self, 'plot_page'):
                if self.plot_page.is_logging:
                    self.logger.log_app("INFO", f"Saving log file: {self.plot_page.log_file_path}")
                self.plot_page.cleanup()
                self.logger.log_app("DEBUG", "Plot page cleanup complete")
            
            # Disconnect from BMS if connected
            if self.bms_connection.is_connected:
                self.logger.log_app("INFO", "Disconnecting from BMS...")
                self.bms_connection.disconnect()
            
            # Stop BMS update timer
            if hasattr(self.bms_connection, 'update_timer'):
                self.bms_connection.update_timer.stop()
                self.logger.log_app("DEBUG", "BMS update timer stopped")
            
            self.logger.log_app("INFO", "Application closed successfully")
            
        except Exception as e:
            self.logger.log_app("ERROR", f"Error during cleanup: {e}")
        
        event.accept()

