from PySide6.QtCore import Signal, QObject

class LogSignal(QObject):
    new_line = Signal(str)
