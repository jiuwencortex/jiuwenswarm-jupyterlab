# Real-Life Examples — JiuwenSwarm for Jupyter

These examples show what actually happens when you use JiuwenSwarm in a notebook.
They are written as stories: what you do, what you type, and what you get back.

**Runnable version:** [`examples/examples.ipynb`](../../examples/examples.ipynb) contains
all examples as executable cells with synthetic data — no external files required.

---

## Before you start — what needs to be installed

**You do not need to run `jiuwenswarm-start`.** This is the key difference from the IDE plugin.

### How the IDE plugin works vs how this works

The IDE plugin (VS Code, JetBrains) connects to a JiuwenSwarm **server** that you start with `jiuwenswarm-start`. That server runs as a separate process, manages the web UI, listens on channels (Slack, Discord, etc.), and exposes a WebSocket endpoint that the IDE plugin connects to. If the server is not running, the plugin shows "disconnected" and cannot do anything.

The Jupyter integration works completely differently. `JiuWenSwarm` is also a Python class — and when you `pip install jiuwenswarm`, that class is available as a regular library. When you load the extension in a notebook, it instantiates `JiuWenSwarm()` directly inside the notebook's Python process. The agent runtime starts up inside the kernel — no separate process, no port, no WebSocket. The same thing that `jiuwenswarm-start` does for the server, the notebook kernel does for itself, on demand.

Think of it like this:
- **`jiuwenswarm-start`** = starts a production server with everything: web UI, all channels, WebSocket for IDE, multi-user sessions
- **`%load_ext jiuwenswarm_jupyter`** = boots just the agent runtime inside your notebook's Python process, nothing else

### What you need

```bash
# 1. Install JiuwenSwarm and the Jupyter integration
pip install jiuwenswarm jiuwenswarm-jupyter

# 2. One-time workspace setup (only needed once per machine)
#    Creates ~/.jiuwenswarm/ with default config and directory structure
jiuwenswarm-init

# 3. Add your API keys to ~/.jiuwenswarm/config/.env
#    (same file used by the CLI and IDE plugin — skip this if you already did it)
```

That is all. After this, `%load_ext jiuwenswarm_jupyter` in any notebook starts the agent inside the kernel. No server to start, no port to check, nothing running in the background.

**Which parts need what:**

| What you want to use | What you need |
|---|---|
| `%%jiuwen` magic, `%jiuwen`, Python API, notebook tools | `pip install` + `jiuwenswarm-init` (one-time) |
| JupyterLab sidebar chat panel, swarm map | The above + build the TypeScript frontend (see [PUBLISHING.md](../operations/PUBLISHING.md)) |

The examples below all work with just `pip install` + `jiuwenswarm-init`. You do not need to build anything for them.

---

## Example 1 — Understanding a dataset (JupyterLab in Chrome)

**Who:** A data scientist who just received a CSV file from a client and wants to understand it quickly.

**Where:** JupyterLab open in Chrome at `localhost:8888`.

---

You open a new notebook. In the first cell you write:

```python
import pandas as pd
df = pd.read_csv("customer_churn.csv")
%load_ext jiuwenswarm_jupyter
```

You run it. The extension loads silently in the background.

Now in the next cell you write:

```
%%jiuwen
What does this dataset contain? How many rows and columns?
Are there any obvious data quality issues I should know about before I start?
```

You press **Shift+Enter**.

Immediately below the cell, text starts appearing in real time — you do not have to wait for the whole answer before reading:

> The dataset `df` has **10,847 rows and 21 columns**.
>
> Looking at the column names and types, it appears to be a customer churn dataset with:
> - Demographics: `age`, `gender`, `tenure_months`
> - Usage metrics: `monthly_charges`, `total_charges`, `num_products`
> - Support history: `num_support_tickets`, `last_complaint_date`
> - Target: `churned` (0/1)
>
> **Data quality issues I can see:**
> 1. `total_charges` has 11 missing values — likely new customers with no billing history yet
> 2. `last_complaint_date` is stored as a string, not a date — you will need to parse it
> 3. `monthly_charges` has a few extreme values above $500 — worth checking if these are data errors or legitimate enterprise accounts
>
> No duplicate rows detected. Class balance: 26% churned, 74% retained.

You did not tell the agent anything about the file. It figured all of this out by reading the `df` variable you loaded in the previous cell.

---

## Example 2 — Writing code you can run (JupyterLab in Chrome)

**Who:** Same data scientist, continuing from Example 1.

**Where:** Same notebook.

---

You add a new cell and type:

```
%%jiuwen --mode code
Fix the two issues you mentioned:
1. Fill the missing total_charges values
2. Convert last_complaint_date to a proper datetime column
Write the code so I can run it right away.
```

The agent responds. In the output area you see a code block appear:

