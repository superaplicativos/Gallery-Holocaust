# Gallery-Holocaust — Acervo para Produção de Documentários

Acervo de imagens e vídeos históricos sobre o Holocausto, organizado como catálogo
consultável por scripts, para alimentar a produção de documentários (narradores pt-BR,
cards, legendas, montagem ffmpeg). O episódio **ep01 — Filip Müller: A Testemunha dos
Crematórios** já usa este pipeline.

## Estrutura

```
Gallery-Holocaust/
├── README.md                      <- este arquivo
├── LICENSES.md                    <- termos de uso por fonte (leia antes de publicar)
├── config/
│   ├── schema.json                <- schema dos registros do catálogo
│   └── pipeline_rules.json        <- regras do pipeline (naming, etapas, rigor)
├── data/
│   ├── media_catalog.jsonl        <- CATÁLOGO: 1 registro JSON por linha
│   ├── victims_and_events.csv     <- vítimas e eventos documentados
│   ├── prompt_templates.json      <- prompts de colorização/restauração/reconstrução
│   └── story_bible.json           <- bíblia de produção (gerada por script)
├── scripts/
│   ├── validate_catalog.py        <- valida o catálogo contra o schema
│   ├── build_story_bible.py       <- gera data/story_bible.json
│   ├── export_episode_batch.py    <- cruza scenes.json com o catálogo -> production_batch.json
│   ├── backfill_commons.py        <- completa ano/licença dos registros pendentes (WMF)
│   ├── fetch_commons_v4.py        <- coleta no Wikimedia Commons (via PetScan + CDN)
│   ├── fetch_websearch.py         <- coleta por busca web (ZAI image search)
│   ├── colorize_ai.py             <- colorização IA (z-ai image-edit) com registro
│   └── add_remote_records.py      <- registra fontes institucionais como remote_reference
├── episodes/
│   └── ep01_filip_mueller/        <- episódio de exemplo (script.md, scenes.json, captions.srt)
└── media/
    ├── raw/web/                   <- fotos históricas brutas (originais intactos)
    ├── raw/commons/               <- fotos do Wikimedia Commons (originais intactos)
    ├── ai_colorized/              <- colorizações IA (reconstrução, requer validação)
    └── video_archive/             <- clipes de arquivo (ffmpeg -t 45)
```

## O catálogo (`data/media_catalog.jsonl`)

Cada linha é um ativo:

```json
{
  "id": "COMMONS_PH_000042",
  "title": "Retrato de prisioneira no registro de Auschwitz",
  "source_archive": "Wikimedia Commons",
  "source_url": "https://commons.wikimedia.org/wiki/File:...",
  "license_status": "public_domain",
  "year": "1943",
  "location": "Oświęcim, Polônia",
  "subject_type": "victim_portrait",
  "linked_victims": ["Katarzyna Kwoka"],
  "processing_stage": "raw_original",
  "local_path": "media/raw/commons/COMMONS_PH_000042.jpg",
  "historical_notes": "...",
  "visual_tags": ["arquivo", "retrato", "oświęcim"]
}
```

Estados (`processing_stage`): `raw_original` (bruto), `upscaled` (restaurado),
`colorized` (colorização validada), `ai_colorized` (colorização IA — reconstrução),
`ai_generated` (cena sintetizada), `remote_reference` (fonte externa não baixada).

## Estado atual do acervo

| Fonte | Registros | Observação |
|---|---|---|
| Web (busca de imagens, 14 queries temáticas) | 107 fotos | `needs_triage`: validar fonte/licença antes de uso público |
| Colorização IA | 5 | reconstrução de cores, origem registrada em `derived_from` |
| Internet Archive (filmes PD) | 2 (remote) | *Nazi Concentration Camps* (1945) e *Death Mills* (1945) |
| USHMM / Yad Vashem / Arolsen / NARA / IWM | 5 (remote) | acervos institucionais para coleta futura |

Total: ~120 registros · ~48 MB de mídia local · licenças a revisar: ver `LICENSES.md`.

## Como usar no pipeline do documentário

```bash
# 1. Validar catálogo
python scripts/validate_catalog.py

# 2. Bíblia de produção (pessoas/eventos + mídias vinculadas)
python scripts/build_story_bible.py

# 3. Lote de produção do episódio (sugestão de mídia por cena)
python scripts/export_episode_batch.py episodes/ep01_filip_mueller
#    -> episodes/ep01_filip_mueller/production_batch.json

# 4. Coletar mais mídia (respeitar rate limit do Wikimedia)
python scripts/fetch_commons_v4.py                # listagem via PetScan + CDN
python scripts/fetch_websearch.py                 # busca web via ZAI image search

# 5. Colorizar (IA) mantendo o original intacto
python scripts/colorize_ai.py
```

O renderer do documentário (fora deste repo: cards PIL 2400x1350 + ffmpeg zoompan
suave + narração edge-tts `pt-BR-AntonioNeural` + legendas) consome
`production_batch.json`: cada cena leva `media_sugerida[0..4]` como plano de fundo.

## Rigor histórico e dignidade

1. **Separe fato de reconstrução.** Imagens `ai_colorized`/`ai_generated` são
   reconstruções — rotular sempre (ex.: "Reconstrução colorida por IA — cores aproximadas").
2. **Não invente detalhes sensíveis.** Cores de uniformes, insígnias e fachadas são
   verificáveis; rostos de vítimas reais não devem ser modificados por IA.
3. **Preserve a dignidade das vítimas.** Nada de sensacionalismo; retratos de
   `victim_portrait` não são colorizados automaticamente pelo pipeline.
4. **Verifique direitos por item.** `license_status` em `license_review_needed` ou
   `institutional_archive_check` exige revisão antes de qualquer publicação.
   Veja `LICENSES.md`.

## Notas de coleta

- O Wikimedia Commons limita por IP: as coletas usam PetScan (listagem), API da
  Wikipédia EN (metadados, resolve arquivos do Commons) e CDN
  (`Special:FilePath`) para download — com backoff. Registros com
  `metadata_pending: true` recebem ano/licença por `backfill_commons.py`.
- Filmes de liberação (domínio público) estão catalogados como
  `remote_reference` com URLs para download no Internet Archive e no Commons
  (`File:Nazi Concentration Camps.webm`, `File:Death Mills (1945).webm`).

## Licença do repositório

O código deste repositório (scripts, schemas) pode ser usado livremente pelo
proprietário do acervo. **As imagens mantêm as licenças de suas fontes originais**
— ver `LICENSES.md` antes de qualquer uso público.
