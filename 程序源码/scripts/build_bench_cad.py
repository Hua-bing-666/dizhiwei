"""Reviewable OCCT concept assembly, in mm; no vendor-exact or manufacturing claim.

Run with tmp/cad_runtime/Scripts/python.exe after installing cadquery-ocp-novtk
7.9.3.1.1 there. The project keeps parameter and geometry evidence, not runtime.
"""
from pathlib import Path
import json, math, sys, hashlib, struct
import numpy as np
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeTorus, BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool, BRep_Builder
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepCheck import BRepCheck_Analyzer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/models'
COLLECTION_REVIEW = '--collection-review' in sys.argv
if COLLECTION_REVIEW:
    OUT = OUT / 'collection_review'
SKILL = Path.home() / '.codex/skills/solidworks-automation-skill'
sys.path.insert(0, str(SKILL / 'scripts'))
from headless_occt_service import build_shape, collect_evidence

PALETTE = {
    'frame': '#b8c2ca', 'panel': '#f5f6f4', 'rubber': '#34434b',
    'supply': '#38627c', 'normal': '#557d77', 'leak': '#bb8954',
    'silver': '#bfc7ca', 'brass': '#bf9b60', 'blue': '#38789a',
    'orange': '#bc7043', 'enclosure': '#e3e7e4', 'lid': '#f8f9f6',
    'vessel': '#becfce', 'cable': '#313b40',
}
PARTS = []
Z = 140


def vec(p): return gp_Pnt(*[float(x) for x in p])


def cylinder(a, b, radius):
    a, b = np.asarray(a, float), np.asarray(b, float)
    direction = b-a
    return BRepPrimAPI_MakeCylinder(gp_Ax2(vec(a), gp_Dir(*direction)), float(radius), float(np.linalg.norm(direction))).Shape()


def cut(shape, tool):
    operation = BRepAlgoAPI_Cut(shape, tool)
    operation.Build()
    assert operation.IsDone(), 'Boolean cut failed'
    return operation.Shape()


def fuse(a, b):
    operation = BRepAlgoAPI_Fuse(a, b)
    operation.Build()
    assert operation.IsDone(), 'Boolean union failed'
    return operation.Shape()


def tube(a, b, radius=10, bore=8):
    direction = (np.asarray(b, float)-np.asarray(a, float))
    direction /= np.linalg.norm(direction)
    return cut(cylinder(a, b, radius), cylinder(np.asarray(a)-direction*.02, np.asarray(b)+direction*.02, bore))


def box(center, size):
    # Use the skill's established box backend, with centred coordinates.
    x, y, z = center
    l, w, h = size
    return build_shape({'features': [{'id': 'box', 'type': 'box', 'parameters': {
        'x': x, 'y': y, 'z': z, 'length': l, 'width': w, 'height': h}}]})


def hexagon(center, radius, height):
    x, y, z = center
    polygon = BRepBuilderAPI_MakePolygon()
    for t in np.arange(6)*math.pi/3:
        polygon.Add(vec((x+radius*math.cos(t), y+radius*math.sin(t), z)))
    polygon.Close()
    return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(polygon.Wire()).Face(), gp_Vec(0, 0, height)).Shape()


def elbow(center, radial_start, normal, radius=20, outer=10, inner=8):
    axes = gp_Ax2(vec(center), gp_Dir(*normal), gp_Dir(*radial_start))
    solid = BRepPrimAPI_MakeTorus(axes, radius, outer, math.pi/2).Shape()
    hollow = BRepPrimAPI_MakeTorus(axes, radius, inner, math.pi/2).Shape()
    return cut(solid, hollow)


def add(name, shape, material, group='water', **meta):
    assert BRepCheck_Analyzer(shape).IsValid(), name
    evidence = collect_evidence(shape)
    assert evidence['volume'] > 0 and evidence['topology']['solids'] >= 1, name
    PARTS.append({'name': name, 'shape': shape, 'material': material,
                  'group': group, 'evidence': evidence, 'meta': meta})


def bolt(name, x, y, z, radius=2.5):
    add(name+'_shaft', cylinder((x,y,z-10),(x,y,z+1), radius), 'silver', 'frame')
    add(name+'_head', hexagon((x,y,z+1), radius*1.7, 3), 'silver', 'frame')