```python
# Fill missing total_charges with 0 (new customers have no charges yet)
df["total_charges"] = df["total_charges"].fillna(0)

# Convert last_complaint_date from string to datetime
df["last_complaint_date"] = pd.to_datetime(df["last_complaint_date"], errors="coerce")

print("Missing values remaining:", df[["total_charges", "last_complaint_date"]].isnull().sum().to_dict())
print("last_complaint_date dtype:", df["last_complaint_date"].dtype)
```

You copy this into a new cell and run it. The output shows:

```
Missing values remaining: {'total_charges': 0, 'last_complaint_date': 0}
last_complaint_date dtype: datetime64[ns]
```

Both issues are fixed.

---

## Example 3 — The agent inserts the code cell for you (JupyterLab with sidebar panel)

**Who:** Same scenario as Example 2, but you have the JupyterLab sidebar panel installed.

**Where:** JupyterLab in Chrome, sidebar chat panel open on the left.

**Setup required (one-time):** The sidebar panel is not included in the basic `pip install`. You need to build the TypeScript frontend once:

```bash
cd packages/frontend && npm install && npm run build
cd ../..
pip install -e .
jupyter labextension develop --overwrite .
```

After this, restart JupyterLab and the icon appears. Examples 1 and 2 work without any of this.

---

You click the JiuwenSwarm icon in the left sidebar. A chat panel opens — it looks like the chat UI from the IDE plugin, showing in a panel on the left side of JupyterLab while your notebook stays open on the right.

You type in the chat input:

> Fix the two data quality issues in df and put the code directly in my notebook

The agent responds in the chat, and at the same time a **new code cell appears in your notebook automatically** — you did not copy anything. The cell already contains:

```python
# Fix missing total_charges
df["total_charges"] = df["total_charges"].fillna(0)

# Convert last_complaint_date to datetime
df["last_complaint_date"] = pd.to_datetime(df["last_complaint_date"], errors="coerce")
```

You just press **Shift+Enter** in that cell to run it. Done.

This is the `insert_notebook_cell` tool being called automatically by the agent. You never had to ask for it explicitly — the agent decided the best way to deliver the code was to put it directly in the notebook rather than just show it in the chat.

---

## Example 4 — Multi-agent research (JupyterLab in Chrome, team mode)

**Who:** An ML engineer who wants to pick the best gradient boosting library for a new project.

**Where:** JupyterLab in Chrome.

---

You type:

```
%%jiuwen --mode team
I need to pick between XGBoost, LightGBM, and CatBoost for a tabular classification task.
Please research each one in parallel and give me a comparison covering:
- Training speed on large datasets
- Handling of categorical features
- Ease of hyperparameter tuning
- Community support and maintenance status in 2025
```

You press **Shift+Enter**.

In the output area, a small status line appears:

> *3 agents active — researching XGBoost, LightGBM, CatBoost...*

About 90 seconds later, the response streams in:

> **XGBoost**
> Training speed: Fast on CPU, excellent GPU support (via `device="cuda"`)...
> Categorical features: Must be encoded manually (label or one-hot)...
>
> **LightGBM**
> Training speed: Fastest of the three on large datasets due to histogram-based splits...
> Categorical features: Native support with `categorical_feature` parameter...
>
> **CatBoost**
> Training speed: Slower than LightGBM on large datasets but handles categoricals internally with no preprocessing...
>
> **Recommendation:** For your use case (tabular classification, large dataset), LightGBM is the fastest starting point. Use CatBoost if you have many high-cardinality categorical columns and want to avoid preprocessing. XGBoost remains the safest choice if you need GPU training.

Three agents ran simultaneously — one for each library. You got the answer in 90 seconds instead of 4–5 minutes of manual reading.

---

## Example 5 — Named sessions: research in one thread, coding in another (any Jupyter)

**Who:** A researcher who wants to keep their literature review separate from their implementation notes.

**Where:** Any Jupyter environment.

---

**Cell 1** — start a research conversation:

```
%%jiuwen --session research
Find me 3 recent papers on contrastive learning for tabular data.
Summarise each in 2 sentences.
```

The agent responds with three paper summaries.

**Cell 2** — in the same notebook, start a separate coding thread:

```
%%jiuwen --session coding
Write a PyTorch Dataset class for my CSV file.
The file has columns: features (all float64) and target (0/1).
```

The agent responds with a complete `TabularDataset` class.

**Cell 3** — go back to the research thread and continue:

```
%%jiuwen --session research
Based on the papers you found, which technique would be easiest to implement from scratch?
```

The agent remembers the three papers from Cell 1 and gives a recommendation based on them — because this cell uses `--session research`, not the coding thread.

The two conversations never mix.

---

## Example 6 — Working in PyCharm

**Who:** A developer who prefers PyCharm and uses its built-in Jupyter notebook support.

