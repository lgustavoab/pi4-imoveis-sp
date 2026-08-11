import polars as pl

from pi4_imoveis_sp.data.ingestion import (
    EXPECTED_COLUMNS,
    INTERIM_FILE,
    MONTH_SHEETS,
)

EXPECTED_TOTAL_ROWS = 230_525
EXPECTED_TOTAL_COLUMNS = 30


def main() -> None:
    print("=" * 80)
    print("VALIDAÇÃO DO PARQUET INTERMEDIÁRIO — ITBI 2025")
    print("=" * 80)

    if not INTERIM_FILE.exists():
        raise FileNotFoundError(f"Parquet intermediário não encontrado: {INTERIM_FILE}")

    dataframe = pl.read_parquet(INTERIM_FILE)

    print(f"\nArquivo: {INTERIM_FILE}")
    print(f"Registros: {dataframe.height:,}")
    print(f"Colunas: {dataframe.width}")

    print("\n1. DIMENSÕES")
    print("-" * 80)

    if dataframe.height != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Quantidade de registros inesperada: "
            f"{dataframe.height:,}. "
            f"Esperado: {EXPECTED_TOTAL_ROWS:,}."
        )

    if dataframe.width != EXPECTED_TOTAL_COLUMNS:
        raise ValueError(
            "Quantidade de colunas inesperada: "
            f"{dataframe.width}. "
            f"Esperado: {EXPECTED_TOTAL_COLUMNS}."
        )

    print("Dimensões válidas.")

    print("\n2. COLUNAS OFICIAIS")
    print("-" * 80)

    missing_columns = [
        column for column in EXPECTED_COLUMNS if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(f"Colunas oficiais ausentes: {missing_columns}")

    print("As 28 colunas oficiais estão presentes.")

    print("\n3. COLUNAS DE RASTREABILIDADE")
    print("-" * 80)

    tracking_columns = (
        "source_sheet",
        "source_month",
    )

    for column in tracking_columns:
        if column not in dataframe.columns:
            raise ValueError(f"Coluna de rastreabilidade ausente: {column}")

    print("source_sheet e source_month presentes.")

    print("\n4. REGISTROS POR MÊS")
    print("-" * 80)

    monthly_counts = (
        dataframe.group_by(
            "source_month",
            "source_sheet",
        )
        .len()
        .sort("source_month")
    )

    print(monthly_counts)

    if monthly_counts.height != len(MONTH_SHEETS):
        raise ValueError("Quantidade de meses diferente do esperado.")

    print("\n5. VALIDAÇÃO DOS MESES")
    print("-" * 80)

    expected_months = set(range(1, 13))

    actual_months = set(dataframe.get_column("source_month").unique().to_list())

    if actual_months != expected_months:
        raise ValueError(
            f"Meses encontrados: {sorted(actual_months)}. "
            f"Esperado: {sorted(expected_months)}."
        )

    print("Meses 1 a 12 presentes.")

    print("\n6. COLUNAS NÃO DOCUMENTADAS")
    print("-" * 80)

    unnamed_columns = [
        column for column in dataframe.columns if column.startswith("__UNNAMED__")
    ]

    if unnamed_columns:
        raise ValueError(
            f"O Parquet ainda contém colunas não documentadas: {unnamed_columns}"
        )

    print("Nenhuma coluna __UNNAMED__ presente.")

    print("\n7. NULOS NAS COLUNAS DE RASTREABILIDADE")
    print("-" * 80)

    source_sheet_nulls = dataframe.get_column("source_sheet").null_count()

    source_month_nulls = dataframe.get_column("source_month").null_count()

    print(f"source_sheet nulos: {source_sheet_nulls:,}")
    print(f"source_month nulos: {source_month_nulls:,}")

    if source_sheet_nulls or source_month_nulls:
        raise ValueError("Existem valores nulos nas colunas de rastreabilidade.")

    print("\n" + "=" * 80)
    print("PARQUET INTERMEDIÁRIO VALIDADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
