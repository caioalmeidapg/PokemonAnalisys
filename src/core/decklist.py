from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup

QTY_NAME_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def fetch_decklist(decklist_url: str, timeout: int = 20) -> dict:
    """
    Retorna a decklist completa em formato:
    {
      "pokemon": ["4 Riolu", ...],
      "trainer": ["4 Judge", ...],
      "energy":  ["10 Fighting Energy", ...]
    }
    """
    r = requests.get(decklist_url, timeout=timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Estratégia bem estável: coletar todos <a> cujo texto comece com "N Nome"
    # (ignorando links de preços).
    def is_card_line(a):
        txt = a.get_text(" ", strip=True)
        if not txt:
            return False
        if txt.startswith("$") or "€" in txt:
            return False
        return bool(QTY_NAME_RE.match(txt))

    anchors = [a for a in soup.find_all("a") if is_card_line(a)]

    # Agora segmenta por seções lendo o texto da página em ordem.
    # Vamos achar os índices onde aparecem "Pokémon", "Trainer", "Energy"
    text_blocks = soup.get_text("\n", strip=True).splitlines()

    # fallback simples: seções pelo que aparece no HTML (Pokémon/Trainer/Energy)
    # mas a coleta real das linhas vem dos anchors.
    deck = {"pokemon": [], "trainer": [], "energy": []}

    # Heurística de seção: percorre os anchors e muda seção quando encontrar o cabeçalho antes deles.
    # Pra ficar bem robusto: vamos localizar no DOM:
    # - achar o texto "Pokémon (" e coletar até "Trainer ("
    # - depois até "Energy ("
    # Se falhar, joga tudo em "trainer" como fallback.
    pokemon_header = soup.find(string=re.compile(r"^Pokémon\s*\(\d+\)"))
    trainer_header = soup.find(string=re.compile(r"^Trainer\s*\(\d+\)"))
    energy_header  = soup.find(string=re.compile(r"^Energy\s*\(\d+\)"))

    # Se não achou headers, devolve tudo sem separar (mas completo)
    if not (pokemon_header and trainer_header and energy_header):
        deck["trainer"] = [a.get_text(" ", strip=True) for a in anchors]
        return deck

    # Coleta por “faixas” no DOM: pega tudo entre headers
    def collect_between(start_node, end_node):
        out = []
        node = start_node.parent
        # anda para frente no documento
        for el in node.find_all_next():
            if end_node and el == end_node.parent:
                break
            if el.name == "a":
                txt = el.get_text(" ", strip=True)
                if is_card_line(el):
                    out.append(txt)
        return out

    deck["pokemon"] = collect_between(pokemon_header, trainer_header)
    deck["trainer"] = collect_between(trainer_header, energy_header)
    deck["energy"]  = collect_between(energy_header, None)

    return deck