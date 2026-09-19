import urllib.request
import json

api_key = "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"

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {api_key}", "User-Agent": "frAIday-Agent/1.0"}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Groq models:", [m['id'] for m in data.get('data', [])])
except Exception as e:
    print("Error:", e)
