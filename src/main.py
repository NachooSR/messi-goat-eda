from analysis import run_analysis
from cleaning import run_cleaning


def main() -> None:
    clean = run_cleaning()
    run_analysis()

    print("EDA de Messi generado correctamente.")
    print(f"Goles analizados: {len(clean)}")
    print(f"Periodo: {clean['year'].min()}-{clean['year'].max()}")
    print("Outputs: data/processed/ y outputs/figures/")


if __name__ == "__main__":
    main()
