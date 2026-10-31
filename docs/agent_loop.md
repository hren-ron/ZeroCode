## 执行过程

1. User Input: 读取 README.md 并总结项目结构

2. Agent → LLM: 发送用户问题和可用工具描述

3. LLM 决策: 决定调用 read_file，参数为 README.md

4. ToolRegistry: Schema 校验 → Workspace 检查 → 读取文件

5. Tool Result: 将文件内容返回给 LLM

6. LLM 再次推理: 根据工具结果生成最终回答，或者继续调用其他工具