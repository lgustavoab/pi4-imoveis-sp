from datetime import date

import polars as pl

from pi4_imoveis_sp.analysis.overview import (
    add_price_ranges,
    apply_filters,
    build_analysis_dataset,
)
from pi4_imoveis_sp.data.cleaning import (
    AREA_COLUMN,
    VALUE_COLUMN,
)


def build_sample_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "registro": [
                1,
                2,
                3,
                4,
                5,
                6,
            ],
            "Data de Transação": [
                date(2025, 1, 10),
                date(2025, 2, 15),
                date(2025, 2, 20),
                date(2025, 3, 5),
                date(2025, 4, 12),
                date(2025, 5, 8),
            ],
            AREA_COLUMN: [
                50.0,
                80.0,
                100.0,
                120.0,
                150.0,
                200.0,
            ],
            VALUE_COLUMN: [
                250_000.0,
                300_000.0,
                450_000.0,
                750_000.0,
                1_500_000.0,
                6_000_000.0,
            ],
            "Padrão (IPTU)": [
                21,
                22,
                22,
                23,
                23,
                24,
            ],
            "cep4": [
                "0301",
                "0430",
                "0453",
                "0453",
                "0501",
                "0565",
            ],
            "flag_valor_m2_muito_baixo": [
                False,
                False,
                False,
                False,
                True,
                False,
            ],
            "flag_transacao_muito_abaixo_vvr": [
                False,
                False,
                False,
                False,
                False,
                True,
            ],
        }
    )


def build_filter_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "registro": [
                1,
                2,
                3,
                4,
                5,
            ],
            AREA_COLUMN: [
                50.0,
                80.0,
                100.0,
                120.0,
                150.0,
            ],
            VALUE_COLUMN: [
                250_000.0,
                300_000.0,
                750_000.0,
                900_000.0,
                2_500_000.0,
            ],
            "mes_transacao": [
                1,
                2,
                2,
                3,
                4,
            ],
            "Padrão (IPTU)": [
                21,
                22,
                23,
                23,
                24,
            ],
            "cep4": [
                "0301",
                "0430",
                "0453",
                "0453",
                "0501",
            ],
        }
    )


def test_build_analysis_dataset_removes_severe_anomalies() -> None:
    dataframe = build_sample_dataframe()

    result = build_analysis_dataset(dataframe)

    assert result.height == 4

    assert result.get_column("registro").to_list() == [
        1,
        2,
        3,
        4,
    ]


def test_build_analysis_dataset_derives_transaction_month() -> None:
    dataframe = build_sample_dataframe()

    result = build_analysis_dataset(dataframe)

    assert result.get_column("mes_transacao").to_list() == [
        1,
        2,
        2,
        3,
    ]


def test_apply_filters_with_empty_optional_filters() -> None:
    dataframe = build_filter_dataframe()

    result = apply_filters(
        dataframe=dataframe,
        selected_months=[],
        selected_patterns=[],
        selected_cep4=[],
        selected_price_range="Todas as faixas",
        minimum_area=50,
        maximum_area=150,
    )

    assert result.height == 5


def test_apply_filters_by_area() -> None:
    dataframe = build_filter_dataframe()

    result = apply_filters(
        dataframe=dataframe,
        selected_months=[],
        selected_patterns=[],
        selected_cep4=[],
        selected_price_range="Todas as faixas",
        minimum_area=80,
        maximum_area=120,
    )

    assert result.get_column("registro").to_list() == [
        2,
        3,
        4,
    ]


def test_apply_filters_by_multiple_dimensions() -> None:
    dataframe = build_filter_dataframe()

    result = apply_filters(
        dataframe=dataframe,
        selected_months=[2],
        selected_patterns=[23],
        selected_cep4=["0453"],
        selected_price_range="R$ 500 mil–1 mi",
        minimum_area=50,
        maximum_area=150,
    )

    assert result.height == 1

    assert result.get_column("registro").item() == 3


def test_price_filter_respects_range_boundaries() -> None:
    dataframe = build_filter_dataframe()

    result = apply_filters(
        dataframe=dataframe,
        selected_months=[],
        selected_patterns=[],
        selected_cep4=[],
        selected_price_range="Até R$ 300 mil",
        minimum_area=1,
        maximum_area=1_000,
    )

    assert result.get_column("registro").to_list() == [
        1,
        2,
    ]


def test_add_price_ranges_classifies_boundaries() -> None:
    dataframe = pl.DataFrame(
        {
            VALUE_COLUMN: [
                300_000.0,
                500_000.0,
                1_000_000.0,
                2_000_000.0,
                5_000_000.0,
                5_000_001.0,
            ]
        }
    )

    result = add_price_ranges(dataframe)

    assert result.get_column("faixa_preco").to_list() == [
        "Até R$ 300 mil",
        "R$ 300–500 mil",
        "R$ 500 mil–1 mi",
        "R$ 1–2 mi",
        "R$ 2–5 mi",
        "Acima de R$ 5 mi",
    ]
