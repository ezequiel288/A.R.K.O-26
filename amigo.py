class Amigo:
    def __init__(self, usuario_email, nome, email, id=None):
        self.id = id
        self.usuario_email = usuario_email
        self.nome = nome
        self.email = email

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["usuario_email"],
            row["nome"],
            row["email"],
            row["id"],
        )

    def exibir_dados(self):
        return f"Nome: {self.nome} | Email: {self.email}"

    def __str__(self):
        return self.exibir_dados()


class AmigoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, amigo):
        cursor = self.conexao.execute(
            "INSERT INTO amigos (usuario_email, nome, email) VALUES (?, ?, ?)",
            (amigo.usuario_email, amigo.nome, amigo.email),
        )
        self.conexao.commit()
        amigo.id = cursor.lastrowid
        return amigo

    def listar_por_usuario(self, usuario_email):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, nome, email FROM amigos WHERE usuario_email = ? ORDER BY nome",
            (usuario_email,),
        ).fetchall()
        return [Amigo.from_row(linha) for linha in linhas]

    def buscar_por_email(self, usuario_email, email):
        linha = self.conexao.execute(
            "SELECT id, usuario_email, nome, email FROM amigos WHERE usuario_email = ? AND email = ?",
            (usuario_email, email),
        ).fetchone()
        return Amigo.from_row(linha)

    def atualizar(self, amigo):
        self.conexao.execute(
            "UPDATE amigos SET nome = ?, email = ? WHERE id = ?",
            (amigo.nome, amigo.email, amigo.id),
        )
        self.conexao.commit()
        return amigo

    def excluir(self, id):
        self.conexao.execute("DELETE FROM amigos WHERE id = ?", (id,))
        self.conexao.commit()

