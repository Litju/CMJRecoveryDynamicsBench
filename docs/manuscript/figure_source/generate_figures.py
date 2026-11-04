from pathlib import Path
import json,textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
W=Path(__file__).resolve().parents[1]; D=json.loads((W/'figure_source/plot_inputs.json').read_text()); ink='#20252b';blue='#235caa';red='#be482d'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':ink,'axes.labelcolor':ink,'svg.hashsalt':'m10','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
def save(n,fig):
 fig.savefig(W/f'figures/figure{n}.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});fig.savefig(W/f'figures/figure{n}.svg',bbox_inches='tight',metadata={'Date':None});fig.savefig(W/f'figures/figure{n}.png',dpi=180,bbox_inches='tight');plt.close(fig)
def box(ax,x,y,s,w=.29,h=.13):
 ax.text(x,y,s,ha='center',va='center',fontsize=12,bbox=dict(boxstyle='square,pad=.6',fc='white',ec=blue),transform=ax.transAxes,zorder=3)
def arrow(ax,a,b):ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color=ink,shrinkA=24,shrinkB=24),zorder=1)
from matplotlib.patches import Rectangle
f,a=plt.subplots(figsize=(10,6));a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off')
pos=[(.18,.87),(.18,.65),(.76,.87),(.18,.42),(.50,.42),(.82,.42),(.56,.14),(.86,.14)]
labels=['Initial preseason','Canonical preseason','Rich-history camp','Preliminary\npost-exposure','Phase-consistent','Correlated exposure','Threshold response','Fixed-mode\ndiscrepancy']
width=.28;height=.16
for v,(xx,yy),label in zip(D['lineage'],pos,labels):
 a.add_patch(Rectangle((xx-width/2,yy-height/2),width,height,fc='white',ec=blue,zorder=3));a.text(xx,yy,label+'\n'+v['status'].replace('_',' '),ha='center',va='center',fontsize=11,zorder=4)
for i,v in enumerate(D['lineage']):
 if v['parent']:
  j=next(j for j,q in enumerate(D['lineage']) if q['id']==v['parent']);x0,y0=pos[j];x1,y1=pos[i]
  if y0==y1:start=(x0+width/2,y0);end=(x1-width/2,y1)
  else:start=(x0,y0-height/2);end=(x1,y1+height/2)
  a.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color=ink,shrinkA=1,shrinkB=1),zorder=2)
save(1,f)
f,a=plt.subplots(figsize=(8,7));a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off');steps=['Preserve originals\nread-only inventory','Authenticate checkpoint\nconfiguration + repeat','Recover source\narchitecture + tensors','Restore fitted preprocessing\nno refitting','Qualify CPU inference\noriginal-source equality','Compare saved CUDA\nfrozen tolerance','Bind claims to receipts\nrights + limitations']
for i,label in enumerate(steps):
 yy=.94-i*.14;a.add_patch(Rectangle((.16,yy-.045),.68,.09,fc='white',ec=blue));a.text(.5,yy,label,ha='center',va='center',fontsize=12)
 if i:a.annotate('',xy=(.5,yy+.045),xytext=(.5,yy+.095),arrowprops=dict(arrowstyle='->',color=ink,shrinkA=1,shrinkB=1))
save(2,f)
f,a=plt.subplots(figsize=(10,7));a.axis('off')
for i,m in enumerate(D['models']):
 y=.96-i*.105;a.text(.01,y,m['id']+'\nr0 / r1',va='top',weight='bold',color=blue);a.text(.13,y,'\n'.join(textwrap.wrap(m['architecture'],76))+'\nInputs: '+m['inputs'],va='top',fontsize=12)
save(3,f)
f,a=plt.subplots(figsize=(9,6));a.set_xlim(-.5,3.8);a.set_ylim(17.5,-.5)
for i,m in enumerate(D['models']):
 for r in range(2):
  row=2*i+r
  for col in range(2):
   passed=(m['cpu']=='Exact source parity') if col==0 else (m['cuda']=='Within recorded tolerance');a.scatter(col,row,marker='o' if passed else 'x',s=100,c=blue if passed else red);a.text(col+.12,row,'exact' if col==0 else ('pass' if passed else 'FAIL'),va='center',fontsize=12)
