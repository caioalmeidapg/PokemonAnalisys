from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
import hashlib

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://limitlesstcg.com/tournaments/jp"
SITE_BASE = "https://limitlesstcg.com"

def make_absolute_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith("/"):
        return SITE_BASE + href
    return href


@dataclass
class MatchRow:
    row_date: date
    alts: list[str]
    tournament_url: Optional[str]
    decklist_url: Optional[str]


def _parse_iso_date(s: str) -> date:
    # "2026-02-16"
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def _page_url(page: int) -> str:
    return BASE_URL if page == 1 else f"{BASE_URL}?page={page}"


def _extract_rows(soup: BeautifulSoup) -> list:
    table = soup.find("table", class_="completed-tournaments") or soup.find("table")
    if not table:
        return []
    tbody = table.find("tbody") or table

    out = []
    for tr in tbody.find_all("tr"):
        if tr.find("th"):
            continue
        if tr.get("data-date"):
            out.append(tr)
    return out


def find_pokemon_in_limitless_since(
    pokemon_name: str,
    min_date: date,
    timeout: int = 20,
    max_pages: int = 500,
) -> list[MatchRow]:
    """
    Varre páginas (?page=N) da lista JP, coletando linhas cujo tr[data-date] >= min_date.
    Em cada linha, extrai:
      - data
      - alts das imgs da coluna Winner
      - tournament_url (link na coluna Date)
      - decklist_url (link /decks/list/... dentro da coluna Winner)
    Retorna somente as linhas em que pokemon_name aparece em alts.
    """

    pokemon_name = pokemon_name.strip().lower()
    matches: list[MatchRow] = []

    prev_hash: Optional[str] = None

    for page in range(1, max_pages + 1):
        url = _page_url(page)
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()

        # anti-loop: se o conteúdo repetir, paramos
        h = hashlib.sha256(r.content).hexdigest()
        if prev_hash == h:
            break
        prev_hash = h

        soup = BeautifulSoup(r.text, "html.parser")
        trs = _extract_rows(soup)

        # acabou a paginação
        if not trs:
            break

        should_stop = False

        for tr in trs:
            data_date = tr.get("data-date")
            if not data_date:
                continue

            row_date = _parse_iso_date(data_date)

            # atingiu data anterior ao corte -> para tudo
            if row_date < min_date:
                should_stop = True
                break

            tds = tr.find_all("td", recursive=False)
            if len(tds) < 4:
                continue

            # link do torneio (coluna Date)
            a_date = tds[0].find("a", href=True)
            tournament_url = make_absolute_url(a_date["href"]) if a_date else None

            # coluna Winner
            winner_td = tds[3]

            # link da decklist (fica dentro do Winner)
            decklist_url = None
            a_deck = winner_td.find("a", href=True)
            if a_deck:
                href = a_deck["href"]
                if "/decks/list/" in href:
                    decklist_url = make_absolute_url(href)

            # alts das imgs dentro do Winner
            imgs = winner_td.find_all("img")
            alts: list[str] = []
            for img in imgs:
                alt = (img.get("alt") or "").strip().lower()
                if alt:
                    alts.append(alt)

            if pokemon_name in alts:
                matches.append(
                    MatchRow(
                        row_date=row_date,
                        alts=alts,
                        tournament_url=tournament_url,
                        decklist_url=decklist_url,
                    )
                )

        if should_stop:
            break

    return matches