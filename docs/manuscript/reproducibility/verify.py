from pathlib import Path
import json,hashlib,statistics,re,subprocess,sys
import pymupdf
W=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=json.loads((W/'evidence/sources.json').read_text())
for s in sources:assert sha(W/s['staged_path'])==s['sha256']
x=json.loads((W/'figure_source/plot_inputs.json').read_text())['results'];d=dict(x);d.pop('compute_costs');d.pop('scientific_results_sha256');assert hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()==x['scientific_results_sha256']
refs=json.loads((W/'bibliography/verified_metadata.json').read_text());assert all(r['verified'] for r in refs)
text=(W/'manuscript/manuscript.md').read_text();assert set(re.findall(r'\[(R\d+)\]',text))=={r['id'] for r in refs}
claims=json.loads((W/'evidence/claims.json').read_text());assert all(c['decision'] in ['verified','qualified'] and c['supporting_evidence'] for c in claims)
for c in claims:assert sha(W/c['document'])==c['document_sha256']
for n in range(1,7):
 for ext in ['pdf','svg','png']:assert (W/f'figures/figure{n}.{ext}').stat().st_size>1000
pages=[]
for name,base in [('manuscript.pdf','manuscript'),('supplement/technical_appendix.pdf','supplement')]:
 doc=pymupdf.open(W/name)
 for i,page in enumerate(doc):
  outside=[b for b in page.get_text('blocks') if b[0]<0 or b[1]<0 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1];assert not outside,(name,i)
  assert not page.get_images(),(name,'unexpected raster embedding')
  imagepath=W/f'evidence/page_inspection/{base}_{i+1:02d}.png'
  pages.append(dict(document=name,page=i+1,pdf_sha256=sha(W/name),image=str(imagepath.relative_to(W)),image_sha256=sha(imagepath) if imagepath.exists() else None,render_dpi=118.8,text_within_page=True,vector_content=True))
for name in ['manuscript/manuscript.md','supplement/technical_appendix.md','manuscript.pdf','supplement/technical_appendix.pdf','supplement/model_identity_sanitized.json']:
 p=W/name;t=p.read_text() if p.suffix!='.pdf' else '\n'.join(q.get_text() for q in pymupdf.open(p));assert '/home/' not in t and 'git:/home/' not in t
pub=json.loads((W/'supplement/model_identity_sanitized.json').read_text());assert len(pub)==18;assert sum(r['saved_cuda']=='FAIL' for r in pub)==10
report=dict(public_sources=len(sources),academic_references=len(refs),claims=len(claims),model_routes=len(pub),failed_saved_cuda_routes=10,pages=pages,unresolved_internal_checks=0,qualification_scope='Internal agent scientific/editorial qualification; no external peer review or new model execution')
(W/'evidence/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pages'},indent=2))
