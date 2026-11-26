#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coloriza fotos históricas selecionadas com IA (z-ai image-edit) e registra no catálogo
como processing_stage=ai_colorized com derived_from e prompt de colorização documental.
Resumível: pula registros já colorizados."""
import json, os, subprocess, sys

ROOT = "/home/z/my-project/gallery_repo"
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
OUT = os.path.join(ROOT, "media", "ai_colorized")
os.makedirs(OUT, exist_ok=True)

PROMPT = ("Colorize this historical black-and-white documentary photograph with period-accurate, "
          "realistic colors: muted earth tones, weathered concrete and brick, overcast sky, natural "
          "skin tones preserved exactly as in the original. Keep the original composition, every "
          "person, object, building and detail unchanged. Documentary colorization only: do not add, "
          "remove or invent any element.")

BUCKETS = ["camp_site", "deportation", "selection", "memorial", "ghetto", "liberation", "archive_photo"]
PER_BUCKET = 5
TARGET_SIZE = "1344x768"

def load_recs():
    return [json.loads(l) for l in open(CATALOG, encoding="utf-8") if l.strip()]

def save_recs(recs):
    with open(CATALOG, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def colorize(src, dst):
    # reduz imagem para payload leve
    import io
    from PIL import Image
    tmp = "/tmp/col_src.jpg"
    img = Image.open(src).convert("RGB")
    img.thumbnail((1344, 1344), Image.LANCZOS)
    img.save(tmp, "JPEG", quality=88)
    p = subprocess.run(["node", "/home/z/my-project/scripts/colorize_one.mjs", tmp, dst, TARGET_SIZE],
                       capture_output=True, text=True, timeout=240, cwd="/home/z/my-project")
    tail = (p.stderr or "").strip().splitlines()[-1] if (p.stderr or "").strip() else ""
    if p.returncode != 0:
        print(f"    [node] {tail[:150]}")
    return os.path.exists(dst) and os.path.getsize(dst) > 20000

def main():
    recs = load_recs()
    colored_ids = {r.get("derived_from") for r in recs if r.get("processing_stage") == "ai_colorized"}
    # candidatas: raw_original locais, buckets variados, boa resolução
    used_srcs = {r.get("derived_from") for r in recs if r.get("processing_stage") == "ai_colorized"}
    candidates = {}
    for r in recs:
        if r.get("processing_stage") != "raw_original": continue
        lp = os.path.join(ROOT, r.get("local_path", ""))
        if not lp or not os.path.exists(lp): continue
        if (r.get("width") or 0) < 750: continue
        st = r.get("subject_type")
        if st in ("victim_portrait", "evidence_atrocity", "victims_group"): continue  # proteger dignidade
        if r["id"] in used_srcs: continue
        candidates.setdefault(st, []).append(r)
    max_new = 16
    added = 0
    counter = max([int(r["id"].split("_PH_")[1]) for r in recs if r["id"].startswith("AIGEN_PH_")] or [0]) + 1
    for st in BUCKETS:
        if added >= max_new: break
        cands = candidates.get(st, [])
        if not cands: continue
        src_rec = cands[0]
        src = os.path.join(ROOT, src_rec["local_path"])
        fn = f"AIGEN_PH_{counter:06d}_color.jpg"
        dst = os.path.join(OUT, fn)
        print(f"[colorize] {src_rec['id']} ({st}) -> {fn}")
        if not colorize(src, dst):
            print("    falhou, pulando")
            continue
        counter += 1
        rec = {
            "id": f"AIGEN_PH_{counter-1:06d}",
            "title": src_rec.get("title", "") + " (colorização IA)",
            "source_archive": "AI colorization (Gallery-Holocaust pipeline)",
            "source_url": src_rec.get("source_url"),
            "license_status": src_rec.get("license_status", "license_review_needed"),
            "year": src_rec.get("year"),
            "location": src_rec.get("location"),
            "subject_type": st,
            "linked_victims": src_rec.get("linked_victims", []),
            "linked_events": src_rec.get("linked_events", []),
            "processing_stage": "ai_colorized",
            "local_path": f"media/ai_colorized/{fn}",
            "derived_from": src_rec["id"],
            "tool": "z-ai image-edit (GLM image editing)",
            "colorization_prompt": PROMPT,
            "historical_notes": "ATENÇÃO: imagem colorizada por IA. Cores são reconstrução aproximada, não registro histórico. Validar cores com referências históricas antes de uso público. Original preservado intacto em media/raw/.",
            "visual_tags": src_rec.get("visual_tags", []) + ["colorizado-ia"],
            "width": None, "height": None,
            "color_mode": "ai_colorized",
        }
        recs.append(rec)
        candidates[st].pop(0)
        added += 1
        save_recs(recs)
    print(f"\nOK: {added} colorizações | total catálogo: {len(recs)}")

if __name__ == "__main__":
    main()
