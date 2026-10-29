"""Before/after images of the regrouped pages: pypdfium2 render, changed cells boxed.

Left panel: cells only in the baseline dump (red). Right panel: cells only in the
patched dump (green). Words on top, lines below. Cropped to the changed region.
"""
import json
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

base_path, patched_path, corpus, out_dir = (Path(a) for a in sys.argv[1:5])
SCALE = 3.0
MARGIN = 18  # pt around the changed region
MAX_REGION_H = 260  # pt; taller regions are cut to the first changed rows
MIN_REGION_W = 260  # pt; keeps the panel labels readable
CLUSTER_GAP = 40  # pt; changes further apart than this get their own strip
STRIP_GAP = 6  # px; grey band between strips


def load(path):
    d = {}
    for line in path.open():
        r = json.loads(line)
        if "error" not in r:
            d[(r["file"], r["page"])] = r
    return d


a, b = load(base_path), load(patched_path)
keys = [k for k in sorted(set(a) & set(b)) if a[k]["words"] != b[k]["words"] or a[k]["lines"] != b[k]["lines"]]
font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
out_dir.mkdir(parents=True, exist_ok=True)
index = []
for name, pno in keys:
    ra, rb = a[(name, pno)], b[(name, pno)]
    diff = {}
    for kind in ("words", "lines"):
        sa = {tuple(c) for c in ra[kind]}
        sb = {tuple(c) for c in rb[kind]}
        diff[kind] = ([c for c in ra[kind] if tuple(c) not in sb], [c for c in rb[kind] if tuple(c) not in sa])
    pdf = pdfium.PdfDocument(str(corpus / name))
    page = pdf[pno - 1]
    w_pt, h_pt = page.get_size()
    full = page.render(scale=SCALE).to_pil().convert("RGB")
    boxes = [c for kind in diff.values() for side in kind for c in side]
    x0 = max(0, min(c[1] for c in boxes) - MARGIN)
    x1 = min(w_pt, max(c[3] for c in boxes) + MARGIN)
    if x1 - x0 < MIN_REGION_W:
        mid = (x0 + x1) / 2
        x0 = max(0, mid - MIN_REGION_W / 2)
        x1 = min(w_pt, x0 + MIN_REGION_W)
    # One strip per vertical group of changes, top of the page first.
    groups = []
    for c in sorted(boxes, key=lambda c: -c[4]):
        if groups and c[4] > groups[-1][0] - CLUSTER_GAP:
            groups[-1][0] = min(groups[-1][0], c[2])
        else:
            groups.append([c[2], c[4]])
    strips = []
    for bot, top in groups:
        top, bot = min(h_pt, top + MARGIN), max(0, bot - MARGIN)
        bot = max(bot, top - MAX_REGION_H)
        strips.append((int(x0 * SCALE), int((h_pt - top) * SCALE), int(x1 * SCALE), int((h_pt - bot) * SCALE)))

    def panel(kind, side, colours):
        # Alternating colours keep two adjacent new cells visibly apart.
        img = full.copy()
        drw = ImageDraw.Draw(img)
        for i, c in enumerate(diff[kind][side]):
            drw.rectangle(
                [c[1] * SCALE, (h_pt - c[4]) * SCALE, c[3] * SCALE, (h_pt - c[2]) * SCALE],
                outline=colours[i % len(colours)], width=3)
        parts = [img.crop(box) for box in strips]
        out = Image.new("RGB", (parts[0].width, sum(q.height for q in parts) + STRIP_GAP * (len(parts) - 1)), (200, 200, 200))
        y = 0
        for q in parts:
            out.paste(q, (0, y))
            y += q.height + STRIP_GAP
        return out

    rows = []
    for kind in ("words", "lines"):
        if diff[kind][0] or diff[kind][1]:
            rows.append((kind, panel(kind, 0, [(220, 30, 30)]), panel(kind, 1, [(20, 150, 40), (30, 90, 220)])))
    cw, chh = rows[0][1].size
    label_h, gap = 40, 12
    sheet = Image.new("RGB", (2 * cw + gap, len(rows) * (chh + label_h)), "white")
    drw = ImageDraw.Draw(sheet)
    for i, (kind, left, right) in enumerate(rows):
        y = i * (chh + label_h)
        drw.text((6, y + 6), f"{kind} before (7.22.1)", fill=(220, 30, 30), font=font)
        drw.text((cw + gap + 6, y + 6), f"{kind} after (prototype)", fill=(20, 120, 40), font=font)
        sheet.paste(left, (0, y + label_h))
        sheet.paste(right, (cw + gap, y + label_h))
    fname = f"{Path(name).stem}-p{pno}.png"
    if sheet.width > 2400:
        sheet = sheet.resize((2400, int(sheet.height * 2400 / sheet.width)), Image.LANCZOS)
    sheet.save(out_dir / fname, optimize=True)
    index.append({"file": name, "page": pno, "png": fname,
                  "words_before": [c[0] for c in diff["words"][0]], "words_after": [c[0] for c in diff["words"][1]],
                  "lines_before": [c[0] for c in diff["lines"][0]], "lines_after": [c[0] for c in diff["lines"][1]]})
    print(fname, sheet.size, len(diff["words"][0]), "->", len(diff["words"][1]), "words;",
          len(diff["lines"][0]), "->", len(diff["lines"][1]), "lines")
(out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
