"""The ``%jiuwen_leakage`` line magic — dedicated data leakage detector."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_leakage`` with the given IPython shell."""

    def jiuwen_leakage(line: str) -> None:
        """Scan the notebook for data leakage patterns and report findings.

        Checks for the most dangerous and common leakage types that cause
        optimistic offline metrics but poor production performance:

        - Future-dated features (using data not available at prediction time)
        - Target encoding or label encoding applied before train/test split
        - Preprocessing (scaling, imputation) fitted on combined train+test
        - Test set rows appearing in training calculations (cross-contamination)
        - Temporal ordering violations in cross-validation splits
        - Target variable directly or indirectly encoded in a feature column
        - GroupKFold / stratification applied incorrectly on temporal data

        Usage::

            %jiuwen_leakage
        """
        # Gather executed cells.
        cells: list[str] = []
        try:
            hist = list(ip.history_manager.get_tail(n=60, include_latest=True))
            cells = [src for _, _, src in hist if src.strip()]
        except Exception:
            pass

        if not cells:
            print("[JiuwenSwarm] No executed cells found.")
            return

        # Gather variable names as extra signal.
        skip = {"In", "Out", "get_ipython", "exit", "quit", "_", "__", "___"}
        var_names = [
            n for n in ip.user_ns
            if not n.startswith("_") and n not in skip
        ]

        cells_block = "\n\n".join(
            f"**Cell {i + 1}:**\n```python\n{src.strip()[:600]}\n```"
            for i, src in enumerate(cells)
        )

        query = (
            "You are a senior ML engineer specialising in data leakage detection. "
            "Audit the following notebook cells for every form of data leakage. "
            "For each leakage found:\n"
            "1. State the leakage type (e.g. temporal leakage, target leakage, "
            "train/test contamination).\n"
            "2. Quote the exact lines responsible.\n"
            "3. Explain WHY it is leakage and what it inflates.\n"
            "4. Provide a corrected code snippet.\n"
            "Rate severity: CRITICAL (will cause production failure) / "
            "HIGH (significant metric inflation) / MEDIUM (minor inflation).\n"
            "If no leakage is found, state that clearly.\n\n"
            f"**Namespace variables:** {var_names[:60]}\n\n"
            f"**Executed cells ({len(cells)} total):**\n\n{cells_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print("[JiuwenSwarm] Scanning for data leakage…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Leakage scan cancelled.")

    ip.register_magic_function(jiuwen_leakage, magic_kind="line", magic_name="jiuwen_leakage")
