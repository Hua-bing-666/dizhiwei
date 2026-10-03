"""Check actual CAD round-trip, open conceptual passages and GLB unit transform.

This is not a global interference, pressure, assembly or hardware validation.
"""
from pathlib import Path
import sys,json,struct,math
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID,TopAbs_IN
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.gp import gp_Pnt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/models'
params=json.loads((OUT/'bench_layout.json').read_text(encoding='utf-8'))
reader=STEPControl_Reader()
assert reader.ReadFile(str(OUT/'bench_layout.step'))==IFSelect_RetDone
reader.TransferRoots();shape=reader.OneShape()
assert BRepCheck_Analyzer(shape).IsValid()
parts=[];explorer=TopExp_Explorer(shape,TopAbs_SOLID)
while explorer.More():
    parts.append(explorer.Current());explorer.Next()
assert len(parts)==len(params['parts'])==199
assert all(BRepCheck_Analyzer(p).IsValid() for p in parts)
water=[p for p,m in zip(parts,params['parts']) if m['group']=='water']
# Sample main and B fluid centres, then the actual separate leak outlet.
# No conceptual pipe or fitting may contain solid material at these locations.
probes=[(x,430,140) for x in range(45,811,17)]
probes += [(x,250,140) for x in range(140,821,19)]
probes += [(685,y,140) for y in range(329,427,9)]
probes += [(685,305,z) for z in (113,115,118)]
blocked=[]
for probe in probes:
    for part in water:
        state=BRepClass3d_SolidClassifier(part,gp_Pnt(*probe),1e-5).State()
        if state==TopAbs_IN:blocked.append(probe);break
assert not blocked,('Solid geometry blocks conceptual fluid centre',blocked)
named=dict(zip([m['name'] for m in params['parts']],params['parts']))
gap=named['leak_free_outlet']['evidence']['bounds']['min'][2]-named['open_measuring_vessel']['evidence']['bounds']['max'][2]
assert abs(gap-20)<1e-4
blob=(OUT/'bench_layout.glb').read_bytes()
magic,version,length=struct.unpack_from('<III',blob)
assert magic==0x46546c67 and version==2 and length==len(blob)
json_length,kind=struct.unpack_from('<II',blob,12)
assert kind==0x4e4f534a
gltf=json.loads(blob[20:20+json_length])
root=gltf['nodes'][gltf['scenes'][0]['nodes'][0]]
assert root['rotation']==[-math.sqrt(.5),0,0,math.sqrt(.5)]
assert len(root['children'])==len(parts)
assert max(a['max'][0] for a in gltf['accessors'] if a['type']=='VEC3')<=.901
result={'step_reopened_valid':True,'valid_solids':len(parts),'fluid_centre_probes':len(probes),
        'blocked_fluid_probes':len(blocked),'free_discharge_gap_mm':round(gap,4),
        'glb_header_length_and_metre_Yup_transform':'passed','manufacturing_or_physical_validation':False,
        'limits':'Centre probes are sparse concept checks, not a whole-bore, clearance, pressure or assembly approval.'}
(OUT/'bench_geometry_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps(result))
