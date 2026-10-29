class Biblioteca:
    def __init__(self, usuario_email, jogo_id, titulo, id=None):
        self.id = id
        self.usuario_email = usuario_email
        self.jogo_id = jogo_id
        self.titulo = titulo

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["usuario_email"],
            row["jogo_id"],
            row["titulo"],
            row["id"],
        )

    def exibir_dados(self):
        return f"Usuário: {self.usuario_email} | Jogo: {self.titulo}"

    def __str__(self):
        return self.exibir_dados()


class BibliotecaRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, biblioteca):
        cursor = self.conexao.execute(
            "INSERT INTO biblioteca (usuario_email, jogo_id, titulo) VALUES (?, ?, ?)",
            (biblioteca.usuario_email, biblioteca.jogo_id, biblioteca.titulo),
        )
        self.conexao.commit()
        biblioteca.id = cursor.lastrowid
        return biblioteca

    def listar_por_usuario(self, usuario_email):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, jogo_id, titulo FROM biblioteca WHERE usuario_email = ? ORDER BY id",
            (usuario_email,),
        ).fetchall()
        return [Biblioteca.from_row(linha) for linha in linhas]

    def remover(self, usuario_email, jogo_id):
        self.conexao.execute(
            "DELETE FROM biblioteca WHERE usuario_email = ? AND jogo_id = ?",
            (usuario_email, jogo_id),
        )
        self.conexao.commit()
