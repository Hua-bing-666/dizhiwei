// 用 Edge 无头 + CDP 捕获真实三维模型的干净渲染图（无界面外壳，保留编号标注）
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'simulation', 'project_review', 'figures');
const SCRATCH = path.join(ROOT, 'tmp', 'model_capture');
await mkdir(OUT, { recursive: true });
await mkdir(SCRATCH, { recursive: true });

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const VIEWER = path.join(ROOT, 'deliverables', '清水试验台架_V1.2.html');
const profile = path.join(SCRATCH, 'edge-' + crypto.randomUUID());
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const child = spawn(EDGE, [
  '--headless=new', '--no-first-run', '--no-default-browser-check',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--remote-debugging-port=0', '--user-data-dir=' + profile, 'about:blank',
], { windowsHide: true, stdio: 'ignore' });

let browser = null;
for (let i = 0; i < 120; i++) {
  try {
    const port = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0];
    browser = await (await fetch('http://127.0.0.1:' + port + '/json/version')).json();
    break;
  } catch { await delay(250); }
}
if (!browser) throw Error('Edge 调试会话未就绪');

const ws = new WebSocket(browser.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const { resolve, reject } = pending.get(m.id);
    pending.delete(m.id);
    m.error ? reject(Error(JSON.stringify(m.error))) : resolve(m.result);
  }
};
const call = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  const key = ++id;
  pending.set(key, { resolve, reject });
  ws.send(JSON.stringify({ id: key, method, params, ...(sessionId ? { sessionId } : {}) }));
});

try {
  const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
  const send = (m, p) => call(m, p, sessionId);
  const evaluate = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };

  await send('Page.enable');
  await send('Runtime.enable');

  const jobs = [
    { name: 'model_render', view: 'iso', w: 1600, h: 1000, labels: true },
    { name: 'model_render_clean', view: 'iso', w: 1600, h: 1000, labels: false },
    { name: 'model_top', view: 'top', w: 1400, h: 900, labels: true },
  ];
  const anchorsOut = {};

  for (const job of jobs) {
    await send('Emulation.setDeviceMetricsOverride',
      { width: job.w, height: job.h, deviceScaleFactor: 2, mobile: false });

    await send('Page.navigate', { url: pathToFileURL(VIEWER).href + '?view=' + job.view });
    let ready = false;
    for (let i = 0; i < 240; i++) {
      if (await evaluate('!!window.benchReady')) { ready = true; break; }
      const err = await evaluate('window.benchError||null');
      if (err) throw Error(err);
      await delay(250);
    }
    if (!ready) throw Error('场景未就绪: ' + job.name);

    // 隐藏界面外壳：从 #stage 向上逐层隐藏所有兄弟节点，只留 3D 舞台
    await evaluate(`(() => {
      const css = document.createElement('style');
      css.textContent = 'html,body{overflow:hidden!important;margin:0!important;' +
        'background:#fff!important;padding:0!important}' +
        '.layout{display:block!important;margin:0!important;padding:0!important;' +
        'gap:0!important;grid-template-columns:none!important}' +
        '#stage{width:100vw!important;height:100vh!important;min-height:0!important;' +
        'max-height:100vh!important;border:0!important;border-radius:0!important;' +
        'margin:0!important;padding:0!important;box-shadow:none!important}';
      document.head.appendChild(css);
      let el = document.getElementById('stage');
      while (el && el !== document.body) {
        const p = el.parentElement;
        if (!p) break;
        for (const s of Array.from(p.children)) {
          if (s !== el) s.style.display = 'none';
        }
        el = p;
      }
      const tag = document.querySelector('.stage-tag');
      if (tag) tag.style.display = 'none';
      bench.setLabels(${job.labels});
      bench.update();
      return bench.getState();
    })()`);

    await evaluate(`bench.view(${JSON.stringify(job.view)})`);
    await delay(400);

    anchorsOut[job.view] = await evaluate(
      'Object.fromEntries(Object.entries(bench.getData().anchors).map(([k,p])=>[k,bench.project(p)]))');

    const png = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    const buf = Buffer.from(png.data, 'base64');
    await writeFile(path.join(OUT, job.name + '.png'), buf);
    console.log(`  ${job.name}.png  ${job.w * 2}x${job.h * 2}  ${(buf.length / 1024).toFixed(0)} KB`);
  }

  await writeFile(path.join(OUT, 'model_anchors.json'),
    JSON.stringify(anchorsOut, null, 1));
  console.log('  锚点已保存 model_anchors.json');
  console.log('模型渲染完成（源：deliverables/清水试验台架_V1.2.html，真实 WebGL 场景）');
} finally {
  await call('Browser.close').catch(() => {});
  ws.close();
  child.kill();
  await delay(300);
  await rm(profile, { recursive: true, force: true }).catch(() => {});
}
