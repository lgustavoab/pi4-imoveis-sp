import polars as pl

from pi4_imoveis_sp.data.cleaning import (
    AREA_COLUMN,
    VALUE_COLUMN,
)

PRICE_RANGES = {
    "Todas as faixas": (
        None,
        None,
    ),
    "Até R$ 300 mil": (
        None,
        300_000,
    ),
    "R$ 300–500 mil": (
        300_000,
        500_000,
    ),
    "R$ 500 mil–1 mi": (
        500_000,
        1_000_000,
    ),
    "R$ 1–2 mi": (
        1_000_000,
        2_000_000,
    ),
    "R$ 2–5 mi": (
        2_000_000,
        5_000_000,
    ),
    "Acima de R$ 5 mi": (
        5_000_000,
        None,
    ),
}


def build_analysis_dataset(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.filter(
        ~pl.col("flag_valor_m2_muito_baixo")
        & ~pl.col("flag_transacao_muito_abaixo_vvr")
    ).with_columns(
        pl.col("Data de Transação").dt.month().cast(pl.Int8).alias("mes_transacao")
    )


def apply_filters(
    dataframe: pl.DataFrame,
    selected_months: list[int],
    selected_patterns: list[int],
    selected_cep4: list[str],
    selected_price_range: str,
    minimum_area: int,
    maximum_area: int,
) -> pl.DataFrame:
    filtered = dataframe.filter(
        (pl.col(AREA_COLUMN) >= minimum_area) & (pl.col(AREA_COLUMN) <= maximum_area)
    )

    if selected_months:
        filtered = filtered.filter(pl.col("mes_transacao").is_in(selected_months))

    if selected_patterns:
        filtered = filtered.filter(pl.col("Padrão (IPTU)").is_in(selected_patterns))

    if selected_cep4:
        filtered = filtered.filter(pl.col("cep4").is_in(selected_cep4))

    minimum_price, maximum_price = PRICE_RANGES[selected_price_range]

    if minimum_price is not None:
        filtered = filtered.filter(pl.col(VALUE_COLUMN) > minimum_price)

    if maximum_price is not None:
        filtered = filtered.filter(pl.col(VALUE_COLUMN) <= maximum_price)

    return filtered


def add_price_ranges(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.with_columns(
        pl.when(pl.col(VALUE_COLUMN) <= 300_000)
        .then(pl.lit("Até R$ 300 mil"))
        .when(pl.col(VALUE_COLUMN) <= 500_000)
        .then(pl.lit("R$ 300–500 mil"))
        .when(pl.col(VALUE_COLUMN) <= 1_000_000)
        .then(pl.lit("R$ 500 mil–1 mi"))
        .when(pl.col(VALUE_COLUMN) <= 2_000_000)
        .then(pl.lit("R$ 1–2 mi"))
        .when(pl.col(VALUE_COLUMN) <= 5_000_000)
        .then(pl.lit("R$ 2–5 mi"))
        .otherwise(pl.lit("Acima de R$ 5 mi"))
        .alias("faixa_preco")
    )
