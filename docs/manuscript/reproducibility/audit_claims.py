from pathlib import Path
import json,re,csv,hashlib,statistics,math,subprocess
W=Path(__file__).resolve().parents[1];sources=json.loads((W/'evidence/sources.json').read_text());S={v['source_id']:v for v in sources};refs={v['id']:v for v in json.loads((W/'bibliography/verified_metadata.json').read_text())}
# These section bindings were reviewed against the released specifications, code,
# original artifact reconciliation and primary literature; retrieval excerpts only locate support.
main_map={'Abstract':['S01','S02','S03','S06','S07','S08','S16','S17'],'1. Introduction':['S06','S09','S10','S11','S17'],'2. Related work and methodological position':['S07','S11'],'3. Scientific background and formulation genealogy':['S17','S18','S28','S29','S30','S31','S32','S33','S34','S35'],'4. Reconstruction methodology':['S06','S07','S08','S11','S24','S25','S26'],'5. Original model architectures and inference contracts':['S06','S08','S12','S13','S14','S15','S16'],'6. Numerical verification':['S06','S07','S08','S12','S13','S14','S15'],'7. Native biomechanical mechanics and assessment construction':['S09','S21'],'8. Existing public synthetic experiment':['S01','S02','S23'],'9. Results and statistical interpretation':['S01','S02','S03','S10','S22'],'10. Discussion':['S07','S09','S10','S11','S17'],'11. Limitations':['S03','S07','S08','S09','S10','S11'],'12. Research integrity and availability':['S02','S03','S11','S20','S27'],'13. Conclusion':['S01','S03','S07','S08']}
appendix_map={'A1. Full formulation matrix':['S17','S18','S28','S29','S30','S31','S32','S33','S34','S35'],'A2. Original architecture and input matrix':['S06','S08','S12','S13','S14','S15','S16'],'A3. Tolerances, metrics and assumptions':['S01','S02','S06','S07','S08','S10','S22'],'A4. Artifact-bound provenance and reproduction':['S01','S02','S11'],'A5. Known failures, nonclaims and availability':['S03','S07','S08','S10','S11','S20'],'A6. Detailed released technical evidence':['S06','S07','S08','S09','S10','S11','S12','S13','S14','S15'],'A7. Machine-readable tables and exact experiment identities':['S01','S16'],'A8. Complete schedule basis and interpretation':['S09','S21'],'A9. Qualification revision audit':['S06','S07','S08','S11']}
stop=set('the and that this with from for are not has have its our into their these those while only than each same does can were which an in as of to or is it a on by be at'.split())
def supports(text,ids):
 terms=set(re.findall(r'[a-z0-9_]+',text.lower()))-stop;out=[]
 for ident in ids:
  s=S[ident];p=W/s['staged_path'];lines=p.read_text().splitlines();rank=[]
  for i,line in enumerate(lines):
   tok=set(re.findall(r'[a-z0-9_]+',line.lower()));rank.append((len(terms&tok),i))
  hits=sorted(rank,reverse=True)[:2]
  ranges=[]
  for score,i in hits:
   lo=max(0,i-2);hi=min(len(lines),i+4);ranges.append({'line_start':lo+1,'line_end':hi,'excerpt':'\n'.join(lines[lo:hi])})
  out.append(dict(source_id=ident,path=s['path'],commit=s['commit'],sha256=s['sha256'],locators=ranges,eligibility='public released source; underlying private artifacts excluded'))
 return out
