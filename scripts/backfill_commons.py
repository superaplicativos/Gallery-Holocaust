#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill: completa metadados (ano, licença, descrição) dos registros COMMONS_PH
marcados metadata_pending=true, consultando a API da Wikipédia EN (que resolve
arquivos do Commons). Rodar novamente quando o rate limit do WMF liberar.
Uso: python scripts/backfill_commons.py"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
EN_API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "GalleryHolocaustArchiveBot/1.0 (educational/memorial documentary archive; contact: superaplicativos)"}

def api(params, tries=3):
    params = dict(params); params["format"] = "json"
    url = EN_API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            wait = 25 if getattr(e, "code", None) in (403, 429) else 3 + i * 3
            if i == tries - 1: return {}
            time.sleep(wait)
    return {}

def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).replace("&amp;", "&").strip()

def license_status(name):
    n = (name or "").lower()
    if "cc0" in n: return "cc0"
    if "public domain" in n or n.startswith("pd"): return "public_domain"
    if "by-sa" in n: return "cc_by_sa"
    if "by " in n or n.startswith("cc by"): return "cc_by"
    return "license_review_needed"

def main():
    recs = []
    with open(CATALOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    pending = [r for r in recs if r.get("metadata_pending") and r.get("source_file_title")]
    print(f"pendentes: {len(pending)}")
    if not pending:
        return 0
    updated = 0
    for gi in range(0, len(pending), 20):
        batch = pending[gi:gi + 20]
        titles = [r["source_file_title"] for r in batch]
        d = api({"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
                 "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1600",
                 "iiextmetadatafilter": "DateTimeOriginal|ImageDescription|LicenseShortName|Artist|LicenseUrl"})
        pages = {p.get("title"): p for p in d.get("query", {}).get("pages", {}).values()}
        for r in batch:
            p = pages.get(r.get("source_file_title"))
            if not p: continue
            ii = (p.get("imageinfo") or [{}])[0]
            ext = ii.get("extmetadata", {}) or {}
            raw_year = strip_html(ext.get("DateTimeOriginal", {}).get("value", ""))
            m = re.search(r"(1[5-9]\d\d|20[0-4]\d)", raw_year)
            y = m.group(1) if m else r.get("year", "unknown")
            if y != "unknown" and int(y) > 1965 and r.get("subject_type") != "memorial":
                r["historical_notes"] = (r.get("historical_notes", "") + " | Excluído por data moderna (" + y + ").").strip()
                r["needs_triage"] = True
            lic = strip_html(ext.get("LicenseShortName", {}).get("value", "")) or "desconhecida"
            r["license_name"] = lic
            r["license_status"] = license_status(lic)
            r["license_url"] = strip_html(ext.get("LicenseUrl", {}).get("value", "")) or None
            if y != "unknown": r["year"] = y
            desc = strip_html(ext.get("ImageDescription", {}).get("value", ""))[:220]
            if desc and len(desc) > 12: r["title"] = desc
            artist = strip_html(ext.get("Artist", {}).get("value", ""))[:120]
            if artist: r["historical_notes"] = f"Foto de arquivo histórica (Commons). Autor: {artist}. Título original: {r.get('source_file_title','').replace('File:','')}"
            r["width"] = ii.get("width", r.get("width"))
            r["height"] = ii.get("height", r.get("height"))
            r["metadata_pending"] = False
            updated += 1
        time.sleep(1.0)
    with open(CATALOG, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"OK: {updated} registros atualizados")

if __name__ == "__main__":
    main()
