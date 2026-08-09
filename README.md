# jiuwenswarm-jupyterlab

JiuwenSwarm integration for Jupyter notebooks and JupyterLab.

Run single agents and multi-agent swarms directly inside your notebook workflow — no separate server, no browser tab, no context switching.

## Features

**Works in any Jupyter environment (PyCharm, VS Code, Google Colab, JupyterLab)**
- `%%jiuwen` cell magic — ask the agent a question, get a streamed answer in the output area
- `%jiuwen` line magic — one-liner queries from any cell
- `JupyterSwarm` Python API — programmatic async access to all agent modes
- Notebook context injection — agent sees your variables, DataFrames, imported packages, and recent cell history automatically
- Named sessions — carry conversation across multiple cells
- Multi-agent team mode — spawn parallel agents from a single cell
- `%jiuwen_export` — save conversation history to a markdown file
- `%jiuwen_replay` — continue in a fresh session with recent context replayed
- `%jiuwen_pin` / `%jiuwen_unpin` — pin variables that are always injected into context
- `%jiuwen_chat` — embed the full chat UI directly in a cell output (useful in Colab, Kaggle, classic Notebook)

**JupyterLab sidebar panel (requires JupyterLab 4+)**
- Persistent chat panel in the JupyterLab sidebar — stays open across notebook tabs
- Session list panel with filter and per-notebook grouping
- Swarm map panel — live visualisation of agent team activity
- Status bar indicator — connection state, active agent count, session cost
- Multi-kernel support — switch between notebooks without reconnecting
- Python kernel comm bridge — all messages stay in-process, no external server

**Notebook-native agent tools (all environments)**
- `read_variable(name)` — inspect any Python variable: DataFrames, arrays, models
- `read_notebook_cell(index)` — agent reads any previous cell without copy-pasting
- `insert_notebook_cell(source)` — agent inserts a runnable code cell directly into the notebook
- `replace_notebook_cell(index, source)` — agent rewrites an existing cell with a diff dialog

## Installation

```bash
# Core (cell magic + Python API, works in any Jupyter environment)
pip install jiuwenswarm-jupyter

# Full (includes JupyterLab sidebar panel)
pip install jiuwenswarm-jupyter[lab]
jupyter labextension develop --overwrite .
```

## Quick start

Load the extension:

```python
%load_ext jiuwenswarm_jupyter
```

Use the cell magic:

```
%%jiuwen
Analyse the dataframe `df` and identify the three most correlated features with the target column.
```

Use the Python API:

```python
from jiuwenswarm_jupyter import JupyterSwarm

swarm = JupyterSwarm(mode="code")
result = await swarm.run("Write a preprocessing pipeline for df")
```

Use multi-agent team mode:

```
%%jiuwen --mode team
Research the top 3 open-source alternatives to XGBoost for tabular data.
Assign one agent per library, benchmark each on the attached dataset, and produce a comparison table.
```

Embed the full chat UI in a cell (Colab / Kaggle / classic Notebook):

```python
%jiuwen_chat
```

## Auto-load on notebook start

Add to `~/.ipython/profile_default/ipython_config.py`:

```python
c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]
```

## Configuration

JiuwenSwarm configuration is read from `~/.jiuwenswarm/config/config.yaml` (same as the CLI and IDE plugin). No additional setup is needed if you have already configured JiuwenSwarm.

## Notebook-native tools

Use directly from any cell:

```python
from jiuwenswarm_jupyter import read_variable, read_notebook_cell, insert_notebook_cell

# Inspect a DataFrame
print(read_variable("df"))

# Read what cell 3 produced
print(read_notebook_cell(3))

# Insert a code cell (agent does this automatically when appropriate)
insert_notebook_cell("print(df.describe())")
```

## Magic options

| Option | Default | Description |
|---|---|---|
| `--mode` | `agent` | Agent mode: `agent`, `code`, `team`, `code.team` |
| `--session` | notebook default | Named session; reuse across cells |
| `--no-context` | off | Skip automatic notebook context injection |
| `--timeout` | 300 | Max seconds to wait for a response |

## Examples

See [docs/user/EXAMPLES.md](docs/user/EXAMPLES.md) for real-life scenarios across different environments.

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full breakdown of the component design, the bridge protocol used by the JupyterLab sidebar panel, and how the shared webview HTML files are reused from the IDE plugin.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

## Publishing

See [docs/operations/PUBLISHING.md](docs/operations/PUBLISHING.md).

## License

MIT
