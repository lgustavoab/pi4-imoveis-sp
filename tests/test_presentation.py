from pi4_imoveis_sp.presentation import (
    build_pattern_label,
    format_currency,
    format_integer,
    get_pattern_name,
)


def test_format_integer() -> None:
    assert format_integer(1000) == "1.000"
    assert format_integer(63807) == "63.807"
    assert format_integer(1) == "1"


def test_format_currency() -> None:
    assert format_currency(1000.0) == "R$ 1.000,00"
    assert format_currency(228857.12) == "R$ 228.857,12"
    assert format_currency(0.5) == "R$ 0,50"


def test_get_pattern_name() -> None:
    assert get_pattern_name(20) == "Padrão A"
    assert get_pattern_name(22) == "Padrão C"
    assert get_pattern_name(25) == "Padrão F"

    assert get_pattern_name(42) == "Padrão C"
    assert get_pattern_name(44) == "Padrão E"


def test_get_pattern_name_unknown_pattern() -> None:
    assert get_pattern_name(26) is None
    assert get_pattern_name(49) is None


def test_build_pattern_label() -> None:
    result = build_pattern_label(
        code=22,
        description="RESIDENCIAL VERTICAL",
    )

    assert result == ("22 — Padrão C — RESIDENCIAL VERTICAL")


def test_build_pattern_label_commercial() -> None:
    result = build_pattern_label(
        code=44,
        description="COMERCIAL VERTICAL",
    )

    assert result == ("44 — Padrão E — COMERCIAL VERTICAL")


def test_build_pattern_label_without_description() -> None:
    result = build_pattern_label(
        code=22,
        description=None,
    )

    assert result == "22 — Padrão C"


def test_build_pattern_label_unknown_pattern() -> None:
    result = build_pattern_label(
        code=26,
        description="OUTRO PADRÃO",
    )

    assert result == "26 — OUTRO PADRÃO"


def test_build_pattern_label_strips_description() -> None:
    result = build_pattern_label(
        code=22,
        description="  RESIDENCIAL VERTICAL  ",
    )

    assert result == ("22 — Padrão C — RESIDENCIAL VERTICAL")
