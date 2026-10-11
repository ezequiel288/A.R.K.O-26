import os
import time

class Avaliacao:

    def __init__(self, avaliacao):
        self.__avaliacao = avaliacao

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR AVALIAÇÃO ===")

        avaliacao = input("Digite sua avaliação (0 a 5): ")

        return cls(avaliacao)

    def get_avaliacao(self):
        return self.__avaliacao

    def set_avaliacao(self, avaliacao):
        if avaliacao.strip() != "":
            self.__avaliacao = avaliacao
        else:
            print("Avaliação inválida.")

    def alterar(self):
        print("\n=== ALTERAR AVALIAÇÃO ===")

        nova_avaliacao = input("Nova avaliação (ENTER para manter): ")

        if nova_avaliacao != "":
            self.set_avaliacao(nova_avaliacao)

        print("Avaliação alterada com sucesso.")

    def exibir_dados(self):
        return f"Minha avaliação: {self.__avaliacao}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_avaliacoes):
        """
        Lista todas as avaliações cadastradas.
        """
        print("\n=== LISTAR AVALIAÇÕES ===")

        if len(lista_avaliacoes) == 0:
            print("Nenhuma avaliação cadastrada.")
            return

        for avaliacao in lista_avaliacoes:
            print(avaliacao)

    def remover_avaliacao(self):
        """
        Remove uma avaliação.
        """

        print("\n=== REMOVER AVALIAÇÃO ===")

        id_avaliacao = input("Digite o ID da avaliação: ").strip()

        avaliacao = self.buscar_por_id(id_avaliacao)

        if avaliacao is None:
            print("Avaliação não encontrada.")
            return

        self.__avaliacoes.remove(avaliacao)
        self.salvar_dados()

    print("Avaliação removida com sucesso.")
