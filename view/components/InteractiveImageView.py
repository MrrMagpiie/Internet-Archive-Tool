from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter
from PyQt6.QtCore import Qt, QTimer

class InteractiveImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()

        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        
        self.scene.addItem(self.pixmap_item)
        
        # Viewport & Interaction Settings
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.apply_high_quality_render)

    def set_pixmap(self, pixmap):
        """Loads the scan and processes it for Moiré-free viewing."""
        if not pixmap.isNull():
            working_pixmap = pixmap
            max_dimension = 2500 
            
            if pixmap.width() > max_dimension or pixmap.height() > max_dimension:
                working_pixmap = pixmap.scaled(
                    max_dimension, max_dimension,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation 
                )
                
            self.pixmap_item.setPixmap(working_pixmap)
            # -------------------------------------
            
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.apply_high_quality_render()
        else:
            print(f"Error: Could not load {pixmap}")


    def wheelEvent(self, event: QWheelEvent):
        """Handles zooming and triggers the debounce timer."""
        # 1. Switch to "Fast Mode" while the user is actively scrolling
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        
        # 2. Calculate and apply the zoom
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
            
        # 3. Restart the timer. 
        self.render_timer.start(250) 

    def apply_high_quality_render(self):
        """Applies the heavy smoothing math only when the user pauses."""
        # 1. Turn high-quality rendering engine back on
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # 2. Force the viewport to redraw itself with the new settings
        self.viewport().update()