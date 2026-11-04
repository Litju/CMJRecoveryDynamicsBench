from pathlib import Path
import json,re,html,csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Flowable,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pymupdf
W=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
s=getSampleStyleSheet()
for key in s.byName:s[key].fontName='DejaVu';s[key].fontSize=10;s[key].leading=15
s['Title'].fontSize=17;s['Title'].leading=23
for key in ['Heading1','Heading2']:s[key].fontName='DejaVu-Bold';s[key].fontSize=12 if key=='Heading1' else 10;s[key].leading=18;s[key].spaceBefore=12;s[key].spaceAfter=7
s['BodyText'].spaceAfter=8
s['Heading1'].keepWithNext=1
s['Heading2'].keepWithNext=1
placements=[]
class VectorPDF(Flowable):
 def __init__(self,path,maxwidth=487,maxheight=500):
  super().__init__();self.path=path
  with pymupdf.open(path) as doc:rect=doc[0].rect
  scale=min(1,maxwidth/rect.width,maxheight/rect.height);self.width=rect.width*scale;self.height=rect.height*scale
 def draw(self):
  x,y=self.canv.absolutePosition(0,0);placements.append((self.canv.getPageNumber()-1,self.path,x,y,self.width,self.height))

def equation_pdf(number):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 expressions={1:r"$|a-b|\leq 10^{-5}+10^{-4}|b|\qquad(1)$",2:r"$F_{\mathrm{rel}}=\frac{1}{mT}\int_{t_{\mathrm{co}}}^{t_{\mathrm{to}}}F_z(t)\,dt\quad[\mathrm{N/kg}]\qquad(2)$",3:r"$J_{\mathrm{rel}}=\frac{1}{m}\int_{t_{\mathrm{co}}}^{t_{\mathrm{to}}}(F_z(t)-mg)\,dt\quad[\mathrm{m/s}]\qquad(3)$",4:r"$\mathrm{RMSE}_c=\sqrt{\frac{\sum_{i=1}^{n_c}(\widehat y_i-y_i)^2}{n_c}},\quad\mathrm{NRMSE}_c=\frac{\mathrm{RMSE}_c}{\mathrm{SD}_{\mathrm{pop}}(y_c)}\quad(4)$"}
 path=W/f'figures/equation{number}.pdf';fig=plt.figure(figsize=(6.5,.65));fig.text(.01,.4,expressions[number],fontsize=14);fig.savefig(path,bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});plt.close(fig);return path

def blocks(text):
 out=[]
 for p in text.split('\n\n'):
  p=p.strip()
  if not p:continue
  match=re.search(r'\(([1-4])\)$',p.strip())
  if match:
   out.append(VectorPDF(equation_pdf(int(match.group(1))),maxwidth=475,maxheight=65));out.append(Spacer(1,8));continue
  level=len(p)-len(p.lstrip('#'));style=s['Title' if level==1 else 'Heading1' if level==2 else 'Heading2' if level==3 else 'BodyText'];out.append(Paragraph(html.escape(p.lstrip('#').strip()).replace('\n','<br/>'),style))
 return out

def footer(c,d):c.setFont('DejaVu',8);c.drawString(48,27,'Private owner-review manuscript • M10 qualified revision V2');c.drawRightString(547,27,str(d.page))
def build(path,story):SimpleDocTemplate(str(path),pagesize=(595,842),rightMargin=48,leftMargin=48,topMargin=45,bottomMargin=45,title='Recovering Reproducibility in Scientific Machine Learning',author='Authorship pending owner confirmation',invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)
def table(rows,widths):
 data=[[Paragraph(html.escape(str(cell)),s['BodyText']) for cell in row] for row in rows];t=Table(data,colWidths=[x*487/sum(widths) for x in widths],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,-1),(-1,-1),.5,colors.black)]));return t
D=json.loads((W/'figure_source/plot_inputs.json').read_text());story=blocks((W/'manuscript/manuscript.md').read_text());story.append(PageBreak());story+=blocks('## Table 1. Fixed-mode public synthetic results\n\nNRMSE is dimensionless. Values are calculated from the original public receipt; SD is sample SD across three roots, not a confidence interval. Each root comprises 16 synthetic camps. Source S01.')
rows=[['Model','Root A','Root B','Root C','Mean','SD']]
for k,n in zip(['zero_innovation','training_constant','ridge_full','structured_full'],['Zero','Constant','Ridge','Structured']):
 v=D['results']['across_root_variability'][k];rows.append([n]+[f'{x:.6f}' for x in v['root_values']+[v['root_mean_nrmse'],v['root_sample_sd_nrmse']]])
