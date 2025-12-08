# BMS Monitor App V2

A comprehensive Battery Management System (BMS) monitoring and control application with Modbus RTU protocol support.

## Features

### 1. Master Page

- **COM Port Selection**: Select and connect to BMS via serial port
- **Connection Control**: Connect/disconnect from Master BMS
- **Configuration**: Set number of slaves and cells in top BMS
- **Real-time Data Display**:
  - Battery pack voltage and current
  - Master BMS cell voltages (up to 16 cells)
  - Master BMS temperatures (4 zones)
  - Slave BMS data (voltages and temperatures)
- **Update Frequency**: 1Hz or 0.5Hz data refresh rate

### 2. Graph/Plotting Page

- **Logging Controls**: Enable/disable data logging with configurable intervals (0.5Hz or 1.0Hz)
- **Dual-Axis Plotting**: Two independent graphs with primary and secondary Y-axes
- **Plot Configuration**: Select different parameters for each axis:
  - Battery Voltage
  - Battery Current
  - Cell Voltage (Average)
  - Temperature (Average)
- **Data Management**: Save logged data to CSV and load from CSV files
- **Interactive Plots**: Pan, zoom, and zoom out capabilities for each graph

### 3. Balancing Page

- **Device Selection**: Choose Master BMS or Slave BMS devices
- **Balancing Modes**:
  - Single Cell Balancing
  - Dual Cell Balancing
- **Balancing Patterns**:
  - Odd Cells
  - Even Cells
- **Visual Status Indicators**: Green (ON) and Red (OFF) indicators for each cell
- **Real-time Status**: Automatic updates of balancing state from BMS

### 4. Debugging Page

- **Command Interface**: Send raw hexadecimal commands to BMS IC
- **Response Display**: View responses from BMS IC
- **CRC Calculation**: Automatic CRC16 calculation for debug commands

### 5. Console Page

- **BMS Communication Log**: Real-time display of all BMS communication (commands sent and responses received)
- **Application Log**: Real-time display of all application activities and events
- **Auto-scroll**: Automatic scrolling to latest log entries
- **Log File Integration**: View logs from log files with automatic refresh
- **Log Management**: Clear logs, open log folder, refresh from files

## Protocol Implementation

The application implements Modbus RTU protocol with the following specifications:

- **Baud Rate**: 115200
- **Parity**: None
- **Data Bits**: 8
- **Stop Bits**: 1
- **CRC16**: ITU-T polynomial (x^16 + x^15 + x^2 + 1)
- **Retry Logic**: Up to 3 retries with 500ms timeout

### Supported Commands

1. **Communication Start/Stop** (Address 0x01)
2. **Number of Slaves** (Address 0x02)
3. **Number of Cells** (Address 0x03)
4. **Battery Pack Voltage** (Address 0x04) - Read only
5. **Battery Pack Current** (Address 0x05) - Read only
6. **Cell Voltage** (Address 0x06) - Read only
7. **Battery Temperature** (Address 0x07) - Read only
8. **Cell Balancing** (Address 0x08)
9. **Set Balancing Sequence** (Address 0x09)
10. **Read Balancing State** (Address 0x0A) - Read only
11. **Debug Command** (Function Code 0x0B)

## Installation

### Prerequisites

- **Python**: 3.8.1 or higher
- **Operating System**: Windows, Linux, or macOS
- **Hardware**: USB-to-Serial adapter for BMS connection

### Required Python Packages

- PyQt6 (GUI framework)
- PyQt6-WebEngine (for Plotly graphs)
- pyserial (serial communication)
- pandas (data handling)
- numpy (numerical operations)
- plotly (interactive graphs)

### Step-by-Step Installation

#### Option 1: Using uv (Recommended)

```bash
# Clone or navigate to the project directory
cd BMSMonitorAppV2

# Install dependencies using uv
uv sync

# Run the application
uv run python main.py
```

#### Option 2: Using pip with virtual environment

```bash
# Clone or navigate to the project directory
cd BMSMonitorAppV2

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install the package in development mode
pip install -e .

# Run the application
python main.py
```

