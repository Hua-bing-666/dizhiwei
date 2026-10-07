"""Build V1.2 inspection UI from the verified V1.1 concept geometry."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def publish():
    text=(ROOT/'deliverables/清水试验台架_V1.1.html').read_text(encoding='utf-8')
    css=(ROOT/'scripts/bench_workspace.css').read_text(encoding='utf-8')
    js=(ROOT/'scripts/bench_workspace.js').read_text(encoding='utf-8')
    text=text.replace('</style>',css+'\n</style>',1).replace('EXPERIMENTAL BENCH · V1.1','EXPERIMENTAL BENCH · V1.2')
    text=text.replace('index.html#overview','index.html#bench')
    marker='<div class="layout">'
    bar='<div class="inspection-bar"><span>STRUCTURE INSPECTION</span><label>检查范围<select id="group-select"><option>模型加载中</option></select></label><label>部件包络<select id="part-select"><option>选择部件</option></select></label><button id="inspection-reset">恢复完整装配</button></div>'
    text=text.replace(marker,bar+marker,1)
    panel='<div class="inspection-main"><div class="phase-panel"><h2>实验路径</h2><div class="phase-buttons"><button data-phase="reference">健康标定</button><button data-phase="restriction">受限注入</button><button data-phase="leak">泄漏注入</button><button data-phase="disturbance">健康扰动</button><button data-phase="electronics">电气布置</button></div><h2 id="phase-title">结构浏览</h2><p id="phase-detail">视角只用于检查结构，不表示已完成实物实验。</p></div><p class="part-detail" id="part-detail">模型加载中。</p></div>'
    text=text.replace('<aside>','<aside tabindex="0" aria-label="台架检查与说明">'+panel,1)
    a=text.index('<div class="geometry-note">')
    b=text.index('<div class="legend">',a)
    technical=text[a:b]
    text=text[:a]+text[b:]
    text=text.replace('</aside>','<details class="model-help"><summary>结构与计量说明</summary>'+technical+'</details></aside>',1)
    text=text.replace('<p id="state">模型加载中</p>','<p id="state" hidden>模型加载中</p>')
    text=text.replace('视角只用于检查结构，不表示已完成实物实验。','选择实验步骤，查看对应水路。')
    text=text.replace('</html>','<script>'+js+'</script></html>')
    (ROOT/'deliverables/清水试验台架_V1.2.html').write_text(text,encoding='utf-8',newline='\n')
    print('V1.2 inspection viewer published; 207-component CAD geometry unchanged.')
if __name__=='__main__':publish()
