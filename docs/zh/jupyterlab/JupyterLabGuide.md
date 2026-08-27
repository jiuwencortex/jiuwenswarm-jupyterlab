# 用户指南 —— 面向 Jupyter 的 JiuwenSwarm

## 安装

```bash
pip install jiuwenswarm-jupyter
```

JupyterLab 侧边栏面板需要构建 TypeScript 前端。完整的构建和安装步骤见
[PUBLISHING.md](../../../jupyterlab/publishing/PUBLISHING.md)。

## 加载扩展

### 方案 A —— 每次会话加载一次

在 notebook 的第一个单元格中添加：

```python
%load_ext jiuwenswarm_jupyter
```

### 方案 B —— 每次 notebook 启动时自动加载

添加到 `~/.ipython/profile_default/ipython_config.py`：

```python
c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]
```

如果文件不存在，请用以下命令创建：

```bash
ipython profile create
```

加载后，一行状态消息确认环境：

- `[JiuwenSwarm] 侧边栏已连接——JupyterLab comm 已激活。`——侧边栏面板可用，且已连接到此内核。
- `[JiuwenSwarm] 无侧边栏运行——单元格插入将使用显示块。`——扩展已加载，但 JupyterLab 前端
  不存在。所有单元格魔法、notebook 工具和 Python API 正常工作；
  `insert_notebook_cell`/`replace_notebook_cell` 会显示输出块，而非就地编辑 notebook。

---

## 单元格魔法 —— `%%jiuwen`

`%%jiuwen` 魔法将单元格正文发送给智能体，并将回复流式输出到单元格输出区域。

### 基本用法

```
%%jiuwen
解释 `df` 数据框包含什么。
```

```
%%jiuwen
与目标列相关性最高的特征有哪些？
```

### 智能体模式

JiuwenSwarm 支持四种模式：

| 模式 | 作用 |
|---|---|
| `agent`（默认） | 通用推理和工具使用 |
| `code` | 针对代码生成和执行优化 |
| `team` | 并行生成多个专业智能体 |
| `code.team` | 团队模式，专用于代码任务 |

```
%%jiuwen --mode code
使用分层采样对目标列进行训练/测试划分。
```

```
%%jiuwen --mode team
研究表格数据上 XGBoost 的前 3 个替代方案。
为每个库分配一个智能体，在数据集上分别评测，然后生成对比表。
```

### 命名会话

默认情况下，notebook 中所有 `%%jiuwen` 单元格共享一个持久会话——智能体记得之前的交流。

使用 `--session` 创建独立的对话线程：

```
%%jiuwen --session research
查找三篇关于不平衡数据集特征选择的论文。
```

```
%%jiuwen --session coding
基于上述研究编写特征选择流水线。
```

每个命名会话都有自己的对话历史。

### 跳过上下文注入

扩展会自动将 notebook 变量摘要和最近的单元格历史注入每个请求。如需干净的提示，请禁用它：

```
%%jiuwen --no-context
法国的首都是什么？
```

### 超时

```
%%jiuwen --timeout 600
对 5 个模型运行完整超参数搜索并总结结果。
```

---

## 行魔法 —— `%jiuwen`

用于简短的单行查询：

```python
%jiuwen df 的形状是什么？
```

---

## `%jiuwen_config` —— 每 notebook 设置

查看或更改应用于当前 notebook 中所有 `%%jiuwen` 单元格的配置默认值：

```
%jiuwen_config                       # 显示当前设置
%jiuwen_config mode=code             # 设置默认智能体模式
%jiuwen_config timeout=600           # 更改默认超时（秒）
%jiuwen_config inject_context=false  # 禁用自动上下文注入
%jiuwen_config model=gpt-4o          # 为此 notebook 覆盖模型
%jiuwen_config reset                 # 恢复所有默认值
```

| 设置 | 默认值 | 说明 |
|---|---|---|
| `mode` | `agent` | 智能体模式：`agent`、`code`、`team`、`code.team` |
| `timeout` | `300` | 请求超时（秒） |
| `inject_context` | `true` | 自动注入 notebook 变量和单元格历史 |
| `model` | _（来自 config.yaml）_ | 覆盖已配置的模型 |
| `pinned_vars` | `[]` | 无论其他设置如何都始终注入的变量 |

配置存储在 notebook 命名空间的 `_jiuwen_config` 中。单个 `%%jiuwen --mode code` 标志仍只覆盖
该单元格的配置。

