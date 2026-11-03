import httpx
from openai import OpenAI

http_client = httpx.Client(
    trust_env=False,
    timeout=httpx.Timeout(180.0),
)

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
    timeout=180,
    max_retries=0,
    http_client=http_client,
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search source code by keyword inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }
]

response = client.chat.completions.create(
    model="qwen2.5-coder:14b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a coding agent. "
                "You MUST use the search_code tool to find the Agent.run method. "
                "Do not output JSON as plain text."
            ),
        },
        {
            "role": "user",
            "content": "Find the Agent.run method in the current project.",
        },
    ],
    tools=tools,
    tool_choice="required",
    stream=False,
)

message = response.choices[0].message

print("Content:", message.content)
print("Tool calls:")

for call in message.tool_calls or []:
    print("Name:", call.function.name)
    print("Arguments:", call.function.arguments)


import httpx


url = "http://127.0.0.1:11434/api/chat"

payload = {
    "model": "qwen3.6:35b-a3b",
    "messages": [
        {
            "role": "user",
            "content": "Search for the Agent.run method."
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Search source code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ],
    "stream": False
}

with httpx.Client(
    trust_env=False,
    timeout=180,
) as client:
    response = client.post(url, json=payload)
    response.raise_for_status()

result = response.json()

print("Message:")
print(result.get("message"))

print("\nTool calls:")
print(result.get("message", {}).get("tool_calls"))