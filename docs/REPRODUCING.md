# Reproduction map

Run all commands from the repository root, with the pinned environment and `OPENBLAS_NUM_THREADS=1`. Preserve this package as a frozen reference and use a separate working copy for commands that overwrite result or summary files.

## Claims and evidence

| Manuscript evidence | Frozen records | Reproduction/check |
|---|---|---|
| Original/held-out main control comparison | `analysis/thrust_review_v12/results/track_*review_main_*.json` | Root README fresh checks; `run_review.py` for all frequencies/seeds |
| Detection and single-window comparisons | `results/detect_*.json`, `calibration/detect_*.json`, `statistics/budget_records.json` | `detect.py`, `detection_budgets.py`, `summarize.py`, `summarize_review.py` |
| Same-ranging-sequence EKF/IMM comparisons | `results/estimators_*.json` | `control.py --group main`, then `estimators.py` |
| Refined periodic phases | `period_frozen.json`, `results/period_validate_*.json` | `period_sensitivity.py --mode validate`, `summarize_period.py` |
| Guard alternatives and four alert-intervention cells | Revision `frozen.json`, `results/track_*validation*.json` | Revision `batch.py validation`, then `summarize.py` |
| Laser-only outage phase dependence | Revision `results/track_outages*.json` | Revision `batch.py outages` |
| Signed aggregate/sequential forecasts | Revision `results/forecast_signed_*.json` and `.npz` | Revision `forecast_diagnostic.py FREQUENCY` |
| Main, held-out and new aggregate consistency | Both JSON result trees and stored summaries | `python scripts/verify_results.py` (46,464 record checks) |
| Published figures | Compact statistics, detection and timeline inputs | `python scripts/plot_all.py` |

Paths above are relative to `analysis/thrust_review_v12/` unless identified as revision (`analysis/applsci_revision_20260929/`). All summary fractions keep their documented trajectory or target denominator. No high-rate epoch is treated as an independent statistical replicate.

## Full frozen main validation

All optical detection NPZ files required by these commands are included. Missing measurement caches are generated automatically from frozen target states.

```bash
python analysis/thrust_review_v12/run_review.py
python analysis/thrust_review_v12/run_service.py
python analysis/thrust_review_v12/bypass.py
MSC_SET=unseen python analysis/thrust_review_v12/bypass.py
python analysis/thrust_review_v12/detection_budgets.py
python analysis/thrust_review_v12/period_sensitivity.py --mode validate
```

For the estimator comparison and original ablations:

```bash
for f in 5 10 15 20; do
  for seed in 260930401 260930402 260930403; do
    python analysis/thrust_review_v12/control.py --freq "$f" --seed "$seed" --group main
    python analysis/thrust_review_v12/estimators.py --freq "$f" --seed "$seed"
  done
  python analysis/thrust_review_v12/forecast_check.py --freq "$f"
done
for seed in 260930401 260930402 260930403; do
  python analysis/thrust_review_v12/control.py --freq 10 --seed "$seed" --group phases
done
python analysis/thrust_review_v12/summarize.py
python analysis/thrust_review_v12/summarize_review.py
python analysis/thrust_review_v12/reanalyze_followup.py
python analysis/thrust_review_v12/summarize_period.py
```

These summary commands can also run against packaged JSON and compact arrays without repeating full simulation. They regenerate omitted CSV exports. An integrity check will intentionally detect changed tracked outputs afterward; compare in a working copy.

## Current revision validation

Use the packaged development-frozen settings; do not run selection again:

```bash
python analysis/applsci_revision_20260929/batch.py validation
python analysis/applsci_revision_20260929/batch.py outages
for f in 5 10 15 20; do
  python analysis/applsci_revision_20260929/forecast_diagnostic.py "$f"
done
python analysis/applsci_revision_20260929/summarize.py
python analysis/applsci_revision_20260929/check.py
```

`batch.py` runs up to five child jobs. Full sweeps are substantially larger than the minimal fresh core checks. They overwrite the working copy's result files. No exact completion-time or maximum-memory guarantee is made.

A single signed-forecast rerun uses:

```bash
python analysis/applsci_revision_20260929/forecast_diagnostic.py 10
```

At 10 Hz there are 4288 sampled starts per tier; expected aggregate-off/reference-on counts are 1/0/1, reverse counts 0/0/0. This reruns filter trajectories with frozen parameters; it is more expensive than an aggregate record check.

## Optional high-rate sample archive

Restore the accompanying `MSC-GP_ValidationSamples_20260930.zip` **at the repository root**, keeping internal paths. It contains two 5 Hz main samples and two 10 Hz revision samples. Then:

```bash
python analysis/thrust_review_v12/verify_sample.py
python analysis/applsci_revision_20260929/check.py
```

The first checks 2304 stored high-rate trajectory records; the second checks 2432 and equal ranging masks. Without these arrays, the commands correctly fail rather than claim raw validation. The upload version of revision `summarize.py` also explicitly refuses a replay-mask check when no high-rate validation arrays are present. `scripts/verify_results.py` is the smaller JSON-only check and states that limited scope.

The optional arrays can be regenerated instead:

```bash
python analysis/thrust_review_v12/control.py --freq 5 --seed 260930401 --group review_main
MSC_SET=unseen python analysis/thrust_review_v12/control.py --freq 5 --seed 261001401 --group review_main
python analysis/applsci_revision_20260929/run.py validation --seed 260930401
MSC_SET=unseen python analysis/applsci_revision_20260929/run.py validation --seed 261001401
```

## Development reconstruction (separate copy only)

Development settings are already frozen. These commands can change selected parameters and are not part of validation:

```bash
python analysis/thrust_review_v12/control.py --freq 10 --seed 260930101 --group main
python analysis/thrust_review_v12/develop_review.py
python analysis/thrust_review_v12/period_sensitivity.py --mode develop
python analysis/applsci_revision_20260929/batch.py development
python analysis/applsci_revision_20260929/select.py
```

The first command restores the omitted development trace used by `develop_review.py`. Earlier initial-development details are in `analysis/thrust_review_v12/protocol.md` and `develop.py`; their frozen choices, candidate records and calibration outputs remain included. Do not interpret rerun selections on validation as the published experiment.

## Data provenance and service definition

The initial states and encounter epochs are the authoritative simulation inputs. The archived TLE catalogue's upstream URL and redistribution terms were not retained; see `THIRD_PARTY_NOTICES.md`. Optional constellation selection uses SGP4; it is not required for frozen-state simulation. Installing an arbitrary SGP4 version is not evidence of reproducing the initial target selection.

Only laser ranging is missing in outage tests. Requests are merged before a fixed-delay shift. Issued requests are neither canceled nor retried; a successful due request provides a current-epoch synchronous range. Only effective returns reset the last-range epoch. Effective time differs from requested time and energy. Full service assumptions and parameters are frozen in the supplied protocol/configurations.
