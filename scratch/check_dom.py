import subprocess
import tempfile

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
with tempfile.TemporaryDirectory() as tmpdir:
    res = subprocess.run([
        chrome_path,
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--virtual-time-budget=2500',
        f'--user-data-dir={tmpdir}',
        '--dump-dom',
        'http://localhost:8080/'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=12)
    dom = res.stdout
    print('DOM length:', len(dom))
    print('Has file-tree-container:', 'file-tree-container' in dom)
    print('Has iframe src:', 'src="/workspace' in dom or 'src="http' in dom)
    for line in dom.splitlines():
        if 'id="live-preview-frame"' in line or 'id="sidebar-file-tree"' in line or 'id="preview-address-display"' in line:
            print('SNIP:', line.strip())
