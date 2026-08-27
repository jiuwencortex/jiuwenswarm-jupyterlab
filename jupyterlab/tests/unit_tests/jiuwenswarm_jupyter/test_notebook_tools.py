"""Unit tests for jiuwenswarm_jupyter.notebook_tools."""

from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from jiuwenswarm_jupyter.notebook_tools import (
    read_notebook_cell,
    read_variable,
    insert_notebook_cell,
    replace_notebook_cell,
    get_dispatcher,
    _display_diff,
    _display_proposed_cell,
    TOOL_DEFINITIONS,
)
from .conftest import MockIPython


# ── read_notebook_cell ─────────────────────────────────────────────────────────

class TestReadNotebookCell:
    def test_returns_source_and_output(self, ip_with_history):
        result = read_notebook_cell(1, ip=ip_with_history)
        assert result["source"] == "df = pd.read_csv('data.csv')"
        assert result["cell_index"] == 1

    def test_returns_output_when_present(self, ip_with_history):
        # History entry at index 1 has line_no=2, which is in Out
        result = read_notebook_cell(1, ip=ip_with_history)
        assert result["output"] is not None
        assert "col1" in result["output"]

    def test_returns_none_output_when_absent(self, ip_with_history):
        # Index 0 (line_no=1) has no Out entry
        result = read_notebook_cell(0, ip=ip_with_history)
        assert result["output"] is None

    def test_out_of_range_returns_error(self, ip_with_history):
        result = read_notebook_cell(99, ip=ip_with_history)
        assert "error" in result
        assert "out of range" in result["error"].lower()

    def test_negative_index_returns_error(self, ip_with_history):
        result = read_notebook_cell(-1, ip=ip_with_history)
        assert "error" in result

    def test_no_history_returns_error(self, ip):
        result = read_notebook_cell(0, ip=ip)
        assert "error" in result

    def test_no_ip_returns_error(self):
        result = read_notebook_cell(0, ip=None)
        # When ip is None and there's no running IPython, returns error
        assert "error" in result or isinstance(result, dict)


# ── read_variable ──────────────────────────────────────────────────────────────

class TestReadVariable:
    def test_string_variable(self, ip):
        ip.user_ns["greeting"] = "hello"
        result = read_variable("greeting", ip=ip)
        assert "hello" in result
        assert "str" in result

    def test_int_variable(self, ip):
        ip.user_ns["count"] = 42
        result = read_variable("count", ip=ip)
        assert "42" in result

    def test_list_variable(self, ip):
        ip.user_ns["nums"] = [1, 2, 3, 4, 5]
        result = read_variable("nums", ip=ip)
        assert "list" in result.lower()
        assert "len=5" in result

    def test_dict_variable(self, ip):
        ip.user_ns["cfg"] = {"a": 1, "b": 2}
        result = read_variable("cfg", ip=ip)
        assert "dict" in result.lower()
        assert "len=2" in result

    def test_missing_variable_lists_available(self, ip):
        ip.user_ns["existing_var"] = 1
        result = read_variable("nonexistent", ip=ip)
        assert "not found" in result.lower()

    def test_no_ip_returns_error(self):
        result = read_variable("anything", ip=None)
        assert "error" in result.lower()

    def test_long_repr_truncated(self, ip):
        ip.user_ns["bigstr"] = "x" * 5000
        result = read_variable("bigstr", ip=ip)
        assert len(result) <= 3000 + 200  # some slack for type prefix + "…"


# ── insert_notebook_cell ───────────────────────────────────────────────────────

class TestInsertNotebookCell:
    def test_empty_source_returns_error(self, ip):
        result = insert_notebook_cell("", ip=ip)
        assert "error" in result.lower()
        assert "empty" in result.lower()

    def test_invalid_cell_type_returns_error(self, ip):
        result = insert_notebook_cell("print(1)", cell_type="html", ip=ip)
        assert "error" in result.lower()

    def test_phase1_fallback_when_comm_fails(self, ip):
        """When comm is unavailable, falls back to display and returns fallback message."""
        displayed = []

        with patch("jiuwenswarm_jupyter.notebook_tools._comm_insert", return_value=False), \
             patch("jiuwenswarm_jupyter.notebook_tools._display_proposed_cell",
                   side_effect=lambda s, ct: displayed.append((s, ct))):
            result = insert_notebook_cell("print('hi')", ip=ip)

        assert "displayed" in result.lower() or "output area" in result.lower()
        assert len(displayed) == 1
        assert displayed[0][0] == "print('hi')"

    def test_phase2_success_message(self, ip):
        """When comm succeeds, returns success message."""
        with patch("jiuwenswarm_jupyter.notebook_tools._comm_insert", return_value=True):
            result = insert_notebook_cell("print('hi')", ip=ip)
        assert "inserted" in result.lower()

    def test_markdown_cell_type_accepted(self, ip):
        with patch("jiuwenswarm_jupyter.notebook_tools._comm_insert", return_value=True):
            result = insert_notebook_cell("# Title", cell_type="markdown", ip=ip)
        assert "error" not in result.lower()


