"""Bundle actual OCCT tessellation and pinned three.js into an offline viewer."""
from pathlib import Path
import base64,json,zlib,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'application/models/vendor/three.cjs'
review='--collection-review' in sys.argv
scene=ROOT/('application/models/collection_review/bench_scene.json' if review else 'application/models/bench_scene.json')
template=(ROOT/'scripts/bench_viewer.template.html').read_text(encoding='utf-8')
if review:
    template=template.replace('双支路滴灌试验台架 三维结构设计','双支路清水台架 收集优化候选版')
    template=template.replace('双支路清水台架 三维结构设计','双支路清水台架 收集优化候选版')
    template=template.replace('<h1>双支路清水台架 收集优化候选版</h1>','<h1>双支路清水台架三维模型</h1>')
    template=template.replace('当前为参数化概念模型；','本版增大收集内腔并移动邻近支架；现阶段拟采用20秒分次取样，先要求实测安全液位有效容量≥440mL，长时排水另行落实。当前为参数化概念模型；')
    template=template.replace('../application/models/bench_layout.', '../application/models/collection_review/bench_layout.')
    template=template.replace('../docs/三维结构模型优化说明.md', '../docs/三维台架建模论证与本轮验收.md')
    template=template.replace('建模取舍与核验边界</a>', '建模论证与分项验收</a><a href="../application/figures/collection_review/collection_overview.png">轴测总览图</a><a href="../application/figures/collection_review/collection_installation.png">俯视安装图</a><a href="../application/figures/collection_review/collection_interfaces.png">取压接口图</a><a href="../application/figures/collection_review/collection_metering.png">计量与容量图</a>')
    template=template.replace('小容器仅表示计量位置，实际容积按流量与时长核定；','内腔几何容量约679mL不能当有效容量；当前20秒取样方案先要求实测安全液位有效容量≥440mL，几何模型和原图的30秒计算保留作历史比较。若流量上界改变须重新核算，长时排水另行落实；')
license_text=(source.parent/'three.LICENSE').read_text(encoding='utf-8')
library='/*\n'+license_text+'\n*/\n'+source.read_text(encoding='utf-8')
html=template.replace('__THREE_SOURCE__',library.replace('</script','<\\/script')).replace('__SCENE_DEFLATE__',base64.b64encode(zlib.compress(scene.read_bytes(),9)).decode())
target='台架三维结构交互模型_收集优化候选版.html' if review else '台架三维结构交互模型.html'
(ROOT/'deliverables'/target).write_text(html,encoding='utf-8',newline='\n')
provenance={'library':'three.js r180','url':'https://github.com/mrdoob/three.js/tree/r180','license':'MIT','source':'https://raw.githubusercontent.com/mrdoob/three.js/r180/build/three.cjs','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'local_scene':'application/models/bench_scene.json','physical_validation':False}
if not review:
    (source.parent/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Offline 3D viewer built:',len(html),'characters; scene geometry embedded.')
