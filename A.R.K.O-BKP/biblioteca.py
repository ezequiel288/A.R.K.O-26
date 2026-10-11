import os
import time

class Biblioteca:

    def __init__(self, donousu):
        self.__donousu = donousu

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR BIBLIOTECA ===")

        donousu = input("Dono da biblioteca: ")

        return cls(donousu)

    def get_donousu(self):
        return self.__donousu

    def set_donousu(self, donousu):
        if donousu.strip() != "":
            self.__donousu = donousu
        else:
            print("Dono inválido.")

    def alterar(self):
        print("\n=== ALTERAR BIBLIOTECA ===")

        novo_donousu = input("Novo dono (ENTER para manter): ")

        if novo_donousu != "":
            self.set_donousu(novo_donousu)

        print("Biblioteca alterada com sucesso.")

    def exibir_dados(self):
        return f"Dono da Biblioteca: {self.__donousu}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_bibliotecas):
        """
        Lista todas as bibliotecas cadastradas.
        """
        print("\n=== LISTAR BIBLIOTECAS ===")

        if len(lista_bibliotecas) == 0:
            print("Nenhuma biblioteca cadastrada.")
            return

        for biblioteca in lista_bibliotecas:
            print(biblioteca)

    def remover_biblioteca(self):
        """
        Remove um item da biblioteca.
        """

        print("\n=== REMOVER ITEM DA BIBLIOTECA ===")

        item = input("Digite o nome do item: ").strip()

        biblioteca = self.buscar_por_item(item)

        if biblioteca is None:
            print("Item não encontrado.")
            return

        self.__bibliotecas.remove(biblioteca)
        self.salvar_dados()

    print("Item removido com sucesso.")