def union(name, center, axis=(1,0,0), mat='rubber'):
    p, axis = np.asarray(center, float), np.asarray(axis, float)
    add(name+'_body', tube(p-axis*14, p+axis*14, 14, 8), mat)
    for side in (-1, 1):
        add(name+f'_collar{side}', tube(p+axis*(side*14-2.5), p+axis*(side*14+2.5), 16, 8), 'blue' if mat != 'normal' else 'normal')


def tee(name, center, branch, material='rubber'):
    p, d = np.asarray(center, float), np.asarray(branch, float)
    main_axis = np.array([1.,0,0]) if abs(d[0]) < .5 else np.array([0.,1,0])
    outside = fuse(cylinder(p-main_axis*18, p+main_axis*18, 14), cylinder(p, p+d*18, 14))
    main_bore = cylinder(p-main_axis*18.1, p+main_axis*18.1, 8)
    branch_bore = cylinder(p-d*.05, p+d*18.1, 8)
    add(name, cut(cut(outside, main_bore), branch_bore), material)


def inline_valve(name, x, y, direction=(1,0,0), material='brass', handle='blue', half=28):
    p, d = np.array([x,y,Z], float), np.asarray(direction, float)
    add(name+'_body', tube(p-d*half, p+d*half, 17, 8), material)
    for side in (-1,1):
        add(name+f'_nut{side}', tube(p+d*(side*half-4), p+d*(side*half+4), 20, 8), 'silver')
    add(name+'_stem', cylinder((x,y,Z+12),(x,y,Z+35),5), 'silver')
    add(name+'_handle', box((x+17,y,Z+38),(66,11,6)),handle)
    add(name+'_pivot', cylinder((x,y,Z+35),(x,y,Z+44),5),'silver')


def straight(name, a, b, material='supply'):
    add(name,tube(a,b),material)


def segments(name, y, start, end, components, material):
    current = start
    for label, x, half in sorted(components, key=lambda item:item[1]):
        if x-half > current:
            straight(name+'_to_'+label,(current,y,Z),(x-half,y,Z),material)
        current = x+half
    if current < end: straight(name+'_end',(current,y,Z),(end,y,Z),material)


def support(name, x, y):
    foot = box((x,y,30),(44,34,8))
    for dx in (-15,15):
        foot = cut(foot,cylinder((x+dx,y,25),(x+dx,y,36),2.75))
        bolt(name+f'_M5_{dx}',x+dx,y,34)
    add(name+'_foot',foot,'silver','frame')
    add(name+'_post',box((x,y,82),(12,12,96)),'silver','frame')
    clamp = tube((x-8,y,Z),(x+8,y,Z),13.5,10.2)
    add(name+'_clamp',clamp,'rubber','frame')


