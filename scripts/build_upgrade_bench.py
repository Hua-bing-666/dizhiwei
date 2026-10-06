"""Add a perforated splash guard to the existing concept, preserving water paths."""
from pathlib import Path
import base64,json,zlib,hashlib
import build_bench_cad as cad
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/models/system_upgrade'
cad.OUT=OUT;cad.COLLECTION_REVIEW=True
old_assembly=cad.make_assembly
def assembly():
    old_assembly()
    # Approach each gland from the rear face, rather than letting the old
    # diagonal cable envelope cut through the new sheet below its openings.
    for name,index in [('P0',0),('P1',1),('Q',2)]:
        cad.PARTS[:]=[p for p in cad.PARTS if p['name']!=name+'_cable_4']
        x=345+index*32
        cad.add(name+'_cable_4',cad.cylinder((185-index*5,120,66),(x,145,85),1.5),'cable','cables',routing_envelope_only=True)
        cad.add(name+'_cable_5',cad.cylinder((x,145,85),(x,135,85),1.5),'cable','cables',routing_envelope_only=True)
    guard=cad.box((425,121,94),(250,2,132))
    for x in (345,377,409):guard=cad.cut(guard,cad.box((x,121,85),(20,6,22)))
    for x in (300,550):
        tab=cad.box((x,110,28),(12,26,4))
        tab=cad.cut(tab,cad.cylinder((x,107,24),(x,107,32),2.75))
        guard=cad.fuse(guard,tab)
    # Through holes in the removable deck match this guard's mounting tabs.
    plate=next(p for p in cad.PARTS if p['name']=='removable_deck')
    for x in (300,550):plate['shape']=cad.cut(plate['shape'],cad.cylinder((x,107,19),(x,107,31),2.75))
    plate['evidence']=cad.collect_evidence(plate['shape'])
    checks=[]
    for p in cad.PARTS:
        common=BRepAlgoAPI_Common(guard,p['shape']);common.Build()
        assert common.IsDone(),p['name']
        properties=GProp_GProps();BRepGProp.VolumeProperties_s(common.Shape(),properties)
        overlap=properties.Mass();assert abs(overlap)<1e-5,(p['name'],overlap)
        checks.append(dict(part=p['name'],overlap_volume_mm3=overlap))
    cad.add('perforated_splash_guard',guard,'silver','electronics',concept_only=True,not_ingress_protection=True)
    for x in (300,550):cad.bolt('guard_M5_'+str(x),x,107,30)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'guard_checks.json').write_text(json.dumps(dict(classification='CAD_guard_only_interference_check',physical_data=False,
             checks=checks,guard_to_lid_gap_mm=3,guard_to_return_pipe_gap_mm=8,gland_holes_mm=[20,22],
             limits='Checks do not certify global clearances, assembly tolerances, cable bend radius or ingress protection.'),indent=2),encoding='utf-8',newline='\n')
cad.make_assembly=assembly
cad.main()
p=OUT/'bench_layout.json';data=json.loads(p.read_text(encoding='utf-8'));data['variant']='system_upgrade';data['collection_design']['target_sample_seconds']=20
data['upgrade']=dict(splash_guard='250 x 132 x 2 mm; three gland clearance openings; two through-hole mounting tabs',
                     water_paths_unchanged=True,continuous_discharge_solution_verified=False,guard_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
scene_path=OUT/'bench_scene.json';scene=json.loads(scene_path.read_text(encoding='utf-8'));scene['variant']='system_upgrade';scene['anchors']['guard']=[425,120,145]
scene_path.write_text(json.dumps(scene,separators=(',',':')),encoding='utf-8',newline='\n')
template=(ROOT/'scripts/bench_viewer.template.html').read_text(encoding='utf-8')
template=template.replace('双支路滴灌试验台架 三维结构设计','双支路清水试验台架').replace('双支路清水台架 三维结构设计','双支路清水试验台架')
template=template.replace('DRIP RESEARCH / BENCH DESIGN','DRIP OPERATIONS / EXPERIMENTAL BENCH · V1.1')
template=template.replace('小容器仅表示计量位置，实际容积按流量与时长核定；','20 秒分次计量先要求实测有效容量≥440 mL；模型内腔几何容量约679 mL，不能替代有效容量标定。增设带过线开口的防溅板，不宣称防水等级，未解决长时排水；')
start=template.index('<h2>几何源文件</h2>');end=template.index('<div class="legend">',start)
template=template[:start]+'<h2>实验结构说明</h2><p>前侧电子盒与泄漏杯分区；防溅板避让三处电缆接头。新增两个安装孔，盒盖后缘与板间保留3 mm概念间隙。水路与受限、分流位置沿用已审查结构。</p>'+template[end:]
template=template.replace('<button id="cables">','<button data-view="electronics">电子盒与防溅板</button><button id="cables">')
template=template.replace("if(which==='pressure'){", "if(which==='electronics'){target.set(425,100,110);theta=-1.28;phi=.72;span=440}if(which==='pressure'){")
template=template.replace("'leak','node'];", "'leak','node','guard'];")
template=template.replace("'泄漏计量','采集/LoRa'];", "'泄漏计量','采集/LoRa','防溅板'];")
template=template.replace('[48,16],[0,35]];', '[48,16],[0,35],[0,-40]];')
template=template.replace('<li>前侧采集与LoRa节点</li>', '<li>前侧采集与LoRa节点</li><li>带过线开口的防溅板</li>')
template=template.replace('P0侧向取压','P0取压支口').replace('P1侧向取压','P1取压支口')
library=(ROOT/'application/models/vendor/three.cjs').read_text(encoding='utf-8');license=(ROOT/'application/models/vendor/three.LICENSE').read_text(encoding='utf-8')
html=template.replace('__THREE_SOURCE__',('/*\n'+license+'\n*/\n'+library).replace('</script','<\\/script')).replace('__SCENE_DEFLATE__',base64.b64encode(zlib.compress(scene_path.read_bytes(),9)).decode())
(ROOT/'deliverables/清水试验台架_V1.1.html').write_text(html,encoding='utf-8',newline='\n')
print('System upgrade concept model and viewer built; original variants untouched.')
