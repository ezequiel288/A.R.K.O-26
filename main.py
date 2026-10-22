import csv
import hashlib
import json
import secrets
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ARKO import Ui_MainWindow


class MainWindow(QMainWindow):
    PASSWORD_HASH_ITERATIONS = 600_000
    BUILTIN_GAMES = (
        {
            "titulo": "Grand Theft Auto VI",
            "descricao": "Aventura de mundo aberto",
            "preco": 314.30,
            "empresa": "Rockstar Games",
        },
        {
            "titulo": "Marvel's Spider-Man",
            "descricao": "Aventura de super-herói",
            "preco": 87.40,
            "empresa": "Insomniac Games",
        },
        {
            "titulo": "Minecraft",
            "descricao": "Construa e explore mundos",
            "preco": 59.40,
            "empresa": "Mojang Studios",
        },
    )

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._current_user_email = None
        self._setup_registration_tab()
        self._setup_friends_page()
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
        self._load_transactions()
        self._load_custom_games()
        self._setup_library_page()
        for index, card in enumerate(self._game_cards):
            card[3].clicked.connect(
                lambda checked=False, game_index=index: self.add_to_cart(game_index)
            )
        self.ui.Pesquisar.clicked.connect(self.search_store)
        self.ui.Store.clicked.connect(self.show_store)
        self.ui.Biblioteca.clicked.connect(self.show_library)
        self.ui.Amigos.clicked.connect(self.show_friends)
        self.ui.Carrinho.clicked.connect(self.show_cart)
        self.ui.Conta.clicked.connect(self.show_account)
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
        self._base_geometries[self._account_tabs] = self._account_tabs.geometry()
        self._base_geometries[self._friends_panel] = self._friends_panel.geometry()
        self._base_geometries[self._library_panel] = self._library_panel.geometry()
        self._base_fonts = {
            widget: widget.font() for widget in self._base_geometries
        }
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def _show_page(self, page):
        self.ui.BemVindo.hide()
        self._account_tabs.hide()
        self._friends_panel.hide()
        self._library_panel.hide()
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
            self._refresh_library()
            self._library_panel.show()
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
        elif page == "registration":
            self._account_tabs.show()
        elif page == "friends":
            self._friends_panel.show()

        self._active_page = page

    def _setup_registration_tab(self):
        self._account_tabs = QTabWidget(parent=self.ui.Barra1)
        self._account_tabs.setObjectName("AccountTabs")
        self._account_tabs.setGeometry(130, 180, 1181, 641)
        self._account_tabs.setStyleSheet(
            "QTabWidget::pane { background-color: #000000; "
            "border: 2px solid #FFFFFF; border-radius: 8px; }"
            "QTabBar::tab { background-color: #202020; color: white; "
            "padding: 10px 22px; }"
            "QTabBar::tab:selected { background-color: #00FF00; color: black; }"
        )

        registration_tab = QWidget()
        registration_layout = QVBoxLayout(registration_tab)
        registration_layout.addStretch()

        card_row = QHBoxLayout()
        card_row.addStretch()
        card = QFrame()
        card.setObjectName("RegistrationCard")
        card.setMaximumWidth(520)
        card.setStyleSheet(
            "QFrame#RegistrationCard { background-color: #202020; "
            "border: 1px solid #FFFFFF; border-radius: 12px; }"
            "QLabel { color: white; }"
            "QLineEdit { background-color: #FFFFFF; color: #000000; "
            "border: 1px solid #00FF00; border-radius: 6px; padding: 8px; }"
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 8px; "
            "font-weight: bold; padding: 9px; }"
            "QPushButton:hover { background-color: #FFFFFF; "
            "border-color: #FFFFFF; }"
        )
        card_layout = QVBoxLayout(card)

        title = QLabel("Criar conta")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        card_layout.addWidget(title)

        form = QFormLayout()
        self._registration_name = QLineEdit()
        self._registration_name.setPlaceholderText("Seu nome")
        self._registration_email = QLineEdit()
        self._registration_email.setPlaceholderText("voce@exemplo.com")
        self._registration_password = QLineEdit()
        self._registration_password.setPlaceholderText("Sua senha")
        self._registration_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nome:", self._registration_name)
        form.addRow("E-mail:", self._registration_email)
        form.addRow("Senha:", self._registration_password)
        card_layout.addLayout(form)

        self._registration_status = QLabel("")
        self._registration_status.setWordWrap(True)
        self._registration_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._registration_status)

        register_button = QPushButton("Cadastrar")
        register_button.clicked.connect(self.register_user)
        card_layout.addWidget(register_button)

        card_row.addWidget(card)
        card_row.addStretch()
        registration_layout.addLayout(card_row)
        registration_layout.addStretch()
        self._account_tabs.addTab(registration_tab, "Cadastro")

        account_tab = QWidget()
        account_layout = QVBoxLayout(account_tab)
        account_layout.setContentsMargins(24, 24, 24, 24)
        self._account_welcome = QLabel("Bem-vindo!")
        self._account_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._account_welcome.setStyleSheet(
            "background-color: #202020; color: #00FF00; "
            "border: 2px solid #00FF00; border-radius: 10px; "
            "font-size: 22px; font-weight: bold; padding: 16px;"
        )
        account_layout.addWidget(self._account_welcome)

        account_actions = QHBoxLayout()
        account_actions.addStretch()
        edit_account_button = QPushButton("Alterar cadastro")
        edit_account_button.clicked.connect(self.show_account_edit)
        account_actions.addWidget(edit_account_button)
        logout_button = QPushButton("Sair da conta")
        logout_button.clicked.connect(self.logout)
        account_actions.addWidget(logout_button)
        account_actions.addStretch()
        account_layout.addLayout(account_actions)

        self._account_edit_panel = QFrame()
        self._account_edit_panel.setObjectName("RegistrationCard")
        self._account_edit_panel.setMaximumWidth(620)
        self._account_edit_panel.setStyleSheet(card.styleSheet())
        account_edit_layout = QVBoxLayout(self._account_edit_panel)
        account_form = QFormLayout()
        self._account_name = QLineEdit()
        self._account_email = QLineEdit()
        self._account_password = QLineEdit()
        self._account_password.setPlaceholderText("Deixe em branco para manter")
        self._account_password.setEchoMode(QLineEdit.EchoMode.Password)
        account_form.addRow("Nome:", self._account_name)
        account_form.addRow("E-mail:", self._account_email)
        account_form.addRow("Nova senha:", self._account_password)
        account_edit_layout.addLayout(account_form)

        self._account_status = QLabel("")
        self._account_status.setWordWrap(True)
        self._account_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        account_edit_layout.addWidget(self._account_status)

        save_account_button = QPushButton("Salvar alterações")
        save_account_button.clicked.connect(self.update_account)
        account_edit_layout.addWidget(save_account_button)
        account_edit_row = QHBoxLayout()
        account_edit_row.addStretch()
        account_edit_row.addWidget(self._account_edit_panel)
        account_edit_row.addStretch()
        account_layout.addLayout(account_edit_row)
        account_layout.addStretch()
        self._account_edit_panel.hide()
        self._account_tabs.addTab(account_tab, "Minha conta")
        self._account_tabs.setTabVisible(1, False)
        self._account_tabs.hide()

    def _setup_friends_page(self):
        self._friends_panel = QWidget(parent=self.ui.Barra1)
        self._friends_panel.setObjectName("FriendsPanel")
        self._friends_panel.setGeometry(130, 180, 1181, 641)
        self._friends_panel.setStyleSheet(
            "QWidget#FriendsPanel { background-color: #000000; "
            "border: 2px solid #FFFFFF; border-radius: 8px; }"
            "QLabel { color: white; }"
            "QLineEdit { background-color: #FFFFFF; color: #000000; "
            "border: 1px solid #00FF00; border-radius: 6px; padding: 8px; }"
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 8px; "
            "font-weight: bold; padding: 9px; }"
            "QPushButton:hover { background-color: #FFFFFF; "
            "border-color: #FFFFFF; }"
            "QListWidget { background-color: #202020; color: white; "
            "border: 1px solid #FFFFFF; border-radius: 6px; }"
        )

        layout = QVBoxLayout(self._friends_panel)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Amigos")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        self._add_friend_button = QPushButton("Adicionar amigo")
        self._add_friend_button.clicked.connect(self.show_add_friend_form)
        layout.addWidget(self._add_friend_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._friends_list = QListWidget()
        self._friends_list.setMinimumHeight(220)
        layout.addWidget(self._friends_list)

        friend_actions = QHBoxLayout()
        self._edit_friend_button = QPushButton("Alterar amigo selecionado")
        self._edit_friend_button.clicked.connect(self.show_edit_friend_form)
        friend_actions.addWidget(self._edit_friend_button)
        self._remove_friend_button = QPushButton("Remover amigo selecionado")
        self._remove_friend_button.clicked.connect(self.remove_friend)
        friend_actions.addWidget(self._remove_friend_button)
        layout.addLayout(friend_actions)

        self._add_friend_form = QFrame()
        self._add_friend_form.setMaximumWidth(620)
        self._add_friend_form.setStyleSheet(
            "QFrame { background-color: #202020; "
            "border: 1px solid #FFFFFF; border-radius: 10px; }"
        )
        form_layout = QVBoxLayout(self._add_friend_form)
        fields = QFormLayout()
        self._friend_name = QLineEdit()
        self._friend_name.setPlaceholderText("Nome do amigo")
        self._friend_email = QLineEdit()
        self._friend_email.setPlaceholderText("amigo@exemplo.com")
        fields.addRow("Nome:", self._friend_name)
        fields.addRow("E-mail:", self._friend_email)
        form_layout.addLayout(fields)

        submit_friend_button = QPushButton("Adicionar")
        self._submit_friend_button = submit_friend_button
        submit_friend_button.clicked.connect(self.add_friend)
        form_layout.addWidget(submit_friend_button)

        self._friend_status = QLabel("")
        self._friend_status.setWordWrap(True)
        self._friend_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._friend_status)

        form_row = QHBoxLayout()
        form_row.addStretch()
        form_row.addWidget(self._add_friend_form)
        form_row.addStretch()
        layout.addLayout(form_row)
        layout.addStretch()
        self._editing_friend_item = None
        self._add_friend_form.hide()
        self._friends_panel.hide()

    def show_welcome(self):
        self._show_page("welcome")

    def show_store(self):
        self._show_page("store")

    def search_store(self):
        search_text, accepted = QInputDialog.getText(
            self,
            "Pesquisar jogos",
            "Digite o nome, a descrição ou a empresa do jogo:",
        )
        if not accepted:
            return

        self._show_page("store")
        search_text = search_text.strip().casefold()
        matches = []
        for index, game in enumerate(self.BUILTIN_GAMES):
            searchable_text = " ".join(
                (game["titulo"], game["descricao"], game["empresa"])
            ).casefold()
            is_match = not search_text or search_text in searchable_text
            matches.append(is_match)
            for widget in self._game_cards[index]:
                widget.setVisible(is_match)

        if search_text and not any(matches):
            QMessageBox.information(
                self,
                "Pesquisa",
                "Nenhum jogo da Store corresponde à pesquisa.",
            )

    def show_cart(self):
        self._show_page("cart")

    def show_library(self):
        self._show_page("library")

    def _load_transactions(self):
        self._transactions_file = (
            Path(__file__).resolve().parent / "dados" / "transacoes.json"
        )
        self._transactions = []
        self._transactions_load_error = False
        if not self._transactions_file.exists():
            return

        try:
            with self._transactions_file.open("r", encoding="utf-8") as file:
                transactions = json.load(file)
            if not isinstance(transactions, list) or any(
                not isinstance(transaction, dict)
                or not {"id", "usuario", "tipo", "jogos", "valor", "data"}.issubset(
                    transaction
                )
                or not isinstance(transaction["id"], str)
                or not isinstance(transaction["usuario"], str)
                or not isinstance(transaction["tipo"], str)
                or transaction["tipo"] not in {"compra", "reembolso"}
                or not isinstance(transaction["jogos"], list)
                or not isinstance(transaction["valor"], (int, float))
                or not isinstance(transaction["data"], str)
                or (
                    transaction["tipo"] == "reembolso"
                    and not isinstance(transaction.get("compra_id"), str)
                )
                or any(
                    not isinstance(game, dict)
                    or not {"id", "titulo", "valor"}.issubset(game)
                    or not isinstance(game["id"], str)
                    or not isinstance(game["titulo"], str)
                    or not isinstance(game["valor"], (int, float))
                    for game in transaction["jogos"]
                )
                for transaction in transactions
            ):
                raise ValueError("O arquivo de transações possui um formato inválido.")
            self._transactions = transactions
        except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as error:
            self._transactions_load_error = True
            QMessageBox.critical(
                self,
                "Erro ao carregar transações",
                f"Não foi possível carregar as transações salvas: {error}",
            )

    def _save_transaction(self, transaction):
        if self._transactions_load_error:
            QMessageBox.critical(
                self,
                "Transação indisponível",
                "Corrija o arquivo dados/transacoes.json antes de continuar.",
            )
            return False

        updated_transactions = [*self._transactions, transaction]
        temporary_file = self._transactions_file.with_suffix(".json.tmp")
        try:
            self._transactions_file.parent.mkdir(parents=True, exist_ok=True)
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(updated_transactions, file, ensure_ascii=False, indent=2)
            temporary_file.replace(self._transactions_file)
        except (OSError, TypeError, ValueError) as error:
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError as cleanup_error:
                error = OSError(
                    f"{error}; falha ao remover arquivo temporário: {cleanup_error}"
                )
            QMessageBox.critical(
                self,
                "Erro ao salvar transação",
                f"Não foi possível salvar a transação: {error}",
            )
            return False

        self._transactions = updated_transactions
        return True

    def _load_custom_games(self):
        self._custom_games_file = Path(__file__).resolve().parent / "dados" / "jogos.json"
        self._custom_games = []
        self._custom_games_load_error = False
        if not self._custom_games_file.exists():
            return

        try:
            with self._custom_games_file.open("r", encoding="utf-8") as file:
                games = json.load(file)
            if not isinstance(games, list) or any(
                not isinstance(game, dict)
                or not {"titulo", "descricao", "preco", "empresa", "capa"}.issubset(game)
                or not all(
                    isinstance(game[key], str)
                    for key in ("titulo", "descricao", "empresa", "capa")
                )
                or not isinstance(game["preco"], (int, float))
                for game in games
            ):
                raise ValueError("O arquivo de jogos possui um formato inválido.")
            data_directory = Path(__file__).resolve().parent
            for game in games:
                cover_path = (data_directory / game["capa"]).resolve()
                if not cover_path.is_relative_to(data_directory):
                    raise ValueError("O caminho da capa está fora da pasta do projeto.")
            self._custom_games = games
        except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as error:
            self._custom_games_load_error = True
            QMessageBox.critical(
                self,
                "Erro ao carregar jogos",
                f"Não foi possível carregar os jogos salvos: {error}",
            )

    def _setup_library_page(self):
        self._library_panel = QWidget(parent=self.ui.Barra1)
        self._library_panel.setObjectName("LibraryPanel")
        self._library_panel.setGeometry(130, 180, 1181, 641)
        self._library_panel.setStyleSheet(
            "QWidget#LibraryPanel { background-color: #000000; "
            "color: #FFFFFF; border: 2px solid #FFFFFF; border-radius: 8px; }"
        )
        self._library_layout = QGridLayout(self._library_panel)
        self._library_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._library_layout.setContentsMargins(24, 24, 24, 24)
        self._library_layout.setHorizontalSpacing(24)
        self._library_layout.setVerticalSpacing(24)

        self._library_scroll = QScrollArea(self._library_panel)
        self._library_scroll.setWidgetResizable(True)
        self._library_scroll.setStyleSheet(
            "QScrollArea { background-color: #000000; border: none; }"
            "QWidget { background-color: #000000; }"
        )
        self._library_content = QWidget()
        self._library_content.setStyleSheet("background-color: #000000;")
        self._library_grid = QGridLayout(self._library_content)
        self._library_grid.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._library_grid.setContentsMargins(12, 12, 12, 12)
        self._library_grid.setHorizontalSpacing(24)
        self._library_grid.setVerticalSpacing(24)
        self._library_scroll.setWidget(self._library_content)
        self._library_layout.addWidget(self._library_scroll, 0, 0)
        self._library_panel.hide()

    def _create_library_card(
        self,
        title,
        description,
        price,
        company,
        cover_path=None,
        edit_callback=None,
        delete_callback=None,
        action_label="Apagar",
    ):
        card = QFrame()
        card.setFixedSize(201, 370)
        card.setToolTip(
            f"{title}\n{description}\nEmpresa: {company}\n"
            f"Preço: R$ {price:.2f}".replace(".", ",")
        )
        card.setStyleSheet(
            "QFrame { background-color: #000000; color: #FFFFFF; "
            "border: 2px solid #FFFFFF; border-radius: 10px; }"
            "QLabel { background-color: #000000; color: #FFFFFF; border: none; }"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(3)

        cover = QLabel()
        cover.setFixedSize(161, 155)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setStyleSheet("background-color: #000000;")
        if cover_path:
            pixmap = (
                cover_path
                if isinstance(cover_path, QPixmap)
                else QPixmap(str(cover_path))
            )
            if not pixmap.isNull():
                cover.setPixmap(
                    pixmap.scaled(
                        cover.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        cover_pixmap = cover.pixmap()
        if cover_pixmap is None or cover_pixmap.isNull():
            cover.setText("Sem capa")
        layout.addWidget(cover, alignment=Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setFixedHeight(22)
        title_label.setToolTip(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        company_label = QLabel(company)
        company_label.setFixedHeight(18)
        company_label.setToolTip(f"Empresa: {company}")
        layout.addWidget(company_label)

        play_button = QPushButton("Jogar")
        play_button.setFixedHeight(31)
        play_button.setStyleSheet(
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 10px; "
            "font-weight: bold; }"
        )
        layout.addWidget(play_button)

        price_label = QLabel(f"R$ {price:.2f}".replace(".", ","))
        price_label.setFixedHeight(22)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet(
            "background-color: #000000; color: #00FF00; "
            "border: 2px solid #00FF00; border-radius: 10px; "
            "font-weight: bold;"
        )
        layout.addWidget(price_label)

        actions = QHBoxLayout()
        if edit_callback is not None:
            edit_button = QPushButton("Alterar")
            edit_button.setToolTip("Alterar informações do jogo")
            edit_button.setFixedHeight(29)
            edit_button.setStyleSheet(
                "QPushButton { background-color: #00FF00; color: black; "
                "border: 2px solid #00FF00; border-radius: 8px; "
                "font-weight: bold; }"
            )
            edit_button.clicked.connect(edit_callback)
            actions.addWidget(edit_button)

        if delete_callback is not None:
            delete_button = QPushButton(action_label)
            delete_button.setFixedHeight(29)
            delete_button.setStyleSheet(
                "QPushButton { background-color: #000000; color: #FFFFFF; "
                "border: 1px solid #FFFFFF; border-radius: 6px; "
                "font-weight: bold; }"
                "QPushButton:hover { background-color: #808080; color: black; }"
            )
            delete_button.clicked.connect(delete_callback)
            actions.addWidget(delete_button)

        if actions.count():
            layout.addLayout(actions)

        return card

    def _refresh_library(self):
        while self._library_grid.count():
            item = self._library_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        cards = []
        for index in sorted(self._library_games):
            game = self.BUILTIN_GAMES[index]
            cover = self._game_cards[index][1].pixmap()
            cards.append(
                self._create_library_card(
                    game["titulo"],
                    game["descricao"],
                    game["preco"],
                    game["empresa"],
                    cover,
                    None,
                    lambda checked=False, game_index=index: self.refund_builtin_game(
                        game_index
                    ),
                    "Emitir reembolso",
                )
            )

        for index, game in enumerate(self._custom_games):
            cover_path = Path(__file__).resolve().parent / game["capa"]
            cards.append(
                self._create_library_card(
                    game["titulo"],
                    game["descricao"],
                    float(game["preco"]),
                    game["empresa"],
                    cover_path,
                    lambda checked=False, game_index=index: self.open_add_game_dialog(
                        game_index
                    ),
                    lambda checked=False, game_index=index: self.delete_custom_game(
                        game_index
                    ),
                    "Apagar",
                )
            )

        add_card = QPushButton()
        add_card.setFixedSize(201, 370)
        add_card.setCursor(Qt.CursorShape.PointingHandCursor)
        add_card.setStyleSheet(
            "QPushButton { background-color: #000000; color: white; "
            "border: 2px solid #FFFFFF; border-radius: 10px; font-weight: bold; }"
            "QPushButton:hover { background-color: #808080; color: black; }"
        )
        add_card.setText("+\nAdicionar jogo")
        add_card.setStyleSheet(
            add_card.styleSheet()
            + "QPushButton { font-size: 24px; }"
        )
        add_card.clicked.connect(
            lambda checked=False: self.open_add_game_dialog()
        )
        cards.append(add_card)

        for index, card in enumerate(cards):
            row, column = divmod(index, 5)
            self._library_grid.addWidget(card, row, column)

        if self._custom_games_load_error:
            add_card.setEnabled(False)

    def open_add_game_dialog(
        self,
        game_index=None,
        initial_game=None,
        initial_cover=None,
        builtin_index=None,
    ):
        if self._custom_games_load_error:
            QMessageBox.warning(
                self,
                "Cadastro indisponível",
                "Corrija o arquivo dados/jogos.json antes de adicionar jogos.",
            )
            return

        editing_game = (
            self._custom_games[game_index]
            if game_index is not None
            else initial_game
        )
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Alterar jogo" if editing_game is not None else "Adicionar jogo"
        )
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet(
            "QDialog { background-color: #202020; color: white; }"
            "QLabel { color: white; }"
            "QLineEdit, QTextEdit, QDoubleSpinBox { background-color: white; "
            "color: black; border: 1px solid #00FF00; padding: 6px; }"
            "QPushButton { background-color: #00FF00; color: black; "
            "font-weight: bold; padding: 8px; }"
        )
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        title_field = QLineEdit()
        description_field = QTextEdit()
        description_field.setFixedHeight(90)
        price_field = QDoubleSpinBox()
        price_field.setRange(0, 999999999.99)
        price_field.setDecimals(2)
        price_field.setPrefix("R$ ")
        company_field = QLineEdit()
        if editing_game is not None:
            title_field.setText(editing_game["titulo"])
            description_field.setPlainText(editing_game["descricao"])
            price_field.setValue(float(editing_game["preco"]))
            company_field.setText(editing_game["empresa"])
        form.addRow("Título:", title_field)
        form.addRow("Descrição:", description_field)
        form.addRow("Preço:", price_field)
        form.addRow("Empresa:", company_field)
        layout.addLayout(form)

        cover_path = {"value": ""}
        current_cover = (
            Path(__file__).resolve().parent / editing_game["capa"]
            if editing_game is not None and editing_game.get("capa")
            else None
        )
        cover_label = QLabel(
            current_cover.name if current_cover is not None else "Nenhuma capa selecionada"
        )
        cover_label.setWordWrap(True)
        cover_preview = QLabel()
        cover_preview.setFixedSize(150, 190)
        cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_preview.setStyleSheet(
            "background-color: #000000; border: 1px solid #FFFFFF;"
        )
        if current_cover is not None or initial_cover is not None:
            current_pixmap = (
                QPixmap(str(current_cover))
                if current_cover is not None
                else initial_cover
            )
            if not current_pixmap.isNull():
                cover_preview.setPixmap(
                    current_pixmap.scaled(
                        cover_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        choose_cover_button = QPushButton("Escolher capa")

        def choose_cover():
            selected_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Escolher capa do jogo",
                "",
                "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
            )
            if selected_path:
                pixmap = QPixmap(selected_path)
                if pixmap.isNull():
                    QMessageBox.warning(
                        dialog,
                        "Capa inválida",
                        "Não foi possível abrir a imagem selecionada.",
                    )
                    return
                cover_path["value"] = selected_path
                cover_label.setText(Path(selected_path).name)
                cover_preview.setPixmap(
                    pixmap.scaled(
                        cover_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        choose_cover_button.clicked.connect(choose_cover)
        layout.addWidget(choose_cover_button)
        layout.addWidget(cover_label)
        layout.addWidget(cover_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        buttons = QHBoxLayout()
        save_button = QPushButton(
            "Salvar alterações" if editing_game is not None else "Adicionar"
        )
        cancel_button = QPushButton("Cancelar")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        cancel_button.clicked.connect(dialog.reject)

        def save_game():
            title = title_field.text().strip()
            description = description_field.toPlainText().strip()
            company = company_field.text().strip()
            if (
                not title
                or not description
                or not company
                or (
                    current_cover is None
                    and initial_cover is None
                    and not cover_path["value"]
                )
            ):
                QMessageBox.warning(
                    dialog,
                    "Campos obrigatórios",
                    "Preencha todos os campos e escolha a capa do jogo.",
                )
                return

            cover_dir = Path(__file__).resolve().parent / "dados" / "capas"
            source_cover = Path(cover_path["value"]) if cover_path["value"] else None
            if source_cover is not None:
                relative_cover = Path("dados") / "capas" / (
                    f"{uuid.uuid4().hex}{source_cover.suffix.lower()}"
                )
            elif current_cover is not None:
                relative_cover = Path(editing_game["capa"])
            elif initial_cover is not None:
                relative_cover = Path("dados") / "capas" / (
                    f"{uuid.uuid4().hex}.png"
                )
            else:
                QMessageBox.warning(
                    dialog, "Capa obrigatória", "Escolha uma capa para o jogo."
                )
                return
            game = {
                "titulo": title,
                "descricao": description,
                "preco": price_field.value(),
                "empresa": company,
                "capa": str(relative_cover),
            }
            updated_games = list(self._custom_games)
            if game_index is None:
                updated_games.append(game)
            else:
                updated_games[game_index] = game
            destination_cover = (
                Path(__file__).resolve().parent / relative_cover
                if source_cover is not None
                else None
            )
            temporary_file = self._custom_games_file.with_suffix(".json.tmp")
            try:
                if source_cover is not None and destination_cover is not None:
                    cover_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_cover, destination_cover)
                elif initial_cover is not None and destination_cover is not None:
                    cover_dir.mkdir(parents=True, exist_ok=True)
                    if not initial_cover.save(str(destination_cover), "PNG"):
                        raise OSError("Não foi possível salvar a capa do jogo.")
                with temporary_file.open("w", encoding="utf-8") as file:
                    json.dump(updated_games, file, ensure_ascii=False, indent=2)
                temporary_file.replace(self._custom_games_file)
            except (OSError, TypeError, ValueError) as error:
                cleanup_errors = []
                for temporary_path in (destination_cover, temporary_file):
                    if temporary_path is None:
                        continue
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError as cleanup_error:
                        cleanup_errors.append(str(cleanup_error))
                cleanup_message = (
                    f"\nFalha ao limpar arquivo temporário: {'; '.join(cleanup_errors)}"
                    if cleanup_errors
                    else ""
                )
                QMessageBox.critical(
                    dialog,
                    "Erro ao salvar jogo",
                    f"Não foi possível salvar o jogo: {error}{cleanup_message}",
                )
                return

            self._custom_games = updated_games
            if (
                editing_game is not None
                and source_cover is not None
                and current_cover is not None
            ):
                try:
                    current_cover.unlink(missing_ok=True)
                except OSError as error:
                    QMessageBox.warning(
                        dialog,
                        "Capa antiga não removida",
                        f"O jogo foi atualizado, mas não foi possível apagar a capa antiga: {error}",
                    )
            if builtin_index is not None:
                self._library_games.discard(builtin_index)
            dialog.accept()

        save_button.clicked.connect(save_game)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_library()

    def edit_builtin_game(self, game_index):
        self.open_add_game_dialog(
            initial_game=self.BUILTIN_GAMES[game_index],
            initial_cover=self._game_cards[game_index][1].pixmap(),
            builtin_index=game_index,
        )

    def refund_builtin_game(self, game_index):
        if self._current_user_email is None:
            QMessageBox.information(
                self,
                "Conta necessária",
                "Necessário uma conta para continuar.",
            )
            return

        game_id = str(game_index)
        refunded_purchases = {
            (transaction.get("compra_id"), item.get("id"))
            for transaction in self._transactions
            if transaction["tipo"] == "reembolso"
            for item in transaction["jogos"]
        }
        purchase = next(
            (
                transaction
                for transaction in reversed(self._transactions)
                if transaction["tipo"] == "compra"
                and transaction["usuario"].casefold()
                == self._current_user_email.casefold()
                and any(item["id"] == game_id for item in transaction["jogos"])
                and (transaction["id"], game_id) not in refunded_purchases
            ),
            None,
        )
        if purchase is None:
            QMessageBox.warning(
                self,
                "Reembolso indisponível",
                "Não foi encontrada uma compra ativa deste jogo para esta conta.",
            )
            return

        game = next(item for item in purchase["jogos"] if item["id"] == game_id)
        confirmation = QMessageBox.question(
            self,
            "Emitir reembolso",
            f"Deseja emitir o reembolso de R$ {game['valor']:.2f} "
            f"para “{game['titulo']}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        refund = {
            "id": str(uuid.uuid4()),
            "compra_id": purchase["id"],
            "usuario": self._current_user_email,
            "tipo": "reembolso",
            "jogos": [game],
            "valor": float(game["valor"]),
            "data": datetime.now(timezone.utc).isoformat(),
        }
        if not self._save_transaction(refund):
            return

        self._library_games.discard(game_index)
        self._refresh_library()
        QMessageBox.information(
            self,
            "Reembolso emitido",
            "O reembolso foi registrado com sucesso.",
        )

    def delete_custom_game(self, game_index):
        game = self._custom_games[game_index]
        confirmation = QMessageBox.question(
            self,
            "Apagar jogo",
            f"Tem certeza de que deseja apagar “{game['titulo']}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        updated_games = list(self._custom_games)
        removed_game = updated_games.pop(game_index)
        temporary_file = self._custom_games_file.with_suffix(".json.tmp")
        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(updated_games, file, ensure_ascii=False, indent=2)
            temporary_file.replace(self._custom_games_file)
        except (OSError, TypeError, ValueError) as error:
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError as cleanup_error:
                error = OSError(f"{error}; falha ao remover arquivo temporário: {cleanup_error}")
            QMessageBox.critical(
                self,
                "Erro ao apagar jogo",
                f"Não foi possível apagar o jogo: {error}",
            )
            return

        self._custom_games = updated_games
        cover_path = Path(__file__).resolve().parent / removed_game["capa"]
        try:
            cover_path.unlink(missing_ok=True)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Capa não removida",
                f"O jogo foi apagado, mas não foi possível apagar a capa: {error}",
            )
        self._refresh_library()

    def show_friends(self):
        self._show_page("friends")

    def show_add_friend_form(self):
        self._editing_friend_item = None
        self._submit_friend_button.setText("Adicionar")
        self._friend_name.clear()
        self._friend_email.clear()
        self._friend_status.clear()
        self._add_friend_form.show()
        self._friend_name.setFocus()

    def show_edit_friend_form(self):
        friend_item = self._friends_list.currentItem()
        if friend_item is None:
            self._friend_status.setStyleSheet("color: #FF7777;")
            self._friend_status.setText("Selecione um amigo para alterar.")
            return

        self._editing_friend_item = friend_item
        self._friend_name.setText(
            friend_item.data(Qt.ItemDataRole.UserRole + 1)
        )
        self._friend_email.setText(
            friend_item.data(Qt.ItemDataRole.UserRole)
        )
        self._submit_friend_button.setText("Salvar alterações")
        self._friend_status.clear()
        self._add_friend_form.show()
        self._friend_name.setFocus()

    def remove_friend(self):
        friend_item = self._friends_list.currentItem()
        if friend_item is None:
            self._friend_status.setStyleSheet("color: #FF7777;")
            self._friend_status.setText("Selecione um amigo para remover.")
            return

        self._friends_list.takeItem(self._friends_list.row(friend_item))
        self._editing_friend_item = None
        self._add_friend_form.hide()
        self._friend_name.clear()
        self._friend_email.clear()
        self._submit_friend_button.setText("Adicionar")
        self._friend_status.setStyleSheet("color: #00FF00;")
        self._friend_status.setText("Amigo removido.")

    def add_friend(self):
        name = self._friend_name.text().strip()
        email = self._friend_email.text().strip()
        if not name or not email:
            self._friend_status.setStyleSheet("color: #FF7777;")
            self._friend_status.setText("Preencha o nome e o e-mail do amigo.")
            return
        if (
            email.count("@") != 1
            or "." not in email.rsplit("@", 1)[1]
            or any(character.isspace() for character in email)
        ):
            self._friend_status.setStyleSheet("color: #FF7777;")
            self._friend_status.setText("Digite um e-mail válido.")
            return
        for index in range(self._friends_list.count()):
            existing_item = self._friends_list.item(index)
            friend_email = existing_item.data(Qt.ItemDataRole.UserRole)
            if (
                str(friend_email).casefold() == email.casefold()
                and existing_item is not self._editing_friend_item
            ):
                self._friend_status.setStyleSheet("color: #FF7777;")
                self._friend_status.setText("Esse amigo já foi adicionado.")
                return

        is_editing = self._editing_friend_item is not None
        if not is_editing:
            friend_item = QListWidgetItem()
            self._friends_list.addItem(friend_item)
        else:
            friend_item = self._editing_friend_item
        friend_item.setText(f"{name} — {email}")
        friend_item.setData(Qt.ItemDataRole.UserRole, email)
        friend_item.setData(Qt.ItemDataRole.UserRole + 1, name)
        self._editing_friend_item = None
        self._submit_friend_button.setText("Adicionar")
        self._friend_name.clear()
        self._friend_email.clear()
        self._friend_status.setStyleSheet("color: #00FF00;")
        self._friend_status.setText(
            "Amigo atualizado." if is_editing else "Amigo adicionado."
        )

    def show_registration(self):
        self._account_tabs.setTabVisible(0, self._current_user_email is None)
        self._account_tabs.setTabVisible(1, self._current_user_email is not None)
        self._account_tabs.setCurrentIndex(
            1 if self._current_user_email is not None else 0
        )
        self._show_page("registration")

    def show_account(self):
        self.show_registration()

    def show_account_edit(self):
        self._account_status.clear()
        self._account_edit_panel.show()

    def _hash_password(self, password):
        salt = secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.PASSWORD_HASH_ITERATIONS,
        )
        return (
            f"pbkdf2_sha256${self.PASSWORD_HASH_ITERATIONS}"
            f"${salt.hex()}${password_hash.hex()}"
        )

    def _show_account_status(self, message, success=False):
        color = "#00FF00" if success else "#FF7777"
        self._account_status.setStyleSheet(f"color: {color};")
        self._account_status.setText(message)

    def register_user(self):
        name = self._registration_name.text().strip()
        email = self._registration_email.text().strip()
        password = self._registration_password.text()

        if not name or not email or not password:
            self._registration_status.setStyleSheet("color: #FF7777;")
            self._registration_status.setText("Preencha nome, e-mail e senha.")
            return

        if (
            email.count("@") != 1
            or "." not in email.rsplit("@", 1)[1]
            or any(character.isspace() for character in email)
        ):
            self._registration_status.setStyleSheet("color: #FF7777;")
            self._registration_status.setText("Digite um e-mail válido.")
            return

        users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
        try:
            if users_file.exists():
                with users_file.open("r", newline="", encoding="utf-8") as file:
                    for user in csv.DictReader(file):
                        if user.get("email", "").strip().casefold() == email.casefold():
                            self._registration_status.setStyleSheet("color: #FF7777;")
                            self._registration_status.setText(
                                "Já existe uma conta com esse e-mail."
                            )
                            return

            users_file.parent.mkdir(parents=True, exist_ok=True)
            has_header = users_file.exists() and users_file.stat().st_size > 0
            if has_header:
                with users_file.open("rb+") as file:
                    file.seek(-1, 2)
                    if file.read(1) not in (b"\n", b"\r"):
                        file.write(b"\n")
            with users_file.open("a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                if not has_header:
                    writer.writerow(["nome", "senha", "email"])
                writer.writerow([name, self._hash_password(password), email])
        except (OSError, csv.Error, UnicodeError) as error:
            QMessageBox.critical(
                self,
                "Erro ao cadastrar",
                f"Não foi possível salvar o cadastro: {error}",
            )
            return

        self._registration_name.clear()
        self._registration_email.clear()
        self._registration_password.clear()
        self._registration_status.setStyleSheet("color: #00FF00;")
        self._registration_status.setText("Cadastro realizado com sucesso!")
        self._current_user_email = email
        self.ui.Conta.setText(f"👤 {name}")
        self._account_welcome.setText(f"Bem-vindo: {name}")
        self._account_name.setText(name)
        self._account_email.setText(email)
        self._account_password.clear()
        self._account_edit_panel.hide()
        self.show_registration()

    def update_account(self):
        if self._current_user_email is None:
            self._show_account_status("Nenhuma conta está conectada.")
            return

        name = self._account_name.text().strip()
        email = self._account_email.text().strip()
        password = self._account_password.text()
        if not name or not email:
            self._show_account_status("Nome e e-mail não podem ficar vazios.")
            return
        if (
            email.count("@") != 1
            or "." not in email.rsplit("@", 1)[1]
            or any(character.isspace() for character in email)
        ):
            self._show_account_status("Digite um e-mail válido.")
            return

        users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
        try:
            with users_file.open("r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                rows = list(reader)
            if not rows or not {"nome", "senha", "email"}.issubset(rows[0]):
                raise ValueError("O arquivo de contas possui um cabeçalho inválido.")
            fieldnames = rows[0]
            name_index = fieldnames.index("nome")
            password_index = fieldnames.index("senha")
            email_index = fieldnames.index("email")
            user_rows = rows[1:]

            account = next(
                (
                    user
                    for user in user_rows
                    if len(user) > email_index
                    and user[email_index].strip().casefold()
                    == self._current_user_email.casefold()
                ),
                None,
            )
            if account is None:
                self._show_account_status(
                    "Não foi possível localizar sua conta para alterá-la."
                )
                return
            if any(
                user is not account
                and len(user) > email_index
                and user[email_index].strip().casefold() == email.casefold()
                for user in user_rows
            ):
                self._show_account_status("Esse e-mail já está sendo usado.")
                return

            account[name_index] = name
            account[email_index] = email
            if password:
                account[password_index] = self._hash_password(password)

            with users_file.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(fieldnames)
                writer.writerows(user_rows)
        except (OSError, csv.Error, UnicodeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Erro ao alterar conta",
                f"Não foi possível salvar as alterações: {error}",
            )
            return

        self._current_user_email = email
        self._account_password.clear()
        self.ui.Conta.setText(f"👤 {name}")
        self._account_welcome.setText(f"Bem-vindo: {name}")
        self._account_edit_panel.hide()
        self._show_account_status("Conta alterada com sucesso.", success=True)

    def logout(self):
        self._current_user_email = None
        self._account_name.clear()
        self._account_email.clear()
        self._account_password.clear()
        self._account_status.clear()
        self._account_welcome.setText("Bem-vindo!")
        self._account_edit_panel.hide()
        self.ui.Conta.setText("👤 HI!")
        self.show_registration()

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

    def _request_payment_amount(self, total):
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirmar compra")
        dialog.setMinimumWidth(360)
        dialog.setStyleSheet(
            "QDialog { background-color: #202020; color: white; }"
            "QLabel { color: white; }"
            "QDoubleSpinBox { background-color: white; color: black; padding: 6px; }"
            "QPushButton { background-color: #00FF00; color: black; "
            "font-weight: bold; padding: 8px; }"
        )
        layout = QVBoxLayout(dialog)
        total_label = QLabel(f"Total da compra: R$ {total:.2f}".replace(".", ","))
        payment_field = QDoubleSpinBox()
        payment_field.setRange(0, 999999999.99)
        payment_field.setDecimals(2)
        payment_field.setPrefix("R$ ")
        payment_field.setSpecialValueText("")
        payment_field.setValue(0)
        form = QFormLayout()
        form.addRow("Valor pago:", payment_field)
        layout.addWidget(total_label)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        confirm_button = QPushButton("Comprar")
        cancel_button = QPushButton("Cancelar")
        buttons.addWidget(confirm_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        confirm_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return payment_field.value()

    def purchase_cart(self):
        if not self._cart_games:
            return

        if self._current_user_email is None:
            QMessageBox.information(
                self,
                "Conta necessária",
                "Necessário uma conta para continuar.",
            )
            return

        games = [
            {
                "id": str(index),
                "titulo": self.BUILTIN_GAMES[index]["titulo"],
                "valor": self.BUILTIN_GAMES[index]["preco"],
            }
            for index in sorted(self._cart_games)
        ]
        total = round(sum(game["valor"] for game in games), 2)
        amount_paid = self._request_payment_amount(total)
        if amount_paid is None:
            return
        amount_paid = round(amount_paid, 2)
        if amount_paid < total:
            QMessageBox.warning(self, "Compra inválida", "Compra invalida.")
            return

        transaction = {
            "id": str(uuid.uuid4()),
            "usuario": self._current_user_email,
            "tipo": "compra",
            "jogos": games,
            "valor": total,
            "valor_pago": amount_paid,
            "data": datetime.now(timezone.utc).isoformat(),
        }
        if not self._save_transaction(transaction):
            return

        quantity = len(games)
        self._library_games.update(self._cart_games)
        self._cart_games.clear()
        self._update_cart_badge()
        self._show_page("cart")
        QMessageBox.information(
            self,
            "Compra concluída",
            f"Compra realizada com sucesso ;) ! Jogos comprados: {quantity}.",
        )

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