from pathlib import Path

from PyQt5.QtCore import (
    Qt,
    QPoint,
    QPoint,
    QRectF,
    QPointF,
    QSizeF,
)
from PyQt5.QtGui import (
    QColor,
    QPixmap,
    QMouseEvent,
    QWheelEvent,
    QBrush,
    QPainter,
)
from PyQt5.QtWidgets import QFrame, QGraphicsView

from .graphics_scene import GraphicsScene


class GraphicsView(QGraphicsView):
    def __init__(self, brush_feedback, parent=None):
        super().__init__(parent)
        self._scene = GraphicsScene(self)
        self._pan_mode = False
        self._last_pos = QPoint()
        self.brush_feedback = brush_feedback

        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(50, 50, 50)))
        self.setFrameShape(QFrame.Shape.NoFrame)  # removes white widget outline
        self.setRenderHint(QPainter.RenderHint.HighQualityAntialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.BlankCursor)

    def reset_zoom(self):
        self.fitInView(self._scene.image_item, Qt.AspectRatioMode.KeepAspectRatio)

    def clear_label(self):
        self._scene.label_item.clear()

    def save_label_to(self, path: Path):
        self._scene.save_label(path)

    def load_sample(self, image_path: Path, label_path: Path):
        print(f"load {image_path.stem} sample")
        image = QPixmap(str(image_path))
        self._scene.setSceneRect(QRectF(QPointF(), QSizeF(image.size())))
        self._scene.image_item.setPixmap(QPixmap(str(image_path)))
        if label_path.exists():
            self._scene.label_item.set_image(str(label_path))
        else:
            self._scene.label_item.clear()
        self.fitInView(self._scene.image_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.centerOn(self._scene.image_item)

    def scrollBy(self, point: QPoint):
        h_val = self.horizontalScrollBar().value() - point.x()
        v_val = self.verticalScrollBar().value() - point.y()
        self.horizontalScrollBar().setValue(h_val)
        self.verticalScrollBar().setValue(v_val)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._pan_mode = True
            self._last_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_mode:
            curr_pos = event.pos()
            delta = curr_pos - self._last_pos
            self.scrollBy(delta)
            self._last_pos = curr_pos
        super().mouseMoveEvent(event)  # allows proper zoom-to-cursor

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._pan_mode = False
            self.setCursor(Qt.CursorShape.BlankCursor)

    def wheelEvent(self, event: QWheelEvent) -> None:
        forward = event.angleDelta().y() > 0
        sign = "+" if forward else "-"
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            # zoom in/out
            factor = 1.25 if forward else 0.8
            self.scale(factor, factor)
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # change brush size
            sign = -1 if forward else 1
            self._scene.change_brush_size(sign, self.brush_feedback)
