import polars as pl

from pi4_imoveis_sp.analysis.estimator import (
    format_cep,
    get_pattern_options,
    normalize_cep,
)


def test_normalize_cep_with_hyphen() -> None:
    assert normalize_cep("04303-000") == "04303000"


def test_normalize_cep_with_only_digits() -> None:
    assert normalize_cep("04303000") == "04303000"


def test_normalize_cep_removes_non_digits() -> None:
    assert normalize_cep("CEP: 04303-000") == "04303000"


def test_format_cep() -> None:
    assert format_cep("04303000") == "04303-000"


def test_cep4_can_be_derived_from_normalized_cep() -> None:
    normalized = normalize_cep("04303-000")

    assert normalized[:4] == "0430"


def test_get_pattern_options() -> None:
    dataframe = pl.DataFrame(
        {
            "Padrão (IPTU)": [
                22,
                23,
                44,
            ],
            "Descrição do padrão (IPTU)": [
                "RESIDENCIAL VERTICAL",
                "RESIDENCIAL VERTICAL",
                "COMERCIAL VERTICAL",
            ],
        }
    )

    result = get_pattern_options(dataframe)

    assert result == {
        22: "22 — Padrão C — RESIDENCIAL VERTICAL",
        23: "23 — Padrão D — RESIDENCIAL VERTICAL",
        44: "44 — Padrão E — COMERCIAL VERTICAL",
    }


def test_get_pattern_options_ignores_null_code() -> None:
    dataframe = pl.DataFrame(
        {
            "Padrão (IPTU)": [
                22,
                None,
            ],
            "Descrição do padrão (IPTU)": [
                "RESIDENCIAL VERTICAL",
                "SEM PADRÃO",
            ],
        }
    )

    result = get_pattern_options(dataframe)

    assert list(result) == [22]


def test_get_pattern_options_removes_duplicates() -> None:
    dataframe = pl.DataFrame(
        {
            "Padrão (IPTU)": [
                22,
                22,
            ],
            "Descrição do padrão (IPTU)": [
                "RESIDENCIAL VERTICAL",
                "RESIDENCIAL VERTICAL",
            ],
        }
    )

    result = get_pattern_options(dataframe)

    assert result == {
        22: "22 — Padrão C — RESIDENCIAL VERTICAL",
    }
