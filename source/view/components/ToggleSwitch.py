from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QRectF, QEasingCurve
from PyQt6.QtGui import QPainter, QColor

class AnimatedToggle(QCheckBox):
    # will need to be reworked to use theme
    def __init__(self, parent=None, active_color="#0366d6"):
        super().__init__(parent)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Colors
        self._bg_color = QColor("#777777")
        self._active_color = QColor(active_color)
        self._thumb_color = QColor("#ffffff")
        
        # Setup Animation
        self._position = 3 
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setDuration(200)
        
        # Connect the built-in checkbox state
        self.stateChanged.connect(self.setup_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()
    # --------------------------------------------------------

    def setup_animation(self, value):
        """Fired automatically when the user clicks the toggle."""
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - 25)
        else:
            self.animation.setEndValue(3)
        self.animation.start()

    def paintEvent(self, e):
        """Hijacks the Qt rendering engine to draw our custom shapes."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw the pill background
        p.setPen(Qt.PenStyle.NoPen)
        track_color = self._active_color if self.isChecked() else self._bg_color
        p.setBrush(track_color)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        
        # 2. Draw the sliding circle (thumb)
        p.setBrush(self._thumb_color)
        p.drawEllipse(QRectF(self._position, 3, 22, 22))
        p.end()
        
    def hitButton(self, pos):
        """Ensures clicking anywhere on the pill toggles the state."""
        return self.contentsRect().contains(pos)