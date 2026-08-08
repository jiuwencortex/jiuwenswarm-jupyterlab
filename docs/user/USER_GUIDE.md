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

## `%jiuwen_config` — per-notebook settings

View or change configuration defaults that apply to all `%%jiuwen` cells in the current notebook:

```
%jiuwen_config                       # show current settings
%jiuwen_config mode=code             # set default agent mode
%jiuwen_config timeout=600           # change default timeout (seconds)
%jiuwen_config inject_context=false  # disable automatic context injection
%jiuwen_config model=gpt-4o          # override model for this notebook
```

| Setting | Default | Description |
|---|---|---|
| `mode` | `agent` | Agent mode: `agent`, `code`, `team`, `code.team` |
| `timeout` | `300` | Request timeout in seconds |
| `inject_context` | `true` | Auto-inject notebook variables and cell history |
| `model` | _(from config.yaml)_ | Override the configured model |

The config is stored in `_jiuwen_config` in the notebook namespace. Individual `%%jiuwen --mode code` flags still override the config for that cell only.

## `%jiuwen_error` — forward last exception to agent

When a cell throws an error, run this immediately after:

```
%jiuwen_error
```

The magic automatically reads the exception traceback and the source of the failing cell, then sends them to the agent. You can add context on the same line:

```
%jiuwen_error explain why the KeyError is raised
%jiuwen_error and also suggest a fix that avoids this for all columns
```

The agent receives the full traceback and the failing cell source — you do not need to copy anything manually.

## `%jiuwen_panel` — interactive control panel

Opens an ipywidgets GUI inside the notebook cell output — dropdowns, sliders, and a text area that replace the `%%jiuwen` flag syntax:

```
%jiuwen_panel
```

Requires `ipywidgets`:

```bash
pip install ipywidgets
```

The panel provides:
- Mode dropdown (`agent` / `code` / `team` / `code.team`)
- Timeout slider (30–3600 seconds)
- Context injection toggle
- Named session field
- Query text area + Send button
- Streaming output rendered in-place

## `%jiuwen_save` — save or restore session

Save the current session ID to a file so it can be shared or restored independently of the automatic restart recovery:

```
%jiuwen_save                       # save to ./jiuwen_session.json
%jiuwen_save path/to/session.json  # save to a specific file
%jiuwen_save load                  # restore from ./jiuwen_session.json
%jiuwen_save load path/to/session.json
```

The conversation history lives on the JiuwenSwarm server, keyed by session ID. Restoring the session ID is enough for the agent to remember the full conversation. Use this to hand off a session between colleagues or machines.

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

### Session persistence across kernel restarts

The session ID is saved to `~/.jiuwenswarm/jupyter_sessions.json` when the extension loads. If you restart the kernel and reload the extension, the same session ID is restored automatically:

```
[jiuwenswarm] Restored session: jupyter_abc123def456
```

The conversation history is kept on the server side and the agent will remember the previous exchange. Restored sessions expire after 30 days.

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

### Sidebar panels

The left sidebar contains three JiuwenSwarm panels (accessible via the sidebar icons or command palette):

| Panel | Description |
|---|---|
| **Chat** (rank 1) | Main conversation panel — same as `%%jiuwen` but interactive |
| **Sessions** (rank 2) | Browse and switch between named sessions; click "+ New" to start one |
| **Skills** (rank 3) | Browse available skills; press ↻ to refresh from the kernel |

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl+Shift+J` | Open the chat panel |
| `Cmd/Ctrl+Shift+N` | Start a new session |

### Opening panels from the command palette

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → search "JiuwenSwarm":

- `JiuwenSwarm: Open Chat` — focus the sidebar chat panel
- `JiuwenSwarm: Open Swarm Map` — open the agent activity panel
- `JiuwenSwarm: New Session` — start a fresh conversation
- `JiuwenSwarm: Open Session List` — open the sessions panel
- `JiuwenSwarm: Open Skills Browser` — open the skills panel

### Agent-generated cell tagging

When the agent inserts a cell via `insert_notebook_cell` and the JupyterLab frontend is active, the cell is tagged with `cell.metadata.jiuwen_generated = true`. In environments without the frontend (Phase 1), inserted code cells start with a `# [jiuwen] Generated by JiuwenSwarm` comment so they remain identifiable.

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