a.set_xticks([0,1],['CPU vs original\nCPU source','CPU vs saved\nhistorical CUDA']);a.set_yticks(range(18),[m['id']+'-'+r for m in D['models'] for r in ['r0','r1']]);a.grid(axis='y',alpha=.15);a.text(2,-.1,'Recorded qualification\n24 synthetic rows\n512 historical rows\n\nCUDA comparison:\n|replayed − saved| ≤\n10⁻⁵ + 10⁻⁴ |saved|\n\nPass ≠ original GPU replay.\nNo accuracy inference.',va='top',fontsize=12);save(4,f)
x=D['results']['across_root_variability']; keys=['zero_innovation','training_constant','ridge_full','structured_full'];print('available',list(x))
# Resolve the receipt's precise model keys, without replacing data.
keys=[next(k for k in x if k in opts) for opts in [('zero','zero_innovation'),('training_constant','train_constant'),('ridge_full',),('structured_full',)]]
f,axs=plt.subplots(1,2,figsize=(10,4),gridspec_kw={'width_ratios':[1,1.25]});labels=['Zero innovation','Training constant','Full ridge','Structured']
for i,k in enumerate(keys):
 vals=x[k]['root_values'];axs[0].scatter(vals,[i]*3,c=blue,marker='o',s=35);axs[0].scatter(x[k]['root_mean_nrmse'],i,c=ink,marker='|',s=150)
axs[0].set_yticks(range(4),labels);axs[0].invert_yaxis();axs[0].set_xlim(0,2.65);axs[0].set_xlabel('Mean six-cell NRMSE (dimensionless)');axs[0].set_title('Three roots; marks are observations')
cells=list(x[keys[2]]['cell_nrmse_across_roots']);cells.sort();arr=np.array([[x[k]['cell_nrmse_across_roots'][c]['root_mean_nrmse'] for k in keys] for c in cells]);axs[1].set_xlim(-.5,3.5);axs[1].set_ylim(5.5,-.5)
for i in range(6):
 for j in range(4):axs[1].add_patch(Rectangle((j-.5,i-.5),1,1,facecolor=plt.cm.Blues(arr[i,j]/3.1),edgecolor='none'))
axs[1].set_yticks(range(6),[c.split('/')[0]+(' impulse' if 'net_impulse' in c else ' force') for c in cells]);axs[1].set_xticks(range(4),['Zero','Constant','Ridge','Structured'],rotation=30,ha='right')
for i in range(6):
 for j in range(4):axs[1].text(j,i,f'{arr[i,j]:.3f}',ha='center',va='center',fontsize=12,color='white' if arr[i,j]>1.8 else ink)
axs[1].set_title('Per-cell NRMSE, mean across roots');f.tight_layout();save(5,f)
f,(a,b)=plt.subplots(2,1,figsize=(10,5),gridspec_kw={'height_ratios':[1,1.2]});a.axis('off');a.text(.02,.7,'Supplied force Fz(t) [N] • explicit system mass m [kg] • interval T = t_to − t_co [s]',fontsize=12);a.text(.02,.35,'Gross mean force: ∫ Fz dt / (mT) [N/kg]\nNet impulse: ∫ (Fz − mg) dt / m [m/s]',fontsize=12);a.text(.02,-.12,'Interpolate event boundaries; composite trapezoids; mean of exactly three valid trials.',fontsize=12)
for y,(lo,hi,label) in enumerate([(-240,-24,'Baseline: latest two qualifying assessments'),(66,78,'H72: 66–78 h'),(156,180,'D7: 156–180 h')]):b.plot([lo,hi],[y,y],lw=10,c=blue);b.text((lo+hi)/2,y+.17,label,ha='center',fontsize=12)
b.axvline(0,c=red,ls='--');b.text(0,2.55,'Origin',ha='center');b.set_xlim(-260,205);b.set_ylim(-.4,2.9);b.set_yticks([]);b.set_xlabel('Hours relative to origin');save(6,f)
