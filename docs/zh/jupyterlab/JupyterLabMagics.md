# 魔法参考 —— 面向 Jupyter 的 JiuwenSwarm

`jiuwenswarm_jupyter` 提供的所有 IPython 魔法的完整参考。首先加载扩展：

```python
%load_ext jiuwenswarm_jupyter
```

---

## 速查表

### 核心

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%%jiuwen`](#jiuwen--jiuwen) | 单元格 / 行 | 向智能体发送查询，流式输出回复 |
| [`%jiuwen`](#jiuwen--jiuwen) | 行 | 单行查询简写 |
| [`%jiuwen_error`](#jiuwen_error) | 行 | 将上次异常转发给智能体进行调试 |
| [`%jiuwen_chat`](#jiuwen_chat) | 行 | 在单元格输出中嵌入完整聊天界面 |

### 会话

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%jiuwen_clear`](#jiuwen_clear) | 行 | 重置对话会话 |
| [`%jiuwen_export`](#jiuwen_export) | 行 | 将对话历史保存为 markdown 文件 |
| [`%jiuwen_replay`](#jiuwen_replay) | 行 | 在新会话中继续，重放最近上下文 |
| [`%jiuwen_pin`](#jiuwen_pin--jiuwen_unpin) | 行 | 始终将特定变量注入上下文 |
| [`%jiuwen_unpin`](#jiuwen_pin--jiuwen_unpin) | 行 | 从固定列表移除变量 |
| [`%jiuwen_memory`](#jiuwen_memory) | 行 | 持久化的跨 notebook 知识库 |

### 分析

*理解代码：解释、审查、安全、分析、叙述。*

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%%jiuwen_explain`](#jiuwen_explain) | 单元格 | 执行单元格并获得智能体编写的解释 |
| [`%jiuwen_audit`](#jiuwen_audit) | 行 | 完整 notebook 健康扫描——代码质量和数据科学问题 |
| [`%jiuwen_story`](#jiuwen_story) | 行 | 将已执行单元格转换为叙述性博客文章、报告或论文 |
| [`%%jiuwen_profile`](#jiuwen_profile) | 单元格 | 用 cProfile 分析单元格并获智能体解读的分析 |
| [`%%jiuwen_guard`](#jiuwen_guard) | 单元格 | 声明前置/后置条件；智能体自动诊断违规 |
| [`%%jiuwen_safe`](#jiuwen_safe) | 单元格 | 运行有风险单元格前的静态副作用分析 |
| [`%jiuwen_diff`](#jiuwen_diff) | 行 | 对比 git 引用并获得智能体评论 |
| [`%%jiuwen_doc`](#jiuwen_doc) | 单元格 | 为任意函数或类生成并插入完整 docstring |

### 转换

*重写代码：修复错误、优化、翻译、生成测试。*

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%jiuwen_fix`](#jiuwen_fix) | 行 | 就地重写失败单元格以修复上次错误 |
| [`%%jiuwen_optimize`](#jiuwen_optimize) | 单元格 | 用向量化代码重写慢单元格并就地替换 |
| [`%%jiuwen_translate`](#jiuwen_translate) | 单元格 | 将代码翻译为不同的数据库（polars、dask、spark、…） |
| [`%%jiuwen_test`](#jiuwen_test) | 单元格 | 为任意函数或类生成完整 pytest 测试套件 |
| [`%jiuwen_todo`](#jiuwen_todo) | 行 | 查找 TODO/FIXME/桩并起草实现 |
| [`%%jiuwen_benchmark`](#jiuwen_benchmark) | 单元格 | 评测多个实现并解释结果 |

### 数据

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%jiuwen_eda`](#jiuwen_eda) | 行 | 带代码单元格的完整自动化探索性数据分析 |
| [`%jiuwen_schema`](#jiuwen_schema) | 行 | 从实时 DataFrame 生成 markdown 数据字典 |
| [`%jiuwen_hypothesis`](#jiuwen_hypothesis) | 行 | 生成可检验的统计假设及代码 |
| [`%jiuwen_features`](#jiuwen_features) | 行 | 领域感知的特征工程建议及代码 |
| [`%jiuwen_leakage`](#jiuwen_leakage) | 行 | 扫描整个 notebook 的数据泄漏 |
| [`%%jiuwen_df`](#jiuwen_df) | 单元格 | 自然语言 DataFrame 查询——生成并运行 pandas 代码 |
| [`%%jiuwen_sql`](#jiuwen_sql) | 单元格 | 通过 DuckDB 对内存中的 DataFrame 进行自然语言 SQL 查询 |
| [`%%jiuwen_viz`](#jiuwen_viz) | 单元格 | 自然语言图表描述——生成完整可视化代码 |
| [`%jiuwen_mock`](#jiuwen_mock) | 行 | 生成镜像真实 DataFrame schema 的合成数据 |
| [`%jiuwen_compare`](#jiuwen_compare) | 行 | 两个 DataFrame 的统计比较和漂移报告 |

### 工作流

| 魔法 | 种类 | 作用 |
|---|---|---|
| [`%jiuwen_track`](#jiuwen_track) | 行 | 记录实验并比较运行 |
| [`%jiuwen_reproduce`](#jiuwen_reproduce) | 行 | 将 notebook 转换为独立 Python 脚本 |
| [`%jiuwen_card`](#jiuwen_card) | 行 | 为任意训练好的模型生成结构化模型卡片 |
| [`%jiuwen_suggest`](#jiuwen_suggest) | 行 | 分析 notebook 状态并建议按优先级排序的下一步 |

---

## 核心

### `%%jiuwen` / `%jiuwen`

向 JiuwenSwarm 智能体发送查询，并将回复流式输出到单元格输出。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--mode`, `-m` | `agent` | 智能体模式：`agent`、`code`、`team`、`code.team` |
| `--session`, `-s` | notebook 默认 | 命名会话——跨单元格复用对话 |
| `--no-context` | 关 | 跳过自动 notebook 上下文注入 |
| `--timeout`, `-t` | `300` | 等待回复的最大秒数 |

**示例**

```
%%jiuwen
解释 df 变量包含什么，并建议一个清洗策略。
```

```
%%jiuwen --mode code
使用分层采样对目标列进行训练/测试划分。
```

```
%%jiuwen --mode team --session research
研究表格数据上 XGBoost 的前 3 个替代方案。为每个库分配一个智能体，
在 df 上分别评测，并生成对比表。
```

```
%%jiuwen --session eda --no-context
总结典型探索性数据分析工作流中的关键步骤。
```

```python
%jiuwen df 的形状是什么？
```

---

### `%jiuwen_error`

将上次 Python 异常转发给智能体进行调试。自动读取 `sys.last_value` 和失败单元格的源码。

**示例**

```python
%jiuwen_error
```

```python
%jiuwen_error 解释为什么发生 KeyError 并建议一个稳健的修复
```

```python
%jiuwen_error 这是一个合并操作——检查 dtype 是否不匹配
```

---

### `%jiuwen_chat`

将完整 JiuwenSwarm 聊天界面作为 iframe 嵌入单元格输出。iframe 通过 Jupyter comm API 连接到
运行中的内核。会话、上下文注入和智能体模式都与 `%%jiuwen` 完全相同。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--height PX` | `520` | iframe 高度（像素） |

**示例**

```python
%jiuwen_chat
```

```python
%jiuwen_chat --height 700
```

最适合用于 Google Colab、Kaggle Notebooks 和没有 JupyterLab 侧边栏面板的经典 Jupyter
Notebook。

---

## 会话

### `%jiuwen_clear`

重置默认或命名会话。此后智能体不再记得之前的交流。

**示例**

```python
%jiuwen_clear                  # 清除默认会话
%jiuwen_clear research         # 清除命名会话
```

---

### `%jiuwen_export`

将会话的完整对话历史保存为 markdown 文件。每次交流保存带时间戳、模式、用户查询和智能体回复。

**选项**

| 标志 | 说明 |
|---|---|
| `--session NAME`, `-s NAME` | 导出命名会话而非默认会话 |
| `FILENAME` | 输出文件（默认：`jiuwen_session_<id>.md`） |

**示例**

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

将最近 N 次交流重新发送到新会话作为上下文。原会话不变。新会话先收到重放摘要，然后等待你的
下一条消息。

**示例**

```python
%jiuwen_replay        # 重放最近 3 次交流（默认）
%jiuwen_replay 5      # 重放最近 5 次交流
```

---

### `%jiuwen_pin` / `%jiuwen_unpin`

固定特定变量，使它们始终包含在智能体上下文中，即使 `--no-context` 生效或自动扫描会跳过它们。

**示例**

```python
%jiuwen_pin df_train model scaler
%jiuwen_pin results_dict feature_names
%jiuwen_unpin scaler
%jiuwen_unpin all
```

---

### `%jiuwen_memory`

存储在 `~/.jiuwenswarm/memory.json` 的持久化跨 notebook 知识库。笔记在内核重启和 notebook
关闭后保留。`search` 命令检索匹配的笔记，并将其作为上下文发送给智能体。

**命令**

| 命令 | 说明 |
|---|---|
| `save "NOTE"` | 保存纯文本笔记 |
| `search "QUERY"` | 查找匹配的笔记并传给智能体 |
| `list` | 打印所有已保存笔记 |
| `delete ID` | 按数字 ID 移除笔记 |
| `clear` | 删除所有已保存笔记 |

**示例**

```python
%jiuwen_memory save "此数据集上验证 AUC 在 200 棵 XGBoost 树后趋于平稳"
```

```python
%jiuwen_memory save "customer_id 合并会丢失约 3% 的行——原始数据流中已知的数据质量问题"
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

## 分析

*理解代码：解释、审查、安全、分析和叙述输出。*

### `%%jiuwen_explain`

在 notebook 命名空间中执行单元格正文，然后流式输出智能体编写的解释，说明代码做了什么以及输出
含义。生成适合作为 markdown 叙述单元格插入的散文。

**示例**

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

收集所有已执行单元格和当前命名空间，然后请求智能体进行结构化健康扫描。智能体检查代码质量
问题、数据科学反模式和潜在运行时故障。

**选项**

| 标志 | 说明 |
|---|---|
| `--quick` | 仅要点列表总结，不引用代码 |

**示例**

```python
%jiuwen_audit
```

```python
%jiuwen_audit --quick
```

智能体检查：
- 死代码或不可达代码
- 未使用的导入
- 训练集和测试集之间的数据泄漏
- 可能在未见数据上静默失败的操作（dtype 不匹配、空值）
- 硬编码路径和魔法数字
- 乱序执行依赖
- 内存密集型模式（`iterrows`、大型 DataFrame 的完整复制）
- 在 I/O 边界缺少错误处理

---

### `%jiuwen_story`

按顺序读取所有已执行单元格，并请智能体生成一篇连贯文档。输出同时写入 markdown 文件并流式输出
到单元格输出。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--output PATH` | `jiuwen_story.md` | 目标文件 |
| `--style STYLE` | `blog` | 写作风格：`blog`、`paper`、`tutorial`、`report` |

| 风格 | 输出 |
|---|---|
| `blog` | 对话式、第一人称技术叙述 |
| `paper` | 摘要、引言、方法、结果、结论 |
| `tutorial` | 分步指南；每个代码块前有散文 |
| `report` | 执行摘要、发现、建议 |

**示例**

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

在 `cProfile` 下执行单元格，打印原始分析统计信息，然后将最慢的调用点发送给智能体进行瓶颈诊断
和优化建议。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--top N` | `20` | 包含的最慢函数数 |

**示例**

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

将前置和后置条件声明为 Python 表达式。条件在单元格运行前后于 notebook 命名空间中评估。任何
违规时，智能体会收到失败的表达式、单元格源码和当前上下文，并诊断哪里出了问题。

**参数**（在 `%%` 行上）

| 参数 | 说明 |
|---|---|
| `pre="EXPR"` | 执行前必须为 True 的表达式 |
| `post="EXPR"` | 执行后必须为 True 的表达式 |

**示例**

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

将单元格正文发送给智能体进行静态副作用分析，**不执行它**。智能体报告写入的文件、网络调用、
数据变更、不可逆操作和异常路径，然后给出 `SAFE / CAUTION / HIGH RISK` 判定。

**选项**

| 标志 | 说明 |
|---|---|
| `--run` | 分析完成后立即执行单元格 |

**示例**

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

针对某个引用运行 `git diff`，并将输出发送给智能体进行结构化审查。先打印原始 diff；随后是
智能体评论。

**参数**

| 参数 | 默认值 | 说明 |
|---|---|---|
| `REF` | `HEAD` | Git 引用：`HEAD~N`、分支名、提交哈希 |
| `--stat` | 关 | 仅摘要 diff（无完整补丁） |
| `--file PATH` | 所有文件 | 将 diff 限制为一个文件 |

**示例**

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

为单元格正文中的函数或类生成完整 docstring 并就地插入。单元格不会执行。支持 numpy、Google 和
Sphinx docstring 风格。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--style STYLE` | `numpy` | Docstring 格式：`numpy`、`google`、`sphinx` |
| `--no-replace` | 关 | 将 docstring 流式输出到输出，而非更新单元格 |

**示例**

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

## 转换

*重写代码：修复错误、优化性能、在库之间翻译、生成测试。*

### `%jiuwen_fix`

通过读取回溯和失败单元格的源码，然后请智能体用修正版重写单元格，来修复上次 Python 错误。
修复后的单元格就地替换原单元格。

**参数**

| 参数 | 说明 |
|---|---|
| `HINT` | 可选的自由文本提示（例如 `"the column is str not int"`） |

**示例**

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

为速度和内存效率重写单元格正文，就地替换原单元格。智能体识别瓶颈——`iterrows`、Python 循环、
冗余复制——并返回向量化的即插即用替代品。

**选项**

| 标志 | 说明 |
|---|---|
| `--profile` | 先对原单元格运行 cProfile 并将统计信息包含在提示中 |
| `--no-replace` | 将优化版本流式输出到输出，而非替换单元格 |

**示例**

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

将单元格正文翻译为不同的数据处理库。智能体生成完整、可运行的等价实现，并将其作为新单元格
插入。原单元格保留。

**选项**

| 标志 | 说明 |
|---|---|
| `--to LIBRARY` | 目标库（必填）：`polars`、`dask`、`spark`、`torch`、`sql`、`modin`、`jax`、`cudf`、`vaex`、`numpy` |

**示例**

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

将单元格正文作为源码读取，并请智能体编写完整的 pytest 测试套件——正常情况、边界情况和预期
失败。单元格不会执行。

**选项**

| 标志 | 说明 |
|---|---|
| `--file PATH` | 将测试写入此文件，而非插入新单元格 |

**示例**

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

扫描每个已执行单元格中的 `# TODO`、`# FIXME`、`# HACK`、`# XXX`、`raise NotImplementedError`
和裸 `pass` 语句。将完整列表发送给智能体，智能体为每个项目起草具体实现，并将其作为可运行的
代码单元格插入。

**选项**

| 标志 | 说明 |
|---|---|
| `--list` | 仅打印找到的条目——不调用智能体 |

**示例**

```python
%jiuwen_todo
```

```python
%jiuwen_todo --list
```

---

### `%%jiuwen_benchmark`

在 `---` 分隔行上拆分单元格，用 `timeit` 评测每个部分，打印带相对最快实现比例的对比表，并将
结果发送给智能体进行解释。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--n N` | `1000` | 每轮计时重复次数 |
| `--setup CODE` | `pass` | 计时前执行一次的设置代码（例如导入） |

**示例**

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
# 方案 A：iterrows
totals = []
for _, row in df.iterrows():
    totals.append(row["price"] * row["qty"])
---
# 方案 B：向量化
totals = (df["price"] * df["qty"]).tolist()
```

---

## 数据

### `%jiuwen_eda`

分析一个 DataFrame，并生成完整的探索性数据分析作为可运行的 notebook 单元格。智能体检查
schema、空值率、分布和相关，然后插入覆盖汇总统计、缺失值热力图、分布和异常检测的单元格。

**选项**

| 标志 | 说明 |
|---|---|
| `--target COL` | 标记标签列——智能体围绕它聚焦 EDA |
| `--quick` | 仅汇总统计，不插入单元格 |

**示例**

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

自动分析一个或多个 DataFrame 的每一列，并请智能体编写 markdown 数据字典。如果未给出 DataFrame
名称，则包含命名空间中所有 pandas DataFrame。

**选项**

| 标志 | 说明 |
|---|---|
| `DF_NAME ...` | 一个或多个 DataFrame 变量名（可选——默认为全部） |
| `--output PATH` | 将数据字典写入此文件 |

**示例**

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

将 DataFrame 的汇总统计和空值率发送给智能体，它生成 N 个可检验的统计假设——每个都带理由和
使用 scipy 或 statsmodels 的完整 Python 代码。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `DF_NAME` | 必填 | DataFrame 变量名 |
| `--target COL` | 无 | 围绕此标签列聚焦假设 |
| `--n N` | `8` | 要生成的假设数 |

**示例**

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

分析列语义（日期、ID、类别、文本、数值），并请智能体提出工程化特征——每个都带理由和 pandas
代码，作为单独的可运行单元格插入。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `DF_NAME` | 必填 | DataFrame 变量名 |
| `--target COL` | 无 | 聚焦于可能预测此列的特征 |
| `--domain TEXT` | 无 | 领域上下文，例如 `"telecom churn"`、`"credit risk"` |
| `--n N` | `12` | 要生成的特征想法数 |

**示例**

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

收集所有已执行单元格和变量名，然后请智能体进行专门的数据泄漏审计。智能体扫描时间泄漏、切分前
的目标编码、训练/测试污染，以及时间序列工作流中的前瞻偏差。

**示例**

```python
%jiuwen_leakage
```

常见发现：
- 在训练/测试切分前对整个数据集拟合的 `StandardScaler`
- 切分前计算的目标均值编码
- `fillna(df['col'].mean())`，其中均值包含测试行
- 从未来事件派生的时间戳列泄漏到特征中

---

### `%%jiuwen_df`

用自然语言描述数据转换或查询。智能体从命名空间中所有 DataFrame 读取真实列名和 dtype，生成
pandas 代码，插入为新单元格，并可选地运行它。

**选项**

| 标志 | 说明 |
|---|---|
| `--df NAME` | 仅将上下文限制为此 DataFrame |
| `--no-run` | 插入单元格但不执行 |

**示例**

```
%%jiuwen_df
按产品类别细分，显示按总营收排名的前 10 名客户。
```

```
%%jiuwen_df --df transactions
将月份作为列、产品作为行、营收总和作为值进行透视。
```

```
%%jiuwen_df --no-run
计算 daily_sales 的 7 天和 30 天滚动平均值，按 store_id 分组。
```

```
%%jiuwen_df
找出 refund_amount 大于原始 purchase_amount 的所有行。
```

---

### `%%jiuwen_sql`

编写自然语言查询。智能体生成一个 DuckDB SQL 查询，将你的 DataFrame 变量名视为表名，插入为
单元格，并可选地在进程内运行，无需外部数据库。

**选项**

| 标志 | 说明 |
|---|---|
| `--no-run` | 插入 SQL 单元格但不执行 |

**示例**

```
%%jiuwen_sql
按平均订单价值找出前 5 个产品类别，排除已取消订单。
```

```
%%jiuwen_sql
在 customer_id 上连接 orders 和 customers，然后按获客渠道计算 90 天留存率。
```

```
%%jiuwen_sql --no-run
窗口函数：按每个国家内客户终身价值排序。
```

```
%%jiuwen_sql
按月显示营收环比增长率百分比，按日期排序。
```

---

### `%%jiuwen_viz`

用自然语言描述图表。智能体检测安装的绘图库（plotly、seaborn 或 matplotlib），生成带正确标签、
标题和图例的完整可视化代码，并可选地运行它。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--lib LIBRARY` | 自动检测 | 强制特定库：`plotly`、`seaborn`、`matplotlib` |
| `--no-run` | 关 | 插入图表单元格但不执行 |

**示例**

```
%%jiuwen_viz
按 churn 标签着色的 age 对 income 散点图，带回归线。
```

```
%%jiuwen_viz --lib plotly
df 中所有数值列相关矩阵的交互式热力图。
```

```
%%jiuwen_viz
按 customer_segment 分组的 purchase_amount 并排箱线图。
```

```
%%jiuwen_viz --lib matplotlib --no-run
daily_active_users 的时间序列，叠加 7 天滚动平均值。
```

---

### `%jiuwen_mock`

生成镜像现有 DataFrame schema 的合成 DataFrame——匹配 dtype、值范围、基数、空值率和日期范围。
生成的代码作为可运行单元格插入。非常适合单元测试、演示，以及在不出示真实数据的情况下共享
notebook。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `DF_NAME` | 必填 | 模板 DataFrame 变量名 |
| `--n N` | `100` | 要生成的行数 |
| `--var NAME` | `df_mock` | 输出 DataFrame 的变量名 |
| `--seed N` | `42` | 用于可复现性的随机种子 |

**示例**

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

比较两个 DataFrame 并获得结构化漂移报告。涵盖 schema 变更（新增/移除/类型变更的列）、数值的
统计漂移、类别分布变化和空值率变化。适用于训练/测试切分验证、清洗前后检查以及数据集版本比较。

**选项**

| 标志 | 说明 |
|---|---|
| `DF1 DF2` | 两个 DataFrame 变量名（必填，位置参数） |
| `--target COL` | 在此标签列上聚焦漂移分析 |

**示例**

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

## 工作流

### `%jiuwen_track`

将实验结果记录到 `~/.jiuwenswarm/experiments.json`。比较运行、找到最佳结果或删除单个条目。
每次记录自动捕获 git 提交哈希、模型超参数（通过 `get_params()`）和时间戳。

**命令**

| 命令 | 说明 |
|---|---|
| `log MODEL METRICS` | 记录实验。`MODEL` 是变量名；`METRICS` 是 `key=value` 对 |
| `compare` | 将所有已记录运行作为对比表打印 |
| `best --by METRIC` | 显示 METRIC 值最高的运行 |
| `delete ID` | 按数字 ID 移除运行 |

**示例**

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

收集最近 80 个已执行单元格，并请智能体生成一个干净、独立的 Python 脚本，带合适的函数、参数
解析和 `if __name__ == '__main__'` 入口点。脚本保存到磁盘，可直接从命令行运行。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--output PATH` | `reproduce.py` | 脚本写入位置 |
| `--no-argparse` | 关 | 省略 argparse，改用硬编码值 |

**示例**

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

内省训练好的模型并生成结构化模型卡片——涵盖概述、输入和输出、训练配置、评估指标、局限和使用
示例。支持 sklearn、XGBoost、LightGBM 以及任何带 `get_params()` 方法的对象。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `MODEL_VAR` | 必填 | 训练好的模型的变量名 |
| `--output PATH` | `model_card.md` | 卡片写入位置 |
| `--metrics "k=v ..."` | 无 | 要包含的内联评估指标（例如 `"auc=0.91 f1=0.88"`） |

**示例**

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

分析所有已执行单元格、当前变量命名空间以及检测到的 DataFrame 和模型，然后建议下一步最有价值
的步骤——每个都带优先级标签、理由和作为单元格插入的可运行代码桩。

**选项**

| 标志 | 默认值 | 说明 |
|---|---|---|
| `--domain TEXT` | 无 | 领域上下文，例如 `"fraud detection"`、`"NLP classification"` |
| `--goal TEXT` | 无 | 最终目标，例如 `"production deployment"`、`"Kaggle submission"` |
| `--n N` | `8` | 要生成的建议数 |

**示例**

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
