"""
BMS Connection Handler with Modbus RTU Protocol
"""

import serial
import serial.tools.list_ports
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QMessageBox
import time
import struct
from typing import Optional, Dict, List

from src.protocol.modbus_rtu import ModbusRTU, DataConverter
from src.utils.logger import get_logger


class BMSConnection(QObject):
    """Handles connection to BMS using Modbus RTU protocol"""
    
    # Signals
    data_received = pyqtSignal(dict)  # Emits parsed BMS data
    connection_status_changed = pyqtSignal(bool)
    connection_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.baud_rate = 115200
        self.timeout = 0.5  # 500ms timeout
        self.retry_count = 3
        self.logger = get_logger()
        
        # Connection failure tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5  # Auto-disconnect after 5 consecutive failures
        
        # Configuration
        self.num_slaves = 0
        self.num_cells_top_bms = 16
        
        # Data storage
        self.pack_voltage = 0.0
        self.pack_current = 0.0
        self.master_cell_voltages: List[float] = []
        self.master_temperatures: List[float] = []
        self.slave_data: Dict[int, Dict] = {}  # {slave_id: {voltages: [], temperatures: []}}
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_interval = 1000  # 1Hz (1000ms)
        
    def connect(self, port: str) -> bool:
        """
        Connect to BMS on specified port
        
        Args:
            port: Serial port name (e.g., 'COM3' or '/dev/ttyUSB0')
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for connection to establish
            time.sleep(0.1)
            
            if self.serial_connection.is_open:
                self.is_connected = True
                self.consecutive_failures = 0  # Reset failure counter on successful connection
                self.connection_status_changed.emit(True)
                self.logger.log_bms("INFO", f"Connected to BMS on port {port} at {self.baud_rate} baud")
                
                # Start communication with BMS
                self.start_communication()
                
                # Start periodic data updates
                self.update_timer.start(self.update_interval)
                
                return True
            else:
                raise Exception(f"Failed to open serial connection to {port}")
                
        except Exception as e:
            self.connection_error.emit(str(e))
            return False
    
    def disconnect(self):
        """Disconnect from BMS"""
        self.is_connected = False
        self.consecutive_failures = 0  # Reset failure counter
        self.logger.log_bms("INFO", "Disconnecting from BMS")
        
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        # Stop communication
        self.stop_communication()
        
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
            except Exception:
                pass  # Ignore errors during disconnect
        
        self.serial_connection = None
        self.connection_status_changed.emit(False)
        self.logger.log_bms("INFO", "Disconnected from BMS")
    
    def start_communication(self) -> bool:
        """
        Start communication with Master BMS
        
        Returns:
            True if successful, False otherwise
        """
        command = ModbusRTU.build_write_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_COMM_START,
            0xAAAA  # Communication start
        )
        self.logger.log_bms("DEBUG", f"Sending command: Start Communication (0xAAAA)")
        result = self._send_command_with_retry(command) is not None
        if result:
            self.logger.log_bms("INFO", "Communication started successfully")
        else:
            self.logger.log_bms("ERROR", "Failed to start communication")
        return result
    
    def stop_communication(self) -> bool:
        """
        Stop communication with Master BMS
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        command = ModbusRTU.build_write_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_COMM_START,
            0xA5A5  # Communication stop
        )
        self.logger.log_bms("DEBUG", f"Sending command: Stop Communication (0xA5A5)")
        result = self._send_command_with_retry(command) is not None
        if result:
            self.logger.log_bms("INFO", "Communication stopped successfully")
        return result
    
    def set_num_slaves(self, num_slaves: int) -> bool:
        """
        Set number of slaves
        
        Args:
            num_slaves: Number of slaves (0-60)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0 <= num_slaves <= 0x3C:
            return False
        
        command = ModbusRTU.build_write_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_NUM_SLAVES,
            num_slaves
        )
        response = self._send_command_with_retry(command)
        if response:
            self.num_slaves = num_slaves
            return True
        return False
    
    def set_num_cells_top_bms(self, num_cells: int) -> bool:
        """
        Set number of cells in top BMS
        
        Args:
            num_cells: Number of cells (0-16)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0 <= num_cells <= 0x10:
            return False
        
        command = ModbusRTU.build_write_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_NUM_CELLS,
            num_cells
        )
        response = self._send_command_with_retry(command)
        if response:
            self.num_cells_top_bms = num_cells
            return True
        return False
    
    def read_pack_voltage(self) -> Optional[float]:
        """
        Read battery pack voltage from Master BMS
        
        Returns:
            Voltage in volts or None if failed
        """
        command = ModbusRTU.build_read_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_PACK_VOLTAGE,
            0x0001  # Read 1 word
        )
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 2:
            try:
                raw_value = struct.unpack('>H', response['data'])[0]  # Big endian
                voltage = DataConverter.voltage_from_raw(raw_value)
                self.pack_voltage = voltage
                self.logger.log_bms("DEBUG", f"Pack voltage parsed: raw=0x{raw_value:04X}, voltage={voltage:.3f}V")
                return voltage
            except Exception as e:
                self.logger.log_bms("ERROR", f"Error parsing pack voltage: {e}, data={response['data'].hex()}")
        else:
            self.logger.log_bms("WARNING", f"Invalid pack voltage response: {response}")
        return None
    
    def read_pack_current(self) -> Optional[float]:
        """
        Read battery pack current from Master BMS
        
        Returns:
            Current in amperes or None if failed
        """
        command = ModbusRTU.build_read_command(
            ModbusRTU.DEVICE_MASTER,
            ModbusRTU.ADDR_PACK_CURRENT,
            0x0002  # Read 2 words (4 bytes)
        )
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 4:
            try:
                # Combine 4 bytes into 32-bit value (big endian)
                raw_value = struct.unpack('>I', response['data'])[0]
                # Mask to 24 bits (3 bytes)
                raw_value = raw_value & 0xFFFFFF
                current = DataConverter.current_from_raw(raw_value)
                self.pack_current = current
                self.logger.log_bms("DEBUG", f"Pack current parsed: raw=0x{raw_value:06X}, current={current:.3f}A")
                return current
            except Exception as e:
                self.logger.log_bms("ERROR", f"Error parsing pack current: {e}, data={response['data'].hex()}")
        else:
            self.logger.log_bms("WARNING", f"Invalid pack current response: {response}")
        return None
    
    def read_cell_voltages(self, device_id: int = ModbusRTU.DEVICE_MASTER) -> Optional[List[float]]:
        """
        Read cell voltages from BMS
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            
        Returns:
            List of cell voltages in volts or None if failed
        """
        command = ModbusRTU.build_read_command(
            device_id,
            ModbusRTU.ADDR_CELL_VOLTAGE,
            0x0010  # Read 16 words (32 bytes)
        )
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 32:
            try:
                voltages = []
                for i in range(0, 32, 2):
                    raw_value = struct.unpack('>H', response['data'][i:i+2])[0]
                    voltage = DataConverter.cell_voltage_from_raw(raw_value)
                    voltages.append(voltage)
                
                if device_id == ModbusRTU.DEVICE_MASTER:
                    self.master_cell_voltages = voltages
                    self.logger.log_bms("DEBUG", f"Master cell voltages parsed: {len(voltages)} cells, range={min(voltages):.3f}V-{max(voltages):.3f}V")
                else:
                    if device_id not in self.slave_data:
                        self.slave_data[device_id] = {'voltages': [], 'temperatures': []}
                    self.slave_data[device_id]['voltages'] = voltages
                    self.logger.log_bms("DEBUG", f"Slave {device_id} cell voltages parsed: {len(voltages)} cells")
                
                return voltages
            except Exception as e:
                self.logger.log_bms("ERROR", f"Error parsing cell voltages: {e}, data_len={len(response.get('data', []))}")
        else:
            self.logger.log_bms("WARNING", f"Invalid cell voltage response: data_len={len(response.get('data', [])) if response else 0}")
        return None
    
    def read_temperatures(self, device_id: int = ModbusRTU.DEVICE_MASTER) -> Optional[List[float]]:
        """
        Read temperatures from BMS
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            
        Returns:
            List of temperatures in degrees Celsius or None if failed
        """
        command = ModbusRTU.build_read_command(
            device_id,
            ModbusRTU.ADDR_TEMPERATURE,
            0x0004  # Read 4 words (8 bytes)
        )
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 8:
            try:
                temperatures = []
                for i in range(0, 8, 2):
                    raw_value = struct.unpack('>H', response['data'][i:i+2])[0]
                    temperature = DataConverter.temperature_from_raw(raw_value)
                    temperatures.append(temperature)
                
                if device_id == ModbusRTU.DEVICE_MASTER:
                    self.master_temperatures = temperatures
                    self.logger.log_bms("DEBUG", f"Master temperatures parsed: {len(temperatures)} zones, range={min(temperatures):.1f}°C-{max(temperatures):.1f}°C")
                else:
                    if device_id not in self.slave_data:
                        self.slave_data[device_id] = {'voltages': [], 'temperatures': []}
                    self.slave_data[device_id]['temperatures'] = temperatures
                    self.logger.log_bms("DEBUG", f"Slave {device_id} temperatures parsed: {len(temperatures)} zones")
                
                return temperatures
            except Exception as e:
                self.logger.log_bms("ERROR", f"Error parsing temperatures: {e}, data_len={len(response.get('data', []))}")
        else:
            self.logger.log_bms("WARNING", f"Invalid temperature response: data_len={len(response.get('data', [])) if response else 0}")
        return None
    
    def set_balancing(self, device_id: int, enable: bool) -> bool:
        """
        Enable or disable balancing for a BMS device (Address 0x08)
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            enable: True to enable, False to disable
            
        Returns:
            True if successful, False otherwise
        """
        data = 0x0001 if enable else 0x0000
        command = ModbusRTU.build_write_command(
            device_id,
            ModbusRTU.ADDR_BALANCING,
            data
        )
        self.logger.log_bms("DEBUG", f"Setting balancing ON/OFF: device={device_id}, enable={enable}")
        response = self._send_command_with_retry(command)
        if response:
            self.logger.log_bms("INFO", f"Balancing {'enabled' if enable else 'disabled'} for device {device_id}")
        return response is not None
    
    def read_balancing_status(self, device_id: int) -> Optional[int]:
        """
        Read balancing status (ON/OFF) for a BMS device (Address 0x08, Read)
        
        Version 0.2: Added read command for balancing status
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            
        Returns:
            0x0001 if balancing is ON, 0x0000 if OFF, or None if failed
        """
        command = ModbusRTU.build_read_command(
            device_id,
            ModbusRTU.ADDR_BALANCING,  # Address 0x08
            0x0001  # Read 1 word
        )
        self.logger.log_bms("DEBUG", f"Reading balancing status: device={device_id}")
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 2:
            status = struct.unpack('>H', response['data'])[0]
            self.logger.log_bms("INFO", f"Balancing status for device {device_id}: {'ON' if status == 0x0001 else 'OFF'}")
            return status
        return None
    
    def set_balancing_sequence(self, device_id: int, sequence: int) -> bool:
        """
        Set balancing sequence for a BMS device (Address 0x09, Write)
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            sequence: 16-bit value where each bit represents a cell (bit 0 = cell 0, bit 15 = cell 15)
            
        Returns:
            True if successful, False otherwise
        """
        command = ModbusRTU.build_write_command(
            device_id,
            ModbusRTU.ADDR_BALANCING_SEQ,
            sequence & 0xFFFF  # Ensure 16-bit
        )
        self.logger.log_bms("DEBUG", f"Setting balancing sequence: device={device_id}, sequence=0x{sequence:04X}")
        response = self._send_command_with_retry(command)
        if response:
            self.logger.log_bms("INFO", f"Balancing sequence set for device {device_id}")
        return response is not None
    
    def read_balancing_state(self, device_id: int) -> Optional[int]:
        """
        Read balancing state for a BMS device (Address 0x09, Read)
        
        Version 0.2: Updated to use address 0x09 for reading balancing state
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            
        Returns:
            16-bit value representing balancing state (each bit = cell state) or None if failed
        """
        command = ModbusRTU.build_read_command(
            device_id,
            ModbusRTU.ADDR_BALANCING_SEQ,  # Address 0x09 (same as set, but read)
            0x0001  # Read 1 word
        )
        self.logger.log_bms("DEBUG", f"Reading balancing state: device={device_id}")
        response = self._send_command_with_retry(command)
        
        if response and 'data' in response and len(response['data']) >= 2:
            state = struct.unpack('>H', response['data'])[0]
            self.logger.log_bms("DEBUG", f"Balancing state for device {device_id}: 0x{state:04X}")
            return state
        return None
    
    def send_debug_command(self, command_bytes: bytes) -> Optional[bytes]:
        """
        Send debug command to BMS IC
        
        Args:
            command_bytes: Raw command bytes to send
            
        Returns:
            Response data bytes or None if failed
        """
        command = ModbusRTU.build_debug_command(command_bytes)
        
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        # Log debug command
        cmd_hex = ' '.join([f'{b:02X}' for b in command])
        self.logger.log_bms("DEBUG", f"Debug TX: {cmd_hex}")
        
        try:
            # Send command
            self.serial_connection.write(command)
            self.serial_connection.flush()
            
            # Wait for response
            time.sleep(0.1)
            
            # Read response
            response = b''
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.serial_connection.in_waiting > 0:
                    response += self.serial_connection.read(self.serial_connection.in_waiting)
                    # Check if we have end marker
                    if ModbusRTU.FRAME_END in response:
                        break
                time.sleep(0.01)
            
            if response:
                resp_hex = ' '.join([f'{b:02X}' for b in response])
                self.logger.log_bms("DEBUG", f"Debug RX: {resp_hex}")
                
                parsed = ModbusRTU.parse_debug_response(response)
                if parsed:
                    resp_data_hex = ' '.join([f'{b:02X}' for b in parsed])
                    self.logger.log_bms("INFO", f"Debug response: {resp_data_hex}")
                return parsed
            else:
                self.logger.log_bms("WARNING", "Debug command timeout - no response")
            
        except Exception as e:
            self.logger.log_bms("ERROR", f"Debug command error: {e}")
        
        return None
    
    def _send_command_with_retry(self, command: bytes) -> Optional[dict]:
        """
        Send command with retry logic (up to 3 attempts)
        
        Args:
            command: Command bytes to send
            
        Returns:
            Parsed response dictionary or None if all retries failed
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            self.consecutive_failures += 1
            self._check_connection_health()
            return None
        
        # Log command
        cmd_hex = ' '.join([f'{b:02X}' for b in command])
        self.logger.log_bms("DEBUG", f"TX: {cmd_hex}")
        
        for attempt in range(self.retry_count):
            try:
                # Clear input buffer
                self.serial_connection.reset_input_buffer()
                
                # Send command
                self.serial_connection.write(command)
                self.serial_connection.flush()
                
                # Wait for response
                time.sleep(0.05)
                
                # Read response
                response = b''
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.serial_connection.in_waiting > 0:
                        response += self.serial_connection.read(self.serial_connection.in_waiting)
                        # Check if we have complete frame
                        if len(response) >= 6:  # Minimum frame size
                            # For write commands, response should be 8 bytes
                            # For read commands, check byte count (2 bytes, big endian)
                            if response[2] == ModbusRTU.FUNC_READ and len(response) >= 6:
                                # Byte count is 2 bytes (big endian) at positions 3-4
                                byte_count = struct.unpack('>H', response[3:5])[0]
                                expected_len = 5 + byte_count + 2  # Header(5) + data + CRC(2)
                                if len(response) >= expected_len:
                                    break
                            elif response[2] == ModbusRTU.FUNC_WRITE:
                                if len(response) >= 8:
                                    break
                    time.sleep(0.01)
                
                if response:
                    resp_hex = ' '.join([f'{b:02X}' for b in response])
                    self.logger.log_bms("DEBUG", f"RX: {resp_hex}")
                    
                    parsed = ModbusRTU.parse_response(response)
                    if parsed and parsed.get('valid'):
                        self.logger.log_bms("DEBUG", f"Command successful (attempt {attempt + 1})")
                        # Reset failure counter on success
                        self.consecutive_failures = 0
                        return parsed
                    else:
                        self.logger.log_bms("WARNING", f"Invalid response format (attempt {attempt + 1})")
                
            except Exception as e:
                self.logger.log_bms("WARNING", f"Command attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(0.1)  # Wait before retry
        
        # All retries failed - increment failure counter
        self.consecutive_failures += 1
        self.logger.log_bms("WARNING", f"Command failed after {self.retry_count} retries (consecutive failures: {self.consecutive_failures})")
        
        # Check if we should auto-disconnect
        self._check_connection_health()
        
        return None
    
    def _check_connection_health(self):
        """Check connection health and auto-disconnect if too many failures"""
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.logger.log_bms("ERROR", f"Too many consecutive failures ({self.consecutive_failures}). Auto-disconnecting.")
            # Emit a signal for auto-disconnect (don't emit individual errors)
            self.connection_error.emit("AUTO_DISCONNECT")
            # Disconnect automatically
            self.disconnect()
    
    def update_data(self):
        """Update all BMS data (called by timer)"""
        if not self.is_connected:
            return
        
        # Read Master BMS data
        voltage = self.read_pack_voltage()
        current = self.read_pack_current()
        cell_voltages = self.read_cell_voltages(ModbusRTU.DEVICE_MASTER)
        temperatures = self.read_temperatures(ModbusRTU.DEVICE_MASTER)
        
        # Read Slave BMS data (Slave 1 = 0x02, Slave 2 = 0x03, ..., up to Slave 35 = 0x24)
        for slave_num in range(1, min(self.num_slaves + 1, ModbusRTU.MAX_SLAVES + 1)):
            slave_id = ModbusRTU.get_slave_device_id(slave_num)
            self.read_cell_voltages(slave_id)
            self.read_temperatures(slave_id)
        
        # Always emit data signal, even if some reads failed (use stored values)
        # This ensures UI updates with latest available data
        data = {
            'pack_voltage': self.pack_voltage,
            'pack_current': self.pack_current,
            'master_cell_voltages': self.master_cell_voltages.copy() if self.master_cell_voltages else [],
            'master_temperatures': self.master_temperatures.copy() if self.master_temperatures else [],
            'slave_data': {k: {'voltages': v['voltages'].copy(), 'temperatures': v['temperatures'].copy()} 
                          for k, v in self.slave_data.items()}
        }
        
        # Log data update
        self.logger.log_bms("DEBUG", 
            f"Emitting data: V={data['pack_voltage']:.3f}V, I={data['pack_current']:.3f}A, "
            f"Cells={len(data['master_cell_voltages'])}, Temps={len(data['master_temperatures'])}")
        
        self.data_received.emit(data)
    
    def set_update_frequency(self, frequency: float):
        """
        Set data update frequency
        
        Args:
            frequency: Update frequency in Hz (0.5 or 1.0)
        """
        if frequency == 0.5:
            self.update_interval = 2000  # 0.5 Hz = 2000ms
        elif frequency == 1.0:
            self.update_interval = 1000  # 1 Hz = 1000ms
        else:
            self.update_interval = 1000  # Default to 1 Hz
        
        if self.update_timer.isActive():
            self.update_timer.setInterval(self.update_interval)
    
    @staticmethod
    def get_available_ports() -> List[str]:
        """
        Get list of available serial ports (filtered to show only real devices)
        
        Returns:
            List of port names with descriptions
        """
        ports = serial.tools.list_ports.comports()
        available = []
        
        for port in ports:
            # Skip Bluetooth and other virtual ports
            desc_lower = port.description.lower() if port.description else ""
            device_lower = port.device.lower()
            
            # Filter out Bluetooth, virtual, debug ports, and n/a entries
            skip_keywords = ['bluetooth', 'bt ', 'rfcomm', 'virtual', 'debug', 'n/a', '(null)']
            if any(kw in desc_lower or kw in device_lower for kw in skip_keywords):
                continue
            
            # Skip if description is exactly "n/a" or similar
            if port.description and port.description.lower().strip() in ['n/a', 'na']:
                continue
            
            # Format: "COM3 - USB Serial Device" or just "COM3" if no description
            if port.description and port.description != port.device:
                available.append(f"{port.device} - {port.description}")
            else:
                available.append(port.device)
        
        return available
    
    @staticmethod
    def extract_port_name(port_string: str) -> str:
        """
        Extract just the port name from a formatted port string
        e.g., "COM3 - USB Serial Device" -> "COM3"
        """
        if " - " in port_string:
            return port_string.split(" - ")[0]
        return port_string

