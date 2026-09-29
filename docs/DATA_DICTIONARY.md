# Data and configuration dictionary

## Frozen inputs

`analysis/thrust_review_v12/data/targets.csv` and `unseen_targets.csv` contain 64 rows each, with disjoint NORAD identifiers. `x0`–`x5` are target position/velocity and `o0`–`o5` observer position/velocity at encounter start (metres and metres/second). `target` is the internal zero-based index; `range_bin_km` is the initial range stratum, not a constant range throughout the arc. `epochs.csv` / `unseen_epochs.csv` preserve encounter timing. `maneuvers.csv` / `unseen_maneuvers.csv` and `unseen_plan.json` preserve the events. The exact columns are named in each CSV header.

`catalogue_provenance.json` identifies the archived input hash and the catalogue reference epoch. The supplied TLE files are source/provenance records, not measured maneuver or ranging data. Truth, thrust and measurements are synthetic. The catalogue hash does not establish the identity of the original upstream distributor.

## Configurations

- `frozen.json`: original selected control parameters.
- `review_frozen.json`: fine RIT/constant choices and frozen numerical source hashes.
- `period_frozen.json`: phase/period development selections.
- `calibration/detect_{frequency}.json`: thresholds, counts and exposure for each rate.
- `detector_choice.json`, `estimator_frozen.json`, `estimator_choice.json`: fixed detector/estimator decisions.
- Revision `protocol.json`: guard search grids, outage phases, seeds and task tiers.
- Revision `frozen.json`: development candidates, selected alternatives and protocol/source record hashes.

## Per-trajectory records

Each `results/track_*.json` includes its configurations and `rows`. A trajectory is identified by dataset, target, frequency, seed, method name, and task limit. Common fields:

| Field | Meaning |
|---|---|
| `req` | Position limit in metres; velocity limit is `req/10` m/s |
| `position_mse`, `velocity_mse` | Time-mean squared error over the common evaluation interval |
| `position_peak`, `velocity_peak` | Maximum 3D error norm over that interval |
| `bad` | Number of epochs with either constraint exceeded |
| `samples` | Evaluation-epoch denominator |
| `longest_bad` | Longest continuous exceedance duration in seconds |
| `laser_time` | Valid range count / rate over [30,700) s |
| `laser_all_time` | Corresponding effective time including initialization |
| `request_time`, `request_windows` | Requested duration and window count; not effective returns |
| `max_gap` | Maximum observed gap between effective ranging returns |
| `event_mse`, `event_peak` | Per-event error summaries with the stated event windows |

Detection JSON records include timely true positives, false negatives, false positives, late/unassociated/repeated alerts and conditional delays. A missing timely detection remains in the event denominator.

## Aggregation

Position RMSE is the square root of the equally weighted mean of trajectory position MSE; velocity is analogous. Dataset-wide peak is the maximum trajectory peak. Target-peak summaries first take a within-target maximum. These metrics are distinct. The 768 trajectories per dataset/task are 64 targets × four rates × three seeds, not 768 independent geometries. New 10 Hz cells have 192 trajectories. Confidence intervals resample targets, using the frozen seeds.

## Compact arrays and omitted files

Detection `.npz`, forecast `.npz`, and compact timeline/bypass/trigger inputs are retained for plotting and checks. Full high-rate `track_*.npz` and measurement caches are regenerable. Four sample arrays are supplied separately for optional direct high-rate checks. Duplicate summary CSV files can be reconstructed from JSON. The omission does not remove failed trajectories from any record table.
