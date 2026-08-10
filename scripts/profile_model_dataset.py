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


def load_dataset() -> pl.DataFrame:
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

    return (
        dataframe.filter(
            (pl.col("Natureza de Transação") == PURCHASE_AND_SALE)
            & (pl.col("Uso (IPTU)") == APARTMENT_USE_CODE)
            & ((pl.col("Proporção Transmitida (%)") - 100.0).abs() < 1e-9)
        )
        .with_columns(
            pl.col("CEP")
            .cast(pl.String)
            .str.pad_start(8, "0")
            .alias("CEP_NORMALIZADO"),
            (pl.col(VALUE_COLUMN) / pl.col(AREA_COLUMN)).alias("VALOR_M2"),
        )
        .with_columns(
            pl.col("CEP_NORMALIZADO").str.slice(0, 3).alias("CEP3"),
            pl.col("CEP_NORMALIZADO").str.slice(0, 4).alias("CEP4"),
            pl.col("CEP_NORMALIZADO").str.slice(0, 5).alias("CEP5"),
        )
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


def print_threshold(
    dataframe: pl.DataFrame,
    minimum_value: float,
) -> None:
    remaining = dataframe.filter(pl.col(VALUE_COLUMN) >= minimum_value).height

    removed = dataframe.height - remaining

    percentage = removed / dataframe.height * 100

    print(
        f"Valor >= R$ {minimum_value:>10,.2f}: "
        f"{remaining:>6,} registros | "
        f"removidos: {removed:>5,} "
        f"({percentage:.2f}%)"
    )


def main() -> None:
    print("=" * 80)
    print("DIAGNÓSTICO DO DATASET DE MODELAGEM — ITBI 2025")
    print("=" * 80)

    dataframe = load_dataset()

    print(f"\nRegistros iniciais: {dataframe.height:,}")

    print("\n1. PREÇO POR M²")
    print("=" * 80)

    print_quantiles(
        dataframe,
        "VALOR_M2",
    )

    print("\n2. IMPACTO DE LIMITES MÍNIMOS DE PREÇO")
    print("=" * 80)

    thresholds = (
        1,
        1_000,
        10_000,
        25_000,
        50_000,
        75_000,
        100_000,
        125_000,
        150_000,
    )

    for threshold in thresholds:
        print_threshold(
            dataframe,
            threshold,
        )

    print("\n3. CARDINALIDADE GEOGRÁFICA")
    print("=" * 80)

    for column in ("CEP3", "CEP4", "CEP5", "CEP_NORMALIZADO"):
        unique_count = dataframe.select(pl.col(column).n_unique()).item()

        print(f"{column:<20} {unique_count:>8,} categorias")

    print("\n4. GRUPOS CEP3 MAIS FREQUENTES")
    print("=" * 80)

    print(dataframe.group_by("CEP3").len().sort("len", descending=True).head(20))

    print("\n5. MENORES PREÇOS POR M²")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "CEP_NORMALIZADO",
                AREA_COLUMN,
                VALUE_COLUMN,
                "VALOR_M2",
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort("VALOR_M2")
        .head(20)
    )

    print("\n6. MAIORES PREÇOS POR M²")
    print("=" * 80)

    print(
        dataframe.select(
            [
                "N° do Cadastro (SQL)",
                "CEP_NORMALIZADO",
                AREA_COLUMN,
                VALUE_COLUMN,
                "VALOR_M2",
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort("VALOR_M2", descending=True)
        .head(20)
    )


if __name__ == "__main__":
    main()
