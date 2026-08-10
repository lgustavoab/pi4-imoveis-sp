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


def load_monthly_data() -> pl.DataFrame:
    sheets = pl.read_excel(
        ITBI_FILE,
        sheet_name=list(MONTH_SHEETS),
    )

    monthly_frames: list[pl.DataFrame] = []

    for sheet_name in MONTH_SHEETS:
        dataframe = sheets[sheet_name]

        unnamed_columns = [
            column for column in dataframe.columns if column.startswith("__UNNAMED__")
        ]

        if unnamed_columns:
            dataframe = dataframe.drop(unnamed_columns)

        dataframe = dataframe.with_columns(pl.lit(sheet_name).alias("Mês de Origem"))

        monthly_frames.append(dataframe)

    return pl.concat(
        monthly_frames,
        how="diagonal_relaxed",
    )


def print_count(label: str, value: int) -> None:
    print(f"{label:<55} {value:>10,}".replace(",", "."))


def main() -> None:
    if not ITBI_FILE.exists():
        raise FileNotFoundError(f"Arquivo do ITBI não encontrado em: {ITBI_FILE}")

    print("=" * 80)
    print("PERFIL DOS APARTAMENTOS — ITBI 2025")
    print("=" * 80)

    dataframe = load_monthly_data()

    print("\n1. FUNIL DE REGISTROS")
    print("-" * 80)

    total = dataframe.height

    purchase_and_sale = dataframe.filter(
        pl.col("Natureza de Transação") == PURCHASE_AND_SALE
    )

    apartments = dataframe.filter(pl.col("Uso (IPTU)") == APARTMENT_USE_CODE)

    apartment_sales = dataframe.filter(
        (pl.col("Natureza de Transação") == PURCHASE_AND_SALE)
        & (pl.col("Uso (IPTU)") == APARTMENT_USE_CODE)
    )

    full_apartment_sales = apartment_sales.filter(
        (pl.col("Proporção Transmitida (%)") - 100.0).abs() < 1e-9
    )

    print_count("Total de registros:", total)
    print_count("Compra e venda:", purchase_and_sale.height)
    print_count("Uso IPTU = 20 (apartamentos):", apartments.height)
    print_count(
        "Compra e venda + apartamento:",
        apartment_sales.height,
    )
    print_count(
        "Apartamento + compra e venda + transmissão 100%:",
        full_apartment_sales.height,
    )

    print("\n2. COMPLETUDE DAS PRINCIPAIS VARIÁVEIS")
    print("-" * 80)

    fields = (
        "Valor de Transação (declarado pelo contribuinte)",
        "Área Construída (m2)",
        "Bairro",
        "Padrão (IPTU)",
        "ACC (IPTU)",
        "Fração Ideal",
    )

    for column in fields:
        null_count = full_apartment_sales[column].null_count()
        valid_count = full_apartment_sales.height - null_count

        percentage = (
            valid_count / full_apartment_sales.height * 100
            if full_apartment_sales.height
            else 0.0
        )

        print(f"{column:<48} {valid_count:>8} válidos ({percentage:>6.2f}%)")

    print("\n3. VALOR DAS TRANSAÇÕES")
    print("-" * 80)

    value_column = "Valor de Transação (declarado pelo contribuinte)"

    value_stats = full_apartment_sales.select(
        pl.col(value_column).min().alias("mínimo"),
        pl.col(value_column).median().alias("mediana"),
        pl.col(value_column).mean().alias("média"),
        pl.col(value_column).max().alias("máximo"),
    )

    print(value_stats)

    print("\n4. ÁREA CONSTRUÍDA")
    print("-" * 80)

    area_stats = full_apartment_sales.select(
        pl.col("Área Construída (m2)").min().alias("mínimo"),
        pl.col("Área Construída (m2)").median().alias("mediana"),
        pl.col("Área Construída (m2)").mean().alias("média"),
        pl.col("Área Construída (m2)").max().alias("máximo"),
    )

    print(area_stats)

    print("\n5. LOCALIZAÇÃO")
    print("-" * 80)

    neighborhoods = full_apartment_sales.select(
        pl.col("Bairro").drop_nulls().n_unique()
    ).item()

    print_count("Bairros distintos:", neighborhoods)

    print("\n15 bairros com mais transações:")
    print(
        full_apartment_sales.filter(pl.col("Bairro").is_not_null())
        .group_by("Bairro")
        .len()
        .sort("len", descending=True)
        .head(15)
    )

    print("\n6. PADRÕES IPTU")
    print("-" * 80)

    print(
        full_apartment_sales.group_by(
            "Padrão (IPTU)",
            "Descrição do padrão (IPTU)",
        )
        .len()
        .sort("len", descending=True)
    )

    print("\n7. POSSÍVEIS VALORES INVÁLIDOS")
    print("-" * 80)

    invalid_values = full_apartment_sales.filter(
        pl.col(value_column).is_null() | (pl.col(value_column) <= 0)
    ).height

    invalid_areas = full_apartment_sales.filter(
        pl.col("Área Construída (m2)").is_null() | (pl.col("Área Construída (m2)") <= 0)
    ).height

    print_count(
        "Valor de transação nulo ou <= 0:",
        invalid_values,
    )
    print_count(
        "Área construída nula ou <= 0:",
        invalid_areas,
    )


if __name__ == "__main__":
    main()
