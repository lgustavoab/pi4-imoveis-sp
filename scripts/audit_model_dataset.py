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

VALUE_COLUMN = "Valor de Transação (declarado pelo contribuinte)"
VVR_COLUMN = "Valor Venal de Referência (proporcional)"
AREA_COLUMN = "Área Construída (m2)"


def load_dataset() -> pl.DataFrame:
    sheets = pl.read_excel(
        ITBI_FILE,
        sheet_name=list(MONTH_SHEETS),
    )

    frames: list[pl.DataFrame] = []

    for sheet_name in MONTH_SHEETS:
        dataframe = sheets[sheet_name]

        unnamed = [
            column for column in dataframe.columns if column.startswith("__UNNAMED__")
        ]

        if unnamed:
            dataframe = dataframe.drop(unnamed)

        frames.append(dataframe)

    dataframe = pl.concat(
        frames,
        how="diagonal_relaxed",
    )

    return (
        dataframe.filter(
            (pl.col("Natureza de Transação") == "1.Compra e venda")
            & (pl.col("Uso (IPTU)") == 20)
            & ((pl.col("Proporção Transmitida (%)") - 100.0).abs() < 1e-9)
        )
        .with_columns(
            pl.col("CEP")
            .cast(pl.String)
            .str.pad_start(8, "0")
            .alias("CEP_NORMALIZADO"),
            (pl.col(VALUE_COLUMN) / pl.col(AREA_COLUMN)).alias("VALOR_M2"),
            (pl.col(VALUE_COLUMN) / pl.col(VVR_COLUMN)).alias("RAZAO_TRANSACAO_VVR"),
        )
        .with_columns(
            pl.col("CEP_NORMALIZADO").str.slice(0, 4).alias("CEP4"),
        )
    )


def main() -> None:
    dataframe = load_dataset()

    print("=" * 80)
    print("AUDITORIA FINAL DO DATASET — ITBI 2025")
    print("=" * 80)

    print(f"\nRegistros: {dataframe.height:,}")

    print("\n1. LIMITES DE PREÇO POR M²")
    print("=" * 80)

    thresholds = (
        100,
        250,
        500,
        750,
        1_000,
        1_250,
        1_500,
        1_750,
        2_000,
    )

    for threshold in thresholds:
        count = dataframe.filter(pl.col("VALOR_M2") < threshold).height

        percentage = count / dataframe.height * 100

        print(
            f"< R$ {threshold:>5,.0f}/m²: {count:>5,} registros ({percentage:>5.2f}%)"
        )

    print("\n2. RELAÇÃO TRANSAÇÃO / VVR")
    print("=" * 80)

    ratios = (
        0.01,
        0.05,
        0.10,
        0.25,
        0.50,
        0.75,
    )

    for ratio in ratios:
        count = dataframe.filter(pl.col("RAZAO_TRANSACAO_VVR") < ratio).height

        percentage = count / dataframe.height * 100

        print(f"Transação < {ratio:>5.0%} do VVR: {count:>5,} ({percentage:>5.2f}%)")

    print("\n3. PREÇOS BAIXOS — AMOSTRA")
    print("=" * 80)

    print(
        dataframe.filter(pl.col("VALOR_M2") < 1_000)
        .select(
            [
                "N° do Cadastro (SQL)",
                "CEP_NORMALIZADO",
                AREA_COLUMN,
                VALUE_COLUMN,
                VVR_COLUMN,
                "VALOR_M2",
                "RAZAO_TRANSACAO_VVR",
                "Padrão (IPTU)",
                "ACC (IPTU)",
            ]
        )
        .sort("VALOR_M2")
        .head(30)
    )

    print("\n4. ACC")
    print("=" * 80)

    print(
        dataframe.select(
            pl.col("ACC (IPTU)").min().alias("mínimo"),
            pl.col("ACC (IPTU)").median().alias("mediana"),
            pl.col("ACC (IPTU)").max().alias("máximo"),
        )
    )

    future_acc = dataframe.filter(pl.col("ACC (IPTU)") > 2025).height

    print(f"ACC > 2025: {future_acc:,}")

    print("\n5. FRAÇÃO IDEAL")
    print("=" * 80)

    invalid_fraction = dataframe.filter(
        pl.col("Fração Ideal").is_null()
        | (pl.col("Fração Ideal") <= 0)
        | (pl.col("Fração Ideal") > 1)
    ).height

    print(f"Fração ideal fora de ]0, 1]: {invalid_fraction:,}")

    print("\n6. REPRESENTATIVIDADE DO CEP4")
    print("=" * 80)

    cep_groups = dataframe.group_by("CEP4").len()

    print(
        cep_groups.select(
            pl.col("len").min().alias("mínimo"),
            pl.col("len").median().alias("mediana"),
            pl.col("len").mean().alias("média"),
            pl.col("len").max().alias("máximo"),
        )
    )

    for minimum_size in (5, 10, 20, 50):
        groups = cep_groups.filter(pl.col("len") < minimum_size).height

        print(f"CEP4 com menos de {minimum_size:>2} registros: {groups:,}")


if __name__ == "__main__":
    main()