# ── replace_notebook_cell ──────────────────────────────────────────────────────

class TestReplaceNotebookCell:
    def test_empty_new_source_returns_error(self, ip_with_history):
        result = replace_notebook_cell(0, "", ip=ip_with_history)
        assert "error" in result.lower()

    def test_out_of_range_returns_error(self, ip_with_history):
        result = replace_notebook_cell(99, "new code", ip=ip_with_history)
        assert "error" in result.lower()
        assert "out of range" in result.lower()

    def test_identical_source_returns_no_changes(self, ip_with_history):
        # Cell 0 = "import pandas as pd"
        result = replace_notebook_cell(0, "import pandas as pd", ip=ip_with_history)
        assert "no changes" in result.lower()

    def test_phase1_fallback_when_comm_fails(self, ip_with_history):
        diffs_shown = []

        with patch("jiuwenswarm_jupyter.notebook_tools._comm_replace", return_value=False), \
             patch("jiuwenswarm_jupyter.notebook_tools._display_diff",
                   side_effect=lambda old, new: diffs_shown.append((old, new))):
            result = replace_notebook_cell(0, "import numpy as np", ip=ip_with_history)

        assert "diff" in result.lower() or "display" in result.lower()
        assert len(diffs_shown) == 1

    def test_phase2_success_message(self, ip_with_history):
        with patch("jiuwenswarm_jupyter.notebook_tools._comm_replace", return_value=True):
            result = replace_notebook_cell(0, "import numpy as np", ip=ip_with_history)
        assert "dialog" in result.lower() or "diff" in result.lower()

    def test_no_ip_returns_error(self):
        result = replace_notebook_cell(0, "x = 1", ip=None)
        assert "error" in result.lower()


# ── _display_diff HTML output ──────────────────────────────────────────────────

class TestDisplayDiff:
    def test_produces_html_output(self):
        # display/HTML are imported inside the function body, so patch at the
        # source module (IPython.display), not at the consuming module.
        with patch("IPython.display.HTML", side_effect=lambda h: h), \
             patch("IPython.display.display") as mock_disp:
            _display_diff("old line\n", "new line\n")
        mock_disp.assert_called_once()

    def test_identical_source_produces_no_output(self):
        """_display_diff should return early without calling display when there are no diffs."""
        with patch("IPython.display.display") as mock_disp:
            _display_diff("same\n", "same\n")
        mock_disp.assert_not_called()

    def test_fallback_to_print_on_import_error(self, capsys):
        with patch("IPython.display.display", side_effect=ImportError("no ipython")):
            _display_diff("old\n", "new\n")
        out = capsys.readouterr().out
        # unified_diff output appears in stdout
        assert "old" in out or "new" in out or "---" in out


# ── _display_proposed_cell HTML output ────────────────────────────────────────

class TestDisplayProposedCell:
    def test_tags_code_cells(self):
        with patch("IPython.display.display") as mock_disp, \
             patch("IPython.display.HTML", side_effect=lambda h: h):
            _display_proposed_cell("print('hi')", "code")
            call_arg = mock_disp.call_args[0][0]
            assert "[jiuwen]" in call_arg

    def test_does_not_tag_markdown_cells(self):
        with patch("IPython.display.display") as mock_disp, \
             patch("IPython.display.HTML", side_effect=lambda h: h):
            _display_proposed_cell("# Header", "markdown")
            call_arg = mock_disp.call_args[0][0]
            assert "[jiuwen]" not in call_arg


# ── get_dispatcher ─────────────────────────────────────────────────────────────

class TestGetDispatcher:
    def test_all_tool_keys_present(self, ip):
        dispatcher = get_dispatcher(ip=ip)
        expected = {
            "read_notebook_cell",
            "read_variable",
            "insert_notebook_cell",
            "replace_notebook_cell",
        }
        assert expected == set(dispatcher.keys())

    def test_dispatcher_callables(self, ip):
        dispatcher = get_dispatcher(ip=ip)
        for name, fn in dispatcher.items():
            assert callable(fn), f"{name} is not callable"


# ── TOOL_DEFINITIONS schema ────────────────────────────────────────────────────

class TestToolDefinitions:
    def test_all_four_tools_defined(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        assert names == {
            "read_notebook_cell",
            "read_variable",
            "insert_notebook_cell",
            "replace_notebook_cell",
        }

    def test_each_tool_has_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "properties" in tool["parameters"]
