import sys
import os
from collections import defaultdict
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QLabel,
    QSpacerItem, QSizePolicy, QCheckBox, QComboBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QTextCursor, QFont, QFontDatabase, QTextCharFormat, QColor

from log_signal import LogSignal
from logcat_worker import LogcatWorker
from utils.formatting import get_format_for_line, get_level


class LogcatViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADB Logcat Viewer")
        self.resize(1200, 750)

        self.dark_theme = True
        self.auto_scroll = True
        self.log_lines = []
        self.paused = False
        self.level_filters = {lvl: True for lvl in ["error", "warn", "info", "debug", "verbose"]}
        self.log_counts = defaultdict(int)

        # Load retro font for everything except log output
        font_path = os.path.join(os.path.dirname(__file__), "PressStart2P-Regular.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Courier New"
        self.retro_font = QFont(family, 9)
        self.setFont(self.retro_font)

        self.signal = LogSignal()
        self.signal.new_line.connect(self.append_log)

        # Title & Main Controls
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
        self.search_box.textChanged.connect(self.refresh_log_display)

        self.buffer_select = QComboBox()
        self.buffer_select.addItems(["main", "system", "crash", "radio", "events"])
        self.buffer_select.setCurrentText("main")
        self.buffer_select.currentTextChanged.connect(self.change_buffer)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.NoWrap)
        # Set standard monospace font for log output (overrides retro font)
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.log_output.setFont(mono_font)

        # Install event filter on viewport for mouse clicks to pin/unpin lines
        self.log_output.viewport().installEventFilter(self)
        self.pinned_lines = set()

        self.pause_button = QPushButton("Pause")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export")
        self.theme_toggle = QCheckBox("Light Theme")
        self.scroll_toggle = QCheckBox("Auto-Scroll")
        self.scroll_toggle.setChecked(True)

        self.summary_label = QLabel("Total: 0 | Error: 0 | Warn: 0 | Info: 0 | Debug: 0")
        self.summary_label.setAlignment(Qt.AlignLeft)
        self.summary_label.setStyleSheet("padding: 4px;")

        # Log Level Checkboxes
        self.level_checkboxes = {}
        for level in self.level_filters:
            cb = QCheckBox(level.capitalize())
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_filters)
            self.level_checkboxes[level] = cb

        filter_group = QGroupBox("Log Level Filters")
        filter_layout = QGridLayout()
        for i, cb in enumerate(self.level_checkboxes.values()):
            filter_layout.addWidget(cb, 0, i)
        filter_group.setLayout(filter_layout)

        button_layout = QHBoxLayout()
        for btn in [self.pause_button, self.clear_button, self.export_button]:
            button_layout.addWidget(btn)
        button_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding))
        button_layout.addWidget(self.scroll_toggle)
        button_layout.addWidget(self.theme_toggle)
        button_layout.addWidget(QLabel("Buffer:"))
        button_layout.addWidget(self.buffer_select)

        # === NEW RIGHT PANEL ===
        import logcat_right_panel  # assume this module has RightPanel class
        self.right_panel = logcat_right_panel.RightPanel(self)

        # Wrap right panel in container widget to control fixed width
        self.right_panel_container = QWidget()
        self.right_panel_container.setLayout(self.right_panel)
        self.right_panel_container.setMinimumWidth(250)  # minimum width fallback
        self.right_panel_container.setMaximumWidth(400)  # max width fallback

        # Main layout for left side
        main_layout = QVBoxLayout()
        main_layout.addLayout(title_wrapper)
        main_layout.addWidget(self.search_box)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.log_output)
        main_layout.addWidget(self.summary_label)
        main_layout.addLayout(button_layout)

        # Horizontal layout combining left main and right panel
        layout = QHBoxLayout()
        layout.addLayout(main_layout)
        layout.addWidget(self.right_panel_container)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker = LogcatWorker(self.signal, self.buffer_select.currentText())
        self.worker.start()

        self.pause_button.clicked.connect(self.toggle_pause)
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        self.scroll_toggle.stateChanged.connect(self.toggle_scroll)

        self.apply_theme()

    def eventFilter(self, obj, event):
        if obj == self.log_output.viewport() and event.type() == QEvent.MouseButtonPress:
            cursor = self.log_output.cursorForPosition(event.pos())
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            line = cursor.selectedText()
            if not line.strip():
                return super().eventFilter(obj, event)

            if line in self.pinned_lines:
                self.pinned_lines.remove(line)
                self.remove_pinned_log(line)
            else:
                self.pinned_lines.add(line)
                self.append_pinned_log(line)
            return True
        return super().eventFilter(obj, event)

    def append_pinned_log(self, line: str):
        self.right_panel.pinned_output.append(line.strip())

    def remove_pinned_log(self, line: str):
        cursor = self.right_panel.pinned_output.textCursor()
        cursor.movePosition(QTextCursor.Start)
        while True:
            cursor = self.right_panel.pinned_output.document().find(line.strip(), cursor)
            if cursor.isNull():
                break
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # remove newline

    def update_filters(self):
        for level, cb in self.level_checkboxes.items():
            self.level_filters[level] = cb.isChecked()
        self.refresh_log_display()

    def change_buffer(self, buffer):
        self.worker.stop()
        self.worker = LogcatWorker(self.signal, buffer)
        self.worker.start()

    def apply_theme(self):
        dark = self.dark_theme
        base_color = "#121212" if dark else "#ffffff"
        text_color = "#dcdcdc" if dark else "#222"
        border_color = "#444" if dark else "#ccc"
        button_color = "#333" if dark else "#eee"
        button_text = "#00FF7F" if dark else "#222"
        button_border = "#00FF7F" if dark else "#666"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {base_color};
                color: {text_color};
                font-family: '{self.retro_font.family()}';
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {base_color};
                color: {text_color};
                border: 1px solid {border_color};
                padding: 6px;
            }}
            QPushButton {{
                background-color: {button_color};
                color: {button_text};
                border: 1px solid {button_border};
                padding: 8px;
            }}
            QCheckBox {{
                padding: 4px;
            }}
        """)

    def update_summary(self):
        summary = "Total: {} | Error: {} | Warn: {} | Info: {} | Debug: {}".format(
            sum(self.log_counts.values()),
            self.log_counts["error"],
            self.log_counts["warn"],
            self.log_counts["info"],
            self.log_counts["debug"]
        )
        self.summary_label.setText(summary)

    def append_log(self, line: str):
        self.log_lines.append(line)
        level = get_level(line)
        self.log_counts[level] += 1
        self.update_summary()

        if not self.level_filters.get(level, True):
            return

        if self.should_show_line(line):
            fmt = get_format_for_line(line, self.retro_font, self.dark_theme)
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(line, fmt)
            if self.auto_scroll:
                self.log_output.moveCursor(QTextCursor.End)

    def should_show_line(self, line: str) -> bool:
        query = self.search_box.text().lower()
        regex = self.right_panel.regex_input.text()
        tag = self.right_panel.tag_input.text().lower()
        pid = self.right_panel.pid_input.text().strip()

        if query and query not in line.lower():
            return False
        if tag and tag not in line.lower():
            return False
        if pid and pid not in line:
            return False
        if regex:
            try:
                if not re.search(regex, line):
                    return False
            except re.error:
                return False
        return True

    def refresh_log_display(self):
        self.log_output.clear()
        for line in self.log_lines:
            if not self.level_filters.get(get_level(line), True):
                continue
            if self.should_show_line(line):
                fmt = get_format_for_line(line, self.retro_font, self.dark_theme)
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
        self.log_counts.clear()
        self.pinned_lines.clear()
        self.right_panel.pinned_output.clear()
        self.update_summary()

    def export_logs(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_output.toPlainText())

    def export_filtered_logs(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Filtered Logs", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                for line in self.log_lines:
                    if self.level_filters.get(get_level(line), True) and self.should_show_line(line):
                        f.write(line)

    def load_logs_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Log File", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                self.log_lines = f.readlines()
            self.log_counts.clear()
            for line in self.log_lines:
                self.log_counts[get_level(line)] += 1
            self.update_summary()
            self.refresh_log_display()

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()
        self.refresh_log_display()

    def toggle_scroll(self):
        self.auto_scroll = self.scroll_toggle.isChecked()

    def resizeEvent(self, event):
        total_width = self.width()
        right_width = int(total_width * 0.25)
        self.right_panel_container.setFixedWidth(right_width)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LogcatViewer()
    viewer.show()
    sys.exit(app.exec())
