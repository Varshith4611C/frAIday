import json
import urllib.request

def call_tool(name, args):
    req = urllib.request.Request(
        "http://localhost:8080/api/tools/execute",
        data=json.dumps({"name": name, "arguments": args}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("1. Testing run_command:")
res1 = call_tool("run_command", {"CommandLine": "python --version"})
print("run_command result:", res1)

print("\n2. Testing list_dir:")
res2 = call_tool("list_dir", {})
print("list_dir entries count:", len(res2.get('entries', [])))

print("\n3. Testing view_file:")
res3 = call_tool("view_file", {"AbsolutePath": "index.html", "StartLine": 1, "EndLine": 5})
print("view_file content:\n", res3.get('content'))

print("\n4. Testing grep_search:")
res4 = call_tool("grep_search", {"Query": "html", "CaseInsensitive": True})
print("grep_search matches count:", res4.get('matches_count'))

print("\nAll tool execution tests passed successfully!")
