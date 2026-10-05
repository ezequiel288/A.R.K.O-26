import os
import time
from pathlib import Path
import csv

from usuario import *
from jogo import *
from biblioteca import *
from amigo import *
from jogobiblioteca import *
from carrinho import *
from transacao import *
from avaliacao import *

# ──────────────────────────────────────────
#  LISTAS DE ARMAZENAMENTO GLOBAL
# ──────────────────────────────────────────

usuarios = []
jogos = []
bibliotecas = []
jogosbiblioteca = []
carrinhos = []
avaliacoes = []
amigos = []
transacoes = []


#──────────────────────────────────────────
#  SUBMENU — USUÁRIOS
# ──────────────────────────────────────────

def menu_usuario():
    limpar_tela()
    usuarios = carregar_usuarios()
    print(f"\n{len(usuarios)} usuario(s) carregado(s).")

    while True:
        print("\n" + "="*40)
        print("           MENU USUÁRIOS")
        print("="*40)
        print("1 - Cadastrar Usuário")
        print("2 - Alterar usuário")
        print("3 - Listar usuários")
        print("4 - Salvar usuários")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            usuario = Usuario.cadastrar()
            usuarios.append(usuario)
            print("Usuário cadastrado com sucesso.")

        elif opcao == "2":
            if len(usuarios) > 0:
                for i, usuario in enumerate(usuarios):
                    print(i, "-", usuario)

                escolha = int(input("Escolha o usuário: "))
                usuarios[escolha].alterar()

            else:
                print("Nenhum usuário cadastrado.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de usuários:", len(usuarios))

            for usuario in usuarios:
                print(usuario)

            input("\nPressione ENTER para voltar...")

        
        elif opcao == "4":

            salvar_usuarios(usuarios)


        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")


# ──────────────────────────────────────────
#  SUBMENU — JOGOS
# ──────────────────────────────────────────
def menu_jogo():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU JOGOS")
        print("="*40)
        print("1 - Cadastrar Jogos")
        print("2 - Alterar Jogos")
        print("3 - Listar Jogos")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            jogo = Jogo.cadastrar()
            jogos.append(jogo)
            print("Jogo cadastrado com sucesso.")

        elif opcao == "2":
            if len(jogos) > 0:
                for i, jogo in enumerate(jogos):
                    print(i, "-", jogo)

                escolha = int(input("Escolha o jogo: "))
                jogos[escolha].alterar()

            else:
                print("Nenhum jogo cadastrado.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de jogos:", len(jogos))

            for jogo in jogos:
                print(jogo)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")

# ──────────────────────────────────────────
#  SUBMENU — BIBLIOTECA
# ──────────────────────────────────────────
def menu_biblioteca():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU BIBLIOTECA")
        print("="*40)
        print("1 - Cadastrar Biblioteca")
        print("2 - Alterar Biblioteca")
        print("3 - Listar Bibliotecas")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            biblioteca = Biblioteca.cadastrar()
            bibliotecas.append(biblioteca)
            print("Biblioteca cadastrada com sucesso.")

        elif opcao == "2":
            if len(bibliotecas) > 0:
                for i, biblioteca in enumerate(bibliotecas):
                    print(i, "-", biblioteca)

                escolha = int(input("Escolha a biblioteca: "))
                bibliotecas[escolha].alterar()

            else:
                print("Nenhuma biblioteca cadastrada.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de bibliotecas:", len(bibliotecas))

            for biblioteca in bibliotecas:
                print(biblioteca)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")
        print("2 - Alterar biblioteca")
        print("3 - Listar bibliotecas")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            biblioteca = Biblioteca.cadastrar()
            bibliotecas.append(biblioteca)
            print("Biblioteca cadastrada com sucesso.")

        elif opcao == "2":
            if len(bibliotecas) > 0:
                for i, biblioteca in enumerate(bibliotecas):
                    print(i, "-", biblioteca)

                escolha = int(input("Escolha a biblioteca: "))
                bibliotecas[escolha].alterar()

            else:
                print("Nenhuma biblioteca cadastrada.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de bibliotecas:", len(bibliotecas))

            for biblioteca in bibliotecas:
                print(biblioteca)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")

# ──────────────────────────────────────────
#  SUBMENU — CARRINHO
# ──────────────────────────────────────────
def menu_carrinho():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU CARRINHO")
        print("="*40)
        print("1 - Adicionar ao Carrinho")
        print("2 - Remover do Carrinho")
        print("3 - Listar Itens no Carrinho")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            carrinho = Carrinho.cadastrar()
            carrinho.append(carrinho)
            print("Carrinho adicionado ao carrinho com sucesso.")

        elif opcao == "2":
            if len(carrinho) > 0:
                for i, carrinho in enumerate(carrinho):
                    print(i, "-", carrinho)

                escolha = int(input("Escolha o carrinho: "))
                carrinho.pop(escolha)
                print("Carrinho removido do carrinho com sucesso.")

            else:
                print("Nenhum carrinho no carrinho.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de carrinhos:", len(carrinho))

            for carrinho in carrinho:
                print(carrinho)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")
        print("2 - Alterar Carrinho")
        print("3 - Listar Carrinhos")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            carrinho = Carrinho.cadastrar()
            carrinho.append(carrinho)
            print("Carrinho cadastrado com sucesso.")

        elif opcao == "2":
            if len(carrinho) > 0:
                for i, carrinho in enumerate(carrinho):
                    print(i, "-", carrinho)

                escolha = int(input("Escolha o carrinho: "))
                carrinho[escolha].alterar()

            else:
                print("Nenhum carrinho cadastrado.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de carrinhos:", len(carrinho))

            for carrinho in carrinho:
                print(carrinho)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")


