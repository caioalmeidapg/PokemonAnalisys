PokemonAnalisys

Ferramenta para análise estatística de decklists vencedoras do Pokémon TCG com base em dados do LimitlessTCG.

O sistema permite:

Identificar quantas vezes um Pokémon apareceu em decklists vencedoras

Identificar o cerne (core) do deck

Identificar cartas com alta taxa de presença

Gerar automaticamente um deck base estatístico

Gerar relatórios em arquivo .txt

Disponibilizar todos os dados via API REST

Requisitos

Python 3.10 ou superior

Windows PowerShell ou CMD

Conexão com internet

Instalação

Execute os comandos abaixo na raiz do projeto:

Criar ambiente virtual:

python -m venv .venv


Ativar ambiente virtual:

.venv\Scripts\activate


Atualizar pip:

python -m pip install --upgrade pip


Instalar dependências:

pip install -r requirements.txt

Execução do modo CLI (relatório TXT)

Configure o PYTHONPATH:

$env:PYTHONPATH="src"


Execute o programa:

python src/run.py


O sistema irá gerar relatórios em:

Deck_Analysis/


Exemplo:

Deck_Analysis/analysis_zoroark_deck_230126.txt

Execução da API

Configure o PYTHONPATH:

$env:PYTHONPATH="src"


Execute o servidor da API:

uvicorn api.api:app --reload


A API estará disponível em:

http://127.0.0.1:8000


Interface interativa (Swagger):

http://127.0.0.1:8000/docs

Endpoints disponíveis
Endpoint 1 — Quantas vezes o Pokémon apareceu

Retorna quantas vezes o Pokémon apareceu em decklists vencedoras desde 23/01/2026.

GET /v1/limitless/count?pokemon=zoroark


Resposta exemplo:

{
  "pokemon_input": "zoroark",
  "pokemon_found": "zoroark",
  "min_date": "2026-01-23",
  "count": 12
}

Endpoint 2 — Cerne do deck

Retorna o cerne estatístico do deck.

GET /v1/deck/core?pokemon=zoroark


Inclui:

ACE SPEC mais provável

cartas do core

médias por categoria

Endpoint 3 — Cartas com mais de 50% de presença (não core)

Retorna cartas com alta taxa de presença que não fazem parte do cerne.

GET /v1/deck/above50?pokemon=zoroark

Endpoint 4 — Deck base estatístico

Constrói automaticamente um deck base respeitando:

limites médios por categoria (Pokemon, Trainer, Energy)

preenchimento por maior taxa de presença

core sempre incluído primeiro

GET /v1/deck/base?pokemon=zoroark


Retorna:

deck completo

distribuição por categoria

total de cartas

estatísticas completas

Observações

Sempre ative o ambiente virtual antes de executar:

.venv\Scripts\activate


Se abrir um novo terminal, execute novamente:

$env:PYTHONPATH="src"