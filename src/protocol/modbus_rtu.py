"""
Modbus RTU Protocol Implementation for BMS Communication
"""

import struct
from typing import List, Optional, Tuple


# CRC16 Table for ITU-T polynomial: x^16 + x^15 + x^2 + 1
CRC16_TABLE = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
]


def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC16 using ITU-T polynomial: x^16 + x^15 + x^2 + 1
    
    Args:
        data: Bytes to calculate CRC for
        
    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF
    for byte in data:
        crc = (crc >> 8) ^ CRC16_TABLE[(crc ^ byte) & 0xFF]
    return crc & 0xFFFF


def calculate_crc16_debug(data: bytes) -> int:
    """
    Calculate CRC16 for debugging commands using ITU-T polynomial
    This uses the same algorithm as the C code provided in the spec
    
    Args:
        data: Bytes to calculate CRC for
        
    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte & 0x00FF
        crc = CRC16_TABLE[crc & 0x00FF] ^ (crc >> 8)
    return crc & 0xFFFF


class ModbusRTU:
    """Modbus RTU Protocol Handler"""
    
    # Function codes
    FUNC_READ = 0x03
    FUNC_WRITE = 0x06
    FUNC_DEBUG = 0x0B
    
    # Device IDs (Master = 0x01, Slaves = 0x02 to 0x24 for up to 35 slaves)
    DEVICE_MASTER = 0x01
    MAX_SLAVES = 35
    
    @staticmethod
    def get_slave_device_id(slave_number: int) -> int:
        """
        Get device ID for a slave number (1-35)
        Slave 1 = 0x02, Slave 2 = 0x03, ..., Slave 35 = 0x24
        """
        if 1 <= slave_number <= 35:
            return slave_number + 1  # Slave 1 = 0x02, etc.
        raise ValueError(f"Invalid slave number: {slave_number}. Must be 1-35.")
    
    @staticmethod
    def get_slave_number(device_id: int) -> int:
        """
        Get slave number (1-35) from device ID (0x02-0x24)
        """
        if 0x02 <= device_id <= 0x24:
            return device_id - 1  # 0x02 = Slave 1, etc.
        raise ValueError(f"Invalid slave device ID: 0x{device_id:02X}. Must be 0x02-0x24.")
    
    # Addresses
    ADDR_COMM_START = 0x01
    ADDR_NUM_SLAVES = 0x02
    ADDR_NUM_CELLS = 0x03
    ADDR_PACK_VOLTAGE = 0x04
    ADDR_PACK_CURRENT = 0x05
    ADDR_CELL_VOLTAGE = 0x06
    ADDR_TEMPERATURE = 0x07
    ADDR_BALANCING = 0x08
    ADDR_BALANCING_SEQ = 0x09
    ADDR_BALANCING_STATE = 0x0A
    ADDR_DIE_TEMP_1 = 0x0C  # Version 0.3
    ADDR_DIE_TEMP_2 = 0x0D  # Version 0.3
    
    # Common read word count for all data (Version 0.4)
    # Reads: Pack Voltage (1) + Current (2) + Cell Voltages (16) + Temperatures (4) = 23 words
    COMMON_READ_WORD_COUNT = 0x0017
    
    # Frame markers
    FRAME_START = ord('*')
    FRAME_END = ord('$')
    
    @staticmethod
    def build_write_command(device_id: int, address: int, data: int) -> bytes:
        """
        Build a Modbus RTU write command (function code 0x06)
        
        Args:
            device_id: Device ID (0x01 for Master)
            address: Starting address
            data: 16-bit data value
            
        Returns:
            Complete command frame with CRC
        """
        # Build command: Start, Device ID, Function Code, Address, Data (2 bytes)
        command = bytearray([
            ModbusRTU.FRAME_START,  # Start of frame
            device_id,
            ModbusRTU.FUNC_WRITE,
            address,
            (data >> 8) & 0xFF,  # High byte
            data & 0xFF           # Low byte
        ])
        
        # Calculate CRC from device ID to data (excluding start frame)
        crc = calculate_crc16(command[1:])
        
        # Append CRC (low byte first, then high byte)
        command.extend([crc & 0xFF, (crc >> 8) & 0xFF])
        
        return bytes(command)
    
    @staticmethod
    def build_read_command(device_id: int, address: int, word_count: int) -> bytes:
        """
        Build a Modbus RTU read command (function code 0x03)
        
        Args:
            device_id: Device ID (0x01 for Master, 0x02 for Slave-1, etc.)
            address: Starting address
            word_count: Number of words to read
            
        Returns:
            Complete command frame with CRC
        """
        # Build command: Start, Device ID, Function Code, Address, Word Count (2 bytes)
        command = bytearray([
            ModbusRTU.FRAME_START,  # Start of frame
            device_id,
            ModbusRTU.FUNC_READ,
            address,
            (word_count >> 8) & 0xFF,  # High byte
            word_count & 0xFF           # Low byte
        ])
        
        # Calculate CRC from device ID to word count (excluding start frame)
        crc = calculate_crc16(command[1:])
        
        # Append CRC (low byte first, then high byte)
        command.extend([crc & 0xFF, (crc >> 8) & 0xFF])
        
        return bytes(command)
    
    @staticmethod
    def build_debug_command(command_bytes: bytes) -> bytes:
        """
        Build a debug command for BMS IC
        
        Args:
            command_bytes: Raw command bytes (CMD-1 to CMD-N)
            
        Returns:
            Complete debug command frame with CRC
        """
        # Build command: Start, Function Code, Command Bytes
        command = bytearray([
            ModbusRTU.FRAME_START,  # Start of frame
            ModbusRTU.FUNC_DEBUG
        ])
        command.extend(command_bytes)
        
        # Calculate CRC for debug command (from function code to end of command)
        crc = calculate_crc16_debug(command[1:])
        
        # Append CRC (low byte first, then high byte)
        command.extend([crc & 0xFF, (crc >> 8) & 0xFF])
        
        # Append end of frame
        command.append(ModbusRTU.FRAME_END)
        
        return bytes(command)
    
    @staticmethod
    def parse_response(response: bytes) -> Optional[dict]:
        """
        Parse a Modbus RTU response
        
        Args:
            response: Response bytes from BMS
            
        Returns:
            Parsed response dictionary or None if invalid
        """
        if len(response) < 6:  # Minimum frame size
            return None
        
        if response[0] != ModbusRTU.FRAME_START:
            return None
        
        device_id = response[1]
        function_code = response[2]
        
        # Verify CRC
        if len(response) >= 4:
            received_crc = struct.unpack('<H', response[-2:])[0]  # Little endian
            calculated_crc = calculate_crc16(response[1:-2])
            
            if received_crc != calculated_crc:
                return None
        
        result = {
            'device_id': device_id,
            'function_code': function_code,
            'valid': True
        }
        
        if function_code == ModbusRTU.FUNC_READ:
            # Read response: Start, Device ID, Function Code, Byte Count (2 bytes), Data..., CRC
            if len(response) >= 6:  # At least 6 bytes: Start, ID, Func, ByteCount(2), CRC(2)
                # Byte count is 2 bytes (big endian)
                byte_count = struct.unpack('>H', response[3:5])[0]
                if len(response) >= 5 + byte_count + 2:  # +2 for CRC
                    data = response[5:5+byte_count]
                    result['byte_count'] = byte_count
                    result['data'] = data
        elif function_code == ModbusRTU.FUNC_WRITE:
            # Write response: Start, Device ID, Function Code, Address, Data (2 bytes), CRC
            if len(response) >= 8:
                address = response[3]
                data = struct.unpack('>H', response[4:6])[0]  # Big endian
                result['address'] = address
                result['data'] = data
        elif function_code == ModbusRTU.FUNC_DEBUG:
            # Debug response: Start, Function Code, Response Data..., End
            if len(response) >= 3:
                # Find end marker
                end_idx = response.find(ModbusRTU.FRAME_END, 2)
                if end_idx > 2:
                    result['data'] = response[2:end_idx]
        
        return result
    
    @staticmethod
    def parse_debug_response(response: bytes) -> Optional[bytes]:
        """
        Parse a debug response from BMS IC
        
        Args:
            response: Response bytes from BMS IC
            
        Returns:
            Response data bytes (without frame markers) or None if invalid
        """
        if len(response) < 4:
            return None
        
        if response[0] != ModbusRTU.FRAME_START:
            return None
        
        if response[1] != ModbusRTU.FUNC_DEBUG:
            return None
        
        # Find end marker
        end_idx = response.find(ModbusRTU.FRAME_END, 2)
        if end_idx > 2:
            return response[2:end_idx]
        
        return None


# Data conversion utilities
class DataConverter:
    """Utilities for converting BMS data values (Protocol Version 0.4)"""
    
    @staticmethod
    def voltage_from_raw(raw_value: int) -> float:
        """
        Convert raw voltage value to actual voltage
        
        Formula (Version 0.4): Battery voltage = raw_value / 1000
        Example: 0xBB7E (48254) / 1000 = 48.254V
        
        Args:
            raw_value: Raw 16-bit value from BMS (0x0000 to 0xFFFF)
            
        Returns:
            Voltage in volts
        """
        return raw_value / 1000.0
    
    @staticmethod
    def current_from_raw(raw_value: int) -> float:
        """
        Convert raw current value to actual current
        
        Formula (Version 0.4): Battery current = raw_value / 1000
        Value is in 2's complement format, range: -8388608 to 8388607
        
        If ((Word data & 0x800000) == 0x800000)
            Word data = ~Word data + 1
            Word data = Word data & 0x7FFFFF
            Battery current = (-1)(Word data) / 1000
        Else
            Battery current = (Word data) / 1000
        
        Args:
            raw_value: Raw 24-bit value from BMS (2's complement, stored in 32 bits)
            
        Returns:
            Current in amperes
        """
        # Check if negative (MSB of 24-bit value set)
        if (raw_value & 0x800000) == 0x800000:
            # Negative value - convert from 2's complement
            raw_value = (~raw_value + 1) & 0x7FFFFF
            return -1.0 * raw_value / 1000.0
        else:
            return raw_value / 1000.0
    
    @staticmethod
    def cell_voltage_from_raw(raw_value: int) -> float:
        """
        Convert raw cell voltage value to actual voltage
        
        Formula (Version 0.4): Cell voltage = raw_value / 1000
        Example: 0x1387 (4999) / 1000 = 4.999V
        
        Args:
            raw_value: Raw 16-bit value from BMS (0x0000 to 0xFFFF)
            
        Returns:
            Cell voltage in volts
        """
        return raw_value / 1000.0
    
    @staticmethod
    def temperature_from_raw(raw_value: int) -> float:
        """
        Convert raw temperature value to actual temperature
        
        Formula (Version 0.4): Z = Word data / 10
        Example: 378 / 10 = 37.8°C
        
        Args:
            raw_value: Raw 16-bit value from BMS (0x0000 to 0xFFFF)
            
        Returns:
            Temperature in degrees Celsius
        """
        return raw_value / 10.0
    
    @staticmethod
    def die_temperature_from_raw(raw_value: int) -> float:
        """
        Convert raw die temperature value to actual temperature (Version 0.3)
        
        Die temperature value is in 2's complement format, range: -32768 to 32767
        
        Formula: Die temperature = Word data / 10
        
        If ((Word data & 0x8000) == 0x8000)
            Word data = ~Word data + 1
            Word data = Word data & 0x7FFF
            Die temperature = (-1)(Word data) / 10 °C
        Else
            Die temperature = (Word data) / 10 °C
        
        Args:
            raw_value: Raw 16-bit value from BMS (2's complement)
            
        Returns:
            Die temperature in degrees Celsius
        """
        # Check if negative (MSB set)
        if (raw_value & 0x8000) == 0x8000:
            # Negative value - convert from 2's complement
            raw_value = (~raw_value + 1) & 0x7FFF
            return -1.0 * raw_value / 10.0
        else:
            return raw_value / 10.0

