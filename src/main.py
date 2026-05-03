from analysis import build_readme_context, run_analysis
from cleaning import run_cleaning


def main() -> None:
    clean = run_cleaning()
    results = run_analysis()
    context = build_readme_context(results)

    print("EDA de Messi generado correctamente.")
    print(f"Goles analizados: {len(clean)}")
    print(f"Periodo: {context['year_start']}-{context['year_end']}")
    print("Outputs: data/processed/ y outputs/figures/")


if __name__ == "__main__":
    main()