**Where:** PyCharm Professional, Jupyter notebook open inside the IDE (not in a browser).

---

PyCharm runs the notebook in an embedded Jupyter kernel. You do not need to start any JiuwenSwarm server — PyCharm launches the kernel when you open the notebook, and JiuwenSwarm loads as a regular Python import inside it. No extra processes, no ports.

You open a notebook in PyCharm, run `%load_ext jiuwenswarm_jupyter` in the first cell, then in a new cell:

```
%%jiuwen --mode code
I have a list called `prices` that contains daily stock prices as floats.
Write a function that calculates the 20-day rolling average and returns a new list.
```

The output appears in the PyCharm cell output area, streaming in real time, exactly as it would in a browser. You get a `rolling_average()` function you can immediately call.

> **Note:** The JupyterLab sidebar panel does not work in PyCharm — that requires a browser-based JupyterLab. All cell magics and notebook tools work normally in PyCharm.

---

## Example 7 — Inspecting a trained model

**Who:** An ML engineer who just trained a model and wants the agent to evaluate it.

**Where:** JupyterLab in Chrome.

---

You train a model in cells 1–4. After training, your namespace has:
- `model` — a scikit-learn RandomForestClassifier
- `X_test`, `y_test` — test data
- `y_pred` — predictions

You add a new cell:

```
%%jiuwen
Look at the model variable and the y_test and y_pred arrays.
Calculate the main classification metrics and tell me if there is a class imbalance problem.
```

Behind the scenes, the agent calls `read_variable("model")` and gets:

```
model: RandomForestClassifier
n_estimators=200, max_depth=12, class_weight=None
...
```

It also calls `read_variable("y_test")` and `read_variable("y_pred")`, getting full shape and distribution information.

It responds:

> **Classification metrics:**
> - Accuracy: 0.87
> - Precision (class 1): 0.61
> - Recall (class 1): 0.43
> - F1 (class 1): 0.50
>
> **Class imbalance problem: yes.**
> Your test set has 2,400 negative examples and only 310 positive ones (87%/13% split).
> With `class_weight=None`, the model is biased toward the majority class — that explains the poor recall on class 1.
>
> **Suggested fix:** Retrain with `class_weight="balanced"` or use SMOTE to oversample the minority class.

You did not paste any data into the prompt. The agent read the variables directly from your notebook.

---

## Example 8 — Quick one-liner question (any Jupyter)

**Who:** Anyone.

**Where:** Any cell in any Jupyter environment.

---

You need a quick answer while working and do not want to write a full cell:

```python
%jiuwen What is the difference between fit() and fit_transform() in scikit-learn?
```

The answer appears immediately in the output area:

> `fit()` computes the parameters (e.g. mean and std for a scaler) from the training data and stores them — it does not return transformed data.
> `fit_transform()` does both in one step: computes the parameters and returns the transformed data. It is a shorthand for `fit(X).transform(X)`.
>
> **Rule of thumb:** Use `fit_transform()` on training data. Use `transform()` only (never `fit_transform()`) on test or production data — otherwise you leak test statistics into your preprocessing.

---

## Example 9 — Google Colab

**Who:** A student working on a machine learning assignment in Google Colab (free cloud notebooks in a browser).

**Where:** Google Colab — colab.research.google.com, running in Chrome.

---

At the top of the Colab notebook, in the first cell:

```python
!pip install jiuwenswarm-jupyter jiuwenswarm -q
%load_ext jiuwenswarm_jupyter
```

This works because Colab uses a standard IPython kernel. After running, the magic is available for the rest of the session.

In the next cell:

```
%%jiuwen --mode code
I need to implement k-fold cross-validation from scratch without using sklearn.
The function should take X, y, a model, and k as input.
```

The agent streams a complete implementation. The student can run it immediately in the next cell.

> **Note:** The JupyterLab sidebar panel does not work in Google Colab — Colab has its own frontend and does not support JupyterLab extensions. All cell magics and notebook tools work normally. Use `%jiuwen_chat` for an embedded chat UI.

---

## Example 10 — Debugging with `%jiuwen_error`

**Scenario:** A data scientist is preprocessing a dataset and gets a cryptic KeyError.

**Cell 1 — raises an error:**

```python
df["normalised"] = (df["revenue"] - df["revenue"].mean()) / df["revenue"].std()
df["label_encoded"] = df["category"].map(label_map["category"])
# KeyError: 'category'
```

**Cell 2 — send the error to the agent with one command:**

```
%jiuwen_error
```

The magic reads the full traceback and the failing cell source automatically, then sends them to the agent. Output:

