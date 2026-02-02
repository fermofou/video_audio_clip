import sys
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QVBoxLayout,
    QPushButton, QWidget
)
from ffmpeg_utils import extract_audio, export_clip
from waveform import load_waveform
from ui import WaveformView

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Slicer")
        self.resize(1000, 400)

        self.video = QFileDialog.getOpenFileName(
            self, "Open Video")[0]

        wav = extract_audio(self.video)
        waveform, self.duration = load_waveform(wav)

        self.view = WaveformView(waveform)

        btn = QPushButton("Export Selection")
        btn.clicked.connect(self.export)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(btn)

    def export(self):
        w = self.view.width()
        s = min(self.view.sel_start, self.view.sel_end) / w * self.duration
        e = max(self.view.sel_start, self.view.sel_end) / w * self.duration

        out, _ = QFileDialog.getSaveFileName(
            self, "Export", filter="*.wav *.mp3 *.mp4"
        )

        if out:
            export_clip(self.video, s, e, out)

app = QApplication(sys.argv)
w = App()
w.show()
sys.exit(app.exec())
