/* Inspect existing CAD meshes; no animation or geometrical displacement. */
(() => {
const $=id=>document.getElementById(id);let inspectGroup='all',selected='';
const groups={all:'完整装配',water:'水路与计量',electronics:'电子盒与防溅板',frame:'底架与支撑',measurement:'计量器具',cables:'线缆包络'};
function initialize(){
 if(!window.benchReady){if(window.benchError){$('part-detail').textContent='模型加载失败，请检查浏览器 WebGL 支持。';return;}setTimeout(initialize,80);return;}
 for(const mesh of meshes){mesh.userData.originalColor=mesh.material.color.clone();mesh.userData.originalOpacity=mesh.material.opacity;}
 $('group-select').innerHTML=Object.entries(groups).filter(([k])=>k==='all'||modelData.meshes.some(m=>m.group===k)).map(([k,v])=>`<option value="${k}">${v}</option>`).join('');
 function options(){const rr=modelData.meshes.filter(m=>inspectGroup==='all'||m.group===inspectGroup||(inspectGroup==='water'&&m.group==='measurement'));$('part-select').innerHTML='<option value="">选择部件查看包络</option>'+rr.map(m=>`<option value="${m.name}">${m.name}</option>`).join('');}
 function paint(){for(const mesh of meshes){const groupMatch=inspectGroup==='all'||mesh.userData.group===inspectGroup||(inspectGroup==='water'&&mesh.userData.group==='measurement'),partMatch=!selected||mesh.name===selected;mesh.visible=mesh.userData.group==='cables'?showCables||inspectGroup==='cables':true;if(mesh.name==='electronics_lid'&&lidOpen)mesh.visible=false;const muted=!groupMatch||!partMatch;mesh.material.transparent=muted;mesh.material.opacity=muted?.10:1;mesh.material.depthWrite=!muted;mesh.material.color.copy(muted?new THREE.Color('#b4c2bc'):mesh.userData.originalColor);mesh.material.needsUpdate=true;}update();}
 function detail(){const part=modelData.meshes.find(m=>m.name===selected);if(!part){$('part-detail').textContent='选择部件可查看模型坐标和三轴包络；尺寸来自网格，不代表厂家实测尺寸。';return;}const low=[0,1,2].map(i=>Math.min(...part.vertices.map(v=>v[i]))),high=[0,1,2].map(i=>Math.max(...part.vertices.map(v=>v[i])));$('part-detail').textContent=`${part.name}\nX × Y × Z 包络：${high.map((v,i)=>(v-low[i]).toFixed(1)).join(' × ')} mm\n最小坐标：${low.map(v=>v.toFixed(1)).join(', ')} mm\n最大坐标：${high.map(v=>v.toFixed(1)).join(', ')} mm\n模型包络用于布局检查；非厂家尺寸或制造公差。`;}
 function setGroup(value){inspectGroup=value in groups?value:'all';selected='';$('group-select').value=inspectGroup;options();paint();detail();}
 function setPart(value){selected=modelData.meshes.some(m=>m.name===value)?value:'';$('part-select').value=selected;paint();detail();}
 $('group-select').onchange=e=>setGroup(e.target.value);$('part-select').onchange=e=>setPart(e.target.value);
 $('inspection-reset').onclick=()=>{setGroup('all');view('iso');};
 const phases={reference:['pressure','all','健康标定','固定 A 负载，核对 P0、P1 与独立流量；在多个稳定压力档记录。'],restriction:['pressure','water','受限注入','受限元件位于 P0 与 P1 之间。一次只改变该元件，记录开度和注入时间。'],leak:['leak','water','泄漏注入','Q 测量分流前的 A 总流量。泄漏支路自由排入计量杯，分次计时收集；先标定有效容量。'],disturbance:['top','water','健康扰动','改变 B 支路健康负载，对照共源供压变化；不把 B 显示为第二个采集节点。'],electronics:['electronics','electronics','电气布置','检查干湿分区、防溅板过线开口与电子盒。线缆仅为包络，防护等级和弯曲半径尚未验证。']};
 function phase(key){const p=phases[key]||phases.reference;setGroup(p[1]);view(p[0]);$('phase-title').textContent=p[2];$('phase-detail').textContent=p[3];document.querySelectorAll('[data-phase]').forEach(b=>{b.classList.toggle('active',b.dataset.phase===key);b.setAttribute('aria-pressed',String(b.dataset.phase===key));});}
 document.querySelectorAll('[data-phase]').forEach(b=>b.onclick=()=>phase(b.dataset.phase));
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{setGroup('all');$('phase-title').textContent='结构浏览';$('phase-detail').textContent='视角只用于检查结构，不表示已完成实物实验。';document.querySelectorAll('[data-phase]').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-pressed','false');});}));
 const oldLid=$('lid').onclick,oldCables=$('cables').onclick;$('lid').onclick=()=>{oldLid();paint();};$('cables').onclick=()=>{oldCables();paint();};
 $('reset').onclick=()=>{setGroup('all');view('iso');};
 options();detail();window.benchInspection={setGroup,setPart,phase,getState:()=>({group:inspectGroup,part:selected})};window.benchToolsReady=true;
}
initialize();
})();
