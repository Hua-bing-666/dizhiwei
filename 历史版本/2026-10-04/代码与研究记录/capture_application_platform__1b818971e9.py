"""Capture the functioning offline site, keeping the synthetic-data labels visible."""
from pathlib import Path
import re,subprocess,uuid,time
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];TMP=ROOT/'tmp/visual_redesign';OUT=ROOT/'deliverables'
template=ROOT/'scripts/portal.template.html';s=template.read_text(encoding='utf-8')
a=s.index('<section id="diagnosis"');b=s.index('<section',a+1)
part=s[a:b]
if '<details class="design-details">' not in part:
    part=re.sub(r'(<img[^>]*dual_pressure_layout[^>]*>)',r'<details class="design-details"><summary>查看测点设计与模型假设</summary>\1</details>',part,count=1)
    s=s[:a]+part+s[b:]
    template.write_text(s,encoding='utf-8',newline='\n')
subprocess.run(['python',str(ROOT/'scripts/build_portal.py')],check=True)
html=(OUT/'研究与答辩资料.html').read_text(encoding='utf-8')
page=TMP/'application-platform.html'
capture='''<script>navigate("diagnosis");const panel=document.querySelector('#diagnosis .grid .panel:nth-child(2)');document.body.replaceChildren(panel);panel.style.cssText='width:520px;border-radius:0;padding:20px;background:white';const style=document.createElement('style');style.textContent='body{width:520px;background:white;font-size:17px;line-height:1.5}h3{font-size:21px}.chip,.fine,label,.workflow-status{font-size:15px}.note{font-size:16px;padding:10px 12px}p{margin:10px 0}.maintenance-details,.workflow-fields,.workflow .actions,.workflow-log{display:none}.workflow{margin-top:12px;padding-top:12px}.workflow h3{font-size:18px}.reading b{font-size:24px}.reading span,.reading small{font-size:15px}.panel>p:not([id]){display:none}';document.head.append(style);</script>'''
page.write_text(html.replace('<head>','<head><base href="'+OUT.as_uri()+'/">',1).replace('</body>',capture+'</body>'),encoding='utf-8')
screen=TMP/'application-platform.png'
screen.unlink(missing_ok=True)
subprocess.run([r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run','--user-data-dir='+str(TMP/('platform-'+uuid.uuid4().hex[:10])),'--force-device-scale-factor=2','--window-size=520,670','--virtual-time-budget=1000','--screenshot='+str(screen),page.as_uri()],check=True,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
deadline=time.monotonic()+20
while not screen.exists():
    if time.monotonic()>deadline:raise RuntimeError('Fresh platform capture missing')
    time.sleep(.2)
# Actual module and values from the functioning page, enlarged for Word.
Image.open(screen).save(ROOT/'application/figures/platform_replay.png')
print('Actual offline management panel captured in a readable publication view; no connected device implied.')
