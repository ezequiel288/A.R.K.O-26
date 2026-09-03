# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget
from ui_form import Ui_Widget

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Conecta o clique ao método que verifica o estado no momento do clique
        self.ui.pushButton.clicked.connect(self.alternar_checkbox)

           # Conecta o clique do pushButton_2 à função imprimir_texto
        self.ui.btn_nome.clicked.connect(self.imprimir_texto)

    def alternar_checkbox(self):
        # A verificação é feita TODA VEZ que o botão é clicado
        if not self.ui.checkBox.isChecked():
            self.ui.checkBox.setChecked(True)
        else:
            self.ui.checkBox.setChecked(False)


    def imprimir_texto(self):
        # Pega o texto do QLineEdit e imprime no console
        # (Substitua 'lineEdit' pelo nome correto da sua variável se for diferente)
        conteudo = self.ui.nome.text()
        print("Conteúdo digitado:", conteudo)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())