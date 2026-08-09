"""The ``%%jiuwen_guard`` cell magic — design-by-contract for notebook cells."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_guard`` with the given IPython shell."""

    def jiuwen_guard(line: str, cell: str) -> None:
        """Assert pre- and post-conditions around a cell; call the agent on violations.

        Define conditions as Python expressions on the ``pre=`` and ``post=``
        keyword arguments on the magic line.  Both are evaluated in the notebook
        namespace.  If either condition fails (evaluates to ``False`` or raises),
        the agent receives the full context and suggests a fix.

        Arguments
        ---------
        pre=EXPR    Expression that must be True before the cell runs.
        post=EXPR   Expression that must be True after the cell runs.

        Usage::

            %%jiuwen_guard pre="df.notna().all().all()" post="result.shape[0] == df.shape[0]"
            result = df.merge(lookup, on="id")

            %%jiuwen_guard post="model is not None"
            model = train(X_train, y_train)
        """
        import re

        if not cell or not cell.strip():
            print("Usage: %%jiuwen_guard [pre=EXPR] [post=EXPR]\\n<cell code>")
            return

        # Parse pre= and post= from line without shlex to allow arbitrary expressions.
        def _extract(key: str, text: str) -> str | None:
            # Match key="..." or key='...'
            m = re.search(rf'{key}="([^"]*)"', text)
            if m:
                return m.group(1)
            m = re.search(rf"{key}='([^']*)'", text)
            if m:
                return m.group(1)
            return None

        pre_expr = _extract("pre", line)
        post_expr = _extract("post", line)

        violations: list[str] = []

        def _eval_condition(expr: str, label: str) -> bool:
            try:
                result = eval(expr, ip.user_ns)  # noqa: S307
                if not result:
                    violations.append(f"{label} condition FAILED: `{expr}` evaluated to {result!r}")
                    return False
                return True
            except Exception as exc:
                violations.append(f"{label} condition ERROR: `{expr}` raised {type(exc).__name__}: {exc}")
                return False

        # Pre-condition
        pre_ok = True
        if pre_expr:
            pre_ok = _eval_condition(pre_expr, "Pre")
            if pre_ok:
                print(f"[JiuwenSwarm] ✔ Pre-condition passed: {pre_expr}")

        # Execute the cell.
        ip.run_cell(cell)

        # Post-condition
        if post_expr:
            post_ok = _eval_condition(post_expr, "Post")
            if post_ok:
                print(f"[JiuwenSwarm] ✔ Post-condition passed: {post_expr}")

        if not violations:
            return

        # One or more conditions failed — call the agent.
        for v in violations:
            print(f"[JiuwenSwarm] ⚠ {v}")

        violations_str = "\n".join(f"- {v}" for v in violations)
        query = (
            "One or more data-contract conditions failed in my Jupyter notebook. "
            "Please diagnose why the conditions failed and suggest a fix.\n\n"
            + (f"**Pre-condition:** `{pre_expr}`\n" if pre_expr else "")
            + (f"**Post-condition:** `{post_expr}`\n" if post_expr else "")
            + f"\n**Violations:**\n{violations_str}\n\n"
            f"**Cell code:**\n```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=True, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Guard analysis cancelled.")

    ip.register_magic_function(jiuwen_guard, magic_kind="cell", magic_name="jiuwen_guard")