---

## `%jiuwen_error` —— 将上次异常转发给智能体

当单元格抛出错误时，请紧跟其后运行：

```
%jiuwen_error
```

该魔法会自动读取异常回溯和失败单元格的源码，然后发送给智能体。你可以同在一行添加上下文：

```
%jiuwen_error 解释为什么抛出 KeyError
%jiuwen_error 并针对所有列建议一个避免此问题的修复
```

智能体会收到完整回溯和失败单元格源码——你无需手动复制任何内容。

---

## `%%jiuwen_explain` —— 运行单元格并即时获得解释

正常执行单元格正文，然后流式输出代码做了什么以及输出含义的解释。解释采用适合作为叙述性
markdown 单元格插入的风格。

```
%%jiuwen_explain
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

```
%%jiuwen_explain
df = df.groupby("category").agg({"revenue": "sum", "units": "mean"}).reset_index()
df.head()
```

单元格先在 notebook 命名空间中执行。然后智能体收到源码和任何输出，并写出每一步发生了什么
的清晰解释。

---

## `%%jiuwen_test` —— 为单元格生成 pytest 测试

将单元格正文作为源码读取，并请智能体生成一整套 pytest 测试。单元格不会执行——只作为源码读取。
智能体将测试作为新代码单元格插入。

```
%%jiuwen_test
def normalize(df, cols):
    return (df[cols] - df[cols].mean()) / df[cols].std()
```

```
%%jiuwen_test --file tests/test_preprocessing.py
class FeatureEncoder:
    def fit(self, df): ...
    def transform(self, df): ...
```

`--file PATH` 将测试写入指定文件（如果已存在则追加），而非插入单元格。

---

## `%jiuwen_audit` —— 完整 notebook 健康扫描

收集所有已执行单元格和当前变量命名空间，然后发送给智能体进行结构化代码质量审查。

智能体检查：
- 死代码或不可达代码
- 未使用的导入
- 训练集和测试集之间的数据泄漏
- 可能在未见数据上静默失败的操作
- 硬编码路径和魔法数字
- 乱序执行依赖
- 内存密集型模式（`iterrows`、不必要的复制）
- 在 I/O 边界缺少错误处理

```
%jiuwen_audit
%jiuwen_audit --quick    # 仅要点列表总结，不引用代码
```

---

## `%jiuwen_story` —— 将 notebook 转换为叙述文档

按顺序读取所有已执行单元格，并请智能体生成一篇连贯的文档——博客文章、技术报告、学术论文或
教程——用散文叙述连接代码部分。结果写入 markdown 文件并流式输出。

```
%jiuwen_story
%jiuwen_story --output analysis.md --style report
%jiuwen_story --style tutorial
%jiuwen_story --output draft.md --style paper
```

| 风格 | 输出 |
|---|---|
| `blog`（默认） | 对话式、第一人称技术叙述 |
| `paper` | 摘要、引言、方法、结果、结论 |
| `tutorial` | 分步指南，在每个代码块前解释 |
| `report` | 执行摘要、发现、建议 |

---

## `%%jiuwen_profile` —— 分析单元格并解读结果

在 `cProfile` 下运行单元格正文，打印原始统计信息，然后将最慢的调用点发送给智能体进行诊断和
优化建议。

```
%%jiuwen_profile
for row in df.iterrows():
    process(row)
