import re

LOG_LEVELS = ["Verbose", "Debug", "Info", "Warn", "Error", "Assert"]
LOG_LEVEL_COLORS = {
    "V": "#AAAAAA",
    "D": "#33B5E5",
    "I": "#99CC00",
    "W": "#FFBB33",
    "E": "#FF4444",
    "A": "#AA66CC",
}

LOGCAT_LEVEL_PREFIX = {
    "Verbose": "V",
    "Debug": "D",
    "Info": "I",
    "Warn": "W",
    "Error": "E",
    "Assert": "A",
}

def log_matches_filters(
    line, active_levels, regex_pattern, tag_filter, pid_filter, tid_filter
):
    if not line.strip():
        return False

    # Check log level
    if not any(line.startswith(level[0]) for level in active_levels):
        return False

    # Check tag
    if tag_filter and tag_filter not in line:
        return False

    # Check PID/TID
    if pid_filter and pid_filter not in line:
        return False
    if tid_filter and tid_filter not in line:
        return False

    # Check regex
    if regex_pattern:
        try:
            if not re.search(regex_pattern, line):
                return False
        except re.error:
            return False

    return True
