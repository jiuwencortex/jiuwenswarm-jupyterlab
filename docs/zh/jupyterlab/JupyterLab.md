# jiuwenswarm-jupyterlab

JiuwenSwarm 与 Jupyter notebook 和 JupyterLab 的集成。

直接在 notebook 工作流中运行单个智能体和多智能体 swarm——无需独立服务器、无需浏览器标签页、无需切换上下文。

## 特性

**可在任何 Jupyter 环境中使用（PyCharm、VS Code、Google Colab、JupyterLab）**
- `%%jiuwen` 单元格魔法——向智能体提问，在输出区域获得流式回答
- `%jiuwen` 行魔法——在任意单元格中发起单行查询
- `JupyterSwarm` Python API——以编程方式异步访问所有智能体模式
- Notebook 上下文注入——智能体自动看到你的变量、DataFrame、导入的包和最近的单元格历史
- 命名会话——在多个单元格间延续对话
- 多智能体团队模式——从单个单元格并行生成智能体
- `%%jiuwen_explain`——执行一个单元格并流式解释它做了什么以及为什么
- `%%jiuwen_test`——为任意函数或类生成完整的 pytest 测试套件
- `%jiuwen_audit`——完整 notebook 健康扫描：死代码、数据泄漏、坏模式、执行顺序问题
- `%jiuwen_story`——将所有已执行单元格转换为叙述性博客文章、报告、论文或教程
- `%%jiuwen_profile`——用 cProfile 分析单元格，然后获得智能体解读的瓶颈分析
- `%%jiuwen_guard`——声明前置/后置条件；智能体自动诊断违规
- `%jiuwen_memory`——持久化的跨 notebook 知识库：保存、搜索和检索发现
- `%jiuwen_diff`——对比任意 git 引用，获得智能体对变更的评论
- `%%jiuwen_safe`——运行有风险的单元格前进行静态副作用分析
- `%jiuwen_todo`——扫描 TODO/FIXME/NotImplementedError 并起草实现
- `%jiuwen_export`——将对话历史保存为 markdown 文件
- `%jiuwen_replay`——在新会话中继续，重放最近的上下文
- `%jiuwen_pin` / `%jiuwen_unpin`——固定始终注入上下文的变量
- `%jiuwen_chat`——将完整聊天界面直接嵌入单元格输出（Colab、Kaggle、经典 Notebook）

**JupyterLab 侧边栏面板（需要 JupyterLab 4+）**
- 侧边栏中的持久聊天面板——跨 notebook 标签页保持打开
- 带过滤和按 notebook 分组的会话列表面板
- Swarm map 面板——智能体团队活动的实时可视化
- 状态栏指示器——连接状态、活动智能体数、会话成本
- 多内核支持——切换 notebook 无需重连
- Python 内核 comm 桥——所有消息保持进程内，无外部服务器

**Notebook 原生智能体工具（所有环境）**
- `read_variable(name)`——检查任意 Python 变量：DataFrame、数组、模型
- `read_notebook_cell(index)`——智能体无需复制粘贴即可读取任意之前的单元格
- `insert_notebook_cell(source)`——智能体将可运行的代码单元格直接插入 notebook
- `replace_notebook_cell(index, source)`——智能体带 diff 对话框重写已有单元格

## 安装

```bash
# 核心（单元格魔法 + Python API，可在任何 Jupyter 环境中使用）
pip install jiuwenswarm-jupyter

# 完整版（包含 JupyterLab 侧边栏面板）
pip install jiuwenswarm-jupyter[lab]
jupyter labextension develop --overwrite .
```

## 快速开始

加载扩展：

```python
%load_ext jiuwenswarm_jupyter
```

向智能体提问：

```
%%jiuwen
分析数据框 `df`，找出与目标列相关性最高的三个特征。
```

生成代码：

```
%%jiuwen --mode code
使用分层采样对目标列进行训练/测试划分。
```

使用多智能体团队模式：

```
%%jiuwen --mode team
研究表格数据上 XGBoost 的前 3 个开源替代品。
为每个库分配一个智能体，在附加数据集上分别评测，并生成对比表。
```

一步执行并解释：

```
%%jiuwen_explain
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

分析与优化：

```
%%jiuwen_profile
for row in df.iterrows():
    process(row)
```

运行任何破坏性操作前检查代码：

```
%%jiuwen_safe
shutil.rmtree("output/")
```

在单元格中嵌入完整聊天界面（Colab / Kaggle / 经典 Notebook）：

```python
%jiuwen_chat
```

## 在 notebook 启动时自动加载

添加到 `~/.ipython/profile_default/ipython_config.py`：

```python
c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]
```

## 配置

JiuwenSwarm 配置从 `~/.jiuwenswarm/config/config.yaml` 读取（与 CLI 和 IDE 插件相同）。如果你已配置好 JiuwenSwarm，则无需额外设置。

## Notebook 原生工具

直接从任意单元格使用：

```python
from jiuwenswarm_jupyter import read_variable, read_notebook_cell, insert_notebook_cell

# 检查 DataFrame
print(read_variable("df"))

# 读取单元格 3 的输出
print(read_notebook_cell(3))

# 插入代码单元格（智能体在适当时自动执行）
insert_notebook_cell("print(df.describe())")
```

## 魔法参考

完整的魔法参考与使用示例见 [JupyterLabMagics.md](JupyterLabMagics.md)。

## 完整用户指南

每个魔法、Python API、侧边栏面板设置和环境专属说明的详细文档见
[JupyterLabGuide.md](JupyterLabGuide.md)。

## 示例

不同环境下的真实场景见 [JupyterLabExamples.md](JupyterLabExamples.md)。

## 许可证

MIT