```

```
%%jiuwen_profile --top 30
result = [expensive_fn(x) for x in large_list]
```

`--top N` 控制智能体上下文中包含多少个最慢函数（默认：20）。

---

## `%%jiuwen_guard` —— notebook 单元格的契约式设计

将前置和后置条件声明为 Python 表达式。该魔法在执行前后评估它们，如果任何条件失败或抛出异常，
会自动调用智能体。

```
%%jiuwen_guard pre="df.notna().all().all()" post="result.shape[0] == df.shape[0]"
result = df.merge(lookup, on="id")
```

```
%%jiuwen_guard post="model is not None"
model = train(X_train, y_train)
```

```
%%jiuwen_guard pre="len(df) > 1000" post="accuracy > 0.8"
accuracy = evaluate(model, X_test, y_test)
```

条件通过时，打印一行确认。条件失败时，智能体收到失败的表达式、单元格源码和当前 notebook
上下文，并诊断哪里出了问题。

---

## `%jiuwen_memory` —— 持久化的跨 notebook 知识库

将笔记保存到存储在 `~/.jiuwenswarm/memory.json` 的个人知识库。笔记在内核重启和 notebook
关闭后仍然保留。`search` 命令检索匹配的笔记，并将其作为上下文发送给智能体。

```
%jiuwen_memory save "验证 AUC 在 200 棵 XGBoost 树后趋于平稳"
%jiuwen_memory save "在 customer_id 上合并会丢失约 3% 的行——已知数据质量问题"
%jiuwen_memory search "XGBoost 性能"
%jiuwen_memory list
%jiuwen_memory delete 3
%jiuwen_memory clear
```

搜索使用关键词匹配。找到结果时，会连同当前 notebook 上下文一起发送给智能体，以便它结合你当前
的工作对过去的发现进行推理。

---

## `%jiuwen_diff` —— 用智能体评论审查 git 变更

针对某个提交引用运行 `git diff`，并将 diff 发送给智能体，对变更内容以及是否有任何看起来有风险
或非预期的内容进行结构化审查。

```
%jiuwen_diff                   # 当前工作树 vs HEAD
%jiuwen_diff HEAD~3            # 最近 3 次提交
%jiuwen_diff main              # 当前分支 vs main
%jiuwen_diff HEAD~1 --stat     # 仅摘要（无完整补丁）
%jiuwen_diff HEAD~2 --file src/model.py
```

先打印原始 diff；随后是智能体评论。

---

## `%%jiuwen_safe` —— 运行前分析

将单元格正文发送给智能体进行静态副作用分析，**不执行它**。智能体报告写入的文件、网络调用、
数据变更、不可逆操作和异常路径，然后给出判定：`SAFE / CAUTION / HIGH RISK`。

```
%%jiuwen_safe
os.remove("data/raw/sensitive.csv")
shutil.rmtree("output/")
```

```
%%jiuwen_safe --run
df.to_sql("results", engine, if_exists="replace")
```

不带 `--run` 时，单元格不会执行——准备好后将代码复制到新单元格。带 `--run` 时，分析完成后
立即执行单元格。

---

## `%jiuwen_todo` —— 为未完成项起草实现

扫描每个已执行单元格中的 `# TODO`、`# FIXME`、`# HACK`、`# XXX`、`raise NotImplementedError`
和裸 `pass` 语句，然后发送给智能体起草具体实现。每个实现作为可运行的代码单元格插入。

```
%jiuwen_todo
%jiuwen_todo --list   # 仅打印找到的条目，不调用智能体
```

---

## `%jiuwen_panel` —— 交互式控制面板

在 notebook 单元格输出内打开一个 ipywidgets GUI——下拉框、滑块和文本框，替代 `%%jiuwen` 标志
语法：

```
%jiuwen_panel
```

需要 `ipywidgets`：

```bash
pip install ipywidgets
```

面板提供：
- 模式下拉框（`agent` / `code` / `team` / `code.team`）
- 超时滑块（30–3600 秒）
- 上下文注入开关
- 命名会话字段
- 查询文本框 + 发送按钮
- 就地渲染的流式输出

---

## `%jiuwen_chat` —— 嵌入的完整聊天界面

将完整的 JiuwenSwarm 聊天界面——与 JupyterLab 侧边栏面板使用的相同——直接嵌入单元格输出区域。
iframe 通过 Jupyter comm 通道连接到运行中的内核，因此所有智能体模式、会话持久化和 notebook
上下文注入都正常工作。

```
%jiuwen_chat               # 默认高度（520 px）
%jiuwen_chat --height 700  # 更高的面板
```

在无 JupyterLab 侧边栏的环境中最有用：

- **Google Colab** —— 输入查询、接收流式回复、切换模式
- **Kaggle Notebooks** —— 与 Colab 相同
- **经典 Jupyter Notebook** —— 浏览器嵌入面板替代侧边栏

在 JupyterLab 中，侧边栏面板是首选界面，但 `%jiuwen_chat` 在那里也有效。

嵌入的聊天界面支持与侧边栏相同的功能：
- 全部四种智能体模式（`agent`、`code`、`team`、`code.team`）
- 带 markdown 和代码块格式的流式回复渲染
- 工具调用显示（可折叠卡片）
- 会话持久化（与同一内核中的 `%%jiuwen` 使用同一会话）

