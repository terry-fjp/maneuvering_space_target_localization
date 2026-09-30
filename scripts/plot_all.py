"""Regenerate the 11 manuscript figures and supporting standalone tables.
Only presentation outputs are overwritten; frozen numerical inputs are unchanged.
"""
from pathlib import Path
import subprocess,sys,shutil
R=Path(__file__).resolve().parents[1]
required=[
 R/'analysis/thrust_review_v12/statistics/timeline_source.npz',
 R/'analysis/thrust_review_v12/statistics/bypass_original.npz',
 R/'analysis/thrust_review_v12/results/detect_10_260930403_0.npz',
]
missing=[str(p.relative_to(R)) for p in required if not p.is_file()]
if missing:
 raise SystemExit('Full-data attachment required. Restore it at the repository root; see docs/FULL_DATA.md. Missing examples: '+', '.join(missing))
old=R/'output/latex/remotesensing_submission_en/figures';new=R/'output/latex/applsci_submission_en/figures'
old.mkdir(parents=True,exist_ok=True);new.mkdir(parents=True,exist_ok=True)
for name in ['diagrams','base_figures','plot_geometry','plot_review','plot_followup']:
 subprocess.run([sys.executable,str(R/f'analysis/manuscript_submission_en/{name}.py')],cwd=R,check=True)
subprocess.run([sys.executable,str(R/'analysis/applsci_revision_20260929/build_results.py')],cwd=R,check=True)
for n in ['scenario','workflow','deadline','geometry_holdout','detection_strata','tradeoff','period_selection_sensitivity','timeline','target_failure','bypass']:
 shutil.copy2(old/f'{n}.pdf',new/f'{n}.pdf')
assert len(list(new.glob('*.pdf')))>=11
print('PASS: all 11 manuscript figures are in output/latex/applsci_submission_en/figures/')
