# main.py
import sys
import os
from pathlib import Path

os.environ["QT_LOGGING_RULES"] = (
    "qt.multimedia.*=false;"
    "qt.core.qfuture.*=false"
)

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QSlider, QLabel
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import Qt, QUrl

from audio import load_waveform, extract_audio, clip_audio
from ui import WaveformView


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Audio Slicer - Improved")
        self.setFixedSize(1200, 750)

        # ---- audio ----
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        # ---- waveform ----
        self.waveform = WaveformView(self.player)
        self.waveform.zoom_changed = self.on_zoom_changed
        self.waveform.pan_changed = self.on_pan_changed

        # ---- buttons ----
        self.open_btn = QPushButton("📂 Open File")
        self.play_btn = QPushButton("▶ Play")
        self.clip_btn = QPushButton("✂ Clip Selection")
        self.clear_btn = QPushButton("❌ Clear Selection")
        self.reset_zoom_btn = QPushButton("🔍 Reset Zoom")
        self.exit_btn = QPushButton("🚪 Exit")

        self.play_btn.setEnabled(False)
        self.clip_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.reset_zoom_btn.setEnabled(False)

        self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.toggle_play)
        self.clip_btn.clicked.connect(self.clip_selection)
        self.clear_btn.clicked.connect(self.waveform.clear_selection)
        self.reset_zoom_btn.clicked.connect(self.waveform.reset_zoom)
        self.exit_btn.clicked.connect(self.close)

        # ---- zoom display ----
        self.zoom_label = QLabel("Zoom: 1.0x")
        self.zoom_label.setMinimumWidth(100)

        # ---- pan slider ----
        self.pan_label = QLabel("Pan:")
        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setRange(0, 1000)
        self.pan_slider.setValue(0)
        self.pan_slider.setEnabled(False)
        self.pan_slider.valueChanged.connect(self.on_slider_moved)
        
        # Flag to prevent feedback loop
        self.updating_slider = False

        # ---- info label ----
        self.info_label = QLabel("💡 Scroll to zoom | Left-click & drag to select | Middle-click & drag to pan | Double-click to reset")
        self.info_label.setStyleSheet("color: #888; font-size: 11px;")

        # ---- layout ----
        layout = QVBoxLayout(self)

        # Top buttons
        top_row = QHBoxLayout()
        top_row.addWidget(self.open_btn)
        top_row.addWidget(self.play_btn)
        top_row.addWidget(self.clip_btn)
        top_row.addWidget(self.clear_btn)
        top_row.addWidget(self.reset_zoom_btn)
        top_row.addStretch()
        top_row.addWidget(self.zoom_label)
        top_row.addWidget(self.exit_btn)

        # Pan controls
        pan_row = QHBoxLayout()
        pan_row.addWidget(self.pan_label)
        pan_row.addWidget(self.pan_slider)

        layout.addLayout(top_row)
        layout.addWidget(self.info_label)
        layout.addWidget(self.waveform, stretch=1)
        layout.addLayout(pan_row)

        # ---- state ----
        self.is_playing = False
        self.current_audio_path = None
        self.clip_index = 1

    # -------------------------
    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Open media file",
            "",
            "Media Files (*.wav *.mp3 *.mp4);;All Files (*)"
        )
        if not file:
            return

        path = Path(file)

        # Extract audio from video if needed
        if path.suffix.lower() == ".mp4":
            try:
                path = extract_audio(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to extract audio:\n{e}")
                return

        self.current_audio_path = path
        self.clip_index = 1

        # Load into player
        self.player.setSource(QUrl.fromLocalFile(str(path)))

        # Load waveform
        try:
            waveform = load_waveform(path)
            self.waveform.set_waveform(waveform)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load waveform:\n{e}")
            return

        # Enable controls
        self.play_btn.setEnabled(True)
        self.clip_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.reset_zoom_btn.setEnabled(True)
        self.pan_slider.setEnabled(True)
        
        self.zoom_label.setText("Zoom: 1.0x")
        self.pan_slider.setValue(0)

    # -------------------------
    def toggle_play(self):
        if self.is_playing:
            self.player.pause()
            self.play_btn.setText("▶ Play")
        else:
            self.player.play()
            self.play_btn.setText("⏸ Pause")
        self.is_playing = not self.is_playing

    # -------------------------
    def on_slider_moved(self, value):
        """User moved the pan slider"""
        if not self.updating_slider:
            normalized = value / 1000.0
            self.waveform.set_pan_normalized(normalized)

    def on_zoom_changed(self, zoom_level):
        """Waveform zoom changed (from mouse wheel)"""
        self.zoom_label.setText(f"Zoom: {zoom_level:.1f}x")
        
        # Enable/disable slider based on zoom
        if zoom_level <= 1.0:
            self.pan_slider.setEnabled(False)
        else:
            self.pan_slider.setEnabled(True)

    def on_pan_changed(self, normalized_position):
        """Waveform pan position changed"""
        self.updating_slider = True
        self.pan_slider.setValue(int(normalized_position * 1000))
        self.updating_slider = False

    # -------------------------
    def clip_selection(self):
        sel = self.waveform.get_selection_ms()
        if not sel:
            QMessageBox.warning(self, "No selection", "Please select a region first")
            return

        start_ms, end_ms = sel
        if end_ms <= start_ms:
            QMessageBox.warning(self, "Invalid selection", "Selection is too small")
            return

        # Create clips directory
        clips_dir = Path.cwd() / "clips"
        clips_dir.mkdir(exist_ok=True)

        try:
            out = clip_audio(
                self.current_audio_path,
                start_ms,
                end_ms
            )
            self.clip_index += 1
            QMessageBox.information(self, "Success", f"Clip saved to:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create clip:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Dark theme
    app.setStyle("Fusion")
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())