> **注意：** `%jiuwen_chat` 要求注册 `jiuwenswarm` comm 目标，这在你 `%load_ext
> jiuwenswarm_jupyter` 时自动发生。在 JupyterLab 中，如果侧边栏和 `%jiuwen_chat` 单元格同时
> 打开，它们共享同一内核——一条消息会同时出现在两者中。

---

## `%jiuwen_clear` —— 重置对话上下文

在不重启内核的情况下开始新对话：

```
%jiuwen_clear                  # 清除默认会话
%jiuwen_clear research         # 清除特定的命名会话
```

`%jiuwen_clear` 创建新的会话 ID，并替换会话注册表和 `_jiuwen` 中的当前条目。此后智能体不再
记得之前的对话。命名会话可以单独清除。

清除后，会打印新的会话 ID：

```
[JiuwenSwarm] 默认会话已清除。新会话：jupyter_a1b2c3d4
```

---

## `%jiuwen_export` —— 将对话保存到文件

将会话的完整对话历史导出为当前目录中的 markdown 文件：

```
%jiuwen_export                              # 写入 jiuwen_session_<id>.md
%jiuwen_export my_research_notes.md        # 显式文件名
%jiuwen_export --session research notes.md # 导出命名会话
```

每次交流保存为带时间戳、模式、用户查询和智能体回复的编号章节。文件是人类可读的 markdown——
可在任意文本编辑器或 Jupyter markdown 单元格中打开。

---

## `%jiuwen_replay` —— 在新会话中继续

将最近 N 次对话交流作为上下文重新发送到全新会话。当对话偏离主题但你希望智能体记住关键结果时
很有用：

```
%jiuwen_replay        # 重放最近 3 次交流（默认）
%jiuwen_replay 5      # 重放最近 5 次交流
```

原会话不会被修改。创建新的默认会话并先发送重放的上下文，因此智能体在你继续之前确认历史。

---

## `%jiuwen_pin` / `%jiuwen_unpin` —— 始终包含的变量

固定特定变量，使它们始终注入智能体上下文，即使使用 `--no-context` 或自动扫描会跳过它们：

```
%jiuwen_pin df_train results_dict model     # 固定多个变量
%jiuwen_unpin df_train                      # 从固定列表移除一个
%jiuwen_unpin all                           # 清除所有固定变量
```

固定变量出现在上下文块顶部的**固定变量**部分，带完整类型摘要。在大型 notebook 中很有用，此时
自动上下文扫描会拾取太多无关变量。

当前固定列表在 `%jiuwen_config` 中可见：

```
%jiuwen_config
  pinned_vars          = ['df_train', 'model']
```

---

## Python API

用于编程式使用或异步 notebook：

```python
from jiuwenswarm_jupyter import JupyterSwarm

swarm = JupyterSwarm(mode="code")
result = await swarm.run("为 df 中的数值列编写一个归一化函数")
print(result)
```

`JupyterSwarm` 构造函数接受：
- `mode` —— 默认智能体模式（`"agent"`、`"code"`、`"team"`、`"code.team"`）
- `session_id` —— 显式会话 ID（未设置时自动生成为 `jupyter_<uuid>`）

`run()` 接受与魔法选项相同的所有关键字参数。

## 访问默认会话对象

当你运行 `%load_ext jiuwenswarm_jupyter` 时，默认 `JupyterSwarm` 实例会自动放入命名空间的
`_jiuwen` 中：

```python
print(_jiuwen.session_id)   # jupyter_abc123def456
print(_jiuwen.mode)         # agent
```

### 跨内核重启的会话持久化

扩展加载时会话 ID 保存到 `~/.jiuwenswarm/jupyter_sessions.json`。如果你重启内核并重新加载
扩展，会自动恢复相同的会话 ID：

```
[jiuwenswarm] 已恢复会话：jupyter_abc123def456
```

对话历史保存在服务器端，智能体会记得之前的交流。恢复的会话在 30 天后过期。

---

## JupyterLab 侧边栏面板

侧边栏面板需要 JupyterLab 4+ 并构建、安装 TypeScript 前端。

### 设置

```bash
cd packages/frontend
npm install && npm run build
cd ../..
pip install -e .
jupyter labextension develop --overwrite .
jupyter lab
```

### 使用面板

当 JupyterLab 在浏览器中打开时，左侧边栏会出现一个 JiuwenSwarm 图标。点击它打开聊天面板。