#### Option 3: Using pip directly

```bash
# Navigate to the project directory
cd BMSMonitorAppV2

# Install dependencies from pyproject.toml
pip install PyQt6 PyQt6-WebEngine pyserial pandas numpy plotly

# Run the application
python main.py
```

### Verify Installation

After installation, run this command to verify all dependencies are installed:

```bash
python -c "import PyQt6; import serial; import pandas; import plotly; print('All dependencies OK!')"
```

## Running the Application

### Quick Start

```bash
# Navigate to project directory
cd BMSMonitorAppV2

# Run the application
python main.py
```

### Running with uv

```bash
uv run python main.py
```

### Running on Different Platforms

#### Windows

```cmd
cd BMSMonitorAppV2
python main.py
```

#### Linux

```bash
cd BMSMonitorAppV2
python3 main.py
```

**Note for Linux users**: You may need to add your user to the `dialout` group to access serial ports:

```bash
sudo usermod -a -G dialout $USER
# Log out and log back in for changes to take effect
```

#### macOS

```bash
cd BMSMonitorAppV2
python3 main.py
```

### Command Line Options

Currently, the application runs with default settings. Configuration is done through the GUI.

### Troubleshooting

#### PyQt6 Import Error

If you get an error about PyQt6, ensure you have the correct version:

```bash
pip install PyQt6==6.6.0 PyQt6-WebEngine==6.6.0
```

#### Serial Port Access Denied (Linux)

```bash
sudo chmod 666 /dev/ttyUSB0  # Temporary fix
# Or add user to dialout group (permanent fix)
sudo usermod -a -G dialout $USER
```

#### No Serial Ports Found

- Ensure your USB-to-Serial adapter is connected
- Check if drivers are installed (especially on Windows)
- Try refreshing ports in the application

## Usage

### Connecting to BMS

1. Open the **Master** page (default tab)
2. **Configure before connecting**:
   - Set the number of slaves (0-35)
   - Set the number of cells in top BMS (0-16)
3. Click **Refresh** to scan for available COM ports
4. Select the appropriate COM port from the dropdown
5. Click **Connect to Master BMS**

### Monitoring Data

- The Master page displays real-time data with **battery indicators**:
  - 🔋 Visual battery widgets for each cell showing:
    - Fill level based on voltage (2V=0%, 5V=100%)
    - Percentage display inside battery
    - Color coding: 🔴 Red (≤2V), 🟠 Orange (2-2.8V), 🟡 Yellow (2.8-3.2V), 🟢 Green (>3.2V)
  - Temperature zones with color-coded values
- **Tabbed interface** for Master and each Slave BMS
- Data updates automatically at 1Hz

### Recording Data

1. Connect to BMS first
2. Click **⏺ Start Recording** to begin recording
3. Recording indicator shows: "⏺ Recording: bms_log_xxx.csv"
4. Click **⏸ Pause** to temporarily pause recording
5. Click **⏺ Resume** to continue recording
6. Click **⏹ Stop** to finish recording
7. **Save dialog** appears - choose filename and folder location
8. Data is saved as CSV with both values and hex representations

### Plotting Data

- **Graph/Plotting** page has separate tabs for each BMS device
- Each device tab has sub-tabs:
  - **⚡ Cell Voltages** - All 16 cell voltage traces
  - **🔋 Pack V & Current** - (Master only) Pack voltage and current
  - **🌡️ Temperature** - All 4 temperature zone traces
- **Toggle buttons** above each graph to show/hide individual traces
- **High contrast colors** for easy visibility
- **Interactive plots**: Pan, zoom, hover for values
- Load previously saved CSV files for offline analysis

### Cell Balancing

1. Navigate to the **Balancing** page
2. Select the target device (Master or Slave)
3. Choose balancing mode (Single or Dual cell)
4. Select pattern (Odd or Even cells)
5. Click **Apply Balancing Pattern**
6. Click **Enable Balancing** to start balancing
7. Monitor cell status indicators (Green = ON, Red = OFF)

