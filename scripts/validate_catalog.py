#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida data/media_catalog.jsonl contra config/schema.json:
- JSON por linha, ids únicos, campos obrigatórios, enums válidos
- local_path existe no disco (exceto remote_reference)
- derived_from aponta para id existente
Uso: python scripts/validate_catalog.py"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
SCHEMA = os.path.join(ROOT, "config", "schema.json")

ID_RE = re.compile(r"^[A-Z]+_[A-Z]+_[0-9]{6}$")

def main():
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    required = schema["required"]
    enum_stage = schema["properties"]["processing_stage"]["enum"]
    enum_license = schema["properties"]["license_status"]["enum"]
    enum_subject = schema["properties"]["subject_type"]["enum"]
    errors, warnings = [], []
    ids = set()
    n = 0
    if not os.path.exists(CATALOG):
        print(f"ERRO: catálogo não existe: {CATALOG}")
        return 2
    for line_no, line in enumerate(open(CATALOG, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        n += 1
        try:
            r = json.loads(line)
        except Exception as e:
            errors.append(f"linha {line_no}: JSON inválido ({e})")
            continue
        rid = r.get("id", f"<sem id linha {line_no}>")
        for f in required:
            if r.get(f) in (None, "") and f != "local_path":
                errors.append(f"{rid}: campo obrigatório ausente: {f}")
        if not ID_RE.match(r.get("id", "")):
            errors.append(f"{rid}: id fora do padrão FONTE_TIPO_NUMERO")
        if r.get("id") in ids:
            errors.append(f"{rid}: id duplicado")
        ids.add(r.get("id"))
        if r.get("processing_stage") not in enum_stage:
            errors.append(f"{rid}: processing_stage inválido: {r.get('processing_stage')}")
        if r.get("license_status") not in enum_license:
            errors.append(f"{rid}: license_status inválido: {r.get('license_status')}")
        if r.get("subject_type") not in enum_subject:
            errors.append(f"{rid}: subject_type inválido: {r.get('subject_type')}")
        lp = r.get("local_path")
        if r.get("processing_stage") == "remote_reference":
            if lp: warnings.append(f"{rid}: remote_reference com local_path definido ({lp})")
        elif not lp:
            errors.append(f"{rid}: local_path ausente (não é remote_reference)")
        elif not os.path.exists(os.path.join(ROOT, lp)):
            errors.append(f"{rid}: local_path não existe no disco: {lp}")
        df = r.get("derived_from")
        if df and df not in ids:
            warnings.append(f"{rid}: derived_from ainda não registrado ({df}) — será resolvido no fim")
        if r.get("license_status") in ("license_review_needed", "institutional_archive_check") and not r.get("needs_triage") and r.get("processing_stage") == "raw_original":
            warnings.append(f"{rid}: licença em review mas sem needs_triage")
    # resolve derived_from em segunda passada
    for line in open(CATALOG, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        df = r.get("derived_from")
        if df and df not in ids:
            warnings = [w for w in warnings if not w.startswith(r.get("id", "??"))]
            errors.append(f"{r.get('id')}: derived_from aponta para id inexistente: {df}")
    print(f"Registros: {n}")
    print(f"Erros: {len(errors)}")
    for e in errors[:40]: print("  [erro]", e)
    print(f"Avisos: {len(warnings)}")
    for w in warnings[:20]: print("  [aviso]", w)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
