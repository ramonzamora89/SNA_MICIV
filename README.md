# SNA MICIV: puentes de Primavera

Red de conversación en X sobre la nota de La Hora «Puentes de Primavera sobrevalorados» (3-oct-2026) y sus citas.

## Flujo
1. `seeds.yaml`: tuits semilla y su carpeta (Medios/Usuarios).
2. `uv run scripts/apify_collect.py interacciones` → comentarios y quotes por API de Apify (tope de gasto por corrida; `--dry-run` para ver el tope).
3. Plugin `sna-pipeline`: `extract-users` → `Dataset/apify_users_list.txt`.
4. `uv run scripts/apify_collect.py followers` → `Dataset/Redes/` (200 seguidores + 200 seguidos por cuenta; el actor exige ≥ 200 seguidos).
5. Plugin: `classify-media`, `define-narratives`, `build-network`, `generate-wordclouds`, `render-site`.
6. `uv run scripts/escucha_social_contexto.py exportar`: contexto de la base de Escucha-Social (solo lectura).
7. `uv run scripts/cruce_personajes.py`: cuentas que reaparecen en AGT, AGT_CC y AGT_USAC.
8. `uv run scripts/prosa_sitio.py`: prosa del sitio (correr después de `render-site`).

Actores de Apify: `patient_discovery/twitter-comments` (JxQa1hxyiV7DNvz8h), `seemuapps/x-quote-tweets-scraper` (1zGIVMa95eYRzncI4), `kaitoeasyapi/premium-x-follower-scraper-following-data` (C2Wk3I6xAqC4Xi63f). `APIFY_TOKEN` y `DATABASE_URL` se leen del `.env` de Escucha-Social.

`Dataset/`, `reportes/` y `runs.log.csv` no se versionan.
