from pathlib import Path

import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ITBI_FILE = PROJECT_ROOT / "data" / "raw" / "itbi_2025.xlsx"

AUXILIARY_SHEETS = (
    "LEGENDA",
    "EXPLICAÇÕES",
    "Tabela de USOS",
    "Tabela de PADRÕES",
)


def print_sheet(
    sheet_name: str,
    dataframe: pl.DataFrame,
) -> None:
    print("\n")
    print("=" * 100)
    print(sheet_name)
    print("=" * 100)

    print(f"\nDimensões: {dataframe.height} linhas x {dataframe.width} colunas")

    print("\nColunas:")
    for index, column in enumerate(dataframe.columns, start=1):
        print(f"{index:02d}. {column}")

    print("\nConteúdo:")
    print("-" * 100)

    for index, row in enumerate(
        dataframe.iter_rows(named=True),
        start=1,
    ):
        print(f"{index:02d}. {row}")


def main() -> None:
    if not ITBI_FILE.exists():
        raise FileNotFoundError(f"Arquivo do ITBI não encontrado em: {ITBI_FILE}")

    print("=" * 100)
    print("DICIONÁRIO E TABELAS AUXILIARES — ITBI 2025")
    print("=" * 100)

    sheets = pl.read_excel(
        ITBI_FILE,
        sheet_name=list(AUXILIARY_SHEETS),
    )

    for sheet_name in AUXILIARY_SHEETS:
        print_sheet(
            sheet_name,
            sheets[sheet_name],
        )


if __name__ == "__main__":
    main()
