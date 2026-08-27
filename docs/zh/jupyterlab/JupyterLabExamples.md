# 真实示例 —— 面向 Jupyter 的 JiuwenSwarm

这些示例展示你在 notebook 中使用 JiuwenSwarm 时实际会发生什么。它们以故事形式编写：你做什么、
输入什么、得到什么。

**可运行版本：** [`examples/examples.ipynb`](../../../jupyterlab/examples/examples.ipynb)
包含所有示例的可执行单元格，使用合成数据——无需外部文件。

---

## 开始前 —— 需要安装什么

**你无需运行 `jiuwenswarm-start`。** 这是与 IDE 插件的关键区别。

### IDE 插件如何工作 vs 这里如何工作

IDE 插件（VS Code、JetBrains）连接到你用 `jiuwenswarm-start` 启动的 JiuwenSwarm **服务器**。
该服务器作为独立进程运行，管理 Web UI、监听频道（Slack、Discord 等），并暴露 IDE 插件连接的
WebSocket 端点。如果服务器未运行，插件会显示「已断开」，无法做任何事情。

Jupyter 集成的工作方式完全不同。`JiuWenSwarm` 也是一个 Python 类——当你 `pip install
jiuwenswarm` 时，该类作为普通库可用。当你在 notebook 中加载扩展时，它会在 notebook 的 Python
进程中直接实例化 `JiuWenSwarm()`。智能体运行时在内核内启动——无独立进程、无端口、无
WebSocket。`jiuwenswarm-start` 为服务器所做的事情，notebook 内核按需为自己做。

可以这样理解：
- **`jiuwenswarm-start`** = 启动一个包含一切的生成服务器：Web UI、所有频道、面向 IDE 的
  WebSocket、多用户会话
- **`%load_ext jiuwenswarm_jupyter`** = 只在你 notebook 的 Python 进程中启动智能体运行时，
  仅此而已

### 你需要什么

```bash
# 1. 安装 JiuwenSwarm 和 Jupyter 集成
pip install jiuwenswarm jiuwenswarm-jupyter

# 2. 一次性工作区设置（每台机器只需一次）
#    创建带有默认配置和目录结构的 ~/.jiuwenswarm/
jiuwenswarm-init

# 3. 将 API 密钥添加到 ~/.jiuwenswarm/config/.env
#    （与 CLI 和 IDE 插件使用相同文件——如果已做过可跳过）
```

仅此而已。之后，在任何 notebook 中 `%load_ext jiuwenswarm_jupyter` 都会在内核内启动智能体。
无需启动服务器、无需检查端口、后台没有任何东西在运行。

**各部分需要什么：**

| 你想使用什么 | 你需要什么 |
|---|---|
| `%%jiuwen` 魔法、`%jiuwen`、Python API、notebook 工具 | `pip install` + `jiuwenswarm-init`（一次性） |
| JupyterLab 侧边栏聊天面板、swarm map | 上述 + 构建 TypeScript 前端（见 [PUBLISHING.md](../../../jupyterlab/publishing/PUBLISHING.md)） |

下面的示例都只需要 `pip install` + `jiuwenswarm-init`。你无需为它们构建任何东西。

---

## 示例 1 —— 理解数据集（Chrome 中的 JupyterLab）

**谁：** 一位刚从客户那里收到 CSV 文件并想快速理解它的数据科学家。

**地点：** 在 `localhost:8888` 的 Chrome 中打开 JupyterLab。

---

你打开一个新 notebook。在第一个单元格中写：

```python
import pandas as pd
df = pd.read_csv("customer_churn.csv")
%load_ext jiuwenswarm_jupyter
```

运行它。扩展在后台静默加载。

现在在下一个单元格中写：

```
%%jiuwen
这个数据集包含什么？有多少行和多少列？
在我开始之前，有哪些明显的数据质量问题需要了解？
```

按 **Shift+Enter**。

单元格下方立即开始实时出现文本——你无需等完整回答即可阅读：