def make_assembly():
    PARTS.clear()
    # Frame and removable deck; all dimensions are provisional design inputs.
    for name,c,size in [('rail_front',(450,10,10),(900,20,20)),('rail_rear',(450,510,10),(900,20,20)),
                        ('rail_left',(10,260,10),(20,480,20)),('rail_right',(890,260,10),(20,480,20)),
                        ('crossbeam',(450,260,10),(860,20,20))]:
        add(name,box(c,size),'frame','frame')
    plate = box((450,260,23),(880,500,6))
    for x in (30,870):
        for y in (30,490):
            plate = cut(plate,cylinder((x,y,19),(x,y,27),3.3))
            bolt(f'frame_M6_{x}_{y}',x,y,26,3)
            add(f'foot_{x}_{y}',cylinder((x,y,-14),(x,y,0),14),'rubber','frame')
    add('removable_deck',plate,'panel','frame')
    # Ports and tees replace continuous pipes: no pipe runs through a valve.
    straight('supply_in',(40,430,Z),(97,430,Z))
    union('supply_port',(48,430,Z))
    tee('common_supply_tee',(115,430,Z),(0,-1,0))
    main = [('Q',180,34),('P0',270,18),('R',360,28),('P1',455,18),('leak',620,18),('A',765,28)]
    segments('A',430,133,820,main,'supply')
    for name,x in [('P0',270),('P1',455)]:
        tee(name+'_tap',(x,430,Z),(0,0,1))
        add(name+'_adaptor',tube((x,430,158),(x,430,172),10,3),'brass')
        boss = cut(hexagon((x,430,172),14,12),cylinder((x,430,171),(x,430,185),3))
        add(name+'_hex',boss,'silver')
        add(name+'_sensor_envelope',cylinder((x,430,184),(x,430,218),12),'silver',envelope_only=True)
        add(name+'_connector',cylinder((x,430,218),(x,430,239),8),'rubber',envelope_only=True)
    inline_valve('restriction',360,430,handle='orange')
    add('Q_meter_envelope',tube((146,430,Z),(214,430,Z),19,8),'rubber',envelope_only=True)
    for x in (146,214):union('Q_union_'+str(x),(x,430,Z))
    add('Q_pulse_cap',box((180,430,164),(27,24,15)),'blue',envelope_only=True)
    tee('leak_tee',(620,430,Z),(0,-1,0),'brass')
    inline_valve('A_equivalent_load',765,430,handle='blue')
    # Common normal return. Both normal loads discharge here, not into the cup.
    add('A_return_elbow',elbow((820,410,Z),(0,1,0),(0,0,-1)), 'normal')
    straight('return_upper',(840,410,Z),(840,268,Z),'normal')
    tee('B_return_tee',(840,250,Z),(-1,0,0),'normal')
    straight('return_lower',(840,232,Z),(840,160,Z),'normal')
    add('return_lower_elbow',elbow((820,160,Z),(1,0,0),(0,0,-1)), 'normal')
    straight('return_out',(820,140,Z),(40,140,Z),'normal')
    union('return_port',(48,140,Z),mat='normal')
    # B healthy switching load connects to the common source and common return.
    straight('B_vertical',(115,412,Z),(115,270,Z))
    add('B_supply_elbow',elbow((135,270,Z),(-1,0,0),(0,0,1)), 'supply')
    segments('B',250,135,822,[('switch',350,28),('Bload',765,28)],'normal')
    inline_valve('B_switch',350,250,handle='blue')
    inline_valve('B_equivalent_load',765,250,handle='blue')
    # Measured leak ends above an open vessel, separated from normal return.
    straight('leak_before_valve',(620,412,Z),(620,393,Z),'leak')
    inline_valve('leak_control',620,365,direction=(0,1,0),handle='orange')
    straight('leak_after_valve',(620,337,Z),(620,325,Z),'leak')
    add('leak_down_elbow',elbow((620,325,120),(0,0,1),(1,0,0)),'leak')
    straight('leak_free_outlet',(620,305,120),(620,305,112),'leak')
    vessel_outer, vessel_inner = (63,60) if COLLECTION_REVIEW else (40,37)
    tray_outer, tray_inner = (146,140) if COLLECTION_REVIEW else (110,104)
    vessel = cut(cylinder((620,305,29),(620,305,92),vessel_outer),cylinder((620,305,32),(620,305,93),vessel_inner))
    add('open_measuring_vessel',vessel,'vessel','measurement',capacity_not_calibrated=True)
    tray = cut(box((620,305,31),(tray_outer,tray_outer,10)),box((620,305,34),(tray_inner,tray_inner,10)))
    add('removable_catch_tray',tray,'silver','measurement')
    collection_support_x = 575 if COLLECTION_REVIEW else 615
    for i,(x,y) in enumerate([(175,430),(285,430),(515,430),(650,430),(175,250),(450,250),(collection_support_x,250),(265,140),(570,140),(840,340)]):
        support('support_'+str(i),x,y)
    # Electronics enclosure with a separate lid, fastening and cable glands.
    shell = cut(box((425,65,66),(230,100,80)),box((425,65,72),(224,94,80)))
    add('electronics_shell',shell,'enclosure','electronics',envelope_only=True)
    add('electronics_lid',box((425,65,110),(234,104,8)),'lid','electronics',envelope_only=True)
    for x in (321,529):
        for y in (27,103):bolt(f'lid_M4_{x}_{y}',x,y,114,2)
    for i,x in enumerate((345,377,409)):
        add('gland_'+str(i),tube((x,111,85),(x,135,85),8,3),'rubber','electronics',envelope_only=True)
    add('antenna_mount',cylinder((515,65,114),(515,65,127),6),'brass','electronics')
    add('LoRa_antenna_envelope',cylinder((515,65,127),(515,65,242),4),'rubber','electronics',envelope_only=True)
    # Optional route envelopes, shown only on request in the model viewer.
    for name,x,z,index in [('P0',270,239,0),('P1',455,239,1),('Q',180,174,2)]:
        points=[(x,430,z),(x,476,z),(x,476,66),(185-index*5,476,66),
                (185-index*5,120,66),(345+index*32,120,85)]
        for j,(a,b) in enumerate(zip(points,points[1:])):
            add(name+'_cable_'+str(j),cylinder(a,b,1.5),'cable','cables',routing_envelope_only=True)


