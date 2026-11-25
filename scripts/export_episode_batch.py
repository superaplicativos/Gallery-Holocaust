#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporta lote de produção de um episódio: cruza episodes/<ep>/scenes.json com
data/media_catalog.jsonl e gera episodes/<ep>/production_batch.json com:
- mídia candidata por cena (por visual_tags/subject_type/linked_events)
- caminhos locais absolutos para o renderer
Uso: python scripts/export_episode_batch.py episodes/ep01_filip_mueller"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def json_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def load_catalog():
    return list(json_lines(os.path.join(ROOT, "data", "media_catalog.jsonl")))

def score(rec, scene):
    """Pontuação de aderência registro x cena."""
    s = 0.0
    want = set(t.lower() for t in scene.get("visual_tags", []))
    have = set(t.lower() for t in rec.get("visual_tags", []))
    s += 2.0 * len(want & have)
    if rec.get("subject_type") in scene.get("subject_types", []): s += 3.0
    for ev in rec.get("linked_events", []):
        if any(ev[:25].lower() in c.lower() for c in scene.get("cues_text", [])):
            s += 2.0
    if rec.get("processing_stage") == "remote_reference": s -= 2.0
    if rec.get("license_status") in ("public_domain", "cc0", "cc_by", "cc_by_sa"): s += 1.0
    if rec.get("needs_triage"): s -= 0.5
    if rec.get("processing_stage") == "ai_colorized": s += 0.3  # preferir colorizado se disponível
    return s

def main():
    ep_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "episodes", "ep01_filip_mueller")
    scenes_path = os.path.join(ep_dir, "scenes.json")
    if not os.path.exists(scenes_path):
        print(f"ERRO: {scenes_path} não existe")
        return 2
    scenes = json.load(open(scenes_path, encoding="utf-8"))
    if isinstance(scenes, dict): scenes = scenes.get("scenes", [])
    catalog = load_catalog()
    batch = {"episodio": os.path.basename(ep_dir), "cenas": []}
    for sc in scenes:
        ranked = sorted(catalog, key=lambda r: -score(r, sc))
        top = [r for r in ranked if score(r, sc) > 0][:5]
        batch["cenas"].append({
            "scene_id": sc.get("scene_id"),
            "titulo": sc.get("titulo"),
            "duracao_s": sc.get("duracao_s"),
            "cues": sc.get("cue_ids", []),
            "media_sugerida": [
                {"id": r["id"], "path": r.get("local_path"), "title": r.get("title"),
                 "year": r.get("year"), "processing_stage": r.get("processing_stage"),
                 "colorizado": r.get("processing_stage") == "ai_colorized",
                 "score": round(score(r, sc), 2)}
                for r in top
            ],
        })
    out = os.path.join(ep_dir, "production_batch.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"OK: {out} ({len(batch['cenas'])} cenas)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
