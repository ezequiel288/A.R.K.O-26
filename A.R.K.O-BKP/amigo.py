import os
import time

class Amigo:
    def __init__(self, emailamigo, nomeamigo):
        self.__emailamigo = emailamigo
        self.__nomeamigo = nomeamigo

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR AMIGO ===")
        emailamigo = input("Email do amigo: ")
        nomeamigo = input("Nome do amigo: ")
        return cls(emailamigo, nomeamigo)

    def get_emailamigo(self):
        return self.__emailamigo

    def set_emailamigo(self, emailamigo):
        if emailamigo.strip() != "":
            self.__emailamigo = emailamigo
        else:
            print("Email inválido.")

    def get_nomeamigo(self):
        return self.__nomeamigo

    def set_nomeamigo(self, nomeamigo):
        if nomeamigo.strip() != "":
            self.__nomeamigo = nomeamigo
        else:
            print("Nome inválido.")

    def alterar(self):
        print("\n=== ALTERAR AMIGO ===")
        novo_email = input("Novo email (ENTER para manter): ")
        if novo_email != "":
            self.set_emailamigo(novo_email)
        novo_nome = input("Novo nome (ENTER para manter): ")
        if novo_nome != "":
            self.set_nomeamigo(novo_nome)
        print("Amigo alterado com sucesso.")

    def exibir_dados(self):
        return f"Email do Amigo: {self.__emailamigo} | Nome do Amigo: {self.__nomeamigo}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_amigos):
        print("\n=== LISTAR AMIGOS ===")
        if len(lista_amigos) == 0:
            print("Nenhum amigo cadastrado.")
            return
        for amigo in lista_amigos:
            print(amigo)

    @staticmethod
    def remover_amigo(lista_amigos, email_alvo):
        print("\n=== REMOVER AMIGO ===")
        for amigo in lista_amigos:
            if amigo.get_emailamigo() == email_alvo:
                lista_amigos.remove(amigo)
                print(f"Amigo {amigo.get_nomeamigo()} removido com sucesso.")
                return
        print("Amigo não encontrado na lista.")