def tessellate(shape):
    mesher = BRepMesh_IncrementalMesh(shape,.25,False,.25,True)
    mesher.Perform()
    assert mesher.IsDone()
    vertices, faces = [], []
    explorer = TopExp_Explorer(shape,TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face,location)
        if tri is not None:
            offset=len(vertices)
            for i in range(1,tri.NbNodes()+1):
                p=tri.Node(i).Transformed(location.Transformation())
                vertices.append([round(p.X(),5),round(p.Y(),5),round(p.Z(),5)])
            for i in range(1,tri.NbTriangles()+1):
                a,b,c=tri.Triangle(i).Get()
                if face.Orientation()==TopAbs_REVERSED:b,c=c,b
                faces.append([offset+a-1,offset+b-1,offset+c-1])
        explorer.Next()
    return vertices,faces


def write_glb(meshes):
    blob=bytearray(); views=[]; accessors=[]; nodes=[]; gl_meshes=[]
    def buffer(data,target):
        while len(blob)%4:blob.append(0)
        offset=len(blob);blob.extend(data)
        views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data),'target':target})
        return len(views)-1
    materials=[{'name':name,'pbrMetallicRoughness':{'baseColorFactor':[int(hexv[i:i+2],16)/255 for i in (1,3,5)]+[1],
                'metallicFactor':.45 if name in ['silver','frame','brass'] else .04,'roughnessFactor':.5},'doubleSided':True} for name,hexv in PALETTE.items()]
    for m in meshes:
        v=np.asarray(m['vertices'],np.float32)*.001 # glTF uses metres, unlike OBJ/STEP.
        idx=np.asarray(m['faces'],np.uint32).reshape(-1)
        va=len(accessors); accessors.append({'bufferView':buffer(v.tobytes(),34962),'componentType':5126,'count':len(v),'type':'VEC3','min':v.min(0).tolist(),'max':v.max(0).tolist()})
        ia=len(accessors); accessors.append({'bufferView':buffer(idx.tobytes(),34963),'componentType':5125,'count':len(idx),'type':'SCALAR'})
        gl_meshes.append({'name':m['name'],'primitives':[{'attributes':{'POSITION':va},'indices':ia,'material':list(PALETTE).index(m['material'])}]})
        nodes.append({'name':m['name'],'mesh':len(gl_meshes)-1,'extras':{'group':m['group']}})
    while len(blob)%4:blob.append(0)
    root_index=len(nodes)
    nodes.append({'name':'mm_Zup_to_m_Yup','children':list(range(root_index)),
                  'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)]})
    doc={'asset':{'version':'2.0','generator':'Project OCCT concept assembly','extras':{'classification':'concept_not_manufacturing','coordinate_system':'Y-up'}},
         'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors,'meshes':gl_meshes,'nodes':nodes,
         'materials':materials,'scenes':[{'nodes':[root_index]}],'scene':0}
    js=json.dumps(doc,separators=(',',':')).encode()
    while len(js)%4:js+=b' '
    payload=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
    (OUT/'bench_layout.glb').write_bytes(payload)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    make_assembly()
    compound=TopoDS_Compound(); builder=BRep_Builder();builder.MakeCompound(compound)
    meshes=[];obj=['# Concept assembly; units mm; not a manufacturing release.','mtllib bench_layout.mtl']; offset=0
    for part in PARTS:
        builder.Add(compound,part['shape'])
        vs,fs=tessellate(part['shape'])
        meshes.append({k:part[k] for k in ['name','material','group']} | {'vertices':vs,'faces':fs})
        obj.extend(['o '+part['name'],'usemtl '+part['material']])
        obj.extend('v '+' '.join(f'{x:.5f}' for x in p) for p in vs)
        obj.extend('f '+' '.join(str(offset+i+1) for i in f) for f in fs)
        offset+=len(vs)
    (OUT/'bench_layout.obj').write_text('\n'.join(obj)+'\n',encoding='utf-8',newline='\n')
    (OUT/'bench_layout.mtl').write_text('\n'.join('newmtl '+k+'\nKd '+' '.join(str(int(v[i:i+2],16)/255) for i in (1,3,5))+'\nKs 0.15 0.15 0.15\nNs 30\n' for k,v in PALETTE.items()),encoding='utf-8',newline='\n')
    step=OUT/'bench_layout.step';writer=STEPControl_Writer()
    assert writer.Transfer(compound,STEPControl_AsIs)==IFSelect_RetDone
    assert writer.Write(str(step))==IFSelect_RetDone
    reader=STEPControl_Reader();assert reader.ReadFile(str(step))==IFSelect_RetDone
    reader.TransferRoots(); reopened=collect_evidence(reader.OneShape())
    assert reopened['valid'] and reopened['topology']['solids']>=len(PARTS)
    write_glb(meshes)
    params={'classification':'parametric_concept_assembly_not_manufacturing_model','units':'mm','base_envelope':[900,520],
            'pipe_centre_height':Z,'provisional_pipe_od_id':[20,16],'bend_centreline_radius':20,
            'vertices':offset,'faces':sum(len(m['faces']) for m in meshes),'components':[p['name'] for p in PARTS],
            'electrical_enclosure_position':'front_zone_separate_from_measured_leak','leak_collection':'open_vessel_with_20mm_air_gap',
            'hydraulic_geometry_calibrated':False,'vendor_geometry_verified':False,'manufacturing_release':False,
            'geometry_backend':'OCCT/OCP 7.9.3.1.1; skill box backend + project tube/tee/quarter-torus extensions',
            'step_reopen_evidence':reopened,'parts':[{'name':p['name'],'group':p['group'],'material':p['material'],'evidence':p['evidence'],'limitations':p['meta']} for p in PARTS],
            'modelled_fasteners':{'frame':'M6 envelopes; four 6.6mm deck holes at x30/870,y30/490',
                                 'supports':'M5 envelopes; paired 5.5mm foot holes 30mm apart; deck mating holes not released',
                                 'lid':'M4 envelopes at x321/529,y27/103; mating threads not released'},
            'important_limits':['Sensor, flow meter, fittings, glands and enclosure are dimensioned envelopes, not vendor-certified replicas.',
                'Valve bores do not model actual spool, throttling or valve coefficient.',
                'Pipe and fitting sockets may overlap by insertion; no global clearance, pressure, electrical ingress or manufacturing approval.',
                'STEP mm, OBJ mm; GLB metres with a glTF Y-up transform; geometry does not change hydraulic simulation parameters.']}
    params['variant']='collection_review' if COLLECTION_REVIEW else 'baseline'
    params['collection_design']={'inner_radius_mm':60 if COLLECTION_REVIEW else 37,'inner_height_mm':60,'free_discharge_gap_mm':20,'capacity_calibrated':False,'target_sample_seconds':30 if COLLECTION_REVIEW else None,'capacity_margin_factor':1.25 if COLLECTION_REVIEW else None,'continuous_discharge_solution_verified':False}
    (OUT/'bench_layout.json').write_text(json.dumps(params,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    scene={'palette':PALETTE,'meshes':meshes,'bounds':{'min':[0,0,-14],'max':[900,520,242]},
           'anchors':{'P0':[270,430,239],'R':[360,430,184],'P1':[455,430,239],'Q':[180,430,176],
                      'A':[765,430,182],'B':[350,250,182],'leak':[586,285,60],'node':[425,65,114]},
           'classification':'concept_design_not_physical_validation'}
    if COLLECTION_REVIEW:
        scene['anchors'].update({'Q':[180,430,171.5],'A':[765,430,184],'B':[350,250,184],
                                'leak':[620+63/math.sqrt(2),305-63/math.sqrt(2),70],
                                'leak_rim':[558.5,305,92]})
    (OUT/'bench_scene.json').write_text(json.dumps(scene,separators=(',',':')),encoding='utf-8',newline='\n')
    print(json.dumps({'parts':len(PARTS),'vertices':offset,'triangles':params['faces'],
                     'step_reopened_valid':reopened['valid'],'solids':reopened['topology']['solids']},ensure_ascii=False))


if __name__=='__main__':main()
