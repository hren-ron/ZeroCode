

## 2026.11.4

1. 打通自动修改和测试反馈闭环

完成完整的任务
```aiignore
用户提出修改需求
       ↓
Agent 分析项目
       ↓
读取相关代码
       ↓
调用 write_file 修改代码
       ↓
调用 run_command 运行 pytest
       ↓
分析测试结果
       ↓
测试失败？── 是 ──→ 继续修改
       │
       否
       ↓
向用户汇报修改结果
```

2. 让 Agent 修复一个已经存在的 Bug

实验设计：
- 手动准备一个存在错误的 Python 函数。
- 准备一个能够检测该错误的 pytest 测试。
- Agent 读取源代码和测试。
- Agent 运行 pytest，观察失败信息。
- Agent 修改错误代码。
- 再次运行 pytest，确认退出码为 0。


## 2026.11.3

1. 实现search code

在项目目录中按关键词搜索代码，返回匹配的文件路径、行号和代码内容。

工具提供以下参数：

| 参数              | 类型       | 默认值 | 说明|
|-----------------|----------|-----| ----- |
| query           | 	string  |	必填|	要搜索的关键词|
| path            | 	string  |	.|	搜索目录|
| file_pattern	   | string   | 	*	     |文件名匹配模式|
| case_sensitive	 | boolean  |	False|	是否区分大小写|
| max_results	    | integer	 | 50      | 	最大匹配行数 |

2. 验证 Agent 的自主代码分析能力

测试任务

分析 ZeroCode 项目中 Agent.run() 的执行流程，重点说明：
- 如何构造初始 messages？
- 如何调用 LLM？
- 如何识别和处理 tool_calls？
- 如何执行工具并将结果返回给 LLM？
- 什么情况下结束循环？
- 如何处理工具执行失败？

预期流程：
```aiignore
用户提出分析任务
       ↓
Agent.run()
       ↓
LLMClient.chat_with_tools()
       ↓
LLM 决定调用哪个工具
       ↓
list_files / search_code / read_file
       ↓
工具执行结果返回 LLM
       ↓
LLM 继续分析
       ↓
输出最终答案
```

3. 实现WriteFileTool

先实现最基础的文件写入，不引入 diff、patch、备份等复杂机制。

4. 实现 RunCommandTool

它将允许 Agent：
- 执行 Python 命令，例如 python main.py。
- 运行测试，例如 pytest -q。
- 获取命令的标准输出、错误输出和退出码。
- 根据执行结果判断问题，并决定是否修改代码。

建议下一步先实现一个最小版本：支持执行命令、设置超时时间、返回执行结果。暂时不扩展复杂的容器隔离和权限系统。

RunCommandTool 是 Coding Agent 从“能够修改代码”走向“能够验证代码”的关键工具。实现后，Agent 就可以形成这样的工作流程：

```aiignore
读取代码
   ↓
分析问题
   ↓
write_file 修改代码
   ↓
run_command 执行测试
   ↓
读取执行结果
   ↓
根据错误继续修复
```

一、先明确 MVP 功能
第一版只实现以下能力：

- 执行命令	支持 pytest -q、python main.py 等
- 指定工作目录	默认使用 Workspace 根目录
- 超时控制	默认 30 秒
- 捕获输出	获取 stdout、stderr
- 返回退出码	0 表示成功，非 0 表示失败

安全边界： 这个工具可以执行任意系统命令，因此第一版只允许在本地可信项目中使用，不要把它暴露给不可信用户或远程模型调用环境。暂时不实现复杂沙箱，但会避免通过命令字符串调用 Shell。

二、设计返回结果
建议统一返回字符串，让模型能够直接读取执行结果：
```aiignore
Command: pytest -q
Exit code: 1

STDOUT:
...

STDERR:
...
```

这样即使测试失败，Agent 也能看到错误信息，并决定下一步操作。

第一版我建议使用 list[str] 表示命令参数，而不是直接使用 Shell 命令字符串。

```aiignore
["pytest", "-q"]
["python", "main.py"]
["python", "-m", "compileall", "src"]
```
这样可以使用 subprocess.run() 的 shell=False 模式，避免 Shell 字符串解析带来的额外风险。

## 2026.11.2

1. 实现工具

- list_files
上面的实现是 MVP 版本，但有一个值得后续优化的地方：

Path.rglob() 的遍历顺序不保证稳定，当前代码是在遍历时达到 max_entries 就停止，最后才排序。

因此，多次运行时，达到上限时选中的文件可能不同。

MVP 阶段可以先接受这一点；如果希望结果稳定，可以在后续改成逐层排序遍历。


## 2026.11.1

1. 实现工具执行失败后的错误反馈机制（Tool Error Recovery）。

工具执行失败时，不应该让整个 Agent 立即退出，而应该把错误反馈给模型，让模型判断是否需要修正参数、换一种工具调用方式，或者向用户解释问题。

```aiignore
用户：读取 README.md

模型：调用 read_file("README.md")
                 |
                 v
工具：FileNotFoundError
                 |
                 v
Agent：将错误作为 tool 消息加入上下文
                 |
                 v
模型：根据错误重新判断
                 |
          +------+------+
          |             |
       再次调用工具    返回错误说明
```

2. 实现
区分可恢复错误与不可恢复错误，并限制模型反复调用同一个失败工具。

实际上异常有不同性质：

| 异常    | 示例                   | 处理策略   |
|-------|----------------------|--------|
| 参数错误  | ValueError、TypeError | 反馈模型   |
| 文件不存在 | 	FileNotFoundError   | 	反馈模型  |
| 权限不足	 | PermissionError	     | 反馈模型                 |
|工具不存在|	KeyError|	反馈模型|
|JSON 解析失败|	JSONDecodeError|	反馈模型|
|程序内部错误	|AttributeError、意外的 RuntimeError|	直接抛出|

