#!/usr/bin/env python3
"""
Helper script to list all HID devices with their VID and PID
Run this to find the VID and PID of your Arduino or BMS device
"""

try:
    import hid
    print("Scanning for HID devices...\n")
    
    devices = hid.enumerate()
    
    if not devices:
        print("No HID devices found.")
        print("\nMake sure your device is connected via USB.")
    else:
        print(f"Found {len(devices)} HID device(s):\n")
        print("-" * 80)
        print(f"{'VID':<8} {'PID':<8} {'Manufacturer':<20} {'Product':<30}")
        print("-" * 80)
        
        for device in devices:
            vid = device.get('vendor_id', 0)
            pid = device.get('product_id', 0)
            manufacturer = device.get('manufacturer_string', 'Unknown') or 'Unknown'
            product = device.get('product_string', 'Unknown') or 'Unknown'
            
            print(f"0x{vid:04X}   0x{pid:04X}   {manufacturer:<20} {product:<30}")
        
        print("-" * 80)
        print(f"\nTotal: {len(devices)} device(s)")
        print("\nTo use in the firmware upgrade page:")
        print("1. Open the Firmware Upgrade page")
        print("2. Click 'Scan Devices' button")
        print("3. Select your device from the dropdown")
        print("4. Click 'Connect'")
        
except ImportError:
    print("ERROR: hidapi library not installed.")
    print("Install it with: pip install hidapi")
    print("Or: uv sync")
except Exception as e:
    print(f"Error: {e}")




