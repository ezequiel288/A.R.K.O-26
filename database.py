import json
import sqlite3
from pathlib import Path


class BancoDeDados:
    """Gerencia a conexão e a estrutura do banco SQLite do projeto."""

    def __init__(self, arquivo="dados/arko.db", perfil="completo"):
        if perfil not in {"completo", "principal", "avaliacoes", "biblioteca"}:
            raise ValueError(f"Perfil de banco de dados inválido: {perfil}")
        self.perfil = perfil
        self.arquivo = Path(arquivo)
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(self.arquivo)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        self.criar_tabelas()

    def criar_tabelas(self):
        tabelas = {
            "usuarios": """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
            """,
            "jogos": """
            CREATE TABLE IF NOT EXISTS jogos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                preco REAL NOT NULL,
                empresa TEXT NOT NULL,
                capa TEXT DEFAULT '',
                execution_path TEXT NOT NULL DEFAULT ''
            )
            """,
            "biblioteca": """
            CREATE TABLE IF NOT EXISTS biblioteca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                data_adicao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "amigos": """
            CREATE TABLE IF NOT EXISTS amigos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                nome TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """,
            "avaliacoes": """
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                nota INTEGER NOT NULL CHECK(nota BETWEEN 1 AND 5),
                data TEXT NOT NULL
            )
            """,
            "transacoes": """
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
            "carrinho": """
            CREATE TABLE IF NOT EXISTS carrinho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT NOT NULL,
                jogo_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 1,
                valor_unitario REAL NOT NULL,
                data_adicao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        }
        tabelas_por_perfil = {
            "completo": set(tabelas),
            "principal": {
                "usuarios",
                "jogos",
                "amigos",
                "transacoes",
                "carrinho",
            },
            "avaliacoes": {"avaliacoes"},
            "biblioteca": {"biblioteca"},
        }

        with self.conexao:
            for nome in tabelas_por_perfil[self.perfil]:
                self.conexao.execute(tabelas[nome])
            if self.perfil in {"completo", "principal"}:
                game_columns = {
                    row["name"]
                    for row in self.conexao.execute(
                        "PRAGMA table_info(jogos)"
                    ).fetchall()
                }
                if "execution_path" not in game_columns:
                    self.conexao.execute(
                        "ALTER TABLE jogos ADD COLUMN execution_path TEXT NOT NULL DEFAULT ''"
                    )
            if self.perfil == "principal":
                self.conexao.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_metadata (
                        chave TEXT PRIMARY KEY,
                        valor TEXT NOT NULL
                    )
                    """
                )

    def copiar_tabela_para(self, destino, tabela, colunas):
        colunas_por_tabela = {
            "avaliacoes": {"id", "usuario_email", "jogo_id", "nota", "data"},
            "biblioteca": {
                "id",
                "usuario_email",
                "jogo_id",
                "titulo",
                "data_adicao",
            },
        }
        if tabela not in colunas_por_tabela or not set(colunas).issubset(
            colunas_por_tabela[tabela]
        ):
            raise ValueError("Tabela ou colunas não permitidas para migração.")

        table_exists = self.conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (tabela,),
        ).fetchone()
        if table_exists is None:
            return 0

        column_list = ", ".join(colunas)
        placeholders = ", ".join("?" for _ in colunas)
        registros = self.conexao.execute(
            f"SELECT {column_list} FROM {tabela}"
        ).fetchall()
        if not registros:
            return 0

        destino.conexao.executemany(
            f"INSERT OR IGNORE INTO {tabela} ({column_list}) "
            f"VALUES ({placeholders})",
            [tuple(registro[coluna] for coluna in colunas) for registro in registros],
        )
        destino.conexao.commit()
        return len(registros)

    def fechar(self):
        self.conexao.close()

    @staticmethod
    def serializar_jogos(jogos):
        return json.dumps(jogos, ensure_ascii=False)

    @staticmethod
    def desserializar_jogos(valor):
        return json.loads(valor) if valor else []
