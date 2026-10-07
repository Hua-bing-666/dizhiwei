function labels(){
 if(!showLabels||capture){overlay.innerHTML='';return;}
 const [w,h]=dimensions();overlay.setAttribute('viewBox',`0 0 ${w} ${h}`);
 const placed=[],tag=document.querySelector('.stage-tag'),stageBox=stage.getBoundingClientRect();
 if(tag&&tag.checkVisibility()){const b=tag.getBoundingClientRect();placed.push({x:b.x-stageBox.x-7,y:b.y-stageBox.y-7,w:b.width+14,h:b.height+14});}
 const intersects=(a,b)=>a.x<b.x+b.w+6&&a.x+a.w+6>b.x&&a.y<b.y+b.h+6&&a.y+a.h+6>b.y;
 function position(px,py,bw,bh,ax,ay){
  const candidates=[];
  for(const dy of [0,-34,34,-68,68,-102,102,-136,136])for(const dx of [0,-40,40,-80,80,-120,120]){
   const x=Math.max(14,Math.min(w-bw-14,px+dx)),y=Math.max(14,Math.min(h-bh-14,py+dy));
   candidates.push({x,y,w:bw,h:bh,score:(x-px)**2+(y-py)**2});
  }
  candidates.sort((a,b)=>a.score-b.score);return candidates.find(a=>!(ax>=a.x-4&&ax<=a.x+a.w+4&&ay>=a.y-4&&ay<=a.y+a.h+4)&&!placed.some(b=>intersects(a,b)));
 }
 let content='';
 for(let i=0;i<anchors.length;i++){
  const key=anchors[i]==='leak'&&['top','leak'].includes(current)&&modelData.anchors.leak_rim?'leak_rim':anchors[i];
  const [x,y,z]=project(modelData.anchors[key]);
  if(z< -1||z>1||x<14||y<14||x>w-14||y>h-14)continue;
  const compact=w<650,[dx,dy]=offsets[i],label=compact?String(i+1):`${i+1} ${names[i]}`;
  const bw=compact?26:Math.ceil([...label].reduce((n,c)=>n+(/[\x00-\x7f]/.test(c)?7.6:14),0)+20),bh=28;
  const b=position(compact?x-13:x+dx-16,compact?y-45:y+dy-14,bw,bh,x,y);if(!b)continue;placed.push(b);
  // Attach the leader to the closest exterior edge. It never runs under text.
  const tx=Math.max(b.x,Math.min(b.x+bw,x)),ty=Math.max(b.y,Math.min(b.y+bh,y));
  const edgeY=y<b.y?b.y:y>b.y+bh?b.y+bh:ty;
  const edgeX=x<b.x?b.x:x>b.x+bw?b.x+bw:tx;
  content+=`<g data-annotation="${key}"><path d="M${x},${y} L${edgeX},${edgeY}" fill="none" stroke="#647782" stroke-width="1.15"/><circle cx="${x}" cy="${y}" r="2.5" fill="#526b73"/><rect x="${b.x}" y="${b.y}" width="${bw}" height="${bh}" rx="5" fill="white" fill-opacity=".97" stroke="#e3e9ec" stroke-width=".7"/><text x="${b.x+bw/2}" y="${b.y+19}" text-anchor="middle" fill="#263c46" font-size="14" font-family="Microsoft YaHei">${label}</text></g>`;
 }
 overlay.innerHTML=content;
}
