from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_application_integration.py').read_text(encoding='utf-8')
s=s.replace("ROOT/'simulation/application_integration'","ROOT/'simulation/quality_review'").replace('tmp/application_integration/candidate','tmp/quality_application/candidate').replace('tmp/application_integration/final-render','tmp/quality_application/render').replace('tmp/reference_review/application_payload.json','tmp/quality_application/application_payload.json')
start=s.index("                chosen=next(c for c in selection")
end=s.index("            assert minimum>=9,",start)
s=s[:start]+'''                a=read(DATA/'figure_checks.json')
                minimum=next(c for c in a['figures'] if c['name']==Path(f['path']).stem)['minFontPt']*width/420
'''+s[end:]
s=s.replace('minimum>=9,','minimum>=9.5,').replace("ROOT/'scripts/prepare_application_payload.py'","ROOT/'scripts/prepare_quality_payload.py'").replace("ROOT/'scripts/fill_application_template.ps1'","ROOT/'scripts/fill_quality_application.ps1'").replace('font >=9pt','font >=9.5pt')
(ROOT/'scripts/verify_quality_application.py').write_text(s,encoding='utf-8',newline='\n')
