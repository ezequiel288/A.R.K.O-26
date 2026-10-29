import json
import sqlite3
from pathlib import Path


class BancoDeDados:
    """Gerencia a conexão e a estrutura do banco SQLite do projeto."""

    def __init__(self, arquivo="dados/arko.db"):
        self.arquivo = Path(arquivo)
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(self.arquivo)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        self.criar_tabelas()

    def criar_tabelas(self):
        sqls = (
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                preco REAL NOT NULL,
                empresa TEXT NOT NULL,
                capa TEXT DEFAULT ''
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS biblioteca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                data_adicao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS amigos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                nome TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                nota INTEGER NOT NULL CHECK(nota BETWEEN 1 AND 5),
                data TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transacoes (
                id TEXT PRIMARY KEY,
                usuario_email TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('compra', 'reembolso')),
                jogos TEXT NOT NULL,
                valor REAL NOT NULL,
                valor_pago REAL,
                data TEXT NOT NULL,
                compra_id TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS carrinho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 1,
                valor_unitario REAL NOT NULL,
                data_adicao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )

        with self.conexao:
            for sql in sqls:
                self.conexao.execute(sql)

    def fechar(self):
        self.conexao.close()

    @staticmethod
    def serializar_jogos(jogos):
        return json.dumps(jogos, ensure_ascii=False)

    @staticmethod
    def desserializar_jogos(valor):
        return json.loads(valor) if valor else []
