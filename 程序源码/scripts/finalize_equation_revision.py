"""Freeze hashes of pages and figures actually inspected during this revision."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'simulation/equation_figure_review'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
save = lambda p,v: p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
checks = read(DATA/'document_checks.json')
assert checks['status'] == 'programmatic_pass_visual_review_required'
for name,digest in checks['artifact_sha256'].items():
    assert sha(ROOT/name) == digest, name
prior = {p['page']:p for p in read(ROOT/'simulation/language_scope_review/visual_review.json')['pages']}
opened = {5:'pages',6:'pages',7:'pages',8:'pages',9:'final_pages',10:'final_pages',
          12:'shipping_pages',16:'final_pages',17:'final_pages'}
pages = []
for number in range(1,21):
    name = f'page-{number:02d}.png'
    digest = sha(ROOT/'tmp/equation_figure_review/shipping_pages'/name)
    if number in opened:
        viewed = ROOT/'tmp/equation_figure_review'/opened[number]/name
        assert sha(viewed) == digest, number
        basis = 'Actually opened this turn; final PNG identical to inspected ' + opened[number]
    else:
        assert prior[number]['sha256'] == digest, number
        basis = 'Byte-identical to individually inspected previous release page'
    pages.append({'page':number,'sha256':digest,'basis':basis,'layout':'pass'})
figures = []
for figure in read(DATA/'figure_checks.json')['figures']:
    name = figure['name']
    digest = sha(ROOT/'application/figures/equation_revision'/(name+'.png'))
    assert digest == figure['png_sha256']
    figures.append({'name':name,'sha256':digest,'basis':'Final figure actually opened this turn',
                    'annotation_and_layout':'pass','data_modified':False})
visual = {'date':'2026-10-05','status':'actual_visual_review_pass_with_stated_whitespace',
          'pages':pages,'figures':figures,'physical_validation':False,
          'render':'WPS native PDF + bundled PDFium; packaged renderer lacks LibreOffice',
          'pagination_exceptions':checks['pages_with_over_25_percent_trailing_whitespace'],
          'validity':'Only these artifact and image hashes; repeat inspection after edits.'}
save(DATA/'visual_review.json', visual)
release = {'date':'2026-10-05','status':'document_review_pass_with_stated_pagination_exceptions',
           'pages':20,'native_math_objects':checks['native_math_objects'],
           'four_core_equations_editable':True,'figures':9,'revised_figures':8,
           'editable_tables':4,'references':{'chinese':5,'english':3},
           'information_fields_blank':True,'physical_validation':False,
           'pagination_exceptions':visual['pagination_exceptions'],
           'artifact_sha256':checks['artifact_sha256'],
           'evidence_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in
                  [DATA/'document_checks.json',DATA/'visual_review.json',DATA/'figure_checks.json']}}
save(ROOT/'deliverables/申报书公式与插图修订验收记录.json',release)
print('Recorded inspection of all final pages and eight final figure variants; no inherited hardware performance claim.')
