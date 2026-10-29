class Usuario:
    def __init__(self, nome, email, senha, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(row["nome"], row["email"], row["senha"], row["id"])

    def exibir_dados(self):
        return f"Nome: {self.nome} | Email: {self.email}"

    def __str__(self):
        return self.exibir_dados()

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "senha": self.senha,
        }


class UsuarioRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, usuario):
        cursor = self.conexao.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (usuario.nome, usuario.email, usuario.senha),
        )
        self.conexao.commit()
        usuario.id = cursor.lastrowid
        return usuario

    def listar(self):
        linhas = self.conexao.execute(
            "SELECT id, nome, email, senha FROM usuarios ORDER BY id"
        ).fetchall()
        return [Usuario.from_row(linha) for linha in linhas]

    def buscar_por_id(self, id):
        linha = self.conexao.execute(
            "SELECT id, nome, email, senha FROM usuarios WHERE id = ?",
            (id,),
        ).fetchone()
        return Usuario.from_row(linha)

    def buscar_por_email(self, email):
        linha = self.conexao.execute(
            "SELECT id, nome, email, senha FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        return Usuario.from_row(linha)

    def atualizar(self, usuario):
        self.conexao.execute(
            "UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?",
            (usuario.nome, usuario.email, usuario.senha, usuario.id),
        )
        self.conexao.commit()
        return usuario

    def excluir(self, id):
        self.conexao.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        self.conexao.commit()

    def autenticar(self, email, senha):
        usuario = self.buscar_por_email(email)
        if usuario is None:
            return None
        if usuario.senha == senha:
            return usuario
        return None

