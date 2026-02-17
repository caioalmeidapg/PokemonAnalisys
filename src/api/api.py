from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException

from core.decklist import fetch_decklist
from core.analysis import analyze_decklists
from core.pokeapi import build_candidates, resolve_pokemon_name_from_candidates
from core.limitless_jp import find_pokemon_in_limitless_since

DEFAULT_MIN_DATE = date(2026, 1, 23)

app = FastAPI(title="PokemonAnalisys API", version="1.0.0")


@app.get("/v1/limitless/count")
def count_in_limitless(pokemon: str):
    if not pokemon or not pokemon.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'pokemon' é obrigatório.")

    min_date = DEFAULT_MIN_DATE

    # 1) Resolve/valida na PokéAPI
    candidates = build_candidates(pokemon)
    found = resolve_pokemon_name_from_candidates(candidates)

    if not found:
        raise HTTPException(
            status_code=404,
            detail={"error": "Pokémon não encontrado na PokéAPI", "candidates": candidates},
        )

    # 2) Busca no Limitless
    matches = find_pokemon_in_limitless_since(found, min_date)

    return {
        "pokemon_input": pokemon,
        "pokemon_found": found,
        "min_date": str(min_date),
        "count": len(matches),
    }

@app.get("/v1/deck/core")
def deck_core(pokemon: str):
    if not pokemon or not pokemon.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'pokemon' é obrigatório.")

    min_date = DEFAULT_MIN_DATE  # travado

    # 1) Resolve/valida na PokéAPI
    candidates = build_candidates(pokemon)
    found = resolve_pokemon_name_from_candidates(candidates)

    if not found:
        raise HTTPException(
            status_code=404,
            detail={"error": "Pokémon não encontrado na PokéAPI", "candidates": candidates},
        )

    # 2) Busca no Limitless
    matches = find_pokemon_in_limitless_since(found, min_date)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"Não foram encontradas listas vencedoras de '{found}' desde {min_date}.",
        )

    # 3) Baixa decklists e analisa
    decklists = []
    errors = []

    for m in matches:
        if not m.decklist_url:
            errors.append({"date": str(m.row_date), "error": "decklist_url ausente"})
            continue
        try:
            deck = fetch_decklist(m.decklist_url)
            decklists.append(deck)
        except Exception as e:
            errors.append({"date": str(m.row_date), "decklist_url": m.decklist_url, "error": str(e)})

    if not decklists:
        raise HTTPException(
            status_code=502,
            detail={"error": "Nenhuma decklist pôde ser baixada/parseada.", "errors": errors[:5]},
        )

    result = analyze_decklists(decklists)

    core_list = []
    for name, qty in sorted(result.core.items(), key=lambda x: x[0].lower()):
        cat = next((s.category for s in result.all_stats if s.name == name), "Trainer")
        core_list.append({"name": name, "qty": qty, "category": cat})

    return {
        "pokemon_input": pokemon,
        "pokemon_found": found,
        "min_date_fixed": str(min_date),
        "matches_found": len(matches),
        "decklists_parsed": len(decklists),
        "ace_spec": result.ace_spec,
        "avg_category_totals": result.avg_category_totals,
        "core_total_cards": result.core_count_cards,
        "core": core_list,
        "errors_count": len(errors),
    }

@app.get("/v1/deck/above50")
def cards_above_50_not_core(pokemon: str):
    if not pokemon or not pokemon.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'pokemon' é obrigatório.")

    min_date = DEFAULT_MIN_DATE

    # 1) Resolve/valida na PokéAPI
    candidates = build_candidates(pokemon)
    found = resolve_pokemon_name_from_candidates(candidates)

    if not found:
        raise HTTPException(
            status_code=404,
            detail={"error": "Pokémon não encontrado na PokéAPI", "candidates": candidates},
        )

    # 2) Busca no Limitless
    matches = find_pokemon_in_limitless_since(found, min_date)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"Não foram encontradas listas vencedoras de '{found}' desde {min_date}.",
        )

    # 3) Baixa decklists
    decklists = []
    errors = []

    for m in matches:
        if not m.decklist_url:
            errors.append({"date": str(m.row_date), "error": "decklist_url ausente"})
            continue
        try:
            decklists.append(fetch_decklist(m.decklist_url))
        except Exception as e:
            errors.append({"date": str(m.row_date), "decklist_url": m.decklist_url, "error": str(e)})

    if not decklists:
        raise HTTPException(
            status_code=502,
            detail={"error": "Nenhuma decklist pôde ser baixada/parseada.", "errors": errors[:5]},
        )

    # 4) Analisa
    result = analyze_decklists(decklists)

    core_names = set(result.core.keys())

    # 5) Filtra cartas > 50% que NÃO são core
    filtered = []
    for s in result.remaining:
        if s.name in core_names:
            continue
        if s.presence_pct > 50.0:
            filtered.append({
                "name": s.name,
                "category": s.category,
                "present_in": s.present_in,
                "n_lists": result.n_lists,
                "presence_pct": int(round(s.presence_pct)),
                "avg_qty": s.avg_qty_round,
            })

    # ordena por % desc, depois nome
    filtered.sort(key=lambda x: (-x["presence_pct"], x["name"].lower()))

    return {
        "pokemon_input": pokemon,
        "pokemon_found": found,
        "min_date_fixed": str(min_date),
        "matches_found": len(matches),
        "decklists_parsed": len(decklists),
        "threshold_pct": 50,
        "count": len(filtered),
        "cards": filtered,
        "errors_count": len(errors),
    }

