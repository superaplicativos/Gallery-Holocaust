# Media

| Pasta | Conteúdo | Regra |
|---|---|---|
| `raw/web/` | Fotos históricas brutas coletadas por busca web (`WEB_PH_*`) | Originais intactos; `needs_triage` até validar fonte/licença |
| `raw/commons/` | Fotos do Wikimedia Commons (`COMMONS_PH_*`) | Originais intactos; metadados podem estar `metadata_pending` |
| `ai_colorized/` | Colorizações IA (`AIGEN_PH_*`) | Reconstrução — exige validação histórica antes de uso público |
| `restored/` | Restaurações/upscale (a criar) | Nunca sobrescrever `raw/` |
| `video_archive/` | Clipes de filmes de arquivo (a coletar) | Filmes PD catalogados em `remote_reference` no catálogo |

Todo arquivo em `media/` deve ter registro correspondente em `data/media_catalog.jsonl`
(validável com `python scripts/validate_catalog.py`).
