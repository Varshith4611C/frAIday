import json
import urllib.request
import urllib.error

API_KEY = "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"
URL = "https://api.groq.com/openai/v1/chat/completions"

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in workspace terminal",
            "parameters": {
                "type": "object",
                "properties": {
                    "CommandLine": {"type": "string", "description": "The exact shell command line to run"}
                },
                "required": ["CommandLine"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "TargetFile": {"type": "string", "description": "Relative file path"},
                    "CodeContent": {"type": "string", "description": "Full file content"}
                },
                "required": ["TargetFile", "CodeContent"]
            }
        }
    }
]

messages = [
    {
        "role": "system",
        "content": "You are frAIday, an autonomous AI software engineer. When asked to build a project, you write files using write_to_file and run commands using run_command."
    },
    {
        "role": "user",
        "content": "Check python version using terminal command."
    }
]

payload = {
    "model": "openai/gpt-oss-120b",
    "messages": messages,
    "tools": tools,
    "tool_choice": "auto",
    "temperature": 0.1,
    "max_tokens": 1000
}

req = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode('utf-8'),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "frAIday-Agent/1.0"
    }
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        msg = res['choices'][0]['message']
        print("Turn 1 Message content:", msg.get('content'))
        print("Turn 1 Tool calls:", json.dumps(msg.get('tool_calls'), indent=2))

        # Turn 2: Feed an error back and see if the agent self-heals!
        messages.append(msg)
        tool_call = msg['tool_calls'][0]
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": tool_call["function"]["name"],
            "content": json.dumps({"stdout": "", "stderr": "'python3' is not recognized as an internal or external command. Use 'python' instead.", "exit_code": 1})
        })

        payload["messages"] = messages
        req2 = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "frAIday-Agent/1.0"
            }
        )
        with urllib.request.urlopen(req2, timeout=30) as resp2:
            res2 = json.loads(resp2.read().decode('utf-8'))
            msg2 = res2['choices'][0]['message']
            print("\nTurn 2 Content:\n", msg2.get('content'))
            print("Turn 2 Tool calls:", json.dumps(msg2.get('tool_calls'), indent=2))


except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Error:", str(e))