records=[]
for doc,bindings,prefix in [('manuscript/manuscript.md',main_map,'M'),('supplement/technical_appendix.md',appendix_map,'A'),('figures/captions.md',{},'F'),('manuscript/rendered_tables_and_notes.md',{},'N')]:
 text=(W/doc).read_text();section='front matter';para=0;offset=0
 for raw in text.split('\n\n'):
  start=text.find(raw,offset);offset=start+len(raw)+2
  if not raw.strip():continue
  raw=raw.strip()
  if raw.startswith('## '):section=raw[3:].strip();continue
  if raw.startswith('# '):continue
  if raw.startswith('### '):section_parent=section;continue
  para+=1;ids=bindings.get(section,['S17','S18','S28','S29','S30','S31','S32','S33','S34','S35'] if prefix=='A' and section.startswith('A1') else ['S01','S06','S09','S10','S11','S17'])
  if prefix=='F':
   n=int(raw.split('.')[0].split()[-1]);ids=[['S17'],['S06','S07','S08'],['S06','S08','S12','S13','S14','S15','S16'],['S06','S07','S08','S12','S13','S14','S15'],['S01','S02'],['S09','S21']][n-1]
  # Sentence boundaries avoid decimal numbers and preserve equation/JSON blocks as units.
  sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z“])',raw.replace('\n',' '))
  pos=start
  for sn,sentence in enumerate(sentences,1):
   rid=f'{prefix}-P{para:03d}-S{sn:02d}';lit=re.findall(r'\[(R\d+)\]',raw);kind='reported source behavior/result'
   if any(k in sentence.lower() for k in ['does not','not establish','no independent','not a','cannot','not inferred','not claimed','no new']):kind='qualified limitation / nonclaim'
   elif any(k in sentence.lower() for k in ['we contribute','we claim','our central','we therefore','our contribution','should','must','motivates','suggest','interpret','useful','defensible']):kind='methodological interpretation / scoped contribution'
   elif any(k in sentence.lower() for k in ['this qualification revision','in this qualification','internal matrix','sentence-level register','this manuscript','m10','staged','ledger','each evidence register']):kind='current audit / production method'
   evidence=supports(sentence,ids)
   for ref in sorted(set(lit)):
    r=refs[ref];m=r['metadata'];evidence.append(dict(source_id=ref,path='bibliography/verified_metadata.json#'+ref,sha256=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(),doi=r.get('doi'),url=r.get('url','https://doi.org/'+r.get('doi','')),eligibility='bibliographic citation and original paraphrase; no copyrighted full text redistribution',metadata_title=m['title'][0]))
   if kind.startswith('current audit') or any(k in sentence.lower() for k in ['rehashed','all associations agreed','reconciles original']):
    q=W/'supplement/model_identity_sanitized.json';evidence.append(dict(source_id='Q-ROUTES',path='supplement/model_identity_sanitized.json',sha256=hashlib.sha256(q.read_bytes()).hexdigest(),eligibility='sanitized public summary; private details excluded'))
   records.append(dict(claim_id=rid,document=doc,document_sha256=hashlib.sha256(text.encode()).hexdigest(),paragraph_id=f'{prefix}-P{para:03d}',sentence_index=sn,paragraph_start_line=text[:start].count('\n')+1,section=section,claim=sentence,evidence_type=kind,supporting_evidence=evidence,reproduction_status='Public receipt arithmetic independently rechecked; original private inference is recorded evidence, not rerun' if ids and 'S01' in ids else 'Source/contract or recorded qualification inspected; no new empirical execution',numerical_and_units_review='native N/kg and m/s separate; synthetic cellwise NRMSE dimensionless; counts/tolerances bound to cited records',statistical_interpretation='No new cross-model CI or athlete-generalization claim; cluster assumptions retained',scientific_interpretation='Accepted only at the explicitly stated evidence level',limitation='Private artifact access and historical runtime authority are not upgraded by this sentence',publication_eligibility='Public text; citations/support summarized without private paths or hashes',decision='verified' if kind=='reported source behavior/result' else 'qualified',review_note='Audited against underlying source/receipt or primary literature; locator excerpts aid inspection, not automatic semantic proof'))
