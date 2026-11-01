"""Independent capacity calculation and local OCCT interference checks.

Use the existing CAD runtime. Results concern this concept's collection group,
not a global fit, a calibrated vessel, pressure rating or physical experiment.
"""
from pathlib import Path
import csv, hashlib, json, math
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID,TopAbs_ON
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform,BRepBuilderAPI_MakeVertex
from OCP.gp import gp_Trsf,gp_Vec,gp_Pnt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/models/collection_review'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(folder):
    meta=json.loads((folder/'bench_layout.json').read_text(encoding='utf-8'))
    reader=STEPControl_Reader();assert reader.ReadFile(str(folder/'bench_layout.step'))==IFSelect_RetDone
    reader.TransferRoots();exp=TopExp_Explorer(reader.OneShape(),TopAbs_SOLID);shapes=[]
    while exp.More():shapes.append(exp.Current());exp.Next()
    assert len(shapes)==len(meta['parts'])
    return meta,{p['name']:(p,s) for p,s in zip(meta['parts'],shapes)}
def common_volume(a,b):
    op=BRepAlgoAPI_Common(a,b);op.Build();assert op.IsDone()
    props=GProp_GProps();BRepGProp.VolumeProperties_s(op.Shape(),props)
    return abs(props.Mass())
def bbox_touches(a,b):
    return all(a['min'][i]<=b['max'][i]+1e-6 and b['min'][i]<=a['max'][i]+1e-6 for i in range(3))