# ──────────────────────────────────────────
#  SUBMENU — AVALIAÇÕES
# ──────────────────────────────────────────

def menu_avaliacoes():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU AVALIAÇÕES")
        print("="*40)
        print("1 - Cadastrar Avaliação")
        print("2 - Alterar avaliação")
        print("3 - Listar avaliações")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            avaliacao = Avaliacao.cadastrar()
            avaliacoes.append(avaliacao)
            print("Avaliação cadastrada com sucesso.")

        elif opcao == "2":
            if len(avaliacoes) > 0:
                for i, avaliacao in enumerate(avaliacoes):
                    print(i, "-", avaliacao)

                escolha = int(input("Escolha a avaliação: "))
                avaliacoes[escolha].alterar()

            else:
                print("Nenhuma avaliação cadastrada.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de avaliações:", len(avaliacoes))

            for avaliacao in avaliacoes:
                print(avaliacao)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")

# ──────────────────────────────────────────
#  SUBMENU — AMIGOS
# ──────────────────────────────────────────
def menu_amigos():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU AMIGOS")
        print("="*40)
        print("1 - Cadastrar Amigo")
        print("2 - Alterar Amigo")
        print("3 - Listar Amigos")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            amigo = Amigo.cadastrar()
            amigos.append(amigo)
            print("Amigo cadastrado com sucesso.")

        elif opcao == "2":
            if len(amigos) > 0:
                for i, amigo in enumerate(amigos):
                    print(i, "-", amigo)

                escolha = int(input("Escolha o amigo: "))
                amigos[escolha].alterar()

            else:
                print("Nenhum amigo cadastrado.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de amigos:", len(amigos))

            for amigo in amigos:
                print(amigo)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")

# ──────────────────────────────────────────
#  SUBMENU — TRANSAÇÕES
# ──────────────────────────────────────────
def menu_transacoes():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU TRANSAÇÕES")
        print("="*40)
        print("1 - Cadastrar Transação")
        print("2 - Alterar Transação")
        print("3 - Listar Transações")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            transacao = Transacao.cadastrar()
            transacoes.append(transacao)
            print("Transação cadastrada com sucesso.")

        elif opcao == "2":
            if len(transacoes) > 0:
                for i, transacao in enumerate(transacoes):
                    print(i, "-", transacao)

                escolha = int(input("Escolha a transação: "))
                transacoes[escolha].alterar()

            else:
                print("Nenhuma transação cadastrada.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de transações:", len(transacoes))

            for transacao in transacoes:
                print(transacao)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")

def menu_jogosbiblioteca():
    limpar_tela()
    while True:
        print("\n" + "="*40)
        print("           MENU TRANSAÇÕES")
        print("="*40)
        print("1 - Cadastrar Transação")
        print("2 - Alterar Transação")
        print("3 - Listar Transações")
        print("0 - Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            jogosbiblioteca = JogoBiblioteca.cadastrar()
            jogosbiblioteca.append(jogosbiblioteca)
            print("Jogo adicionado a Biblioteca com sucesso.")

        elif opcao == "2":
            if len(jogosbiblioteca) > 0:
                for i, jogosbiblioteca in enumerate(jogosbiblioteca):
                    print(i, "-", jogosbiblioteca)

                escolha = int(input("Escolha o Jogo na Biblioteca: "))
                jogosbiblioteca[escolha].alterar()

            else:
                print("Nenhum Jogo adicionado na Biblioteca.")

        elif opcao == "3":
            print("Entrou na opção 3")
            print("Quantidade de Jogos na Biblioteca:", len(jogosbiblioteca))

            for jogosbiblioteca in jogosbiblioteca:
                print(jogosbiblioteca)

            input("\nPressione ENTER para voltar...")

        elif opcao == "0":
            limpar_tela()
            break

        else:
            print("Opção inválida.")


def limpar_tela():
# Verifica o sistema operacional ('nt' é o Windows)
    if os.name == 'nt':
            os.system('cls')
    else:
            os.system('clear')
    

# ──────────────────────────────────────────
#  MENU PRINCIPAL
# ──────────────────────────────────────────
    
def main():
    limpar_tela()
    
    while True:
        print("\n" + "="*50)
        print("       SISTEMA DE DISTRIBUIÇÃO DE JOGOS A.R.K.O")
        print("="*50)

        print("1 - Usuários")
        print("2 - Jogos")
        print("3 - Biblioteca")
        print("4 - Carrinho")
        print("5 - Avaliações")
        print("6 - Amigos")
        print("7 - Transações")
        print("8 - Jogos na Biblioteca")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            menu_usuario()
        
        elif opcao == "2":
            menu_jogo()
        
        elif opcao == "3":
            menu_biblioteca()

        elif opcao == "4":
            menu_carrinho() 

        elif opcao == "5":
            menu_avaliacoes()

        elif opcao == "6":
            menu_amigos()

        elif opcao == "7":
            menu_transacoes()

        elif opcao == "8":
            menu_jogosbiblioteca()        

        elif opcao == "0":
            limpar_tela()
            print("PROGRAMA FINALIZANDO. POR FAVOR, AGUARDE", end="")
            for i in range(3):
                print(".", end="", flush=True)
                time.sleep(1)
            limpar_tela()
            print("PROGRAMA FINALIZADO COM SUCESSO!!!\n")
            break

        else:
            print("Função não implementada ou inválida.")

if __name__ == "__main__":
    main()



