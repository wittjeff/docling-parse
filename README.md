# Evidence for docling-parse renderer topic PR (#428: stroke clipping, tiling patterns, soft masks)

- `compare.md`: before/after `mean_abs_error` and `changed_pixels_ratio` against pypdfium2 over the regression corpus (`main` 2fb6525 vs the PR branch), produced with the same page set, scale and metric as `tests/test_regression_pypdfium_render.py`.
- `main.csv`, `topic.csv`: the per-page measurements behind it.
- `panels/`: three-panel images of the cited pages, pypdfium2 | before (main) | after (this PR), at the test's render scale.
