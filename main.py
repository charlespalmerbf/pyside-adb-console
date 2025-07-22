import sys
from PySide6.QtWidgets import QApplication
from logcat_viewer import LogcatViewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LogcatViewer()
    viewer.show()
    sys.exit(app.exec())
