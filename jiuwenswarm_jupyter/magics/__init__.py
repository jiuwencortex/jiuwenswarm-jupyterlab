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
└── analysis/      — code intelligence, safety, profiling, generation
    ├── explain.py  %%jiuwen_explain
    ├── test_gen.py %%jiuwen_test
    ├── audit.py    %jiuwen_audit
    ├── story.py    %jiuwen_story
    ├── profile.py  %%jiuwen_profile
    ├── guard.py    %%jiuwen_guard
    ├── safe.py     %%jiuwen_safe
    ├── todo.py     %jiuwen_todo
    └── diff.py     %jiuwen_diff

Each leaf module exposes a ``register(ip)`` function.
Each sub-package exposes a ``register_all(ip)`` function.
:func:`register_all` at this level calls everything in order.
"""

from __future__ import annotations

from . import analysis, chat, error, jiuwen, session

__all__ = ["register_all", "jiuwen", "error", "chat", "session", "analysis"]


def register_all(ip) -> None:
    """Register all JiuwenSwarm magics with the given IPython shell."""
    # Core — primary interaction
    jiuwen.register(ip)
    error.register(ip)
    chat.register(ip)

    # Session — conversation lifecycle and context
    session.register_all(ip)

    # Analysis — code intelligence and safety
    analysis.register_all(ip)
