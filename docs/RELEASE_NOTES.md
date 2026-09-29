# Distribution revision upload1

Date: 2026-09-30. Scientific reference: AS-MSCGP-20260929-R2.

- Frozen numerical implementation, selected parameters, target inputs, trajectory JSON and summary values are copied from the verified S1 archive without tuning.
- Removed historical manuscript PDFs, MDPI template/style/logo files, local review correspondence, local audit logs and manuscript migration scripts.
- Split four regenerable high-rate validation NPZ files into an optional Release attachment; omitted duplicate CSV exports and a regenerable development trace.
- English plotting scripts use Matplotlib DejaVu Sans instead of an unnecessary separately bundled Droid fallback. Data, axes and plot geometry remain unchanged.
- Revision `summarize.py` now fails explicitly if no high-rate validation NPZ exists before checking replay-mask identity. The statistical formulas and outputs when samples exist are unchanged; a vacuous check is never reported as PASS.
- Added integrity and aggregate-result checks, exact fresh-run commands, plotting wrapper, input/record dictionary, citation metadata and a rights-reserved notice, as requested by the authors.
- This package is not an open-source release. No GitHub upload, DOI deposit or journal submission was performed by the packaging step.

Local execution results are in `LOCAL_VALIDATION.json`. File-level hashes are in the repository root `SHA256SUMS.json`; optional-archive hashes are in the external delivery manifest to avoid a circular archive self-hash.
