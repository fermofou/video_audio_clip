from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class WaveformView(QWidget):
    def __init__(self, waveform):
        super().__init__()
        self.waveform = waveform
        self.sel_start = None
        self.sel_end = None

    def paintEvent(self, e):
        p = QPainter(self)
        w = self.width()
        h = self.height()

        max_amp = max(self.waveform)

        for i, amp in enumerate(self.waveform):
            x = int(i / len(self.waveform) * w)
            bar_h = int((amp / max_amp) * h)
            p.setPen(QColor(100, 200, 255))
            p.drawLine(x, h, x, h - bar_h)

        if self.sel_start is not None and self.sel_end is not None:
            p.setBrush(QColor(0, 255, 0, 80))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(
                min(self.sel_start, self.sel_end), 0,
                abs(self.sel_end - self.sel_start), h
            )

    def mousePressEvent(self, e):
        self.sel_start = e.position().x()
        self.sel_end = self.sel_start
        self.update()

    def mouseMoveEvent(self, e):
        self.sel_end = e.position().x()
        self.update()

    def mouseReleaseEvent(self, e):
        self.sel_end = e.position().x()
        self.update()
