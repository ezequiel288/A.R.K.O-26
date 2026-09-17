import os
import time

class JogoBiblioteca:

    def __init__(self, jogoBIB):
        self.__jogoBIB = jogoBIB

    @classmethod
    def cadastrar(cls):
        print("\n=== ADICIONAR JOGO NA BIBLIOTECA ===")

        jogoBIB = input("Nome do jogo: ")

        return cls(jogoBIB)

    def get_jogoBIB(self):
        return self.__jogoBIB

    def set_jogoBIB(self, jogoBIB):
        if jogoBIB.strip() != "":
            self.__jogoBIB = jogoBIB
        else:
            print("Jogo inválido.")

    def alterar(self):
        print("\n=== ALTERAR JOGO DA BIBLIOTECA ===")

        novo_jogo = input("Novo jogo (ENTER para manter): ")

        if novo_jogo != "":
            self.set_jogoBIB(novo_jogo)

        print("Jogo alterado com sucesso.")

    def exibir_dados(self):
        return f"Jogo na Biblioteca: {self.__jogoBIB}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_jogos_biblioteca):
        """
        Lista todos os jogos da biblioteca.
        """
        print("\n=== LISTAR JOGOS DA BIBLIOTECA ===")

        if len(lista_jogos_biblioteca) == 0:
            print("Nenhum jogo cadastrado na biblioteca.")
            return

        for item in lista_jogos_biblioteca:
            print(item)

    def remover_jogo_biblioteca(self):
        """
        Remove um jogo da biblioteca.
        """

        print("\n=== REMOVER JOGO ===")

        nome = input("Digite o nome do jogo: ").strip()

        item = self.buscar_por_nome(nome)

        if item is None:
            print("Jogo não encontrado.")
            return

        self.__itens.remove(item)
        self.salvar_dados()

    print("Jogo removido com sucesso.")