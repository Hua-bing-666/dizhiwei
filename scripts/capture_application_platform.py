"""Capture the functioning offline site, keeping the synthetic-data labels visible."""
from pathlib import Path
import re,subprocess
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
html=(OUT/'index.html').read_text(encoding='utf-8')
page=TMP/'application-platform.html'
page.write_text(html.replace('<head>','<head><base href="'+OUT.as_uri()+'/">',1).replace('</body>','<script>navigate("diagnosis");</script></body>'),encoding='utf-8')
screen=TMP/'application-platform.png'
subprocess.run([r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run','--user-data-dir='+str(TMP/'platform-profile'),'--window-size=1440,1100','--virtual-time-budget=1000','--screenshot='+str(screen),page.as_uri()],check=True,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
# Crop only the app navigation; preserve all state/data labels in the main section.
Image.open(screen).crop((252,0,1440,920)).save(ROOT/'application/figures/platform_replay.png')
print('Real offline website screenshot saved; no connected device implied.')