> 数据集 `df` 有 **10,847 行和 21 列**。
>
> 从列名和类型来看，它似乎是客户流失数据集，包含：
> - 人口统计：`age`、`gender`、`tenure_months`
> - 使用指标：`monthly_charges`、`total_charges`、`num_products`
> - 支持历史：`num_support_tickets`、`last_complaint_date`
> - 目标：`churned`（0/1）
>
> **我能看到的数据质量问题：**
> 1. `total_charges` 有 11 个缺失值——可能是尚无计费历史的新客户
> 2. `last_complaint_date` 存储为字符串而非日期——你需要解析它
> 3. `monthly_charges` 有一些超过 $500 的极端值——值得检查是数据错误还是合法的企业账户
>
> 未检测到重复行。类别平衡：26% 流失，74% 保留。

你没有告诉智能体任何关于文件的信息。它通过读取你在上一个单元格中加载的 `df` 变量就推断出了
这一切。

---

## 示例 2 —— 编写你可以运行的代码（Chrome 中的 JupyterLab）

**谁：** 同一位数据科学家，继续示例 1。

**地点：** 同一个 notebook。

---

你添加一个新单元格并输入：

```
%%jiuwen --mode code
修复你提到的两个问题：
1. 填充缺失的 total_charges 值
2. 将 last_complaint_date 转换为合适的 datetime 列
编写代码让我可以立即运行。
```

智能体回复。在输出区域出现一个代码块：

```python
# 用 0 填充缺失的 total_charges（新客户还没有费用）
df["total_charges"] = df["total_charges"].fillna(0)

# 将 last_complaint_date 从字符串转换为 datetime
df["last_complaint_date"] = pd.to_datetime(df["last_complaint_date"], errors="coerce")

print("剩余缺失值：", df[["total_charges", "last_complaint_date"]].isnull().sum().to_dict())
print("last_complaint_date dtype：", df["last_complaint_date"].dtype)
```

你把它复制到新单元格并运行。输出显示：

```
剩余缺失值： {'total_charges': 0, 'last_complaint_date': 0}
last_complaint_date dtype: datetime64[ns]
```

两个问题都修复了。

---

## 示例 3 —— 智能体为你插入代码单元格（带侧边栏面板的 JupyterLab）

**谁：** 与示例 2 相同场景，但你安装了 JupyterLab 侧边栏面板。

**地点：** Chrome 中的 JupyterLab，左侧打开侧边栏聊天面板。

**所需设置（一次性）：** 侧边栏面板不包含在基础 `pip install` 中。你需要构建一次 TypeScript
前端：

```bash
cd packages/frontend && npm install && npm run build
cd ../..
pip install -e .
jupyter labextension develop --overwrite .
```

之后重启 JupyterLab，图标出现。示例 1 和 2 无需这些即可工作。

---

你点击左侧边栏中的 JiuwenSwarm 图标。聊天面板打开——看起来像 IDE 插件的聊天界面，显示在
JupyterLab 左侧面板中，而你的 notebook 在右侧保持打开。

你在聊天输入框中输入：

> 修复 df 中的两个数据质量问题，并把代码直接放进我的 notebook

智能体在聊天中回复，同时**你的 notebook 中自动出现一个新代码单元格**——你没有复制任何东西。
该单元格已包含：

```python
# 修复缺失的 total_charges
df["total_charges"] = df["total_charges"].fillna(0)

# 将 last_complaint_date 转换为 datetime
df["last_complaint_date"] = pd.to_datetime(df["last_complaint_date"], errors="coerce")
```

你只需在该单元格中按 **Shift+Enter** 运行即可。完成。

这是智能体自动调用 `insert_notebook_cell` 工具。你从未显式要求它——智能体决定交付代码的最佳
方式是把代码直接放进 notebook，而不是仅在聊天中显示。

---

## 示例 4 —— 多智能体研究（Chrome 中的 JupyterLab，团队模式）

**谁：** 一位想为新项目选择最佳梯度提升库的 ML 工程师。

**地点：** Chrome 中的 JupyterLab。

---

你输入：

```
%%jiuwen --mode team
我需要为表格分类任务在 XGBoost、LightGBM 和 CatBoost 之间做选择。
请并行研究每一个，并给出涵盖以下内容的对比：
- 大型数据集上的训练速度
- 对类别特征的处理
- 超参数调优的难易程度
- 2025 年的社区支持和维护状态
```

按 **Shift+Enter**。

在输出区域出现一行小状态：

> *3 个智能体活跃——正在研究 XGBoost、LightGBM、CatBoost...*

约 90 秒后，回复流式进入：

