"""Assemble a self-contained software package; audit extraction and smoke run."""
from pathlib import Path
import hashlib,json,subprocess,sys,uuid,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'prototype'))
reads=set();original=Path.read_text
def tracked(path,*args,**kwargs):
    resolved=path.resolve()
    if resolved.is_relative_to(ROOT) and resolved.suffix=='.json':reads.add(resolved)
    return original(path,*args,**kwargs)
Path.read_text=tracked
from platform_service import Platform,SCENES
platform=Platform()
try:
    for scene in SCENES:platform.start(scene,.3);platform.step(1)
finally:platform.close();Path.read_text=original

paths=set(reads)
for folder in ('prototype','simulation'):paths.update((ROOT/folder).rglob('*.py'))
for name in ('integer_diagnosis.c','integer_diagnosis.h','acquisition_bridge.c'):paths.add(ROOT/'firmware'/name)
for name in ('run_platform.py','启动运行平台.ps1','build_system_upgrade.py','build_upgrade_bench.py','build_bench_cad.py','platform_upgrade.css','platform_upgrade.js','platform_upgrade.template.html','verify_platform_upgrade.py','verify_platform_browser.mjs','package_system_upgrade.py'):
    paths.add(ROOT/'scripts'/name)
paths.update((ROOT/'simulation/platform_upgrade').glob('*'))
paths.update((ROOT/'application/models/system_upgrade').glob('*'))
paths.update((ROOT/'application/models/vendor').glob('*'))
paths.add(ROOT/'scripts/bench_viewer.template.html')
paths.add(ROOT/'simulation/extend_platform_reference.py')
paths.add(ROOT/'requirements-platform.txt')
paths.add(ROOT/'deliverables/index.html')
paths.update((ROOT/'deliverables/软件升级验收预览').glob('*.png'))
paths.add(ROOT/'deliverables/清水试验台架_V1.1.html')
paths.add(ROOT/'docs/软件升级包使用说明.md')
paths.add(ROOT/'docs/软件算法与三维升级执行计划.md')
paths.add(ROOT/'docs/软件算法与三维升级验收记录.md')
paths.add(ROOT/'tmp/platform_runtime/acquisition_bridge.exe')
paths.add(ROOT/'tmp/platform_runtime/acquisition_bridge.sha256')
paths={p for p in paths if p.is_file() and p.name not in ('package_acceptance.json','release_acceptance.json')}
manifest=dict(version='20261007-platform-c-v1',classification='host_software_and_concept_CAD',physical_data=False,
              runtime='Python 3.10 + requirements-platform.txt; included Windows host C bridge, not MCU firmware',
              runtime_json_dependencies=sorted(p.relative_to(ROOT).as_posix() for p in reads),
              files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(paths)])
target=ROOT/'deliverables/滴智卫_算法与软件升级包.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(paths):z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('UPGRADE_README.txt','先读 docs/软件升级包使用说明.md。\n离线网页：deliverables/index.html\n主机模式：安装 requirements-platform.txt，运行 scripts/启动运行平台.ps1 或 python scripts/run_platform.py。\n模型：deliverables/清水试验台架_V1.1.html\n附带的 EXE 是 Windows 主机 C 诊断程序，不是 STM32 固件。\n无射频、实际串口、能耗或阀门控制验证。\n')
    z.writestr('upgrade_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
scratch=(ROOT/'tmp/package_verification'/uuid.uuid4().hex).resolve();scratch.mkdir(parents=True)
with zipfile.ZipFile(target) as z:
    for name in z.namelist():assert (scratch/name).resolve().is_relative_to(scratch),name
    z.extractall(scratch)
for entry in manifest['files']:assert hashlib.sha256((scratch/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
snippet="import sys;sys.path.insert(0,'prototype');from platform_service import Platform;p=Platform();p.start('leak',.3);p.step(32);assert p.state()['count']==32;p.close();print('extracted upgrade smoke passed')"
result=subprocess.run([sys.executable,'-c',snippet],cwd=scratch,capture_output=True,text=True)
if result.returncode:raise RuntimeError(result.stderr)
receipt=dict(zip_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=len(paths),bytes=target.stat().st_size,manifest_verified=True,extracted_runtime_smoke=True,physical_data=False,runtime_json_dependencies=manifest['runtime_json_dependencies'])
(ROOT/'simulation/platform_upgrade/package_acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(result.stdout.strip());print(json.dumps(receipt,ensure_ascii=False))
