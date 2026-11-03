"""Dump word and line cells of the regression page selection as JSONL.

Run from a docling-parse worktree with PYTHONPATH set to it, so that its
docling_parse package and tests.constants are the ones imported:
    cd $W && PYTHONPATH=$W python dump_cells.py OUT.jsonl [--limit N] [--jobs J]
Record: {"file", "page", "words": [[text, x0, y0, x1, y1], ...], "lines": [...],
         "clip_words": <words carrying a clip box>}  (bottom-left origin, 3 dp)
"""
import argparse
import glob
import json
import os
import sys
from multiprocessing import Pool

from docling_core.types.doc.base import CoordOrigin
from docling_core.types.doc.page import PdfPageBoundaryType

from docling_parse.pdf_parser import DecodeConfig, DoclingPdfParser
from tests.constants import PARSER_PAGE_RESTRICTIONS


def cell_rec(cell):
    r = cell.rect
    xs = (r.r_x0, r.r_x1, r.r_x2, r.r_x3)
    ys = (r.r_y0, r.r_y1, r.r_y2, r.r_y3)
    assert r.coord_origin == CoordOrigin.BOTTOMLEFT, r.coord_origin
    return [cell.text, round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]


def dump_doc(path):
    name = os.path.basename(path)
    out = []
    parser = DoclingPdfParser(loglevel="fatal")
    try:
        doc = parser.load(
            path_or_stream=path,
            boundary_type=PdfPageBoundaryType.CROP_BOX,
            lazy=True,
            decode_config=DecodeConfig(keep_glyphs=True, keep_qpdf_warnings=False, do_sanitization=True),
        )
    except Exception as exc:  # noqa: BLE001
        return [{"file": name, "page": 0, "error": f"load: {exc}"}]
    n = doc.number_of_pages()
    requested = PARSER_PAGE_RESTRICTIONS.get(name)
    pages = list(range(1, n + 1)) if requested is None else sorted(p for p in requested if 1 <= p <= n)
    for pno in pages:
        try:
            page = doc.get_page(pno)
            words = [cell_rec(c) for c in page.word_cells]
            lines = [cell_rec(c) for c in page.textline_cells]
            clip_words = sum(1 for c in page.word_cells if getattr(c, "clip_bbox", None) is not None)
            out.append({"file": name, "page": pno, "words": words, "lines": lines, "clip_words": clip_words})
        except Exception as exc:  # noqa: BLE001
            out.append({"file": name, "page": pno, "error": str(exc)})
        finally:
            doc.unload_pages(page_range=(pno, pno + 1))
    doc.unload()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    docs = sorted(glob.glob("tests/data/regression/*.pdf"))
    if a.only:
        docs = [d for d in docs if os.path.basename(d) in set(a.only)]
    if a.limit:
        docs = docs[: a.limit]
    n_pages = 0
    with Pool(a.jobs) as pool, open(a.out, "w") as fw:
        for i, recs in enumerate(pool.imap_unordered(dump_doc, docs, chunksize=1), 1):
            for r in recs:
                fw.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_pages += sum(1 for r in recs if "error" not in r)
            if i % 25 == 0:
                print(f"{i}/{len(docs)} docs, {n_pages} pages", file=sys.stderr, flush=True)
    print(f"done: {len(docs)} docs, {n_pages} pages -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