> **XGBoost**
> 训练速度：CPU 上快，GPU 支持出色（通过 `device="cuda"`）...
> 类别特征：必须手动编码（标签或独热）...
>
> **LightGBM**
> 训练速度：由于基于直方图的切分，在大数据集上三者中最快...
> 类别特征：通过 `categorical_feature` 参数原生支持...
>
> **CatBoost**
> 训练速度：大数据集上比 LightGBM 慢，但内部处理类别特征，无需预处理...
>
> **建议：** 对你的用例（表格分类、大数据集），LightGBM 是最快的起点。如果你有大量高基数
> 类别列并想避免预处理，使用 CatBoost。如果需要 GPU 训练，XGBoost 仍是最安全的选择。

三个智能体同时运行——每个库一个。你 90 秒就得到答案，而非手动阅读 4–5 分钟。

---

## 示例 5 —— 命名会话：一个线程做研究，另一个写代码（任意 Jupyter）

**谁：** 一位想把文献综述与实现笔记分开的研究人员。

**地点：** 任意 Jupyter 环境。

---

**单元格 1** —— 开始研究对话：

```
%%jiuwen --session research
为我找到 3 篇关于表格数据对比学习的最新论文。
每篇用 2 句话总结。
```

智能体回复三篇论文摘要。

**单元格 2** —— 在同一个 notebook 中，开始独立的编码线程：

```
%%jiuwen --session coding
为我的 CSV 文件编写一个 PyTorch Dataset 类。
文件列有：features（全部 float64）和 target（0/1）。
```

智能体回复一个完整的 `TabularDataset` 类。

**单元格 3** —— 回到研究线程继续：

```
%%jiuwen --session research
基于你找到的论文，哪种技术最容易从零实现？
```

智能体记得单元格 1 中的三篇论文，并基于它们给出建议——因为这个单元格使用
`--session research`，而非编码线程。

两个对话从不混淆。

---

## 示例 6 —— 在 PyCharm 中工作

**谁：** 一位偏好 PyCharm 并使用其内置 Jupyter notebook 支持的开发者。

**地点：** PyCharm Professional，IDE 内打开 Jupyter notebook（非浏览器）。

---

PyCharm 在嵌入式 Jupyter 内核中运行 notebook。你无需启动任何 JiuwenSwarm 服务器——PyCharm
在打开 notebook 时启动内核，JiuwenSwarm 在其中作为普通 Python 导入加载。无额外进程、无端口。

你在 PyCharm 中打开 notebook，在第一个单元格中运行 `%load_ext jiuwenswarm_jupyter`，然后在
新单元格中：

```
%%jiuwen --mode code
我有一个名为 `prices` 的列表，包含每日股票价格的浮点数。
编写一个计算 20 天滚动平均值并返回新列表的函数。
```

输出出现在 PyCharm 单元格输出区域，实时流式输出，与浏览器中完全相同。你得到一个可以立即调用
的 `rolling_average()` 函数。

> **注意：** JupyterLab 侧边栏面板在 PyCharm 中不可用——那需要基于浏览器的 JupyterLab。
> 所有单元格魔法和 notebook 工具在 PyCharm 中正常工作。

---

## 示例 7 —— 检查训练好的模型

**谁：** 一位刚训练好模型并希望智能体评估它的 ML 工程师。

**地点：** Chrome 中的 JupyterLab。

---

你在单元格 1–4 中训练模型。训练后，你的命名空间有：
- `model` —— 一个 scikit-learn RandomForestClassifier
- `X_test`、`y_test` —— 测试数据
- `y_pred` —— 预测

你添加一个新单元格：

```
%%jiuwen
查看 model 变量以及 y_test 和 y_pred 数组。
计算主要分类指标，并告诉我是否存在类别不平衡问题。
```

在后台，智能体调用 `read_variable("model")` 并得到：

```
model: RandomForestClassifier
n_estimators=200, max_depth=12, class_weight=None
...
```

它还调用 `read_variable("y_test")` 和 `read_variable("y_pred")`，获得完整形状和分布信息。

它回复：

