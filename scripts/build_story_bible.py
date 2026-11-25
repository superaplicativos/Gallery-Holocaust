#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera data/story_bible.json a partir de data/victims_and_events.csv:
consolidar vítimas e eventos em uma bíblia de produção com mídias vinculadas
do catálogo (por linked_victims/linked_events/subject_type).
Uso: python scripts/build_story_bible.py"""
import csv, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "victims_and_events.csv")
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
OUT = os.path.join(ROOT, "data", "story_bible.json")

def main():
    people, events = {}, {}
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item = {
                "id": row["id"], "nome": row["nome"], "data": row["data"],
                "local": row["local"], "resumo": row["resumo"],
                "fontes": [s.strip() for s in row["fontes"].split(";") if s.strip()],
            }
            (people if row["tipo"] == "vitima" else events)[row["id"]] = item

    links = defaultdict(lambda: {"pessoas": [], "eventos": [], "media": []})
    for r in json_lines(CATALOG):
        entry = {"id": r["id"], "title": r.get("title"), "local_path": r.get("local_path"),
                 "year": r.get("year"), "subject_type": r.get("subject_type"),
                 "processing_stage": r.get("processing_stage")}
        for v in r.get("linked_victims", []):
            for pid, p in people.items():
                if v.lower() in p["nome"].lower() or p["nome"].lower() in v.lower():
                    links[pid]["pessoas"].append(p["nome"])
                    links[pid]["media"].append(entry)
        for ev in r.get("linked_events", []):
            for eid, e in events.items():
                if ev[:30].lower() in e["resumo"].lower() or e["nome"].lower()[:30] in ev.lower():
                    links[eid]["eventos"].append(e["nome"])
                    links[eid]["media"].append(entry)
        for pid in people:
            nm = people[pid]["nome"]
            if any(nm.lower() in (r.get("historical_notes", "") or "").lower() for r in [r] if False):
                pass
    bible = {
        "gerado_em": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "pessoas": people,
        "eventos": events,
        "midias_vinculadas": {k: v["media"] for k, v in links.items()},
        "resumo": {
            "pessoas": len(people), "eventos": len(events),
            "registros_catalogo": sum(1 for _ in json_lines(CATALOG)),
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(bible, f, ensure_ascii=False, indent=2)
    print(f"OK: {OUT} ({bible['resumo']['pessoas']} pessoas, {bible['resumo']['eventos']} eventos, "
          f"{bible['resumo']['registros_catalogo']} registros)")

def json_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

if __name__ == "__main__":
    main()
