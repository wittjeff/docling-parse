#!/bin/bash
# A/B after the clip box cache: upstream main (c2b39af) vs PR #443 with the cache, both Python 3.12.
# Phase B first (docling-core#964 is installed by the test step): tagged corpus, Python builds a BoundingBox per clipped cell.
# Phase A: locked docling-core 2.103.1, all four configurations; 7 repeats where the cost showed.
S=/tmp/claude-1000/-home-witt-code-docling/18f36680-f38e-4a68-a312-d9cdae94a438/scratchpad/mypy443
BASE=/home/witt/code/docling-parse-404-base/.venv/bin/python
PR=/home/witt/code/docling-parse-404/.venv/bin/python
D=/home/witt/Downloads/337-followups
set -o pipefail
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' in p.PdfTextCell.model_fields" || { echo "phase B needs #964 installed"; exit 1; }
echo "##### phase B: PR venv with docling-core#964 (cached build)"
for skip in 1 0; do
  echo "=== corpus=bench-tagged-20 skip_shapes=$skip core=964 ==="
  AB_SKIP_SHAPES=$skip python3 -I $S/ab_rss.py $D/bench-tagged-20 3 main=$BASE pr443=$PR || exit 1
done
uv pip install -q --python $PR docling-core==2.103.1 || { echo "install 2.103.1 failed"; exit 1; }
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' not in p.PdfTextCell.model_fields" || exit 1
echo "##### phase A: PR venv with locked docling-core 2.103.1 (cached build)"
echo "=== corpus=bench-tagged-20 skip_shapes=1 core=2.103.1 ==="
AB_SKIP_SHAPES=1 python3 -I $S/ab_rss.py $D/bench-tagged-20 7 main=$BASE pr443=$PR || exit 1
echo "=== corpus=bench-tagged-20 skip_shapes=0 core=2.103.1 ==="
AB_SKIP_SHAPES=0 python3 -I $S/ab_rss.py $D/bench-tagged-20 3 main=$BASE pr443=$PR || exit 1
for skip in 1 0; do
  echo "=== corpus=bench-untagged skip_shapes=$skip core=2.103.1 ==="
  AB_SKIP_SHAPES=$skip python3 -I $S/ab_rss.py $D/bench-untagged 3 main=$BASE pr443=$PR || exit 1
done
echo "AB2_DONE"
