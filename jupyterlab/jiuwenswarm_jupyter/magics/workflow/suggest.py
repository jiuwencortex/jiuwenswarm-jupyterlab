"""The ``%jiuwen_suggest`` line magic — propose next steps from notebook state."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_suggest`` with the given IPython shell."""

    def jiuwen_suggest(line: str) -> None:
        """Analyze the current notebook state and propose the next logical steps.

        Reads all executed cells, the current variable namespace, and DataFrame
        schemas to understand where the project stands. Returns a prioritized list
        of recommended next actions with rationale and code stubs inserted as cells.

        Arguments
        ---------
        --domain TEXT  Domain hint e.g. "churn prediction", "NLP classification".
        --goal TEXT    The end goal e.g. "production deployment", "Kaggle submission".
        --n N          Number of suggestions to produce (default: 8).

        Usage::

            %jiuwen_suggest
            %jiuwen_suggest --domain "fraud detection"
            %jiuwen_suggest --goal "production deployment" --n 10
            %jiuwen_suggest --domain "time series" --goal "forecast next 30 days"
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []

        domain: str | None = None
        goal: str | None = None
        n_suggestions = 8

        i = 0
        while i < len(tokens):
            if tokens[i] == "--domain" and i + 1 < len(tokens):
                domain = tokens[i + 1]
                i += 2
            elif tokens[i] == "--goal" and i + 1 < len(tokens):
                goal = tokens[i + 1]
                i += 2
            elif tokens[i] == "--n" and i + 1 < len(tokens):
                try:
                    n_suggestions = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1

        # Executed cell history (last 40)
        try:
            history = list(ip.history_manager.get_range(output=False))[-40:]
            cells = [src for _, _, src in history if src.strip()]
        except Exception:
            cells = []

        # Namespace snapshot: DataFrames and models
        try:
            import pandas as pd

            dfs = {
                k: v
                for k, v in ip.user_ns.items()
                if isinstance(v, pd.DataFrame) and not k.startswith("_")
            }
            df_summary = "\n".join(
                f"  {k}: shape={v.shape}, cols={list(v.columns)[:10]}"
                for k, v in list(dfs.items())[:10]
            )
        except Exception:
            df_summary = "  (could not inspect namespace)"

        # Detect trained models
        model_names: list[str] = []
        for k, v in ip.user_ns.items():
            if k.startswith("_"):
                continue
            if hasattr(v, "predict") or hasattr(v, "fit"):
                model_names.append(k)

        domain_note = f"\nDomain: {domain}." if domain else ""
        goal_note = f"\nEnd goal: {goal}." if goal else ""
        model_note = f"\nTrained models in namespace: {model_names}." if model_names else ""

        cell_digest = "\n---\n".join(cells[-20:])

        query = (
            f"Analyze this Jupyter notebook and propose the {n_suggestions} most valuable next steps."
            f"{domain_note}{goal_note}{model_note}\n\n"
            "For each suggestion output:\n"
            "1. **Title** and priority label: `[HIGH]` / `[MEDIUM]` / `[LOW]`\n"
            "2. One-sentence rationale (why this step matters now)\n"
            "3. A concrete starter — either `insert_notebook_cell` with runnable code "
            "or a specific tool/method to call.\n\n"
            "Consider gaps in: EDA, data validation, feature engineering, model evaluation, "
            "cross-validation, hyperparameter tuning, leakage checks, reproducibility, "
            "and deployment readiness.\n\n"
            f"**DataFrames in namespace:**\n{df_summary}\n\n"
            "**Last 20 executed cells:**\n"
            f"{cell_digest}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Analyzing notebook state, generating {n_suggestions} suggestions…")
        try:
            swarm.run_sync(query, inject_context=True, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Suggestion cancelled.")

    ip.register_magic_function(jiuwen_suggest, magic_kind="line", magic_name="jiuwen_suggest")