- 面板的工作方式与 `%%jiuwen` 相同——相同的智能体模式、相同的会话持久化、相同的上下文注入。
- 多智能体团队运行时，**Swarm Map** 标签页自动打开，显示实时智能体活动。
- JupyterLab 底部的状态栏显示连接状态、团队运行期间的活动智能体数、累计会话成本（当 API
  使用计费时），以及多个内核打开时的活动 notebook 名称。
- **会话面板**顶部有过滤输入框——输入可按标题跨所有内核筛选会话。

### 侧边栏面板

| 面板 | 说明 |
|---|---|
| **聊天** | 主对话面板——与 `%%jiuwen` 相同但可交互 |
| **会话** | 浏览和切换会话；按标题过滤；点击「+ 新建」开始一个 |

### 多个 notebook

你可以同时打开多个 notebook，每个都有自己的内核。侧边栏会自动处理：

- 当你**切换到不同的 notebook 标签页**时，聊天面板连接到该标签页的内核。你发送的所有消息
  都会发往焦点 notebook 的智能体。
- 连接多个内核时，**会话面板**按 notebook 分组显示会话。每个组以 notebook 文件名开头。
- 如果**内核重启**，侧边栏会自动重连，无需手动操作。
- 当**notebook 关闭**时，侧边栏与该内核断开，并从列表中移除其会话。

无需配置——正常打开多个 notebook 即可。

### 键盘快捷键

| 快捷键 | 操作 |
|---|---|
| `Cmd/Ctrl+Shift+J` | 打开聊天面板 |
| `Cmd/Ctrl+Shift+N` | 开始新会话 |

### 命令面板

按 `Ctrl+Shift+P`（Mac 上为 `Cmd+Shift+P`）→ 搜索「JiuwenSwarm」：

- `JiuwenSwarm: 打开聊天` —— 聚焦侧边栏聊天面板
- `JiuwenSwarm: 打开 Swarm Map` —— 打开智能体活动面板
- `JiuwenSwarm: 新会话` —— 开始新对话
- `JiuwenSwarm: 打开会话列表` —— 打开会话面板

---

## Notebook 工具

这四个函数可从任意单元格作为普通 Python 使用——无需魔法。智能体在需要检查你的 notebook 状态时
也会自动调用它们。

### `read_variable(name)`

检查当前 notebook 中的任意变量：

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

适用于 DataFrame、NumPy 数组、列表、字典、训练好的模型以及任何其他 Python 对象。

### `read_notebook_cell(cell_index)`

读取任意之前执行的单元格的源码和输出：

```python
from jiuwenswarm_jupyter import read_notebook_cell

info = read_notebook_cell(2)
print(info["source"])   # 你在单元格 2 中写的代码
print(info["output"])   # 它打印或返回的内容
```

### `insert_notebook_cell(source, cell_type, execute, confirm_execute)`

在 notebook 中插入一个新单元格：

```python
from jiuwenswarm_jupyter import insert_notebook_cell

# 插入单元格（用户手动运行）
insert_notebook_cell("print(df.describe())", cell_type="code")

# 插入并立即运行
insert_notebook_cell("print(df.describe())", cell_type="code", execute=True)

# 插入并在运行前请求确认
insert_notebook_cell(
    "df.drop(columns=['id'], inplace=True)",
    cell_type="code",
    execute=True,
    confirm_execute=True,
)
```

在**连接侧边栏的 JupyterLab** 中：单元格直接出现在 notebook 中。使用 `confirm_execute=True`
时，执行前会显示对话框。

在**其他环境**（经典 Notebook、Colab、VS Code Notebooks）中：源码以格式化块显示在单元格输出中。
使用 `confirm_execute=True` 时，通过 `input()` 提示用户。

### `replace_notebook_cell(cell_index, new_source)`

重写已有单元格，应用前显示前后 diff 供审查：

```python
from jiuwenswarm_jupyter import replace_notebook_cell

replace_notebook_cell(3, "df = df.dropna(subset=['target'])")
```

在**连接侧边栏的 JupyterLab** 中：出现 diff 对话框，显示旧源码（红色）和拟议替换（绿色）。
点击**应用**更新单元格，或**取消**丢弃。

在**其他环境**中：在单元格输出区域渲染彩色统一 diff。通过编辑单元格手动应用变更。

`cell_index` 使用与 `read_notebook_cell` 相同的零基执行历史刻度。

### 智能体生成的单元格标记

