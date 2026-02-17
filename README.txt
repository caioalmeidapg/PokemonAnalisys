# PokemonAnalisys

Ferramenta para análise estatística de decklists vencedoras do Pokémon TCG com base em dados do LimitlessTCG.

O sistema permite:

- Identificar quantas vezes um Pokémon apareceu em decklists vencedoras
- Identificar o cerne (core) do deck
- Identificar cartas com alta taxa de presença
- Gerar automaticamente um deck base estatístico
- Gerar relatórios em arquivo .txt
- Disponibilizar todos os dados via API REST

---

# Requisitos

- Python 3.10 ou superior  
- Windows PowerShell ou CMD  
- Conexão com internet  

---

# Instalação

Execute os comandos abaixo na raiz do projeto:

Criar ambiente virtual:
python -m venv .venv

Ativar ambiente virtual:
.venv\Scripts\activate

Atualizar pip:
python -m pip install --upgrade pip

Instalar dependências:
pip install -r requirements.txt

Configurar PYTHONPATH:
$env:PYTHONPATH="src"

Executar o programa:
python src/run.py

O sistema irá gerar relatórios em:
Deck_Analysis/
Exemplo:
Deck_Analysis/analysis_zoroark_deck_230126.txt













