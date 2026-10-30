import csv
import ast
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import sqlite3
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

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
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPixmap
from PyQt6.uic import loadUiType
from database import BancoDeDados
from usuario import Usuario, UsuarioRepositorio
from amigo import Amigo, AmigoRepositorio
from avaliacao import Avaliacao, AvaliacaoRepositorio
from biblioteca import Biblioteca, BibliotecaRepositorio
from carrinho import Carrinho, CarrinhoRepositorio
from transacao import Transacao, TransacaoRepositorio


Ui_MainWindowBase, _ = loadUiType(str(Path(__file__).resolve().parent / "main.ui"))


class Ui_MainWindow(Ui_MainWindowBase):
    pass


class MainWindow(QMainWindow):
    PASSWORD_HASH_ITERATIONS = 600_000

    def __init__(self):
        super().__init__()

        self._games_directory = Path(__file__).resolve().parent / "jogos"
        self.db = BancoDeDados(perfil="principal")
        self.avaliacoes_db = BancoDeDados(
            self.db.arquivo.with_name("avaliacoes.db"),
            perfil="avaliacoes",
        )
        self.biblioteca_db = BancoDeDados(
            self.db.arquivo.with_name("biblioteca.db"),
            perfil="biblioteca",
        )
        self._migrate_separated_databases()
        self.usuario_repo = UsuarioRepositorio(self.db)
        self.amigo_repo = AmigoRepositorio(self.db)
        self.avaliacao_repo = AvaliacaoRepositorio(self.avaliacoes_db)
        self.biblioteca_repo = BibliotecaRepositorio(self.biblioteca_db)
        self.carrinho_repo = CarrinhoRepositorio(self.db)
        self.transacao_repo = TransacaoRepositorio(self.db)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._custom_game_files_error = not self._migrate_custom_game_files()
        self._store_executor_dir = Path(__file__).resolve().parent / "executador"
        try:
            self._store_executor_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Pasta de execução indisponível",
                f"Não foi possível criar a pasta de jogos da Store: {error}",
            )

        self._apply_window_images()

        if not hasattr(self.ui, "BemVindo"):
            self.ui.BemVindo = QLabel(parent=self.ui.Barra1)
            self.ui.BemVindo.setObjectName("BemVindo")
            self.ui.BemVindo.setGeometry(self.ui.Menu3.geometry())
            self.ui.BemVindo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.BemVindo.setStyleSheet(
                "QLabel { color: #FFFFFF; background: transparent; font-weight: bold; }"
            )
            self.ui.BemVindo.setText("Bem vindo(a) a A.R.K.O!")
            self.ui.BemVindo.hide()

        if not hasattr(self.ui, "jogos"):
            self.ui.jogos = (
                self.ui.SELgta6,
                self.ui.GTA6_2,
                self.ui.ComprarBT,
                self.ui.Preco,
                self.ui.Desconto,
                self.ui.SELMspider,
                self.ui.Mspider,
                self.ui.ComprarBT_2,
                self.ui.Preco_2,
                self.ui.Desconto_2,
                self.ui.SELMinecraft,
                self.ui.Minecraft,
                self.ui.ComprarBT_3,
                self.ui.Preco_3,
                self.ui.Desconto_3,
                self.ui.SELMinecraft_2,
                self.ui.Hollow,
                self.ui.ComprarBT_4,
                self.ui.Preco_4,
                self.ui.Desconto_4,
                self.ui.SELMinecraft_3,
                self.ui.SHADOW,
                self.ui.ComprarBT_5,
                self.ui.Desconto_5,
                self.ui.Preco_6,
                self.ui.SELMinecraft_4,
                self.ui.Zelda,
                self.ui.ComprarBT_7,
                self.ui.Preco_7,
                self.ui.Desconto_7,
                self.ui.SELMinecraft_5,
                self.ui.Resident,
                self.ui.ComprarBT_8,
                self.ui.Preco_8,
                self.ui.Desconto_8,
            )

        self._unused_store_widgets = (
            self.ui.Preco_5,
            self.ui.ComprarBT_6,
            self.ui.Desconto_6,
        )

        if not hasattr(self.ui, "ContadorCarrinho"):
            self.ui.ContadorCarrinho = QLabel(parent=self.ui.Barra1)
            self.ui.ContadorCarrinho.setObjectName("ContadorCarrinho")
            self.ui.ContadorCarrinho.setGeometry(1670, 108, 25, 25)
            self.ui.ContadorCarrinho.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.ContadorCarrinho.setStyleSheet(
                "QLabel {"
                "background-color: #00FF00;"
                "color: black;"
                "border: 1px solid #FFFFFF;"
                "border-radius: 12px;"
                "font-weight: bold;"
                "}"
            )
            self.ui.ContadorCarrinho.setText("0")
            self.ui.ContadorCarrinho.hide()

        self._current_user_email = None
        self._current_user_name = None
        self._migrate_legacy_data()
        self.STORE_GAMES = self._load_store_catalog()
        self._setup_registration_tab()
        self._setup_friends_page()
        self._setup_store_page()
        self._game_cards = self._build_store_cards()
        self._cart_games = set()
        self._library_games = set()
        self._load_transactions()
        self._load_reviews()
        self._load_custom_games()
        self._setup_library_page()
        self._setup_cart_page()
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
        self._content_panels = [
            self.ui.BemVindo,
            self._account_tabs,
            self._friends_panel,
            self._library_panel,
            self._cart_panel,
            self._store_panel,
        ]
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
        self._current_font_scale = 1.0
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def _apply_window_images(self):
        image_map = {
            "Logo": "WhatsApp Image 2026-10-01 at 15.10.22 (1).jpeg",
            "GTA6_2": "images.jfif",
            "Mspider": "images (68).jpg",
            "Minecraft": "js.png",
        }
        images_dir = Path(__file__).resolve().parent / "imagens"
        if not images_dir.exists():
            return

        for attr_name, filename in image_map.items():
            label = getattr(self.ui, attr_name, None)
            if label is None or not isinstance(label, QLabel):
                continue
            candidate = images_dir / filename
            if not candidate.exists():
                continue
            pixmap = QPixmap(str(candidate))
            if pixmap.isNull():
                continue
            label.setPixmap(
                pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            label.setText("")

    def _sync_all_panels_to_main_area(self):
        main_area_rect = self.ui.Menu3.geometry()
        for panel in self._content_panels:
            panel.setGeometry(main_area_rect)

    @staticmethod
    def _set_font_size(widget, point_size, bold=None):
        font = widget.font()
        font.setPointSizeF(point_size)
        if bold is not None:
            font.setBold(bold)
        widget.setFont(font)

    def _build_cover_pixmap(self, title, color="#111111", accent="#00FF00"):
        pixmap = QPixmap(161, 221)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, 161, 221, QColor(color))
        painter.fillRect(0, 0, 161, 36, QColor(accent))
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        words = title.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= 13:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        if not lines:
            lines = [title[:12]]
        for index, line in enumerate(lines[:3]):
            painter.drawText(10, 58 + index * 18, line[:18])
        painter.end()
        return pixmap

    @staticmethod
    def _normalize_cover_name(value):
        normalized = unicodedata.normalize("NFKD", str(value))
        cleaned = "".join(
            char.lower() for char in normalized if not unicodedata.combining(char)
        )
        cleaned = (
            cleaned.replace("&", "and")
            .replace("'", "")
            .replace("\"", "")
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
            .replace(".", "")
        )
        return cleaned

    def _find_store_cover(self, game_title):
        images_dir = Path(__file__).resolve().parent / "imagens"
        if not images_dir.exists():
            return None

        normalized_title = self._normalize_cover_name(game_title)
        best_match = None
        best_score = -1

        for file_path in sorted(images_dir.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp"}:
                continue

            normalized_name = self._normalize_cover_name(file_path.stem)
            if normalized_title in normalized_name or normalized_name in normalized_title:
                return file_path

            score = 0
            for token in ["gta", "spider", "minecraft", "dragon", "reddead", "poppy", "hollow", "souls", "fortnite", "shadow", "war", "valorant", "lastofus", "among", "stray", "fall", "fifa", "pacman", "pes", "street", "mortal", "forza"]:
                if token in normalized_title and token in normalized_name:
                    score += 3
            if score > best_score:
                best_match = file_path
                best_score = score

        return best_match

    def _load_store_cover(self, game_title, fallback_color="#111111"):
        cover_path = self._find_store_cover(game_title)
        if cover_path is not None:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                return pixmap
        return self._build_cover_pixmap(game_title, fallback_color)

    def _setup_store_page(self):
        self._store_panel = QWidget(parent=self.ui.Barra1)
        self._store_panel.setObjectName("StorePanel")
        self._store_panel.setGeometry(self.ui.Menu3.geometry())
        self._store_panel.setStyleSheet(
            "QWidget#StorePanel { background-color: #000000; "
            "color: #FFFFFF; border: 2px solid #FFFFFF; border-radius: 8px; }"
        )

        layout = QVBoxLayout(self._store_panel)
        layout.setContentsMargins(24, 24, 24, 24)
        self._store_scroll = QScrollArea(self._store_panel)
        self._store_scroll.setWidgetResizable(True)
        self._store_scroll.setStyleSheet(
            "QScrollArea { background-color: #000000; border: none; }"
            "QWidget { background-color: #000000; }"
        )
        self._store_content = QWidget()
        self._store_content.setStyleSheet("background-color: #000000;")
        self._store_grid = QGridLayout(self._store_content)
        self._store_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._store_grid.setContentsMargins(12, 12, 12, 12)
        self._store_grid.setHorizontalSpacing(24)
        self._store_grid.setVerticalSpacing(24)
        self._store_scroll.setWidget(self._store_content)
        self._add_store_game_button = QPushButton("Adicionar jogo à Store")
        self._add_store_game_button.hide()
        self._add_store_game_button.clicked.connect(self.open_add_store_game_dialog)
        layout.addWidget(self._add_store_game_button)
        layout.addWidget(self._store_scroll)
        self._store_panel.hide()

    def _is_store_admin(self):
        return (
            self._current_user_name is not None
            and self._current_user_name.strip().casefold() == "administrador"
        )

    def _update_store_admin_controls(self):
        self._add_store_game_button.setVisible(self._is_store_admin())

    def _build_store_cards(self):
        button_style = (
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 8px; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #FFFFFF; border-color: #FFFFFF; }"
        )
        cards = []

        for index, game in enumerate(self.STORE_GAMES):
            card = QFrame(self._store_content)
            card.setObjectName("StoreGameCard")
            card.setFixedSize(201, 370)
            card.setStyleSheet(
                "QFrame#StoreGameCard { background-color: #000000; color: #FFFFFF; "
                "border: 2px solid #FFFFFF; border-radius: 10px; }"
                "QLabel { background-color: #000000; color: #FFFFFF; border: none; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(6)

            price_label = QLabel(f"R$ {game['preco']:.2f}".replace(".", ","))
            price_label.setFixedHeight(26)
            price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_label.setStyleSheet(
                "background-color: #000000; color: #00FF00; "
                "border: 2px solid #00FF00; border-radius: 10px; "
                "font-weight: bold;"
            )
            price_stack = QVBoxLayout()
            price_stack.setSpacing(2)
            if game["preco_ant"] > game["preco"]:
                previous_price_label = QLabel(
                    f"R$ {game['preco_ant']:.2f}".replace(".", ",")
                )
                previous_price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                previous_price_label.setFixedHeight(15)
                previous_price_font = previous_price_label.font()
                previous_price_font.setStrikeOut(True)
                previous_price_label.setFont(previous_price_font)
                previous_price_label.setStyleSheet(
                    "background-color: transparent; color: #AAAAAA; "
                    "font-size: 10px;"
                )
                price_stack.addWidget(previous_price_label)
            price_stack.addWidget(price_label)

            price_row = QHBoxLayout()
            price_row.setSpacing(6)
            discount = float(game["desconto"])
            if discount > 0:
                discount_label = QLabel(f"-{discount:.0%}")
                discount_label.setFixedSize(36, 36)
                discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                discount_label.setToolTip(
                    f"Desconto de {discount:.0%}"
                )
                discount_label.setStyleSheet(
                    "background-color: #00FF00; color: #000000; "
                    "border: 1px solid #00FF00; border-radius: 18px; "
                    "font-size: 9px; font-weight: bold;"
                )
                price_row.addWidget(discount_label)
            price_row.addLayout(price_stack, 1)

            cover_label = QLabel()
            cover_label.setFixedSize(161, 155)
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cover_label.setStyleSheet("background-color: #000000;")
            cover_path = self._store_game_cover_path(game)
            if cover_path is not None:
                pixmap = QPixmap(str(cover_path))
            else:
                pixmap = self._build_cover_pixmap(game["titulo"])
            if pixmap is not None and not pixmap.isNull():
                cover_label.setPixmap(
                    pixmap.scaled(
                        cover_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            card_layout.addWidget(cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

            title_label = QLabel(game["titulo"])
            title_label.setFixedHeight(22)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setToolTip(game["descricao"])
            title_label.setStyleSheet("font-weight: bold;")
            card_layout.addWidget(title_label)

            company_label = QLabel(game["empresa"])
            company_label.setFixedHeight(18)
            company_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            company_label.setToolTip(f"Empresa: {game['empresa']}")
            card_layout.addWidget(company_label)

            card_layout.addStretch(1)
            buy_button = QPushButton("Adicionar ao carrinho")
            buy_button.setFixedHeight(31)
            buy_button.setStyleSheet(button_style)
            card_layout.addWidget(buy_button)
            card_layout.addLayout(price_row)

            cards.append((card, cover_label, None, buy_button, price_label, None))
            self._store_grid.addWidget(card, index // 5, index % 5)

        return tuple(cards)

    def _resize_store_cards_to_fill_panel(self):
        if not hasattr(self, "_game_cards") or not self._game_cards:
            return

        visible_card_count = sum(
            not card[0].isHidden() for card in self._game_cards
        )
        if not visible_card_count:
            return

        row_count = (visible_card_count + 4) // 5
        margins = self._store_grid.contentsMargins()
        available_height = (
            self._store_scroll.viewport().height()
            - margins.top()
            - margins.bottom()
            - self._store_grid.verticalSpacing() * (row_count - 1)
        )
        card_height = max(370, available_height // row_count)
        for card, *_ in self._game_cards:
            card.setFixedHeight(card_height)

    def _show_page(self, page):
        self._sync_all_panels_to_main_area()
        self.ui.BemVindo.hide()
        self._account_tabs.hide()
        self._friends_panel.hide()
        self._library_panel.hide()
        self._cart_panel.hide()
        self._store_panel.hide()
        for widget in self.ui.jogos:
            widget.hide()
        for widget in self._unused_store_widgets:
            widget.hide()
        self.ui.ComprarCarrinho.hide()

        if page == "welcome":
            self.ui.BemVindo.setText("Bem-vindo(a) a A.R.K.O!")
            self.ui.BemVindo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.BemVindo.setStyleSheet(
                "QLabel { color: #FFFFFF; background: transparent; font-weight: bold; }"
            )
            self._set_font_size(self.ui.BemVindo, 21, bold=True)
            self.ui.BemVindo.show()
        elif page == "store":
            self._resize_store_cards_to_fill_panel()
            for index, card in enumerate(self._game_cards):
                card[0].show()
                self._set_store_cart_button(index)
            self._store_panel.show()
        elif page == "library":
            self._refresh_library()
            self._library_panel.show()
        elif page == "cart":
            self._refresh_cart_page()
            self._cart_panel.show()
        elif page == "registration":
            self._account_tabs.show()
        elif page == "friends":
            self._friends_panel.show()

        self._active_page = page

    def _migrate_legacy_data(self):
        users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
        if users_file.exists():
            try:
                with users_file.open("r", newline="", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if not row or not row.get("email"):
                            continue
                        email = str(row["email"]).strip()
                        if not email or self.usuario_repo.buscar_por_email(email):
                            continue
                        nome = str(row.get("nome") or "").strip()
                        senha = str(row.get("senha") or "").strip()
                        if nome and senha:
                            self.usuario_repo.inserir(Usuario(nome, email, senha))
            except (OSError, csv.Error, UnicodeError):
                pass

        reviews_file = Path(__file__).resolve().parent / "dados" / "avaliacoes.json"
        if reviews_file.exists():
            try:
                with reviews_file.open("r", encoding="utf-8") as file:
                    reviews = json.load(file)
                for review in reviews:
                    if not isinstance(review, dict):
                        continue
                    usuario_email = str(review.get("usuario") or "").strip()
                    jogo_id = str(review.get("jogo_id") or "").strip()
                    if not usuario_email or not jogo_id:
                        continue
                    existing = self.avaliacao_repo.buscar_por_usuario_e_jogo(usuario_email, int(jogo_id))
                    if existing is None:
                        self.avaliacao_repo.inserir(
                            Avaliacao(
                                usuario_email,
                                int(jogo_id),
                                int(review.get("nota", 1)),
                                review.get("data", datetime.now(timezone.utc).isoformat()),
                            )
                        )
            except (OSError, json.JSONDecodeError, UnicodeError, ValueError):
                pass

        transactions_file = Path(__file__).resolve().parent / "dados" / "transacoes.json"
        if transactions_file.exists():
            try:
                with transactions_file.open("r", encoding="utf-8") as file:
                    transactions = json.load(file)
                for transaction in transactions:
                    if not isinstance(transaction, dict):
                        continue
                    transaction_id = str(transaction.get("id") or "").strip()
                    if not transaction_id or self.transacao_repo.buscar_por_id(transaction_id):
                        continue
                    self.transacao_repo.inserir(
                        Transacao(
                            str(transaction.get("usuario") or "").strip(),
                            str(transaction.get("tipo") or "").strip(),
                            transaction.get("jogos") or [],
                            float(transaction.get("valor", 0)),
                            transaction.get("data") or datetime.now(timezone.utc).isoformat(),
                            id=transaction_id,
                            valor_pago=transaction.get("valor_pago"),
                            compra_id=transaction.get("compra_id"),
                        )
                    )
            except (OSError, json.JSONDecodeError, UnicodeError, ValueError):
                pass

    def _migrate_separated_databases(self):
        try:
            migrations = (
                (
                    "split_reviews_and_library_v1",
                    (
                        (
                            self.avaliacoes_db,
                            "avaliacoes",
                            ("id", "usuario_email", "jogo_id", "nota", "data"),
                        ),
                        (
                            self.biblioteca_db,
                            "biblioteca",
                            (
                                "id",
                                "usuario_email",
                                "jogo_id",
                                "titulo",
                                "data_adicao",
                            ),
                        ),
                    ),
                ),
            )
            for migration_key, tables in migrations:
                migration = self.db.conexao.execute(
                    "SELECT valor FROM app_metadata WHERE chave = ?",
                    (migration_key,),
                ).fetchone()
                if migration is not None and migration["valor"] == "done":
                    continue

                for destination, table, columns in tables:
                    source_exists = self.db.conexao.execute(
                        "SELECT 1 FROM sqlite_master "
                        "WHERE type = 'table' AND name = ?",
                        (table,),
                    ).fetchone()
                    if source_exists is None:
                        continue

                    available_columns = {
                        row["name"]
                        for row in self.db.conexao.execute(
                            f"PRAGMA table_info({table})"
                        ).fetchall()
                    }
                    source_columns = tuple(
                        column for column in columns if column in available_columns
                    )
                    required_columns = {
                        "avaliacoes": {
                            "id",
                            "usuario_email",
                            "jogo_id",
                            "nota",
                            "data",
                        },
                        "biblioteca": {
                            "id",
                            "usuario_email",
                            "jogo_id",
                            "titulo",
                        },
                    }[table]
                    if not required_columns.issubset(source_columns):
                        raise ValueError(
                            f"A tabela antiga {table} não possui todas as colunas "
                            "necessárias para a migração."
                        )
                    self.db.copiar_tabela_para(
                        destination,
                        table,
                        source_columns,
                    )

                with self.db.conexao:
                    self.db.conexao.execute(
                        "INSERT OR REPLACE INTO app_metadata (chave, valor) "
                        "VALUES (?, 'done')",
                        (migration_key,),
                    )
        except (OSError, sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self,
                "Erro ao organizar os bancos",
                f"Não foi possível migrar os dados: {error}",
            )
            raise RuntimeError("Falha ao migrar os dados para os novos bancos.") from error

    def _load_friends_from_db(self):
        self._friends_list.clear()
        if self._current_user_email is None:
            return
        for amigo in self.amigo_repo.listar_por_usuario(self._current_user_email):
            item = QListWidgetItem(f"{amigo.nome} — {amigo.email}")
            item.setData(Qt.ItemDataRole.UserRole, amigo.email)
            item.setData(Qt.ItemDataRole.UserRole + 1, amigo.nome)
            self._friends_list.addItem(item)

    def _setup_registration_tab(self):
        self._account_tabs = QTabWidget(parent=self.ui.Barra1)
        self._account_tabs.setObjectName("AccountTabs")
        self._account_tabs.setGeometry(self.ui.Menu3.geometry())
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
        title.setStyleSheet("font-weight: bold;")
        self._set_font_size(title, 16.5, bold=True)
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
        self._add_password_visibility_toggle(
            form, "Senha:", self._registration_password
        )
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

        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_layout.addStretch()
        login_card_row = QHBoxLayout()
        login_card_row.addStretch()
        login_card = QFrame()
        login_card.setObjectName("RegistrationCard")
        login_card.setMaximumWidth(520)
        login_card.setStyleSheet(card.styleSheet())
        login_card_layout = QVBoxLayout(login_card)

        login_title = QLabel("Entrar na conta")
        login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_title.setStyleSheet("font-weight: bold;")
        self._set_font_size(login_title, 16.5, bold=True)
        login_card_layout.addWidget(login_title)

        login_form = QFormLayout()
        self._login_email = QLineEdit()
        self._login_email.setPlaceholderText("voce@exemplo.com")
        self._login_password = QLineEdit()
        self._login_password.setPlaceholderText("Sua senha")
        self._login_password.setEchoMode(QLineEdit.EchoMode.Password)
        login_form.addRow("E-mail:", self._login_email)
        self._add_password_visibility_toggle(
            login_form, "Senha:", self._login_password
        )
        login_card_layout.addLayout(login_form)

        self._login_status = QLabel("")
        self._login_status.setWordWrap(True)
        self._login_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_card_layout.addWidget(self._login_status)

        login_button = QPushButton("Entrar")
        login_button.setDefault(True)
        login_button.clicked.connect(self.login_user)
        self._login_password.returnPressed.connect(self.login_user)
        login_card_layout.addWidget(login_button)

        login_card_row.addWidget(login_card)
        login_card_row.addStretch()
        login_layout.addLayout(login_card_row)
        login_layout.addStretch()
        self._account_tabs.addTab(login_tab, "Entrar")

        account_tab = QWidget()
        account_layout = QVBoxLayout(account_tab)
        account_layout.setContentsMargins(24, 24, 24, 24)
        self._account_welcome = QLabel("Bem-vindo!")
        self._account_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._account_welcome.setStyleSheet(
            "background-color: #202020; color: #00FF00; "
            "border: 2px solid #00FF00; border-radius: 10px; "
            "font-weight: bold; padding: 16px;"
        )
        self._set_font_size(self._account_welcome, 16.5, bold=True)
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
        self._account_current_password = QLineEdit()
        self._account_current_password.setPlaceholderText(
            "Necessária para redefinir a senha"
        )
        self._account_current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._account_password = QLineEdit()
        self._account_password.setPlaceholderText("Deixe em branco para manter")
        self._account_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._account_password_confirmation = QLineEdit()
        self._account_password_confirmation.setPlaceholderText(
            "Digite novamente a nova senha"
        )
        self._account_password_confirmation.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        account_form.addRow("Nome:", self._account_name)
        account_form.addRow("E-mail:", self._account_email)
        account_form.addRow("Senha atual:", self._account_current_password)
        account_form.addRow("Nova senha:", self._account_password)
        account_form.addRow("Confirmar nova senha:", self._account_password_confirmation)
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
        self._account_tabs.setTabVisible(2, False)
        self._account_tabs.hide()

    def _add_password_visibility_toggle(self, form, label, password_field):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(password_field)

        visibility_button = QPushButton("Mostrar")
        visibility_button.setCheckable(True)
        visibility_button.setToolTip("Mostrar ou ocultar a senha digitada")
        visibility_button.toggled.connect(
            lambda visible: self._set_password_visibility(
                password_field, visibility_button, visible
            )
        )
        row_layout.addWidget(visibility_button)
        form.addRow(label, row)

    @staticmethod
    def _set_password_visibility(password_field, visibility_button, visible):
        password_field.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        visibility_button.setText("Ocultar" if visible else "Mostrar")

    def _setup_friends_page(self):
        self._friends_panel = QWidget(parent=self.ui.Barra1)
        self._friends_panel.setObjectName("FriendsPanel")
        self._friends_panel.setGeometry(self.ui.Menu3.geometry())
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
        title.setStyleSheet("font-weight: bold;")
        self._set_font_size(title, 16.5, bold=True)
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
        search_text = (search_text or "").strip().casefold()
        matches = []
        matching_cards = []
        for index, game in enumerate(self.STORE_GAMES):
            searchable_text = " ".join(
                (game["titulo"], game["descricao"], game["empresa"])
            ).casefold()
            is_match = not search_text or search_text in searchable_text
            matches.append(is_match)
            card = self._game_cards[index][0]
            self._store_grid.removeWidget(card)
            card.setVisible(is_match)
            if is_match:
                matching_cards.append(card)

        for position, card in enumerate(matching_cards):
            self._store_grid.addWidget(card, position // 5, position % 5)
        self._resize_store_cards_to_fill_panel()

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
        self._transactions = []
        self._transactions_load_error = False
        try:
            for transaction in self.transacao_repo.listar():
                self._transactions.append(
                    {
                        "id": transaction.id,
                        "usuario": transaction.usuario_email,
                        "tipo": transaction.tipo,
                        "jogos": transaction.jogos,
                        "valor": float(transaction.valor),
                        "valor_pago": transaction.valor_pago,
                        "data": transaction.data,
                        "compra_id": transaction.compra_id,
                    }
                )
        except Exception as error:
            self._transactions_load_error = True
            QMessageBox.critical(
                self,
                "Erro ao carregar transações",
                f"Não foi possível carregar as transações salvas: {error}",
            )

    def _save_transaction(self, transaction):
        try:
            self.transacao_repo.inserir(
                Transacao(
                    transaction["usuario"],
                    transaction["tipo"],
                    transaction["jogos"],
                    float(transaction["valor"]),
                    transaction["data"],
                    id=transaction["id"],
                    valor_pago=transaction.get("valor_pago"),
                    compra_id=transaction.get("compra_id"),
                )
            )
            self._transactions = [*self._transactions, transaction]
            return True
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar transação",
                f"Não foi possível salvar a transação: {error}",
            )
            return False

    def _load_reviews(self):
        self._reviews = []
        self._reviews_load_error = False
        try:
            for review in self.avaliacao_repo.listar():
                self._reviews.append(
                    {
                        "usuario": review.usuario_email,
                        "jogo_id": str(review.jogo_id),
                        "nota": int(review.nota),
                        "data": review.data,
                    }
                )
        except Exception as error:
            self._reviews_load_error = True
            QMessageBox.critical(
                self,
                "Erro ao carregar avaliações",
                f"Não foi possível carregar as avaliações salvas: {error}",
            )

    def _save_reviews(self, reviews):
        try:
            self._reviews = reviews
            for review in reviews:
                usuario = str(review["usuario"]).strip()
                jogo_id = int(review["jogo_id"])
                existing = self.avaliacao_repo.buscar_por_usuario_e_jogo(usuario, jogo_id)
                if existing is None:
                    self.avaliacao_repo.inserir(
                        Avaliacao(usuario, jogo_id, int(review["nota"]), review["data"])
                    )
                else:
                    existing.nota = int(review["nota"])
                    existing.data = review["data"]
                    self.avaliacao_repo.atualizar(existing)
            return True
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao salvar avaliação",
                f"Não foi possível salvar a avaliação: {error}",
            )
            return False

    def _transaction_item_matches_game(self, item, game_index):
        if str(item.get("id")) != str(game_index):
            return False
        item_title = item.get("titulo")
        return (
            not item_title
            or str(item_title).casefold()
            == self.STORE_GAMES[game_index]["titulo"].casefold()
        )

    def _active_purchase_for_game(self, user_email, game_index):
        game_id = str(game_index)
        refunded_purchases = {
            (transaction.get("compra_id"), item.get("id"))
            for transaction in self._transactions
            if transaction["tipo"] == "reembolso"
            for item in transaction["jogos"]
        }
        return next(
            (
                transaction
                for transaction in reversed(self._transactions)
                if transaction["tipo"] == "compra"
                and transaction["usuario"].casefold() == user_email.casefold()
                and any(
                    self._transaction_item_matches_game(item, game_index)
                    for item in transaction["jogos"]
                )
                and (transaction["id"], game_id) not in refunded_purchases
            ),
            None,
        )

    def _load_user_library(self, user_email):
        game_ids = set()
        refunded_purchases = {
            (transaction.get("compra_id"), item.get("id"))
            for transaction in self._transactions
            if transaction["tipo"] == "reembolso"
            for item in transaction["jogos"]
        }
        for transaction in self._transactions:
            if (
                transaction["tipo"] != "compra"
                or transaction["usuario"].casefold() != user_email.casefold()
            ):
                continue
            for game in transaction["jogos"]:
                try:
                    game_index = int(game["id"])
                except (KeyError, TypeError, ValueError):
                    continue
                if (
                    0 <= game_index < len(self.STORE_GAMES)
                    and self._transaction_item_matches_game(game, game_index)
                    and (transaction["id"], game["id"]) not in refunded_purchases
                ):
                    game_ids.add(game_index)
        self._library_games = game_ids

    def _get_user_review(self, user_email, game_index):
        return next(
            (
                review
                for review in self._reviews
                if review["usuario"].casefold() == user_email.casefold()
                and review["jogo_id"] == str(game_index)
            ),
            None,
        )

    @staticmethod
    def _store_game_slug(title):
        normalized = unicodedata.normalize("NFKD", str(title))
        ascii_title = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
        return slug or "jogo"

    def _store_game_text(self, game):
        fields = (
            ("titulo", str(game["titulo"])),
            ("descricao", str(game["descricao"])),
            ("preco", float(game["preco"])),
            ("preco_ant", float(game["preco_ant"])),
            ("empresa", str(game["empresa"])),
            ("desconto", float(game["desconto"])),
        )
        lines = ["{"]
        for key, value in fields:
            formatted_value = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, str)
                else f"{value:.2f}"
            )
            lines.append(f"    {json.dumps(key)}: {formatted_value},")
        lines.extend(("}", ""))
        return "\n".join(lines)

    def _write_store_game_txt(self, game, file_path):
        temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")
        try:
            temporary_path.write_text(self._store_game_text(game), encoding="utf-8")
            temporary_path.replace(file_path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise

    def _validate_store_game(self, data, source_path):
        required_fields = {"titulo", "descricao", "preco", "empresa", "desconto"}
        allowed_fields = required_fields | {"preco_ant"}
        if (
            not isinstance(data, dict)
            or not required_fields.issubset(data)
            or not set(data).issubset(allowed_fields)
        ):
            raise ValueError(
                "O TXT precisa conter titulo, descricao, preco, empresa e desconto; "
                "preco_ant é opcional."
            )
        if not all(
            isinstance(data[field], str) and data[field].strip()
            for field in ("titulo", "descricao", "empresa")
        ):
            raise ValueError("Título, descrição e empresa precisam ser textos preenchidos.")
        if (
            isinstance(data["preco"], bool)
            or not isinstance(data["preco"], (int, float))
            or not math.isfinite(data["preco"])
            or data["preco"] < 0
        ):
            raise ValueError("O preço precisa ser um número válido e não negativo.")
        previous_price = data.get("preco_ant", data["preco"])
        if (
            isinstance(previous_price, bool)
            or not isinstance(previous_price, (int, float))
            or not math.isfinite(previous_price)
            or previous_price < data["preco"]
        ):
            raise ValueError(
                "O preço anterior precisa ser um número válido e maior ou igual ao preço atual."
            )
        if (
            isinstance(data["desconto"], bool)
            or not isinstance(data["desconto"], (int, float))
            or not math.isfinite(data["desconto"])
            or not 0 <= data["desconto"] <= 1
        ):
            raise ValueError("O desconto precisa estar entre 0 e 1.")
        return {
            "titulo": data["titulo"].strip(),
            "descricao": data["descricao"].strip(),
            "preco": float(data["preco"]),
            "preco_ant": float(previous_price),
            "empresa": data["empresa"].strip(),
            "desconto": float(data["desconto"]),
            "_catalog_file": source_path,
        }

    def _load_store_catalog(self):
        self._games_directory.mkdir(parents=True, exist_ok=True)
        catalog_files = sorted(
            self._games_directory.glob("*.txt"),
            key=self._store_catalog_sort_key,
        )
        games = []
        invalid_files = []
        for file_path in catalog_files:
            try:
                data = ast.literal_eval(file_path.read_text(encoding="utf-8"))
                games.append(self._validate_store_game(data, file_path))
            except (OSError, SyntaxError, ValueError, TypeError) as error:
                invalid_files.append(f"{file_path.name}: {error}")

        if invalid_files:
            QMessageBox.warning(
                self,
                "Arquivos de jogos inválidos",
                "Estes TXT foram ignorados. Corrija-os para exibir os jogos:\n"
                + "\n".join(invalid_files),
            )
        return games

    @staticmethod
    def _store_catalog_sort_key(path):
        prefix = path.name.split("-", 1)[0]
        if prefix.isdigit():
            return (0, int(prefix), path.name.casefold())
        return (1, 0, path.name.casefold())

    def _store_asset_directory(self, game):
        return self._games_directory / Path(game["_catalog_file"]).stem

    def _store_game_cover_path(self, game):
        image_directory = self._store_asset_directory(game) / "imagens"
        if image_directory.is_dir():
            images = sorted(
                path
                for path in image_directory.iterdir()
                if path.is_file()
                and path.suffix.lower()
                in {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp"}
            )
            if images:
                return images[0]
        return self._find_store_cover(game["titulo"])

    def _read_legacy_game_records(self):
        project_root = Path(__file__).resolve().parent
        legacy_paths = (
            self._games_directory / "jogos.db",
            project_root / "dados" / "arko.db",
        )
        games_by_id = {}
        for database_path in legacy_paths:
            if not database_path.is_file():
                continue
            connection = sqlite3.connect(
                f"{database_path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
            connection.row_factory = sqlite3.Row
            try:
                exists = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='jogos'"
                ).fetchone()
                if exists is None:
                    continue
                available_columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(jogos)")
                }
                required = {"id", "titulo", "descricao", "preco", "empresa"}
                if not required.issubset(available_columns):
                    raise ValueError(
                        f"A tabela de jogos em {database_path} está incompleta."
                    )
                optional = {"capa", "execution_path"} & available_columns
                columns = ["id", "titulo", "descricao", "preco", "empresa"]
                columns.extend(sorted(optional))
                for row in connection.execute(
                    f"SELECT {', '.join(columns)} FROM jogos ORDER BY id"
                ):
                    if row["id"] in games_by_id:
                        continue
                    games_by_id[row["id"]] = {
                        "id": row["id"],
                        "titulo": row["titulo"],
                        "descricao": row["descricao"],
                        "preco": float(row["preco"]),
                        "empresa": row["empresa"],
                        "capa": row["capa"] if "capa" in optional else "",
                        "execution_path": (
                            row["execution_path"]
                            if "execution_path" in optional
                            else ""
                        ),
                    }
            finally:
                connection.close()
        return list(games_by_id.values())

    def open_add_store_game_dialog(self):
        if not self._is_store_admin():
            QMessageBox.warning(
                self,
                "Acesso restrito",
                "Somente o usuário Administrador pode adicionar jogos à Store.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar jogo à Store")
        dialog.setMinimumWidth(520)
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
        previous_price_field = QDoubleSpinBox()
        previous_price_field.setRange(0, 999999999.99)
        previous_price_field.setDecimals(2)
        previous_price_field.setPrefix("R$ ")
        company_field = QLineEdit()
        discount_field = QDoubleSpinBox()
        discount_field.setRange(0, 100)
        discount_field.setDecimals(0)
        discount_field.setSuffix("%")
        form.addRow("Título:", title_field)
        form.addRow("Descrição:", description_field)
        form.addRow("Preço atual:", price_field)
        form.addRow("Preço anterior:", previous_price_field)
        form.addRow("Empresa:", company_field)
        form.addRow("Desconto:", discount_field)

        image_field = QLineEdit()
        image_field.setReadOnly(True)
        image_button = QPushButton("Escolher imagem")
        image_row = QWidget()
        image_layout = QHBoxLayout(image_row)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(image_field)
        image_layout.addWidget(image_button)
        form.addRow("Capa:", image_row)

        executor_field = QLineEdit()
        executor_field.setReadOnly(True)
        executor_button = QPushButton("Escolher executável")
        executor_row = QWidget()
        executor_layout = QHBoxLayout(executor_row)
        executor_layout.setContentsMargins(0, 0, 0, 0)
        executor_layout.addWidget(executor_field)
        executor_layout.addWidget(executor_button)
        form.addRow("Executável:", executor_row)
        layout.addLayout(form)

        def choose_image():
            selected_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Escolher capa do jogo",
                "",
                "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
            )
            if selected_path:
                image_field.setText(selected_path)

        def choose_executor():
            selected_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Escolher arquivo do jogo",
                "",
                "Programas, atalhos e páginas (*.exe *.bat *.cmd *.lnk *.html *.htm);;"
                "Todos os arquivos (*)",
            )
            if selected_path:
                executor_field.setText(selected_path)

        image_button.clicked.connect(choose_image)
        executor_button.clicked.connect(choose_executor)

        buttons = QHBoxLayout()
        save_button = QPushButton("Adicionar")
        cancel_button = QPushButton("Cancelar")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        cancel_button.clicked.connect(dialog.reject)

        def save_store_game():
            data = {
                "titulo": title_field.text().strip(),
                "descricao": description_field.toPlainText().strip(),
                "preco": price_field.value(),
                "preco_ant": previous_price_field.value(),
                "empresa": company_field.text().strip(),
                "desconto": discount_field.value() / 100,
            }
            try:
                validated = self._validate_store_game(data, self._games_directory / "novo.txt")
            except ValueError as error:
                QMessageBox.warning(dialog, "Dados inválidos", str(error))
                return
            if not image_field.text() or not executor_field.text():
                QMessageBox.warning(
                    dialog,
                    "Arquivos obrigatórios",
                    "Escolha a capa e o executável do jogo.",
                )
                return

            title_key = validated["titulo"].casefold()
            if any(game["titulo"].casefold() == title_key for game in self.STORE_GAMES):
                QMessageBox.warning(
                    dialog,
                    "Jogo já cadastrado",
                    "Já existe um jogo com esse título na Store.",
                )
                return

            try:
                executor = self._normalize_launch_target(executor_field.text())
                cover = Path(image_field.text()).resolve(strict=True)
                if not cover.is_file() or QPixmap(str(cover)).isNull():
                    raise ValueError("A imagem da capa não é válida.")

                catalog_number = max(
                    (
                        int(path.name.split("-", 1)[0])
                        for path in self._games_directory.glob("*.txt")
                        if path.name.split("-", 1)[0].isdigit()
                    ),
                    default=-1,
                ) + 1
                stem = f"{catalog_number:03d}-{self._store_game_slug(data['titulo'])}"
                txt_path = self._games_directory / f"{stem}.txt"
                while txt_path.exists():
                    catalog_number += 1
                    stem = f"{catalog_number:03d}-{self._store_game_slug(data['titulo'])}"
                    txt_path = self._games_directory / f"{stem}.txt"
                asset_directory = self._games_directory / stem
                image_directory = asset_directory / "imagens"
                executor_directory = asset_directory / "executador"
                image_directory.mkdir(parents=True, exist_ok=True)
                executor_directory.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cover, image_directory / f"capa{cover.suffix.lower()}")
                if executor.lower().startswith(("http://", "https://")):
                    raise ValueError(
                        "A Store aceita um arquivo de execução; endereços de site não são suportados nesta tela."
                    )
                executor_path = Path(executor)
                shutil.copy2(executor_path, executor_directory / executor_path.name)
                self._write_store_game_txt(data, txt_path)
            except (OSError, RuntimeError, TypeError, ValueError) as error:
                if "asset_directory" in locals() and not txt_path.exists():
                    try:
                        shutil.rmtree(asset_directory)
                    except OSError as cleanup_error:
                        error = OSError(
                            f"{error}; não foi possível limpar os arquivos temporários: "
                            f"{cleanup_error}"
                        )
                QMessageBox.critical(
                    dialog,
                    "Erro ao adicionar jogo",
                    f"Não foi possível salvar o jogo: {error}",
                )
                return

            self.STORE_GAMES = self._load_store_catalog()
            self._rebuild_store_cards()
            dialog.accept()

        save_button.clicked.connect(save_store_game)
        dialog.exec()

    def _rebuild_store_cards(self):
        while self._store_grid.count():
            item = self._store_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._game_cards = self._build_store_cards()
        for index, card in enumerate(self._game_cards):
            card[3].clicked.connect(
                lambda checked=False, game_index=index: self.add_to_cart(game_index)
            )
            self._set_store_cart_button(index)
        self._resize_store_cards_to_fill_panel()

    def _custom_game_directory(self, game_id):
        return self._games_directory / f"jogo_{game_id}"

    def _resolve_game_asset_path(self, stored_path):
        path = Path(str(stored_path or "")).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        return path.resolve()

    @staticmethod
    def _path_is_within(path, directory):
        try:
            path.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            return False

    def _copy_game_asset(self, game_id, source_path, asset_folder, file_name=None):
        source = self._resolve_game_asset_path(source_path)
        if not source.is_file():
            raise FileNotFoundError(f"O arquivo do jogo não foi encontrado: {source}")

        game_directory = self._custom_game_directory(game_id)
        if self._path_is_within(source, game_directory) and (
            file_name is None or source.name == file_name
        ):
            return source.relative_to(Path(__file__).resolve().parent).as_posix()

        destination_directory = game_directory / asset_folder
        destination_directory.mkdir(parents=True, exist_ok=True)
        destination = destination_directory / (
            file_name or source.name
        )
        if source != destination.resolve():
            shutil.copy2(source, destination)
        return destination.relative_to(Path(__file__).resolve().parent).as_posix()

    def _write_custom_game_metadata(self, game):
        game_directory = self._custom_game_directory(game["id"])
        game_directory.mkdir(parents=True, exist_ok=True)
        metadata_path = game_directory / "jogo.txt"
        temporary_path = game_directory / "jogo.txt.tmp"
        with temporary_path.open("w", encoding="utf-8") as file:
            file.write(self._store_game_text(game))
        temporary_path.replace(metadata_path)

    def _migrate_custom_game_files(self):
        self._games_directory.mkdir(parents=True, exist_ok=True)
        migration_marker = self._games_directory / ".legacy-library-migration-done"
        if migration_marker.exists():
            return True

        missing_assets = []
        try:
            for game in self._read_legacy_game_records():
                game_directory = self._custom_game_directory(game["id"])
                metadata_path = game_directory / "jogo.txt"
                if game["capa"] and not any(
                    (game_directory / "imagens").glob("*")
                ):
                    cover_source = self._resolve_game_asset_path(game["capa"])
                    if cover_source.is_file():
                        cover_extension = cover_source.suffix.lower() or ".png"
                        self._copy_game_asset(
                            game["id"],
                            cover_source,
                            "imagens",
                            f"capa{cover_extension}",
                        )
                    else:
                        missing_assets.append(f"{game['titulo']}: capa não encontrada")

                execution_path = str(game["execution_path"] or "").strip()
                if execution_path and not execution_path.lower().startswith(
                    ("http://", "https://")
                ) and not any((game_directory / "executador").glob("*")):
                    executor_source = self._resolve_game_asset_path(execution_path)
                    if executor_source.is_file():
                        self._copy_game_asset(
                            game["id"],
                            executor_source,
                            "executador",
                        )
                    else:
                        missing_assets.append(
                            f"{game['titulo']}: arquivo de execução não encontrado"
                        )

                if execution_path.lower().startswith(("http://", "https://")):
                    executor_directory = game_directory / "executador"
                    executor_directory.mkdir(parents=True, exist_ok=True)
                    (executor_directory / "url.txt").write_text(
                        execution_path,
                        encoding="utf-8",
                    )

                if not metadata_path.exists():
                    self._write_custom_game_metadata(
                        {
                            "id": game["id"],
                            "titulo": game["titulo"],
                            "descricao": game["descricao"],
                            "preco": game["preco"],
                            "preco_ant": game["preco"],
                            "empresa": game["empresa"],
                            "desconto": 0.0,
                        }
                    )

            for metadata_path in self._games_directory.glob("jogo_*/jogo.json"):
                with metadata_path.open("r", encoding="utf-8") as file:
                    game = json.load(file)
                if not isinstance(game, dict):
                    raise ValueError(f"Arquivo inválido: {metadata_path}")
                folder_id = metadata_path.parent.name[len("jogo_"):]
                game_id = int(game.get("id", folder_id))
                text_path = metadata_path.with_name("jogo.txt")
                if not text_path.exists():
                    self._write_custom_game_metadata(
                        {
                            "id": game_id,
                            "titulo": str(game["titulo"]),
                            "descricao": str(game["descricao"]),
                            "preco": float(game["preco"]),
                            "preco_ant": float(game["preco"]),
                            "empresa": str(game["empresa"]),
                            "desconto": 0.0,
                        }
                    )

            if missing_assets:
                QMessageBox.warning(
                    self,
                    "Arquivos de jogos não encontrados",
                    "Alguns arquivos antigos não puderam ser copiados para as "
                    "pastas dos jogos:\n" + "\n".join(missing_assets),
                )
            migration_marker.write_text("done\n", encoding="utf-8")
        except (OSError, sqlite3.Error, TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Erro ao organizar jogos",
                f"Não foi possível migrar as informações e arquivos dos jogos: {error}",
            )
            return False
        return True

    def _load_custom_games(self):
        self._custom_games = []
        self._custom_games_load_error = self._custom_game_files_error
        try:
            for metadata_path in sorted(
                self._games_directory.glob("jogo_*/jogo.txt"),
                key=lambda path: int(path.parent.name[len("jogo_"):]),
            ):
                data = ast.literal_eval(metadata_path.read_text(encoding="utf-8"))
                game = self._validate_store_game(data, metadata_path)
                game_id = int(metadata_path.parent.name[len("jogo_"):])
                image_directory = metadata_path.parent / "imagens"
                images = sorted(
                    path
                    for path in image_directory.iterdir()
                    if path.is_file()
                    and path.suffix.lower()
                    in {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp"}
                ) if image_directory.is_dir() else []
                executor_directory = metadata_path.parent / "executador"
                executors = sorted(
                    path
                    for path in executor_directory.iterdir()
                    if path.is_file()
                    and path.name != "url.txt"
                ) if executor_directory.is_dir() else []
                url_path = executor_directory / "url.txt"
                execution_path = (
                    url_path.read_text(encoding="utf-8").strip()
                    if url_path.is_file()
                    else str(executors[0]) if executors else ""
                )
                self._custom_games.append(
                    {
                        "id": game_id,
                        "titulo": game["titulo"],
                        "descricao": game["descricao"],
                        "preco": game["preco"],
                        "preco_ant": game["preco_ant"],
                        "empresa": game["empresa"],
                        "capa": str(images[0]) if images else "",
                        "execution_path": execution_path,
                    }
                )
        except (OSError, SyntaxError, TypeError, ValueError) as error:
            self._custom_games_load_error = True
            QMessageBox.critical(
                self,
                "Erro ao carregar jogos",
                f"Não foi possível carregar os jogos salvos: {error}",
            )

    def _setup_library_page(self):
        self._library_panel = QWidget(parent=self.ui.Barra1)
        self._library_panel.setObjectName("LibraryPanel")
        self._library_panel.setGeometry(self.ui.Menu3.geometry())
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

    def _setup_cart_page(self):
        self._cart_panel = QWidget(parent=self.ui.Barra1)
        self._cart_panel.setObjectName("CartPanel")
        self._cart_panel.setGeometry(self.ui.Menu3.geometry())
        self._cart_panel.setStyleSheet(
            "QWidget#CartPanel { background-color: #000000; color: #FFFFFF; "
            "border: 2px solid #FFFFFF; border-radius: 8px; }"
        )

        layout = QVBoxLayout(self._cart_panel)
        layout.setContentsMargins(24, 24, 24, 16)
        self._cart_scroll = QScrollArea(self._cart_panel)
        self._cart_scroll.setWidgetResizable(True)
        self._cart_scroll.setStyleSheet(
            "QScrollArea { background-color: #000000; border: none; }"
            "QWidget { background-color: #000000; }"
        )
        self._cart_content = QWidget()
        self._cart_content.setStyleSheet("background-color: #000000;")
        self._cart_grid = QGridLayout(self._cart_content)
        self._cart_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._cart_grid.setContentsMargins(8, 8, 8, 8)
        self._cart_grid.setHorizontalSpacing(20)
        self._cart_grid.setVerticalSpacing(20)
        self._cart_scroll.setWidget(self._cart_content)
        layout.addWidget(self._cart_scroll)

        self._cart_empty_label = QLabel("Seu carrinho está vazio.")
        self._cart_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cart_empty_label.setStyleSheet(
            "color: #FFFFFF; font-weight: bold;"
        )
        self._set_font_size(self._cart_empty_label, 15, bold=True)
        self._cart_grid.addWidget(self._cart_empty_label, 0, 0)

        self._cart_purchase_button = QPushButton("Comprar carrinho")
        self._cart_purchase_button.setStyleSheet(
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 10px; "
            "font-weight: bold; padding: 10px 24px; }"
            "QPushButton:hover { background-color: #FFFFFF; border-color: #FFFFFF; }"
        )
        self._cart_purchase_button.clicked.connect(self.purchase_cart)
        layout.addWidget(self._cart_purchase_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self._cart_panel.hide()
        self._cart_card_widgets = []

    def _refresh_cart_page(self):
        while self._cart_grid.count():
            item = self._cart_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cart_card_widgets.clear()

        if not self._cart_games:
            self._cart_empty_label = QLabel("Seu carrinho está vazio.")
            self._cart_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cart_empty_label.setStyleSheet(
                "color: #FFFFFF; font-weight: bold;"
            )
            self._set_font_size(self._cart_empty_label, 15, bold=True)
            self._cart_grid.addWidget(self._cart_empty_label, 0, 0)
            self._cart_purchase_button.hide()
            return

        self._cart_purchase_button.show()
        available_width = max(1, self.ui.Menu3.width() - 64)
        card_width = 201
        columns = max(1, (available_width + 20) // (card_width + 20))

        for position, game_index in enumerate(sorted(self._cart_games)):
            game = self.STORE_GAMES[game_index]
            card = QFrame()
            card.setObjectName("CartGameCard")
            card.setFixedSize(card_width, 321)
            card.setStyleSheet(
                "QFrame#CartGameCard { background-color: #000000; color: #FFFFFF; "
                "border: 2px solid #FFFFFF; border-radius: 10px; }"
                "QLabel { border: none; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(4)

            cover_label = QLabel()
            cover_label.setFixedSize(161, 221)
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = self._game_cards[game_index][1].pixmap()
            if pixmap is not None and not pixmap.isNull():
                cover_label.setPixmap(
                    pixmap.scaled(
                        cover_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            card_layout.addWidget(cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(game["titulo"])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            name_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            name_label.setFixedHeight(28)
            card_layout.addWidget(name_label)

            price_label = QLabel(f"R$ {game['preco']:.2f}".replace(".", ","))
            price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_label.setStyleSheet(
                "color: #00FF00; border: 1px solid #00FF00; "
                "border-radius: 8px; font-weight: bold; padding: 4px;"
            )
            price_label.setFixedHeight(25)
            card_layout.addWidget(price_label)

            row, column = divmod(position, columns)
            self._cart_grid.addWidget(card, row, column)
            self._cart_card_widgets.append(card)

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
        review_rating=None,
        review_callback=None,
        remove_review_callback=None,
        launch_callback=None,
    ):
        card = QFrame()
        card.setFixedSize(201, 420 if review_callback is not None else 370)
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
        if launch_callback is None:
            play_button.setEnabled(False)
            play_button.setToolTip("Nenhum arquivo ou link foi configurado.")
        else:
            play_button.clicked.connect(launch_callback)
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

        if review_callback is not None:
            review_label = QLabel(
                "Sua avaliação: "
                + (
                    f"{'★' * review_rating}{'☆' * (5 - review_rating)} "
                    f"({review_rating}/5)"
                    if review_rating is not None
                    else "Ainda não avaliado"
                )
            )
            review_label.setFixedHeight(20)
            review_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            review_label.setStyleSheet("color: #FFD700; font-weight: bold;")
            layout.addWidget(review_label)

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

        if review_callback is not None:
            review_actions = QHBoxLayout()
            review_button = QPushButton(
                "Alterar avaliação" if review_rating is not None else "Avaliar"
            )
            review_button.setToolTip("Avaliar este jogo de 1 a 5 estrelas")
            review_button.setFixedHeight(29)
            review_button.setStyleSheet(
                "QPushButton { background-color: #00FF00; color: black; "
                "border: 2px solid #00FF00; border-radius: 8px; "
                "font-weight: bold; }"
            )
            review_button.clicked.connect(review_callback)
            review_actions.addWidget(review_button)

            if remove_review_callback is not None and review_rating is not None:
                remove_review_button = QPushButton("Remover")
                remove_review_button.setToolTip("Remover sua avaliação")
                remove_review_button.setFixedHeight(29)
                remove_review_button.setStyleSheet(
                    "QPushButton { background-color: #000000; color: #FFFFFF; "
                    "border: 1px solid #FFFFFF; border-radius: 6px; "
                    "font-weight: bold; }"
                    "QPushButton:hover { background-color: #808080; color: black; }"
                )
                remove_review_button.clicked.connect(remove_review_callback)
                review_actions.addWidget(remove_review_button)

            layout.addLayout(review_actions)

        return card

    def _refresh_library(self):
        while self._library_grid.count():
            item = self._library_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        cards = []
        for index in sorted(self._library_games):
            game = self.STORE_GAMES[index]
            cover = self._game_cards[index][1].pixmap()
            active_purchase = (
                self._active_purchase_for_game(self._current_user_email, index)
                if self._current_user_email is not None
                else None
            )
            user_review = (
                self._get_user_review(self._current_user_email, index)
                if active_purchase is not None
                else None
            )
            review_callback = (
                lambda checked=False, game_index=index: self.rate_builtin_game(game_index)
            )
            remove_review_callback = (
                lambda checked=False, game_index=index: self.remove_builtin_review(
                    game_index
                )
            )
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
                    user_review["nota"] if user_review is not None else None,
                    review_callback if active_purchase is not None else None,
                    remove_review_callback if user_review is not None else None,
                    launch_callback=lambda checked=False, game_index=index: self._launch_store_game(
                        game_index
                    ),
                )
            )

        for index, game in enumerate(self._custom_games):
            cover_path = self._resolve_game_asset_path(game["capa"])
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
                    launch_callback=lambda checked=False, game_index=index: self._launch_game(
                        self._custom_games[game_index].get("execution_path", "")
                    ),
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
        self._set_font_size(add_card, 18)
        add_card.clicked.connect(
            lambda checked=False: self.open_add_game_dialog()
        )
        cards.append(add_card)

        for index, card in enumerate(cards):
            row, column = divmod(index, 5)
            self._library_grid.addWidget(card, row, column)

        if self._custom_games_load_error:
            add_card.setEnabled(False)

    def _normalize_launch_target(self, target):
        target = target.strip()
        if not target:
            return ""

        if target.lower().startswith(("http://", "https://")):
            try:
                parsed_url = urlsplit(target)
            except ValueError as error:
                raise ValueError("O endereço do site não é válido.") from error
            if parsed_url.scheme.lower() not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError("Informe um endereço completo começando com http:// ou https://.")
            return target

        file_path = Path(target).expanduser()
        if not file_path.is_absolute():
            file_path = Path(__file__).resolve().parent / file_path
        try:
            file_path = file_path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError("O arquivo selecionado não foi encontrado.") from error
        if not file_path.is_file():
            raise ValueError("O destino selecionado precisa ser um arquivo.")
        return str(file_path)

    def _launch_game(self, target):
        target = str(target or "").strip()
        if not target:
            QMessageBox.information(
                self,
                "Destino não configurado",
                "Edite o jogo na Biblioteca e selecione um arquivo ou endereço de site.",
            )
            return

        try:
            if target.lower().startswith(("http://", "https://")):
                opened = QDesktopServices.openUrl(QUrl(target))
                if not opened:
                    raise OSError("O navegador não conseguiu abrir o endereço.")
            else:
                file_path = self._resolve_game_asset_path(target)
                if not file_path.is_file():
                    raise OSError("O arquivo configurado não foi encontrado.")
                start_file = getattr(os, "startfile", None)
                if start_file is not None:
                    start_file(str(file_path))
                elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path))):
                    raise OSError("O sistema não conseguiu abrir o arquivo.")
        except OSError as error:
            QMessageBox.critical(
                self,
                "Não foi possível iniciar o jogo",
                f"Falha ao abrir o destino configurado: {error}",
            )

    def _launch_store_game(self, game_index):
        game = self.STORE_GAMES[game_index]
        normalized_title = self._normalize_cover_name(game["titulo"])
        try:
            game_executor_directory = (
                self._store_asset_directory(game) / "executador"
            )
            game_files = (
                sorted(
                    file_path
                    for file_path in game_executor_directory.iterdir()
                    if file_path.is_file()
                )
                if game_executor_directory.is_dir()
                else []
            )
            matching_files = game_files or sorted(
                file_path
                for file_path in self._store_executor_dir.iterdir()
                if file_path.is_file()
                and self._normalize_cover_name(file_path.stem) == normalized_title
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Erro ao procurar jogo",
                f"Não foi possível acessar a pasta {self._store_executor_dir}: {error}",
            )
            return

        if not matching_files:
            QMessageBox.information(
                self,
                "Arquivo não encontrado",
                f"Coloque o arquivo do jogo na pasta "
                f"{self._store_asset_directory(game) / 'executador'} ou em "
                f"{self._store_executor_dir}.",
            )
            return
        if len(matching_files) > 1:
            file_names = "\n".join(file_path.name for file_path in matching_files)
            QMessageBox.warning(
                self,
                "Mais de um arquivo encontrado",
                f"Mantenha apenas um arquivo de execução para “{game['titulo']}”:\n"
                f"{file_names}",
            )
            return

        self._launch_game(str(matching_files[0]))

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
                "Corrija os arquivos TXT das pastas em jogos/ antes de adicionar jogos.",
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
        launch_target_field = QLineEdit()
        launch_target_field.setPlaceholderText(
            "Arquivo local ou endereço de site (obrigatório)"
        )
        if editing_game is not None:
            title_field.setText(editing_game["titulo"])
            description_field.setPlainText(editing_game["descricao"])
            price_field.setValue(float(editing_game["preco"]))
            company_field.setText(editing_game["empresa"])
            launch_target_field.setText(editing_game.get("execution_path", ""))
        form.addRow("Título:", title_field)
        form.addRow("Descrição:", description_field)
        form.addRow("Preço:", price_field)
        form.addRow("Empresa:", company_field)

        launch_target_row = QWidget()
        launch_target_layout = QHBoxLayout(launch_target_row)
        launch_target_layout.setContentsMargins(0, 0, 0, 0)
        launch_target_layout.addWidget(launch_target_field)
        choose_launch_target_button = QPushButton("Escolher arquivo")
        launch_target_layout.addWidget(choose_launch_target_button)
        form.addRow("Executável ou site:", launch_target_row)
        layout.addLayout(form)

        def choose_launch_target():
            selected_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Escolher arquivo para iniciar",
                "",
                "Programas, atalhos e páginas (*.exe *.bat *.cmd *.lnk *.html *.htm);;"
                "Todos os arquivos (*)",
            )
            if selected_path:
                launch_target_field.setText(selected_path)

        choose_launch_target_button.clicked.connect(choose_launch_target)

        cover_path = {"value": ""}
        current_cover = (
            self._resolve_game_asset_path(editing_game["capa"])
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
            try:
                launch_target = self._normalize_launch_target(
                    launch_target_field.text()
                )
            except ValueError as error:
                QMessageBox.warning(dialog, "Destino inválido", str(error))
                return
            if not title or not description or not company:
                QMessageBox.warning(
                    dialog,
                    "Campos obrigatórios",
                    "Preencha o título, a descrição e a empresa.",
                )
                return
            if not launch_target:
                QMessageBox.warning(
                    dialog,
                    "Executável obrigatório",
                    "Escolha um arquivo para iniciar o jogo ou informe um endereço de site.",
                )
                return
            source_cover = Path(cover_path["value"]) if cover_path["value"] else None
            if (
                source_cover is None
                and initial_cover is None
                and (current_cover is None or not current_cover.is_file())
            ):
                QMessageBox.warning(
                    dialog, "Capa obrigatória", "Escolha uma capa para o jogo."
                )
                return

            game_id = (
                self._custom_games[game_index]["id"]
                if game_index is not None
                else max((game["id"] for game in self._custom_games), default=0) + 1
            )
            while (
                game_index is None
                and self._custom_game_directory(game_id).exists()
            ):
                game_id += 1
            game_directory = self._custom_game_directory(game_id)
            is_new_game = game_index is None

            try:
                if source_cover is not None:
                    cover_extension = source_cover.suffix.lower() or ".png"
                    self._copy_game_asset(
                        game_id,
                        source_cover,
                        "imagens",
                        f"capa{cover_extension}",
                    )
                elif initial_cover is not None:
                    cover_directory = game_directory / "imagens"
                    cover_directory.mkdir(parents=True, exist_ok=True)
                    destination_cover = cover_directory / "capa.png"
                    if not initial_cover.save(str(destination_cover), "PNG"):
                        raise OSError("Não foi possível salvar a capa do jogo.")
                else:
                    self._copy_game_asset(
                        game_id,
                        current_cover,
                        "imagens",
                        f"capa{current_cover.suffix.lower() or '.png'}",
                    )

                if launch_target.lower().startswith(("http://", "https://")):
                    executor_directory = game_directory / "executador"
                    executor_directory.mkdir(parents=True, exist_ok=True)
                    for existing_executor in executor_directory.iterdir():
                        if existing_executor.is_file():
                            existing_executor.unlink()
                    (executor_directory / "url.txt").write_text(
                        launch_target,
                        encoding="utf-8",
                    )
                else:
                    executor_directory = game_directory / "executador"
                    executor_directory.mkdir(parents=True, exist_ok=True)
                    executor_source = self._resolve_game_asset_path(launch_target)
                    if not self._path_is_within(executor_source, executor_directory):
                        for existing_executor in executor_directory.iterdir():
                            if existing_executor.is_file():
                                existing_executor.unlink()
                        self._copy_game_asset(game_id, launch_target, "executador")

                image_directory = game_directory / "imagens"
                for existing_image in image_directory.iterdir():
                    if (
                        existing_image.is_file()
                        and existing_image != image_directory / f"capa{existing_image.suffix.lower()}"
                    ):
                        existing_image.unlink()
                game_data = {
                    "id": game_id,
                    "titulo": title,
                    "descricao": description,
                    "preco": float(price_field.value()),
                    "preco_ant": float(price_field.value()),
                    "empresa": company,
                    "desconto": 0.0,
                }
                self._write_custom_game_metadata(game_data)
                saved_game = dict(game_data)
                saved_game["capa"] = str(
                    next(
                        path
                        for path in image_directory.iterdir()
                        if path.is_file()
                    )
                )
                url_path = game_directory / "executador" / "url.txt"
                saved_game["execution_path"] = (
                    url_path.read_text(encoding="utf-8").strip()
                    if url_path.is_file()
                    else str(
                        next(
                            path
                            for path in executor_directory.iterdir()
                            if path.is_file()
                        )
                    )
                )
            except (OSError, StopIteration, TypeError, ValueError) as error:
                if is_new_game:
                    try:
                        shutil.rmtree(game_directory)
                    except OSError as cleanup_error:
                        error = OSError(
                            f"{error}; não foi possível limpar o cadastro incompleto: "
                            f"{cleanup_error}"
                        )
                QMessageBox.critical(
                    dialog,
                    "Erro ao salvar jogo",
                    f"Não foi possível salvar o jogo: {error}",
                )
                return

            if game_index is None:
                self._custom_games.append(saved_game)
            else:
                self._custom_games[game_index] = saved_game
            if builtin_index is not None:
                self._library_games.discard(builtin_index)
            dialog.accept()

        save_button.clicked.connect(save_game)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_library()

    def edit_builtin_game(self, game_index):
        self.open_add_game_dialog(
            initial_game=self.STORE_GAMES[game_index],
            initial_cover=self._game_cards[game_index][1].pixmap(),
            builtin_index=game_index,
        )

    def rate_builtin_game(self, game_index):
        if self._current_user_email is None:
            QMessageBox.information(
                self,
                "Conta necessária",
                "Entre em uma conta para avaliar este jogo.",
            )
            return
        if self._active_purchase_for_game(self._current_user_email, game_index) is None:
            QMessageBox.warning(
                self,
                "Avaliação indisponível",
                "Só é possível avaliar um jogo comprado e não reembolsado.",
            )
            return

        existing_review = self._get_user_review(self._current_user_email, game_index)
        rating, accepted = QInputDialog.getInt(
            self,
            "Avaliar jogo",
            "Escolha uma nota de 1 a 5 estrelas:",
            existing_review["nota"] if existing_review is not None else 5,
            1,
            5,
        )
        if not accepted:
            return

        updated_reviews = [
            review
            for review in self._reviews
            if not (
                review["usuario"].casefold() == self._current_user_email.casefold()
                and review["jogo_id"] == str(game_index)
            )
        ]
        updated_reviews.append(
            {
                "usuario": self._current_user_email,
                "jogo_id": str(game_index),
                "nota": rating,
                "data": datetime.now(timezone.utc).isoformat(),
            }
        )
        if self._save_reviews(updated_reviews):
            existing_db_review = self.avaliacao_repo.buscar_por_usuario_e_jogo(self._current_user_email, game_index)
            if existing_db_review is None:
                self.avaliacao_repo.inserir(
                    Avaliacao(self._current_user_email, game_index, rating, datetime.now(timezone.utc).isoformat())
                )
            else:
                existing_db_review.nota = rating
                existing_db_review.data = datetime.now(timezone.utc).isoformat()
                self.avaliacao_repo.atualizar(existing_db_review)
            self._refresh_library()

    def remove_builtin_review(self, game_index):
        if self._current_user_email is None:
            QMessageBox.information(
                self,
                "Conta necessária",
                "Entre em uma conta para remover sua avaliação.",
            )
            return
        if self._active_purchase_for_game(self._current_user_email, game_index) is None:
            QMessageBox.warning(
                self,
                "Avaliação indisponível",
                "Só é possível alterar a avaliação de um jogo comprado e não reembolsado.",
            )
            return

        existing_review = self._get_user_review(self._current_user_email, game_index)
        if existing_review is None:
            QMessageBox.information(
                self,
                "Avaliação não encontrada",
                "Você ainda não avaliou este jogo.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Remover avaliação",
            f"Deseja remover sua avaliação de "
            f"“{self.STORE_GAMES[game_index]['titulo']}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        updated_reviews = [
            review
            for review in self._reviews
            if not (
                review["usuario"].casefold() == self._current_user_email.casefold()
                and review["jogo_id"] == str(game_index)
            )
        ]
        if self._save_reviews(updated_reviews):
            existing_db_review = self.avaliacao_repo.buscar_por_usuario_e_jogo(self._current_user_email, game_index)
            if existing_db_review is not None:
                self.avaliacao_repo.excluir(existing_db_review.id)
            self._refresh_library()

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
                and any(
                    self._transaction_item_matches_game(item, game_index)
                    for item in transaction["jogos"]
                )
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

        self.biblioteca_repo.remover(self._current_user_email, game_index)
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
        self._custom_games = updated_games
        try:
            game_directory = self._custom_game_directory(removed_game["id"]).resolve()
            if game_directory.parent != self._games_directory.resolve():
                raise ValueError("A pasta do jogo está fora do diretório permitido.")
            if game_directory.exists():
                shutil.rmtree(game_directory)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Arquivos do jogo não removidos",
                f"O jogo foi apagado, mas não foi possível remover sua pasta: {error}",
            )
        except ValueError as error:
            QMessageBox.critical(
                self,
                "Pasta do jogo inválida",
                f"O jogo foi apagado, mas a pasta foi preservada: {error}",
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

        email = str(friend_item.data(Qt.ItemDataRole.UserRole) or "")
        if not email:
            self._friend_status.setStyleSheet("color: #FF7777;")
            self._friend_status.setText("Não foi possível identificar o amigo selecionado.")
            return

        existing = self.amigo_repo.buscar_por_email(self._current_user_email, email)
        if existing is not None:
            self.amigo_repo.excluir(existing.id)

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
        if is_editing:
            friend_item = self._editing_friend_item
            existing = self.amigo_repo.buscar_por_email(self._current_user_email, str(friend_item.data(Qt.ItemDataRole.UserRole) or ""))
            if existing is not None:
                existing.nome = name
                existing.email = email
                self.amigo_repo.atualizar(existing)
        else:
            self.amigo_repo.inserir(Amigo(self._current_user_email, name, email))
            friend_item = QListWidgetItem()
            self._friends_list.addItem(friend_item)

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
        self._account_tabs.setTabVisible(1, self._current_user_email is None)
        self._account_tabs.setTabVisible(2, self._current_user_email is not None)
        self._account_tabs.setCurrentIndex(
            2 if self._current_user_email is not None else 0
        )
        self._show_page("registration")

    def show_account(self):
        self.show_registration()

    def show_account_edit(self):
        self._account_status.clear()
        self._account_current_password.clear()
        self._account_password.clear()
        self._account_password_confirmation.clear()
        self._account_edit_panel.show()

    def _activate_account(self, email, name):
        self._current_user_email = email
        self._current_user_name = name
        self._update_store_admin_controls()
        self._load_user_library(email)
        self._load_friends_from_db()
        self.ui.Conta.setText(f"👤 {name}")
        self._account_welcome.setText(f"Bem-vindo: {name}")
        self._account_name.setText(name)
        self._account_email.setText(email)
        self._account_current_password.clear()
        self._account_password.clear()
        self._account_password_confirmation.clear()
        self._account_edit_panel.hide()
        self._login_email.clear()
        self._login_password.clear()
        self.show_registration()

    def _verify_password(self, password, stored_password):
        if stored_password.startswith("pbkdf2_sha256$"):
            try:
                algorithm, iterations_text, salt_hex, expected_hash = (
                    stored_password.split("$")
                )
                iterations = int(iterations_text)
                if algorithm != "pbkdf2_sha256" or not 1 <= iterations <= 10_000_000:
                    return False, False
                if (
                    not salt_hex
                    or len(expected_hash) != 64
                    or not expected_hash.isascii()
                    or any(character not in "0123456789abcdefABCDEF" for character in expected_hash)
                ):
                    return False, False
                salt = bytes.fromhex(salt_hex)
                actual_hash = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt,
                    iterations,
                ).hex()
            except (ValueError, OverflowError):
                return False, False
            return secrets.compare_digest(actual_hash, expected_hash), False

        matches_legacy_password = secrets.compare_digest(
            password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )
        return matches_legacy_password, matches_legacy_password

    def _upgrade_legacy_password(self, email, new_password_hash):
        users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
        temporary_file = users_file.with_suffix(".csv.tmp")
        try:
            with users_file.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))
            if not rows or not {"nome", "senha", "email"}.issubset(rows[0]):
                raise ValueError("O arquivo de contas possui um cabeçalho inválido.")

            fieldnames = rows[0]
            password_index = fieldnames.index("senha")
            email_index = fieldnames.index("email")
            account = next(
                (
                    row
                    for row in rows[1:]
                    if len(row) > email_index
                    and row[email_index].strip().casefold() == email.casefold()
                ),
                None,
            )
            if account is None or len(account) <= password_index:
                raise ValueError("Não foi possível localizar a conta para atualizar a senha.")
            account[password_index] = new_password_hash

            with temporary_file.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            temporary_file.replace(users_file)
        except (OSError, csv.Error, UnicodeError, ValueError) as error:
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError as cleanup_error:
                error = OSError(f"{error}; falha ao limpar arquivo temporário: {cleanup_error}")
            QMessageBox.critical(
                self,
                "Erro ao atualizar senha",
                f"A senha antiga foi aceita, mas não foi possível protegê-la: {error}",
            )
            return False
        return True

    def login_user(self):
        email = self._login_email.text().strip()
        password = self._login_password.text()
        if not email or not password:
            self._login_status.setStyleSheet("color: #FF7777;")
            self._login_status.setText("Digite seu e-mail e sua senha.")
            return

        account = self.usuario_repo.buscar_por_email(email)
        if account is None:
            users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
            try:
                with users_file.open("r", newline="", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    row = next(
                        (
                            row
                            for row in reader
                            if str(row.get("email") or "").strip().casefold() == email.casefold()
                        ),
                        None,
                    )
                if row is not None:
                    account = Usuario(str(row.get("nome") or "").strip(), email, str(row.get("senha") or "").strip())
            except (FileNotFoundError, OSError, csv.Error, UnicodeError):
                pass

        if account is None or not account.senha or not account.nome:
            self._login_status.setStyleSheet("color: #FF7777;")
            self._login_status.setText("E-mail ou senha incorretos.")
            return

        password_matches, needs_upgrade = self._verify_password(
            password, account.senha
        )
        if not password_matches:
            self._login_status.setStyleSheet("color: #FF7777;")
            self._login_status.setText("E-mail ou senha incorretos.")
            return

        account_email = str(account.email or "").strip()
        if needs_upgrade and not self._upgrade_legacy_password(
            account_email, self._hash_password(password)
        ):
            return

        self._login_status.setStyleSheet("color: #00FF00;")
        self._login_status.setText("Login realizado com sucesso.")
        self._activate_account(account_email, str(account.nome).strip())

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

        existing = self.usuario_repo.buscar_por_email(email)
        if existing is not None:
            self._registration_status.setStyleSheet("color: #FF7777;")
            self._registration_status.setText("Já existe uma conta com esse e-mail.")
            return

        users_file = Path(__file__).resolve().parent / "dados" / "usuario.csv"
        try:
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

        self.usuario_repo.inserir(Usuario(name, email, self._hash_password(password)))

        self._registration_name.clear()
        self._registration_email.clear()
        self._registration_password.clear()
        self._registration_status.setStyleSheet("color: #00FF00;")
        self._registration_status.setText("Cadastro realizado com sucesso!")
        self._activate_account(email, name)

    def update_account(self):
        if self._current_user_email is None:
            self._show_account_status("Nenhuma conta está conectada.")
            return

        name = self._account_name.text().strip()
        email = self._account_email.text().strip()
        password = self._account_password.text()
        current_password = self._account_current_password.text()
        password_confirmation = self._account_password_confirmation.text()
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

        current_user = self.usuario_repo.buscar_por_email(self._current_user_email)
        if password:
            if password_confirmation != password:
                self._show_account_status("A confirmação da nova senha não corresponde.")
                return
            if (
                current_user is None
                or not current_user.senha
                or not self._verify_password(current_password, current_user.senha)[0]
            ):
                self._show_account_status("A senha atual está incorreta.")
                return

        updated_password_hash = self._hash_password(password) if password else None
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
            if updated_password_hash:
                account[password_index] = updated_password_hash

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

        if current_user is not None:
            current_user.nome = name
            current_user.email = email
            if updated_password_hash:
                current_user.senha = updated_password_hash
            self.usuario_repo.atualizar(current_user)

        self._current_user_email = email
        self._current_user_name = name
        self._update_store_admin_controls()
        self._account_current_password.clear()
        self._account_current_password.clear()
        self._account_password.clear()
        self._account_password_confirmation.clear()
        self.ui.Conta.setText(f"👤 {name}")
        self._account_welcome.setText(f"Bem-vindo: {name}")
        self._account_edit_panel.hide()
        self._show_account_status("Conta alterada com sucesso.", success=True)

    def logout(self):
        self._current_user_email = None
        self._current_user_name = None
        self._update_store_admin_controls()
        self._library_games.clear()
        self._friends_list.clear()
        self._account_name.clear()
        self._account_email.clear()
        self._account_current_password.clear()
        self._account_password.clear()
        self._account_password_confirmation.clear()
        self._account_status.clear()
        self._login_email.clear()
        self._login_password.clear()
        self._login_status.clear()
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
        self._set_store_cart_button(game_index)

        if self._active_page == "cart":
            self._show_page("cart")

    def _set_store_cart_button(self, game_index):
        button = self._game_cards[game_index][3]
        if game_index in self._cart_games:
            button.setText("Adicionado")
            button.setStyleSheet(
                "QPushButton { background-color: #FFFFFF; color: black; "
                "border: 2px solid #FFFFFF; border-radius: 8px; "
                "font-weight: bold; }"
            )
            return

        button.setText("Adicionar ao carrinho")
        button.setStyleSheet(
            "QPushButton { background-color: #00FF00; color: black; "
            "border: 2px solid #00FF00; border-radius: 8px; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #FFFFFF; border-color: #FFFFFF; }"
        )

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
                "titulo": self.STORE_GAMES[index]["titulo"],
                "valor": self.STORE_GAMES[index]["preco"],
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

        for game in games:
            self.biblioteca_repo.inserir(
                Biblioteca(self._current_user_email, int(game["id"]), game["titulo"])
            )

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

        if hasattr(self, "_base_geometries"):
            central_size = self.ui.centralwidget.size()
            base_scroll_area = self._base_geometries[self.ui.scrollArea]
            scale_x = central_size.width() / base_scroll_area.width()
            scale_y = central_size.height() / base_scroll_area.height()
            font_scale = max(0.85, min(1.5, min(scale_x, scale_y)))
            font_scale_delta = font_scale / self._current_font_scale
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
            for widget in self.findChildren(QWidget):
                font = widget.font()
                point_size = font.pointSizeF()
                if point_size > 0:
                    font.setPointSizeF(point_size * font_scale_delta)
                elif font.pixelSize() > 0:
                    font.setPixelSize(
                        max(1, round(font.pixelSize() * font_scale_delta))
                    )
                else:
                    continue
                widget.setFont(font)
            self._current_font_scale = font_scale

        if hasattr(self, "_content_panels"):
            self._sync_all_panels_to_main_area()
            self._resize_store_cards_to_fill_panel()
            if getattr(self, "_active_page", None) == "cart":
                self._refresh_cart_page()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()