这里的分类是初始策略。比如某些 RuntimeError 也可能是业务错误，后续可以通过自定义异常进一步细分。

3. 实现防止工具重复调用

- 对工具名称和参数生成 Fingerprint。 
- 记录失败的工具调用。
- 检测重复失败调用。
- 达到阈值后停止重试，并返回明确错误。

4. 实现Tool Timeout
实现工具执行超时控制。

这一阶段分成三个小步骤 
- 设计超时机制：理解同步函数、线程池和异步超时的区别。 
- 实现 ToolExecutor：统一管理工具执行和超时。 
- 接入 Agent：让 Agent 能够处理超时，并将结果反馈给模型。


with ThreadPoolExecutor(...) 退出时默认会等待正在运行的任务结束。因此，如果工具卡住 60 秒，即使 10 秒时抛出超时异常，退出 with 时仍可能等待剩余的 50 秒。

所以我们不能简单地把上面的代码直接当成完整的超时实现。

因此，我们把超时机制独立成一个 ToolExecutor，不直接塞进 Agent 或 ToolRegistry。

整体调用链调整为：

```aiignore
Agent
  |
  v
ToolExecutor
  |
  v
ThreadPoolExecutor
  |
  v
ToolRegistry.execute()
  |
  v
具体工具
```

这样职责比较清晰：
- ToolRegistry：负责工具注册、参数校验和实际调用。
- ToolExecutor：负责线程池调度、超时控制。
- Agent：负责模型交互、工具调用循环和错误反馈。

还有一个边界需要记住：**线程超时只能让调用方停止等待，不能杀死正在运行的工具线程。** 所以我们先实现调用方超时和线程池容量限制；以后如果需要强制终止不可信或可能永久卡死的工具，再考虑进程隔离。

5. 解决线程池资源耗尽问题

需要进一步考虑： 
- 如何限制等待队列长度？ 
- 如何避免超时任务无限占用线程？ 
- 如何避免重复创建线程池？ 
- Agent 退出时如何正确释放资源？

建议：先增加并发提交限制和资源管理，再接入 Agent。

还有一个架构原则：对于可能永久阻塞、需要强制终止的工具，最终应采用进程隔离，而不是依赖线程超时。

**使用 BoundedSemaphore 控制容量**

Python 的 ThreadPoolExecutor 虽然有 max_workers，但内部提交队列默认没有容量上限。
用 threading.BoundedSemaphore 增加一层容量控制

6. 完善 ToolExecutor 的资源生命周期管理

解决三个问题：
- 如何确保线程池在 Agent 退出时正确关闭？
- 如何避免重复调用 shutdown() 带来的问题？
- 是否需要支持 with ToolExecutor(...) as executor:？

7. 设计问题：如何避免 execute() 与 shutdown() 之间的竞态条件。

目前 execute() 和 shutdown() 之间还存在并发竞争：
- 线程 A 检查容量并获得 semaphore。
- 线程 B 调用 shutdown()，关闭线程池。
- 线程 A 调用 submit()，得到 RuntimeError。

目前这种情况虽然不会造成 semaphore 泄漏，但存在一个问题：execute() 没有明确检查执行器是否已经关闭，而是依赖底层线程池抛出异常。

- 明确关闭状态检查: 在 ToolExecutor 中增加一个私有方法


8. toolExecutor接入agent

职责分工如下：

- Agent
决定调用哪个工具、组织对话


- ToolExecutor
超时控制、并发限制、任务调度


- ToolRegistry
工具查找、参数校验、调用 Handler


- Builtin Tools
read_file 等实际工具

## 2026.10.31

实现agent loop:

1. User Input: 读取 README.md 并总结项目结构

2. Agent → LLM: 发送用户问题和可用工具描述

3. LLM 决策: 决定调用 read_file，参数为 README.md

4. ToolRegistry: Schema 校验 → Workspace 检查 → 读取文件

5. Tool Result: 将文件内容返回给 LLM

6. LLM 再次推理: 根据工具结果生成最终回答，或者继续调用其他工具


实现顺序分成五个小阶段：
1. 将 ToolSchema 转换成 OpenAI-compatible JSON Schema。
2. 修改 LLMClient，支持带工具定义的模型请求。
3. 实现 Agent 的消息管理和工具调用循环。
4. 增加最大循环次数、工具异常处理等保护机制。
5. 使用 Mock 编写 Agent Loop 测试，最后再连接本地 Ollama 实测。

OpenAI-compatible Tool Calling 接口，Ollama 是否支持当前模型的工具调用能力，还需要在最后进行实际验证。


工具调用的流程如下：

1. Agent

2. ToolRegistry.to_openai_tools()
导出工具定义

3. LLMClient.chat_with_tools()
模型决定是否调用工具

4. ToolRegistry.execute()
执行模型选择的工具

5. 将工具执行结果交回模型，继续循环，直到模型给出最终回答


agent loop的执行过程：
1. 用户输入：
请读取 README.md

2. LLM 请求：
chat_with_tools(messages, tools)

3. 判断模型响应：
是否包含 tool_calls？
没有工具调用，返回最终回答。存在工具调用，执行工具，保存执行结果

4. 工具执行完成后，将结果加入 messages，再次请求 LLM。

## 2026.10.28
当前已完成
- ToolParameter: 定义参数名称、类型、描述和是否必填。
- ToolSchema: 校验必填参数、未知参数、参数类型和重复定义。
- ToolRegistry: 集成工具执行前先校验参数，校验失败不会调用 handler。

下一步：实现 Workspace 路径管理

让 Agent 的文件操作统一经过 Workspace，并限制在指定的项目目录内。

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