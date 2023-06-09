from pathlib import Path

from PyQt5.QtCore import (
    Qt,
    QPoint,
    QLineF,
    QPoint,
    QRectF,
    QPointF,
    QSizeF,
)
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsSceneMouseEvent,
    QMainWindow,
    QFrame,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGroupBox,
    QPushButton,
    QSlider,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt5.QtGui import (
    QColor,
    QKeyEvent,
    QPixmap,
    QMouseEvent,
    QWheelEvent,
    QBrush,
    QPainter,
    QPen,
)


class BrushCursor(QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        rect = QRectF(-25, -25, 50, 50)
        self.setRect(rect)
        self._border_pen = QPen()
        self._border_pen.setColor(Qt.GlobalColor.black)
        self._border_pen.setWidth(1)
        self._fill_brush = QBrush()
        self._fill_brush.setColor(Qt.GlobalColor.transparent)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(self._border_pen)
        painter.setBrush(self._fill_brush)
        painter.drawEllipse(self.rect())

    def change_size_by(self, value: int):
        rect = self.rect()
        offset = value / 2
        size = int(rect.width()) + value
        rect.setX(rect.x() - offset)
        rect.setY(rect.y() - offset)
        rect.setWidth(size)
        rect.setHeight(size)
        self.setRect(rect)

    def set_border_color(self, color: QColor):
        self._border_pen.setColor(color)


class LabelLayer(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpacity(0.5)
        self._erase_state = False
        self._brush_color = QColor(0, 0, 0)
        self._brush_size = 50
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self._pixmap = QPixmap()
        self.line = QLineF()
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_brush_color(self, color: QColor):
        self._brush_color = color

    def set_eraser(self, value: bool):
        self._erase_state = value

    def change_brush_size_by(self, size: int):
        self._brush_size += size

    def draw_line(self):
        painter = QPainter(self._pixmap)
        if self._erase_state:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        pen = QPen(self._brush_color, self._brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.line)
        painter.end()
        self.update()

    def set_image(self, path: str):
        r = self.parentItem().pixmap().rect()
        self.setRect(QRectF(r))
        self._pixmap.load(path)

    def clear(self):
        r = self.parentItem().pixmap().rect()
        self.setRect(QRectF(r))
        self._pixmap = QPixmap(r.size())
        self._pixmap.fill(Qt.GlobalColor.transparent)

    def export_pixmap(self, out_path: Path):
        self._pixmap.save(str(out_path))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.save()
        painter.drawPixmap(QPoint(), self._pixmap)
        painter.restore()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.line.setP1(event.pos())
        self.line.setP2(event.pos())
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.line.setP2(event.pos())
        self.draw_line()
        self.line.setP1(event.pos())
        super().mouseMoveEvent(event)


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_item = QGraphicsPixmapItem()
        self.label_item = LabelLayer(self.image_item)
        self.cursor_item = BrushCursor(self.image_item)

        self.addItem(self.image_item)

    def set_brush_color(self, color: QColor):
        self.cursor_item.set_border_color(color)
        self.label_item.set_brush_color(color)

    def set_brush_eraser(self, value):
        self.label_item.set_eraser(value)

    def change_brush_size_by(self, value: int):
        self.cursor_item.change_size_by(value)
        self.label_item.change_brush_size_by(value)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.cursor_item.setPos(event.scenePos())
        super().mouseMoveEvent(event)

    def save_label(self, label_path: Path):
        self.label_item.export_pixmap(label_path)


class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = GraphicsScene(self)
        self._pan_mode = False
        self._last_pos = QPoint()

        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(50, 50, 50)))
        self.setFrameShape(QFrame.Shape.NoFrame)  # removes white widget outline
        self.setRenderHint(QPainter.RenderHint.HighQualityAntialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

    def wheelEvent(self, event: QWheelEvent) -> None:
        forward = event.angleDelta().y() > 0
        sign = "+" if forward else "-"
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            # zoom in/out
            factor = 1.25 if forward else 0.8
            self.scale(factor, factor)
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # change brush size
            value = 5 if forward else -5
            self._scene.change_brush_size_by(value)


class MainWindow(QMainWindow):
    def __init__(self, workdir: str):
        super(MainWindow, self).__init__()
        self.setWindowTitle("sam_annotator")
        self.resize(1000, 1000)
        self._workdir = Path(workdir)
        self._image_dir = self._workdir / "images"
        self._label_dir = self._workdir / "labels"
        self._label_dir.mkdir(exist_ok=True)
        self._image_stems = [path.stem for path in sorted(self._image_dir.iterdir())]

        self._graphics_view = GraphicsView()

        pen_group = QGroupBox(self.tr("Pen settings"))

        self.pen_button = QPushButton()
        # color = QColor(0, 0, 0)
        # self.pen_button.setStyleSheet("background-color: {}".format(color.name()))
        self.pen_slider = QSlider(
            Qt.Horizontal,
            minimum=1,
            maximum=100,
            value=10,
        )
        pen_lay = QFormLayout(pen_group)
        pen_lay.addRow(self.tr("Pen color"), self.pen_button)
        pen_lay.addRow(self.tr("Pen size"), self.pen_slider)

        vlay = QVBoxLayout()
        vlay.addWidget(pen_group)
        vlay.addStretch()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        lay = QHBoxLayout(central_widget)
        lay.addWidget(self._graphics_view, stretch=1)
        lay.addLayout(vlay, stretch=0)

        self._curr_id = 0

    def load_first_sample(self):
        self._curr_id = 0
        name = f"{self._image_stems[self._curr_id]}.png"
        image_path = self._image_dir / name
        label_path = self._label_dir / name
        self._graphics_view.load_sample(image_path, label_path)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.key() == Qt.Key.Key_Space:
            self._graphics_view.fitInView(
                self._graphics_view._scene.image_item,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        elif a0.key() == Qt.Key.Key_E:
            self._graphics_view._scene.set_brush_eraser(True)
        elif a0.key() == Qt.Key.Key_0:
            self._graphics_view._scene.set_brush_eraser(False)
            self._graphics_view._scene.set_brush_color(QColor(0, 0, 0))
        elif a0.key() == Qt.Key.Key_1:
            self._graphics_view._scene.set_brush_eraser(False)
            self._graphics_view._scene.set_brush_color(QColor(255, 0, 0))
        elif a0.key() == Qt.Key.Key_2:
            self._graphics_view._scene.set_brush_eraser(False)
            self._graphics_view._scene.set_brush_color(QColor(0, 255, 0))
        elif a0.key() == Qt.Key.Key_3:
            self._graphics_view._scene.set_brush_eraser(False)
            self._graphics_view._scene.set_brush_color(QColor(0, 0, 255))
        elif a0.key() == Qt.Key.Key_Comma:
            self.switch_sample_by(-1)
        elif a0.key() == Qt.Key.Key_Period:
            self.switch_sample_by(1)

        return super().keyPressEvent(a0)

    def switch_sample_by(self, step: int):
        if step == 0:
            return
        curr_label_path = self._label_dir / f"{self._image_stems[self._curr_id]}.png"
        self._graphics_view._scene.save_label(curr_label_path)
        max_id = len(self._image_stems) - 1
        corner_case_id = 0 if step < 0 else max_id
        new_id = self._curr_id + step
        new_id = new_id if new_id in range(max_id + 1) else corner_case_id
        new_name = f"{self._image_stems[new_id]}.png"
        self._curr_id = new_id
        image_path = self._image_dir / new_name
        label_path = self._label_dir / new_name
        self._graphics_view.load_sample(image_path, label_path)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mw = MainWindow("/hdd_ext4/datasets/images/raw_2")
    mw.show()
    mw.load_first_sample()
    sys.exit(app.exec_())
