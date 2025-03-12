import sys
import psutil
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QProgressBar, QGridLayout, QPushButton, QTextEdit,
                             QPlainTextEdit, QSplitter)
from PyQt5.QtCore import QTimer, QProcess, Qt
from PyQt5.QtGui import QFont
import os
import ptyprocess

class TerminalWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 10))  # Use a monospace font

    def write(self, text):
        self.appendPlainText(text)

    def flush(self):
        pass  # Not strictly needed for this simple example

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initData()
        self.initTimer()
        self.initTerminal()


    def initUI(self):
        self.setWindowTitle('RK3588 System Monitor')
        self.setGeometry(100, 100, 800, 600)  # Larger window

        self.cpu_temp_label = QLabel('CPU Temperature: ')
        self.cpu_temp_value = QLabel('-')
        self.cpu_load_label = QLabel('CPU Load: ')
        self.cpu_load_bar = QProgressBar()
        self.mem_usage_label = QLabel('Memory Usage: ')
        self.mem_usage_bar = QProgressBar()
        self.disk_io_read_label = QLabel('Disk Read: ')
        self.disk_io_read_value = QLabel('-')
        self.disk_io_write_label = QLabel('Disk Write: ')
        self.disk_io_write_value = QLabel('-')

        layout = QGridLayout()
        layout.addWidget(self.cpu_temp_label, 0, 0)
        layout.addWidget(self.cpu_temp_value, 0, 1)
        layout.addWidget(self.cpu_load_label, 1, 0)
        layout.addWidget(self.cpu_load_bar, 1, 1)
        layout.addWidget(self.mem_usage_label, 2, 0)
        layout.addWidget(self.mem_usage_bar, 2, 1)
        layout.addWidget(self.disk_io_read_label, 3, 0)
        layout.addWidget(self.disk_io_read_value, 3, 1)
        layout.addWidget(self.disk_io_write_label, 4, 0)
        layout.addWidget(self.disk_io_write_value, 4, 1)

        self.update_button = QPushButton("Update")
        self.update_output = QTextEdit()
        self.update_output.setReadOnly(True)

        left_layout = QVBoxLayout()  # Layout for system monitor widgets
        left_layout.addLayout(layout)
        left_layout.addWidget(self.update_button)
        left_layout.addWidget(self.update_output)

        # Create a splitter to hold the left (system monitor) and right (terminal) sides
        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        self.splitter.addWidget(left_widget)

        # Terminal widget will be added to the splitter later in initTerminal

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.splitter)


        self.update_button.clicked.connect(self.run_update_script)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.update_output_display)
        self.process.readyReadStandardError.connect(self.update_output_display)
        self.process.finished.connect(self.update_finished)

    def initData(self):
        self.disk_io_counters = psutil.disk_io_counters()

    def initTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(1000)

    def initTerminal(self):
        self.terminal = TerminalWidget()
        self.splitter.addWidget(self.terminal)  # Add terminal to the splitter

        self.pty_process = ptyprocess.PtyProcessUnicode.spawn(['bash'])

        self.terminal_timer = QTimer(self)
        self.terminal_timer.timeout.connect(self.read_terminal_output)
        self.terminal_timer.start(50)  # Check for output every 50ms

        # Connect keyPressEvent to capture terminal input
        self.terminal.keyPressEvent = self.handle_terminal_keypress

    def handle_terminal_keypress(self, event):
        text = event.text()
        if text:
            self.pty_process.write(text)
        elif event.key() == Qt.Key_Backspace:
            self.pty_process.write('\b') # Handle backspace
        elif event.key() == Qt.Key_Return:
            self.pty_process.write('\r') # Handle Enter
        elif event.key() == Qt.Key_Left:
            self.pty_process.write('\033[D')  # Left arrow key
        elif event.key() == Qt.Key_Right:
            self.pty_process.write('\033[C')  # Right arrow key
        elif event.key() == Qt.Key_Up:
            self.pty_process.write('\033[A')  # Up arrow key
        elif event.key() == Qt.Key_Down:
            self.pty_process.write('\033[B')  # Down arrow key
        # Add more key handling as needed (e.g., Ctrl+C, Ctrl+D)
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
             self.pty_process.sendcontrol('c')
        elif event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
             self.pty_process.sendcontrol('d')


    def read_terminal_output(self):
      try:
        output = self.pty_process.read()
        if output:
            self.terminal.write(output)
      except EOFError:
          self.terminal.write("\n[Process Terminated]\n")
          self.terminal_timer.stop()

    def updateData(self):
        self.updateCpuTemp()
        self.updateCpuLoad()
        self.updateMemoryUsage()
        self.updateDiskIO()

    def updateCpuTemp(self):
        try:
            temp_path = "/sys/class/thermal/thermal_zone0/temp"  # Try zone0 first
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_raw = f.read().strip()
                try:
                    temp_celsius = int(temp_raw) / 1000.0
                    self.cpu_temp_value.setText(f"{temp_celsius:.1f} °C")
                    return  # Exit if zone0 is successful
                except ValueError:
                    print(f"Error: Invalid temperature value: {temp_raw}")
                    self.cpu_temp_value.setText("Error")
                    return

            temp_path = "/sys/class/thermal/thermal_zone1/temp"  # Then try zone1
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_raw = f.read().strip()
                try:
                    temp_celsius = int(temp_raw) / 1000.0
                    self.cpu_temp_value.setText(f"{temp_celsius:.1f} °C")
                    return
                except ValueError:
                    print(f"Error: Invalid temperature value: {temp_raw}")
                    self.cpu_temp_value.setText("Error")
                    return

            self.cpu_temp_value.setText("N/A")  # If neither zone exists

        except FileNotFoundError:
            self.cpu_temp_value.setText("N/A")
        except Exception as e:
            print(f"Error getting CPU temp: {e}")
            self.cpu_temp_value.setText("Error")

    def updateCpuLoad(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_load_bar.setValue(int(cpu_percent))
        except Exception as e:
            print(f"Error getting CPU load: {e}")
            self.cpu_load_bar.setValue(0)

    def updateMemoryUsage(self):
        try:
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            self.mem_usage_bar.setValue(int(mem_percent))
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            self.mem_usage_bar.setValue(0)

    def updateDiskIO(self):
        try:
            new_disk_io_counters = psutil.disk_io_counters()
            read_bytes = new_disk_io_counters.read_bytes - self.disk_io_counters.read_bytes
            write_bytes = new_disk_io_counters.write_bytes - self.disk_io_counters.write_bytes

            self.disk_io_read_value.setText(f'{read_bytes / 1024:.2f} KB/s')
            self.disk_io_write_value.setText(f'{write_bytes / 1024:.2f} KB/s')

            self.disk_io_counters = new_disk_io_counters
        except Exception as e:
            print(f"Error getting Disk IO: {e}")
            self.disk_io_read_value.setText("Error")
            self.disk_io_write_value.setText("Error")

    def run_update_script(self):
        self.update_output.clear()
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto-update.sh")
        self.process.start("sudo", [script_path])

    def update_output_display(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        self.update_output.append(output)
        self.update_output.append(error)

    def update_finished(self, exitCode, exitStatus):
        self.update_output.append(f"Update process finished with exit code {exitCode}")

    def closeEvent(self, event):
        # Clean up the pty process when the window is closed.
        if hasattr(self, 'pty_process') and self.pty_process.isalive():
            self.pty_process.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())