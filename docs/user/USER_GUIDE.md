# User Guide — JiuwenSwarm for Jupyter

## Installation

```bash
pip install jiuwenswarm-jupyter
```

This installs the Python package only. The JupyterLab sidebar panel (Phase 2) requires the additional frontend build step described in [PUBLISHING.md](../operations/PUBLISHING.md).

## Loading the extension

### Option A — Load once per session

Add this to the first cell of your notebook:

```python
%load_ext jiuwenswarm_jupyter
```

### Option B — Auto-load on every notebook start

Add to `~/.ipython/profile_default/ipython_config.py`:

```python
c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]
```

If the file does not exist, create it with:

```bash
ipython profile create
```

## Cell magic — `%%jiuwen`

The `%%jiuwen` magic sends the cell body to the agent and streams the response into the cell output area.

### Basic usage

```
%%jiuwen
Explain what the `df` dataframe contains.
```

```
%%jiuwen
What are the most correlated features with the target column?
```

### Agent modes

JiuwenSwarm supports four modes:

| Mode | What it does |
|---|---|
| `agent` (default) | General-purpose reasoning and tool use |
| `code` | Optimised for code generation and execution |
| `team` | Spawns multiple specialised agents working in parallel |
| `code.team` | Team mode, specialised for code tasks |

```
%%jiuwen --mode code
Write a train/test split using stratified sampling on the target column.
```

```
%%jiuwen --mode team
Research the top 3 alternatives to XGBoost for tabular data.
Assign one agent per library, have each benchmark it on the dataset, then
produce a comparison table.
```

### Named sessions

By default, all `%%jiuwen` cells in a notebook share one persistent session — the agent remembers previous exchanges.

Use `--session` to create independent threads:

```
%%jiuwen --session research
Find three papers on feature selection for imbalanced datasets.
```

```
%%jiuwen --session coding
Write the feature selection pipeline based on the research above.
```

Each named session has its own conversation history.

### Skipping context injection

The extension automatically injects a summary of your notebook variables and recent cell history into each request. Disable this for a clean prompt:

```
%%jiuwen --no-context
What is the capital of France?
```

### Timeout

```
%%jiuwen --timeout 600
Run a full hyperparameter search across 5 models and summarise the results.
```

## Line magic — `%jiuwen`

For short single-line queries:

```python
%jiuwen What is the shape of df?
```

## Python API

For programmatic use or async notebooks:

```python
from jiuwenswarm_jupyter import JupyterSwarm

swarm = JupyterSwarm(mode="code")
result = await swarm.run("Write a normalisation function for the numeric columns in df")
print(result)
```

The `JupyterSwarm` constructor accepts:
- `mode` — default agent mode (`"agent"`, `"code"`, `"team"`, `"code.team"`)
- `session_id` — explicit session ID (auto-generated as `jupyter_<uuid>` if not set)

`run()` accepts all the same keyword arguments as the magic options.

## Accessing the default session object

When you run `%load_ext jiuwenswarm_jupyter`, a default `JupyterSwarm` instance is placed in `_jiuwen` in the namespace automatically:

```python
print(_jiuwen.session_id)   # jupyter_abc123def456
print(_jiuwen.mode)         # agent
```

---

## Phase 2 — JupyterLab sidebar panel

The sidebar panel requires JupyterLab 4+ and the TypeScript frontend to be built and installed.

### Setup

```bash
cd packages/frontend
npm install && npm run build
cd ../..
pip install -e .
jupyter labextension develop --overwrite .
jupyter lab
```

### Using the panel

When JupyterLab opens in the browser, a JiuwenSwarm icon appears in the left sidebar. Click it to open the chat panel.

- The panel works the same way as `%%jiuwen` — same agent modes, same session persistence, same context injection.
- When a multi-agent team is running, a **Swarm Map** tab opens automatically showing live agent activity.
- The status bar at the bottom of JupyterLab shows connection state and, during a team run, the number of active agents.

### Opening panels from the command palette

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → search "JiuwenSwarm":

- `JiuwenSwarm: Open Chat` — focus the sidebar chat panel
- `JiuwenSwarm: Open Swarm Map` — open the agent activity panel
- `JiuwenSwarm: New Session` — start a fresh conversation

---

## Phase 3 — Notebook-native tools

These three tools are available from any cell as plain Python functions — no magic needed.

### `read_variable(name)`

Inspect any variable currently in your notebook:

```python
from jiuwenswarm_jupyter import read_variable

print(read_variable("df"))
# DataFrame shape=(10000, 15)
# dtypes: age:int64, income:float64, target:int64, ...
# First 5 rows:
#    age  income  target
# 0   32  55000.0       1
# ...
# Numeric summary:
#         age        income     target
# count  10000.0  10000.0  10000.0
# ...
```

Works with DataFrames, NumPy arrays, lists, dicts, trained models, and any other Python object.

### `read_notebook_cell(cell_index)`

Read the source and output of any previously executed cell:

```python
from jiuwenswarm_jupyter import read_notebook_cell

info = read_notebook_cell(2)
print(info["source"])   # the code you wrote in cell 2
print(info["output"])   # what it printed or returned
```

Useful when you want to ask the agent about something you ran earlier without copy-pasting.

### `insert_notebook_cell(source, cell_type, execute)`

Insert a new cell into the notebook:

```python
from jiuwenswarm_jupyter import insert_notebook_cell

insert_notebook_cell("print(df.describe())", cell_type="code")
```

- In **JupyterLab with the sidebar panel active (Phase 2)**: the cell appears immediately in the notebook.
- In **any other environment (Phase 1)**: the code is displayed as a formatted block in the output area so you can copy and run it.

### When the agent uses these tools

When running a `%%jiuwen` cell, the agent can call these tools itself if it decides it needs to look at a variable or a cell more closely.  It will do this automatically — you do not need to tell it.

---

## Configuration

JiuwenSwarm reads its configuration from `~/.jiuwenswarm/config/config.yaml`. This is the same file used by the CLI, VS Code plugin, and JetBrains plugin — no separate Jupyter configuration is needed.

## Troubleshooting

**`ImportError: jiuwenswarm is not installed`**
Install the core package: `pip install jiuwenswarm`

**Magic not found after `%load_ext jiuwenswarm_jupyter`**
Restart the kernel and try again.

**Response times out**
Increase the timeout: `%%jiuwen --timeout 600`

**Agent does not see my DataFrame**
Make sure the DataFrame is assigned to a variable (not anonymous). The context extractor reads from `ip.user_ns`, so `df = pd.read_csv(...)` makes `df` visible but `pd.read_csv(...)` alone does not.

**JupyterLab sidebar icon is not showing**
The TypeScript frontend may not have been built. Run `cd packages/frontend && npm install && npm run build`, then `jupyter labextension develop --overwrite .` and restart JupyterLab.

**Sidebar panel says "disconnected"**
The comm target was not registered. Make sure `%load_ext jiuwenswarm_jupyter` runs in the kernel before the sidebar connects. If you opened JupyterLab before running any cells, run `%load_ext jiuwenswarm_jupyter` in any cell and then reload the sidebar.

**`insert_notebook_cell` shows a block instead of inserting**
This is the Phase 1 fallback — the cell cannot be inserted directly unless the JupyterLab sidebar panel is active (Phase 2). Copy the displayed code and paste it into a new cell.