story.append(table(rows,[84,83,83,83,83,83]));story.append(Spacer(1,20));story+=blocks('## Table 2. Original model families and qualification\n\nEvery family has repeats r0 and r1. CPU equality is recorded original-source equality; CUDA status compares CPU outputs with saved historical CUDA outputs under Equation (1). No original GPU replay or predictive accuracy is implied. Public sources S06–S08 and S12–S16; private identities were reconciled separately.')
counts=[1346,2690,6850,7138,10626,10658,10738,10786,10796];rows=[['ID','Params','Input branches','CPU source','Saved CUDA']]
for m,c in zip(D['models'],counts):rows.append([m['id'],f'{c:,}',m['inputs'],'Exact, r0/r1','Pass, r0/r1' if m['cuda']=='Within recorded tolerance' else 'FAIL, r0/r1'])
story.append(table(rows,[45,70,200,92,92]))
refs=json.loads((W/'bibliography/verified_metadata.json').read_text());bib=[]
for r in refs:
 assert r['verified'];m=r['metadata'];a=', '.join(q.get('family','')+' '+''.join(v[0]+'.' for v in q.get('given','').split() if v) for q in m.get('author',[])[:6])+(', et al.' if len(m.get('author',[]))>6 else '');year=m.get('published',m.get('issued',{})).get('date-parts',[[0]])[0][0];vol=m.get('volume','');page=m.get('page',m.get('article-number',''));bib.append(f"[{r['id']}] {a} ({year}). {m['title'][0]}. {m.get('container-title',[''])[0]} {vol}: {page}. {r.get('doi',r.get('url',''))}")
(W/'bibliography/references.md').write_text('\n\n'.join(bib));story.append(PageBreak());story+=blocks('## References\n\n'+'\n\n'.join(bib)+'\n\nPyTorch contributors. Numerical accuracy. https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html (accessed 4 November 2026). Implementation documentation; not peer reviewed.')
caps=(W/'figures/captions.md').read_text().split('\n\n')
for i in range(1,7):story.append(PageBreak());story+=blocks('## Figure '+str(i));story.append(VectorPDF(W/f'figures/figure{i}.pdf'));story.append(Spacer(1,15));story+=blocks(caps[i-1]+' Figures are designed for a full journal text width of approximately 175–180 mm; retain full width for the architecture and numerical matrices.')
build(W/'manuscript.pdf',story)
with pymupdf.open(W/'manuscript.pdf') as doc:
 for pn,path,x,y,width,height in placements:
  with pymupdf.open(path) as figure:doc[pn].show_pdf_page(pymupdf.Rect(x,842-y-height,x+width,842-y),figure,0)
 doc.save(W/'manuscript.vector.pdf',no_new_id=True,garbage=4,deflate=True)
(W/'manuscript.vector.pdf').replace(W/'manuscript.pdf')
a=blocks((W/'supplement/technical_appendix.md').read_text());a.append(Spacer(1,16));a+=blocks('## Table A2. Architecture and qualification matrix\n\nEach row represents repeats r0 and r1 with the same public architecture and qualification status. Private hashes and run locators are excluded. The corresponding 18-route CSV retains one row per repeat. Sources S06–S08 and S12–S16.');a.append(table(rows,[45,70,200,92,92]));a.append(PageBreak());a+=blocks('## Table A3. Six-cell synthetic results\n\nMean NRMSE across roots A/B/C; population-SD normalization within each outcome/horizon. Values are dimensionless. Source S01. Full root-specific values and sample SDs are in six_cell_results.csv.')
keys=['zero_innovation','training_constant','ridge_full','structured_full'];xx=D['results']['across_root_variability'];cells=sorted(xx['ridge_full']['cell_nrmse_across_roots']);rr=[['Cell','Zero','Constant','Ridge','Structured']]
for cell in cells:rr.append([cell.split('/')[0]+(' impulse' if 'net_impulse' in cell else ' force')]+[f"{xx[k]['cell_nrmse_across_roots'][cell]['root_mean_nrmse']:.6f}" for k in keys])
a.append(table(rr,[119,95,95,95,95]));a.append(Spacer(1,20));a+=blocks('## Table A4. Recorded paired camp-bootstrap intervals\n\n95% percentile intervals for aggregate NRMSE and model-minus-zero NRMSE. Each root has 16 synthetic camps; 5,000 valid paired resamples, PCG64 seed 49,505,000. Negative deltas favor the model. These are descriptive same-generator intervals and are not ridge-versus-structured comparisons. Original endpoints retained from S01; no bootstrap rerun.')
rr=[['Root','Model','NRMSE interval','Delta vs zero interval']]
for row in csv.DictReader((W/'supplement/recorded_uncertainty.csv').open()):rr.append([row['root'],'Ridge' if row['model']=='ridge_full' else 'Structured',f"[{float(row['nrmse_lower']):.4f}, {float(row['nrmse_upper']):.4f}]",f"[{float(row['paired_delta_vs_zero_lower']):.4f}, {float(row['paired_delta_vs_zero_upper']):.4f}]"])
a.append(table(rr,[40,95,176,176]));build(W/'supplement/technical_appendix.pdf',a)
print('Rendered vector-figure manuscript and complete supplement tables')