### `insert_notebook_cell(source, cell_type, execute, confirm_execute)`

Insert a new cell into the notebook:

```python
from jiuwenswarm_jupyter import insert_notebook_cell

# Insert and display (user runs manually)
insert_notebook_cell("print(df.describe())", cell_type="code")

# Insert and run immediately (JupyterLab Phase 2 only)
insert_notebook_cell("print(df.describe())", cell_type="code", execute=True)

# Insert and ask before running (shows a dialog in JupyterLab; input() prompt in Phase 1)
insert_notebook_cell(
    "df.drop(columns=['id'], inplace=True)",
    cell_type="code",
    execute=True,
    confirm_execute=True,
)
```

- In **JupyterLab with the sidebar panel active (Phase 2)**: the cell appears immediately in the notebook. With `confirm_execute=True`, a "Run generated cell?" dialog is shown before execution.
- In **any other environment (Phase 1)**: the code is displayed as a formatted block in the output area. With `confirm_execute=True`, the user is prompted via `input()`.

### When the agent uses these tools

When running a `%%jiuwen` cell, the agent can call these tools itself if it decides it needs to look at a variable or a cell more closely.  It will do this automatically — you do not need to tell it.

---

## Configuration

JiuwenSwarm reads its configuration from `~/.jiuwenswarm/config/config.yaml`. This is the same file used by the CLI, VS Code plugin, and JetBrains plugin — no separate Jupyter configuration is needed.

---

## Google Colab

Phase 1 (magic + notebook tools) works in Colab with no extra setup. Phase 2 (JupyterLab sidebar) is not supported — Colab uses its own frontend.

**Setup (first cell of the notebook):**

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
# On first use, run jiuwenswarm-init to create the config file:
!jiuwenswarm-init
%load_ext jiuwenswarm_jupyter
```

After the config is created, subsequent sessions only need:

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
%load_ext jiuwenswarm_jupyter
```

Everything then works as normal: `%%jiuwen`, `%jiuwen`, `%jiuwen_error`, `read_variable()`, `insert_notebook_cell()` (display-block fallback), etc.

> **Note:** `insert_notebook_cell(..., execute=True)` shows the code in the output area in Colab — it cannot insert a runnable cell directly because the Phase 2 frontend is not available.

## JupyterHub

Phase 1 and Phase 3 work on JupyterHub with no changes. For Phase 2 (sidebar panel), the extension must be installed into the shared JupyterLab environment.

**Multi-user isolation:** Each user runs their own kernel and their own in-process `JiuWenSwarm` instance. Sessions are keyed by `os.getcwd()` (per-user home directory), so there is no shared state between users.

**Installing the extension for all users (server admin):**

```bash
pip install jiuwenswarm jiuwenswarm-jupyter
jupyter labextension install @jiuwenswarm/jupyterlab  # after building the frontend
```

Or in the JupyterHub `Dockerfile`:

```dockerfile
RUN pip install jiuwenswarm jiuwenswarm-jupyter && \
    cd /path/to/jiuwenswarm-jupyterlab && \
    npm install && npm run build && \
    pip install -e . && \
    jupyter labextension develop --overwrite .
```

Each user still needs their own `~/.jiuwenswarm/config/config.yaml` (run `jiuwenswarm-init` once per user account).

## Remote Jupyter servers

When connecting to a remote Jupyter server via SSH tunnel or `jupyter lab --ip=0.0.0.0`:

- Phase 1 (`%%jiuwen`) works without any changes — the magic runs in the remote kernel.
- Phase 2 (sidebar): the TypeScript extension runs in your local browser but communicates with the remote kernel via the Jupyter comm protocol, which is automatically tunnelled through the standard Jupyter server WebSocket. No extra ports are needed.
- `JiuWenSwarm` must be installed on the **remote** machine, not the local one.

---

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
