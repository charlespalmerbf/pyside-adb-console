# logcat_viewer.py

import sys
import subprocess
import threading
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QFileDialog,
    QLabel, QSpacerItem, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor, QFont, QFontDatabase, QTextCharFormat, QColor


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
        self.resize(1000, 700)

        self.dark_theme = True
        self.auto_scroll = True
        self.log_lines = []
        self.paused = False

        font_path = os.path.join(os.path.dirname(__file__), "PressStart2P-Regular.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.retro_font = QFont(family, 9)
        else:
            self.retro_font = QFont("Courier New", 9)

        self.setFont(self.retro_font)

        self.title_label = QLabel("ADB Logcat Viewer")
        self.title_label.setFont(QFont(self.retro_font.family(), 12))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #00FF7F; padding: 10px;")

        title_wrapper = QHBoxLayout()
        title_wrapper.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding))
        title_wrapper.addWidget(self.title_label)
        title_wrapper.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding))

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter logs")
        self.search_box.setClearButtonEnabled(True)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.NoWrap)

        self.pause_button = QPushButton("Pause")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export")
        self.theme_toggle = QCheckBox("Light Theme")
        self.scroll_toggle = QCheckBox("Auto-Scroll")
        self.scroll_toggle.setChecked(True)

        button_layout = QHBoxLayout()
        for btn in [self.pause_button, self.clear_button, self.export_button]:
            button_layout.addWidget(btn)
        button_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding))
        button_layout.addWidget(self.scroll_toggle)
        button_layout.addWidget(self.theme_toggle)

        layout = QVBoxLayout()
        layout.addLayout(title_wrapper)
        layout.addWidget(self.search_box)
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.signal = LogSignal()
        self.signal.new_line.connect(self.append_log)

        self.worker = LogcatWorker(self.signal)
        self.worker.start()

        self.search_box.textChanged.connect(self.refresh_log_display)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        self.scroll_toggle.stateChanged.connect(self.toggle_scroll)

        self.apply_theme()

    def apply_theme(self):
        if self.dark_theme:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: #121212;
                    color: #dcdcdc;
                    font-family: '{self.retro_font.family()}';
                }}
                QLineEdit, QTextEdit {{
                    background-color: #1e1e1e;
                    color: #dcdcdc;
                    border: 1px solid #444;
                    padding: 6px;
                }}
                QPushButton {{
                    background-color: #333;
                    color: #00FF7F;
                    border: 1px solid #00FF7F;
                    padding: 8px;
                }}
                QCheckBox {{
                    padding: 4px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: #ffffff;
                    color: #222;
                    font-family: '{self.retro_font.family()}';
                }}
                QLineEdit, QTextEdit {{
                    background-color: #ffffff;
                    color: #222;
                    border: 1px solid #ccc;
                    padding: 6px;
                }}
                QPushButton {{
                    background-color: #eee;
                    color: #222;
                    border: 1px solid #666;
                    padding: 8px;
                }}
                QCheckBox {{
                    padding: 4px;
                }}
            """)

    def get_format_for_line(self, line):
        fmt = QTextCharFormat()
        fmt.setFont(self.retro_font)
        line_lower = line.lower()

        if "error" in line_lower:
            fmt.setForeground(QColor("red"))
        elif "warn" in line_lower:
            fmt.setForeground(QColor("yellow"))
        elif "info" in line_lower:
            fmt.setForeground(QColor("green"))
        elif "debug" in line_lower:
            fmt.setForeground(QColor("cyan"))
        else:
            fmt.setForeground(QColor("#dcdcdc" if self.dark_theme else "#222"))

        return fmt

    def append_log(self, line: str):
        self.log_lines.append(line)
        if self.search_box.text().lower() in line.lower():
            fmt = self.get_format_for_line(line)
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(line, fmt)

            if self.auto_scroll:
                self.log_output.moveCursor(QTextCursor.End)

    def refresh_log_display(self):
        query = self.search_box.text().lower()
        self.log_output.clear()
        for line in self.log_lines:
            if query in line.lower():
                fmt = self.get_format_for_line(line)
                cursor = self.log_output.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.insertText(line, fmt)

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

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()
        self.refresh_log_display()

    def toggle_scroll(self):
        self.auto_scroll = self.scroll_toggle.isChecked()

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LogcatViewer()
    viewer.show()
    sys.exit(app.exec())