在 JupyterLab 中通过 `insert_notebook_cell` 插入的单元格会打上 `cell.metadata.jiuwen_generated
= true`。在其他环境中，插入的代码单元格以 `# [jiuwen] Generated by JiuwenSwarm` 开头，因此
在任何 Jupyter 环境中都可识别智能体生成的代码。

---

## 配置

JiuwenSwarm 从 `~/.jiuwenswarm/config/config.yaml` 读取其配置。这与 CLI、VS Code 插件和
JetBrains 插件使用的文件相同——无需单独的 Jupyter 配置。

---

## Google Colab

单元格魔法、notebook 工具和 Python API 无需额外设置即可在 Colab 中使用。JupyterLab 侧边栏
不可用——Colab 使用自己的前端。

**设置（notebook 的第一个单元格）：**

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
# 首次使用时创建配置文件：
!jiuwenswarm-init
%load_ext jiuwenswarm_jupyter
```

创建配置后，后续会话只需：

```python
!pip install jiuwenswarm jiuwenswarm-jupyter -q
%load_ext jiuwenswarm_jupyter
```

然后一切照常工作：`%%jiuwen`、`%jiuwen`、`%jiuwen_error`、`read_variable()` 等。

> **注意：** 在 Colab 中 `insert_notebook_cell(..., execute=True)` 会在输出区域显示代码——
> 直接插入单元格需要 JupyterLab 侧边栏。

---

## JupyterHub

所有单元格魔法和 notebook 工具无需更改即可在 JupyterHub 上使用。要使用侧边栏面板，请将扩展
安装到共享的 JupyterLab 环境中。

**多用户隔离：** 每个用户运行自己的内核和自己的进程内 `JiuWenSwarm` 实例。会话以
`os.getcwd()`（每用户主目录）为键，因此用户之间没有共享状态。

**为所有用户安装扩展（服务器管理员）：**

```bash
pip install jiuwenswarm jiuwenswarm-jupyter
jupyter labextension install @jiuwenswarm/jupyterlab  # 构建前端后
```

或在 JupyterHub `Dockerfile` 中：

```dockerfile
RUN pip install jiuwenswarm jiuwenswarm-jupyter && \
    cd /path/to/jiuwenswarm-jupyterlab && \
    npm install && npm run build && \
    pip install -e . && \
    jupyter labextension develop --overwrite .
```

每个用户仍需要自己的 `~/.jiuwenswarm/config/config.yaml`（每个用户账户运行一次
`jiuwenswarm-init`）。

---

## 远程 Jupyter 服务器

当通过 SSH 隧道或 `jupyter lab --ip=0.0.0.0` 连接远程 Jupyter 服务器时：

- 单元格魔法无需任何更改即可工作——它们在远程内核中运行。
- 侧边栏面板在本地浏览器中运行，但通过 Jupyter comm 协议与远程内核通信，并自动通过标准
  Jupyter 服务器 WebSocket 隧道传输。无需额外端口。
- `JiuWenSwarm` 必须安装在**远程**机器上，而非本地。

---

## 故障排查

**`ImportError: jiuwenswarm is not installed`**
安装核心包：`pip install jiuwenswarm`

**`%load_ext jiuwenswarm_jupyter` 后找不到魔法**
重启内核并重试。

**回复超时**
增加超时：`%%jiuwen --timeout 600`

**智能体看不到我的 DataFrame**
确保 DataFrame 赋值给变量（而非匿名）。上下文提取器从 `ip.user_ns` 读取，因此
`df = pd.read_csv(...)` 使 `df` 可见，但单独的 `pd.read_csv(...)` 不可见。

**JupyterLab 侧边栏图标不显示**
TypeScript 前端可能未构建。运行 `cd packages/frontend && npm install && npm run build`，然后
`jupyter labextension develop --overwrite .` 并重启 JupyterLab。

**侧边栏面板显示「已断开」**
comm 目标未注册。确保侧边栏连接前内核中运行了 `%load_ext jiuwenswarm_jupyter`。如果你在运行
任何单元格之前打开了 JupyterLab，请在任意单元格中运行 `%load_ext jiuwenswarm_jupyter`，然后
重新加载侧边栏。

**`insert_notebook_cell` 显示块而非插入**
未连接 JupyterLab 侧边栏时无法直接插入单元格。复制显示的代码并粘贴到新单元格中。

**`replace_notebook_cell` 显示 diff 而非对话框**
同样的情况——diff 显示在输出区域。通过编辑单元格并重新运行来手动应用变更。
