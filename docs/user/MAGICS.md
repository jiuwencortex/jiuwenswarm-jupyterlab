# Magic Reference — JiuwenSwarm for Jupyter

Complete reference for all IPython magics provided by `jiuwenswarm_jupyter`.
Load the extension first:

```python
%load_ext jiuwenswarm_jupyter
```

---

## Quick-reference table

### Core

| Magic | Kind | What it does |
|---|---|---|
| [`%%jiuwen`](#jiuwen--jiuwen) | cell / line | Send a query to the agent, stream the response |
| [`%jiuwen`](#jiuwen--jiuwen) | line | One-line query shorthand |
| [`%jiuwen_error`](#jiuwen_error) | line | Forward the last exception to the agent for debugging |
| [`%jiuwen_chat`](#jiuwen_chat) | line | Embed the full chat UI in a cell output |

### Session

| Magic | Kind | What it does |
|---|---|---|
| [`%jiuwen_clear`](#jiuwen_clear) | line | Reset the conversation session |
| [`%jiuwen_export`](#jiuwen_export) | line | Save conversation history to a markdown file |
| [`%jiuwen_replay`](#jiuwen_replay) | line | Continue in a fresh session with recent context replayed |
| [`%jiuwen_pin`](#jiuwen_pin--jiuwen_unpin) | line | Always inject specific variables into context |
| [`%jiuwen_unpin`](#jiuwen_pin--jiuwen_unpin) | line | Remove variables from the pinned list |
| [`%jiuwen_memory`](#jiuwen_memory) | line | Persistent cross-notebook knowledge base |

### Analysis

*Understand code: explain, audit, safety, profiling, narrative.*

| Magic | Kind | What it does |
|---|---|---|
| [`%%jiuwen_explain`](#jiuwen_explain) | cell | Execute a cell and get an agent-written explanation |
| [`%jiuwen_audit`](#jiuwen_audit) | line | Full notebook health scan — code quality and data science issues |
| [`%jiuwen_story`](#jiuwen_story) | line | Convert executed cells into a narrated blog post, report, or paper |
| [`%%jiuwen_profile`](#jiuwen_profile) | cell | Profile a cell with cProfile and get agent-interpreted analysis |
| [`%%jiuwen_guard`](#jiuwen_guard) | cell | Declare pre/post conditions; agent diagnoses violations automatically |
| [`%%jiuwen_safe`](#jiuwen_safe) | cell | Static side-effect analysis before running a risky cell |
| [`%jiuwen_diff`](#jiuwen_diff) | line | Diff against a git ref and get agent commentary |
| [`%%jiuwen_doc`](#jiuwen_doc) | cell | Generate and insert a complete docstring for any function or class |

### Transform

*Rewrite code: fix errors, optimize, translate, generate tests.*

| Magic | Kind | What it does |
|---|---|---|
| [`%jiuwen_fix`](#jiuwen_fix) | line | Fix the last error by rewriting the failing cell in-place |
| [`%%jiuwen_optimize`](#jiuwen_optimize) | cell | Rewrite a slow cell with vectorized code, replacing it in-place |
| [`%%jiuwen_translate`](#jiuwen_translate) | cell | Translate code to a different data library (polars, dask, spark, …) |
| [`%%jiuwen_test`](#jiuwen_test) | cell | Generate a full pytest test suite for any function or class |
| [`%jiuwen_todo`](#jiuwen_todo) | line | Find TODO/FIXME/stubs and draft implementations |
| [`%%jiuwen_benchmark`](#jiuwen_benchmark) | cell | Benchmark multiple implementations and explain the results |

### Data

| Magic | Kind | What it does |
|---|---|---|
| [`%jiuwen_eda`](#jiuwen_eda) | line | Full automated exploratory data analysis with code cells |
| [`%jiuwen_schema`](#jiuwen_schema) | line | Generate a markdown data dictionary from live DataFrames |
| [`%jiuwen_hypothesis`](#jiuwen_hypothesis) | line | Generate testable statistical hypotheses with code |
| [`%jiuwen_features`](#jiuwen_features) | line | Domain-aware feature engineering suggestions with code |
| [`%jiuwen_leakage`](#jiuwen_leakage) | line | Scan for data leakage across the entire notebook |
| [`%%jiuwen_df`](#jiuwen_df) | cell | Natural-language DataFrame query — generates and runs pandas code |
| [`%%jiuwen_sql`](#jiuwen_sql) | cell | Natural-language SQL query over in-memory DataFrames via DuckDB |
| [`%%jiuwen_viz`](#jiuwen_viz) | cell | Natural-language chart description — generates complete visualization code |
| [`%jiuwen_mock`](#jiuwen_mock) | line | Generate synthetic data that mirrors a real DataFrame's schema |
| [`%jiuwen_compare`](#jiuwen_compare) | line | Statistical comparison and drift report for two DataFrames |

### Workflow

| Magic | Kind | What it does |
|---|---|---|
| [`%jiuwen_track`](#jiuwen_track) | line | Log experiments and compare runs |
| [`%jiuwen_reproduce`](#jiuwen_reproduce) | line | Convert a notebook into a standalone Python script |
| [`%jiuwen_card`](#jiuwen_card) | line | Generate a structured model card for any trained model |
| [`%jiuwen_suggest`](#jiuwen_suggest) | line | Analyze notebook state and propose prioritized next steps |

---

## Core

### `%%jiuwen` / `%jiuwen`

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

### `%jiuwen_error`

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

### `%jiuwen_chat`

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

## Session

### `%jiuwen_clear`

Reset the default or a named session. The agent will have no memory of previous exchanges after this point.

**Examples**

```python
%jiuwen_clear                  # clear default session
%jiuwen_clear research         # clear a named session
```

---

### `%jiuwen_export`

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

### `%jiuwen_replay`

Re-send the last N exchanges into a fresh session as context. The original session is unchanged. The new session receives the replay summary first, then waits for your next message.

**Examples**

```python
%jiuwen_replay        # replay last 3 exchanges (default)
%jiuwen_replay 5      # replay last 5 exchanges
```

---

### `%jiuwen_pin` / `%jiuwen_unpin`

Pin specific variables so they are always included in the agent's context, even when `--no-context` is active or the automatic sweep would skip them.

**Examples**

```python
%jiuwen_pin df_train model scaler
%jiuwen_pin results_dict feature_names
%jiuwen_unpin scaler
%jiuwen_unpin all
```

---

### `%jiuwen_memory`

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
%jiuwen_memory search "XGBoost"
```

```python
%jiuwen_memory list
```

```python
%jiuwen_memory delete 2
```

---

## Analysis

*Understand code: explain, audit, safety, profiling, and narrative output.*

### `%%jiuwen_explain`

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

### `%jiuwen_audit`

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

### `%jiuwen_story`

Read all executed cells in order and ask the agent to produce a flowing document. Output is written to a markdown file and streamed to the cell output simultaneously.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--output PATH` | `jiuwen_story.md` | Destination file |
| `--style STYLE` | `blog` | Writing style: `blog`, `paper`, `tutorial`, `report` |

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

### `%%jiuwen_profile`

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

### `%%jiuwen_guard`

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

### `%%jiuwen_safe`

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

---

### `%jiuwen_diff`

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

---

### `%%jiuwen_doc`

Generate a complete docstring for the function or class in the cell body and insert it in-place. The cell is not executed. Supports numpy, Google, and Sphinx docstring styles.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--style STYLE` | `numpy` | Docstring format: `numpy`, `google`, `sphinx` |
| `--no-replace` | off | Stream the docstring to output instead of updating the cell |

**Examples**

```
%%jiuwen_doc
def compute_roc_auc(y_true, y_prob, pos_label=1):
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(y_true, y_prob)
```

```
%%jiuwen_doc --style google
class DataPipeline:
    def __init__(self, steps):
        self.steps = steps

    def run(self, df):
        for step in self.steps:
            df = step.transform(df)
        return df
```

```
%%jiuwen_doc --style sphinx --no-replace
def rolling_zscore(series, window=30):
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std
```

---

## Transform

*Rewrite code: fix errors, optimize performance, translate between libraries, generate tests.*

### `%jiuwen_fix`

Fix the last Python error by reading the traceback and the source of the failing cell, then asking the agent to rewrite the cell with a corrected version. The fixed cell replaces the original in-place.

**Arguments**

| Argument | Description |
|---|---|
| `HINT` | Optional free-text hint for the agent (e.g. `"the column is str not int"`) |

**Examples**

```python
%jiuwen_fix
```

```python
%jiuwen_fix the customer_id column is string, not integer
```

```python
%jiuwen_fix avoid inplace=True, use assignment instead
```

```python
%jiuwen_fix the merge should be a left join, not inner
```

---

### `%%jiuwen_optimize`

Rewrite the cell body for speed and memory efficiency, replacing the original cell in-place. The agent identifies bottlenecks — `iterrows`, Python loops, redundant copies — and returns a vectorized drop-in replacement.

**Options**

| Flag | Description |
|---|---|
| `--profile` | Run cProfile on the original cell first and include stats in the prompt |
| `--no-replace` | Stream the optimized version to output instead of replacing the cell |

**Examples**

```
%%jiuwen_optimize
for idx, row in df.iterrows():
    df.loc[idx, 'score'] = row['a'] * 2 + row['b']
```

```
%%jiuwen_optimize --profile
result = []
for i in range(len(df)):
    result.append(heavy_transform(df.iloc[i]))
```

```
%%jiuwen_optimize --no-replace
counts = {}
for val in df['category']:
    counts[val] = counts.get(val, 0) + 1
```

---

### `%%jiuwen_translate`

Translate the cell body to a different data-processing library. The agent produces a complete, runnable equivalent and inserts it as a new cell. The original cell is kept.

**Options**

| Flag | Description |
|---|---|
| `--to LIBRARY` | Target library (required): `polars`, `dask`, `spark`, `torch`, `sql`, `modin`, `jax`, `cudf`, `vaex`, `numpy` |

**Examples**

```
%%jiuwen_translate --to polars
df_agg = df.groupby("region").agg({"revenue": "sum", "orders": "count"}).reset_index()
```

```
%%jiuwen_translate --to sql
result = df[df["age"] > 30].sort_values("revenue", ascending=False).head(20)
```

```
%%jiuwen_translate --to dask
result = df.merge(other, on="customer_id").groupby("segment")["amount"].mean()
```

```
%%jiuwen_translate --to spark
pivoted = df.pivot_table(index="month", columns="product", values="revenue", aggfunc="sum")
```

---

### `%%jiuwen_test`

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

### `%jiuwen_todo`

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

---

### `%%jiuwen_benchmark`

Split the cell on `---` separator lines, benchmark each section with `timeit`, print a comparison table with ratios to the fastest implementation, and send the results to the agent for explanation.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--n N` | `1000` | Number of repetitions per timing round |
| `--setup CODE` | `pass` | Setup code executed once before timing (e.g., imports) |

**Examples**

```
%%jiuwen_benchmark --n 500
result = [x**2 for x in range(10000)]
---
import numpy as np
result = np.arange(10000) ** 2
```

```
%%jiuwen_benchmark --setup "import pandas as pd; df = pd.read_parquet('data.parquet')"
merged = df.merge(lookup, on="id")
---
merged = df.join(lookup.set_index("id"), on="id")
```

```
%%jiuwen_benchmark --n 100
# Approach A: iterrows
totals = []
for _, row in df.iterrows():
    totals.append(row["price"] * row["qty"])
---
# Approach B: vectorized
totals = (df["price"] * df["qty"]).tolist()
```

---

## Data

### `%jiuwen_eda`

Profile a DataFrame and generate a full exploratory data analysis as runnable notebook cells. The agent inspects the schema, null rates, distributions, and correlations, then inserts cells covering summary stats, missing value heatmaps, distributions, and outlier detection.

**Options**

| Flag | Description |
|---|---|
| `--target COL` | Flag a label column — agent focuses EDA around it |
| `--quick` | Summary statistics only, no cell insertion |

**Examples**

```python
%jiuwen_eda df
```

```python
%jiuwen_eda df_train --target churn
```

```python
%jiuwen_eda transactions --quick
```

```python
%jiuwen_eda df --target price
```

---

### `%jiuwen_schema`

Auto-profile every column of one or more DataFrames and ask the agent to write a markdown data dictionary. If no DataFrame name is given, all pandas DataFrames in the namespace are included.

**Options**

| Flag | Description |
|---|---|
| `DF_NAME ...` | One or more DataFrame variable names (optional — defaults to all) |
| `--output PATH` | Write the data dictionary to this file |

**Examples**

```python
%jiuwen_schema
```

```python
%jiuwen_schema df_raw
```

```python
%jiuwen_schema df_train df_test --output data_dictionary.md
```

```python
%jiuwen_schema transactions customers
```

---

### `%jiuwen_hypothesis`

Send a DataFrame's summary statistics and null rates to the agent, which generates N testable statistical hypotheses — each with a rationale and complete Python code using scipy or statsmodels.

**Options**

| Flag | Default | Description |
|---|---|---|
| `DF_NAME` | required | DataFrame variable name |
| `--target COL` | none | Focus hypotheses around this label column |
| `--n N` | `8` | Number of hypotheses to generate |

**Examples**

```python
%jiuwen_hypothesis df --target churn
```

```python
%jiuwen_hypothesis sales_df --target revenue --n 10
```

```python
%jiuwen_hypothesis df
```

```python
%jiuwen_hypothesis medical_df --target readmission --n 5
```

---

### `%jiuwen_features`

Profile column semantics (dates, IDs, categoricals, text, numerics) and ask the agent to propose engineered features — each with a rationale and pandas code, inserted as individual runnable cells.

**Options**

| Flag | Default | Description |
|---|---|---|
| `DF_NAME` | required | DataFrame variable name |
| `--target COL` | none | Focus on features likely predictive of this column |
| `--domain TEXT` | none | Domain context e.g. `"telecom churn"`, `"credit risk"` |
| `--n N` | `12` | Number of feature ideas to generate |

**Examples**

```python
%jiuwen_features df --target churn
```

```python
%jiuwen_features df_train --target price --domain "real estate"
```

```python
%jiuwen_features transactions --n 20 --domain "fraud detection"
```

```python
%jiuwen_features clickstream --target conversion --domain "e-commerce" --n 15
```

---

### `%jiuwen_leakage`

Collect all executed cells and variable names, then ask the agent for a dedicated data leakage audit. The agent scans for temporal leakage, target encoding before splits, train/test contamination, and look-ahead bias in time-series workflows.

**Examples**

```python
%jiuwen_leakage
```

Common findings:
- `StandardScaler` fitted on full dataset before train/test split
- Target mean encoding computed before splitting
- `fillna(df['col'].mean())` where mean includes test rows
- A timestamp column derived from a future event leaks into features

---

### `%%jiuwen_df`

Describe a data transformation or query in natural language. The agent reads real column names and dtypes from all DataFrames in the namespace, generates pandas code, inserts it as a new cell, and optionally runs it.

**Options**

| Flag | Description |
|---|---|
| `--df NAME` | Limit context to this DataFrame only |
| `--no-run` | Insert the cell but do not execute it |

**Examples**

```
%%jiuwen_df
Show me the top 10 customers by total revenue, broken down by product category.
```

```
%%jiuwen_df --df transactions
Pivot month as columns, product as rows, and sum of revenue as values.
```

```
%%jiuwen_df --no-run
Compute 7-day and 30-day rolling averages of daily_sales, grouped by store_id.
```

```
%%jiuwen_df
Find all rows where the refund_amount is larger than the original purchase_amount.
```

---

### `%%jiuwen_sql`

Write a natural-language query. The agent generates a DuckDB SQL query that treats your DataFrame variable names as table names, inserts it as a cell, and optionally runs it in-process with no external database required.

**Options**

| Flag | Description |
|---|---|
| `--no-run` | Insert the SQL cell but do not execute it |

**Examples**

```
%%jiuwen_sql
Find the top 5 product categories by average order value, excluding cancelled orders.
```

```
%%jiuwen_sql
Join orders and customers on customer_id, then compute the 90-day retention rate per acquisition channel.
```

```
%%jiuwen_sql --no-run
Window function: rank customers by lifetime value within each country.
```

```
%%jiuwen_sql
Show month-over-month revenue growth as a percentage, ordered by date.
```

---

### `%%jiuwen_viz`

Describe a chart in natural language. The agent detects which plotting library is installed (plotly, seaborn, or matplotlib), generates complete visualization code with proper labels, title, and legend, and optionally runs it.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--lib LIBRARY` | auto-detect | Force a specific library: `plotly`, `seaborn`, `matplotlib` |
| `--no-run` | off | Insert the chart cell but do not execute it |

**Examples**

```
%%jiuwen_viz
Scatter plot of age vs income, coloured by churn label, with a regression line.
```

```
%%jiuwen_viz --lib plotly
Interactive heatmap of the correlation matrix for all numeric columns in df.
```

```
%%jiuwen_viz
Side-by-side box plots of purchase_amount grouped by customer_segment.
```

```
%%jiuwen_viz --lib matplotlib --no-run
Time series of daily_active_users with a 7-day rolling average overlay.
```

---

### `%jiuwen_mock`

Generate a synthetic DataFrame that mirrors the schema of an existing one — matching dtypes, value ranges, cardinality, null rates, and date ranges. The generated code is inserted as a runnable cell. Ideal for unit tests, demos, and sharing notebooks without exposing real data.

**Options**

| Flag | Default | Description |
|---|---|---|
| `DF_NAME` | required | Template DataFrame variable name |
| `--n N` | `100` | Number of rows to generate |
| `--var NAME` | `df_mock` | Variable name for the output DataFrame |
| `--seed N` | `42` | Random seed for reproducibility |

**Examples**

```python
%jiuwen_mock df
```

```python
%jiuwen_mock df_train --n 500 --var df_synthetic
```

```python
%jiuwen_mock transactions --n 1000 --seed 0
```

```python
%jiuwen_mock customers --n 200 --var df_test_customers --seed 7
```

---

### `%jiuwen_compare`

Compare two DataFrames and get a structured drift report. Covers schema changes (added/removed/type-changed columns), statistical drift for numerics, categorical distribution changes, and null rate shifts. Useful for train/test split validation, before/after cleaning checks, and dataset version comparisons.

**Options**

| Flag | Description |
|---|---|
| `DF1 DF2` | Two DataFrame variable names (required, positional) |
| `--target COL` | Focus drift analysis on this label column |

**Examples**

```python
%jiuwen_compare df_train df_test
```

```python
%jiuwen_compare df_v1 df_v2 --target churn
```

```python
%jiuwen_compare raw_df cleaned_df
```

```python
%jiuwen_compare baseline_df current_df --target revenue
```

---

## Workflow

### `%jiuwen_track`

Log experiment results to `~/.jiuwenswarm/experiments.json`. Compare runs, find the best result, or delete individual entries. Automatically captures git commit hash, model hyperparameters (via `get_params()`), and a timestamp for every logged run.

**Commands**

| Command | Description |
|---|---|
| `log MODEL METRICS` | Log an experiment. `MODEL` is a variable name; `METRICS` is `key=value` pairs |
| `compare` | Print all logged runs as a comparison table |
| `best --by METRIC` | Show the run with the highest value of METRIC |
| `delete ID` | Remove a run by its numeric ID |

**Examples**

```python
%jiuwen_track log model accuracy=0.94 f1=0.91 dataset=churn_v3
```

```python
%jiuwen_track log xgb_clf auc=0.88 precision=0.85 recall=0.79
```

```python
%jiuwen_track compare
```

```python
%jiuwen_track best --by auc
```

```python
%jiuwen_track delete 3
```

---

### `%jiuwen_reproduce`

Collect the last 80 executed cells and ask the agent to produce a clean, standalone Python script with proper functions, argument parsing, and a `if __name__ == '__main__'` entry point. The script is saved to disk and ready to run from the command line.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--output PATH` | `reproduce.py` | Where to write the script |
| `--no-argparse` | off | Omit argparse and use hardcoded values instead |

**Examples**

```python
%jiuwen_reproduce
```

```python
%jiuwen_reproduce --output train_model.py
```

```python
%jiuwen_reproduce --output pipeline.py --no-argparse
```

```python
%jiuwen_reproduce --output src/run_experiment.py
```

---

### `%jiuwen_card`

Introspect a trained model and generate a structured model card — covering overview, inputs and outputs, training configuration, evaluation metrics, limitations, and a usage example. Supports sklearn, XGBoost, LightGBM, and any object with a `get_params()` method.

**Options**

| Flag | Default | Description |
|---|---|---|
| `MODEL_VAR` | required | Variable name of the trained model |
| `--output PATH` | `model_card.md` | Where to write the card |
| `--metrics "k=v ..."` | none | Inline evaluation metrics to include (e.g. `"auc=0.91 f1=0.88"`) |

**Examples**

```python
%jiuwen_card model
```

```python
%jiuwen_card clf --metrics "auc=0.91 f1=0.88 precision=0.86"
```

```python
%jiuwen_card xgb_pipeline --output docs/model_card_v2.md
```

```python
%jiuwen_card lgbm_clf --metrics "accuracy=0.94 recall=0.89" --output cards/churn_model.md
```

---

### `%jiuwen_suggest`

Analyze all executed cells, the current variable namespace, and detected DataFrames and models, then propose the next most valuable steps — each with a priority label, rationale, and a runnable code stub inserted as a cell.

**Options**

| Flag | Default | Description |
|---|---|---|
| `--domain TEXT` | none | Domain context e.g. `"fraud detection"`, `"NLP classification"` |
| `--goal TEXT` | none | The end goal e.g. `"production deployment"`, `"Kaggle submission"` |
| `--n N` | `8` | Number of suggestions to produce |

**Examples**

```python
%jiuwen_suggest
```

```python
%jiuwen_suggest --domain "fraud detection"
```

```python
%jiuwen_suggest --goal "production deployment" --n 10
```

```python
%jiuwen_suggest --domain "time series" --goal "forecast next 30 days"
```
