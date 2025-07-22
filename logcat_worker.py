import subprocess
import threading

class LogcatWorker(threading.Thread):
    def __init__(self, signal, buffer: str):
        super().__init__(daemon=True)
        self.signal = signal
        self.running = True
        self.paused = False
        self.process = None
        self.buffer = buffer

    def run(self):
        self.process = subprocess.Popen(
            ["adb", "logcat", "-b", self.buffer],
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

    def restart(self, buffer):
        self.stop()
        self.buffer = buffer
        self.running = True
        self.paused = False
        self.run()
