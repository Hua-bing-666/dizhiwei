"""Bundle actual OCCT tessellation and pinned three.js into an offline viewer."""
from pathlib import Path
import base64,json,zlib,hashlib
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'application/models/vendor/three.cjs'
scene=ROOT/'application/models/bench_scene.json'
template=(ROOT/'scripts/bench_viewer.template.html').read_text(encoding='utf-8')
license_text=(source.parent/'three.LICENSE').read_text(encoding='utf-8')
library='/*\n'+license_text+'\n*/\n'+source.read_text(encoding='utf-8')
html=template.replace('__THREE_SOURCE__',library.replace('</script','<\\/script')).replace('__SCENE_DEFLATE__',base64.b64encode(zlib.compress(scene.read_bytes(),9)).decode())
(ROOT/'deliverables/台架三维结构交互模型.html').write_text(html,encoding='utf-8',newline='\n')
provenance={'library':'three.js r180','url':'https://github.com/mrdoob/three.js/tree/r180','license':'MIT','source':'https://raw.githubusercontent.com/mrdoob/three.js/r180/build/three.cjs','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'local_scene':'application/models/bench_scene.json','physical_validation':False}
(source.parent/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Offline 3D viewer built:',len(html),'characters; scene geometry embedded.')
