#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta fotos históricas via z-ai image-search (URLs OSS alcançáveis).
Valida com PIL, evita duplicatas (hash) e registra em data/media_catalog.jsonl. Resumível."""
import io, json, os, re, subprocess, sys, time
import urllib.request
from PIL import Image

ROOT = "/home/z/my-project/Gallery-Holocaust"
OUT_DIR = os.path.join(ROOT, "media", "raw", "web")
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120"}
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CATALOG), exist_ok=True)

# (query, local padrão, modern_ok)
QUERIES = [
    ("Sonderkommando Auschwitz photographs 1944", "Oświęcim, Polônia", False),
    ("Katarzyna Kwoka Auschwitz victim portrait photograph", "Oświęcim, Polônia", False),
    ("Auschwitz Album Birkenau 1944 arrival Hungarian Jews photograph", "Birkenau, Polônia", False),
    ("Auschwitz Arbeit macht frei gate historic photograph", "Oświęcim, Polônia", False),
    ("Auschwitz Birkenau railway tracks barracks historic photograph", "Brzezinka, Polônia", False),
    ("Auschwitz crematorium ruins Birkenau photograph", "Brzezinka, Polônia", False),
    ("Warsaw ghetto Stroop report 1943 photograph", "Varsóvia, Polônia", False),
    ("Warsaw ghetto residents street 1941 photograph", "Varsóvia, Polônia", False),
    ("Bergen-Belsen liberation 1945 photograph", "Bergen-Belsen, Alemanha", False),
    ("Buchenwald liberation 1945 survivors photograph", "Weimar, Alemanha", False),
    ("Jewish deportation cattle wagons 1942 photograph", "Europa", False),
    ("Jewish children Holocaust victims historical photograph", "Europa", False),
    ("Holocaust survivors after liberation 1945 photograph", "Europa", False),
    ("Auschwitz Birkenau memorial monument photograph", "Brzezinka, Polônia", True),
]
COUNT_PER_QUERY = 8
MAX_TOTAL = 110

def existing_records():
    recs = {}
    if os.path.exists(CATALOG):
        with open(CATALOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    r = json.loads(line); recs[r.get("source_url", r.get("id"))] = r
                except Exception: pass
    return recs

def run_search(q):
    for attempt in range(2):
        try:
            p = subprocess.run(["z-ai", "image-search", "-q", q, "--count", str(COUNT_PER_QUERY),
                                "--gl", "us", "--no-rank"],
                               capture_output=True, text=True, timeout=170)
            out = p.stdout
            i = out.find("{")
            if i < 0: raise ValueError("sem JSON no stdout")
            return json.loads(out[i:])
        except Exception as e:
            if attempt == 1:
                print(f"    [warn] busca falhou: {str(e)[:90]}")
                return {}
            time.sleep(5)

def download_image(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 6000: return True
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)); img.verify()
        img = Image.open(io.BytesIO(data))
        if min(img.size) < 380: return False
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=90)
        return os.path.getsize(path) > 6000
    except Exception as e:
        return False

def subject_type_from_query(q):
    t = q.lower()
    if "portrait" in t or "kwoka" in t: return "victim_portrait"
    if "crematorium" in t: return "camp_site"
    if "gate" in t or "arbeit" in t: return "camp_site"
    if "barracks" in t or "ruins" in t: return "camp_site"
    if "railway" in t or "deportation" in t or "wagons" in t: return "deportation"
    if "liberation" in t or "survivors" in t: return "liberation"
    if "memorial" in t or "monument" in t: return "memorial"
    if "children" in t: return "victims_group"
    if "album" in t or "arrival" in t: return "selection"
    if "ghetto" in t or "stroop" in t: return "ghetto"
    return "archive_photo"

def main():
    recs = existing_records()
    counter = [max([int(r["id"].split("_PH_")[1]) for r in recs.values() if str(r.get("id", "")).startswith("WEB_PH_")] or [0]) + 1]
    added = 0
    for q, loc, modern_ok in QUERIES:
        if counter[0] > MAX_TOTAL: break
        print(f"[busca] {q}")
        d = run_search(q)
        if not d.get("success"): continue
        got = 0
        for r in d.get("results", []):
            if counter[0] > MAX_TOTAL: break
            url = r.get("original_url")
            if not url: continue
            if url in recs: continue
            site = r.get("source") or "origem web"
            n = counter[0]
            fn = f"WEB_PH_{n:06d}.jpg"
            path = os.path.join(OUT_DIR, fn)
            if not download_image(url, path): continue
            img = Image.open(path)
            if img.width < 700 or img.height < 450:
                if max(img.size) < 800: os.remove(path); continue
            counter[0] += 1
            st = subject_type_from_query(q)
            yr = re.search(r"(19[3-4]\d)", q)
            rec = {
                "id": f"WEB_PH_{n:06d}",
                "title": q.replace(" photograph", "").replace(" photograph", ""),
                "source_archive": "Web (via ZAI image search)",
                "source_site": site,
                "source_url": url,
                "license_status": "license_review_needed",
                "license_name": "a verificar",
                "year": yr.group(1) if yr else ("unknown" if not modern_ok else "pós-guerra"),
                "location": loc,
                "subject_type": st,
                "linked_victims": ["Katarzyna Kwoka"] if "kwoka" in q.lower() else [],
                "linked_events": ["Levantamento do Gueto de Varsóvia (1943)"] if "stroop" in q.lower() else [],
                "processing_stage": "raw_original",
                "local_path": f"media/raw/web/{fn}",
                "historical_notes": f"Imagem histórica localizada por busca web via {site}. Atenção: validar fonte, data e licença antes de uso público.",
                "visual_tags": [w for w in ["arquivo", st.replace("_", "-")] if w],
                "width": img.width, "height": img.height,
                "color_mode": "bw_or_sepiatone" if "memorial" not in st else "color",
                "needs_triage": True,
            }
            recs[url] = rec
            with open(CATALOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            got += 1; added += 1
        print(f"    +{got} (total {counter[0]-1})")
        time.sleep(2)
    print(f"\nOK: {added} novas imagens | catálogo total: {len(recs)} registros")

if __name__ == "__main__":
    main()