```
[jiuwenswarm] Sending last error to agent…

The key 'category' is missing from label_map. The dict only contains:
{'product_type': ..., 'region': ...}

You likely meant label_map["product_type"] — here is the corrected line:
    df["label_encoded"] = df["category"].map(label_map["product_type"])

Alternatively, if "category" should exist, check how label_map was built.
```

You can add your own note on the same line:

```
%jiuwen_error and also make sure NaN values in the column are handled
```

---

## Example 11 — Configuring defaults with `%jiuwen_config`

**Scenario:** A researcher always wants team mode and a longer timeout for this notebook, without typing flags on every cell.

**One-time setup cell:**

```
%jiuwen_config mode=team timeout=600
```

Output:

```
mode          : team
timeout       : 600
inject_context: True
model         : (from config.yaml)
```

From now on, every `%%jiuwen` cell in this notebook uses team mode with a 10-minute timeout by default. A cell can still override:

```
%%jiuwen --mode agent --timeout 30
Quick one-sentence answer: what is a p-value?
```

View the current config at any time:

```
%jiuwen_config
```

---

## Example 13 — Embedded full chat UI (`%jiuwen_chat`)

**Who:** A data scientist using Google Colab who wants a GUI instead of cell magic syntax.

**Where:** Google Colab (or any environment without the JupyterLab sidebar).

---

After loading the extension, run this in any cell:

```python
%jiuwen_chat
```

The cell output area becomes a fully interactive chat panel — the same themed interface used by the JupyterLab sidebar. A text input at the bottom accepts queries; responses stream in with markdown rendering, code blocks, and collapsible tool call cards.

The panel is connected to the running kernel via the Jupyter comm channel. It shares the same session as your `%%jiuwen` cells — you can mix magic cells and the chat panel in the same notebook.

**Height control:**

```python
%jiuwen_chat --height 700   # taller panel for long conversations
```

**What works inside `%jiuwen_chat`:**

- All four agent modes (`agent`, `code`, `team`, `code.team`) via the mode selector
- Session persistence — same conversation continues if you scroll back to the cell
- Notebook context injection — the agent sees your variables and recent cells
- Streaming response rendering with typing indicator
- Tool call display (collapsible cards showing what the agent did)

**In JupyterLab:** The sidebar panel is preferred, but `%jiuwen_chat` works there too. Both connect to the same kernel — useful for having the chat panel visible alongside a specific output cell.

---

## Summary — What works where

**Does JiuwenSwarm need to be running as a separate process?**
No. Unlike the IDE plugin (which connects to a server on port 18092), this Jupyter integration imports JiuwenSwarm directly as a Python library into the notebook kernel. You only need `pip install jiuwenswarm jiuwenswarm-jupyter` and a config file — nothing to start or keep running.

| Feature | JupyterLab (Chrome) | PyCharm | Google Colab | VS Code Notebooks |
|---|---|---|---|---|
| Separate JiuwenSwarm server needed? | **No** | **No** | **No** | **No** |
| Extra setup beyond `pip install`? | Only for sidebar | No | No | No |
| `%%jiuwen` cell magic | Yes | Yes | Yes | Yes |
| `%jiuwen` line magic | Yes | Yes | Yes | Yes |
| `%jiuwen_error` — forward last exception | Yes | Yes | Yes | Yes |
| `%jiuwen_config` — per-notebook settings | Yes | Yes | Yes | Yes |
| `%jiuwen_export` — save conversation history | Yes | Yes | Yes | Yes |
| `%jiuwen_replay` — continue in fresh session | Yes | Yes | Yes | Yes |
| `%jiuwen_pin` / `%jiuwen_unpin` | Yes | Yes | Yes | Yes |
| Context injection (variables, DataFrames) | Yes | Yes | Yes | Yes |
| Named sessions | Yes | Yes | Yes | Yes |
| Session persistence across kernel restarts | Yes | Yes | Yes | Yes |
| Multi-agent team mode | Yes | Yes | Yes | Yes |
| Streaming output in cell | Yes | Yes | Yes | Yes |
| `read_variable()` | Yes | Yes | Yes | Yes |
| `read_notebook_cell()` | Yes | Yes | Yes | Yes |
| `insert_notebook_cell()` — display block fallback | Yes | Yes | Yes | Yes |
| `%jiuwen_chat` — embedded full chat UI | Yes | No | Yes | No |
| JupyterLab sidebar chat panel | Yes | No | No | No |
| Session list panel (sidebar) | Yes | No | No | No |
| Swarm map panel (sidebar) | Yes | No | No | No |
| `insert_notebook_cell()` — actual cell insertion | Yes (sidebar) | No | No | No |
| Agent-generated cell tagging (metadata) | Yes (sidebar) | No | No | No |
| Keyboard shortcuts (`Cmd+Shift+J` / `N`) | Yes (sidebar) | No | No | No |
| Status bar indicator | Yes (sidebar) | No | No | No |
