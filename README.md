# jiuwenswarm-jupyterlab

JiuwenSwarm integration for Jupyter notebooks and JupyterLab.

Run single agents and multi-agent swarms directly inside your notebook workflow — no separate server, no browser tab, no context switching.

**Requires:** a JiuwenSwarm config at `~/.jiuwenswarm/config/config.yaml` (created by `jiuwenswarm-init`).

## Features

- `%%jiuwen` / `%jiuwen` magics, `JupyterSwarm` Python API, and `%%jiuwen_explain`/`%%jiuwen_test`/`%%jiuwen_audit` and 40+ more magics
- Notebook context injection — the agent sees your variables, DataFrames, imports, and cell history
- Multi-agent team mode, named sessions, session persistence
- JupyterLab sidebar chat panel + Swarm map (requires JupyterLab 4+ and a built frontend)
- Notebook-native tools: `read_variable`, `read_notebook_cell`, `insert_notebook_cell`, `replace_notebook_cell`
- Works in PyCharm, VS Code, Google Colab, Kaggle, and classic Notebook

## Quick Start

```bash
# 1. Install JiuwenSwarm + the Jupyter integration
pip install jiuwenswarm jiuwenswarm-jupyter

# 2. One-time config
jiuwenswarm-init

# 3. In a notebook:
%load_ext jiuwenswarm_jupyter
%%jiuwen
Analyse the dataframe `df` and identify the three most correlated features.
```

For the JupyterLab sidebar panel, build the TypeScript frontend (see `jupyterlab/publishing/PUBLISHING.md`).

## Documentation

- [User Guide](docs/en/jupyterlab/JupyterLabGuide.md)
- [Magic Reference](docs/en/jupyterlab/JupyterLabMagics.md)
- [Examples](docs/en/jupyterlab/JupyterLabExamples.md)

## Repository layout

```
jupyterlab/          The extension (Python package jiuwenswarm_jupyter + packages/frontend, packages/shared-webview; jupyterlab/publishing/)
docs/                User-facing docs (en + zh)
internal/            Working/design docs (not shipped)
```
