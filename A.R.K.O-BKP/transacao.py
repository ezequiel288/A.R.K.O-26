import os
import time

class Transacao:

    def __init__(self, transacao, jogocomprado):
        self.__transacao = transacao
        self.__jogocomprado = jogocomprado

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR TRANSAÇÃO ===")

        transacao = input("Tipo de transação: ")
        jogocomprado = input("Jogo comprado: ")

        return cls(transacao, jogocomprado)

    def get_transacao(self):
        return self.__transacao

    def set_transacao(self, transacao):
        if transacao.strip() != "":
            self.__transacao = transacao
        else:
            print("Transação inválida.")

    def get_jogocomprado(self):
        return self.__jogocomprado

    def set_jogocomprado(self, jogocomprado):
        if jogocomprado.strip() != "":
            self.__jogocomprado = jogocomprado
        else:
            print("Jogo inválido.")

    def alterar(self):
        print("\n=== ALTERAR TRANSAÇÃO ===")

        nova_transacao = input("Nova transação (ENTER para manter): ")
        if nova_transacao != "":
            self.set_transacao(nova_transacao)

        novo_jogo = input("Novo jogo comprado (ENTER para manter): ")
        if novo_jogo != "":
            self.set_jogocomprado(novo_jogo)

        print("Transação alterada com sucesso.")

    def exibir_dados(self):
        return f"Transação: {self.__transacao} | Jogo comprado: {self.__jogocomprado}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_transacoes):
        """
        Lista todas as transações cadastradas.
        """
        print("\n=== LISTAR TRANSAÇÕES ===")

        if len(lista_transacoes) == 0:
            print("Nenhuma transação cadastrada.")
            return

        for transacao in lista_transacoes:
            print(transacao)
    
    def remover_transacao(self):
        """
        Remove uma transação pelo ID.
        """

        print("\n=== REMOVER TRANSAÇÃO ===")

        id_transacao = input("Digite o ID da transação: ").strip()

        transacao = self.buscar_por_id(id_transacao)

        if transacao is None:
            print("Transação não encontrada.")
            return

        self.__transacoes.remove(transacao)
        self.salvar_dados()

    print("Transação removida com sucesso.")

