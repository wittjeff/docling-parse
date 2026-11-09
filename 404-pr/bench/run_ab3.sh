#!/bin/bash
# Upper bound re-measured: PR venv with docling-core#964 (Python builds a BoundingBox per clipped cell), tagged corpus, shapes skipped, 7 passes.
S=/tmp/claude-1000/-home-witt-code-docling/18f36680-f38e-4a68-a312-d9cdae94a438/scratchpad/mypy443
BASE=/home/witt/code/docling-parse-404-base/.venv/bin/python
PR=/home/witt/code/docling-parse-404/.venv/bin/python
D=/home/witt/Downloads/337-followups
set -o pipefail
uv pip install -q --python $PR /home/witt/code/docling-core-404 || exit 1
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' in p.PdfTextCell.model_fields" || exit 1
echo "=== clipped cells per level, bench-tagged-20, shapes skipped (PR build, #964) ==="
$PR -I - "$D/bench-tagged-20" <<'PY'
import sys, glob
from docling_parse.pdf_parser import DoclingPdfParser, ContentConfig, ContentLevel
parser = DoclingPdfParser(loglevel="fatal")
counts = {"char": [0, 0], "word": [0, 0], "line": [0, 0]}
for f in sorted(glob.glob(sys.argv[1] + "/*.pdf")):
    try: doc = parser.load(path_or_stream=f, content_config=ContentConfig(shapes_content_level=ContentLevel.SKIP))
    except Exception: continue
    for _, page in doc.iterate_pages():
        for name, cells in (("char", page.char_cells), ("word", page.word_cells), ("line", page.textline_cells)):
            counts[name][0] += len(cells)
            counts[name][1] += sum(1 for c in cells if c.clip_bbox is not None)
    doc.unload()
for k, (n, c) in counts.items(): print(f"{k}: {c} of {n} cells carry a clip box")
print("total clip boxes:", sum(c for _, c in counts.values()))
PY
echo "=== corpus=bench-tagged-20 skip_shapes=1 core=964 (7 passes, cached build) ==="
AB_SKIP_SHAPES=1 python3 -I $S/ab_rss.py $D/bench-tagged-20 7 main=$BASE pr443=$PR || exit 1
uv pip install -q --python $PR docling-core==2.103.1 || exit 1
$PR -c "import docling_core.types.doc.page as p; assert 'clip_bbox' not in p.PdfTextCell.model_fields" && echo "venv back on 2.103.1"
echo "AB3_DONE"
