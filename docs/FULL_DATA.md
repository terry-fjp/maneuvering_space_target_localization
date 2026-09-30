# Full-data attachment

The slim GitHub repository is sufficient for integrity checking, smoke testing, and the two fresh 5 Hz core reproductions in the root README. The complete frozen numerical record is intentionally kept outside Git history.

The companion full-data attachment restores these paths:

- `analysis/thrust_review_v12/results/`, except the two reference JSON files already present;
- `analysis/thrust_review_v12/statistics/*.npz`;
- `analysis/applsci_revision_20260929/results/`;
- optional high-rate validation samples documented in `REPRODUCING.md` when those samples are distributed.

Extract the attachment at the repository root without changing its internal paths. Then run:

```bash
python scripts/verify_integrity.py
python scripts/verify_results.py
python scripts/plot_all.py
```

The attachment should be distributed as a GitHub Release asset or deposited in a research-data repository. Publish its SHA-256 digest alongside the download. Do not commit the restored files to the slim branch; `.gitignore` excludes them deliberately.