def main():
    meta,parts=load(OUT);_,old=load(ROOT/'application/models')
    hardware=ROOT/'simulation/hardware_results/summary.json'
    gridfile=ROOT/'simulation/hardware_results/range_grid.csv'
    config=json.loads(hardware.read_text(encoding='utf-8'))
    with gridfile.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    c0=config['healthy_c'];cmax=config['leak_max_c']
    leakrows=[r for r in rows if math.isclose(float(r['c']),cmax)]
    worst=max(leakrows,key=lambda r:(float(r['c'])-c0)*math.sqrt(float(r['p1_kpa'])))
    max_leak=(float(worst['c'])-c0)*math.sqrt(float(worst['p1_kpa']))
    design=meta['collection_design'];seconds=design['target_sample_seconds'];margin=design['capacity_margin_factor']
    capacity=math.pi*design['inner_radius_mm']**2*design['inner_height_mm']/1000
    # Baseline inner bore is documented in the unchanged parameterized CAD source.
    baseline_capacity=math.pi*37**2*60/1000
    required=max_leak*1000*seconds/60*margin
    assert baseline_capacity<required<=capacity
    tested=[];culled=0;conflicts=[]
    group=['open_measuring_vessel','removable_catch_tray']
    for name in group:
        pa,sa=parts[name]
        for other,(pb,sb) in parts.items():
            if other in group:continue
            if not bbox_touches(pa['evidence']['bounds'],pb['evidence']['bounds']):culled+=1;continue
            volume=common_volume(sa,sb)
            tested.append({'collection_part':name,'other_part':other,'common_volume_mm3':volume})
            if volume>1e-5:conflicts.append(tested[-1])
    assert not conflicts,conflicts
    tray=parts['removable_catch_tray'][1];foot=parts['support_6_foot'][1]
    distance=BRepExtrema_DistShapeShape(tray,foot);distance.Perform();assert distance.IsDone()
    clearance=distance.Value();assert abs(clearance-15)<1e-4
    previous_overlap=common_volume(tray,old['support_6_foot'][1]);assert previous_overlap>1e-5
    gap=parts['leak_free_outlet'][0]['evidence']['bounds']['min'][2]-parts['open_measuring_vessel'][0]['evidence']['bounds']['max'][2]
    assert abs(gap-20)<1e-4
    scene=json.loads((OUT/'bench_scene.json').read_text(encoding='utf-8'))
    targets={'P0':'P0_connector','R':'restriction_pivot','P1':'P1_connector','Q':'Q_pulse_cap','A':'A_equivalent_load_pivot','B':'B_switch_pivot','leak':'open_measuring_vessel','leak_rim':'open_measuring_vessel','node':'electronics_lid'}
    anchors=[]
    for key,name in targets.items():
        point=scene['anchors'][key];vertex=BRepBuilderAPI_MakeVertex(gp_Pnt(*point)).Vertex()
        check=BRepExtrema_DistShapeShape(vertex,parts[name][1]);check.Perform();assert check.IsDone()
        assert check.Value()<1e-4,(key,name,check.Value())
        assert BRepClass3d_SolidClassifier(parts[name][1],gp_Pnt(*point),1e-5).State()==TopAbs_ON,(key,'Anchor not on target boundary')
        anchors.append({'label':key,'target_part':name,'point_mm':point,'distance_to_target_shape_mm':check.Value(),'on_target_boundary':True})
    # A proposed removal path: lift 8 mm above the tray lip, then slide forward.
    # Samples are not a continuous swept-volume proof or an ergonomic validation.
    path_positions=[(0,0,z) for z in (0,2,4,6,8)]+[(0,-y,8) for y in range(15,226,15)]
    removal=[];cup_meta,cup_shape=parts['open_measuring_vessel'];cup_bounds=cup_meta['evidence']['bounds']
    for offset in path_positions:
        tr=gp_Trsf();tr.SetTranslation(gp_Vec(*offset));moved=BRepBuilderAPI_Transform(cup_shape,tr,True).Shape()
        bb={key:[v+offset[i] for i,v in enumerate(cup_bounds[key])] for key in ('min','max')}
        for name,(p,s) in parts.items():
            if name=='open_measuring_vessel' or not bbox_touches(bb,p['evidence']['bounds']):continue
            volume=common_volume(moved,s);removal.append({'translation_mm':offset,'other_part':name,'common_volume_mm3':volume})
            assert volume<1e-5,('Sampled removal conflict',offset,name,volume)
    record={
      'classification':'uncalibrated_concept_capacity_and_local_CAD_checks',
      'source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in [OUT/'bench_layout.step',OUT/'bench_layout.json',gridfile,hardware,Path(__file__)]},
      'design_calculation':{'grid_rows':len(rows),'healthy_c':c0,'max_leak_c':cmax,'max_leak_l_min':max_leak,'worst_grid_row':worst,'sample_seconds':seconds,'capacity_margin_factor':margin,'baseline_inner_radius_mm':37,'baseline_inner_height_mm':60,'baseline_geometric_capacity_ml':baseline_capacity,'candidate_geometric_capacity_ml':capacity,'required_with_margin_ml':required,'candidate_model_capacity_pass':True,'max_seconds_with_margin':capacity/(max_leak*1000*margin)*60,'ten_minute_required_with_margin_l':max_leak*10*margin},
      'geometry_checks':{'scope':'collection vessel and tray versus all 197 other concept solids; AABB rejection and exact common volume for remaining pairs; excludes the mutual vessel/tray mounting contact','candidate_pairs':394,'aabb_rejected_pairs':culled,'exact_pairs':tested,'positive_volume_conflicts':conflicts,'support_foot_to_tray_min_distance_mm':clearance,'enlarged_tray_with_old_support_counterexample_volume_mm3':previous_overlap,'outlet_to_lip_vertical_gap_mm':gap,'cup_outer_diameter_mm':126,'tray_inner_width_mm':140,'cup_to_tray_inner_side_clearance_mm':7},
      'sampled_removal_path':{'positions':path_positions,'sampled_positions':len(path_positions),'exact_checks':removal,'positive_volume_conflicts':0,'lift_mm':8,'forward_slide_mm':225,'tray_lip_vertical_clearance_mm':1,'continuous_swept_volume_verified':False,'hands_handles_and_splash_verified':False},
      'annotation_anchor_checks':anchors,
      'acceptance':{'geometric_and_assumed_grid_calculation':'passed','physical_capacity_calibrated':False,'splash_and_air_gap_effects_verified':False,'continuous_collection_or_return_verified':False,'vendor_connector_fit_verified':False,'global_interference_or_manufacturing_release':False},
      'required_follow_up':['Calibrate effective capacity by mass/volume and determine safe filling limit with splash headroom.','Measure actual maximum leakage over the eventual pressure/valve range; resize if it exceeds this assumption.','Before any long run, implement a free discharge collection/return route that does not create downstream head; the short-sampling cup does not satisfy continuous operation.','Confirm purchased dimensions, hose routing, wet/electrical separation and actual assembly.']}
    (OUT/'collection_feasibility.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    with (OUT/'collection_intersections.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['collection_part','other_part','common_volume_mm3'],lineterminator='\n');writer.writeheader();writer.writerows(tested)
    print(json.dumps({'capacity_ml':capacity,'required_ml':required,'max_leak_l_min':max_leak,'exact_intersection_pairs':len(tested),'conflicts':len(conflicts),'support_gap_mm':clearance,'counterexample_overlap_mm3':previous_overlap,'physical_validation':False}))
if __name__=='__main__':main()
