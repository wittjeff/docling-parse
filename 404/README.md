# docling-parse #404: word and line cells under per-cell clips

Pages of the regression page selection (`tests/regression_page_selection.py`) whose
word or line cells differ between docling-parse 7.22.1 and the prototype on
wittjeff/docling-parse `fix/clipped-cell-text` (cd85824). Page render: pypdfium2.
Left: cells that 7.22.1 emits and the prototype does not (red). Right: the cells
that replace them (green and blue alternate so adjacent cells stay apart).
No text changes on any page; 918 of 940 pages are identical.

Script: `before_after.py` (base dump, patched dump, corpus dir, out dir).
