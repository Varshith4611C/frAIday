import urllib.request
import json

api_key = "csk-xmdfvw9944fk9rxw2vjyctty5reynyvd2rntk2mewvy3ey9r"

req = urllib.request.Request(
    "https://api.cerebras.ai/v1/models",
    headers={"Authorization": f"Bearer {api_key}", "User-Agent": "frAIday-Agent/1.0"}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Cerebras models:", [m['id'] for m in data.get('data', [])])
except Exception as e:
    print("Cerebras Error:", e)
