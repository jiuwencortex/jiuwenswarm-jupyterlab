# User Guide — JiuwenSwarm for Jupyter

## Installation

```bash
pip install jiuwenswarm-jupyter
```

The JupyterLab sidebar panel requires the TypeScript frontend to be built. See [PUBLISHING.md](../operations/PUBLISHING.md) for the full build and install steps.

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

After loading, a one-line status message confirms the environment:

- `[JiuwenSwarm] Sidebar connected — JupyterLab comm active.` — the sidebar panel is available and connected to this kernel.
- `[JiuwenSwarm] Running without sidebar — cell insertion will use display blocks.` — the extension loaded but the JupyterLab frontend is not present. All cell magics, notebook tools, and the Python API work normally; `insert_notebook_cell`/`replace_notebook_cell` show output blocks instead of editing the notebook in-place.

---

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

Use `--session` to create independent conversation threads:

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

---

## Line magic — `%jiuwen`

For short single-line queries:

```python
%jiuwen What is the shape of df?
```

---

## `%jiuwen_config` — per-notebook settings

View or change configuration defaults that apply to all `%%jiuwen` cells in the current notebook:

```
%jiuwen_config                       # show current settings
%jiuwen_config mode=code             # set default agent mode
%jiuwen_config timeout=600           # change default timeout (seconds)
%jiuwen_config inject_context=false  # disable automatic context injection
%jiuwen_config model=gpt-4o          # override model for this notebook
%jiuwen_config reset                 # restore all defaults
```

| Setting | Default | Description |
|---|---|---|
| `mode` | `agent` | Agent mode: `agent`, `code`, `team`, `code.team` |
| `timeout` | `300` | Request timeout in seconds |
| `inject_context` | `true` | Auto-inject notebook variables and cell history |
| `model` | _(from config.yaml)_ | Override the configured model |
| `pinned_vars` | `[]` | Variables always injected regardless of other settings |

The config is stored in `_jiuwen_config` in the notebook namespace. Individual `%%jiuwen --mode code` flags still override the config for that cell only.

---

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

---

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

---

## `%jiuwen_clear` — reset conversation context

Start a fresh conversation without restarting the kernel:

```
%jiuwen_clear                  # clear the default session
%jiuwen_clear research         # clear a specific named session
```

`%jiuwen_clear` creates a new session ID and replaces the current entry in the session registry and `_jiuwen`. The agent has no memory of the previous conversation after this point. Named sessions can be cleared individually.

After clearing, the new session ID is printed:

```
[JiuwenSwarm] Default session cleared. New session: jupyter_a1b2c3d4
```

---

## `%jiuwen_export` — save conversation to file

Export the full conversation history of a session to a markdown file in the current directory:

```
%jiuwen_export                              # writes jiuwen_session_<id>.md
%jiuwen_export my_research_notes.md        # explicit filename
%jiuwen_export --session research notes.md # export a named session
```

Each exchange is saved as a numbered section with timestamp, mode, the user query, and the agent response. The file is human-readable markdown — open it in any text editor or Jupyter markdown cell.

---

## `%jiuwen_replay` — continue in a fresh session

Re-send the last N conversation exchanges as context into a brand-new session. Useful when a conversation has drifted off-topic but you want the agent to remember the key results:

```
%jiuwen_replay        # replay last 3 exchanges (default)
%jiuwen_replay 5      # replay last 5 exchanges
```

The original session is not modified. A new default session is created and the replayed context is sent first, so the agent acknowledges the history before you continue.

---

## `%jiuwen_pin` / `%jiuwen_unpin` — always-included variables

Pin specific variables so they are always injected into the agent's context, even when `--no-context` is used or the automatic sweep would skip them:

```
%jiuwen_pin df_train results_dict model     # pin several variables
%jiuwen_unpin df_train                      # remove one from pinned list
%jiuwen_unpin all                           # clear all pinned variables
```

Pinned variables appear in a **Pinned variables** section at the top of the context block, with full type summaries. Useful in large notebooks where the auto-context sweep picks up too many irrelevant variables.

The current pinned list is visible in `%jiuwen_config`:

```
%jiuwen_config
  pinned_vars          = ['df_train', 'model']
```

---

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

## JupyterLab sidebar panel

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
- The status bar at the bottom of JupyterLab shows connection state, active agent count during team runs, accumulated session cost (when API usage is metered), and the active notebook name when multiple kernels are open.
- The **Sessions panel** has a filter input at the top — type to narrow sessions by title across all kernels.

### Sidebar panels

| Panel | Description |
|---|---|
| **Chat** | Main conversation panel — same as `%%jiuwen` but interactive |
| **Sessions** | Browse and switch between sessions; filter by title; click "+ New" to start one |

### Multiple notebooks

