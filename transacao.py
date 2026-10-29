import json


class Transacao:
    def __init__(self, usuario_email, tipo, jogos, valor, data, id=None, valor_pago=None, compra_id=None):
        self.id = id
        self.usuario_email = usuario_email
        self.tipo = tipo
        self.jogos = jogos or []
        self.valor = valor
        self.valor_pago = valor_pago
        self.data = data
        self.compra_id = compra_id

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["usuario_email"],
            row["tipo"],
            json.loads(row["jogos"]),
            row["valor"],
            row["data"],
            row["id"],
            row["valor_pago"],
            row["compra_id"],
        )

    def exibir_dados(self):
        return f"Usuário: {self.usuario_email} | Tipo: {self.tipo} | Valor: {self.valor}"

    def __str__(self):
        return self.exibir_dados()

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario_email,
            "tipo": self.tipo,
            "jogos": self.jogos,
            "valor": self.valor,
            "valor_pago": self.valor_pago,
            "data": self.data,
            "compra_id": self.compra_id,
        }


class TransacaoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    def inserir(self, transacao):
        self.conexao.execute(
            "INSERT INTO transacoes (id, usuario_email, tipo, jogos, valor, valor_pago, data, compra_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                transacao.id,
                transacao.usuario_email,
                transacao.tipo,
                json.dumps(transacao.jogos, ensure_ascii=False),
                transacao.valor,
                transacao.valor_pago,
                transacao.data,
                transacao.compra_id,
            ),
        )
        self.conexao.commit()
        return transacao

    def listar(self):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, tipo, jogos, valor, valor_pago, data, compra_id FROM transacoes ORDER BY data DESC"
        ).fetchall()
        return [Transacao.from_row(linha) for linha in linhas]

    def listar_por_usuario(self, usuario_email):
        linhas = self.conexao.execute(
            "SELECT id, usuario_email, tipo, jogos, valor, valor_pago, data, compra_id FROM transacoes WHERE usuario_email = ? ORDER BY data DESC",
            (usuario_email,),
        ).fetchall()
        return [Transacao.from_row(linha) for linha in linhas]

    def buscar_por_id(self, id):
        linha = self.conexao.execute(
            "SELECT id, usuario_email, tipo, jogos, valor, valor_pago, data, compra_id FROM transacoes WHERE id = ?",
            (id,),
        ).fetchone()
        return Transacao.from_row(linha)

    def excluir(self, id):
        self.conexao.execute("DELETE FROM transacoes WHERE id = ?", (id,))
        self.conexao.commit()

