#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta v5: fases separadas — listagem + metadados via api.php (janela boa),
downloads do CDN upload.wikimedia.org com backoff paciente em 429.
Uso:
  python3 fetch_commons_v5.py list            # fases A: títulos das categorias -> /tmp/v5_titles.json
  python3 fetch_commons_v5.py meta            # fase B: imageinfo em batch     -> /tmp/v5_meta.json
  python3 fetch_commons_v5.py download        # fase C: downloads + catálogo    -> media/raw/commons/
"""
import json, os, re, sys, time, hashlib, urllib.parse, urllib.request

ROOT = "/home/z/my-project/gallery_repo"
OUT_DIR = os.path.join(ROOT, "media", "raw", "commons")
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
TITLES_F = "/tmp/v5_titles.json"
META_F = "/tmp/v5_meta.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "GalleryHolocaustArchiveBot/2.0 (educational/memorial documentary archive; contact: superaplicativos)"}
os.makedirs(OUT_DIR, exist_ok=True)

CATEGORIES = [
    ("Sonderkommando photographs", "Oświęcim, Polônia", False, "Revolta do Sonderkommando (7 out 1944)"),
    ("Katarzyna Kwoka", "Oświęcim, Polônia", False, ""),
    ("Auschwitz Album", "Birkenau, Polônia", False, "Chegada de judeus húngaros a Birkenau (maio 1944)"),
    ("Auschwitz concentration camp", "Oświęcim, Polônia", False, ""),
    ("Warsaw Ghetto", "Varsóvia, Polônia", False, "Levantamento do Gueto de Varsóvia (1943)"),
    ("Stroop Report", "Varsóvia, Polônia", False, "Levantamento do Gueto de Varsóvia (1943)"),
    ("Treblinka extermination camp", "Treblinka, Polônia", False, ""),
    ("Sobibor extermination camp", "Sobibór, Polônia", False, ""),
    ("Majdanek concentration camp", "Lublin, Polônia", False, ""),
    ("Bergen-Belsen concentration camp", "Bergen-Belsen, Alemanha", False, "Liberação dos campos (1945)"),
    ("Buchenwald concentration camp", "Weimar, Alemanha", False, "Liberação dos campos (1945)"),
    ("Dachau concentration camp", "Dachau, Alemanha", False, "Liberação dos campos (1945)"),
    ("Mauthausen concentration camp", "Mauthausen, Áustria", False, ""),
    ("Theresienstadt", "Terezín, Tchéquia", False, ""),
    ("Kristallnacht", "Alemanha", False, "Noite dos Cristais (1938)"),
    ("Holocaust survivors", "Europa", False, "Liberação dos campos (1945)"),
    ("Deportation of Jews", "Europa", False, "Deportações para os campos (1941-1945)"),
    ("Jewish children in the Holocaust", "Europa", False, ""),
    ("Holocaust memorials", "Europa", True, "Memoriais do Holocausto (pós-guerra)"),
]
PER_CAT = 40
MAX_TOTAL = 220

def get(url, timeout=45, tries=6):
    for i in range(tries):
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            code = getattr(e, "code", None)
            if code in (403, 429):
                wait = 40 + i * 45          # 40, 85, 130, 175, 220
                print(f"    [429/403] aguardando {wait}s...", flush=True)
                time.sleep(wait)
            else:
                time.sleep(3 + i * 3)
    return None

def api_params(params, tries=6):
    params = dict(params); params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    data = get(url, tries=tries)
    return json.loads(data) if data else {}

def phase_list():
    all_t = {}
    for cat, loc, modern_ok, event in CATEGORIES:
        titles, cont = [], None
        while len(titles) < PER_CAT:
            p = {"action": "query", "list": "categorymembers", "cmtitle": f"Category:{cat}",
                 "cmnamespace": "6", "cmlimit": "200"}
            if cont: p["cmcontinue"] = cont
            d = api_params(p)
            for m in d.get("query", {}).get("categorymembers", []):
                t = m.get("title", "")
                if re.search(r"\.(jpg|jpeg|png|tif|tiff)$", t, re.I):
                    titles.append(t)
            cont = d.get("continue", {}).get("cmcontinue")
            if not cont: break
        all_t[cat] = titles[:PER_CAT]
        print(f"[{cat}] {len(all_t[cat])}", flush=True)
        time.sleep(2.5)
    json.dump(all_t, open(TITLES_F, "w"), ensure_ascii=False)
    print("OK titles ->", TITLES_F)

def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).replace("&amp;", "&").strip()

def phase_meta():
    all_t = json.load(open(TITLES_F))
    titles = [t for ts in all_t.values() for t in ts]
    titles = list(dict.fromkeys(titles))
    meta = {}
    for i in range(0, len(titles), 20):
        batch = "|".join(titles[i:i + 20])
        d = api_params({"action": "query", "titles": batch, "prop": "imageinfo",
                        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1600",
                        "iiextmetadatafilter": "DateTimeOriginal|ImageDescription|LicenseShortName|Artist|LicenseUrl"})
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if p.get("title") and ii:
                ii["_ext"] = {k: strip_html((v or {}).get("value", ""))
                              for k, v in ((ii.get("extmetadata") or {}).items())}
                meta[p["title"]] = ii
        print(f"    meta {min(i+20, len(titles))}/{len(titles)}", flush=True)
        time.sleep(3)
    json.dump(meta, open(META_F, "w"), ensure_ascii=False)
    print("OK meta ->", META_F)

def year_of(ii, modern_ok):
    raw = (ii.get("_ext") or {}).get("DateTimeOriginal", "")
    m = re.search(r"(1[5-9]\d\d|20[0-4]\d)", raw)
    y = m.group(1) if m else "unknown"
    if y != "unknown" and int(y) > 1965 and not modern_ok:
        return None
    return y

def license_status(name):
    n = (name or "").lower()
    if "cc0" in n: return "cc0"
    if "public domain" in n or n.startswith("pd"): return "public_domain"
    if "by-sa" in n: return "cc_by_sa"
    if "by " in n or n.startswith("cc by"): return "cc_by"
    return "license_review_needed"

def subject_type(text):
    t = (text or "").lower()
    rules = [
        (("portrait", "rosto", "face", "kwoka", "retrato"), "victim_portrait"),
        (("cremator", "kremator", "gas chamber", "gaskammer"), "camp_site"),
        (("arbeit macht frei", "gate", "tor "), "camp_site"),
        (("barracks", "hut ", "block", "baracke", "barraca"), "camp_site"),
        (("ruins", "ruína", "rubble", "destroyed"), "camp_site"),
        (("ramp", "selection", "seleção", "arrival"), "selection"),
        (("deport", "wagon", "train", "transport", "vagão"), "deportation"),
        (("liberation", "libertação", "liberated"), "liberation"),
        (("survivor", "sobrevivente"), "liberation"),
        (("memorial", "monument", "memória"), "memorial"),
        (("map", "karte", "plan "), "map"),
        (("document", "telegra", "list ", "record", "regist"), "document"),
        (("children", "kinder", "criança"), "victims_group"),
        (("corpse", "bodies", "graves", "burial", "cadáver"), "evidence_atrocity"),
        (("ghetto", "gueto"), "ghetto"),
        (("wall", "fence", "wire", "cerca", "arame"), "camp_site"),
    ]
    for kws, st in rules:
        if any(k in t for k in kws): return st
    return "archive_photo"

def base_tags(st, loc):
    tags = ["arquivo"]
    m = {"victim_portrait": "retrato", "camp_site": "campo", "selection": "rampa-seleção",
         "deportation": "deportação", "liberation": "liberação", "memorial": "memorial",
         "map": "mapa", "document": "documento", "victims_group": "vítimas",
         "evidence_atrocity": "evidência", "ghetto": "gueto", "archive_photo": "histórica"}
    tags.append(m.get(st, "histórica"))
    if loc: tags.append(loc.split(",")[0].strip().lower())
    return tags

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

def thumb_url(title, width=1600):
    name = title.replace("File:", "").replace(" ", "_")
    q = urllib.parse.quote(name)
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"

def dl(url, path, tries=4):
    if os.path.exists(path) and os.path.getsize(path) > 8000: return True
    for i in range(tries):
        data = get(url, timeout=120, tries=2)
        if data and len(data) > 8000:
            with open(path, "wb") as w: w.write(data)
            time.sleep(2.0)
            return True
        time.sleep(30)
    return False

def phase_download():
    all_t = json.load(open(TITLES_F))
    meta = json.load(open(META_F))
    recs = existing_records()
    counter = [max([int(r["id"].split("_PH_")[1]) for r in recs.values()
                    if str(r.get("id", "")).startswith("COMMONS_PH_")] or [0]) + 1]
    added = fail = 0
    for cat, loc, modern_ok, event in CATEGORIES:
        for t in all_t.get(cat, []):
            if counter[0] > MAX_TOTAL: break
            ii = meta.get(t)
            if not ii: continue
            mime = ii.get("mime", "")
            if mime not in ("image/jpeg", "image/png"): continue
            ext = ii.get("_ext", {})
            y = year_of(ii, modern_ok)
            if y is None: continue
            src_url = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_"))
            if src_url in recs: continue
            fname_raw = t.replace("File:", "")
            desc = (ext.get("ImageDescription") or "")[:220]
            artist = (ext.get("Artist") or "desconhecido")[:120]
            lic_name = ext.get("LicenseShortName") or "desconhecida"
            fn = f"COMMONS_PH_{counter[0]:06d}{'.png' if mime == 'image/png' else '.jpg'}"
            path = os.path.join(OUT_DIR, fn)
            ok = dl(ii.get("thumburl") or ii.get("url"), path) or dl(thumb_url(t), path)
            if not ok:
                fail += 1
                print(f"    FAIL {t[:60]}", flush=True)
                continue
            counter[0] += 1
            full = f"{fname_raw} {desc}".lower()
            st = subject_type(full)
            linked_v = []
            if "kwoka" in full: linked_v.append("Katarzyna Kwoka")
            if "müller" in full or "mueller" in full or "muller" in full: linked_v.append("Filip Müller")
            rec = {
                "id": fn.rsplit(".", 1)[0],
                "title": desc if desc and len(desc) > 12 else fname_raw.rsplit(".", 1)[0].replace("_", " "),
                "source_archive": "Wikimedia Commons",
                "source_url": src_url,
                "source_file_title": t,
                "license_status": license_status(lic_name),
                "license_name": lic_name,
                "license_url": ext.get("LicenseUrl") or None,
                "year": y, "location": loc, "subject_type": st,
                "linked_victims": linked_v,
                "linked_events": [event] if event else [],
                "processing_stage": "raw_original",
                "local_path": f"media/raw/commons/{fn}",
                "historical_notes": f"Foto de arquivo histórica (Commons). Autor: {artist}. Título original: {fname_raw}",
                "visual_tags": base_tags(st, loc),
                "width": ii.get("width"), "height": ii.get("height"),
                "color_mode": "bw_or_sepiatone",
            }
            recs[src_url] = rec
            with open(CATALOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
        if counter[0] > MAX_TOTAL: break
    print(f"\nOK download: +{added} novas | falhas: {fail} | catálogo: {len(recs)}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list": phase_list()
    elif cmd == "meta": phase_meta()
    elif cmd == "download": phase_download()
    else: print("uso: list | meta | download")
