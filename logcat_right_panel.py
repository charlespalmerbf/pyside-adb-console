from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
)

class RightPanel(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        # Regex Search
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("Regex Search")
        self.regex_input.textChanged.connect(parent.refresh_log_display)
        self.addWidget(QLabel("Regex Filter"))
        self.addWidget(self.regex_input)

        # Tag Filter
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag Filter")
        self.tag_input.textChanged.connect(parent.refresh_log_display)
        self.addWidget(QLabel("Tag Filter"))
        self.addWidget(self.tag_input)

        # PID/TID Filter
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("PID/TID Filter")
        self.pid_input.textChanged.connect(parent.refresh_log_display)
        self.addWidget(QLabel("PID/TID Filter"))
        self.addWidget(self.pid_input)

        # Load logs from file
        self.load_button = QPushButton("Load Logs from File")
        self.load_button.clicked.connect(parent.load_logs_from_file)
        self.addWidget(self.load_button)

        # Export filtered logs
        self.export_filtered_button = QPushButton("Export Filtered Logs")
        self.export_filtered_button.clicked.connect(parent.export_filtered_logs)
        self.addWidget(self.export_filtered_button)

        # Pinned logs area
        self.addWidget(QLabel("Pinned Logs"))
        self.pinned_output = QTextEdit()
        self.pinned_output.setReadOnly(True)
        self.addWidget(self.pinned_output)

    def append_pinned_log(self, line):
        self.pinned_output.append(line.strip())
