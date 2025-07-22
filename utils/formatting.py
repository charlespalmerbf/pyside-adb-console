from PySide6.QtGui import QTextCharFormat, QColor

def get_format_for_line(line, retro_font, dark_theme):
    fmt = QTextCharFormat()
    fmt.setFont(retro_font)
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
        fmt.setForeground(QColor("#dcdcdc" if dark_theme else "#222"))

    return fmt

def get_level(line: str):
    line_lower = line.lower()
    if "error" in line_lower:
        return "error"
    elif "warn" in line_lower:
        return "warn"
    elif "info" in line_lower:
        return "info"
    elif "debug" in line_lower:
        return "debug"
    elif "verbose" in line_lower:
        return "verbose"
    return "other"