### Debugging

1. Navigate to the **Debugging** page
2. Enter hexadecimal command bytes (space-separated)
   - Example: `01 02 03 04`
3. Click **Send Command**
4. View response in the response box

## Data Formats

### Voltage Conversion

- **Pack Voltage**: `(raw_value × 3.05) / 1000` volts
- **Cell Voltage**: `(raw_value × 0.19073) / 1000` volts

### Current Conversion

- **Pack Current**: `(raw_value × 14.9) / 1000000` amperes
- Uses 2's complement format for negative values

### Temperature Conversion

- **Zone Temperature**: `(-2.082 × Z³) + (17.434 × Z²) - (68.588 × Z) + 119.824` °C

## Logging System

The application includes a comprehensive logging system with the following features:

- **Hourly Log Rotation**: Log files rotate every hour automatically
- **Day-wise Organization**: Logs are organized in day-wise folders (YYYY-MM-DD)
- **Automatic Archiving**: Logs older than 7 days are automatically archived
- **Two Log Types**:
  - **Application Log**: All application activities, errors, and events
  - **BMS Communication Log**: All commands sent to and responses received from BMS
- **Log File Location**: `logs/YYYY-MM-DD/app.log` and `logs/YYYY-MM-DD/bms_comm.log`
- **Archived Logs**: Archived logs are stored in `logs/archived/YYYY-MM-DD/`

### Log Structure

```
logs/
├── 2025-01-15/
│   ├── app.log              # Application log (rotates hourly)
│   ├── app.log.2025-01-15_10  # Hourly backup
│   ├── bms_comm.log         # BMS communication log (rotates hourly)
│   └── bms_comm.log.2025-01-15_10  # Hourly backup
├── 2025-01-16/
│   └── ...
└── archived/
    ├── 2025-01-08/          # Logs older than 7 days
    └── ...
```

## Project Structure

```
BMSMonitorAppV2/
├── main.py                 # Application entry point
├── pyproject.toml          # Project configuration
├── README.md               # This file
└── src/
    ├── __init__.py
    ├── main_window.py      # Main application window
    ├── components/         # UI components
    │   ├── master_page.py  # BMS monitoring with battery indicators
    │   ├── plot_page.py    # Graphing with tabbed device views
    │   ├── balancing_page.py
    │   ├── debug_page.py
    │   ├── console_page.py
    │   ├── nav_bar.py      # Horizontal navigation bar
    │   └── sidebar.py      # (Legacy) Vertical sidebar
    ├── data/               # Data handling
    │   └── bms_connection.py  # Serial communication & Modbus RTU
    ├── protocol/           # Protocol implementation
    │   └── modbus_rtu.py   # Modbus RTU frames & CRC16
    └── utils/              # Utilities
        ├── theme.py        # Application theme
        ├── logger.py       # Logging system
        └── message_box.py  # Styled dialog boxes
```

## Theme

The application uses a custom green-themed dark mode interface for better visibility and professional appearance.

## Error Handling

- Automatic retry mechanism (3 attempts) for failed communications
- Connection timeout detection (500ms)
- User-friendly error messages for common issues
- Status bar updates for connection and operation status

## License

Proprietary - Internal use only

## Version

0.2.0

## Changelog

### v0.2.0 (December 2024)

- Added horizontal navigation bar (replaces sidebar)
- Added battery indicator widgets with percentage display
- Added tabbed views for Master and Slave BMS devices
- Added Start/Pause/Stop recording with save dialog
- Added toggle buttons for graph traces
- Added high contrast colors for graph visibility
- Added support for up to 35 slave devices
- Improved port filtering (removes Bluetooth/virtual ports)
- Real-time file logging (writes immediately, no data loss)
- Proper cleanup on application close

### v0.1.0 (September 2024)

- Initial release
- Basic Modbus RTU protocol implementation
- Master page with data display
- Graph plotting with Plotly
- Cell balancing control
- Debug command interface
- Console logging

## Author

Based on BMS Data Visualization Protocol v0.2 (December 2024)
