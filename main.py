import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import Qt
from ARKO import Ui_MainWindow


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._base_geometries = {
            widget: widget.geometry()
            for widget in vars(self.ui).values()
            if isinstance(widget, QWidget)
            and widget is not self.ui.centralwidget
            and widget is not self.ui.menubar
            and widget is not self.ui.statusbar
        }
        self._base_fonts = {
            widget: widget.font() for widget in self._base_geometries
        }
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "_base_geometries"):
            return

        central_size = self.ui.centralwidget.size()
        base_scroll_area = self._base_geometries[self.ui.scrollArea]
        scale = min(
            central_size.width() / base_scroll_area.width(),
            central_size.height() / base_scroll_area.height(),
        )
        scroll_width = round(base_scroll_area.width() * scale)
        scroll_height = round(base_scroll_area.height() * scale)
        self.ui.scrollArea.setGeometry(
            round((central_size.width() - scroll_width) / 2),
            round((central_size.height() - scroll_height) / 2),
            scroll_width,
            scroll_height,
        )

        for widget, geometry in self._base_geometries.items():
            if widget is self.ui.scrollArea:
                continue
            widget.setGeometry(
                round(geometry.x() * scale),
                round(geometry.y() * scale),
                round(geometry.width() * scale),
                round(geometry.height() * scale),
            )
            font = self._base_fonts[widget]
            point_size = font.pointSizeF()
            if point_size > 0:
                font.setPointSizeF(point_size * scale)
                widget.setFont(font)
            elif font.pixelSize() > 0:
                font.setPixelSize(max(1, round(font.pixelSize() * scale)))
                widget.setFont(font)


app = QApplication(sys.argv)

window = MainWindow()
window.showMaximized()

sys.exit(app.exec())