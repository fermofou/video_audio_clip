# 🎵 Audio Slicer - Waveform-Based Audio Clipper

A PyQt6-based desktop application for visually selecting and extracting segments from audio and video files. Features an intuitive waveform viewer with zoom, pan, and precision selection tools.

![Audio Slicer Interface](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red.svg)

---

## 🌟 Features

- **Visual Waveform Display** - See your audio as you work with it
- **Intuitive Zoom & Pan** - Mouse-centered zoom, smooth panning
- **Precise Selection** - Click and drag to select exact regions
- **Video Support** - Automatically extracts audio from MP4 files
- **Audio Looping** - Preview your selection on loop before clipping
- **Multiple Export** - Create unlimited clips from one file
- **Dark Theme** - Easy on the eyes for long editing sessions


### Prerequisites

1. **Python 3.8+**
   ```bash
   python --version  # Check your version
   ```

2. **FFmpeg** (for audio/video processing)
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt install ffmpeg
   ```
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Windows:**
   Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

3. **Python Dependencies**
   ```bash
   pip install PyQt6 numpy
   ```


## User Guide

### Controls Reference

#### Mouse Controls
| Action | Result |
|--------|--------|
| **Scroll Wheel Up** | Zoom in (centered on cursor) |
| **Scroll Wheel Down** | Zoom out (centered on cursor) |
| **Left Click + Drag** | Select audio region |
| **Middle Click + Drag** | Pan the view left/right |
| **Double Click** | Reset zoom to full view |

#### Buttons
| Button | Function |
|--------|----------|
| **📂 Open File** | Load audio/video file |
| **▶ Play** | Start/pause playback |
| **✂ Clip Selection** | Export selected region |
| **❌ Clear Selection** | Remove current selection |
| **🔍 Reset Zoom** | Return to full waveform view |
| **🚪 Exit** | Close application |

#### Pan Slider
- Only enabled when zoomed in
- Drag to scroll through the waveform
- Auto-updates when panning with mouse

### Keyboard Shortcuts
- `Space` - Play/Pause (when player is focused)
- `Esc` - Clear selection

---

## Project Structure

```
audio-slicer/
│
├── main.py          # Main application window and UI logic
├── ui.py      # Waveform viewer widget (core visualization)
├── audio.py            # Audio processing utilities
├── clips/              # Output directory (auto-created)
│   ├── audio_1.wav
│   ├── audio_2.wav
│   └── ...
│
└── README.md           # This file
```

### File Descriptions

#### `main.py`
- Application entry point
- Main window setup
- Button handlers
- Player control
- File I/O dialogs

#### `ui.py` (WaveformView)
- Waveform visualization
- Zoom/pan logic
- Selection handling
- Coordinate transformations
- Mouse/wheel event processing

#### `audio.py`
- FFmpeg wrapper functions
- Audio extraction from video
- Waveform data generation
- Audio clipping operations