You can have several notebooks open at the same time, each with its own kernel. The sidebar handles this automatically:

- When you **switch to a different notebook tab**, the chat panel connects to that tab's kernel. All messages you send go to the focused notebook's agent.
- The **Sessions panel** shows sessions grouped by notebook when more than one kernel is connected. Each group is headed by the notebook filename.
- If a **kernel restarts**, the sidebar re-connects without any manual action.
- When a **notebook is closed**, the sidebar disconnects from that kernel and removes its sessions from the list.

No configuration is needed — just open multiple notebooks normally.

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl+Shift+J` | Open the chat panel |
| `Cmd/Ctrl+Shift+N` | Start a new session |

### Command palette

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → search "JiuwenSwarm":

- `JiuwenSwarm: Open Chat` — focus the sidebar chat panel
- `JiuwenSwarm: Open Swarm Map` — open the agent activity panel
- `JiuwenSwarm: New Session` — start a fresh conversation
- `JiuwenSwarm: Open Session List` — open the sessions panel

---

## Notebook tools

These four functions are available from any cell as plain Python — no magic needed. The agent also calls them automatically when it needs to inspect your notebook state.

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

### `insert_notebook_cell(source, cell_type, execute, confirm_execute)`

Insert a new cell into the notebook:

```python
from jiuwenswarm_jupyter import insert_notebook_cell

# Insert a cell (user runs it manually)
insert_notebook_cell("print(df.describe())", cell_type="code")

# Insert and run immediately
insert_notebook_cell("print(df.describe())", cell_type="code", execute=True)

# Insert and ask for confirmation before running
insert_notebook_cell(
    "df.drop(columns=['id'], inplace=True)",
    cell_type="code",
    execute=True,
    confirm_execute=True,
)
```

In **JupyterLab with the sidebar connected**: the cell appears directly in the notebook. With `confirm_execute=True`, a dialog is shown before execution.

In **other environments** (classic Notebook, Colab, VS Code Notebooks): the source is displayed as a formatted block in the cell output. With `confirm_execute=True`, the user is prompted via `input()`.

### `replace_notebook_cell(cell_index, new_source)`

Rewrite an existing cell, with a before/after diff shown for review before applying:

```python
from jiuwenswarm_jupyter import replace_notebook_cell

replace_notebook_cell(3, "df = df.dropna(subset=['target'])")
```

In **JupyterLab with the sidebar connected**: a diff dialog appears showing the old source (red) and the proposed replacement (green). Click **Apply** to update the cell or **Cancel** to discard.

In **other environments**: a coloured unified diff is rendered in the cell output area. Apply the change manually by editing the cell.

`cell_index` uses the same zero-based execution-history scale as `read_notebook_cell`.

### Agent-generated cell tagging

Cells inserted via `insert_notebook_cell` in JupyterLab are tagged with `cell.metadata.jiuwen_generated = true`. In other environments, inserted code cells start with `# [jiuwen] Generated by JiuwenSwarm` so agent-generated code is identifiable in any Jupyter environment.

---

## Configuration

JiuwenSwarm reads its configuration from `~/.jiuwenswarm/config/config.yaml`. This is the same file used by the CLI, VS Code plugin, and JetBrains plugin — no separate Jupyter configuration is needed.

---

## Google Colab

Cell magics, notebook tools, and the Python API work in Colab with no extra setup. The JupyterLab sidebar is not available — Colab uses its own frontend.

**Setup (first cell of the notebook):**

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
# On first use, create the config file:
!jiuwenswarm-init
%load_ext jiuwenswarm_jupyter
```

After the config is created, subsequent sessions only need:

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
%load_ext jiuwenswarm_jupyter
```

Everything then works as normal: `%%jiuwen`, `%jiuwen`, `%jiuwen_error`, `read_variable()`, etc.

> **Note:** `insert_notebook_cell(..., execute=True)` shows the code in the output area in Colab — direct cell insertion requires the JupyterLab sidebar.

---

## JupyterHub

All cell magics and notebook tools work on JupyterHub with no changes. To use the sidebar panel, install the extension into the shared JupyterLab environment.

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

---

## Remote Jupyter servers

When connecting to a remote Jupyter server via SSH tunnel or `jupyter lab --ip=0.0.0.0`:

- Cell magics work without any changes — they run in the remote kernel.
- The sidebar panel runs in your local browser but communicates with the remote kernel via the Jupyter comm protocol, automatically tunnelled through the standard Jupyter server WebSocket. No extra ports are needed.
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
The cell cannot be inserted directly without the JupyterLab sidebar connected. Copy the displayed code and paste it into a new cell.

**`replace_notebook_cell` shows a diff instead of a dialog**
Same situation — the diff is displayed in the output area. Apply the change manually by editing the cell and re-running it.
