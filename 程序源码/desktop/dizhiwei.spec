# Build from the repository root with the dedicated desktop build environment.
from pathlib import Path
root = Path(SPECPATH).parent
datas = [
    (str(root/'deliverables/index.html'), 'deliverables'),
    (str(root/'deliverables/清水试验台架_V1.2.html'), 'deliverables'),
    (str(root/'application/config/workspace.json'), 'application/config'),
    (str(root/'simulation/quality_interval_review/frozen_parameters.json'), 'simulation/quality_interval_review'),
    (str(root/'simulation/diagnosis_review/protocol.json'), 'simulation/diagnosis_review'),
    (str(root/'desktop/app.ico'), 'desktop'),
    (str(root/'desktop/bin/bridge.json'), 'desktop/bin'),
    (str(root/'scripts/vendor/echarts/LICENSE'), 'licenses/ECharts'),
    (str(root/'scripts/vendor/echarts/NOTICE'), 'licenses/ECharts'),
    (str(root/'scripts/vendor/echarts/provenance.json'), 'licenses/ECharts'),
    (str(root/'desktop/licenses'), 'licenses'),
]
datas += [(str(root/'firmware'/name), 'firmware') for name in
          ('integer_diagnosis.c', 'integer_diagnosis.h', 'acquisition_bridge.c')]
a = Analysis([str(root/'desktop/app.py')],
    pathex=[str(root/'scripts'), str(root/'prototype'), str(root/'simulation'), str(root/'simulation/interface_review')],
    binaries=[(str(root/'desktop/bin/acquisition_bridge.exe'), 'desktop/bin')],
    datas=datas,
    hiddenimports=['review_quality_intervals', 'integer_profile'],
    hookspath=[], hooksconfig={'matplotlib':{'backends':['Agg']}}, runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter', 'scipy', 'IPython', 'pytest'],
    noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
    name='滴智卫', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon=str(root/'desktop/app.ico'), version=str(root/'desktop/version_info.txt'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='滴智卫_桌面版_V1.3')
single = EXE(pyz, a.scripts, a.binaries, a.datas, [],
    name='滴智卫_V1.3', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon=str(root/'desktop/app.ico'), version=str(root/'desktop/version_info.txt'))
