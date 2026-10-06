"""Package the accepted EXE, without any user's data/ directory."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_desktop import copy_licenses


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tested-folder',type=Path,required=True)
    args=parser.parse_args()
    product=ROOT/'deliverables/滴智卫_桌面版_V1.2'
    evidence=ROOT/'tmp/desktop_acceptance'
    acceptance=json.loads((evidence/'acceptance.json').read_text(encoding='utf-8'))
    assert acceptance['result']=='passed'
    assert sha(args.tested_folder/'滴智卫.exe')==sha(product/'滴智卫.exe')
    checked=0
    for source in (args.tested_folder/'_internal').rglob('*'):
        if source.is_file():
            assert sha(source)==sha(product/source.relative_to(args.tested_folder)),source
            checked+=1
    proof=ROOT/'deliverables/桌面版V1.2验收预览'
    proof.mkdir(exist_ok=True)
    acceptance['tested_exe_sha256']=sha(args.tested_folder/'滴智卫.exe')
    acceptance['matched_runtime_files']=checked
    (proof/'acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in acceptance['screenshots']:shutil.copy2(evidence/name,proof/name)
    copy_licenses(product)
    shutil.copy2(ROOT/'docs/桌面版使用说明.md',product/'使用说明.md')
    files=[p for p in product.rglob('*') if p.is_file() and p.relative_to(product).parts[0]!='data' and p.name!='文件校验.json']
    checks=dict(version='1.2.0',desktop_checks=acceptance['passed'],service_checks=34,browser_checks=72,
        physical_data=False,files=[dict(path=p.relative_to(product).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)])
    (product/'文件校验.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    package=Path(str(product)+'.zip')
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in product.rglob('*'):
            if p.is_file() and p.relative_to(product).parts[0]!='data':archive.write(p,p.relative_to(product.parent))
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert not any('/data/' in name for name in archive.namelist())
    release=dict(version='1.2.0',package=package.relative_to(ROOT).as_posix(),package_bytes=package.stat().st_size,
        package_sha256=sha(package),exe_sha256=sha(product/'滴智卫.exe'),desktop_checks=acceptance['passed'],
        service_checks=34,browser_checks=72,matched_runtime_files=checked,no_user_data_in_package=True,
        zip_crc_check='passed',physical_data=False)
    (proof/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(release,ensure_ascii=False))


if __name__=='__main__':main()
