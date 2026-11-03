# docling-parse #404 PR: word and line cells under per-cell clips

Pages of the regression page selection (`tests/regression_page_selection.py`,
453 documents, 950 pages, dataset revision `df881cc`) whose word or line cells
differ between `main` (f4b12cf) and the #404 branch `fix/clipped-cell-text`
rebased on it. Page render: pypdfium2. Left: cells that `main` emits and the
branch does not (red). Right: the cells that replace them (green and blue
alternate so adjacent cells stay apart). No text changes on any page;
928 of 950 pages are identical, 22 regroup.

Scripts: `dump_cells.py` (word/line cells of the selection as JSONL, run from
each worktree), `compare_dumps.py` (classification and per-page diff, writes
`changes.json`), `before_after.py` (base dump, patched dump, corpus dir, out dir).
