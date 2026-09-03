import os
import time

class Carrinho:

    def __init__(self, usuario, jogoad, total):
        self.__usuario = usuario
        self.__jogoad = jogoad
        self.__total = total

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR CARRINHO ===")

        usuario = input("Usuário: ")
        jogoad = input("Jogo adicionado: ")
        total = input("Total: ")

        return cls(usuario, jogoad, total)

    def get_usuario(self):
        return self.__usuario

    def set_usuario(self, usuario):
        if usuario.strip() != "":
            self.__usuario = usuario
        else:
            print("Usuário inválido.")

    def get_jogoad(self):
        return self.__jogoad

    def set_jogoad(self, jogoad):
        if jogoad.strip() != "":
            self.__jogoad = jogoad
        else:
            print("Jogo inválido.")

    def get_total(self):
        return self.__total

    def set_total(self, total):
        if total.strip() != "":
            self.__total = total
        else:
            print("Total inválido.")

    def alterar(self):
        print("\n=== ALTERAR CARRINHO ===")

        novo_usuario = input("Novo usuário (ENTER para manter): ")
        if novo_usuario != "":
            self.set_usuario(novo_usuario)

        novo_jogo = input("Novo jogo (ENTER para manter): ")
        if novo_jogo != "":
            self.set_jogoad(novo_jogo)

        novo_total = input("Novo total (ENTER para manter): ")
        if novo_total != "":
            self.set_total(novo_total)

        print("Carrinho alterado com sucesso.")

    def exibir_dados(self):
        return f"Usuário: {self.__usuario} | Jogo: {self.__jogoad} | Total: {self.__total}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_carrinhos):
        """
        Lista todos os carrinhos cadastrados.
        """
        print("\n=== LISTAR CARRINHOS ===")

        if len(lista_carrinhos) == 0:
            print("Nenhum carrinho cadastrado.")
            return

        for carrinho in lista_carrinhos:
            print(carrinho)

    def remover_carrinho(self):
        """
        Remove um jogo do carrinho.
        """

        print("\n=== REMOVER JOGO DO CARRINHO ===")

        titulo = input("Digite o título do jogo: ").strip()

        carrinho = self.buscar_por_titulo(titulo)

        if carrinho is None:
            print("Jogo não encontrado no carrinho.")
            return

        self.__carrinhos.remove(carrinho)
        self.salvar_dados()

    print("Jogo removido do carrinho com sucesso.")
