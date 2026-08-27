"""The ``%jiuwen_card`` line magic — auto-generate a model card for a trained model."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_card`` with the given IPython shell."""

    def jiuwen_card(line: str) -> None:
        """Inspect a trained model and generate a structured model card.

        Reads the model object from the namespace — parameters, feature names,
        training environment, evaluation metrics if present — and writes a
        markdown model card documenting intended use, inputs/outputs, performance,
        and known limitations.

        Arguments
        ---------
        MODEL_VAR      Variable name of the trained model (required).
        --output PATH  Write the card to this file (default: model_card.md).
        --metrics "k=v ..."  Evaluation metrics to include (supplementary).

        Usage::

            %jiuwen_card model
            %jiuwen_card clf --output docs/model_card.md
            %jiuwen_card pipeline --metrics "auc=0.91 f1=0.88 precision=0.86"
        """
        import os
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print("Usage: %jiuwen_card <model_var> [--output PATH] [--metrics 'k=v ...']")
            return

        model_var: str | None = None
        output_file = "model_card.md"
        extra_metrics: dict[str, str] = {}

        i = 0
        while i < len(tokens):
            if tokens[i] == "--output" and i + 1 < len(tokens):
                output_file = tokens[i + 1]
                i += 2
            elif tokens[i] == "--metrics" and i + 1 < len(tokens):
                for pair in tokens[i + 1].split():
                    if "=" in pair:
                        k, _, v = pair.partition("=")
                        extra_metrics[k.strip()] = v.strip()
                i += 2
            elif not tokens[i].startswith("--"):
                model_var = tokens[i]
                i += 1
            else:
                i += 1

        if model_var is None:
            print("Usage: %jiuwen_card <model_var> [--output PATH]")
            return

        model = ip.user_ns.get(model_var)
        if model is None:
            print(f"[JiuwenSwarm] Variable '{model_var}' not found in the namespace.")
            return

        # Extract model metadata.
        cls_name = type(model).__name__
        module = (type(model).__module__ or "").split(".")[0]
        metadata: dict = {"class": cls_name, "module": module}

        if hasattr(model, "get_params"):
            try:
                metadata["params"] = {
                    k: v for k, v in model.get_params().items() if not callable(v)
                }
            except Exception:
                pass

        if hasattr(model, "feature_names_in_"):
            try:
                metadata["feature_names"] = list(model.feature_names_in_)
            except Exception:
                pass
        elif hasattr(model, "feature_name_"):
            try:
                metadata["feature_names"] = list(model.feature_name_())
            except Exception:
                pass

        if hasattr(model, "classes_"):
            try:
                metadata["classes"] = list(model.classes_)
            except Exception:
                pass

        if hasattr(model, "n_features_in_"):
            metadata["n_features"] = int(model.n_features_in_)

        if extra_metrics:
            metadata["metrics"] = extra_metrics

        dest = os.path.join(os.getcwd(), output_file)

        query = (
            f"Generate a structured model card for the following trained model. "
            "Use this markdown structure:\n"
            "# Model Card — {model class}\n"
            "## Model Overview\n"
            "## Intended Use\n"
            "## Inputs and Outputs\n"
            "## Training Configuration\n"
            "## Evaluation Metrics\n"
            "## Known Limitations and Risks\n"
            "## How to Load and Use\n\n"
            "Fill in each section with the information available from the metadata below. "
            "For sections where information is not available (e.g. fairness analysis), "
            "note what additional evaluation is recommended. "
            f"Save the card to `{dest}` and also insert it as a markdown cell "
            "using `insert_notebook_cell`.\n\n"
            f"**Model variable:** `{model_var}`\n"
            f"**Metadata:**\n```json\n"
            + __import__("json").dumps(metadata, indent=2, default=str)
            + "\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating model card for `{model_var}` → {dest}")
        try:
            response = swarm.run_sync(query, inject_context=False, ip=ip)
            if response and not os.path.exists(dest):
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(response)
                print(f"[JiuwenSwarm] Model card saved to {dest}")
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Model card generation cancelled.")

    ip.register_magic_function(jiuwen_card, magic_kind="line", magic_name="jiuwen_card")
