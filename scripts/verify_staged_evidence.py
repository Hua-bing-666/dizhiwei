"""Verify manifest SHA256 against staged Git bytes, including line endings."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'deliverables/证据清单.json').read_text(encoding='utf-8'))['entries']
request=''.join(':'+entry['path']+'\n' for entry in entries).encode('utf-8')
data=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=request,capture_output=True,check=True).stdout
position=0
for entry in entries:
    end=data.index(b'\n',position);header=data[position:end].split()
    assert len(header)==3 and header[1]==b'blob',(entry['path'],header)
    length=int(header[2]);start=end+1;content=data[start:start+length]
    assert hashlib.sha256(content).hexdigest()==entry['sha256'],('Staged Git evidence differs',entry['path'])
    position=start+length+1
assert position==len(data)
print('Staged Git blobs match all',len(entries),'evidence hashes.')
