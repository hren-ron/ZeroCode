

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