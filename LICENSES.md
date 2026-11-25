# Licenças e Direitos por Fonte

Antes de qualquer publicação, verifique o `license_status` de cada registro no
catálogo. Resumo das fontes usadas/previstas:

| Fonte | Status típico | O que precisa |
|---|---|---|
| **Wikimedia Commons** | `public_domain`, `cc0`, `cc_by`, `cc_by_sa` (por item) | Crédito do autor quando CC BY/CC BY-SA; verificar `license_name`/`license_url` do registro. |
| **Internet Archive** (Nazi Concentration Camps, Death Mills) | `public_domain` (filmes do governo dos EUA, 1945) | Livre para uso com crédito institucional recomendado (NARA). |
| **US National Archives (NARA)** | `public_domain` (material US Gov) | Crédito: National Archives (ARC/ID do item). |
| **USHMM** | `institutional_archive_check` | Termos por item; muitas fotos exigem crédito "United States Holocaust Memorial Museum, courtesy of..." e algumas exigem autorização. |
| **Yad Vashem** | `institutional_archive_check` | Uso editorial exige revisão por item; fotos de famílias podem ter direitos. |
| **Arolsen Archives** | `institutional_archive_check` | Documentos pessoais: uso educacional geralmente aceito com crédito; confirmar por item. |
| **Imperial War Museums (IWM)** | `institutional_archive_check` | Muitos itens com IWM Non-Commercial Licence; uso comercial precisa licença paga. |
| **Busca web (ZAI image search)** | `license_review_needed` | ORIGEM NÃO VERIFICADA por padrão (`needs_triage: true`): identificar o site de origem, checar licença e substituir por cópia de acervo institucional quando possível. |
| **Colorização IA (`ai_colorized`)** | herda a licença da origem | É RECONSTRUÇÃO: rotular no vídeo/publicação; cores aproximadas, não registro histórico. |

## Regras do acervo

1. **Uso público** (vídeo publicado, mídia social, exposição) só com
   `public_domain`, `cc0`, `cc_by` ou `cc_by_sa`.
2. **Registros em review** (`license_review_needed`, `institutional_archive_check`)
   podem ser usados em rascunhos e pré-visualizações internas, mas não em
   publicações.
3. **Sempre manter o original intacto** em `media/raw/` — restaurações e
   colorizações ficam em arquivos separados com `derived_from` apontando ao ID.
4. **Crédito mínimo recomendado** na descrição do vídeo quando a fonte é
   conhecida (ex.: "Fotos: Wikimedia Commons / USHMM / Internet Archive").

## Como resolver um registro pendente

1. Abrir `source_url` do registro.
2. Identificar autor/coleção e licença (página de detalhe do acervo).
3. Atualizar no catálogo: `license_status`, `license_name`, `license_url`,
   `historical_notes` e `needs_triage: false`.
4. Rodar `python scripts/validate_catalog.py` para conferir.
