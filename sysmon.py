import sys
import psutil
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QProgressBar, QGridLayout, QPushButton, QTextEdit)
from PyQt5.QtCore import QTimer, QProcess
import os

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initData()
        self.initTimer()

    def initUI(self):
        self.setWindowTitle('RK3588 System Monitor')
        self.setGeometry(100, 100, 400, 400)

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

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(self.update_button)
        main_layout.addWidget(self.update_output)

        self.setLayout(main_layout)

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

    def updateData(self):
        self.updateCpuTemp()
        self.updateCpuLoad()
        self.updateMemoryUsage()
        self.updateDiskIO()

    def updateCpuTemp(self):
        try:
            temp_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_raw = f.read().strip()
                    try:
                        temp_celsius = int(temp_raw) / 1000.0
                        self.cpu_temp_value.setText(f"{temp_celsius:.1f} °C")
                    except ValueError:
                        print(f"Error: Invalid temperature value: {temp_raw}")
                        self.cpu_temp_value.setText("Error")
                    return

            temp_path = "/sys/class/thermal/thermal_zone1/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_raw = f.read().strip()
                    try:
                        temp_celsius = int(temp_raw) / 1000.0
                        self.cpu_temp_value.setText(f"{temp_celsius:.1f} °C")
                    except ValueError:
                        print(f"Error: Invalid temperature value: {temp_raw}")
                        self.cpu_temp_value.setText("Error")
                    return

            self.cpu_temp_value.setText("N/A")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())
