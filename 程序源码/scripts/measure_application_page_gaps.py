"""Measure trailing body-page whitespace, excluding the school form's blank fields."""
from pathlib import Path
import json
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
result={'method':'PDFium text and image vertical bounds; A4 body margins 70.9pt; excludes cover, instructions, registration, signatures and approval; measures trailing whitespace, not total ink area','threshold':.25}
for key,name in [('before','大创申报书_表格与文献修订审阅版.pdf'),('after','大创申报书_紧凑排版审阅版.pdf')]:
    doc=pdfium.PdfDocument(str(ROOT/'deliverables'/name));rows=[]
    for index in range(3,len(doc)-2):
        page=doc[index];tp=page.get_textpage();boxes=[]
        for ci in range(tp.count_chars()):
            s=tp.get_text_range(ci,1)
            if not s.strip() or not s.isprintable():continue
            b=tp.get_charbox(ci)
            if b[1]>=71 and b[3]<=page.get_height()-69:boxes.append(b)
        boxes.extend(o.get_bounds() for o in page.get_objects() if o.type==pdfium.raw.FPDF_PAGEOBJ_IMAGE)
        gap=max(0,min(b[1] for b in boxes)-70.9)
        rows.append({'page':index+1,'bottom_gap_pt':round(gap,1),'bottom_gap_ratio':round(gap/(page.get_height()-141.8),3)})
        tp.close();page.close()
    doc.close()
    result[key]={'pages':len(rows),'pages_with_bottom_gap_over_25_percent':[r['page'] for r in rows if r['bottom_gap_ratio']>.25],'rows':rows}
out=ROOT/'simulation/compact_layout_review/page_gap_comparison.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Trailing whitespace >25% of available body height:',len(result['before']['pages_with_bottom_gap_over_25_percent']),'->',len(result['after']['pages_with_bottom_gap_over_25_percent']))
