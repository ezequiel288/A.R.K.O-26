# A.R.K.O
Projeto POO
Integrantes: Arthur Duarte, David dos Santos, Ezequiel Teixeira, João Victor, José Alberto, José Alexandre.
IFAL Campus Palmeira dos Índios.
Professor: Luciano Torres Marques.

ARKO é uma plataforma de deistribuição de jogos online e offline, inspirado no Padrão das Plataformas da atualidade (ex.: Steam, Epicgames, etc.)

https://realpython.com/qt-designer-python/ -> Link para o QT Designer

https://tkinterbuilder.com/

## Organização dos dados

- `dados/arko.db`: contas, carrinho, amigos e transações.
- `dados/avaliacoes.db`: avaliações dos jogos.
- `dados/biblioteca.db`: jogos associados às bibliotecas dos usuários.
- `jogos/*.txt`: catálogo da Store, um arquivo por jogo, no formato Python com
  `titulo`, `descricao`, `preco`, `empresa` e `desconto`.
- `jogos/<arquivo-do-jogo>/`: capas em `imagens/` e executáveis em
  `executador/` associados a cada jogo da Store.
- `jogos/jogo_<id>/`: dados TXT de jogos locais da Biblioteca, com capa em
  `imagens/` e executável, atalho ou página em `executador/`.
- `imagens/`: imagens usadas pela interface.
- `executador/`: arquivos locais usados para iniciar jogos da Store.

Os jogos que antes eram definidos no código foram migrados para arquivos TXT
individuais em `jogos/`. Use **Adicionar jogo à Store** na tela Store para
cadastrar um jogo com sua capa e executável; o app cria o TXT e guarda os
arquivos nas pastas associadas ao jogo. O banco antigo `jogos/jogos.db`, se
existir, é lido somente para migrar jogos próprios cadastrados na Biblioteca;
novos jogos próprios são salvos em `jogo_<id>/jogo.txt`. O catálogo da Store
não usa banco de dados.