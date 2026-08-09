"""The ``%jiuwen_track`` line magic — lightweight in-notebook experiment tracker."""

from __future__ import annotations

import json
import time
from pathlib import Path

_EXPERIMENTS_FILE = Path.home() / ".jiuwenswarm" / "experiments.json"

_KNOWN_MODEL_ATTRS = {
    "sklearn": ("get_params", "classes_", "feature_importances_"),
    "xgboost": ("get_params", "feature_importances_", "best_score"),
    "lightgbm": ("get_params", "feature_importances_"),
    "torch": ("state_dict",),
}


def _load_experiments() -> list[dict]:
    try:
        if _EXPERIMENTS_FILE.exists():
            return json.loads(_EXPERIMENTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_experiments(data: list[dict]) -> None:
    _EXPERIMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _EXPERIMENTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _detect_model(ip) -> dict:
    """Scan the namespace for a trained model and extract its metadata."""
    model_info: dict = {}
    for name, obj in ip.user_ns.items():
        if name.startswith("_"):
            continue
        cls_name = type(obj).__name__
        module = type(obj).__module__ or ""
        # Check for sklearn/xgboost/lightgbm-like objects
        if hasattr(obj, "get_params"):
            try:
                model_info["model_var"] = name
                model_info["model_class"] = cls_name
                model_info["model_module"] = module.split(".")[0]
                model_info["params"] = {
                    k: v for k, v in obj.get_params().items()
                    if not callable(v)
                }
            except Exception:
                model_info["model_var"] = name
                model_info["model_class"] = cls_name
            break
    return model_info


def register(ip) -> None:
    """Register ``%jiuwen_track`` with the given IPython shell."""

    def jiuwen_track(line: str) -> None:
        """Lightweight experiment tracker — log runs, compare, find the best.

        Stores model parameters, metrics, git hash, timestamp, and a note to
        ``~/.jiuwenswarm/experiments.json``.  No server, no UI, no extra
        dependencies beyond what is already in the notebook.

        Commands
        --------
        log              Capture current model + metrics as a new run.
          --metrics "k=v k=v"  Key-value metric pairs (e.g. "auc=0.87 f1=0.82").
          --note TEXT          Free-text note attached to the run.
          --name TEXT          Human-readable run name.
        compare          Print a table of all runs for this notebook.
        best --by METRIC Print the single best run by the given metric.
        delete ID        Remove a run by its numeric ID.

        Usage::

            %jiuwen_track log --metrics "auc=0.87 f1=0.82" --note "log-transform revenue"
            %jiuwen_track log --name "XGB baseline" --metrics "rmse=145.3"
            %jiuwen_track compare
            %jiuwen_track best --by auc
            %jiuwen_track delete 3
        """
        import os
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print("Commands: log [--metrics ...] [--note ...] | compare | best --by METRIC | delete ID")
            return

        cmd = tokens[0].lower()

        # ── log ───────────────────────────────────────────────────────────────
        if cmd == "log":
            metrics: dict[str, float] = {}
            note = ""
            run_name = ""

            i = 1
            while i < len(tokens):
                if tokens[i] == "--metrics" and i + 1 < len(tokens):
                    for pair in tokens[i + 1].split():
                        if "=" in pair:
                            k, _, v = pair.partition("=")
                            try:
                                metrics[k.strip()] = float(v.strip())
                            except ValueError:
                                metrics[k.strip()] = v.strip()
                    i += 2
                elif tokens[i] == "--note" and i + 1 < len(tokens):
                    note = tokens[i + 1]
                    i += 2
                elif tokens[i] == "--name" and i + 1 < len(tokens):
                    run_name = tokens[i + 1]
                    i += 2
                else:
                    i += 1

            # Git hash (best effort)
            git_hash = ""
            try:
                import subprocess
                result = subprocess.run(  # noqa: S603
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True, text=True, cwd=os.getcwd()
                )
                if result.returncode == 0:
                    git_hash = result.stdout.strip()
            except Exception:
                pass

            model_info = _detect_model(ip)
            experiments = _load_experiments()
            run: dict = {
                "id": len(experiments) + 1,
                "name": run_name or f"run-{len(experiments) + 1}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "notebook": os.getcwd(),
                "git_hash": git_hash,
                "metrics": metrics,
                "note": note,
            }
            run.update(model_info)
            experiments.append(run)
            _save_experiments(experiments)

            print(f"[JiuwenSwarm] Run #{run['id']} logged: {run['name']}")
            if metrics:
                print("  Metrics: " + "  ".join(f"{k}={v}" for k, v in metrics.items()))
            if model_info.get("model_class"):
                print(f"  Model: {model_info['model_class']} ({model_info.get('model_module', '')})")
            if git_hash:
                print(f"  Git: {git_hash}")

        # ── compare ───────────────────────────────────────────────────────────
        elif cmd == "compare":
            experiments = _load_experiments()
            if not experiments:
                print("[JiuwenSwarm] No runs logged yet. Use: %jiuwen_track log")
                return
            # Collect all metric keys
            all_metrics: set[str] = set()
            for e in experiments:
                all_metrics.update(e.get("metrics", {}).keys())
            metric_cols = sorted(all_metrics)
            header = f"{'ID':>4}  {'Name':<20}  {'Timestamp':<19}  {'Model':<20}  " + \
                     "  ".join(f"{m:<10}" for m in metric_cols) + "  Note"
            print(header)
            print("-" * len(header))
            for e in experiments:
                metrics_str = "  ".join(
                    f"{e.get('metrics', {}).get(m, '-'):<10}"
                    for m in metric_cols
                )
                model_str = e.get("model_class", "-")[:20]
                print(
                    f"{e['id']:>4}  {e.get('name', ''):<20}  "
                    f"{e.get('timestamp', ''):<19}  {model_str:<20}  "
                    f"{metrics_str}  {e.get('note', '')}"
                )

        # ── best ──────────────────────────────────────────────────────────────
        elif cmd == "best":
            by_metric = "auc"
            i = 1
            while i < len(tokens):
                if tokens[i] == "--by" and i + 1 < len(tokens):
                    by_metric = tokens[i + 1]
                    i += 2
                else:
                    i += 1
            experiments = _load_experiments()
            candidates = [e for e in experiments if by_metric in e.get("metrics", {})]
            if not candidates:
                print(f"[JiuwenSwarm] No runs with metric '{by_metric}' found.")
                return
            best = max(candidates, key=lambda e: float(e["metrics"][by_metric]))
            print(f"[JiuwenSwarm] Best run by {by_metric}:")
            print(json.dumps(best, indent=2))

        # ── delete ────────────────────────────────────────────────────────────
        elif cmd == "delete":
            if len(tokens) < 2:
                print("Usage: %jiuwen_track delete <id>")
                return
            try:
                target_id = int(tokens[1])
            except ValueError:
                print(f"Expected numeric ID, got {tokens[1]!r}")
                return
            experiments = _load_experiments()
            before = len(experiments)
            experiments = [e for e in experiments if e.get("id") != target_id]
            if len(experiments) == before:
                print(f"[JiuwenSwarm] No run with ID {target_id}.")
            else:
                _save_experiments(experiments)
                print(f"[JiuwenSwarm] Run #{target_id} deleted.")

        else:
            print(f"[JiuwenSwarm] Unknown command {cmd!r}. Commands: log | compare | best | delete")

    ip.register_magic_function(jiuwen_track, magic_kind="line", magic_name="jiuwen_track")
