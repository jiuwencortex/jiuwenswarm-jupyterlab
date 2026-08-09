# Magic Reference — JiuwenSwarm for Jupyter

Complete reference for all IPython magics provided by `jiuwenswarm_jupyter`.
Load the extension first:

```python
%load_ext jiuwenswarm_jupyter
```

---

## Quick-reference table

| Magic | Kind | What it does |
|---|---|---|
| [`%%jiuwen`](#jiuwen--jiuwen) | cell / line | Send a query to the agent, stream the response |
| [`%jiuwen`](#jiuwen--jiuwen) | line | One-line query shorthand |
| [`%jiuwen_config`](#jiuwen_config) | line | View and change per-notebook settings |
| [`%jiuwen_error`](#jiuwen_error) | line | Forward the last exception to the agent for debugging |
| [`%%jiuwen_explain`](#jiuwen_explain) | cell | Execute a cell and get an agent-written explanation |
| [`%%jiuwen_test`](#jiuwen_test) | cell | Generate a full pytest test suite for any function or class |
| [`%jiuwen_audit`](#jiuwen_audit) | line | Full notebook health scan — code quality and data science issues |
| [`%jiuwen_story`](#jiuwen_story) | line | Convert executed cells into a narrated blog post, report, or paper |
| [`%%jiuwen_profile`](#jiuwen_profile) | cell | Profile a cell with cProfile and get agent-interpreted analysis |
| [`%%jiuwen_guard`](#jiuwen_guard) | cell | Declare pre/post conditions; agent diagnoses violations automatically |
| [`%jiuwen_memory`](#jiuwen_memory) | line | Persistent cross-notebook knowledge base |
| [`%jiuwen_diff`](#jiuwen_diff) | line | Diff against a git ref and get agent commentary |
| [`%%jiuwen_safe`](#jiuwen_safe) | cell | Static side-effect analysis before running a risky cell |
| [`%jiuwen_todo`](#jiuwen_todo) | line | Find TODO/FIXME/stubs and draft implementations |
| [`%jiuwen_clear`](#jiuwen_clear) | line | Reset the conversation session |
| [`%jiuwen_export`](#jiuwen_export) | line | Save conversation history to a markdown file |
| [`%jiuwen_replay`](#jiuwen_replay) | line | Continue in a fresh session with recent context replayed |
| [`%jiuwen_pin`](#jiuwen_pin--jiuwen_unpin) | line | Always inject specific variables into context |
| [`%jiuwen_unpin`](#jiuwen_pin--jiuwen_unpin) | line | Remove variables from the pinned list |
| [`%jiuwen_chat`](#jiuwen_chat) | line | Embed the full chat UI in a cell output |
| [`%jiuwen_panel`](#jiuwen_panel) | line | Open an ipywidgets GUI panel |

---

## `%%jiuwen` / `%jiuwen`

Send a query to the JiuwenSwarm agent and stream the response into the cell output.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--mode`, `-m` | `agent` | Agent mode: `agent`, `code`, `team`, `code.team` |
| `--session`, `-s` | notebook default | Named session — reuse conversation across cells |
| `--no-context` | off | Skip automatic notebook context injection |
| `--timeout`, `-t` | `300` | Max seconds to wait for a response |

**Examples**

```
%%jiuwen
Explain what the df variable contains and suggest a cleaning strategy.
```

```
%%jiuwen --mode code
Write a train/test split with stratified sampling on the target column.
```

```
%%jiuwen --mode team --session research
Research the top 3 XGBoost alternatives for tabular data. Assign one agent per library,
benchmark each on df, and produce a comparison table.
```

```
%%jiuwen --session eda --no-context
Summarise the key steps in a typical exploratory data analysis workflow.
```

```python
%jiuwen What is the shape of df?
```

---

## `%jiuwen_config`

View and change per-notebook defaults. Settings apply to all subsequent `%%jiuwen` calls in this notebook session.

**Settings**

| Key | Default | Description |
|---|---|---|
| `mode` | `agent` | Default agent mode |
| `timeout` | `300` | Default timeout in seconds |
| `inject_context` | `true` | Auto-inject notebook state |
| `model` | from config.yaml | Override the LLM model |
| `pinned_vars` | `[]` | Variables always included in context |

**Examples**

```python
%jiuwen_config                        # show current settings
%jiuwen_config mode=code              # switch to code mode for all cells
%jiuwen_config timeout=600            # extend default timeout
%jiuwen_config inject_context=false   # disable context for all cells
%jiuwen_config model=gpt-4o           # override model
%jiuwen_config reset                  # restore all defaults
```

---

## `%jiuwen_error`

Forward the last Python exception to the agent for debugging. Reads `sys.last_value` and the source of the failing cell automatically.

**Examples**

```python
%jiuwen_error
```

```python
%jiuwen_error explain why the KeyError is happening and suggest a robust fix
```

```python
%jiuwen_error this is a merge operation — check for dtype mismatches
```

---

## `%%jiuwen_explain`

Execute the cell body in the notebook namespace, then stream an agent-written explanation of what the code did and what the output means. Produces prose suitable for inserting as a markdown narrative cell.

**Examples**

```
%%jiuwen_explain
model.fit(X_train, y_train)
print(f"Train score: {model.score(X_train, y_train):.3f}")
print(f"Test score:  {model.score(X_test, y_test):.3f}")
```

```
%%jiuwen_explain
df = (
    df.groupby("region")
      .agg(revenue=("amount", "sum"), orders=("order_id", "nunique"))
      .reset_index()
)
df.head()
```

```
%%jiuwen_explain
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
print(pca.explained_variance_ratio_)
```

---

## `%%jiuwen_test`

Read the cell body as source and ask the agent to write a complete pytest test suite — normal cases, edge cases, and expected failures. The cell is not executed.

**Options**

| Flag | Description |
|---|---|
| `--file PATH` | Write tests to this file instead of inserting a new cell |

**Examples**

```
%%jiuwen_test
def normalize(df, cols):
    return (df[cols] - df[cols].mean()) / df[cols].std()
```

```
%%jiuwen_test
def split_dataset(df, target, test_size=0.2, seed=42):
    from sklearn.model_selection import train_test_split
    X = df.drop(columns=[target])
    y = df[target]
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=seed)
```

```
%%jiuwen_test --file tests/test_features.py
class FeatureEncoder:
    def fit(self, df): ...
    def transform(self, df): ...
    def fit_transform(self, df): ...
```

---

## `%jiuwen_audit`

Collect all executed cells and the current namespace, then request a structured health scan from the agent. The agent checks for code quality problems, data science anti-patterns, and potential runtime failures.

**Options**

| Flag | Description |
|---|---|
| `--quick` | Bullet-point summary only, no code quotes |

**Examples**

```python
%jiuwen_audit
```

```python
%jiuwen_audit --quick
```

The agent checks for:
- Dead or unreachable code
- Unused imports
- Data leakage between train and test splits
- Operations that may silently fail on unseen data (dtype mismatches, nulls)
- Hardcoded paths and magic numbers
- Out-of-order execution dependencies
- Memory-heavy patterns (`iterrows`, full copies of large DataFrames)
- Missing error handling at I/O boundaries

---

## `%jiuwen_story`

Read all executed cells in order and ask the agent to produce a flowing document. Output is written to a markdown file and streamed to the cell output simultaneously.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--output PATH` | `jiuwen_story.md` | Destination file |
| `--style STYLE` | `blog` | Writing style (see table below) |

| Style | Output |
|---|---|
| `blog` | Conversational, first-person technical narrative |
| `paper` | Abstract, intro, methodology, results, conclusion |
| `tutorial` | Step-by-step guide; prose before each code block |
| `report` | Executive summary, findings, recommendations |

**Examples**

```python
%jiuwen_story
```

```python
%jiuwen_story --output customer_churn_analysis.md
```

```python
%jiuwen_story --style report --output q3_fraud_findings.md
```

```python
%jiuwen_story --style tutorial --output how_to_train_xgboost.md
```

---

## `%%jiuwen_profile`

Execute the cell under `cProfile`, print the raw profile stats, then send the top slowest call sites to the agent for bottleneck diagnosis and optimisation suggestions.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--top N` | `20` | Number of slowest functions to include |

**Examples**

```
%%jiuwen_profile
for row in df.iterrows():
    result.append(transform(row))
```

```
%%jiuwen_profile --top 30
similarities = [cosine_similarity(query, doc) for doc in corpus]
```

```
%%jiuwen_profile
X_scaled = scaler.fit_transform(X_train)
model.fit(X_scaled, y_train)
```

---

## `%%jiuwen_guard`

Declare pre- and post-conditions as Python expressions. Conditions are evaluated in the notebook namespace before and after the cell runs. On any violation the agent receives the failing expression, the cell source, and the current context, and diagnoses what went wrong.

**Arguments** (on the `%%` line)

| Argument | Description |
|---|---|
| `pre="EXPR"` | Expression that must be True before execution |
| `post="EXPR"` | Expression that must be True after execution |

**Examples**

```
%%jiuwen_guard pre="df.notna().all().all()" post="result.shape[0] == df.shape[0]"
result = df.merge(lookup_table, on="customer_id")
```

```
%%jiuwen_guard post="model is not None"
model = build_and_train(X_train, y_train, config)
```

```
%%jiuwen_guard pre="len(df) >= 500" post="0.0 <= accuracy <= 1.0"
accuracy = evaluate_model(model, X_test, y_test)
```

```
%%jiuwen_guard pre="'target' in df.columns" post="df['target'].notna().all()"
df['target'] = df['raw_label'].map(label_map)
```

---

## `%jiuwen_memory`

Persistent cross-notebook knowledge base stored in `~/.jiuwenswarm/memory.json`. Notes survive kernel restarts and notebook closures. The `search` command retrieves matching notes and sends them to the agent as context.

**Commands**

| Command | Description |
|---|---|
| `save "NOTE"` | Save a plain-text note |
| `search "QUERY"` | Find matching notes and pass them to the agent |
| `list` | Print all saved notes |
| `delete ID` | Remove a note by its numeric ID |
| `clear` | Delete all saved notes |

**Examples**

```python
%jiuwen_memory save "Validation AUC plateaus after 200 XGBoost trees on this dataset"
```

```python
%jiuwen_memory save "The customer_id merge drops ~3% of rows — known data quality issue in raw feed"
```

```python
%jiuwen_memory save "Best preprocessing: log-transform revenue, cap age at 80, impute income with median"
```

```python
%jiuwen_memory search "XGBoost"
```

```python
%jiuwen_memory search "data quality merge"
```

```python
%jiuwen_memory list
```

```python
%jiuwen_memory delete 2
```

---

## `%jiuwen_diff`

Run `git diff` against a reference and send the output to the agent for a structured review. The raw diff is printed first; the agent's commentary follows.

**Arguments**

| Argument | Default | Description |
|---|---|---|
| `REF` | `HEAD` | Git reference: `HEAD~N`, branch name, commit hash |
| `--stat` | off | Summary diff only (no full patch) |
| `--file PATH` | all files | Limit diff to one file |

**Examples**

```python
%jiuwen_diff
```

```python
%jiuwen_diff HEAD~3
```

```python
%jiuwen_diff main --stat
```

```python
%jiuwen_diff HEAD~1 --file src/features.py
```

```python
%jiuwen_diff feature/new-model
```

---

## `%%jiuwen_safe`

Send the cell body to the agent for static side-effect analysis **without executing it**. The agent reports files written, network calls, data mutations, non-reversible operations, and exception paths, then delivers a `SAFE / CAUTION / HIGH RISK` verdict.

**Options**

| Flag | Description |
|---|---|
| `--run` | Execute the cell immediately after the analysis completes |

**Examples**

```
%%jiuwen_safe
os.remove("data/raw/customer_pii.csv")
shutil.rmtree("output/")
```

```
%%jiuwen_safe
conn.execute("DROP TABLE IF EXISTS staging_results")
df_final.to_sql("results", conn, if_exists="replace", index=False)
```

```
%%jiuwen_safe --run
df.to_parquet("processed/features_v3.parquet", index=False)
```

```
%%jiuwen_safe
import subprocess
subprocess.run(["rsync", "-av", "output/", "s3://prod-bucket/results/"])
```

---

## `%jiuwen_todo`

Scan every executed cell for `# TODO`, `# FIXME`, `# HACK`, `# XXX`, `raise NotImplementedError`, and bare `pass` statements. Sends the full list to the agent, which drafts a concrete implementation for each item and inserts them as runnable code cells.

**Options**

| Flag | Description |
|---|---|
| `--list` | Print found items only — do not call the agent |

**Examples**

```python
%jiuwen_todo
```

```python
%jiuwen_todo --list
```

Use in a notebook that contains stubs like:

```python
def load_features(path):
    # TODO: add validation for column names
    pass

def evaluate(model, X_test, y_test):
    # FIXME: handle multi-class case
    raise NotImplementedError
```

Running `%jiuwen_todo` finds both items, sends them to the agent with their surrounding cell context, and inserts complete implementations as new cells.

---

## `%jiuwen_clear`

Reset the default or a named session. The agent will have no memory of previous exchanges after this point.

**Examples**

```python
%jiuwen_clear                  # clear default session
%jiuwen_clear research         # clear a named session
```

---

## `%jiuwen_export`

Save the full conversation history of a session to a markdown file. Each exchange is saved with a timestamp, mode, user query, and agent response.

**Options**

| Flag | Description |
|---|---|
| `--session NAME`, `-s NAME` | Export a named session instead of the default |
| `FILENAME` | Output file (default: `jiuwen_session_<id>.md`) |

**Examples**

```python
%jiuwen_export
```

```python
%jiuwen_export eda_session_notes.md
```

```python
%jiuwen_export --session research paper_notes.md
```

---

## `%jiuwen_replay`

Re-send the last N exchanges into a fresh session as context. The original session is unchanged. The new session receives the replay summary first, then waits for your next message.

**Examples**

```python
%jiuwen_replay        # replay last 3 exchanges (default)
%jiuwen_replay 5      # replay last 5 exchanges
```

---

## `%jiuwen_pin` / `%jiuwen_unpin`

Pin specific variables so they are always included in the agent's context, even when `--no-context` is active or the automatic sweep would skip them.

**Examples**

```python
%jiuwen_pin df_train model scaler
%jiuwen_pin results_dict feature_names
%jiuwen_unpin scaler
%jiuwen_unpin all
```

---

## `%jiuwen_chat`

Embed the full JiuwenSwarm chat UI as an iframe in the cell output. The iframe connects to the running kernel via the Jupyter comm API. Session, context injection, and agent modes all work identically to `%%jiuwen`.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--height PX` | `520` | Iframe height in pixels |

**Examples**

```python
%jiuwen_chat
```

```python
%jiuwen_chat --height 700
```

Best used in Google Colab, Kaggle Notebooks, and classic Jupyter Notebook where the JupyterLab sidebar panel is not available.

---

## `%jiuwen_panel`

Open an ipywidgets GUI panel inside the cell output. Provides dropdowns, sliders, and a text area as an alternative to typing `%%jiuwen` flag arguments manually. Requires `pip install ipywidgets`.

**Example**

```python
%jiuwen_panel
```

The panel provides:
- Mode dropdown (`agent` / `code` / `team` / `code.team`)
- Timeout slider
- Context injection toggle
- Named session field
- Query text area and Send button
- Streaming output rendered in-place