#TESTE
@app.get("/v1/deck/base")
def build_base_deck(pokemon: str):
    if not pokemon or not pokemon.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'pokemon' é obrigatório.")

    min_date = DEFAULT_MIN_DATE

    # 1) Resolve/valida na PokéAPI
    candidates = build_candidates(pokemon)
    found = resolve_pokemon_name_from_candidates(candidates)

    if not found:
        raise HTTPException(
            status_code=404,
            detail={"error": "Pokémon não encontrado na PokéAPI", "candidates": candidates},
        )

    # 2) Busca no Limitless
    matches = find_pokemon_in_limitless_since(found, min_date)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"Não foram encontradas listas vencedoras de '{found}' desde {min_date}.",
        )

    # 3) Baixa decklists
    decklists = []
    errors = []
    for m in matches:
        if not m.decklist_url:
            errors.append({"date": str(m.row_date), "error": "decklist_url ausente"})
            continue
        try:
            decklists.append(fetch_decklist(m.decklist_url))
        except Exception as e:
            errors.append({"date": str(m.row_date), "decklist_url": m.decklist_url, "error": str(e)})

    if not decklists:
        raise HTTPException(
            status_code=502,
            detail={"error": "Nenhuma decklist pôde ser baixada/parseada.", "errors": errors[:5]},
        )

    # 4) Analisa
    result = analyze_decklists(decklists)

    targets = dict(result.avg_category_totals)  # {"Pokemon": 18, "Trainer": 34, "Energy": 8}

    # helper: acha categoria "oficial" (conforme all_stats)
    def cat_of(name: str) -> str:
        return next((s.category for s in result.all_stats if s.name == name), "Trainer")

    # 5) Começa com o CORE
    base_deck = {"Pokemon": [], "Trainer": [], "Energy": []}
    core_cat_totals = {"Pokemon": 0, "Trainer": 0, "Energy": 0}

    for name, qty in result.core.items():
        cat = cat_of(name)
        # segurança: se vier algo fora, joga em Trainer
        if cat not in base_deck:
            cat = "Trainer"
        base_deck[cat].append({"name": name, "qty": qty, "presence_pct": 100})
        core_cat_totals[cat] += qty

    # 6) Verifica se o CORE já estourou a meta da categoria
    over = {c: core_cat_totals[c] - targets[c] for c in targets if core_cat_totals[c] > targets[c]}
    if over:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "O cerne (core) excede o limite de uma ou mais categorias. Não dá para montar deck fixo por categoria.",
                "targets": targets,
                "core_category_totals": core_cat_totals,
                "overflow": over,
            },
        )

    remaining_slots = {c: targets[c] - core_cat_totals[c] for c in targets}

    # 7) Completa com as cartas mais presentes (que NÃO são core), respeitando categoria
    core_names = set(result.core.keys())

    # usa all_stats (já tem categoria + presença). Ordena por presença desc
    candidates_stats = [s for s in result.all_stats if s.name not in core_names]
    candidates_stats.sort(key=lambda s: (-s.presence_pct, s.name.lower()))

    for s in candidates_stats:
        cat = s.category if s.category in remaining_slots else "Trainer"
        if remaining_slots[cat] <= 0:
            continue

        desired_qty = max(1, int(s.avg_qty_round))
        qty_to_add = min(desired_qty, remaining_slots[cat])

        if qty_to_add <= 0:
            continue

        base_deck[cat].append(
            {
                "name": s.name,
                "qty": qty_to_add,
                "presence_pct": int(round(s.presence_pct)),
            }
        )
        remaining_slots[cat] -= qty_to_add

        # terminou tudo
        if all(v == 0 for v in remaining_slots.values()):
            break

    # 8) Ordena cartas dentro de cada categoria (por presença desc)
    for cat in base_deck:
        base_deck[cat].sort(key=lambda x: (-x["presence_pct"], x["name"].lower()))

    final_counts = {c: sum(item["qty"] for item in base_deck[c]) for c in base_deck}
    total_cards = sum(final_counts.values())

    return {
        "pokemon_input": pokemon,
        "pokemon_found": found,
        "min_date_fixed": str(min_date),
        "matches_found": len(matches),
        "decklists_parsed": len(decklists),
        "avg_category_totals": targets,
        "core_category_totals": core_cat_totals,
        "remaining_slots_after_fill": remaining_slots,
        "final_category_counts": final_counts,
        "total_cards": total_cards,
        "deck_base": base_deck,  # lista por categoria com qty e % presença
        "errors_count": len(errors),
    }
