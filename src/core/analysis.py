from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from collections import defaultdict, Counter


# ================== ACE SPECS ==================

ACE_SPECS = {
   "Neo Upper Energy",
    "Reboot Pod",
    "Prime Catcher",
    "Maximum Belt",
    "Master Ball",
    "Hero's Cape",
    "Awakening Drum",
    "Legacy Energy",
    "Unfair Stamp",
    "Survival Brace",
    "Secret Box",
    "Scoop Up Cyclone",
    "Hyper Aroma",
    "Poké Vital A",
    "Neutralization Zone",
    "Dangerous Laser",
    "Sparkling Crystal",
    "Grand Tree",
    "Deluxe Bomb",
    "Enriching Energy",
    "Scramble Switch",
    "Precious Trolley",
    "Miracle Headset",
    "Megaton Blower",
    "Energy Search Pro",
    "Brilliant Blender",
    "Amulet of Hope",
    "Treasure Tracker",
    "Max Rod"
}


# ================== MODELOS ==================

@dataclass
class CardStat:
    name: str
    category: str
    present_in: int
    presence_pct: float
    avg_qty_raw: float
    avg_qty_round: int


@dataclass
class AnalysisResult:
    n_lists: int
    core: Dict[str, int]
    core_count_cards: int
    avg_category_totals: Dict[str, int]
    ace_spec: str | None
    remaining: List[CardStat]
    all_stats: List[CardStat]


# ================== UTIL ==================

def _round_half_up_int(x: float) -> int:
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _parse_line(line: str) -> Tuple[int, str]:
    parts = line.strip().split(" ", 1)
    return int(parts[0]), parts[1].strip()


def compute_category_averages_force_60(
    totals_by_cat_each: List[Dict[str, int]],
    target_total: int = 60,
) -> Dict[str, int]:

    cats = ["Pokemon", "Trainer", "Energy"]

    raw = {}
    rounded = {}

    for cat in cats:
        vals = [t[cat] for t in totals_by_cat_each]
        avg = sum(vals) / len(vals) if vals else 0.0
        raw[cat] = avg
        rounded[cat] = _round_half_up_int(avg)

    def total():
        return sum(rounded.values())

    diff = target_total - total()

    # Ajuste fino
    while diff != 0:
        best_cat = None
        best_cost = None

        for cat in cats:
            if diff > 0:
                next_int = rounded[cat] + 1
                cost = next_int - raw[cat]
            else:
                if rounded[cat] <= 0:
                    continue
                prev_int = rounded[cat] - 1
                cost = raw[cat] - prev_int

            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_cat = cat

        if best_cat is None:
            break

        if diff > 0:
            rounded[best_cat] += 1
            diff -= 1
        else:
            rounded[best_cat] -= 1
            diff += 1

    return rounded


# ================== CORE ANALYSIS ==================

def normalize_deck(deck: Dict[str, List[str]]) -> Tuple[Dict[str, int], Dict[str, str]]:

    card_qty = {}
    card_cat = {}

    mapping = {
        "pokemon": "Pokemon",
        "trainer": "Trainer",
        "energy": "Energy",
    }

    for k, cat in mapping.items():
        for line in deck.get(k, []) or []:
            qty, name = _parse_line(line)
            card_qty[name] = card_qty.get(name, 0) + qty
            card_cat[name] = cat

    return card_qty, card_cat


