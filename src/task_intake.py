"""Deterministic text helpers for a synthetic coding exercise."""


def normalize_label(value: str) -> str:
    """Trim and collapse Unicode whitespace without changing letter case."""
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    return " ".join(value.split())
