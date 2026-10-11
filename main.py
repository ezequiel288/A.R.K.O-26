import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt6.QtCore import Qt
from ARKO import Ui_MainWindow


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._game_cards = (
            (
                self.ui.SELgta6,
                self.ui.GTA6_2,
                self.ui.BibliotecaBT,
                self.ui.ComprarBT,
                self.ui.Preco,
                self.ui.Desconto,
            ),
            (
                self.ui.SELMspider,
                self.ui.Mspider,
                self.ui.BibliotecaBT_2,
                self.ui.ComprarBT_2,
                self.ui.Preco_2,
                self.ui.Desconto_2,
            ),
            (
                self.ui.SELMinecraft,
                self.ui.Minecraft,
                self.ui.BibliotecaBT_3,
                self.ui.ComprarBT_3,
                self.ui.Preco_3,
                self.ui.Desconto_3,
            ),
        )
        self._cart_games = set()
        self._library_games = set()
        for index, card in enumerate(self._game_cards):
            card[3].clicked.connect(
                lambda checked=False, game_index=index: self.add_to_cart(game_index)
            )
        self.ui.Pesquisar.clicked.connect(self.show_store)
        self.ui.Store.clicked.connect(self.show_store)
        self.ui.Biblioteca.clicked.connect(self.show_library)
        self.ui.Carrinho.clicked.connect(self.show_cart)
        self.ui.HOME.clicked.connect(self.show_welcome)
        self.ui.ComprarCarrinho.clicked.connect(self.purchase_cart)
        self._update_cart_badge()
        self._show_page("welcome")
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

    def _show_page(self, page):
        self.ui.BemVindo.hide()
        for widget in self.ui.jogos:
            widget.hide()
        self.ui.ComprarCarrinho.hide()

        if page == "welcome":
            self.ui.BemVindo.setText("Bem vindo(a) a A.R.K.O!")
            self.ui.BemVindo.show()
        elif page == "store":
            for index, card in enumerate(self._game_cards):
                for widget in card:
                    if widget is card[2]:
                        continue
                    widget.show()
                card[2].setVisible(index in self._library_games)
            for index, card in enumerate(self._game_cards):
                button = card[3]
                if index in self._library_games:
                    button.setText("Jogar")
                    button.setEnabled(True)
                    button.setStyleSheet(
                        "QPushButton { background-color: #00FF00; color: black; "
                        "border: 2px solid #00FF00; border-radius: 10px; "
                        "font-weight: bold; }"
                    )
                elif index in self._cart_games:
                    button.setText("Adicionado")
                    button.setEnabled(True)
                    button.setStyleSheet(
                        "QPushButton { background-color: #00FF00; color: black; "
                        "border: 2px solid #00FF00; border-radius: 10px; "
                        "font-weight: bold; }"
                    )
                else:
                    button.setText("Adicionar ao carrinho")
                    button.setEnabled(True)
                    button.setStyleSheet(
                        "QPushButton { background-color: #FFFFFF; color: black; "
                        "border: 2px solid #FFFFFF; border-radius: 10px; "
                        "font-weight: bold; }"
                        "QPushButton:hover { background-color: #000000; color: white; }"
                    )
        elif page == "library":
            if not self._library_games:
                self.ui.BemVindo.setText("Sua biblioteca está vazia.")
                self.ui.BemVindo.show()
            else:
                for index in sorted(self._library_games):
                    for widget in self._game_cards[index]:
                        widget.show()
                    button = self._game_cards[index][3]
                    button.setText("Jogar")
                    button.setEnabled(True)
                    button.setStyleSheet(
                        "QPushButton { background-color: #00FF00; color: black; "
                        "border: 2px solid #00FF00; border-radius: 10px; "
                        "font-weight: bold; }"
                    )
        elif page == "cart":
            if not self._cart_games:
                self.ui.BemVindo.setText("Seu carrinho está vazio.")
                self.ui.BemVindo.show()
            else:
                for index in sorted(self._cart_games):
                    for widget in self._game_cards[index]:
                        if widget is self._game_cards[index][2]:
                            continue
                        widget.show()
                self.ui.ComprarCarrinho.show()

        self._active_page = page

    def show_welcome(self):
        self._show_page("welcome")

    def show_store(self):
        self._show_page("store")

    def show_cart(self):
        self._show_page("cart")

    def show_library(self):
        self._show_page("library")

    def add_to_cart(self, game_index):
        if game_index in self._library_games:
            return

        if game_index in self._cart_games:
            self._cart_games.remove(game_index)
        else:
            self._cart_games.add(game_index)

        self._update_cart_badge()
        button = self._game_cards[game_index][3]
        if game_index in self._cart_games:
            button.setText("Adicionado")
            button.setStyleSheet(
                "QPushButton { background-color: #00FF00; color: black; "
                "border: 2px solid #00FF00; border-radius: 10px; font-weight: bold; }"
            )
        else:
            button.setText("Adicionar ao carrinho")
            button.setStyleSheet(
                "QPushButton { background-color: #FFFFFF; color: black; "
                "border: 2px solid #FFFFFF; border-radius: 10px; "
                "font-weight: bold; }"
                "QPushButton:hover { background-color: #000000; color: white; }"
            )

        if self._active_page == "cart":
            self._show_page("cart")

    def _update_cart_badge(self):
        count = len(self._cart_games)
        self.ui.ContadorCarrinho.setText(str(count))
        self.ui.ContadorCarrinho.setVisible(count > 0)

    def purchase_cart(self):
        if not self._cart_games:
            return

        quantity = len(self._cart_games)
        QMessageBox.information(
            self,
            "Compra concluída",
            f"Compra realizada com sucesso ;) ! Jogos comprados: {quantity}.",
        )
        self._library_games.update(self._cart_games)
        self._cart_games.clear()
        self._update_cart_badge()
        self._show_page("cart")

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "_base_geometries"):
            return

        central_size = self.ui.centralwidget.size()
        base_scroll_area = self._base_geometries[self.ui.scrollArea]
        scale_x = central_size.width() / base_scroll_area.width()
        scale_y = central_size.height() / base_scroll_area.height()
        font_scale = min(scale_x, scale_y)
        self.ui.scrollArea.setGeometry(0, 0, central_size.width(), central_size.height())

        for widget, geometry in self._base_geometries.items():
            if widget is self.ui.scrollArea:
                continue
            widget.setGeometry(
                round(geometry.x() * scale_x),
                round(geometry.y() * scale_y),
                round(geometry.width() * scale_x),
                round(geometry.height() * scale_y),
            )
            font = self._base_fonts[widget]
            point_size = font.pointSizeF()
            if point_size > 0:
                font.setPointSizeF(point_size * font_scale)
                widget.setFont(font)
            elif font.pixelSize() > 0:
                font.setPixelSize(max(1, round(font.pixelSize() * font_scale)))
                widget.setFont(font)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()