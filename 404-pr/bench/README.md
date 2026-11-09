# Cost of the clip capture (docling-parse PR #443)

Interleaved A/B of upstream `main` (c2b39af) against the PR branch, single thread,
on one x86_64 Linux machine (GCC 15), both builds on CPython 3.12.15.

- `ab_rss.py`: the harness. One fresh process per pass, builds in alternating
  order; each pass loads every PDF of a directory, iterates its pages and
  materialises char, word and line cells to Python; prints wall time,
  `ru_maxrss`, pages, words and the words that carry a clip box.
  `AB_SKIP_SHAPES=1` parses with `shapes_content_level=SKIP`, which is what
  docling does unless it renders.
- Corpora: `bench-untagged`, 60 PDFs, 1021 pages, 311k words (16% under a
  clip); `bench-tagged-20`, 20 tagged PDFs, 147 pages, 44k words (33% under a
  clip). Local benchmark sets, not the regression dataset.
- `run_ab.sh` -> `ab.log`: head 59e8341 (before the clip box cache). Phase 1
  with docling-core#964 installed (Python builds a `BoundingBox` per clipped
  cell), phase 2 with the locked docling-core 2.103.1.
- `confirm_tagged_skip.log`: 59e8341, tagged corpus, shapes skipped, locked
  docling-core, 7 passes.
- `run_ab2.sh` -> `ab2.log`: head 0ac887c (with the cache); phase B with
  docling-core#964, phase A with the locked release, 7 passes where the cost
  had shown.
- `run_ab3.sh` -> `ab3.log`: 0ac887c with docling-core#964, tagged corpus,
  shapes skipped, 7 passes, plus the count of clip boxes per cell level.
- `sizeof_probe.cpp`: the syntax-only probe that reports
  `sizeof(page_item<PAGE_CELL>)` as a compile error (448 on main, 488 on the
  branch, with the include directories of a configured build).
