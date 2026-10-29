class Jogo:
    def __init__(self, titulo, descricao, preco, empresa, capa="", id=None):
        self.id = id
        self.titulo = titulo
        self.descricao = descricao
        self.preco = preco
        self.empresa = empresa
        self.capa = capa

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["titulo"],
            row["descricao"],
            row["preco"],
            row["empresa"],
            row["capa"],
            row["id"],
        )

    def exibir_dados(self):
        return (
            f"Título: {self.titulo} | Descrição: {self.descricao} | "
            f"Preço: {self.preco} | Empresa: {self.empresa}"
        )

    def __str__(self):
        return self.exibir_dados()

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "preco": self.preco,
            "empresa": self.empresa,
            "capa": self.capa,
        }


class JogoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, jogo):
        cursor = self.conexao.execute(
            "INSERT INTO jogos (titulo, descricao, preco, empresa, capa) VALUES (?, ?, ?, ?, ?)",
            (jogo.titulo, jogo.descricao, jogo.preco, jogo.empresa, jogo.capa),
        )
        self.conexao.commit()
        jogo.id = cursor.lastrowid
        return jogo

    def listar(self):
        linhas = self.conexao.execute(
            "SELECT id, titulo, descricao, preco, empresa, capa FROM jogos ORDER BY id"
        ).fetchall()
        return [Jogo.from_row(linha) for linha in linhas]

    def buscar_por_id(self, id):
        linha = self.conexao.execute(
            "SELECT id, titulo, descricao, preco, empresa, capa FROM jogos WHERE id = ?",
            (id,),
        ).fetchone()
        return Jogo.from_row(linha)

    def buscar_por_titulo(self, titulo):
        linha = self.conexao.execute(
            "SELECT id, titulo, descricao, preco, empresa, capa FROM jogos WHERE titulo = ?",
            (titulo,),
        ).fetchone()
        return Jogo.from_row(linha)

    def atualizar(self, jogo):
        self.conexao.execute(
            "UPDATE jogos SET titulo = ?, descricao = ?, preco = ?, empresa = ?, capa = ? WHERE id = ?",
            (jogo.titulo, jogo.descricao, jogo.preco, jogo.empresa, jogo.capa, jogo.id),
        )
        self.conexao.commit()
        return jogo

    def excluir(self, id):
        self.conexao.execute("DELETE FROM jogos WHERE id = ?", (id,))
        self.conexao.commit()