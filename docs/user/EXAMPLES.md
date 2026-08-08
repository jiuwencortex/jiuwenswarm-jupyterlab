# Real-Life Examples — JiuwenSwarm for Jupyter

These examples show what actually happens when you use JiuwenSwarm in a notebook.
They are written as stories: what you do, what you type, and what you get back.

---

## Before you start — what needs to be installed

**You do not need to start a JiuwenSwarm server.** This is different from the IDE plugin.

The IDE plugin (VS Code, JetBrains) connects to a JiuwenSwarm server that runs separately on your machine — you have to start it, and if it is not running, the plugin shows "disconnected". The Jupyter integration works differently: it imports JiuwenSwarm directly as a Python library into the same process as your notebook. Nothing else needs to be running.

The only things you need:

```bash
# 1. Install the main JiuwenSwarm package
pip install jiuwenswarm

# 2. Install the Jupyter integration
pip install jiuwenswarm-jupyter

# 3. Make sure you have a config file at ~/.jiuwenswarm/config/config.yaml
#    This is created the first time you configure JiuwenSwarm (API keys, model settings).
#    If you already use the CLI or IDE plugin, you already have this file.
```

That is all. When you run `%load_ext jiuwenswarm_jupyter` in a cell, it loads JiuwenSwarm into the notebook's Python process directly — no port, no server to start, no daemon in the background.

**Which parts need what:**

| What you want to use | What you need |
|---|---|
| `%%jiuwen` cell magic, `%jiuwen`, Python API, `read_variable`, `read_notebook_cell`, `insert_notebook_cell` | `pip install jiuwenswarm jiuwenswarm-jupyter` only |
| JupyterLab sidebar chat panel, swarm map | The above + build the TypeScript frontend (see [PUBLISHING.md](../operations/PUBLISHING.md)) |

The examples below that say "JupyterLab in Chrome" work with just `pip install`. You do not need to build anything for them.

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

## Example 3 — The agent inserts the code cell for you (JupyterLab with sidebar panel, Phase 2)

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

This is the `insert_notebook_cell` tool (Phase 3) being called automatically by the agent. You never had to ask for it explicitly — the agent decided the best way to deliver the code was to put it directly in the notebook rather than just show it in the chat.

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

> **Note:** The JupyterLab sidebar panel (Phase 2) does not work in PyCharm — that requires a browser-based JupyterLab. Everything in Phase 1 and Phase 3 works normally in PyCharm.

---

## Example 7 — Inspecting a trained model (Phase 3 tools)

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

> **Note:** Phase 2 (JupyterLab sidebar panel) does not work in Google Colab — Colab has its own frontend and does not support JupyterLab extensions. Phase 1 and Phase 3 work normally.

---

## Summary — What works where

**Does JiuwenSwarm need to be running as a separate process?**
No. Unlike the IDE plugin (which connects to a server on port 18092), this Jupyter integration imports JiuwenSwarm directly as a Python library into the notebook kernel. You only need `pip install jiuwenswarm jiuwenswarm-jupyter` and a config file — nothing to start or keep running.

| Feature | JupyterLab (Chrome) | PyCharm | Google Colab | VS Code Notebooks |
|---|---|---|---|---|
| Separate JiuwenSwarm server needed? | **No** | **No** | **No** | **No** |
| Extra setup beyond `pip install`? | Only for Phase 2 sidebar | No | No | No |
| `%%jiuwen` cell magic | Yes | Yes | Yes | Yes |
| `%jiuwen` line magic | Yes | Yes | Yes | Yes |
| Context injection (variables, DataFrames) | Yes | Yes | Yes | Yes |
| Named sessions | Yes | Yes | Yes | Yes |
| Multi-agent team mode | Yes | Yes | Yes | Yes |
| Streaming output in cell | Yes | Yes | Yes | Yes |
| `read_variable()` | Yes | Yes | Yes | Yes |
| `read_notebook_cell()` | Yes | Yes | Yes | Yes |
| `insert_notebook_cell()` — display block fallback | Yes | Yes | Yes | Yes |
| JupyterLab sidebar chat panel | Yes (Phase 2) | No | No | No |
| Swarm map panel | Yes (Phase 2) | No | No | No |
| `insert_notebook_cell()` — actual cell insertion | Yes (Phase 2 only) | No | No | No |
| Status bar indicator | Yes (Phase 2) | No | No | No |
