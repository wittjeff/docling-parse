#!/bin/bash
# Interleaved A/B, both builds on Python 3.12: upstream main (c2b39af) vs PR #443 head (59e8341).
# Phase 1: PR venv with docling-core#964 (Python builds a BoundingBox per clipped cell) = upper bound.
# Phase 2: PR venv with the locked docling-core 2.103.1 (what the lockfile gives today).
S=/tmp/claude-1000/-home-witt-code-docling/18f36680-f38e-4a68-a312-d9cdae94a438/scratchpad/mypy443
BASE=/home/witt/code/docling-parse-404-base/.venv/bin/python
PR=/home/witt/code/docling-parse-404/.venv/bin/python
D=/home/witt/Downloads/337-followups
set -o pipefail
uv pip install -q --python $PR /home/witt/code/docling-core-404 || { echo "install #964 failed"; exit 1; }
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' in p.PdfTextCell.model_fields" || exit 1
echo "##### phase 1: PR venv with docling-core#964"
for corpus in bench-untagged bench-tagged-20; do
  for skip in 0 1; do
    echo "=== corpus=$corpus skip_shapes=$skip core=964 ==="
    AB_SKIP_SHAPES=$skip python3 -I $S/ab_rss.py $D/$corpus 3 main=$BASE pr443=$PR || exit 1
  done
done
uv pip install -q --python $PR docling-core==2.103.1 || { echo "install 2.103.1 failed"; exit 1; }
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' not in p.PdfTextCell.model_fields" || exit 1
echo "##### phase 2: PR venv with locked docling-core 2.103.1"
for corpus in bench-untagged bench-tagged-20; do
  for skip in 0 1; do
    echo "=== corpus=$corpus skip_shapes=$skip core=2.103.1 ==="
    AB_SKIP_SHAPES=$skip python3 -I $S/ab_rss.py $D/$corpus 3 main=$BASE pr443=$PR || exit 1
  done
done
echo "AB_DONE"
