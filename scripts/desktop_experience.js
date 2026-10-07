/* Uses the same C snapshots as every other page. No new classifier. */
const chartInstances=new Map();let playbackTimer=null;
Object.assign(state,{chartRange:180,playing:false,theme:'light'});
function disposeCharts(){for(const chart of chartInstances.values())chart.dispose();chartInstances.clear();}
function chartSummary(id){const chart=chartInstances.get(id);if(!chart)return null;const opt=chart.getOption();return {series:opt.series.map(s=>({name:s.name,data:s.data,connectNulls:s.connectNulls})),markers:opt.series[0]?.markLine?.data||[],range:state.chartRange};}
function drawCharts(){
 const dark=state.theme==='dark',ink=dark?'#b6c9df':'#52687b',border=dark?'#304257':'#e3eaf0';
 const all=samples(),ss=state.chartRange?all.slice(-(state.chartRange+1)):all;
 for(const el of document.querySelectorAll('.chart')){
  let instance=chartInstances.get(el.id);
  if(instance&&instance.getDom()!==el){instance.dispose();chartInstances.delete(el.id);instance=null;}
  if(!instance){instance=echarts.init(el,null,{renderer:'svg'});chartInstances.set(el.id,instance);}
  const flow=el.dataset.flow==='true',keys=flow?['q']:['p0','p1'];
  const colors=dark?{p0:'#52cda7',p1:'#76aaff',q:'#dfb469'}:{p0:'#188267',p1:'#376fc2',q:'#a56d25'};
  const labels={p0:'入口 P0',p1:'下游 P1',q:'流量 Q₁₀'};
  const begin=ss[0]?.t_s??0,end=ss.at(-1)?.t_s??1,session=state.server?.run?.session;
  const markers=events().filter(e=>e.code>=4&&e.snapshot.t_s>=begin&&e.snapshot.t_s<=end&&(!state.backend||e.session===session)).slice(-10);
  const series=keys.map((key,i)=>({name:labels[key],type:'line',showSymbol:false,symbolSize:5,connectNulls:false,
   lineStyle:{width:2,type:key==='p1'?'dashed':'solid'},itemStyle:{color:colors[key]},
   data:ss.map(r=>[r.t_s,(!Number.isFinite(r[key])||(!flow&&r.status===3))?null:r[key]]),
   ...(i===0&&!flow?{markLine:{silent:false,symbol:['none','none'],lineStyle:{color:dark?'#ddb775':'#a8792b',width:1,type:'dotted'},
    label:{formatter:'候选',fontSize:10,color:ink,position:'insideEndTop'},data:markers.map(e=>({name:e.label,xAxis:e.snapshot.t_s}))}}:{})
  }));
  instance.setOption({animation:false,textStyle:{fontFamily:'Segoe UI, Microsoft YaHei, sans-serif'},
   aria:{enabled:true,label:{description:`${flow?'流量':'压力'}合成回放曲线，单位 ${flow?'L/min':'kPa'}。缺测保持断线，候选标记来自本会话事件。`}},
   legend:{data:keys.map(k=>labels[k]),right:8,top:0,textStyle:{color:ink,fontSize:10},selectedMode:false},
   grid:{left:43,right:17,top:31,bottom:30},
   tooltip:{trigger:'axis',confine:true,backgroundColor:dark?'#1d2b40':'#ffffff',borderColor:border,textStyle:{color:dark?'#e3edf8':'#1b3043',fontSize:12},
    axisPointer:{type:'line',lineStyle:{color:dark?'#7fa4c4':'#849eaf',type:'dashed'}},
    formatter:params=>{const p=Array.isArray(params)?params:[];if(!p.length)return '';return `<b>回放 ${Math.round(p[0].value[0])} s</b><br>`+p.map(item=>`${esc(item.seriesName)}：${Number.isFinite(item.value[1])?Number(item.value[1]).toFixed(flow?3:2):'缺测'} ${flow?'L/min':'kPa'}`).join('<br>');}},
   xAxis:{type:'value',min:begin,max:Math.max(begin+1,end),splitNumber:4,axisLabel:{color:ink,fontSize:10,formatter:v=>Math.round(v)+' s',hideOverlap:true},axisLine:{lineStyle:{color:border}},axisTick:{show:false},splitLine:{show:false}},
   yAxis:{type:'value',name:flow?'L/min':'kPa',nameTextStyle:{color:ink,fontSize:10,align:'left'},min:0,splitNumber:3,
    max:v=>flow?Math.max(1,Math.ceil((Number.isFinite(v.max)?v.max:0)*1.2)):Math.max(40,Math.ceil((Number.isFinite(v.max)?v.max:0)*1.1/20)*20),
    axisLabel:{color:ink,fontSize:10},axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:border,type:'dashed'}}},
   dataZoom:[{type:'inside',filterMode:'none',zoomOnMouseWheel:'ctrl',moveOnMouseWheel:false,moveOnMouseMove:false}],series},true);
  instance.resize();
 }
}
function updatePlaybackControls(){const button=$('playback-toggle');if(!button)return;button.textContent=state.playing?'暂停回放':'播放 · 10×';button.setAttribute('aria-pressed',String(state.playing));button.disabled=state.busy||state.backend&&!state.server?.active;$('advance').disabled=state.busy||state.playing||state.backend&&!state.server?.active;}
function stopPlayback(){clearTimeout(playbackTimer);playbackTimer=null;state.playing=false;updatePlaybackControls();}
async function playbackTick(){
 if(!state.playing)return;
 if(document.hidden){stopPlayback();return;}
 if(state.busy){playbackTimer=setTimeout(playbackTick,100);return;}
 const before=current()?.t_s??-1;
 if(state.backend)await mutate('/api/replay/step',{n:5});
 else{state.cursor=Math.min(trace().samples.length-1,state.cursor+5);render();}
 if(!state.playing)return;
 if((current()?.t_s??-1)<=before||!state.backend&&state.cursor>=trace().samples.length-1){stopPlayback();return;}
 playbackTimer=setTimeout(playbackTick,500);
}
function togglePlayback(){if(state.playing){stopPlayback();return;}if(state.busy||state.backend&&!state.server?.active)return;state.playing=true;updatePlaybackControls();playbackTimer=setTimeout(playbackTick,500);}
function setTheme(theme,persist=true){if(!['light','dark'].includes(theme))return;state.theme=theme;document.documentElement.dataset.theme=theme;$('theme-toggle').textContent=theme==='dark'?'切换浅色':'切换深色';$('theme-toggle').setAttribute('aria-pressed',String(theme==='dark'));if($('appearance-theme'))$('appearance-theme').value=theme;drawCharts();updateBenchSnapshot();if(persist)savePreferences({theme});}
function savePreferences(values){try{const prev=JSON.parse(localStorage.getItem('drip-ui-preferences')||'{}');localStorage.setItem('drip-ui-preferences',JSON.stringify({...prev,...values}));}catch{}if(window.pywebview?.api?.save_preferences)window.pywebview.api.save_preferences(values).catch(()=>notify('外观偏好未能保存，可稍后重试。'));}
function applyPreferences(values){if(values&&[0,180,600].includes(values.chart_range))state.chartRange=values.chart_range;for(const button of document.querySelectorAll('[data-chart-range]'))button.setAttribute('aria-pressed',String(Number(button.dataset.chartRange)===state.chartRange));setTheme(values?.theme==='dark'?'dark':'light',false);}
function initializeExperience(){
 $('theme-toggle').onclick=()=>setTheme(state.theme==='dark'?'light':'dark');
 $('playback-toggle').onclick=togglePlayback;
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stopPlayback();});
 window.addEventListener('beforeunload',stopPlayback);
 window.addEventListener('message',e=>{const f=$('bench-frame');if(f&&e.source===f.contentWindow&&e.data?.type==='drip-bench-ready'){f.dataset.loaded='true';updateBenchSnapshot();if(f.dataset.pendingFocus)f.contentWindow.postMessage({type:'drip-bench-focus',part:f.dataset.pendingFocus},'*');}});
 try{applyPreferences(JSON.parse(localStorage.getItem('drip-ui-preferences')||'{}'));}catch{setTheme('light',false);}
 window.addEventListener('pywebviewready',async()=>{try{applyPreferences(await window.pywebview.api.read_preferences());}catch{}});
}
function updateBenchSnapshot(){
 if(!$('bench-snapshot'))return;const c=current(),good=c&&c.status!==3;
 $('bench-time').textContent=c?`${state.backend?'S'+state.server.run.session:'离线'} · ${c.t_s} s`:'暂无回放记录';
 for(const [id,value,unit] of [['bench-p0',good?c.p0:null,'kPa'],['bench-p1',good?c.p1:null,'kPa'],['bench-q',c?.q,'L/min']])$(id).textContent=`${fmt(value,id==='bench-q'?3:2)} ${unit}`;
 const frame=$('bench-frame');if(frame?.contentWindow)frame.contentWindow.postMessage({type:'drip-bench-state',snapshot:{t_s:c?.t_s??null,p0:good?c.p0:null,p1:good?c.p1:null,q:c?.q??null,session:state.backend?state.server?.run?.session:null,physical_data:false,theme:state.theme}},'*');
}
function loadBenchModel(){if(!$('model-slot')||$('bench-frame'))return;$('model-slot').innerHTML='<iframe id="bench-frame" class="embed" title="双支路清水台架结构检查" src="清水试验台架_V1.2.html?embedded=1"></iframe>';$('model-load').hidden=true;$('bench-frame').onload=()=>{const f=$('bench-frame');f.dataset.loaded='true';updateBenchSnapshot();if(f.dataset.pendingFocus)f.contentWindow.postMessage({type:'drip-bench-focus',part:f.dataset.pendingFocus},'*');};}
function wireExperience(){
 for(const button of document.querySelectorAll('[data-chart-range]'))button.onclick=()=>{state.chartRange=Number(button.dataset.chartRange);for(const other of document.querySelectorAll('[data-chart-range]'))other.setAttribute('aria-pressed',String(Number(other.dataset.chartRange)===state.chartRange));savePreferences({chart_range:state.chartRange});drawCharts();};
 if($('appearance-theme'))$('appearance-theme').onchange=e=>setTheme(e.target.value);
 for(const button of document.querySelectorAll('[data-bench-point]'))button.onclick=()=>{loadBenchModel();const f=$('bench-frame');f.dataset.pendingFocus=button.dataset.benchPoint;if(f.dataset.loaded)f.contentWindow.postMessage({type:'drip-bench-focus',part:button.dataset.benchPoint},'*');};
 if($('model-load'))$('model-load').onclick=loadBenchModel;
 updatePlaybackControls();updateBenchSnapshot();
}
