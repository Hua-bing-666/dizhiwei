"""Record an explicitly reviewed revision; do not edit prose or assume page counts.

Pass both reviewed PDF hashes after viewing their rendered pages. Hash matching
prevents applying an old review to new files; it does not judge visual quality.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviewed-pdf-sha256', required=True)
    parser.add_argument('--reviewed-scope-sha256', required=True)
    args = parser.parse_args()
    pdf = ROOT / 'deliverables/大创申报书_模板审阅版.pdf'
    scope = ROOT / 'deliverables/项目书审阅版.pdf'
    if digest(pdf) != args.reviewed_pdf_sha256 or digest(scope) != args.reviewed_scope_sha256:
        parser.error('Reviewed hashes differ from current PDFs; review changed files first.')
    source = (ROOT / 'application/正式模板正文.md').read_text(encoding='utf-8')
    figures = re.findall(r'!\[[^\]]+\]\((figures/[^)]+)\)', source)
    tables = re.findall(r'^表\d+\s', source, flags=re.M)
    assert len(figures) == 9 and len(tables) == 4
    with zipfile.ZipFile(ROOT / 'deliverables/大创申报书_模板填写稿.docx') as docx:
        media = {hashlib.sha256(docx.read(n)).hexdigest() for n in docx.namelist()
                 if n.startswith('word/media/')}
        assert all(digest(ROOT / 'application' / f) in media for f in figures), 'Stale embedded image'
    model = json.loads((ROOT / 'application/models/bench_layout.json').read_text(encoding='utf-8'))
    geometry = (ROOT / 'application/models/bench_layout.obj').read_text(encoding='utf-8').splitlines()
    vertices = sum(line.startswith('v ') for line in geometry)
    faces = [line.split()[1:] for line in geometry if line.startswith('f ')]
    assert vertices == model['vertices'] and len(faces) == model['faces']
    assert all(1 <= int(i.split('/')[0]) <= vertices for face in faces for i in face)
    assert model['hydraulic_geometry_calibrated'] is False
    app_doc = pymupdf.open(pdf)
    scope_doc = pymupdf.open(scope)
    bibliography_pages = sorted({page.number + 1 for page in app_doc
                                 if re.search(r'\[\d+\]\s', page.get_text())})
    path = ROOT / 'deliverables/申报书验收记录.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    record['date'] = '2026-10-04'
    record['native_pdf_sha256'] = digest(pdf)
    record['scope_pdf_sha256'] = digest(scope)
    review = record['visual_review']
    review.pop('unchanged_previously_reviewed_raster_pages', None)
    review.update({
        'application_native_wps_pdf_pages': app_doc.page_count,
        'application_reviewed_pages': list(range(1, app_doc.page_count + 1)),
        'scope_pdf_pages': scope_doc.page_count,
        'scope_reviewed_pages': list(range(1, scope_doc.page_count + 1)),
        'figures': len(figures), 'editable_record_tables': len(tables),
        'formal_diagnosis_flowcharts': 1, 'monochrome_design_figures': 3,
        'color_design_figures': 3, 'statistical_figures': 2,
        'actual_local_demo_screenshot': 1,
        'acceptance_priority': ['logical_correctness', 'completeness_and_relevance',
                                'label_arrow_frame_alignment_and_legibility',
                                'complementary_presentation_forms', 'color'],
        'review_identity': 'Current PDF pages viewed; matching image hashes checked separately.',
        'all_nine_current_images_embedded_in_docx': True,
    })
    record['references']['bibliography_pdf_pages'] = bibliography_pages
    record['geometry_check'] = {
        'vertices': vertices, 'faces': len(faces), 'indices_valid': True,
        'units': model['units'], 'base_envelope': model['base_envelope'],
        'manufacturing_or_physical_validation': False,
    }
    geometry_record = ROOT / 'application/models/bench_geometry_checks.json'
    if geometry_record.exists():
        record['geometry_check'].update(json.loads(geometry_record.read_text(encoding='utf-8')))
        record['geometry_check']['source'] = geometry_record.relative_to(ROOT).as_posix()
        record['geometry_check']['model_is_vendor_exact'] = False
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps({'application_pages': app_doc.page_count, 'scope_pages': scope_doc.page_count,
                      'current_images_embedded': len(figures), 'bibliography_pages': bibliography_pages,
                      'obj_vertices': vertices, 'obj_faces': len(faces)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
