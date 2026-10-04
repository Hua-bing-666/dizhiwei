"""Check staged evidence, original-artifact preservation and actual links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
MODELS=ROOT/'application/models/collection_review'
FIGURES=ROOT/'application/figures/collection_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    audit=read(MODELS/'collection_feasibility.json');views=read(MODELS/'bench_views.json');proof=read(FIGURES/'plate_provenance.json');layout=read(MODELS/'plate_layout_checks.json');geometry=read(MODELS/'bench_geometry_checks.json')
    for path,digest in audit['source_sha256'].items():assert sha(ROOT/path)==digest,('Stale calculation',path)
    assert sha(MODELS/'bench_scene.json')==views['sceneSha256']==proof['scene_sha256']
    assert proof['source_render_sha256']==views['imageSha256']
    for name,digest in views['imageSha256'].items():assert sha(FIGURES/name)==digest
    for plate in layout['plates']:
        assert not plate['outside'] and not plate['overlaps'] and plate['minimumFontPx']>=23
        for extension,digest in plate['sha256'].items():assert sha(FIGURES/(plate['name']+'.'+extension))==digest
    assert len(layout['plates'])==len(proof['figures'])==4
    assert len(audit['annotation_anchor_checks'])==9 and all(c['on_target_boundary'] for c in audit['annotation_anchor_checks'])
    assert len(views['annotationVisibilityChecks'])==2
    assert all(c['targetVisibleWithinHalfPixel'] for v in views['annotationVisibilityChecks'] for c in v['checks'])
    viewer=ROOT/'deliverables/台架三维结构交互模型_收集优化候选版.html'
    assert views['interactiveChecks']['viewerSha256']==sha(viewer)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            f=dict(attrs)
            if tag=='a' and 'href' in f:
                url=urlsplit(f['href'])
                if not url.scheme and url.path:self.paths.append(unquote(url.path))
    parser=Links();parser.feed(viewer.read_text(encoding='utf-8'))
    assert '../application/models/collection_review/bench_layout.step' in parser.paths
    for path in parser.paths:assert (viewer.parent/path).resolve().is_file(),path
    originals=['deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf','deliverables/项目书审阅版.pdf','deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf','deliverables/index.html','application/models/bench_layout.step','application/models/bench_scene.json','application/figures/bench_model.png','deliverables/台架三维结构交互模型.html']
    unchanged=[]
    for path in originals:
        prior=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,capture_output=True,check=True).stdout
        assert (ROOT/path).read_bytes()==prior,('Unexpected scope change',path)
        unchanged.append({'path':path,'sha256':sha(ROOT/path)})
    plan=ROOT/'docs/三阶段分项执行与验收标准.md'
    items=re.findall(r'^### ([ABC]\d{2}) (.+)$',plan.read_text(encoding='utf-8'),re.M)
    assert len(items)==25 and len([i for i,t in items if i.startswith('A')])==13
    progress={'date':'2026-10-04','scope':'detailed plan and A05 concept-model evidence only','plan_sha256':sha(plan),'this_turn':'A05 concept checks and pictures complete; not integrated into application','next':'A06—A07 simulation and diagnosis evidence review','tasks':[{'id':i,'name':t,'status':'candidate_internal_checks_passed_physical_unverified' if i=='A05' else 'planned_or_existing_to_review','requirement':'docs/三阶段分项执行与验收标准.md'} for i,t in items]}
    (ROOT/'deliverables/分项验收进度.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    report={'date':'2026-10-04','status':'passed_with_stated_concept_scope','scope':progress['scope'],'geometry_checks':geometry,'annotations':{'boundary_checks':len(audit['annotation_anchor_checks']),'raycast_view_checks':sum(len(v['checks']) for v in views['annotationVisibilityChecks']),'raycast_tolerance_pixels':0.5},'figure_layout':layout,'manual_visual_review':{'reviewed_figures':[p['name'] for p in layout['plates']],'checks':['numbered targets versus actual parts and legend','projection occlusion and top-view rim selection','dimension start/end planes and units','cropping, text clearance, visible main components','model/calculation identity and consistent caption'],'repairs':['overview canvas expanded to retain last explanatory line','Q anchor moved onto pulse-cap boundary; cup anchor moved from cavity to wall','top view selects visible left cup rim rather than occluded rim','20mm dimension moved to explicitly non-scale vertical relation sketch; 92mm value moved clear of outline'],'not_an_independent_external_acceptance':True},'local_links_checked':parser.paths,'original_artifacts_unchanged':unchanged,'manufacturing_and_physical_validation':False,'continuous_discharge_verified':False,'application_integration_complete':False}
    (ROOT/'deliverables/三维分项验收记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    status=read(ROOT/'deliverables/交付检查.json');status['staged_collection_review']={'artifact':viewer.name,'scope':progress['scope'],'record':'三维分项验收记录.json','status':report['status'],'application_integration_complete':False,'physical_validation':False}
    (ROOT/'deliverables/交付检查.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(f'Plan: {len(items)} tasks; 4 plates; 9 boundary anchors; 16 raycast checks; {len(parser.paths)} local links; 10 original artifacts unchanged.')
if __name__=='__main__':main()
