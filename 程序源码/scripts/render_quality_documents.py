"""Native WPS PDF fallback; bundled renderer lacks LibreOffice in this workspace."""
from pathlib import Path
import argparse,pypdfium2 as pdfium,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('pdf');ap.add_argument('output');args=ap.parse_args()
p=ROOT/args.pdf;out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(str(p));records=[]
for i in range(len(doc)):
    page=doc[i];image=page.render(scale=1.8).to_pil();path=out/f'page-{i+1:02}.png';image.save(path)
    records.append({'page':i+1,'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});page.close()
doc.close();(out/'pages.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(f'Rendered {len(records)} pages for individual visual inspection.')
