#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adiciona ao catálogo registros remotos (remote_only):
- Filmes históricos em domínio público (Internet Archive / Commons / NARA)
- Acervos institucionais (USHMM, Yad Vashem, Arolsen, NARA, IWM) como fontes de referência."""
import json, os

ROOT = "/home/z/my-project/Gallery-Holocaust"
CATALOG = os.path.join(ROOT, "data", "media_catalog.jsonl")
os.makedirs(os.path.dirname(CATALOG), exist_ok=True)

VIDEOS = [
    {
        "id": "IA_VID_000001",
        "title": "Nazi Concentration Camps (1945) - compilacao de liberacao dos Aliados",
        "source_archive": "Internet Archive (Prelinger/NARA)",
        "source_url": "https://archive.org/details/nazi_concentration_camps",
        "alternate_urls": ["https://archive.org/details/gov.archives.arc.43452",
                           "https://commons.wikimedia.org/wiki/File:Nazi_Concentration_Camps.webm"],
        "license_status": "public_domain",
        "year": "1945",
        "location": "Alemanha e Austria (liberacao 1945)",
        "subject_type": "archival_film",
        "linked_events": ["Liberação dos campos (1945)"],
        "historical_notes": "Compilacao do US Dept. of Defense exibida no Processo de Nuremberg (nov 1945). Domínio público (US Government). Para uso: baixar do IA, recortar trechos com ffmpeg e registrar processing_stage=upscaled.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["arquivo", "filme", "liberação"],
    },
    {
        "id": "IA_VID_000002",
        "title": "Death Mills / Die Todesmuehlen (1945) - dirigido por Billy Wilder",
        "source_archive": "Internet Archive",
        "source_url": "https://archive.org/details/DeathMills",
        "alternate_urls": ["https://commons.wikimedia.org/wiki/File:Death_Mills_(1945).webm",
                           "https://collections.ushmm.org/search/catalog/irn1000182"],
        "license_status": "public_domain",
        "year": "1945",
        "location": "Alemanha e Austria (liberacao 1945)",
        "subject_type": "archival_film",
        "linked_events": ["Liberação dos campos (1945)"],
        "historical_notes": "Filme de liberacao (jun 1945) preparado para exibicao na Alemanha ocupada, com versao em alemao. Domínio público. Mostre Auschwitz, Majdanek, Treblinka e Belsen.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["arquivo", "filme", "liberação"],
    },
]

INSTITUTIONAL = [
    {
        "id": "USHMM_REF_000001",
        "title": "Acervo de fotografias e filmagens USHMM (Washington DC)",
        "source_archive": "United States Holocaust Memorial Museum",
        "source_url": "https://collections.ushmm.org/search/",
        "license_status": "institutional_archive_check",
        "year": "varios",
        "location": "Washington DC, EUA",
        "subject_type": "institutional_reference",
        "linked_events": [],
        "historical_notes": "Dezenas de milhares de fotos, documentos e registros fílmicos. Uso exige verificar termos por item (collections.ushmm.org). Muitas imagens possíveis de licenciar para uso educacional/memorial com crédito.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["instituição", "referência"],
    },
    {
        "id": "YAD_REF_000001",
        "title": "Yad Vashem Central Database of Shoah Victims Names + Photo Archive",
        "source_archive": "Yad Vashem (Jerusalém)",
        "source_url": "https://yvng.yadvashem.org/",
        "license_status": "institutional_archive_check",
        "year": "varios",
        "location": "Jerusalém, Israel",
        "subject_type": "institutional_reference",
        "linked_victims": ["Katarzyna Kwoka", "Filip Müller"],
        "linked_events": [],
        "historical_notes": "Base de nomes de vítimas, cartões de registro e fotos de retrato. Consultar termos de uso por item (vários exigem autorização para reprodução).",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["instituição", "referência"],
    },
    {
        "id": "AROL_REF_000001",
        "title": "Arolsen Archives (ex-ITS Bad Arolsen) - registros de perseguicao e trabalho forcado",
        "source_archive": "Arolsen Archives",
        "source_url": "https://arolsen-archives.org/en/search-online-archive/",
        "license_status": "institutional_archive_check",
        "year": "varios",
        "location": "Bad Arolsen, Alemanha",
        "subject_type": "institutional_reference",
        "linked_victims": [],
        "linked_events": [],
        "historical_notes": "Milhões de registros documentais (presos, trabalho forçado, deslocados). Útil para trajetórias individuais e datas; documentos escaneados disponíveis na busca online.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["instituição", "referência"],
    },
    {
        "id": "NARA_REF_000001",
        "title": "US National Archives (NARA) - fotos e filmagens de liberacao (ex. ARC 43452)",
        "source_archive": "US National Archives (NARA)",
        "source_url": "https://catalog.archives.gov/",
        "license_status": "public_domain",
        "year": "varios",
        "location": "College Park, EUA",
        "subject_type": "institutional_reference",
        "linked_events": ["Liberação dos campos (1945)"],
        "historical_notes": "Fotos militares, mapas de inteligência aérea e filmagens de liberação (ex.: Nazi Concentration Camps ARC 43452; Death Mills 111-OF-19). API v2 exige api key gratuita (catalog.archives.gov/developers). Domínio público para material US Gov.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["instituição", "referência"],
    },
    {
        "id": "IWM_REF_000001",
        "title": "Imperial War Museums (IWM) - fotografias militares e filmagens de liberacao",
        "source_archive": "Imperial War Museums (Reino Unido)",
        "source_url": "https://www.iwm.org.uk/collections",
        "license_status": "institutional_archive_check",
        "year": "varios",
        "location": "Londres, Reino Unido",
        "subject_type": "institutional_reference",
        "linked_events": ["Liberação dos campos (1945)"],
        "historical_notes": "Fotos militares aliadas e filmagens de liberação (Bergen-Belsen etc.). Licenças variam por item; verificar cada registro no site.",
        "processing_stage": "remote_reference",
        "local_path": None,
        "visual_tags": ["instituição", "referência"],
    },
]

def main():
    existing = set()
    if os.path.exists(CATALOG):
        with open(CATALOG, encoding="utf-8") as f:
            for line in f:
                try:
                    existing.add(json.loads(line).get("id"))
                except Exception:
                    pass
    added = 0
    with open(CATALOG, "a", encoding="utf-8") as f:
        for rec in VIDEOS + INSTITUTIONAL:
            if rec["id"] in existing: continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
    print(f"OK: {added} registros remotos adicionados")

if __name__ == "__main__":
    main()
