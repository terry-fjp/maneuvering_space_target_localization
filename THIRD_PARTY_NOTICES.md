# Third-party inputs and dependencies

- NumPy, SciPy and Matplotlib are installed separately through `requirements.txt`; their upstream licenses apply. No dependency binaries or environments are bundled.
- TLE records originate from the user-supplied archived Starlink catalogue identified in `analysis/thrust_review_v12/data/catalogue_provenance.json`. The exact original provider URL, retrieval timestamp and redistribution terms were not retained. No upstream provider or license is invented here, and the repository's rights notice does not grant rights in third-party records. The public-release operator should verify the catalogue's redistribution basis before publication. Frozen numerical target states permit all main benchmark simulations without downloading a catalogue or installing SGP4.
- The original catalogue SHA-256 is `9f7e04fc3ffbf6e0e0fc8d26fb80ceeebd9db1f0f896aeca2fb01a393414d9b6`.
- MDPI class/style/logo files, template-formatted manuscript PDFs and historical manuscripts are excluded from this public code repository. Their journal-submission package remains separate. Standalone author-generated tables and plotting scripts are included.
- No font files are bundled. English plot builders use Matplotlib's DejaVu Sans font.
