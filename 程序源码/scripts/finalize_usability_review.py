"""Record an explicitly completed manual review and check the packaged byte manifest."""
from pathlib import Path
from zipfile import ZipFile
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--pages-and-screens-reviewed',action='store_true',required=True);ap.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
folder=R/'application/usability_revision'
accepted=json.loads((folder/'acceptance.json').read_text(encoding='utf-8'))
assert accepted['result']=='passed'
review={'date':'2026-10-07','kind':'manual visual review plus structural checks','documents':{},'desktop_screens_reviewed':['overview-light','monitor-light','events-light','devices-light','history-light','experiments-light','bench-model','settings-light','monitor-dark','model-focus-P1_sensor_envelope'],'findings_corrected':['pressure measurement points drawn as side taps','reference evaluation arrows terminate inside the correct block','leak collection separated from normal return','model callouts tied to projected CAD anchors','model legend avoids unsupported subscript glyphs','redundant subsection removed to prevent a stranded title','execution book redundant final-page version paragraph removed'],'retained_whitespace':'School cover, instructions, blank personnel/budget/signature areas; occasional figure-related page endings. No cropped or stretched images identified.','physical_data':False}
for kind,doc in accepted['documents'].items():
    assert sha(R/doc['output'])==doc['output_sha256']
    for page in doc['page_images']:assert sha(R/page['file'])==page['sha256']
    review['documents'][kind]={'output':doc['output'],'sha256':doc['output_sha256'],'pages_individually_reviewed':list(range(1,doc['pages']+1)),'page_images':doc['page_images'],'pdf_sha256':doc['pdf_sha256']}
    edit_path=folder/(kind+'_edit.json');edit=json.loads(edit_path.read_text(encoding='utf-8'));edit['visual_review']='passed';edit_path.write_text(json.dumps(edit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
release_path=R/'deliverables/桌面版V1.3验收预览/release.json'
release=json.loads(release_path.read_text(encoding='utf-8'))
assert sha(R/release['package'])==release['package_sha256']
assert sha(R/release['single_file'])==release['single_file_sha256']
with ZipFile(R/release['package']) as z:
    assert z.testzip() is None
    assert not any('/data/' in n for n in z.namelist())
    manifest_name=next(n for n in z.namelist() if n.endswith('/文件校验.json'))
    manifest=json.loads(z.read(manifest_name));prefix=manifest_name.rsplit('/',1)[0]+'/'
    for item in manifest['files']:
        content=z.read(prefix+item['path'])
        assert len(content)==item['bytes'] and hashlib.sha256(content).hexdigest()==item['sha256']
    assert manifest['ui_checks']==50 and manifest['browser_checks']==72
review['desktop_release_sha256']=sha(release_path)
review['zip_manifest_files_verified']=len(manifest['files'])
(folder/'visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manual review recorded; packaged manifest verified:',len(manifest['files']),'files.')
