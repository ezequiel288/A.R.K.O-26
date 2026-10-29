class Avaliacao:
    def __init__(self, usuario_email, jogo_id, nota, data, id=None):
        self.id = id
        self.usuario_email = usuario_email
        self.jogo_id = jogo_id
        self.nota = nota
        self.data = data

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["usuario_email"],
            row["jogo_id"],
            row["nota"],
            row["data"],
            row["id"],
        )

    def exibir_dados(self):
        return f"Usuário: {self.usuario_email} | Jogo: {self.jogo_id} | Nota: {self.nota}"

    def __str__(self):
        return self.exibir_dados()


class AvaliacaoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, avaliacao):
        cursor = self.conexao.execute(
            "INSERT INTO avaliacoes (usuario_email, jogo_id, nota, data) VALUES (?, ?, ?, ?)",
            (avaliacao.usuario_email, avaliacao.jogo_id, avaliacao.nota, avaliacao.data),
        )
        self.conexao.commit()
        avaliacao.id = cursor.lastrowid
        return avaliacao

    def listar(self):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, jogo_id, nota, data FROM avaliacoes ORDER BY data DESC"
        ).fetchall()
        return [Avaliacao.from_row(linha) for linha in linhas]

    def buscar_por_usuario_e_jogo(self, usuario_email, jogo_id):
        linha = self.conexao.execute(
            "SELECT id, usuario_email, jogo_id, nota, data FROM avaliacoes WHERE usuario_email = ? AND jogo_id = ?",
            (usuario_email, jogo_id),
        ).fetchone()
        return Avaliacao.from_row(linha)

    def atualizar(self, avaliacao):
        self.conexao.execute(
            "UPDATE avaliacoes SET nota = ?, data = ? WHERE id = ?",
            (avaliacao.nota, avaliacao.data, avaliacao.id),
        )
        self.conexao.commit()
        return avaliacao

    def excluir(self, id):
        self.conexao.execute("DELETE FROM avaliacoes WHERE id = ?", (id,))
        self.conexao.commit()
