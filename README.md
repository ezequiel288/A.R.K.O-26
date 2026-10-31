# A.R.K.O
Projeto POO
Integrantes: Arthur Duarte, David dos Santos, Ezequiel Teixeira, João Victor, José Alberto, José Alexandre.
IFAL Campus Palmeira dos Índios.
Professor: Luciano Torres Marques.

ARKO é uma plataforma de deistribuição de jogos online e offline, inspirado no Padrão das Plataformas da atualidade (ex.: Steam, Epicgames, etc.)

https://realpython.com/qt-designer-python/ -> Link para o QT Designer

https://tkinterbuilder.com/

## Organização dos dados

- `dados/arko.db`: contas, carrinho, amigos, transações, avaliações e
  jogos associados às bibliotecas dos usuários.
- `jogos/*.txt`: catálogo da Store, um arquivo por jogo, no formato Python com
  `titulo`, `descricao`, `preco`, `empresa` e `desconto`.
- `jogos/<arquivo-do-jogo>/`: capas em `imagens/` e executáveis ou links
  (`url.txt`) em `executador/` associados a cada jogo da Store; ambos são
  opcionais.
- `jogos/jogo_<id>/`: dados TXT de jogos locais da Biblioteca, com capa em
  `imagens/` e executável, atalho ou página em `executador/`, todos opcionais.
- `imagens/`: imagens usadas pela interface.
- `executador/`: arquivos locais usados para iniciar jogos da Store.

As capas da Store e da Biblioteca aceitam PNG, JPG, JPEG, JFIF, WebP, BMP e
outros formatos de imagem suportados pela instalação do Qt.

Os dados de contas, biblioteca, avaliações, carrinho, amigos e transações são
mantidos juntos em `dados/arko.db`. Se `avaliacoes.db` ou `biblioteca.db`
existirem de versões anteriores, seus registros são consolidados sem duplicar
jogos ou avaliações e os arquivos separados são removidos após a migração.

Os jogos que antes eram definidos no código foram migrados para arquivos TXT
individuais em `jogos/`. Use **Adicionar jogo à Store** na tela Store para
cadastrar um jogo com capa e executável ou link HTTP/HTTPS opcionais; o app cria
o TXT e guarda os arquivos informados nas pastas associadas ao jogo. Links são
salvos em `executador/url.txt` e abertos no navegador padrão. O banco antigo
`jogos/jogos.db`, se existir, é lido somente para migrar jogos próprios
cadastrados na Biblioteca; novos jogos próprios são salvos em
`jogo_<id>/jogo.txt`. O catálogo da Store não usa banco de dados.