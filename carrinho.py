class Carrinho:
    def __init__(self, usuario_email, jogo_id, valor_unitario, quantidade=1, id=None):
        self.id = id
        self.usuario_email = usuario_email
        self.jogo_id = jogo_id
        self.valor_unitario = valor_unitario
        self.quantidade = quantidade

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["usuario_email"],
            row["jogo_id"],
            row["valor_unitario"],
            row["quantidade"],
            row["id"],
        )

    def exibir_dados(self):
        return (
            f"Usuário: {self.usuario_email} | Jogo: {self.jogo_id} | "
            f"Quantidade: {self.quantidade} | Valor: {self.valor_unitario}"
        )

    def __str__(self):
        return self.exibir_dados()


class CarrinhoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, item):
        cursor = self.conexao.execute(
            "INSERT INTO carrinho (usuario_email, jogo_id, quantidade, valor_unitario) VALUES (?, ?, ?, ?)",
            (item.usuario_email, item.jogo_id, item.quantidade, item.valor_unitario),
        )
        self.conexao.commit()
        item.id = cursor.lastrowid
        return item

    def listar_por_usuario(self, usuario_email):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, jogo_id, quantidade, valor_unitario FROM carrinho WHERE usuario_email = ? ORDER BY id",
            (usuario_email,),
        ).fetchall()
        return [Carrinho.from_row(linha) for linha in linhas]

    def atualizar(self, item):
        self.conexao.execute(
            "UPDATE carrinho SET quantidade = ?, valor_unitario = ? WHERE id = ?",
            (item.quantidade, item.valor_unitario, item.id),
        )
        self.conexao.commit()
        return item

    def excluir(self, id):
        self.conexao.execute("DELETE FROM carrinho WHERE id = ?", (id,))
        self.conexao.commit()

    def limpar_usuario(self, usuario_email):
        self.conexao.execute("DELETE FROM carrinho WHERE usuario_email = ?", (usuario_email,))
        self.conexao.commit()
