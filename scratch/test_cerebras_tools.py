import urllib.request
import json

api_key = "csk-xmdfvw9944fk9rxw2vjyctty5reynyvd2rntk2mewvy3ey9r"

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "CommandLine": {"type": "string", "description": "The command line string"}
                },
                "required": ["CommandLine"]
            }
        }
    }
]

payload = {
    "model": "gpt-oss-120b",
    "messages": [
        {"role": "system", "content": "You are frAIday, an autonomous coding agent."},
        {"role": "user", "content": "Check python version using terminal command."}
    ],
    "tools": tools,
    "temperature": 0.1
}

req = urllib.request.Request(
    "https://api.cerebras.ai/v1/chat/completions",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "frAIday-Agent/1.0"}
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        msg = res['choices'][0]['message']
        print("Cerebras tool_calls:", json.dumps(msg.get('tool_calls'), indent=2))
        print("Cerebras content:", msg.get('content'))
except urllib.error.HTTPError as e:
    print("Cerebras HTTP Error:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
