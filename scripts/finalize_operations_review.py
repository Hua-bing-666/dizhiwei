"""Connect existing browser receipts to current files; no physical validation implied."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables'
def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))

operations = read('界面验收记录.json')
research = read('研究资料界面验收记录.json')
assert operations['status'] == research['status'] == 'passed'
assert operations['source_sha256'] == hashlib.sha256((OUT / 'index.html').read_bytes()).hexdigest(), 'Browser receipt is stale'
assert len(operations['navigation_checks']) == len(operations['replay_checks']) == 24
assert len(operations['workflow_checks']) == 16
assert len(operations['export_checks']) == 3
assert not operations['console_errors'] and not operations['external_requests']

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.local = []
    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == 'a' and 'href' in fields:
            url = urlsplit(fields['href'])
            if not url.scheme and url.path:
                self.local.append(unquote(url.path))

link_checks = []
for page in ['index.html', '研究与答辩资料.html']:
    parser = Links()
    parser.feed((OUT / page).read_text(encoding='utf-8'))
    for relative in sorted(set(parser.local)):
        target = (OUT / relative).resolve()
        assert target.is_file(), f'Missing link: {page} -> {relative}'
        link_checks.append({'page': page, 'path': relative, 'exists': True})

# This turn is restricted to the website and planning: ensure original authoring
# artifacts are byte-for-byte identical to the prior committed deliverables.
unchanged = []
for name in ['大创申报书_模板填写稿.docx', '大创申报书_模板审阅版.pdf', '项目书审阅版.pdf', '立项答辩.pptx', '立项答辩审阅版.pdf']:
    current = (OUT / name).read_bytes()
    prior = subprocess.run(['git', 'show', 'HEAD:deliverables/' + name], cwd=ROOT, capture_output=True, check=True).stdout
    assert current == prior, f'Unexpected material change: {name}'
    unchanged.append({'path': name, 'sha256': hashlib.sha256(current).hexdigest(), 'unchanged_from_pre_turn_commit': True})

report = read('交付检查.json')
report['browser_artifact'] = '研究与答辩资料.html'
report['operations_site'] = {
    'artifact': 'index.html', 'status': operations['status'],
    'navigation_checks': len(operations['navigation_checks']),
    'replay_checks': len(operations['replay_checks']),
    'workflow_checks': len(operations['workflow_checks']),
    'export_files': len(operations['export_checks']),
    'source_sha256': operations['source_sha256'],
}
report['local_link_checks'] = link_checks
report['unchanged_materials'] = unchanged
(OUT / '交付检查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(f'Current browser receipt matched; {len(link_checks)} local links exist; 5 Word/PDF/PPT artifacts unchanged.')