def analyze_decklists(decklists: List[Dict[str, List[str]]]) -> AnalysisResult:

    n = len(decklists)
    if n == 0:
        return AnalysisResult(
            0, {}, 0,
            {"Pokemon": 0, "Trainer": 0, "Energy": 0},
            None, [], []
        )

    decks_qty = []
    decks_cat = []
    totals_by_cat_each = []

    for d in decklists:
        qty_map, cat_map = normalize_deck(d)
        decks_qty.append(qty_map)
        decks_cat.append(cat_map)

        totals = {"Pokemon": 0, "Trainer": 0, "Energy": 0}
        for name, qty in qty_map.items():
            totals[cat_map[name]] += qty
        totals_by_cat_each.append(totals)

    cat_votes = defaultdict(Counter)
    for cat_map in decks_cat:
        for name, cat in cat_map.items():
            cat_votes[name][cat] += 1

    def best_cat(name: str) -> str:
        return cat_votes[name].most_common(1)[0][0]

    appear_counts = Counter()
    qty_lists = defaultdict(list)

    for deck in decks_qty:
        for name, qty in deck.items():
            appear_counts[name] += 1
            qty_lists[name].append(qty)

    core = {}
    all_stats = []
    remaining = []

    for name, qtys in qty_lists.items():
        present = appear_counts[name]
        pct = (present / n) * 100
        avg_raw = sum(qtys) / len(qtys)
        avg_round = _round_half_up_int(avg_raw)

        stat = CardStat(
            name=name,
            category=best_cat(name),
            present_in=present,
            presence_pct=pct,
            avg_qty_raw=avg_raw,
            avg_qty_round=avg_round,
        )

        all_stats.append(stat)

        if present == n:
            core[name] = max(avg_round, 1)
        else:
            remaining.append(stat)

    # ACE SPEC
    ace_counts = {s.name: s.present_in for s in all_stats if s.name in ACE_SPECS}
    ace_spec = None
    if ace_counts:
        max_count = max(ace_counts.values())
        ace_spec = sorted(
            [k for k, v in ace_counts.items() if v == max_count],
            key=str.lower
        )[0]

    avg_category_totals = compute_category_averages_force_60(
        totals_by_cat_each, 60
    )

    core_count_cards = sum(core.values())

    remaining.sort(key=lambda s: (-s.presence_pct, s.name.lower()))
    all_stats.sort(key=lambda s: (-s.presence_pct, s.name.lower()))

    return AnalysisResult(
        n_lists=n,
        core=core,
        core_count_cards=core_count_cards,
        avg_category_totals=avg_category_totals,
        ace_spec=ace_spec,
        remaining=remaining,
        all_stats=all_stats,
    )


# ================== TXT OUTPUT ==================

def write_analysis_txt(
    out_path: str,
    found_name: str,
    min_date_br: str,
    result: AnalysisResult,
) -> None:

    buckets = {"Pokemon": [], "Trainer": [], "Energy": []}

    for name, qty in result.core.items():
        cat = next((s.category for s in result.all_stats if s.name == name), "Trainer")
        buckets[cat].append((name, qty))

    for cat in buckets:
        buckets[cat].sort(key=lambda x: x[0].lower())

    core_cat_totals = {cat: sum(q for _, q in buckets[cat]) for cat in buckets}

    total_media = sum(result.avg_category_totals.values())

    lines = []
    lines.append("PokemonAnalisys - Core Deck Report")
    lines.append(f"Pokemon: {found_name}")
    lines.append(f"Filtro (desde): {min_date_br}")
    lines.append(f"Listas analisadas: {result.n_lists}")
    lines.append("")
    lines.append("=== MÉDIAS POR CATEGORIA ===")
    lines.append(f"Pokémon:  {result.avg_category_totals['Pokemon']}")
    lines.append(f"Trainer:  {result.avg_category_totals['Trainer']}")
    lines.append(f"Energy:   {result.avg_category_totals['Energy']}")
    lines.append(f"Total:    {total_media}")
    lines.append("")
    lines.append(f"ACE SPEC mais provável: {result.ace_spec or '(não identificada)'}")
    lines.append("")
    lines.append("=== CERNE DO DECK ===")
    lines.append(f"Total de cartas no cerne: {result.core_count_cards}")
    lines.append("")

    for cat in ["Pokemon", "Trainer", "Energy"]:
        label = "Pokémon" if cat == "Pokemon" else cat
        lines.append(f"{label}: {core_cat_totals[cat]}")
        for name, qty in buckets[cat]:
            lines.append(f"{qty} {name}")
        lines.append("")

    lines.append("=== CARTAS RESTANTES (probabilidade de entrar no deck) ===")
    lines.append("Formato: %Presença | Listas | QtdMédia | Carta | Tipo")
    lines.append("")

    for s in result.remaining:
        pct = _round_half_up_int(s.presence_pct)
        lines.append(
            f"{pct:>3}% | {s.present_in:>2}/{result.n_lists} | {s.avg_qty_round:>2} | {s.name} | {s.category}"
        )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))