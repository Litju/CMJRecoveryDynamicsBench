from pathlib import Path
import json,math,csv,statistics
W=Path(__file__).resolve().parents[1];x=json.loads((W/'figure_source/plot_inputs.json').read_text())['results'];count=0;unc=[]
for root_index,root in enumerate(x['independent_test_roots']):
 for name,m in root['models'].items():
  cells=m['cells'];assert len(cells)==6
  for c in cells:
   assert c['rows']==4000;assert c['truth_population_sd']>0;assert math.isclose(c['rmse']/c['truth_population_sd'],c['nrmse'],rel_tol=1e-14);count+=1
   assert math.isclose(c['nrmse'],x['across_root_variability'][name]['cell_nrmse_across_roots'][c['cell']]['root_values'][root_index],abs_tol=1e-14)
  assert math.isclose(statistics.mean(c['nrmse'] for c in cells),m['mean_six_cell_nrmse'],abs_tol=1e-14)
  assert math.isclose(m['mean_six_cell_nrmse'],x['across_root_variability'][name]['root_values'][root_index],abs_tol=1e-14)
 for name in ['ridge_full','structured_full']:
  b=root['paired_camp_bootstrap']['models'][name];assert b['valid_replicates']==5000;assert root['paired_camp_bootstrap']['replicates_requested']==5000;assert root['paired_camp_bootstrap']['seed']==49505000
  lo,hi=b['mean_six_cell_nrmse_95_percentile_interval'];dl,dh=b['paired_nrmse_delta_vs_zero_95_percentile_interval'];assert lo<hi and dl<dh<0;unc.append(dict(root='ABC'[root_index],model=name,nrmse_lower=lo,nrmse_upper=hi,paired_delta_vs_zero_lower=dl,paired_delta_vs_zero_upper=dh,valid_replicates=5000))
with (W/'supplement/recorded_uncertainty.csv').open('w') as f:z=csv.DictWriter(f,fieldnames=unc[0]);z.writeheader();z.writerows(unc)
(W/'evidence/numerical_review.json').write_text(json.dumps(dict(per_cell_rmse_sd_ratios_checked=count,root_aggregate_cells_checked=51,original_receipt_vs_summary_equality=True,uncertainty_records_checked=6,uncertainty_recomputed=False,reason='Stored bootstrap endpoints checked and preserved; no new bootstrap or scoring',units={'native_force':'N/kg = m/s^2','native_net_impulse':'N s/kg = m/s','native_identity':'g + J_rel/T has m/s^2','synthetic_nrmse':'dimensionless, cellwise truth-population SD'},no_new_model_execution=True),indent=2))
