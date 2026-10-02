"""Package public-to-this-private-project materials, excluding scratch references."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'deliverables/申报材料与证据包.zip'
selected=[]
for base in ['application','docs','simulation','scripts','deliverables',
             'projects/drip-research_ppt169_20261002/analysis',
             'projects/drip-research_ppt169_20261002/sources',
             'projects/drip-research_ppt169_20261002/svg_output',
             'projects/drip-research_ppt169_20261002/svg_final',
             'projects/drip-research_ppt169_20261002/notes',
             'projects/drip-research_ppt169_20261002/validation']:
    selected.extend(p for p in (ROOT/base).rglob('*') if p.is_file()
                    and '__pycache__' not in p.parts and p!=target
                    and p.suffix not in ['.pyc','.log'] and p.name!='.env')
selected += [ROOT/'README.md',ROOT/'附件1：塔里木大学大学生创新训练项目申报书.doc']
selected += list((ROOT/'projects/drip-research_ppt169_20261002').glob('*.md'))
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(set(selected)):
        z.write(path,path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert not any(n.startswith(('tmp/','output/')) for n in z.namelist())
    evidence=json.loads(z.read('deliverables/证据清单.json'))
    for entry in evidence['entries']:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
    print('Bundle verified:',len(z.namelist()),'files;',len(evidence['entries']),'evidence hashes;',target.stat().st_size,'bytes')