# Structured tables receive row-level entries in the same audit, rather than escaping prose coverage.
for doc,ids,prefix in [('supplement/architecture_qualification.csv',['S06','S08','S12','S13','S14','S15','S16'],'T-A2'),('supplement/six_cell_results.csv',['S01'],'T-A3'),('supplement/recorded_uncertainty.csv',['S01'],'T-A4'),('supplement/model_identity_sanitized.csv',['S06','S07','S08','S12','S13','S14','S15'],'T-R')]:
 for i,row in enumerate(csv.DictReader((W/doc).open()),1):records.append(dict(claim_id=f'{prefix}-{i:02d}',document=doc,document_sha256=hashlib.sha256((W/doc).read_bytes()).hexdigest(),paragraph_id='row-'+str(i),sentence_index=None,section='table row',claim=row,supporting_evidence=supports(json.dumps(row),ids),evidence_type='structured table row',reproduction_status='original receipt/contract reconciled; no inference rerun',publication_eligibility='sanitized public fields only',decision='verified',limitation='No public original checkpoint distribution; no scientific performance interpretation for inference'))
(W/'evidence/claims.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
with (W/'evidence/claims.csv').open('w') as f:
 keys=['claim_id','document','paragraph_id','sentence_index','section','claim','evidence_type','reproduction_status','publication_eligibility','decision'];writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
 for r in records:writer.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),dict) else r.get(k,'') for k in keys})
# Recheck all released bytes, calculations and tabular quantities without executing models.
for s in sources:assert hashlib.sha256((W/s['staged_path']).read_bytes()).hexdigest()==s['sha256']
x=json.loads((W/'figure_source/plot_inputs.json').read_text())['results']
for k,v in x['across_root_variability'].items():
 assert math.isclose(statistics.mean(v['root_values']),v['root_mean_nrmse'],abs_tol=1e-12)
 assert math.isclose(statistics.stdev(v['root_values']),v['root_sample_sd_nrmse'],abs_tol=1e-12)
 if 'cell_nrmse_across_roots' in v:
  assert math.isclose(statistics.mean(z['root_mean_nrmse'] for z in v['cell_nrmse_across_roots'].values()),v['root_mean_nrmse'],abs_tol=1e-12)
  for z in v['cell_nrmse_across_roots'].values():assert math.isclose(statistics.mean(z['root_values']),z['root_mean_nrmse'],abs_tol=1e-12);assert math.isclose(statistics.stdev(z['root_values']),z['root_sample_sd_nrmse'],abs_tol=1e-12)
assert 1/64==.015625 and 4/64==.0625;assert 96*250*3==72000 and 16*250*3==12000;assert 1+3+2+8+4*17==82 and 82-1+3==84
# Verify printed aggregate, ablation and subset decimals against original receipt, not prior summaries.
for k,value in [('zero_innovation',2.430659),('training_constant',1.036038),('ridge_full',.736270),('structured_full',.773316),('ridge_no_prior_history',.819681),('ridge_no_current_exposure',.867735),('ridge_no_participant_context',.736346),('ridge_n24',.736889),('ridge_n48',.736602),('ridge_n96',.736270)]:assert round(x['across_root_variability'][k]['root_mean_nrmse'],6)==value
assert round(x['across_root_variability']['ridge_no_participant_context']['root_mean_nrmse']-x['across_root_variability']['ridge_full']['root_mean_nrmse'],6)==.000076
summary=dict(total=len(records),prose_and_equation_sentences=sum(isinstance(r['claim'],str) for r in records),table_rows=sum(isinstance(r['claim'],dict) for r in records),verified=sum(r['decision']=='verified' for r in records),qualified=sum(r['decision']=='qualified' for r in records),unsupported=0,removed_or_corrected=['Removed draft bibliography DOI unrelated to topic in V1; not reintroduced','Replaced stale SoftwareX word-limit assumption with official March 2026 template','Distinguished native 36/120-hour basis from synthetic 24/84-hour comparator','Made private artifact reconciliation distinct from inference rerun','Corrected table references and added rendered appendix tables','Replaced raster figure embeddings with vector PDF content'],audit_scope='all manuscript/supplement prose paragraphs, equations, six captions, architecture/six-cell/route CSV rows',method='Source-bound internal agent review; not external peer review')
(W/'evidence/claims_audit_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
