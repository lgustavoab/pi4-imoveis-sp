from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "itbi_2025.xlsx"
INTERIM_FILE = PROJECT_ROOT / "data" / "interim" / "itbi_2025.parquet"

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

EXPECTED_COLUMNS = (
    "N° do Cadastro (SQL)",
    "Nome do Logradouro",
    "Número",
    "Complemento",
    "Bairro",
    "Referência",
    "CEP",
    "Natureza de Transação",
    "Valor de Transação (declarado pelo contribuinte)",
    "Data de Transação",
    "Valor Venal de Referência",
    "Proporção Transmitida (%)",
    "Valor Venal de Referência (proporcional)",
    "Base de Cálculo adotada",
    "Tipo de Financiamento",
    "Valor Financiado",
    "Cartório de Registro",
    "Matrícula do Imóvel",
    "Situação do SQL",
    "Área do Terreno (m2)",
    "Testada (m)",
    "Fração Ideal",
    "Área Construída (m2)",
    "Uso (IPTU)",
    "Descrição do uso (IPTU)",
    "Padrão (IPTU)",
    "Descrição do padrão (IPTU)",
    "ACC (IPTU)",
)


def validate_source_file(path: Path = RAW_FILE) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo bruto do ITBI não encontrado: {path}")


def remove_undocumented_columns(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    extra_columns = [
        column for column in dataframe.columns if column not in EXPECTED_COLUMNS
    ]

    unexpected_columns = [
        column for column in extra_columns if not column.startswith("__UNNAMED__")
    ]

    if unexpected_columns:
        raise ValueError(
            f"Foram encontradas colunas extras não reconhecidas: {unexpected_columns}"
        )

    if extra_columns:
        dataframe = dataframe.drop(extra_columns)

    return dataframe


def validate_schema(
    dataframe: pl.DataFrame,
    sheet_name: str,
) -> None:
    missing_columns = [
        column for column in EXPECTED_COLUMNS if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"A aba {sheet_name!r} não contém todas as colunas esperadas. "
            f"Ausentes: {missing_columns}"
        )

    if dataframe.columns != list(EXPECTED_COLUMNS):
        raise ValueError(
            f"A aba {sheet_name!r} possui ordem de colunas diferente "
            "do esquema oficial esperado."
        )


def load_monthly_sheets(
    path: Path = RAW_FILE,
) -> dict[str, pl.DataFrame]:
    validate_source_file(path)

    sheets = pl.read_excel(
        path,
        sheet_name=list(MONTH_SHEETS),
    )

    missing_sheets = [
        sheet_name for sheet_name in MONTH_SHEETS if sheet_name not in sheets
    ]

    if missing_sheets:
        raise ValueError(f"Abas mensais ausentes no arquivo: {missing_sheets}")

    return sheets


def build_interim_dataframe(
    path: Path = RAW_FILE,
) -> pl.DataFrame:
    sheets = load_monthly_sheets(path)

    monthly_frames: list[pl.DataFrame] = []

    for month_number, sheet_name in enumerate(
        MONTH_SHEETS,
        start=1,
    ):
        dataframe = sheets[sheet_name]

        dataframe = remove_undocumented_columns(dataframe)
        validate_schema(dataframe, sheet_name)

        dataframe = dataframe.with_columns(
            pl.lit(sheet_name).alias("source_sheet"),
            pl.lit(month_number).cast(pl.Int8).alias("source_month"),
        )

        monthly_frames.append(dataframe)

    return pl.concat(
        monthly_frames,
        how="vertical_relaxed",
    )


def write_interim_parquet(
    dataframe: pl.DataFrame,
    output_path: Path = INTERIM_FILE,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.write_parquet(
        output_path,
        compression="zstd",
    )


def run_ingestion(
    source_path: Path = RAW_FILE,
    output_path: Path = INTERIM_FILE,
) -> pl.DataFrame:
    dataframe = build_interim_dataframe(source_path)

    write_interim_parquet(
        dataframe,
        output_path,
    )

    return dataframe
