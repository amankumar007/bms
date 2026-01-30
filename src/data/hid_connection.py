"""
USB HID Connection Handler for Firmware Upgrade
Implements custom USB HID protocol for BMS firmware upgrade
"""

import time
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import struct

try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

from src.utils.logger import get_logger


class HIDConnection(QObject):
    """Handles USB HID connection for firmware upgrade"""
    
    # Signals
    connection_status_changed = pyqtSignal(bool)
    device_info_received = pyqtSignal(str, str)  # serial_number, firmware_version
    upgrade_progress = pyqtSignal(int)  # progress percentage
    upgrade_complete = pyqtSignal(bool, str)  # success, message
    
    # Report structure: 64 bytes
    REPORT_ID = 0x01
    REPORT_SIZE = 64
    
    # Command codes
    CMD_CONNECT = 0x01
    CMD_DISCONNECT = 0x01
    CMD_GET_INFO = 0x02
    CMD_MAKE_SPACE = 0x03
    CMD_START_UPGRADE = 0x04
    CMD_UPGRADE_DATA = 0x05
    CMD_LAST_CHUNK = 0x06
    
    # Data values
    DATA_CONNECT = 0xAAAA
    DATA_DISCONNECT = 0xA5A5
    DATA_ACK = 0x5555
    DATA_NACK = 0x9999
    
    def __init__(self, vid: int = 0x0000, pid: int = 0x0000):
        """
        Initialize HID connection
        
        Args:
            vid: Vendor ID (to be configured)
            pid: Product ID (to be configured)
        """
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.device = None
        self.is_connected = False
        self.logger = get_logger()
        self.timeout = 5.0  # 5 seconds timeout
        self.retry_count = 3
        
        # Device info
        self.serial_number = ""
        self.firmware_version = ""
        
        # Upgrade state
        self.upgrade_in_progress = False
        self.upgrade_start_time = 0
        self.max_upgrade_time = 600  # 10 minutes
        
        # Device discovery timer
        self.discovery_timer = QTimer()
        self.discovery_timer.timeout.connect(self.check_device_availability)
        self.discovery_interval = 30000  # 30 seconds
        
    def set_vid_pid(self, vid: int, pid: int):
        """Set Vendor ID and Product ID for device identification"""
        self.vid = vid
        self.pid = pid
    
    def check_device_availability(self) -> bool:
        """
        Check if HID device is available and auto-connect if not already connected
        
        Returns:
            True if device found, False otherwise
        """
        if not HID_AVAILABLE:
            return False
        
        try:
            devices = hid.enumerate()
            for device_info in devices:
                if device_info.get('vendor_id') == self.vid and device_info.get('product_id') == self.pid:
                    # Device found - try to connect if not already connected
                    if not self.is_connected and self.vid != 0x0000 and self.pid != 0x0000:
                        self.logger.log_app("INFO", "HID device found, attempting to connect...")
                        self.connect()
                    return True
            return False
        except Exception as e:
            self.logger.log_app("ERROR", f"Error checking HID device availability: {e}")
            return False
    
    def start_device_discovery(self):
        """Start periodic device discovery (every 30 seconds)"""
        if not self.is_connected:
            self.discovery_timer.start(self.discovery_interval)
    
    def stop_device_discovery(self):
        """Stop device discovery"""
        self.discovery_timer.stop()
    
    def connect(self) -> bool:
        """
        Connect to HID device
        
        Returns:
            True if connection successful, False otherwise
        """
        if not HID_AVAILABLE:
            self.logger.log_app("ERROR", "HID library not available. Please install hidapi.")
            return False
        
        try:
            # Find and open device
            self.device = hid.device()
            self.device.open(self.vid, self.pid)
            self.device.set_nonblocking(True)
            
            self.logger.log_app("INFO", f"Opened HID device VID={self.vid:04X}, PID={self.pid:04X}")
            
            # Send connection command
            if self._send_connect_command():
                self.is_connected = True
                self.stop_device_discovery()
                self.connection_status_changed.emit(True)
                self.logger.log_app("INFO", "HID device connected successfully")
                
                # Request device info
                self.request_device_info()
                return True
            else:
                self.device.close()
                self.device = None
                self.logger.log_app("WARNING", "Failed to connect to HID device - no response")
                return False
                
        except Exception as e:
            self.logger.log_app("ERROR", f"Error connecting to HID device: {e}")
            if self.device:
                try:
                    self.device.close()
                except:
                    pass
                self.device = None
            return False
    
    def disconnect(self):
        """Disconnect from HID device"""
        if self.device and self.is_connected:
            try:
                self._send_disconnect_command()
            except:
                pass
        
        if self.device:
            try:
                self.device.close()
            except:
                pass
            self.device = None
        
        self.is_connected = False
        self.serial_number = ""
        self.firmware_version = ""
        self.connection_status_changed.emit(False)
        self.logger.log_app("INFO", "HID device disconnected")
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum (sum of all bytes)"""
        return sum(data) & 0xFFFF
    
    def _build_report(self, command: int, data_high: int = 0, data_low: int = 0, payload: bytes = b'') -> bytes:
        """
        Build HID report (64 bytes)
        
        Structure:
        - Byte 0: Report ID (0x01)
        - Byte 1: Command code
        - Bytes 2-3: Data High/Low (or first 2 bytes of payload)
        - Bytes 4-61: Unused data (0x00) or payload data
        - Bytes 62-63: Checksum (2 bytes, big endian)
        """
        report = bytearray(self.REPORT_SIZE)
        report[0] = self.REPORT_ID
        report[1] = command
        
        if payload:
            # For commands with payload (0x04, 0x05, 0x06)
            payload_len = min(len(payload), 60)
            report[2:2+payload_len] = payload[:payload_len]
            # Fill rest with 0x00
            for i in range(2+payload_len, 62):
                report[i] = 0x00
        else:
            # For commands without payload
            report[2] = (data_high >> 8) & 0xFF
            report[3] = data_high & 0xFF
            report[4] = (data_low >> 8) & 0xFF
            report[5] = data_low & 0xFF
            # Fill rest with 0x00
            for i in range(6, 62):
                report[i] = 0x00
        
        # Calculate checksum (bytes 0-61)
        checksum = self._calculate_checksum(report[:62])
        report[62] = (checksum >> 8) & 0xFF
        report[63] = checksum & 0xFF
        
        return bytes(report)
    
    def _send_report(self, report: bytes) -> bool:
        """Send HID report to device"""
        if not self.device:
            return False
        
        try:
            self.device.write(report)
            return True
        except Exception as e:
            self.logger.log_app("ERROR", f"Error sending HID report: {e}")
            return False
    
    def _read_report(self, timeout: float = None) -> Optional[bytes]:
        """
        Read HID report from device
        
        Args:
            timeout: Timeout in seconds (default: self.timeout)
            
        Returns:
            Report bytes or None if timeout/error
        """
        if not self.device:
            return None
        
        if timeout is None:
            timeout = self.timeout
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data = self.device.read(self.REPORT_SIZE)
                if data and len(data) == self.REPORT_SIZE:
                    return bytes(data)
            except Exception as e:
                if "would block" not in str(e).lower():
                    self.logger.log_app("ERROR", f"Error reading HID report: {e}")
                time.sleep(0.01)
            time.sleep(0.01)
        
        return None
    
    def _send_connect_command(self) -> bool:
        """Send connection command and wait for ACK"""
        report = self._build_report(self.CMD_CONNECT, self.DATA_CONNECT, 0)
        self.logger.log_app("DEBUG", f"Sending connect command: {report.hex()}")
        
        if not self._send_report(report):
            return False
        
        # Wait for response
        response = self._read_report(timeout=15.0)  # 15 seconds timeout as per spec
        if response:
            self.logger.log_app("DEBUG", f"Received response: {response.hex()}")
            if len(response) >= 4:
                cmd = response[1]
                data_high = (response[2] << 8) | response[3]
                if cmd == self.CMD_CONNECT and data_high == self.DATA_ACK:
                    return True
        
        return False
    
    def _send_disconnect_command(self) -> bool:
        """Send disconnection command"""
        report = self._build_report(self.CMD_DISCONNECT, self.DATA_DISCONNECT, 0)
        self.logger.log_app("DEBUG", f"Sending disconnect command: {report.hex()}")
        return self._send_report(report)
    
    def request_device_info(self) -> bool:
        """
        Request serial number and firmware version
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        report = self._build_report(self.CMD_GET_INFO, 0, 0)
        self.logger.log_app("DEBUG", f"Requesting device info: {report.hex()}")
        
        if not self._send_report(report):
            return False
        
        # Wait for response
        response = self._read_report(timeout=15.0)
        if response and len(response) >= 22:
            self.logger.log_app("DEBUG", f"Received device info: {response.hex()}")
            
            # Parse serial number (bytes 2-9, 8 bytes ASCII)
            serial_bytes = response[2:10]
            self.serial_number = serial_bytes.decode('ascii', errors='ignore').strip('\x00')
            
            # Parse firmware version (bytes 10-20, 11 bytes ASCII)
            version_bytes = response[10:21]
            self.firmware_version = version_bytes.decode('ascii', errors='ignore').strip('\x00')
            
            self.logger.log_app("INFO", f"Device Serial: {self.serial_number}, Firmware: {self.firmware_version}")
            self.device_info_received.emit(self.serial_number, self.firmware_version)
            return True
        
        return False
    
    def make_space_for_firmware(self, firmware_size: int) -> bool:
        """
        Request device to make space for new firmware
        
        Args:
            firmware_size: Size of firmware in bytes
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        # Convert size to high/low bytes (4 bytes total)
        # High bytes: upper 2 bytes, Low bytes: lower 2 bytes
        data_high = (firmware_size >> 16) & 0xFFFF
        data_low = firmware_size & 0xFFFF
        
        report = self._build_report(self.CMD_MAKE_SPACE, data_high, data_low)
        self.logger.log_app("DEBUG", f"Making space for firmware ({firmware_size} bytes): {report.hex()}")
        
        if not self._send_report(report):
            return False
        
        # Wait for ACK
        response = self._read_report(timeout=5.0)
        if response and len(response) >= 4:
            cmd = response[1]
            data_high = (response[2] << 8) | response[3]
            if cmd == self.CMD_MAKE_SPACE and data_high == self.DATA_ACK:
                return True
        
        return False
    
    def send_firmware_chunk(self, chunk: bytes, is_first: bool = False, is_last: bool = False) -> bool:
        """
        Send firmware chunk to device
        
        Args:
            chunk: Firmware data chunk (up to 60 bytes)
            is_first: True if this is the first chunk
            is_last: True if this is the last chunk
            
        Returns:
            True if ACK received, False otherwise
        """
        if not self.is_connected:
            return False
        
        # Determine command code
        if is_first:
            cmd = self.CMD_START_UPGRADE
        elif is_last:
            cmd = self.CMD_LAST_CHUNK
        else:
            cmd = self.CMD_UPGRADE_DATA
        
        # Pad chunk to 60 bytes if needed
        padded_chunk = chunk[:60].ljust(60, b'\x00')
        
        report = self._build_report(cmd, payload=padded_chunk)
        
        # Retry logic (up to 3 times)
        for attempt in range(self.retry_count):
            if self._send_report(report):
                # Wait for ACK
                response = self._read_report(timeout=5.0)
                if response and len(response) >= 4:
                    resp_cmd = response[1]
                    data_high = (response[2] << 8) | response[3]
                    if resp_cmd in [self.CMD_START_UPGRADE, self.CMD_UPGRADE_DATA, self.CMD_LAST_CHUNK] and data_high == self.DATA_ACK:
                        return True
                
                if attempt < self.retry_count - 1:
                    self.logger.log_app("WARNING", f"Chunk ACK failed, retrying ({attempt + 1}/{self.retry_count})")
                    time.sleep(0.1)
            else:
                if attempt < self.retry_count - 1:
                    self.logger.log_app("WARNING", f"Chunk send failed, retrying ({attempt + 1}/{self.retry_count})")
                    time.sleep(0.1)
        
        return False
    
    def upgrade_firmware(self, firmware_data: bytes) -> bool:
        """
        Upgrade firmware on device
        
        Args:
            firmware_data: Complete firmware file data
            
        Returns:
            True if upgrade successful, False otherwise
        """
        if not self.is_connected:
            self.logger.log_app("ERROR", "Not connected to device")
            return False
        
        self.upgrade_in_progress = True
        self.upgrade_start_time = time.time()
        
        try:
            # Step 1: Make space for firmware
            self.logger.log_app("INFO", f"Making space for firmware ({len(firmware_data)} bytes)")
            if not self.make_space_for_firmware(len(firmware_data)):
                self.logger.log_app("ERROR", "Failed to make space for firmware")
                self.upgrade_in_progress = False
                return False
            
            # Step 2: Send firmware in chunks of 60 bytes
            chunk_size = 60
            total_chunks = (len(firmware_data) + chunk_size - 1) // chunk_size
            bytes_sent = 0
            
            self.logger.log_app("INFO", f"Starting firmware upgrade ({total_chunks} chunks)")
            
            for i in range(total_chunks):
                # Check timeout (10 minutes)
                if time.time() - self.upgrade_start_time > self.max_upgrade_time:
                    self.logger.log_app("ERROR", "Firmware upgrade timeout (>10 minutes)")
                    self.upgrade_in_progress = False
                    return False
                
                # Get chunk
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, len(firmware_data))
                chunk = firmware_data[start_idx:end_idx]
                
                is_first = (i == 0)
                is_last = (i == total_chunks - 1)
                
                # Send chunk
                if not self.send_firmware_chunk(chunk, is_first, is_last):
                    self.logger.log_app("ERROR", f"Failed to send chunk {i+1}/{total_chunks}")
                    self.upgrade_in_progress = False
                    return False
                
                bytes_sent += len(chunk)
                
                # Update progress
                progress = int((bytes_sent / len(firmware_data)) * 100)
                self.upgrade_progress.emit(progress)
                self.logger.log_app("DEBUG", f"Progress: {progress}% ({bytes_sent}/{len(firmware_data)} bytes)")
            
            # Upgrade complete
            self.logger.log_app("INFO", "Firmware upgrade completed successfully")
            self.upgrade_in_progress = False
            self.upgrade_complete.emit(True, "Firmware upgrade completed successfully")
            return True
            
        except Exception as e:
            self.logger.log_app("ERROR", f"Firmware upgrade error: {e}")
            self.upgrade_in_progress = False
            self.upgrade_complete.emit(False, f"Firmware upgrade failed: {e}")
            return False
    
    @staticmethod
    def enumerate_devices():
        """
        Enumerate all HID devices
        
        Returns:
            List of device info dictionaries
        """
        if not HID_AVAILABLE:
            return []
        
        try:
            devices = hid.enumerate()
            return devices
        except Exception as e:
            return []

