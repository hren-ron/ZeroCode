# ZeroCodeAgent
A local software development agent

# 项目执行过程

## 第一步：确认配置

ZeroCode需要使用LLM，因此先配置LLM的API Key等参数。

如果使用云端大模型，则按以下步骤进行配置（以百炼大模型为例）。

2. 按照example.env中的字段，创建.env文件

```commandline
cp exmple.env .env
```

2. 检查项目根目录下的 .env，确认有以下四项：
```aiignore
BAILIAN_API_KEY=你的百炼API_KEY
BAILIAN_WORKSPACE_ID=你的工作空间ID
BAILIAN_BASE_URL=你的百炼API地址
BAILIAN_MODEL=你的模型名称
```

如果使用本地模型，则需要先在本地启动模型（以ollama为例）。

```aiignore
ollama run qwen2.5-coder:14b
```


## 第二步：安装依赖
```aiignore
python -m pip install -e ".[dev]"

```

## 第三步：执行测试
```aiignore
python -m pytest -v 
```

# 当前开发进展

## 2026.10.28
当前已完成

- ToolParameter: 定义参数名称、类型、描述和是否必填。
- ToolSchema: 校验必填参数、未知参数、参数类型和重复定义。
- ToolRegistry: 集成工具执行前先校验参数，校验失败不会调用 handler。

下一步：实现 Workspace 路径管理

按下面的顺序逐步实现：
1. 创建 Workspace 类，初始化项目根目录。
2. 实现 resolve_path()，将相对路径解析成绝对路径。
3. 拒绝访问工作区之外的路径，包括 .. 路径穿越。
4. 用 pytest 测试正常路径、文件不存在、路径穿越等情况。
5. 后续再实现 read_file 工具，将它注册到 ToolRegistry。

最终的调用关系会是：
1. Agent
2. ToolRegistry + Schema 校验
3. ReadFileTool
4. Workspace 路径安全检查
5. 本地项目文件

# 整体开发路线

按照从简单到复杂的顺序推进，每个阶段完成后再进入下一阶段。

- 搭建最小可运行项目

当前阶段：

创建项目目录、虚拟环境、依赖配置和入口程序，理解 Code Agent 的基本运行方式。

- 实现 LLM 调用与单 Agent

接收用户任务，调用模型，获得回答；再逐步引入工具调用，让 Agent 可以实际操作代码仓库。

- 实现代码仓库操作工具

文件搜索、文件读取、代码修改、Git 状态查询、命令执行和安全校验。

- 实现自动开发闭环

代码修改 → 测试 → 错误分析 → 自动修复 → 再次测试。

- 升级为多 Agent 系统

引入 Planner、Coding、Test、Review Agent，完成任务拆解、调度、状态管理和质量门禁。

- 完善工程化能力

Git worktree、Docker 隔离、任务恢复、评测体系、CI/CD 和部署审批。





