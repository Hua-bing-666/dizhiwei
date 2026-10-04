"""Parse nine prose sections, local figure anchors and native table records."""
from pathlib import Path
import re,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/reference_review';OUT.mkdir(parents=True,exist_ok=True)
text=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
parts=re.split(r'^## ',text,flags=re.M)[1:];sections=[];figures=[];tables=[];references=[]
for section_id,part in enumerate(parts):
    lines=part.splitlines();result=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if re.match(r'^\[\d+\]\s',line):
            if not references:result.append('[[BIBLIOGRAPHY]]')
            references.append(line);i+=1;continue
        match=re.fullmatch(r'!\[(.+)\]\((figures/[^)]+)\)',line)
        if match:
            marker=f'[[FIGURE{len(figures)+1}]]'
            source=ROOT/'application'/match[2]
            width=380 if source.name=='website_diagnosis_panel.png' else 410
            png=source.read_bytes();assert png.startswith(b'\x89PNG\r\n\x1a\n')
            pixels=struct.unpack('>II',png[16:24])
            figures.append({'marker':marker,'section':section_id,'path':'application/'+match[2],'caption':match[1],'width_pt':width,'height_pt':width*pixels[1]/pixels[0],'pixel_dimensions':pixels,'sha256':hashlib.sha256(png).hexdigest()})
            result.append(marker);i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',x) for x in row):rows.append(row)
                i+=1
            marker=f'[[TABLE{len(tables)+1}]]'
            caption=result.pop() if result and re.match(r'^表\d+\s',result[-1]) else ''
            widths=([55,105,155,110] if len(rows[0])==4 else [85,140,200] if rows[0][0]=='层次' else [90,150,185] if rows[0][0]=='时段' else [110,55,260])
            assert len(widths)==len(rows[0]) and sum(widths)==425
            tables.append({'marker':marker,'section':section_id,'caption':caption,'rows':rows,'column_widths_pt':widths})
            result.append(marker);continue
        result.append(re.sub(r'^#{3,4}\s+','',line));i+=1
    # WPS can ignore KeepWithNext across a continued outer table row.
    # A soft break keeps each inner heading in the first body paragraph.
    joined=[];j=0
    while j<len(result):
        if re.match(r'^\d+\s',result[j]) and j+2<len(result) and re.match(r'^\d+\.\d+\s',result[j+1]) and not result[j+2].startswith('[['):
            joined.append(result[j]+'\x0b'+result[j+1]+'\x0b'+result[j+2]);j+=3
        elif re.match(r'^\d+(\.\d+)?\s',result[j]) and j+1<len(result) and not result[j+1].startswith('[[') and not re.match(r'^\d+(\.\d+)?\s',result[j+1]):
            joined.append(result[j]+'\x0b'+result[j+1]);j+=2
        else:joined.append(result[j]);j+=1
    sections.append('\r'.join(joined))
assert len(sections)==9 and len(figures)==9 and len(tables)==4
payload={'title':text.splitlines()[0][2:],'sections':sections,'figures':figures,'tables':tables,'references':references}
(OUT/'application_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print('Nine template sections; nine complementary figures; four native table records; abstract',len(parts[0].split('\n\n')[1]),'characters.')
