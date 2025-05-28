import sys
import subprocess
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QObject


class LogSignal(QObject):
    new_line = Signal(str)


class LogcatWorker(threading.Thread):
    def __init__(self, signal: LogSignal):
        super().__init__(daemon=True)
        self.signal = signal
        self.running = True
        self.paused = False
        self.process = None

    def run(self):
        self.process = subprocess.Popen(
            ["adb", "logcat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in self.process.stdout:
            if not self.running:
                break
            if not self.paused:
                self.signal.new_line.emit(line)

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()


class LogcatViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADB Logcat Viewer")
        self.setGeometry(300, 200, 800, 600)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter log...")

        self.pause_button = QPushButton("Pause")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)

        layout = QVBoxLayout()
        layout.addWidget(self.search_box)
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.log_lines = []
        self.paused = False

        self.signal = LogSignal()
        self.signal.new_line.connect(self.append_log)

        self.worker = LogcatWorker(self.signal)
        self.worker.start()

        self.search_box.textChanged.connect(self.filter_logs)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)

    def append_log(self, line: str):
        self.log_lines.append(line)
        if self.search_box.text().lower() in line.lower():
            self.log_output.append(line)

    def filter_logs(self):
        query = self.search_box.text().lower()
        self.log_output.clear()
        for line in self.log_lines:
            if query in line.lower():
                self.log_output.append(line)

    def toggle_pause(self):
        self.paused = not self.paused
        self.worker.paused = self.paused
        self.pause_button.setText("Resume" if self.paused else "Pause")

    def clear_logs(self):
        self.log_lines.clear()
        self.log_output.clear()

    def export_logs(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_output.toPlainText())

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LogcatViewer()
    viewer.show()
    sys.exit(app.exec())
