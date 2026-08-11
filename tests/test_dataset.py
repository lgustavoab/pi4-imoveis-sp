from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    NUMERICAL_FEATURES_WITHOUT_MONTH,
)

EXPECTED_FINAL_FEATURES = {
    "Área Construída (m2)",
    "cep4",
    "Padrão (IPTU)",
    "idade_imovel",
    "Fração Ideal",
}

LEAKAGE_COLUMNS = {
    "Valor Venal de Referência",
    "Valor Venal de Referência (proporcional)",
    "Base de Cálculo adotada",
    "Valor Financiado",
    "valor_m2",
    "razao_transacao_vvr",
}


def test_final_model_has_five_features() -> None:
    assert len(FEATURE_COLUMNS_WITHOUT_MONTH) == 5


def test_final_model_feature_contract() -> None:
    assert set(FEATURE_COLUMNS_WITHOUT_MONTH) == EXPECTED_FINAL_FEATURES


def test_month_is_not_final_model_feature() -> None:
    assert "mes_transacao" not in FEATURE_COLUMNS_WITHOUT_MONTH


def test_month_exists_only_in_experimental_feature_set() -> None:
    assert "mes_transacao" in FEATURE_COLUMNS
    assert len(FEATURE_COLUMNS) == 6


def test_final_categorical_features() -> None:
    assert set(CATEGORICAL_FEATURES) == {
        "cep4",
        "Padrão (IPTU)",
    }


def test_final_numerical_features() -> None:
    assert set(NUMERICAL_FEATURES_WITHOUT_MONTH) == {
        "Área Construída (m2)",
        "idade_imovel",
        "Fração Ideal",
    }


def test_final_features_do_not_contain_leakage() -> None:
    assert not (set(FEATURE_COLUMNS_WITHOUT_MONTH) & LEAKAGE_COLUMNS)
