import re
import unicodedata
import requests
from typing import Optional

API = "https://pokeapi.co/api/v2/pokemon/{}"

IGNORE = {"ex"}
FORMS = {"mega"}
SUFFIXES = {"x", "y"}


def normalize_tokens(s: str) -> list[str]:
    s = s.strip().lower()

    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    s = s.replace("-", " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    return [t for t in s.split() if t and t not in IGNORE]


def build_candidates(user_input: str) -> list[str]:
    tokens = normalize_tokens(user_input)

    has_mega = "mega" in tokens
    suffix = next((t for t in tokens if t in SUFFIXES), None)

    base_tokens = [t for t in tokens if t not in FORMS and t not in SUFFIXES]
    if not base_tokens:
        return []

    base = "-".join(base_tokens)

    candidates: list[str] = []

    if has_mega:
        if suffix:
            candidates.append(f"{base}-mega-{suffix}")
        candidates.append(f"{base}-mega")

    candidates.append(base)

    out: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_pokemon_name_from_candidates(candidates: list[str], timeout: int = 10) -> Optional[str]:
    for name in candidates:
        r = requests.get(API.format(name), timeout=timeout)
        if r.status_code == 200:
            return name
        if r.status_code != 404:
            r.raise_for_status()
    return None