from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow

class LojaWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("ui/loja.ui", self)

        self.btnComprar.clicked.connect(self.comprar_jogo)
        self.btnCarrinho.clicked.connect(self.abrir_carrinho)

    def comprar_jogo(self):
        print("Jogo adicionado ao carrinho!")

    def abrir_carrinho(self):
        print("Abrindo carrinho...")

