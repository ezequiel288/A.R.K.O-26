import os
import time

class Jogo:

    def __init__(self, titulo, descricao, preco, empresa):
        self.__titulo = titulo
        self.__descricao = descricao
        self.__preco = preco
        self.__empresa = empresa

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR JOGO ===")

        titulo = input("Título: ")
        descricao = input("Descrição: ")
        preco = input("Preço: ")
        empresa = input("Empresa: ")

        return cls(titulo, descricao, preco, empresa)

    def get_titulo(self):
        return self.__titulo

    def set_titulo(self, titulo):
        if titulo.strip() != "":
            self.__titulo = titulo
        else:
            print("Título inválido.")

    def get_descricao(self):
        return self.__descricao

    def set_descricao(self, descricao):
        if descricao.strip() != "":
            self.__descricao = descricao
        else:
            print("Descrição inválida.")

    def get_preco(self):
        return self.__preco

    def set_preco(self, preco):
        if preco.strip() != "":
            self.__preco = preco
        else:
            print("Preço inválido.")

    def get_empresa(self):
        return self.__empresa

    def set_empresa(self, empresa):
        if empresa.strip() != "":
            self.__empresa = empresa
        else:
            print("Empresa inválida.")

    def alterar(self):
        print("\n=== ALTERAR JOGO ===")

        novo_titulo = input("Novo título (ENTER para manter): ")
        if novo_titulo != "":
            self.set_titulo(novo_titulo)

        nova_descricao = input("Nova descrição (ENTER para manter): ")
        if nova_descricao != "":
            self.set_descricao(nova_descricao)

        novo_preco = input("Novo preço (ENTER para manter): ")
        if novo_preco != "":
            self.set_preco(novo_preco)

        nova_empresa = input("Nova empresa (ENTER para manter): ")
        if nova_empresa != "":
            self.set_empresa(nova_empresa)

        print("Jogo alterado com sucesso.")

    def exibir_dados(self):
        return f"Título: {self.__titulo} | Descrição: {self.__descricao} | Preço: {self.__preco} | Empresa: {self.__empresa}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_jogos):
        """
        Lista todos os jogos cadastrados.
        """
        print("\n=== LISTAR JOGOS ===")

        if len(lista_jogos) == 0:
            print("Nenhum jogo cadastrado.")
            return

        for jogo in lista_jogos:
            print(jogo)

    def remover_jogo(self):
        """
        Remove um jogo pelo título.
        """

        print("\n=== REMOVER JOGO ===")

        titulo = input("Digite o título: ").strip()

        jogo = self.buscar_por_titulo(titulo)

        if jogo is None:
            print("Jogo não encontrado.")
            return

        self.__jogos.remove(jogo)
        self.salvar_dados()

    print("Jogo removido com sucesso.")