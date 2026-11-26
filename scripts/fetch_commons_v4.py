#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta v4: listagem via PetScan (serviço externo, estável), metadados via EN api.php,
download via CDN upload.wikimedia.org (fallback Special:FilePath). Resumível."""
import json, os, re, sys, time, hashlib, urllib.parse, urllib.request

ROOT = "/home/z/my-project/gallery_repo"
OUT_DIR = os.path.join(ROOT, "media", "raw", "commons")
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
EN_API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "GalleryHolocaustArchiveBot/1.0 (educational/memorial documentary archive; contact: superaplicativos)"}
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CATALOG), exist_ok=True)

CATEGORIES = [
    ("Sonderkommando photographs", "Oświęcim, Polônia", False, "Revolta do Sonderkommando (7 out 1944)"),
    ("Katarzyna Kwoka", "Oświęcim, Polônia", False, ""),
    ("Auschwitz Album", "Birkenau, Polônia", False, "Chegada de judeus húngaros a Birkenau (maio 1944)"),
    ("Auschwitz concentration camp", "Oświęcim, Polônia", False, ""),
    ("Auschwitz II (Birkenau)", "Brzezinka, Polônia", False, ""),
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
PER_CAT = 55

def petscan_titles(cat):
    """Listagem via API nativa do Commons (categorymembers, ns=6) — substitui PetScan (bloqueado)."""
    titles, cont = [], None
    while len(titles) < PER_CAT:
        params = {"action": "query", "list": "categorymembers",
                  "cmtitle": f"Category:{cat}", "cmnamespace": "6",
                  "cmlimit": "200", "format": "json"}
        if cont: params["cmcontinue"] = cont
        d = json.loads(http_get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)))
        for m in d.get("query", {}).get("categorymembers", []):
            if m.get("title"): titles.append(m["title"])
        cont = d.get("continue", {}).get("cmcontinue")
        if not cont: break
    return titles[:PER_CAT]

def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).replace("&amp;", "&").strip()

def http_get(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def api_en(params, tries=4):
    params = dict(params); params["format"] = "json"
    url = EN_API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            return json.loads(http_get(url))
        except Exception as e:
            code = getattr(e, "code", None)
            wait = 25 if code in (403, 429) else 3 + i * 3
            if i == tries - 1:
                print(f"    [warn] en api falhou: {code or e}")
                return {}
            time.sleep(wait)
    return {}

def year_of(ext, modern_ok):
    raw = strip_html(ext.get("DateTimeOriginal", {}).get("value", ""))
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

def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 8000: return True
    for i in range(3):
        try:
            data = http_get(url, timeout=90)
            if len(data) < 8000: raise ValueError("pequeno demais")
            with open(path, "wb") as w: w.write(data)
            time.sleep(0.9)
            return True
        except Exception as e:
            code = getattr(e, "code", None)
            wait = 18 if code in (403, 429) else 1 + i * 2
            if i == 2: return False
            time.sleep(wait)
    return False

def download_fallback(title, path, width=1600):
    base = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(title.replace("File:", ""))
    if download(base + f"?width={width}", path): return True
    return download(base, path)  # original completo (caso thumb exceda tamanho)

def hash_thumb_url(title, width=1600):
    """URL da thumb derivada do hash MD5 do nome (não depende de API)."""
    name = title.replace("File:", "").replace(" ", "_")
    q = urllib.parse.quote(name)
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"

def meta_batch(titles):
    out = {}
    for gi in range(0, len(titles), 20):
        batch = "|".join(titles[gi:gi + 20])
        d = api_en({"action": "query", "titles": batch, "prop": "imageinfo",
                    "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1600",
                    "iiextmetadatafilter": "DateTimeOriginal|ImageDescription|LicenseShortName|Artist|LicenseUrl"})
        for p in d.get("query", {}).get("pages", {}).values():
            t = p.get("title", "")
            ii = (p.get("imageinfo") or [None])[0]
            if t and ii: out[t] = ii
        time.sleep(0.8)
    return out

def add_record(recs, counter, page_title, ii, cat, loc, modern_ok, event):
    ext = (ii.get("extmetadata", {}) or {}) if ii else {}
    fname_raw = page_title.replace("File:", "")
    if ii:
        y = year_of(ext, modern_ok)
        if y is None: return None
        mime = ii.get("mime", "")
        if mime not in ("image/jpeg", "image/png"): return None
        if ii.get("width", 0) < 700 or ii.get("height", 0) < 450: return None
    else:
        y = "unknown"
        mime = "image/png" if fname_raw.lower().endswith(".png") else "image/jpeg"
    pending = (ii is None) or (not ext.get("LicenseShortName", {}).get("value", ""))
    src_url = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(page_title.replace(" ", "_"))
    if src_url in recs: return None
    lic = strip_html(ext.get("LicenseShortName", {}).get("value", "")) or "desconhecida"
    desc = strip_html(ext.get("ImageDescription", {}).get("value", ""))[:220]
    artist = strip_html(ext.get("Artist", {}).get("value", ""))[:120] or "desconhecido"
    fname = fname_raw.replace("/", "_")
    n = counter[0]
    extf = ".png" if mime == "image/png" else ".jpg"
    fn = f"COMMONS_PH_{n:06d}{extf}"
    path = os.path.join(OUT_DIR, fn)
    url = (ii.get("thumburl") or ii.get("url")) if ii else None
    ok = False
    if url: ok = download(url, path)
    if not ok: ok = download_fallback(page_title, path)  # rota estável primeiro
    if not ok: ok = download(hash_thumb_url(page_title), path)
    if not ok: return None
    counter[0] += 1
    full = f"{fname_raw} {desc} {fname}".lower()
    st = subject_type(full)
    linked_v = []
    if "kwoka" in full: linked_v.append("Katarzyna Kwoka")
    if "müller" in full or "mueller" in full or "muller" in full: linked_v.append("Filip Müller")
    linked_e = [event] if event else []
    rec = {
        "id": f"COMMONS_PH_{n:06d}",
        "title": desc if desc and len(desc) > 12 else fname.rsplit(".", 1)[0].replace("_", " "),
        "source_archive": "Wikimedia Commons",
        "source_url": src_url,
        "source_file_title": page_title,
        "license_status": license_status(lic) if ii else "license_review_needed",
        "license_name": lic,
        "license_url": strip_html(ext.get("LicenseUrl", {}).get("value", "")) or None,
        "year": y,
        "location": loc,
        "subject_type": st,
        "linked_victims": linked_v,
        "linked_events": linked_e,
        "processing_stage": "raw_original",
        "local_path": f"media/raw/commons/{fn}",
        "historical_notes": f"Foto de arquivo histórica (Commons). Autor: {artist}. Título original: {fname}",
        "visual_tags": base_tags(st, loc),
        "width": ii.get("width") if ii else None, "height": ii.get("height") if ii else None,
        "color_mode": "bw_or_sepiatone",
        "metadata_pending": pending,
    }
    recs[src_url] = rec
    with open(CATALOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    recs = existing_records()
    counter = [max([int(r["id"].split("_PH_")[1]) for r in recs.values() if str(r.get("id", "")).startswith("COMMONS_PH_")] or [0]) + 1]
    added = 0
    MAX_TOTAL = 150
    for cat, loc, modern_ok, event in CATEGORIES:
        if only and cat not in only: continue
        if counter[0] >= MAX_TOTAL: break
        try:
            titles = petscan_titles(cat)
        except Exception as e:
            print(f"[{cat}] ERRO PetScan: {str(e)[:80]}")
            continue
        print(f"[{cat}] {len(titles)} títulos")
        if not titles: continue
        metas = meta_batch(titles) if not os.environ.get("SKIP_META") else {}
        got = 0
        for t in titles:
            if counter[0] >= MAX_TOTAL: break
            rec = add_record(recs, counter, t, metas.get(t), cat, loc, modern_ok, event)
            if rec: got += 1; added += 1
        print(f"    +{got} (total {counter[0]-1})")
        time.sleep(1.2)
    print(f"\nOK: {added} novas imagens | catálogo total: {len(recs)} registros")

if __name__ == "__main__":
    main()
