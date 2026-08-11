PATTERN_LETTERS = {
    0: "Padrão A",
    1: "Padrão B",
    2: "Padrão C",
    3: "Padrão D",
    4: "Padrão E",
    5: "Padrão F",
}


def format_integer(
    value: int,
) -> str:
    return f"{value:,}".replace(",", ".")


def format_currency(
    value: float,
) -> str:
    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {formatted}"


def get_pattern_name(
    code: int,
) -> str | None:
    pattern_index = code % 10

    return PATTERN_LETTERS.get(pattern_index)


def build_pattern_label(
    code: int,
    description: str | None,
) -> str:
    pattern_name = get_pattern_name(code)

    parts = [str(code)]

    if pattern_name:
        parts.append(pattern_name)

    if description:
        parts.append(description.strip())

    return " — ".join(parts)
