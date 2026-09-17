import os
import time
from pathlib import Path
import csv

# --------------------------------
# CONFIGURAÇÃO DO ARQUIVO
# --------------------------------

DIRETORIO_DADOS = Path("dados")

DIRETORIO_DADOS.mkdir(exist_ok=True)

ARQUIVO_usuario = DIRETORIO_DADOS / "usuario.csv"

class Usuario:

    def __init__(self, nome, email, senha):
        self.__nome = nome
        self.__email = email
        self.__senha = senha

    @classmethod
    def cadastrar(cls):
        print("\n=== CADASTRAR USUÁRIO ===")

        nome = input("Nome: ")
        email = input("Email: ")
        senha = input("Senha: ")

        return cls(nome, email, senha)

    def get_nome(self):
        return self.__nome

    def set_nome(self, nome):
        if nome.strip() != "":
            self.__nome = nome
        else:
            print("Nome inválido.")

    def get_email(self):
        return self.__email

    def set_email(self, email):
        if email.strip() != "":
            self.__email = email
        else:
            print("Email inválido.")

    def get_senha(self):
        return self.__senha

    def set_senha(self, senha):
        if senha.strip() != "":
            self.__senha = senha
        else:
            print("Senha inválida.")

    def alterar(self):
        print("\n=== ALTERAR USUÁRIO ===")

        novo_nome = input("Novo nome (ENTER para manter): ").strip()
        if novo_nome != "":
            self.set_nome(novo_nome)

        novo_email = input("Novo email (ENTER para manter): ").strip()
        if novo_email != "":
            self.set_email(novo_email)

        nova_senha = input("Nova senha (ENTER para manter): ").strip()
        if nova_senha != "":
            self.set_senha(nova_senha)

        print("Usuário alterado com sucesso.")

    def exibir_dados(self):
        return f"Nome: {self.__nome} | Email: {self.__email} | Senha: {self.__senha}"

    def __str__(self):
        return self.exibir_dados()

    @staticmethod
    def listar(lista_usuarios):
        """
        Lista todos os usuários cadastrados.

        CONCEITO: POLIMORFISMO
        --------------------------------------------------------
        A lista pode conter objetos Usuario e suas subclasses.
        Quando usamos print(usuario), cada objeto executa sua própria
        versão de exibir_dados() através do método __str__.
        """
        print("\n=== LISTAR USUÁRIOS ===")

        if len(lista_usuarios) == 0:
            print("Nenhum usuário cadastrado.")
            return

        for usuario in lista_usuarios:
            print(usuario)

    def remover_usuario(self):
        """
        Remove um usuário pelo e-mail.
        """

        print("\n=== REMOVER USUÁRIO ===")

        email = input("Digite o e-mail: ").strip()

        usuario = self.buscar_por_email(email)

        if usuario is None:
            print ("Usuário não encontrado.")
            return

        self.__usuarios.remove(usuario)
        self.salvar_dados()

        print("Usuário removido com sucesso.")

    def para_csv(self):
        return [
            self.nome,
            self.senha,
            self.email
        ]
    



    # --------------------------------
    # SALVAR
    # --------------------------------

    def salvar_usuarios(usuarios):

        with open(ARQUIVO_usuario, 
            "w",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            escritor = csv.writer(arquivo)

            escritor.writerow(
                ["nome", "senha", "email"]
            )

            for usuario in usuario:
                escritor.writerow(
                    usuario.para_csv()
                )

        print("\nDados salvos com sucesso!") 

    # --------------------------------
    # CARREGAR
    # --------------------------------

    def carregar_usuarios():

        usuarios = []

        # Verifica se o arquivo existe
        if not ARQUIVO_usuario.exists():
            return usuarios

        with open(
            ARQUIVO_usuario,
            "r",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            leitor = csv.reader(arquivo)

            # Ignora o cabeçalho
            next(leitor, None)

            for linha in leitor:

                nome = linha[0]
                senha = linha[1]
                email = linha[2]

            usuario = Usuario(
                    nome,
                    senha,
                    email
                )

            usuario.append(usuario)

        return usuarios




