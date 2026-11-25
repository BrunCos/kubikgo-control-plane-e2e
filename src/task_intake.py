"""Deterministic text helpers for a synthetic coding exercise."""


def normalize_label(value: str) -> str:
    """Trim and collapse Unicode whitespace without changing letter case."""
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    return " ".join(value.split())


def normalize_labels(values: list[str]) -> list[str]:
    """Return distinct nonempty labels in order, preserving the first spelling."""
    if not isinstance(values, list):
        raise TypeError("values must be a list of strings")

    labels = []
    seen = set()
    for value in values:
        label = normalize_label(value)
        key = label.casefold()
        if label and key not in seen:
            seen.add(key)
            labels.append(label)
    return labels