> **分类指标：**
> - 准确率：0.87
> - 精确率（类别 1）：0.61
> - 召回率（类别 1）：0.43
> - F1（类别 1）：0.50
>
> **类别不平衡问题：是。**
> 你的测试集有 2,400 个负例和只有 310 个正例（87%/13% 划分）。
> 使用 `class_weight=None`，模型偏向多数类——这解释了类别 1 的召回率偏低。
>
> **建议修复：** 使用 `class_weight="balanced"` 重新训练，或使用 SMOTE 对少数类过采样。

你没有向提示粘贴任何数据。智能体直接从你的 notebook 读取变量。

---

## 示例 8 —— 快速单行问题（任意 Jupyter）

**谁：** 任何人。

**地点：** 任意 Jupyter 环境中的任意单元格。

---

你在工作时需要快速回答，不想写完整单元格：

```python
%jiuwen scikit-learn 中 fit() 和 fit_transform() 有什么区别？
```

答案立即出现在输出区域：

> `fit()` 从训练数据计算参数（例如缩放器的均值和标准差）并存储它们——它不返回转换后的数据。
> `fit_transform()` 一步完成两件事：计算参数并返回转换后的数据。它是 `fit(X).transform(X)`
> 的简写。
>
> **经验法则：** 在训练数据上使用 `fit_transform()`。在测试或生产数据上只用 `transform()`
> （绝不用 `fit_transform()`）——否则你会把测试统计信息泄漏到预处理中。

---

## 示例 9 —— Google Colab

**谁：** 一位在 Google Colab（浏览器中的免费云端 notebook）中做机器学习作业的学生。

**地点：** Google Colab —— colab.research.google.com，在 Chrome 中运行。

---

在 Colab notebook 顶部，第一个单元格：

```python
!pip install jiuwenswarm-jupyter jiuwenswarm -q
%load_ext jiuwenswarm_jupyter
```

这可行是因为 Colab 使用标准 IPython 内核。运行后，该魔法在本次会话的剩余时间内可用。

在下一个单元格：

```
%%jiuwen --mode code
我需要在不使用 sklearn 的情况下从零实现 k 折交叉验证。
该函数应接受 X、y、一个模型和 k 作为输入。
```

智能体流式输出完整实现。学生可以立即在下一个单元格中运行它。

> **注意：** JupyterLab 侧边栏面板在 Google Colab 中不可用——Colab 有自己的前端，不支持
> JupyterLab 扩展。所有单元格魔法和 notebook 工具正常工作。对于嵌入式聊天界面，使用
> `%jiuwen_chat`。

---

## 示例 10 —— 用 `%jiuwen_error` 调试

**场景：** 一位数据科学家正在预处理数据集，遇到一个令人困惑的 KeyError。

**单元格 1 —— 引发错误：**

```python
df["normalised"] = (df["revenue"] - df["revenue"].mean()) / df["revenue"].std()
df["label_encoded"] = df["category"].map(label_map["category"])
# KeyError: 'category'
```

**单元格 2 —— 用一条命令将错误发送给智能体：**

```
%jiuwen_error
```

该魔法自动读取完整回溯和失败单元格源码，然后发送给智能体。输出：

```
[jiuwenswarm] 正在将上次错误发送给智能体…

键 'category' 在 label_map 中缺失。该字典只包含：
{'product_type': ..., 'region': ...}

你可能是想说 label_map["product_type"]——这里是修正后的行：
    df["label_encoded"] = df["category"].map(label_map["product_type"])

或者，如果 "category" 应该存在，请检查 label_map 是如何构建的。
```

你可以同一行添加自己的注释：

```
%jiuwen_error 并确保该列中的 NaN 值也被处理
```

---

## 示例 11 —— 用 `%jiuwen_config` 配置默认值

**场景：** 一位研究人员希望本 notebook 始终使用团队模式和更长的超时，而不用在每个单元格输入
标志。

**一次性设置单元格：**

```
%jiuwen_config mode=team timeout=600
```

输出：

```
mode          : team
timeout       : 600
inject_context: True
model         : (from config.yaml)
```

从现在起，此 notebook 中每个 `%%jiuwen` 单元格默认使用团队模式和 10 分钟超时。单个单元格仍可
覆盖：

```
%%jiuwen --mode agent --timeout 30
快速一句话回答：什么是 p 值？
```

随时查看当前配置：

```
%jiuwen_config
```

---

## 示例 13 —— 嵌入式完整聊天界面（`%jiuwen_chat`）

