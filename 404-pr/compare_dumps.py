"""Compare two cell dumps (base, patched): per-page classification and PR tables.

usage: compare_dumps.py BASE.jsonl PATCHED.jsonl [--examples N] [--md OUT.md]
"""
import argparse
import json
import re
from collections import OrderedDict, defaultdict


def load(path):
    d = OrderedDict()
    errs = {}
    for line in open(path):
        r = json.loads(line)
        k = (r["file"], r["page"])
        if "error" in r:
            errs[k] = r["error"]
        else:
            d[k] = r
    return d, errs


def page_text(rec):
    return "".join(c[0] for c in rec["words"]).replace(" ", "")


def natkey(k):
    return ([int(t) if t.isdigit() else t for t in re.split(r"(\d+)", k[0])], k[1])


ap = argparse.ArgumentParser()
ap.add_argument("base"); ap.add_argument("patched")
ap.add_argument("--examples", type=int, default=5)
ap.add_argument("--md", default=None)
a = ap.parse_args()
A, ea = load(a.base); B, eb = load(a.patched)
common = sorted(set(A) & set(B), key=natkey)
identical, regrouped, text_changed = [], [], []
for k in common:
    ra, rb = A[k], B[k]
    if ra["words"] == rb["words"] and ra["lines"] == rb["lines"]:
        identical.append(k)
    elif page_text(ra) == page_text(rb):
        regrouped.append(k)
    else:
        text_changed.append(k)
print(f"pages compared: {len(common)}  (base only: {len(set(A)-set(B))}, patched only: {len(set(B)-set(A))}, errors base/patched: {len(ea)}/{len(eb)})")
print(f"identical: {len(identical)}  regrouped: {len(regrouped)}  text changed: {len(text_changed)}")
docs_changed = sorted({k[0] for k in regrouped + text_changed})
print(f"documents with changes: {len(docs_changed)}")
clip_pages = sum(1 for k in common if B[k].get("clip_words", 0) > 0)
clip_words = sum(B[k].get("clip_words", 0) for k in common)
print(f"pages with >=1 word carrying a clip box: {clip_pages}; words with a clip box: {clip_words}")
if ea or eb:
    print("errors:", {k: v for k, v in list(ea.items())[:5]}, {k: v for k, v in list(eb.items())[:5]})

out = []
for k in regrouped + text_changed:
    ra, rb = A[k], B[k]
    wa = {tuple(c) for c in ra["words"]}; wb = {tuple(c) for c in rb["words"]}
    la = {tuple(c) for c in ra["lines"]}; lb = {tuple(c) for c in rb["lines"]}
    words_before = [c for c in ra["words"] if tuple(c) not in wb]
    words_after = [c for c in rb["words"] if tuple(c) not in wa]
    lines_before = [c for c in ra["lines"] if tuple(c) not in lb]
    lines_after = [c for c in rb["lines"] if tuple(c) not in la]
    out.append({"file": k[0], "page": k[1], "kind": "text changed" if k in text_changed else "regrouped",
                "words": (len(ra["words"]), len(rb["words"])), "lines": (len(ra["lines"]), len(rb["lines"])),
                "words_before": [c[0] for c in words_before], "words_after": [c[0] for c in words_after],
                "lines_before": [c[0] for c in lines_before], "lines_after": [c[0] for c in lines_after]})
    print(f"\n{k[0]} p{k[1]} [{out[-1]['kind']}] words {len(ra['words'])}->{len(rb['words'])} lines {len(ra['lines'])}->{len(rb['lines'])}")
    for label, before, after in (("words", words_before, words_after), ("lines", lines_before, lines_after)):
        if before or after:
            print(f"  {label} before: {[c[0] for c in before][:a.examples]}")
            print(f"  {label} after : {[c[0] for c in after][:a.examples]}")
if a.md:
    with open(a.md, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {a.md}")
