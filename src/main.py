from __future__ import annotations

from datetime import date
from pathlib import Path
from datetime import date, datetime

from core.pokeapi import (
    build_candidates,
    resolve_pokemon_name_from_candidates,
)
from core.limitless_jp import find_pokemon_in_limitless_since
from core.decklist import fetch_decklist
from core.analysis import analyze_decklists, write_analysis_txt

MIN_DATE = date(2026, 1, 23)


class PokemonAnalisysApp:
    def run(self):
        while True:
            q = input("Digite o nome do Pokémon (ou 'sair'): ").strip()
            if not q:
                continue
            if q.lower() == "sair":
                break

            # 1) valida pokémon na PokéAPI
            candidates = build_candidates(q)
            found = resolve_pokemon_name_from_candidates(candidates)

            if not found:
                print(f"❌ Pokémon não existe na PokéAPI. Tentativas: {candidates}")
                continue

            print(f"✅ {found} foi encontrado e validado pela PokéAPI")
            print(f"\n🔎 Localizando decklists vencedoras de {found}...\n")

            # 2) procura no Limitless (JP) desde MIN_DATE
            matches = find_pokemon_in_limitless_since(found, MIN_DATE)

            if not matches:
                print(f"❌ Não apareceu como winner desde {MIN_DATE.strftime('%d/%m/%Y')}.")
                continue

            print(
                f"✅ Foram encontradas {len(matches)} listas de {found} no Limitless desde {MIN_DATE.strftime('%d/%m/%Y')}"
            )
            print(f"\n🔎 Obtendo as decklists vencedoras...\n")

            # 3) loop nas matches e baixa decklist de cada uma
            decklists_dict = {}

            for i, m in enumerate(matches, start=1):
                key = f"lista_{i}"

                if not m.decklist_url:
                    decklists_dict[key] = {
                        "error": "decklist_url não encontrada na coluna Winner",
                        "date": str(m.row_date),
                        "alts": m.alts,
                        "tournament_url": m.tournament_url,
                        "decklist_url": None,
                    }
                    continue

                try:
                    deck = fetch_decklist(m.decklist_url)
                    decklists_dict[key] = {
                        "date": str(m.row_date),
                        "alts": m.alts,
                        "tournament_url": m.tournament_url,
                        "decklist_url": m.decklist_url,
                        "deck": deck,
                    }
                except Exception as e:
                    decklists_dict[key] = {
                        "error": f"Falha ao baixar/parsear decklist: {e}",
                        "date": str(m.row_date),
                        "alts": m.alts,
                        "tournament_url": m.tournament_url,
                        "decklist_url": m.decklist_url,
                    }

            print(f"✅ Todas as {len(decklists_dict)} decklists foram coletadas\n")

            # 4) roda a análise (cerne + presença + ACE etc.)
            decklists = [v["deck"] for v in decklists_dict.values() if "deck" in v]

            result = analyze_decklists(decklists)

            # Caminho do Desktop do usuário
            desktop = Path.home() / "Desktop"

            # Pasta Deck_Analysis no Desktop
            analysis_dir = desktop / "Deck_Analysis"

            # cria a pasta se não existir
            analysis_dir.mkdir(parents=True, exist_ok=True)

            # data atual
            date_str = datetime.now().strftime("%Y%m%d")

            # arquivo final
            out_file = analysis_dir / f"analysis_{found}_deck_{date_str}.txt"
            
            write_analysis_txt(
                out_path=out_file,
                found_name=found,
                min_date_br=MIN_DATE.strftime("%d/%m/%Y"),
                result=result,
            )

            print(f"✅ Relatório de análise do deck de {found} foi gerado com sucesso: {out_file}\n")

def main():
    PokemonAnalisysApp().run()


if __name__ == "__main__":
    main()