**谁：** 一位使用 Google Colab 且想要 GUI 而非单元格魔法语法的数据科学家。

**地点：** Google Colab（或任何没有 JupyterLab 侧边栏的环境）。

---

加载扩展后，在任意单元格运行：

```python
%jiuwen_chat
```

单元格输出区域变成一个完全可交互的聊天面板——与 JupyterLab 侧边栏使用的主题界面相同。底部
文本输入接受查询；回复以 markdown 渲染、代码块和可折叠工具调用卡片流式输出。

面板通过 Jupyter comm 通道连接到运行中的内核。它与你的 `%%jiuwen` 单元格共享同一会话——你
可以在同一个 notebook 中混合使用魔法单元格和聊天面板。

**高度控制：**

```python
%jiuwen_chat --height 700   # 更高的面板，适合长对话
```

**`%jiuwen_chat` 内部可用：**

- 通过模式选择器使用全部四种智能体模式（`agent`、`code`、`team`、`code.team`）
- 会话持久化——如果你回滚到该单元格，同一对话继续
- Notebook 上下文注入——智能体看到你的变量和最近的单元格
- 带打字指示器的流式回复渲染
- 工具调用显示（显示智能体做了什么的可折叠卡片）

**在 JupyterLab 中：** 侧边栏面板是首选，但 `%jiuwen_chat` 那里也有效。两者连接到同一内核——
在特定输出单元格旁同时显示聊天面板很有用。

---

## 总结 —— 什么在哪里可用

**JiuwenSwarm 需要作为独立进程运行吗？**
不需要。与 IDE 插件（连接 18092 端口上的服务器）不同，这个 Jupyter 集成将 JiuwenSwarm 直接
作为 Python 库导入 notebook 内核。你只需要 `pip install jiuwenswarm jiuwenswarm-jupyter` 和
一个配置文件——无需启动或保持运行任何东西。

| 功能 | JupyterLab（Chrome） | PyCharm | Google Colab | VS Code Notebooks |
|---|---|---|---|---|
| 需要独立 JiuwenSwarm 服务器？ | **否** | **否** | **否** | **否** |
| 除 `pip install` 外额外设置？ | 仅侧边栏 | 否 | 否 | 否 |
| `%%jiuwen` 单元格魔法 | 是 | 是 | 是 | 是 |
| `%jiuwen` 行魔法 | 是 | 是 | 是 | 是 |
| `%jiuwen_error` —— 转发上次异常 | 是 | 是 | 是 | 是 |
| `%jiuwen_config` —— 每 notebook 设置 | 是 | 是 | 是 | 是 |
| `%jiuwen_export` —— 保存对话历史 | 是 | 是 | 是 | 是 |
| `%jiuwen_replay` —— 在新会话中继续 | 是 | 是 | 是 | 是 |
| `%jiuwen_pin` / `%jiuwen_unpin` | 是 | 是 | 是 | 是 |
| 上下文注入（变量、DataFrame） | 是 | 是 | 是 | 是 |
| 命名会话 | 是 | 是 | 是 | 是 |
| 跨内核重启的会话持久化 | 是 | 是 | 是 | 是 |
| 多智能体团队模式 | 是 | 是 | 是 | 是 |
| 单元格中的流式输出 | 是 | 是 | 是 | 是 |
| `read_variable()` | 是 | 是 | 是 | 是 |
| `read_notebook_cell()` | 是 | 是 | 是 | 是 |
| `insert_notebook_cell()` —— 显示块回退 | 是 | 是 | 是 | 是 |
| `%jiuwen_chat` —— 嵌入式完整聊天界面 | 是 | 否 | 是 | 否 |
| JupyterLab 侧边栏聊天面板 | 是 | 否 | 否 | 否 |
| 会话列表面板（侧边栏） | 是 | 否 | 否 | 否 |
| Swarm map 面板（侧边栏） | 是 | 否 | 否 | 否 |
| `insert_notebook_cell()` —— 实际单元格插入 | 是（侧边栏） | 否 | 否 | 否 |
| 智能体生成的单元格标记（metadata） | 是（侧边栏） | 否 | 否 | 否 |
| 键盘快捷键（`Cmd+Shift+J` / `N`） | 是（侧边栏） | 否 | 否 | 否 |
| 状态栏指示器 | 是（侧边栏） | 否 | 否 | 否 |
