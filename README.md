# MSC-GP: Maneuvering Space Target Tracking and Laser Ranging Control

Code and compact numerical records accompanying **Multiscale Consistency-Driven Tracking and Laser Ranging Control for Maneuvering Space Targets**, by Jiapeng Feng, Shihan Dong, Yuqing Li, Sensen Guo, Haiying Hu, and Jun Zhou. Intended journal: *Applied Sciences*, Aerospace Science and Engineering.

Scientific configuration: **AS-MSCGP-20260929-R2**. Packaging revision: **github-slim1** (2026-09-30). This repository contains the implementation, frozen configuration, compact summaries, and two 5 Hz reference files for fresh core checks. The full per-trajectory and plotting records are distributed separately; see [docs/FULL_DATA.md](docs/FULL_DATA.md). The manuscript is unpublished; no article DOI or journal acceptance is claimed.

**Rights:** publicly viewable for review, **not open source**. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before reuse.

## What is evaluated

MSC-GP combines optical maneuver alerts, prior-retaining estimation, process-noise adaptation, and guarded prediction of laser-ranging demand. This is an **algorithm benchmark under a hypothetical observation-service interface**, not a demonstrated payload specification or a probability-of-safety guarantee.

- Observer: 800 km altitude, 60° inclination; original and disjoint held-out sets contain 64 targets each.
- Sustained thrust only: 60 s events, acceleration 0.01–0.20 m/s² across eight prescribed levels; timely detection deadline 60 s.
- Paired synchronous angular/range sampling: 5, 10, 15, 20 Hz. Angular total RMSE 100 μrad; range RMSE 50 m; range cutoff 2000 km.
- Position/velocity limits: 500 m/50 m/s, 1000 m/100 m/s, 1500 m/150 m/s.
- Main evaluation: all trajectories over [30,700) s, 768 trajectories per dataset/tier. Inference resamples 64 target clusters.
- Effective range occupancy is valid measurement count divided by frequency. It is not energy or hardware busy time. Supplementary outages affect only the laser; optical observations continue.

## Installation and first checks

Recorded numerical environment: Python 3.12.3, NumPy 2.5.2, SciPy 1.18.1, Matplotlib 3.11.1. No machine-learning model or training weights are required. Main frozen-state simulations do not require SGP4 or network access after dependency installation. Versions are pinned in `requirements.txt`.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1
python scripts/verify_integrity.py
python analysis/thrust_review_v12/smoke.py
```

The integrity command checks every distributed file. The smoke check exercises the filter, IMM and coordinate invariance. Restoring the full-data attachment additionally enables the 46,464-record aggregate check and complete plotting workflow.

## Fresh simulation from frozen initial states

Run from the repository root. These commands regenerate truth, noise, optical alerts and tracking without measurement caches, in temporary directories, and compare 256 method–target records per dataset:

```bash
python analysis/applsci_submission_en/reproduce_core.py --dataset original --output reproduced/original.json
python analysis/applsci_submission_en/reproduce_core.py --dataset unseen --output reproduced/unseen.json
```

Expected: `status: PASS` and `matched_records: 256` in each file. Continuous MSE/peak fields use `rtol=1e-6, atol=1e-5`; violation counts, range counts/times and longest violations require exact matches. A changed discrete decision fails visibly; the checker does not relax tolerances. This is a local reproducibility procedure, not a claim of external independent replication.

Representative **5 Hz, one seed, 1000 m/100 m/s** results follow. They are not the pooled main-table results.

| Dataset | Controller | Position RMSE (m) | Peak (m) | Violating trajectories | Effective ranging (s) |
|---|---|---:|---:|---:|---:|
| Original | MSC-GP | 104.808712 | 842.878975 | 0/64 | 21.812500 |
| Original | Periodic | 56.884320 | 486.673780 | 0/64 | 31.787500 |
| Original | RIT-fine | 115.509824 | 920.366545 | 0/64 | 21.231250 |
| Original | Constant | 104.470278 | 882.523134 | 0/64 | 21.734375 |
| Held-out | MSC-GP | 94.928475 | 772.518821 | 0/64 | 22.393750 |
| Held-out | Periodic | 56.727624 | 489.716602 | 0/64 | 32.484375 |
| Held-out | RIT-fine | 111.668114 | 1275.555193 | 1/64 | 21.862500 |
| Held-out | Constant | 107.112447 | 1050.484224 | 1/64 | 22.240625 |

## Compact results and full-data attachment

Compact published summaries and standalone table sources are included. Large development sweeps, complete per-trajectory records, and plotting NPZ files are intentionally omitted from the Git repository. Their expected paths and the capabilities they restore are listed in [docs/FULL_DATA.md](docs/FULL_DATA.md).

After restoring the full-data attachment at the repository root, run `python scripts/verify_results.py` to recompute 134 aggregate groups from 46,464 trajectory records and `python scripts/plot_all.py` to regenerate all 11 manuscript figures. These checks do not claim external independent replication or onboard timing validation.

See [docs/REPRODUCING.md](docs/REPRODUCING.md) for the full claim-to-command map, development/validation separation, optional high-rate checks, and omitted-cache regeneration. [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) describes inputs and record fields. [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) lists presentation-only and check-reporting changes made for distribution. [docs/LOCAL_VALIDATION.json](docs/LOCAL_VALIDATION.json) records package checks actually run.

The complete new-condition tables are in `analysis/applsci_revision_20260929/SUPPLEMENTARY_RESULTS.md`; compact pooled statistics are in `analysis/thrust_review_v12/statistics/`. Full failed-trajectory and competitive-baseline records are in the separate data attachment. Fixed additive margins can use less range time; IMM often has lower RMSE; outage overlap can cause violations. The work does not establish universal MSC-GP superiority.

## Repository layout

| Path | Role |
|---|---|
| `analysis/thrust_review_v12/` | Frozen main implementation, calibration, target states, configurations, compact statistics and two core reference files |
| `analysis/applsci_revision_20260929/` | Guard alternatives, intervention decomposition, outage phases and signed forecasts |
| `analysis/applsci_submission_en/reproduce_core.py` | Fresh original/held-out simulation check |
| `analysis/manuscript_submission_en/` | English standalone figure builders |
| `output/latex/applsci_submission_en/tables/` | Standalone scientific table sources; no MDPI class or manuscript |
| `scripts/` | Integrity check plus full-data aggregate and figure entry points |
| `docs/` | Reproduction, data definitions, provenance and local validation |
