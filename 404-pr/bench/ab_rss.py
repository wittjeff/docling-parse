"""Interleaved A/B of two docling-parse builds: single-threaded parse (char/word/line
cells materialised to Python), fresh process per pass, wall time and peak RSS.
usage: [AB_SKIP_SHAPES=1] python ab_rss.py <pdf_dir> <repeats> <label=venv_python>..."""
import subprocess, sys, statistics, pathlib
pdf_dir, repeats = sys.argv[1], int(sys.argv[2])
builds = dict(a.split("=", 1) for a in sys.argv[3:])
WORKER = r'''
import sys, time, glob, resource, os
from docling_parse.pdf_parser import DoclingPdfParser, ContentConfig, ContentLevel
parser = DoclingPdfParser(loglevel="fatal")
load_kwargs = {}
if os.environ.get("AB_SKIP_SHAPES") == "1":
    load_kwargs["content_config"] = ContentConfig(shapes_content_level=ContentLevel.SKIP)
files = sorted(glob.glob(sys.argv[1] + "/*.pdf"))
t0 = time.perf_counter(); pages = 0; words = 0; clipped = 0
for f in files:
    try: doc = parser.load(path_or_stream=f, **load_kwargs)
    except Exception: continue
    for page_no, page in doc.iterate_pages():
        pages += 1
        words += len(page.word_cells)
        clipped += sum(1 for c in page.word_cells if getattr(c, "clip_bbox", None) is not None)
    doc.unload()
dt = time.perf_counter() - t0
rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(dt, pages, words, clipped, rss_kib)
'''
results = {k: {"t": [], "rss": [], "info": None} for k in builds}
for r in range(repeats):
    order = list(builds) if r % 2 == 0 else list(reversed(list(builds)))
    for k in order:
        out = subprocess.run([builds[k], "-I", "-c", WORKER, pdf_dir], capture_output=True, text=True)
        if out.returncode != 0:
            print(f"run {r+1} {k}: FAILED\n{out.stderr[-2000:]}", flush=True); sys.exit(1)
        secs, pages, words, clipped, rss = out.stdout.split()[-5:]
        results[k]["t"].append(float(secs)); results[k]["rss"].append(int(rss) / 1024)
        results[k]["info"] = (pages, words, clipped)
        print(f"run {r+1} {k}: {float(secs):.2f} s, maxrss {int(rss)/1024:.0f} MiB, {pages} pages, {words} words, {clipped} clipped", flush=True)
print()
ref = list(results)[0]
for k, v in results.items():
    print(f"{k}: time min={min(v['t']):.2f} median={statistics.median(v['t']):.2f} max={max(v['t']):.2f} s; "
          f"maxrss min={min(v['rss']):.0f} median={statistics.median(v['rss']):.0f} MiB; {len(v['t'])} passes; pages/words/clipped={v['info']}")
for k in list(results)[1:]:
    print(f"{k} vs {ref}: time median ratio {statistics.median(results[k]['t'])/statistics.median(results[ref]['t']):.3f}, "
          f"maxrss median ratio {statistics.median(results[k]['rss'])/statistics.median(results[ref]['rss']):.3f}")
