"""Build a portable Windows folder. Run in desktop/requirements.txt environment."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'prototype'), str(ROOT/'simulation')]
from platform_service import compile_bridge


def copy_licenses(folder):
    for distribution in importlib.metadata.distributions():
        for resource in distribution.files or []:
            if not any('license' in part.lower() or part.lower().startswith('copying')
                       for part in resource.parts):
                continue
            source=Path(distribution.locate_file(resource))
            if not source.is_file() or source.suffix.lower() not in ('','.txt','.md','.rst'):
                continue
            destination=folder/'licenses'/distribution.metadata['Name']/resource.name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():
        (folder/'licenses/Python').mkdir(parents=True,exist_ok=True)
        shutil.copy2(python_license,folder/'licenses/Python/LICENSE.txt')
    for name in ('LICENSE','NOTICE','provenance.json'):
        destination=folder/'licenses/ECharts'/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'scripts/vendor/echarts'/name,destination)


def main():
    if sys.platform != 'win32':
        raise SystemExit('请在 Windows x64 上构建桌面版。')
    subprocess.run([sys.executable,str(ROOT/'scripts/build_portal.py'),'--operations-only'],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/'scripts/build_bench_workspace.py')],check=True,cwd=ROOT)
    exe,digest = compile_bridge()
    target = ROOT/'desktop/bin'
    target.mkdir(parents=True,exist_ok=True)
    shutil.copy2(exe,target/exe.name)
    (target/'bridge.json').write_text(json.dumps(dict(
        source_sha256=digest,binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        classification='compiled_C_host_replay_not_MCU',physical_data=False
    ),indent=2)+'\n',encoding='utf-8')
    # Simple scalable water mark using the platform's existing teal palette.
    image = Image.new('RGBA',(256,256),(0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8,8,248,248),radius=52,fill='#13584f')
    draw.polygon([(128,43),(75,123),(181,123)],fill='white')
    draw.ellipse((70,94,186,210),fill='white')
    draw.ellipse((113,132,147,166),fill='#13584f')
    draw.line((130,163,151,184),fill='#13584f',width=10)
    image.save(ROOT/'desktop/app.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    copy_licenses(ROOT/'desktop')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm',
        '--distpath',str(ROOT/'tmp/desktop_distribution'),'--workpath',str(ROOT/'tmp/desktop_build'),
        str(ROOT/'desktop/dizhiwei.spec')],check=True,cwd=ROOT)
    folder=ROOT/'deliverables/滴智卫_桌面版_V1.3'
    # Merge only program files; a user's data/ is never part of the build.
    shutil.copytree(ROOT/'tmp/desktop_distribution/滴智卫_桌面版_V1.3',folder,dirs_exist_ok=True)
    shutil.copy2(ROOT/'tmp/desktop_distribution/滴智卫_V1.3.exe',ROOT/'deliverables/滴智卫_V1.3.exe')
    shutil.copy2(ROOT/'docs/桌面版使用说明.md',folder/'使用说明.md')
    copy_licenses(folder)
    subprocess.run([sys.executable,'-m','pip','freeze'],check=True,stdout=(ROOT/'desktop/build-lock.txt').open('w',encoding='utf-8'))
    print(folder/'滴智卫.exe')


if __name__=='__main__':
    main()
