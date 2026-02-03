from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF


class WaveformView(QWidget):
    """
    Clean waveform viewer with intuitive zoom/pan.
    
    Core concept:
    - view_start: absolute sample index where visible window starts
    - view_end: absolute sample index where visible window ends
    - Zoom adjusts window size
    - Pan shifts window position
    """
    
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.player.positionChanged.connect(self.on_position_changed)
        
        # Waveform data
        self.waveform = None
        self.sample_rate = 44100
        self.duration_ms = 0
        
        # View window (in sample indices)
        self.view_start = 0
        self.view_end = 0
        
        # Selection (in pixels, converted to samples when needed)
        self.sel_start_px = None
        self.sel_end_px = None
        self.dragging = False
        
        # Panning
        self.panning = False
        self.last_pan_x = 0
        
        # Playback
        self.position_ms = 0
        
        # Callbacks
        self.zoom_changed = None
        self.pan_changed = None
        
    def set_waveform(self, waveform):
        """Load new waveform data"""
        self.waveform = waveform
        self.view_start = 0
        self.view_end = len(waveform)
        self.sel_start_px = None
        self.sel_end_px = None
        self.position_ms = 0
        self.update()
        
    def clear_selection(self):
        """Clear current selection"""
        self.sel_start_px = None
        self.sel_end_px = None
        self.update()
        
    # ==================== COORDINATE TRANSFORMS ====================
    
    def get_visible_samples(self):
        """Get number of samples currently visible"""
        return max(1, self.view_end - self.view_start)
    
    def get_zoom_level(self):
        """Get current zoom as a multiplier (1.0 = no zoom)"""
        if self.waveform is None:
            return 1.0
        return len(self.waveform) / self.get_visible_samples()
    
    def pixel_to_sample(self, px):
        """Convert pixel position to waveform sample index"""
        if self.waveform is None:
            return 0
        visible = self.get_visible_samples()
        ratio = px / self.width()
        sample = self.view_start + int(ratio * visible)
        return max(0, min(len(self.waveform) - 1, sample))
    
    def sample_to_pixel(self, sample):
        """Convert waveform sample index to pixel position"""
        if self.waveform is None:
            return 0
        visible = self.get_visible_samples()
        if visible == 0:
            return 0
        ratio = (sample - self.view_start) / visible
        return int(ratio * self.width())
    
    def sample_to_ms(self, sample):
        """Convert sample index to milliseconds"""
        if self.waveform is None:
            return 0
        duration = self.player.duration()
        return int((sample / len(self.waveform)) * duration)
    
    def ms_to_sample(self, ms):
        """Convert milliseconds to sample index"""
        if self.waveform is None:
            return 0
        duration = self.player.duration()
        if duration == 0:
            return 0
        return int((ms / duration) * len(self.waveform))
    
    # ==================== ZOOM & PAN ====================
    
    def zoom_at_point(self, px, zoom_in=True):
        """Zoom in or out, keeping the point under 'px' stable"""
        if self.waveform is None:
            return
        
        # Get the sample that's currently under this pixel
        focus_sample = self.pixel_to_sample(px)
        
        # Calculate new window size
        current_size = self.get_visible_samples()
        if zoom_in:
            new_size = max(50, int(current_size / 1.3))
        else:
            new_size = min(len(self.waveform), int(current_size * 1.3))
        
        # Calculate where the window should start to keep focus_sample under px
        ratio = px / self.width()
        new_start = focus_sample - int(new_size * ratio)
        
        # Clamp to valid range
        new_start = max(0, min(len(self.waveform) - new_size, new_start))
        new_end = new_start + new_size
        
        self.view_start = new_start
        self.view_end = new_end
        
        # Notify
        if self.zoom_changed:
            self.zoom_changed(self.get_zoom_level())
        if self.pan_changed:
            self.pan_changed(self.view_start / max(1, len(self.waveform) - new_size))
            
        self.update()
    
    def pan_by_pixels(self, dx):
        """Pan the view by a pixel amount"""
        if self.waveform is None:
            return
        
        # Convert pixel delta to sample delta
        visible = self.get_visible_samples()
        sample_delta = int((dx / self.width()) * visible)
        
        # Shift window
        new_start = self.view_start - sample_delta
        window_size = visible
        
        # Clamp
        new_start = max(0, min(len(self.waveform) - window_size, new_start))
        new_end = new_start + window_size
        
        self.view_start = new_start
        self.view_end = new_end
        
        # Notify
        if self.pan_changed:
            max_offset = len(self.waveform) - window_size
            if max_offset > 0:
                self.pan_changed(new_start / max_offset)
        
        self.update()
    
    def set_pan_normalized(self, value):
        """Set pan position from 0.0 to 1.0"""
        if self.waveform is None:
            return
        
        window_size = self.get_visible_samples()
        max_start = len(self.waveform) - window_size
        
        self.view_start = int(value * max_start)
        self.view_end = self.view_start + window_size
        
        self.update()
    
    def reset_zoom(self):
        """Reset to full view"""
        if self.waveform is None:
            return
        self.view_start = 0
        self.view_end = len(self.waveform)
        if self.zoom_changed:
            self.zoom_changed(1.0)
        if self.pan_changed:
            self.pan_changed(0.0)
        self.update()
    
    # ==================== SELECTION ====================
    
    def get_selection_ms(self):
        """Get selection in milliseconds, or None"""
        if self.sel_start_px is None or self.sel_end_px is None:
            return None
        
        # Must be at least a few pixels wide
        if abs(self.sel_end_px - self.sel_start_px) < 5:
            return None
        
        # Convert to samples
        start_sample = self.pixel_to_sample(min(self.sel_start_px, self.sel_end_px))
        end_sample = self.pixel_to_sample(max(self.sel_start_px, self.sel_end_px))
        
        # Convert to ms
        start_ms = self.sample_to_ms(start_sample)
        end_ms = self.sample_to_ms(end_sample)
        
        return start_ms, end_ms
    
    # ==================== EVENTS ====================
    
    def wheelEvent(self, event):
        """Mouse wheel = zoom at cursor"""
        if self.waveform is None:
            return
        
        zoom_in = event.angleDelta().y() > 0
        mouse_x = int(event.position().x())
        self.zoom_at_point(mouse_x, zoom_in)
    
    def mousePressEvent(self, event):
        """Start selection or panning"""
        x = int(event.position().x())
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Start selection
            self.dragging = True
            self.sel_start_px = x
            self.sel_end_px = x
            
            # Jump playhead
            sample = self.pixel_to_sample(x)
            ms = self.sample_to_ms(sample)
            self.player.setPosition(ms)
            
        elif event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self.panning = True
            self.last_pan_x = x
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        self.update()
    
    def mouseMoveEvent(self, event):
        """Update selection or pan"""
        x = int(event.position().x())
        
        if self.dragging:
            self.sel_end_px = x
            # Update playhead while dragging
            sample = self.pixel_to_sample(x)
            ms = self.sample_to_ms(sample)
            self.player.setPosition(ms)
            self.update()
            
        elif self.panning:
            dx = x - self.last_pan_x
            self.pan_by_pixels(dx)
            self.last_pan_x = x
    
    def mouseReleaseEvent(self, event):
        """End selection or panning"""
        if self.dragging:
            self.dragging = False
            x = int(event.position().x())
            self.sel_end_px = x
            
            # If too small, clear selection
            if abs(self.sel_end_px - self.sel_start_px) < 5:
                self.sel_start_px = None
                self.sel_end_px = None
            
            self.update()
            
        elif self.panning:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseDoubleClickEvent(self, event):
        """Double click = reset zoom"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_zoom()
    
    # ==================== RENDERING ====================
    
    def on_position_changed(self, pos_ms):
        """Player position changed"""
        self.position_ms = pos_ms
        
        # Loop if selection active
        sel = self.get_selection_ms()
        if sel:
            start_ms, end_ms = sel
            if pos_ms >= end_ms:
                self.player.setPosition(start_ms)
        
        self.update()
    
    def paintEvent(self, event):
        """Draw waveform, selection, and playhead"""
        if self.waveform is None:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor(30, 30, 35))
        
        # Get visible data
        start_idx = max(0, self.view_start)
        end_idx = min(len(self.waveform), self.view_end)
        visible_data = self.waveform[start_idx:end_idx]
        
        if len(visible_data) == 0:
            return
        
        # Downsample if needed
        samples_per_pixel = len(visible_data) / w
        
        if samples_per_pixel > 1:
            # Many samples per pixel - draw bars
            max_amp = max(visible_data) if len(visible_data) > 0 else 1
            painter.setPen(QColor(100, 200, 255))
            
            for x in range(w):
                idx_start = int(x * samples_per_pixel)
                idx_end = int((x + 1) * samples_per_pixel)
                idx_end = min(idx_end, len(visible_data))
                
                if idx_start < len(visible_data):
                    segment = visible_data[idx_start:idx_end]
                    if len(segment) > 0:
                        amp = max(segment)
                        bar_height = int((amp / max_amp) * h * 0.9)
                        y1 = h // 2 - bar_height // 2
                        y2 = h // 2 + bar_height // 2
                        painter.drawLine(x, y1, x, y2)
        else:
            # Few samples per pixel - draw line
            max_amp = max(visible_data) if len(visible_data) > 0 else 1
            painter.setPen(QPen(QColor(100, 200, 255), 2))
            
            points = []
            for i, amp in enumerate(visible_data):
                x = int((i / len(visible_data)) * w)
                y = h // 2 - int((amp / max_amp) * h * 0.4)
                points.append(QPointF(x, y))
            
            if len(points) > 1:
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
        
        # Draw selection
        if self.sel_start_px is not None and self.sel_end_px is not None:
            x1 = int(min(self.sel_start_px, self.sel_end_px))
            x2 = int(max(self.sel_start_px, self.sel_end_px))
            
            painter.fillRect(x1, 0, x2 - x1, h, QColor(100, 255, 100, 60))
            painter.setPen(QPen(QColor(100, 255, 100), 2))
            painter.drawLine(x1, 0, x1, h)
            painter.drawLine(x2, 0, x2, h)
        
        # Draw playhead
        playhead_sample = self.ms_to_sample(self.position_ms)
        playhead_px = self.sample_to_pixel(playhead_sample)
        
        if 0 <= playhead_px <= w:
            painter.setPen(QPen(QColor(255, 80, 80), 3))
            painter.drawLine(playhead_px, 0, playhead_px, h)