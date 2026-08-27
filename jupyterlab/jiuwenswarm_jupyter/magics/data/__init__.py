"""Data science magics — EDA, schema, hypothesis, features, leakage, df, SQL, viz, mock, compare."""

from __future__ import annotations

from . import compare, df_magic, eda, features, hypothesis, leakage, mock, schema, sql, viz

__all__ = [
    "register_all",
    "compare",
    "df_magic",
    "eda",
    "features",
    "hypothesis",
    "leakage",
    "mock",
    "schema",
    "sql",
    "viz",
]


def register_all(ip) -> None:
    """Register all data science magics with the given IPython shell."""
    eda.register(ip)
    schema.register(ip)
    hypothesis.register(ip)
    features.register(ip)
    leakage.register(ip)
    df_magic.register(ip)
    sql.register(ip)
    viz.register(ip)
    mock.register(ip)
    compare.register(ip)
