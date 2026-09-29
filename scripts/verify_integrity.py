"""Validate SHA-256 and the frozen numerical core; no dependencies needed."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'SHA256SUMS.json').read_text())
failed=[]
for n,h in manifest.items():
 p=ROOT/n
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:failed.append(n)
if failed:
 print(json.dumps({'status':'FAIL','changed_or_missing_files':failed},indent=2));sys.exit(1)
print(json.dumps({'status':'PASS','files_checked':len(manifest)},indent=2))
