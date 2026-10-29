"""
CRUD de Alunos com Python, POO e SQLite3
Aula: Persistência de dados em banco de dados

Estrutura (cada classe tem UMA responsabilidade):
    Aluno             -> representa o dado (o "molde" do aluno)
    BancoDeDados      -> cuida da conexão e da criação da tabela
    AlunoRepositorio  -> faz o CRUD (comandos SQL)
    Menu              -> conversa com o usuário (input/print)
"""

import sqlite3


# ----------------------------------------------------------------------
# 1) MODELO: a classe que representa o objeto do mundo real
# ----------------------------------------------------------------------
class Aluno:
    def __init__(self, nome, idade, turma, id=None):
        self.id = id          # o banco gera o id automaticamente
        self.nome = nome
        self.idade = idade
        self.turma = turma

    def __str__(self):
        return f"[{self.id}] {self.nome} | {self.idade} anos | Turma: {self.turma}"


# ----------------------------------------------------------------------
# 2) BANCO DE DADOS: conexão e criação da tabela
# ----------------------------------------------------------------------
class BancoDeDados:
    def __init__(self, arquivo="escola.db"):
        # Se o arquivo não existir, o SQLite cria sozinho
        self.conexao = sqlite3.connect(arquivo)
        self.criar_tabela()

    def criar_tabela(self):
        sql = """
            CREATE TABLE IF NOT EXISTS alunos (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                nome  TEXT    NOT NULL,
                idade INTEGER NOT NULL,
                turma TEXT    NOT NULL
            )
        """
        self.conexao.execute(sql)
        self.conexao.commit()

    def fechar(self):
        self.conexao.close()


# ----------------------------------------------------------------------
# 3) REPOSITÓRIO: as 4 operações do CRUD
#    C = Create (inserir)   R = Read (listar/buscar)
#    U = Update (atualizar) D = Delete (excluir)
# ----------------------------------------------------------------------
class AlunoRepositorio:
    def __init__(self, banco):
        self.conexao = banco.conexao

    # C - CREATE
    def inserir(self, aluno):
        sql = "INSERT INTO alunos (nome, idade, turma) VALUES (?, ?, ?)"
        cursor = self.conexao.execute(sql, (aluno.nome, aluno.idade, aluno.turma))
        self.conexao.commit()          # commit = "salvar de verdade"
        aluno.id = cursor.lastrowid    # guarda o id que o banco criou

    # R - READ (todos)
    def listar(self):
        cursor = self.conexao.execute("SELECT id, nome, idade, turma FROM alunos")
        # Transforma cada linha do banco em um objeto Aluno
        return [Aluno(nome, idade, turma, id) for (id, nome, idade, turma) in cursor.fetchall()]

    # R - READ (um só)
    def buscar_por_id(self, id):
        sql = "SELECT id, nome, idade, turma FROM alunos WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Aluno(linha[1], linha[2], linha[3], linha[0])

    # U - UPDATE
    def atualizar(self, aluno):
        sql = "UPDATE alunos SET nome = ?, idade = ?, turma = ? WHERE id = ?"
        self.conexao.execute(sql, (aluno.nome, aluno.idade, aluno.turma, aluno.id))
        self.conexao.commit()

    # D - DELETE
    def excluir(self, id):
        self.conexao.execute("DELETE FROM alunos WHERE id = ?", (id,))
        self.conexao.commit()


# ----------------------------------------------------------------------
# 4) MENU: a interface com o usuário
# ----------------------------------------------------------------------
class Menu:
    def __init__(self, repositorio):
        self.repo = repositorio

    def exibir(self):
        print("\n===== SISTEMA DE ALUNOS =====")
        print("1 - Cadastrar aluno")
        print("2 - Listar alunos")
        print("3 - Buscar aluno por ID")
        print("4 - Atualizar aluno")
        print("5 - Excluir aluno")
        print("0 - Sair")

    def executar(self):
        while True:
            self.exibir()
            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                self.cadastrar()
            elif opcao == "2":
                self.listar()
            elif opcao == "3":
                self.buscar()
            elif opcao == "4":
                self.atualizar()
            elif opcao == "5":
                self.excluir()
            elif opcao == "0":
                print("Até a próxima!")
                break
            else:
                print("Opção inválida! Tente novamente.")

    # --- funções auxiliares para ler números com segurança ---
    def ler_inteiro(self, mensagem):
        while True:
            try:
                return int(input(mensagem))
            except ValueError:
                print("Digite apenas números inteiros!")

    # --- ações do menu ---
    def cadastrar(self):
        print("\n--- Cadastrar aluno ---")
        nome = input("Nome: ")
        idade = self.ler_inteiro("Idade: ")
        turma = input("Turma: ")

        aluno = Aluno(nome, idade, turma)
        self.repo.inserir(aluno)
        print(f"Aluno cadastrado com sucesso! ID = {aluno.id}")

    def listar(self):
        print("\n--- Lista de alunos ---")
        alunos = self.repo.listar()
        if not alunos:
            print("Nenhum aluno cadastrado.")
        for aluno in alunos:
            print(aluno)

    def buscar(self):
        id = self.ler_inteiro("\nDigite o ID do aluno: ")
        aluno = self.repo.buscar_por_id(id)
        if aluno:
            print(aluno)
        else:
            print("Aluno não encontrado.")

    def atualizar(self):
        id = self.ler_inteiro("\nDigite o ID do aluno que deseja atualizar: ")
        aluno = self.repo.buscar_por_id(id)

        if aluno is None:
            print("Aluno não encontrado.")
            return

        print(f"Dados atuais: {aluno}")
        print("(Pressione ENTER para manter o valor atual)")

        nome = input("Novo nome: ")
        idade = input("Nova idade: ")
        turma = input("Nova turma: ")

        # Só troca o que o usuário digitou
        if nome != "":
            aluno.nome = nome
        if idade != "":
            aluno.idade = int(idade)
        if turma != "":
            aluno.turma = turma

        self.repo.atualizar(aluno)
        print("Aluno atualizado com sucesso!")

    def excluir(self):
        id = self.ler_inteiro("\nDigite o ID do aluno que deseja excluir: ")
        aluno = self.repo.buscar_por_id(id)

        if aluno is None:
            print("Aluno não encontrado.")
            return

        confirmar = input(f"Excluir {aluno.nome}? (s/n): ")
        if confirmar.lower() == "s":
            self.repo.excluir(id)
            print("Aluno excluído com sucesso!")
        else:
            print("Operação cancelada.")


# ----------------------------------------------------------------------
# PROGRAMA PRINCIPAL: junta todas as peças
# ----------------------------------------------------------------------
if __name__ == "__main__":
    banco = BancoDeDados()                 # abre/cria o banco
    repositorio = AlunoRepositorio(banco)  # entrega o banco ao repositório
    menu = Menu(repositorio)               # entrega o repositório ao menu
    menu.executar()
    banco.fechar()
