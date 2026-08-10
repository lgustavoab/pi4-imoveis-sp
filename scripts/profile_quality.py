from pathlib import Path

import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ITBI_FILE = PROJECT_ROOT / "data" / "raw" / "itbi_2025.xlsx"

MONTH_SHEETS = (
    "JAN-2025",
    "FEV-2025",
    "MAR-2025",
    "ABR-2025",
    "MAI-2025",
    "JUN-2025",
    "JUL-2025",
    "AGO-2025",
    "SET-2025",
    "OUT-2025",
    "NOV-2025",
    "DEZ-2025",
)

PURCHASE_AND_SALE = "1.Compra e venda"
APARTMENT_USE_CODE = 20

VALUE_COLUMN = "Valor de Transação (declarado pelo contribuinte)"
AREA_COLUMN = "Área Construída (m2)"


def load_apartment_sales() -> pl.DataFrame:
    sheets = pl.read_excel(
        ITBI_FILE,
        sheet_name=list(MONTH_SHEETS),
    )

    frames: list[pl.DataFrame] = []

    for sheet_name in MONTH_SHEETS:
        dataframe = sheets[sheet_name]

        unnamed_columns = [
            column for column in dataframe.columns if column.startswith("__UNNAMED__")
        ]

        if unnamed_columns:
            dataframe = dataframe.drop(unnamed_columns)

        dataframe = dataframe.with_columns(pl.lit(sheet_name).alias("Mês de Origem"))

        frames.append(dataframe)

    dataframe = pl.concat(
        frames,
        how="diagonal_relaxed",
    )

    return dataframe.filter(
        (pl.col("Natureza de Transação") == PURCHASE_AND_SALE)
        & (pl.col("Uso (IPTU)") == APARTMENT_USE_CODE)
        & ((pl.col("Proporção Transmitida (%)") - 100.0).abs() < 1e-9)
    )


def print_quantiles(
    dataframe: pl.DataFrame,
    column: str,
) -> None:
    quantiles = (
        0.001,
        0.005,
        0.01,
        0.05,
        0.25,
        0.50,
        0.75,
        0.95,
        0.99,
        0.995,
        0.999,
    )

    print(f"\n{column}")
    print("-" * 80)

    for quantile in quantiles:
        value = dataframe.select(pl.col(column).quantile(quantile)).item()

        print(f"P{quantile * 100:>5.1f}: {value:,.2f}")


def main() -> None:
    print("=" * 80)
    print("DIAGNÓSTICO DE QUALIDADE — APARTAMENTOS ITBI 2025")
    print("=" * 80)

    dataframe = load_apartment_sales()

    print(f"\nRegistros analisados: {dataframe.height:,}")

    print("\n1. QUANTIS")
    print("=" * 80)

    print_quantiles(
        dataframe,
        VALUE_COLUMN,
    )

    print_quantiles(
        dataframe,
        AREA_COLUMN,
    )

    print("\n2. MENORES VALORES DE TRANSAÇÃO")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "Bairro",
                AREA_COLUMN,
                VALUE_COLUMN,
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort(VALUE_COLUMN)
        .head(20)
    )

    print("\n3. MAIORES VALORES DE TRANSAÇÃO")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "Bairro",
                AREA_COLUMN,
                VALUE_COLUMN,
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort(VALUE_COLUMN, descending=True)
        .head(20)
    )

    print("\n4. MENORES ÁREAS")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "Bairro",
                AREA_COLUMN,
                VALUE_COLUMN,
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort(AREA_COLUMN)
        .head(20)
    )

    print("\n5. MAIORES ÁREAS")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "Bairro",
                AREA_COLUMN,
                VALUE_COLUMN,
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort(AREA_COLUMN, descending=True)
        .head(20)
    )

    print("\n6. POSSÍVEIS BAIRROS SUSPEITOS")
    print("=" * 80)

    suspicious_patterns = (
        "TORRE",
        "BLOCO",
        "EDIFICIO",
        "EDIFÍCIO",
        "APTO",
        "APART",
        "COND",
    )

    neighborhood_expression = pl.col("Bairro").str.to_uppercase()

    condition = pl.lit(False)

    for pattern in suspicious_patterns:
        condition = condition | neighborhood_expression.str.contains(
            pattern,
            literal=True,
        )

    suspicious_neighborhoods = (
        dataframe.filter(pl.col("Bairro").is_not_null() & condition)
        .group_by("Bairro")
        .len()
        .sort("len", descending=True)
        .head(50)
    )

    print(suspicious_neighborhoods)

    print("\n7. CEP")
    print("=" * 80)

    valid_cep = dataframe.filter(pl.col("CEP").is_not_null()).height

    print(
        f"CEP preenchido: "
        f"{valid_cep:,} / {dataframe.height:,} "
        f"({valid_cep / dataframe.height * 100:.2f}%)"
    )

    distinct_cep = dataframe.select(pl.col("CEP").drop_nulls().n_unique()).item()

    print(f"CEPs distintos: {distinct_cep:,}")


if __name__ == "__main__":
    main()
