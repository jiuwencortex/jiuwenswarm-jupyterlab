"""IPython magics for JiuwenSwarm.

Layout
------
magics/
├── jiuwen.py      %%jiuwen / %jiuwen  — primary query magic
├── error.py       %jiuwen_error       — forward last exception to agent
├── chat.py        %jiuwen_chat        — embedded full chat UI
│
├── session/       — conversation lifecycle, context pinning, persistent memory
│   ├── clear.py   %jiuwen_clear
│   ├── export.py  %jiuwen_export
│   ├── replay.py  %jiuwen_replay
│   ├── pin.py     %jiuwen_pin
│   ├── unpin.py   %jiuwen_unpin
│   └── memory.py  %jiuwen_memory
│
├── analysis/      — understand code: explain, audit, safety, profiling, narrative
│   ├── explain.py  %%jiuwen_explain
│   ├── audit.py    %jiuwen_audit
│   ├── story.py    %jiuwen_story
│   ├── profile.py  %%jiuwen_profile
│   ├── guard.py    %%jiuwen_guard
│   ├── safe.py     %%jiuwen_safe
│   ├── diff.py     %jiuwen_diff
│   └── doc.py      %%jiuwen_doc
│
├── transform/     — rewrite code: fix, optimize, translate, generate tests
│   ├── fix.py        %jiuwen_fix
│   ├── optimize.py   %%jiuwen_optimize
│   ├── translate.py  %%jiuwen_translate
│   ├── test_gen.py   %%jiuwen_test
│   ├── todo.py       %jiuwen_todo
│   └── benchmark.py  %%jiuwen_benchmark
│
├── data/          — data science: EDA, schema, features, SQL, viz, mock, compare
│   ├── eda.py        %jiuwen_eda
│   ├── schema.py     %jiuwen_schema
│   ├── hypothesis.py %jiuwen_hypothesis
│   ├── features.py   %jiuwen_features
│   ├── leakage.py    %jiuwen_leakage
│   ├── df_magic.py   %%jiuwen_df
│   ├── sql.py        %%jiuwen_sql
│   ├── viz.py        %%jiuwen_viz
│   ├── mock.py       %jiuwen_mock
│   └── compare.py    %jiuwen_compare
│
└── workflow/      — experiment lifecycle: tracking, reproduction, model cards, suggestions
    ├── track.py     %jiuwen_track
    ├── reproduce.py %jiuwen_reproduce
    ├── card.py      %jiuwen_card
    └── suggest.py   %jiuwen_suggest

Each leaf module exposes a ``register(ip)`` function.
Each sub-package exposes a ``register_all(ip)`` function.
:func:`register_all` at this level calls everything in order.
"""

from __future__ import annotations

from . import analysis, chat, data, error, jiuwen, session, transform, workflow

__all__ = [
    "register_all",
    "jiuwen",
    "error",
    "chat",
    "session",
    "analysis",
    "transform",
    "data",
    "workflow",
]


def register_all(ip) -> None:
    """Register all JiuwenSwarm magics with the given IPython shell."""
    # Core — primary interaction
    jiuwen.register(ip)
    error.register(ip)
    chat.register(ip)

    # Session — conversation lifecycle and context
    session.register_all(ip)

    # Analysis — understand and narrate code
    analysis.register_all(ip)

    # Transform — rewrite and generate code
    transform.register_all(ip)

    # Data — EDA, features, SQL, viz
    data.register_all(ip)

    # Workflow — experiment tracking, reproduction, model cards
    workflow.register_all(ip)
