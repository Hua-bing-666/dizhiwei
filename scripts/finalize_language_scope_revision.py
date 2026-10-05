"""Record completed visual inspection without inferring it from machine checks."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'simulation/language_scope_review'
CURRENT = ROOT / 'tmp/language_scope_review/shipping_pages'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

checks = json.loads((DATA / 'document_checks.json').read_text(encoding='utf-8'))
assert checks['pages'] == 20
assert checks['status'] == 'programmatic_pass_visual_record_required'
for name, digest in checks['artifact_sha256'].items():
    assert sha(ROOT / name) == digest, name

# Pages in these folders were actually opened earlier in this same review.
# Pages 8–18 of the final render were opened after the last authoring change.
earlier = {1: 'pages', 2: 'pages', 3: 'pages', 4: 'final_release_pages',
           5: 'final_release_pages', 6: 'final_release_pages',
           7: 'final_release_pages', 19: 'pages', 20: 'pages'}
observed = set(range(8, 19))
entries = []
for page in range(1, 21):
    name = f'page-{page:02d}.png'
    png = CURRENT / name
    digest = sha(png)
    if page in observed:
        basis = 'Final page image opened and visually inspected'
    else:
        previous = ROOT / 'tmp/language_scope_review' / earlier[page] / name
        assert sha(previous) == digest, page
        basis = f'Byte-identical to image actually inspected in {earlier[page]}'
    entries.append({'page': page, 'sha256': digest, 'basis': basis,
                    'layout_review': 'pass'})

visual = {
    'date': '2026-10-05', 'reviewer': 'Codex visual inspection',
    'method': 'Native WPS PDF rendered with bundled PDFium, scale 1.8',
    'pdf_sha256': checks['artifact_sha256']['deliverables/大创申报书_语言与范围修订审阅版.pdf'],
    'pages': entries,
    'observations': [
        'School cover, notes, application form and approval areas retained; fillable values blank.',
        'All four tables and their captions centered; complete tables kept on one page.',
        'All nine illustrations paired with captions; no observed clipping or overlapping annotations.',
        'R combining accent retained using Cambria Math; body font size not reduced.',
        'Pages 8 and 12 leave space to preserve the next complete figure or experimental table.',
        'Page 18 ends the budget section before the original approval pages.',
        'Three body pages have trailing whitespace over 25%; accepted with stated reasons, not claimed absent.'
    ],
    'physical_validation': False,
    'warning': 'Inspection applies only to these file and page hashes. Re-render and inspect after edits.'
}
save(DATA / 'visual_review.json', visual)
release = {
    'status': 'document_review_pass_with_documented_pagination_exceptions',
    'date': '2026-10-05', 'scope': 'Application prose, research scope and rendered layout',
    'pages': 20, 'illustrations': 9, 'editable_tables': 4,
    'blank_field_cells': 42, 'references': {'chinese': 5, 'english': 3},
    'input_preserved': checks['input_preserved'],
    'physical_validation': False,
    'pagination_exceptions': checks['body_pages_over_25_percent'],
    'checks': 'simulation/language_scope_review/document_checks.json',
    'visual_review': 'simulation/language_scope_review/visual_review.json',
    'artifact_sha256': checks['artifact_sha256'],
    'review_record_sha256': {
        'simulation/language_scope_review/document_checks.json': sha(DATA / 'document_checks.json'),
        'simulation/language_scope_review/visual_review.json': sha(DATA / 'visual_review.json')
    }
}
save(ROOT / 'deliverables/申报书语言与范围修订验收记录.json', release)
print('Recorded final 20-page visual inspection and artifact hashes; three pagination exceptions stated.')
