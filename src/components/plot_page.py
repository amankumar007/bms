"""
Graph/Plotting Page Component - Data visualization and logging
Separate tabs for each BMS device with individual graphs for Voltage, Current, Temperature
Uses JavaScript updates to prevent flickering
Real-time file logging
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTabWidget, QScrollArea,
    QFrame, QGridLayout
)
from src.utils.message_box import StyledMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from datetime import datetime
import json
import os


class PlotPage(QWidget):
    """Graph/Plotting page with tabbed graphs for each BMS device"""
    
    # Signals
    recording_state_changed = pyqtSignal(str, str)  # (state, info) - state: recording/paused/stopped
    logging_interval_changed = pyqtSignal(float)
    
    MAX_SLAVES = 35
    MAX_CELLS = 16
    MAX_TEMP_ZONES = 4
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_paused = False
        self.logging_interval = 1.0
        self.plot_data = []
        
        # Real-time file logging
        self.log_file = None
        self.log_file_path = ""
        self.temp_log_path = ""  # Temporary file path before save dialog
        self.log_header_written = False
        
        # Track known slaves
        self.known_slaves = set()
        self.configured_slave_count = 0  # Maximum number of slaves to show
        
        # Graph widgets storage {device_id: {'voltage': widget, 'current': widget, 'temp': widget}}
        self.graph_widgets = {}
        self._graph_initialized = {}
        self._page_loaded = {}  # Track which widgets have finished loading
        
        # Update timer
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._perform_plot_update)
        self._update_timer.start(2000)
        
        self.setup_ui()
    
    # Backward compatibility
    @property
    def is_logging(self):
        return self.is_recording and not self.is_paused
        
    def setup_ui(self):
        """Setup the plot page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("BMS Data Visualization")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        
        header.addStretch()
        
        # Log file indicator
        self.log_file_label = QLabel("")
        self.log_file_label.setStyleSheet("color: rgb(255, 200, 100); font-size: 11px;")
        header.addWidget(self.log_file_label)
        
        layout.addLayout(header)
        
        # Main tab widget for BMS devices
        self.device_tabs = QTabWidget()
        self.device_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid rgb(2, 44, 34);
                border-radius: 8px;
                background-color: rgb(15, 35, 30);
            }
            QTabBar::tab {
                background-color: rgb(25, 50, 45);
                color: rgb(200, 220, 200);
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 80px;
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
        self.device_tabs.setUsesScrollButtons(True)
        
        # Create Master BMS tab
        self._create_device_tab(0, "Master BMS", is_master=True)
        
        layout.addWidget(self.device_tabs)
    
    def _create_device_tab(self, device_id: int, name: str, is_master: bool = False):
        """Create a tab for a BMS device with sub-tabs for each graph type"""
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        device_layout.setContentsMargins(5, 5, 5, 5)
        
        # Sub-tabs for graph types
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgb(2, 44, 34);
                border-radius: 5px;
                background-color: rgb(20, 40, 35);
            }
            QTabBar::tab {
                background-color: rgb(30, 55, 50);
                color: rgb(180, 200, 180);
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: rgb(50, 120, 50);
                color: white;
            }
        """)
        
        # Store graph widgets for this device
        self.graph_widgets[device_id] = {}
        self._graph_initialized[device_id] = {}
        
        # High contrast colors for cells
        cell_colors = [
            '#FF0000', '#00FF00', '#0080FF', '#FF00FF',
            '#FFFF00', '#00FFFF', '#FF8000', '#8000FF',
            '#FF0080', '#00FF80', '#80FF00', '#0000FF',
            '#FF8080', '#80FF80', '#8080FF', '#FFFFFF',
        ]
        temp_colors = ['#FF0000', '#FF8000', '#FFFF00', '#00FFFF']
        
        # Voltage Graph Tab with toggle buttons
        voltage_container = QWidget()
        voltage_layout = QVBoxLayout(voltage_container)
        voltage_layout.setContentsMargins(2, 2, 2, 2)
        voltage_layout.setSpacing(2)
        
        # Toggle buttons for cells - compact strip
        voltage_toggle_frame = QFrame()
        voltage_toggle_frame.setFixedHeight(36)
        voltage_toggle_frame.setStyleSheet("background-color: rgb(25, 45, 40); border-radius: 4px;")
        voltage_toggle_layout = QHBoxLayout(voltage_toggle_frame)
        voltage_toggle_layout.setContentsMargins(8, 2, 8, 2)
        voltage_toggle_layout.setSpacing(2)
        
        toggle_label = QLabel("Cells:")
        toggle_label.setStyleSheet("color: #96c896; font-size: 11px; font-weight: bold;")
        voltage_toggle_layout.addWidget(toggle_label)
        self.graph_widgets[device_id] = {'voltage_toggles': []}
        
        for i in range(16):
            btn = QPushButton(str(i+1))
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cell_colors[i]};
                    color: #000000;
                    border: 2px solid #333;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 9px;
                }}
                QPushButton:checked {{
                    background-color: {cell_colors[i]};
                    border: 2px solid #fff;
                }}
                QPushButton:!checked {{
                    background-color: #333;
                    color: #666;
                    border: 2px solid #222;
                }}
            """)
            btn.clicked.connect(lambda checked, d=device_id: self._on_toggle_clicked(d, 'voltage'))
            voltage_toggle_layout.addWidget(btn)
            self.graph_widgets[device_id]['voltage_toggles'].append(btn)
        
        voltage_toggle_layout.addStretch()
        voltage_layout.addWidget(voltage_toggle_frame)
        
        voltage_graph = self._create_graph_widget(device_id, 'voltage')
        voltage_layout.addWidget(voltage_graph, 1)  # stretch factor = 1 to take remaining space
        self.graph_widgets[device_id]['voltage'] = voltage_graph
        self._graph_initialized[device_id] = {'voltage': False}
        
        graph_tabs.addTab(voltage_container, "⚡ Cell Voltages")
        
        # Current Graph Tab (only for Master)
        if is_master:
            current_widget = self._create_graph_widget(device_id, 'current')
            graph_tabs.addTab(current_widget, "🔋 Pack V & Current")
            self.graph_widgets[device_id]['current'] = current_widget
            self._graph_initialized[device_id]['current'] = False
        
        # Temperature Graph Tab with toggle buttons
        temp_container = QWidget()
        temp_layout = QVBoxLayout(temp_container)
        temp_layout.setContentsMargins(2, 2, 2, 2)
        temp_layout.setSpacing(2)
        
        # Toggle buttons for zones - compact strip
        temp_toggle_frame = QFrame()
        temp_toggle_frame.setFixedHeight(36)
        temp_toggle_frame.setStyleSheet("background-color: rgb(25, 45, 40); border-radius: 4px;")
        temp_toggle_layout = QHBoxLayout(temp_toggle_frame)
        temp_toggle_layout.setContentsMargins(8, 2, 8, 2)
        
        zone_label = QLabel("Zones:")
        zone_label.setStyleSheet("color: #96c896; font-size: 11px; font-weight: bold;")
        temp_toggle_layout.addWidget(zone_label)
        self.graph_widgets[device_id]['temp_toggles'] = []
        
        for i in range(4):
            btn = QPushButton(f"Z{i+1}")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedSize(32, 24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {temp_colors[i]};
                    color: #000;
                    border: 2px solid #333;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 9px;
                }}
                QPushButton:checked {{
                    background-color: {temp_colors[i]};
                    border: 2px solid #fff;
                }}
                QPushButton:!checked {{
                    background-color: #333;
                    color: #666;
                    border: 2px solid #222;
                }}
            """)
            btn.clicked.connect(lambda checked, d=device_id: self._on_toggle_clicked(d, 'temp'))
            temp_toggle_layout.addWidget(btn)
            self.graph_widgets[device_id]['temp_toggles'].append(btn)
        
        temp_toggle_layout.addStretch()
        temp_layout.addWidget(temp_toggle_frame)
        
        temp_graph = self._create_graph_widget(device_id, 'temp')
        temp_layout.addWidget(temp_graph, 1)  # stretch factor = 1 to take remaining space
        self.graph_widgets[device_id]['temp'] = temp_graph
        self._graph_initialized[device_id]['temp'] = False
        
        graph_tabs.addTab(temp_container, "🌡️ Temperature")
        
        device_layout.addWidget(graph_tabs)
        
        # Add to main device tabs
        self.device_tabs.addTab(device_widget, name)
        
        # Store the graph_tabs reference for later access
        device_widget.graph_tabs = graph_tabs
    
    def _on_toggle_clicked(self, device_id: int, graph_type: str):
        """Handle toggle button click - update graph visibility"""
        # Force graph to reinitialize with new visibility settings
        if device_id in self._graph_initialized and graph_type in self._graph_initialized[device_id]:
            self._graph_initialized[device_id][graph_type] = False
    
    def _create_graph_widget(self, device_id: int, graph_type: str) -> QWebEngineView:
        """Create a graph widget with Plotly base HTML"""
        widget = QWebEngineView()
        widget.setMinimumHeight(200)
        from PyQt6.QtWidgets import QSizePolicy
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Track page load status
        widget_key = f"{device_id}_{graph_type}"
        self._page_loaded[widget_key] = False
        
        def on_load_finished(ok):
            if ok:
                self._page_loaded[widget_key] = True
        
        widget.loadFinished.connect(on_load_finished)
        
        base_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body { margin: 0; padding: 0; background-color: #0f231e; overflow: hidden; }
                #plot { width: 100%; height: 100vh; }
                #waiting {
                    display: flex; justify-content: center; align-items: center;
                    height: 100vh; color: #96c896;
                    font-family: 'Segoe UI', sans-serif; text-align: center;
                }
                #waiting h3 { color: #f0f8ff; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <div id="waiting">
                <div>
                    <h3>Waiting for data...</h3>
                    <p style="font-size: 12px;">Connect to BMS to see graph</p>
                </div>
            </div>
            <div id="plot" style="display: none;"></div>
            <script>
                var plotInitialized = false;
                var plotlyReady = false;
                
                // Check if Plotly is loaded
                function checkPlotly() {
                    if (typeof Plotly !== 'undefined') {
                        plotlyReady = true;
                    } else {
                        setTimeout(checkPlotly, 100);
                    }
                }
                checkPlotly();
                
                function initPlot(data, layout) {
                    if (!plotlyReady) {
                        setTimeout(function() { initPlot(data, layout); }, 100);
                        return;
                    }
                    document.getElementById('waiting').style.display = 'none';
                    document.getElementById('plot').style.display = 'block';
                    Plotly.newPlot('plot', data, layout, {
                        displayModeBar: true, scrollZoom: true,
                        displaylogo: false, responsive: true
                    });
                    plotInitialized = true;
                }
                
                function updatePlotData(newData) {
                    if (!plotInitialized || !plotlyReady) return;
                    var plotDiv = document.getElementById('plot');
                    if (!plotDiv || !plotDiv.data) return;
                    
                    var update = {x: [], y: []};
                    for (var i = 0; i < newData.length && i < plotDiv.data.length; i++) {
                        update.x.push(newData[i].x);
                        update.y.push(newData[i].y);
                    }
                    var indices = [];
                    for (var i = 0; i < Math.min(newData.length, plotDiv.data.length); i++) {
                        indices.push(i);
                    }
                    Plotly.restyle('plot', update, indices);
                }
            </script>
        </body>
        </html>
        """
        widget.setHtml(base_html)
        return widget
    
    def _add_slave_tab(self, slave_id: int):
        """Add a new tab for a slave BMS"""
        slave_num = slave_id - 1  # Slave 1 = device_id 2
        name = f"Slave {slave_num}"
        self._create_device_tab(slave_id, name, is_master=False)
    
    def _remove_slave_tab(self, slave_id: int):
        """Remove a slave BMS tab"""
        if slave_id not in self.known_slaves:
            return
        
        # Find and remove the tab
        slave_num = slave_id - 1
        tab_name = f"Slave {slave_num}"
        
        for i in range(self.device_tabs.count()):
            if self.device_tabs.tabText(i) == tab_name:
                self.device_tabs.removeTab(i)
                break
        
        # Clean up tracking data
        self.known_slaves.discard(slave_id)
        
        # Remove graph widgets
        if slave_id in self.graph_widgets:
            del self.graph_widgets[slave_id]
        
        # Remove initialization flags
        if slave_id in self._graph_initialized:
            del self._graph_initialized[slave_id]
        
        # Remove page load flags
        for graph_type in ['voltage', 'current', 'temp']:
            widget_key = f"{slave_id}_{graph_type}"
            if widget_key in self._page_loaded:
                del self._page_loaded[widget_key]
    
    def update_slave_count(self, num_slaves: int):
        """Update slave tabs based on the configured number of slaves"""
        self.configured_slave_count = num_slaves
        
        # Expected slave IDs: 2, 3, 4, ... (num_slaves + 1)
        expected_slaves = set(range(2, num_slaves + 2))
        
        # Remove slaves that are no longer needed
        slaves_to_remove = self.known_slaves - expected_slaves
        for slave_id in list(slaves_to_remove):
            self._remove_slave_tab(slave_id)
    
    def start_recording(self):
        """Start or resume recording"""
        if self.is_paused:
            # Resume recording
            self.is_paused = False
            self.log_file_label.setText(f"⏺ Recording: {os.path.basename(self.temp_log_path)}")
            self.recording_state_changed.emit("recording", self.temp_log_path)
            return
        
        if self.is_recording:
            return  # Already recording
        
        # Start new recording
        self.is_recording = True
        self.is_paused = False
        self.temp_log_path = f"bms_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            self.log_file = open(self.temp_log_path, 'w', newline='')
            self.log_header_written = False
            self.log_file_label.setText(f"⏺ Recording: {self.temp_log_path}")
            self.recording_state_changed.emit("recording", self.temp_log_path)
        except Exception as e:
            self.is_recording = False
            self.log_file = None
            StyledMessageBox.critical(self, "Error", f"Failed to start recording: {e}")
    
    def pause_recording(self):
        """Pause recording"""
        if not self.is_recording or self.is_paused:
            return
        
        self.is_paused = True
        self.log_file_label.setText(f"⏸ Paused: {os.path.basename(self.temp_log_path)}")
        self.recording_state_changed.emit("paused", self.temp_log_path)
    
    def stop_recording(self):
        """Stop recording and show save dialog"""
        if not self.is_recording:
            return
        
        # First flush and close the temp file
        if self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
            except:
                pass
            self.log_file = None
        
        self.is_recording = False
        self.is_paused = False
        
        # Show save dialog
        default_name = os.path.basename(self.temp_log_path)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Recording",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                # Move/rename temp file to chosen location
                import shutil
                if os.path.exists(self.temp_log_path):
                    shutil.move(self.temp_log_path, file_path)
                    self.log_file_path = file_path
                    self.log_file_label.setText(f"✅ Saved: {os.path.basename(file_path)}")
                    self.recording_state_changed.emit("stopped", file_path)
                    StyledMessageBox.information(self, "Recording Saved", f"Recording saved to:\n{file_path}")
            except Exception as e:
                StyledMessageBox.critical(self, "Error", f"Failed to save recording: {e}")
                self.recording_state_changed.emit("stopped", "")
        else:
            # User cancelled - keep temp file
            self.log_file_label.setText(f"✅ Saved: {self.temp_log_path}")
            self.recording_state_changed.emit("stopped", self.temp_log_path)
    
    def toggle_logging(self):
        """Legacy method for backward compatibility"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def on_interval_changed(self, text: str):
        """Handle logging interval change"""
        try:
            interval = float(text.replace(" Hz", ""))
            self.logging_interval = interval
            self.logging_interval_changed.emit(interval)
        except ValueError:
            pass
    
    def load_log_file(self):
        """Load log file and display"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Log File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.plot_data = df.to_dict('records')
                self._reset_all_graphs()
                StyledMessageBox.information(self, "Success", f"Log loaded: {file_path}")
            except Exception as e:
                StyledMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")
    
    def _reset_all_graphs(self):
        """Reset all graph initialization flags"""
        for device_id in self._graph_initialized:
            for graph_type in self._graph_initialized[device_id]:
                self._graph_initialized[device_id][graph_type] = False
                widget_key = f"{device_id}_{graph_type}"
                self._page_loaded[widget_key] = False
                # Reinitialize widget HTML
                if device_id in self.graph_widgets and graph_type in self.graph_widgets[device_id]:
                    widget = self.graph_widgets[device_id][graph_type]
                    
                    # Reconnect loadFinished signal
                    def make_load_handler(key):
                        def on_load_finished(ok):
                            if ok:
                                self._page_loaded[key] = True
                        return on_load_finished
                    
                    try:
                        widget.loadFinished.disconnect()
                    except:
                        pass
                    widget.loadFinished.connect(make_load_handler(widget_key))
                    widget.setHtml(self._get_base_html())
    
    def _get_base_html(self):
        """Get base HTML for graph widget"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body { margin: 0; padding: 0; background-color: #0f231e; overflow: hidden; }
                #plot { width: 100%; height: 100vh; }
                #waiting {
                    display: flex; justify-content: center; align-items: center;
                    height: 100vh; color: #96c896;
                    font-family: 'Segoe UI', sans-serif; text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="waiting"><div><h3>Loading...</h3></div></div>
            <div id="plot" style="display: none;"></div>
            <script>
                var plotInitialized = false;
                var plotlyReady = false;
                
                function checkPlotly() {
                    if (typeof Plotly !== 'undefined') {
                        plotlyReady = true;
                    } else {
                        setTimeout(checkPlotly, 100);
                    }
                }
                checkPlotly();
                
                function initPlot(data, layout) {
                    if (!plotlyReady) {
                        setTimeout(function() { initPlot(data, layout); }, 100);
                        return;
                    }
                    document.getElementById('waiting').style.display = 'none';
                    document.getElementById('plot').style.display = 'block';
                    Plotly.newPlot('plot', data, layout, {displayModeBar: true, scrollZoom: true, displaylogo: false, responsive: true});
                    plotInitialized = true;
                }
                function updatePlotData(newData) {
                    if (!plotInitialized || !plotlyReady) return;
                    var plotDiv = document.getElementById('plot');
                    if (!plotDiv || !plotDiv.data) return;
                    var update = {x: [], y: []};
                    for (var i = 0; i < newData.length && i < plotDiv.data.length; i++) {
                        update.x.push(newData[i].x); update.y.push(newData[i].y);
                    }
                    var indices = [];
                    for (var i = 0; i < Math.min(newData.length, plotDiv.data.length); i++) indices.push(i);
                    Plotly.restyle('plot', update, indices);
                }
            </script>
        </body>
        </html>
        """
    
    def _float_to_hex(self, value: float) -> str:
        try:
            import struct
            return struct.pack('>f', value).hex().upper()
        except:
            return "N/A"
    
    def _voltage_to_raw_hex(self, voltage: float) -> str:
        try:
            return f"{int(voltage * 65535 / 5):04X}"
        except:
            return "N/A"
    
    def _write_log_entry(self, data_point: dict):
        """Write a single log entry to file"""
        if not self.log_file or not self.is_recording or self.is_paused:
            return
        
        try:
            log_entry = {'timestamp': data_point['timestamp'].isoformat()}
            log_entry['pack_voltage'] = data_point['pack_voltage']
            log_entry['pack_voltage_hex'] = self._float_to_hex(data_point['pack_voltage'])
            log_entry['pack_current'] = data_point['pack_current']
            log_entry['pack_current_hex'] = self._float_to_hex(data_point['pack_current'])
            
            for i in range(self.MAX_CELLS):
                v = data_point.get(f'master_cell_{i+1}_v')
                log_entry[f'master_cell_{i+1}_v'] = v if v is not None else ''
                log_entry[f'master_cell_{i+1}_v_hex'] = self._voltage_to_raw_hex(v) if v is not None else ''
            
            for i in range(self.MAX_TEMP_ZONES):
                t = data_point.get(f'master_temp_{i+1}')
                log_entry[f'master_temp_{i+1}'] = t if t is not None else ''
                log_entry[f'master_temp_{i+1}_hex'] = self._float_to_hex(t) if t is not None else ''
            
            # Master Die Temperatures
            die1 = data_point.get('master_die_temp_1')
            log_entry['master_die_temp_1'] = die1 if die1 is not None else ''
            log_entry['master_die_temp_1_hex'] = self._float_to_hex(die1) if die1 is not None else ''
            die2 = data_point.get('master_die_temp_2')
            log_entry['master_die_temp_2'] = die2 if die2 is not None else ''
            log_entry['master_die_temp_2_hex'] = self._float_to_hex(die2) if die2 is not None else ''
            
            for slave_id in sorted(self.known_slaves):
                for cell in range(self.MAX_CELLS):
                    v = data_point.get(f'slave_{slave_id}_cell_{cell+1}_v')
                    log_entry[f'slave_{slave_id}_cell_{cell+1}_v'] = v if v is not None else ''
                for zone in range(self.MAX_TEMP_ZONES):
                    t = data_point.get(f'slave_{slave_id}_temp_{zone+1}')
                    log_entry[f'slave_{slave_id}_temp_{zone+1}'] = t if t is not None else ''
                
                # Slave Die Temperatures
                s_die1 = data_point.get(f'slave_{slave_id}_die_temp_1')
                log_entry[f'slave_{slave_id}_die_temp_1'] = s_die1 if s_die1 is not None else ''
                s_die2 = data_point.get(f'slave_{slave_id}_die_temp_2')
                log_entry[f'slave_{slave_id}_die_temp_2'] = s_die2 if s_die2 is not None else ''
            
            if not self.log_header_written:
                self.log_file.write(','.join(log_entry.keys()) + '\n')
                self.log_header_written = True
            
            self.log_file.write(','.join(str(v) for v in log_entry.values()) + '\n')
            self.log_file.flush()
        except Exception as e:
            print(f"Log error: {e}")
    
    def add_data_point(self, data: dict):
        """Add a data point for logging/plotting"""
        timestamp = datetime.now()
        
        data_point = {
            'timestamp': timestamp,
            'pack_voltage': data.get('pack_voltage', 0.0),
            'pack_current': data.get('pack_current', 0.0),
        }
        
        master_voltages = data.get('master_cell_voltages', [])
        for i in range(self.MAX_CELLS):
            data_point[f'master_cell_{i+1}_v'] = master_voltages[i] if i < len(master_voltages) else None
        
        master_temps = data.get('master_temperatures', [])
        for i in range(self.MAX_TEMP_ZONES):
            data_point[f'master_temp_{i+1}'] = master_temps[i] if i < len(master_temps) else None
        
        # Master Die Temperatures
        master_die_temps = data.get('master_die_temps', [])
        data_point['master_die_temp_1'] = master_die_temps[0] if len(master_die_temps) > 0 else None
        data_point['master_die_temp_2'] = master_die_temps[1] if len(master_die_temps) > 1 else None
        
        slave_data = data.get('slave_data', {})
        
        # Track new slaves and create tabs (only if within configured limit)
        # Slave IDs: 2 = Slave 1, 3 = Slave 2, etc.
        max_allowed_slave_id = self.configured_slave_count + 1  # e.g., 2 slaves means IDs 2 and 3
        
        for slave_id in slave_data.keys():
            # Only add slave tab if within configured limit
            if slave_id <= max_allowed_slave_id and slave_id not in self.known_slaves:
                self.known_slaves.add(slave_id)
                self._add_slave_tab(slave_id)
                # Backfill nulls
                for old_point in self.plot_data:
                    for cell in range(self.MAX_CELLS):
                        old_point[f'slave_{slave_id}_cell_{cell+1}_v'] = None
                    for zone in range(self.MAX_TEMP_ZONES):
                        old_point[f'slave_{slave_id}_temp_{zone+1}'] = None
                    # Backfill die temps
                    old_point[f'slave_{slave_id}_die_temp_1'] = None
                    old_point[f'slave_{slave_id}_die_temp_2'] = None
        
        for slave_id in self.known_slaves:
            slave_info = slave_data.get(slave_id, {})
            voltages = slave_info.get('voltages', [])
            temperatures = slave_info.get('temperatures', [])
            die_temps = slave_info.get('die_temps', [])
            
            for cell in range(self.MAX_CELLS):
                data_point[f'slave_{slave_id}_cell_{cell+1}_v'] = voltages[cell] if cell < len(voltages) else None
            for zone in range(self.MAX_TEMP_ZONES):
                data_point[f'slave_{slave_id}_temp_{zone+1}'] = temperatures[zone] if zone < len(temperatures) else None
            
            # Slave Die Temperatures
            data_point[f'slave_{slave_id}_die_temp_1'] = die_temps[0] if len(die_temps) > 0 else None
            data_point[f'slave_{slave_id}_die_temp_2'] = die_temps[1] if len(die_temps) > 1 else None
        
        # Calculate averages
        valid_voltages = [v for v in master_voltages if v is not None]
        valid_temps = [t for t in master_temps if t is not None]
        data_point['master_avg_voltage'] = sum(valid_voltages) / len(valid_voltages) if valid_voltages else None
        data_point['master_avg_temp'] = sum(valid_temps) / len(valid_temps) if valid_temps else None
        
        if self.is_recording and not self.is_paused:
            self._write_log_entry(data_point)
        
        self.plot_data.append(data_point)
        
        if len(self.plot_data) > 500:
            self.plot_data = self.plot_data[-500:]
    
    def _perform_plot_update(self):
        """Update all graphs"""
        if not self.plot_data:
            return
        
        timestamps = [p['timestamp'].isoformat() if hasattr(p['timestamp'], 'isoformat') 
                      else str(p['timestamp']) for p in self.plot_data]
        
        # Update Master graphs (device_id = 0)
        self._update_device_graphs(0, timestamps, is_master=True)
        
        # Update Slave graphs
        for slave_id in sorted(self.known_slaves):
            self._update_device_graphs(slave_id, timestamps, is_master=False)
    
    def _update_device_graphs(self, device_id: int, timestamps: list, is_master: bool):
        """Update graphs for a specific device"""
        if device_id not in self.graph_widgets:
            return
        
        widgets = self.graph_widgets[device_id]
        initialized = self._graph_initialized[device_id]
        
        # Voltage graph
        if 'voltage' in widgets:
            widget_key = f"{device_id}_voltage"
            if self._page_loaded.get(widget_key, False):
                traces = self._build_voltage_traces(device_id, timestamps, is_master)
                self._update_graph(widgets['voltage'], traces, initialized.get('voltage', False), 
                                 "Cell Voltages (V)", "Voltage (V)")
                initialized['voltage'] = True
        
        # Current graph (Master only)
        if is_master and 'current' in widgets:
            widget_key = f"{device_id}_current"
            if self._page_loaded.get(widget_key, False):
                traces = self._build_current_traces(timestamps)
                self._update_graph(widgets['current'], traces, initialized.get('current', False),
                                 "Pack Voltage & Current", "Value")
                initialized['current'] = True
        
        # Temperature graph
        if 'temp' in widgets:
            widget_key = f"{device_id}_temp"
            if self._page_loaded.get(widget_key, False):
                traces = self._build_temp_traces(device_id, timestamps, is_master)
                self._update_graph(widgets['temp'], traces, initialized.get('temp', False),
                                 "Temperature (°C)", "Temperature (°C)")
                initialized['temp'] = True
    
    def _build_voltage_traces(self, device_id: int, timestamps: list, is_master: bool):
        """Build voltage traces for a device with high contrast colors"""
        traces = []
        # High contrast distinct colors for each cell
        colors = [
            '#FF0000',  # Red
            '#00FF00',  # Lime Green
            '#0080FF',  # Sky Blue
            '#FF00FF',  # Magenta
            '#FFFF00',  # Yellow
            '#00FFFF',  # Cyan
            '#FF8000',  # Orange
            '#8000FF',  # Purple
            '#FF0080',  # Pink
            '#00FF80',  # Spring Green
            '#80FF00',  # Chartreuse
            '#0000FF',  # Blue
            '#FF8080',  # Light Red
            '#80FF80',  # Light Green
            '#8080FF',  # Light Blue
            '#FFFFFF',  # White
        ]
        
        prefix = 'master' if is_master else f'slave_{device_id}'
        
        # Get toggle button states
        toggles = self.graph_widgets.get(device_id, {}).get('voltage_toggles', [])
        
        for cell in range(self.MAX_CELLS):
            # Check if toggle exists and is checked
            is_visible = True
            if cell < len(toggles):
                is_visible = toggles[cell].isChecked()
            
            key = f'{prefix}_cell_{cell+1}_v'
            cell_data = [p.get(key) for p in self.plot_data]
            if any(v is not None for v in cell_data):
                traces.append({
                    'x': timestamps, 'y': cell_data,
                    'name': f'Cell {cell+1}',
                    'type': 'scatter', 'mode': 'lines',
                    'line': {'color': colors[cell % len(colors)], 'width': 2},
                    'visible': is_visible
                })
        
        return traces
    
    def _build_current_traces(self, timestamps: list):
        """Build pack voltage and current traces"""
        traces = []
        
        # Pack Voltage
        pack_voltages = [p.get('pack_voltage', 0) for p in self.plot_data]
        traces.append({
            'x': timestamps, 'y': pack_voltages,
            'name': 'Pack Voltage (V)',
            'type': 'scatter', 'mode': 'lines',
            'line': {'color': '#00ff00', 'width': 2},
            'yaxis': 'y'
        })
        
        # Pack Current
        pack_currents = [p.get('pack_current', 0) for p in self.plot_data]
        traces.append({
            'x': timestamps, 'y': pack_currents,
            'name': 'Pack Current (A)',
            'type': 'scatter', 'mode': 'lines',
            'line': {'color': '#ff6600', 'width': 2},
            'yaxis': 'y2'
        })
        
        return traces
    
    def _build_temp_traces(self, device_id: int, timestamps: list, is_master: bool):
        """Build temperature traces for a device with distinct colors"""
        traces = []
        # Distinct colors for temperature zones
        colors = ['#FF0000', '#FF8000', '#FFFF00', '#00FFFF']
        
        prefix = 'master' if is_master else f'slave_{device_id}'
        
        # Get toggle button states
        toggles = self.graph_widgets.get(device_id, {}).get('temp_toggles', [])
        
        for zone in range(self.MAX_TEMP_ZONES):
            # Check if toggle exists and is checked
            is_visible = True
            if zone < len(toggles):
                is_visible = toggles[zone].isChecked()
            
            key = f'{prefix}_temp_{zone+1}'
            temp_data = [p.get(key) for p in self.plot_data]
            if any(t is not None for t in temp_data):
                traces.append({
                    'x': timestamps, 'y': temp_data,
                    'name': f'Zone {zone+1}',
                    'type': 'scatter', 'mode': 'lines',
                    'line': {'color': colors[zone], 'width': 3},
                    'visible': is_visible
                })
        
        return traces
    
    def _update_graph(self, widget, traces, initialized: bool, title: str, y_title: str):
        """Update a graph widget"""
        if not traces:
            return
        
        layout = {
            'title': {'text': title, 'font': {'size': 14, 'color': '#f0f8ff'}},
            'xaxis': {'title': 'Time', 'showgrid': True, 'gridcolor': 'rgba(2, 44, 34, 0.5)',
                     'color': '#96c896', 'tickfont': {'color': '#96c896'}},
            'yaxis': {'title': y_title, 'showgrid': True, 'gridcolor': 'rgba(2, 44, 34, 0.5)',
                     'color': '#96c896', 'tickfont': {'color': '#96c896'}},
            'autosize': True,
            'showlegend': True,
            'legend': {'orientation': 'v', 'x': 1.02, 'y': 1, 'font': {'size': 10, 'color': '#f0f8ff'},
                      'bgcolor': 'rgba(15, 35, 30, 0.9)'},
            'margin': {'l': 60, 'r': 150, 't': 35, 'b': 40},
            'paper_bgcolor': 'rgb(15, 35, 30)',
            'plot_bgcolor': 'rgb(25, 45, 40)',
            'hovermode': 'x unified',
            'hoverlabel': {
                'bgcolor': 'rgba(0, 0, 0, 0.9)',
                'bordercolor': '#44FF44',
                'font': {'color': '#FFFFFF', 'size': 13, 'family': 'monospace'}
            }
        }
        
        # Add secondary y-axis for current graph
        if any('yaxis' in t and t['yaxis'] == 'y2' for t in traces):
            layout['yaxis2'] = {
                'title': 'Current (A)',
                'overlaying': 'y',
                'side': 'right',
                'showgrid': False
            }
        
        if not initialized:
            # Initialize plot
            js_code = f"initPlot({json.dumps(traces)}, {json.dumps(layout)});"
            widget.page().runJavaScript(js_code)
        else:
            # Update data
            update_data = [{'x': t['x'], 'y': t['y']} for t in traces]
            js_code = f"updatePlotData({json.dumps(update_data)});"
            widget.page().runJavaScript(js_code)
    
    def update_plot(self):
        """Force update all plots"""
        self._reset_all_graphs()
    
    def clear_data(self):
        """Clear all data"""
        self.plot_data = []
        self.known_slaves = set()
        self._reset_all_graphs()
        
        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass
            self.log_file = None
        self.is_logging = False
        self.log_file_label.setText("")
    
    def cleanup(self):
        """Cleanup all resources before closing"""
        # Stop update timer
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()
        
        # Stop recording and save file
        if self.is_recording:
            self.is_recording = False
            self.is_paused = False
        
        if self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
                print(f"Log file saved: {self.temp_log_path}")
            except Exception as e:
                print(f"Error closing log file: {e}")
            self.log_file = None
        
        # Clear data
        self.plot_data = []
        self.known_slaves = set()
