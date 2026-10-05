# SNA MICIV: puentes de Primavera

Red de conversación en X sobre la nota de La Hora «Puentes de Primavera sobrevalorados» (3-oct-2026) y sus citas.

## Flujo
1. `seeds.yaml`: tuits semilla y su carpeta (Medios/Usuarios).
2. `uv run scripts/apify_collect.py interacciones` → comentarios y quotes por API de Apify (tope de gasto por corrida; `--dry-run` para ver el tope).
3. Plugin `sna-pipeline`: `extract-users` → `Dataset/apify_users_list.txt`, y enseguida `uv run scripts/filtrar_participantes.py` (el plugin mete también a los seguidores de `Redes/`).
4. `uv run scripts/apify_collect.py followers` → `Dataset/Redes/` (200 seguidores + 200 seguidos por cuenta; el actor exige ≥ 200 seguidos). Solo pide las cuentas que aún no están en `Redes/`.
5. Plugin: `classify-media`, `define-narratives`, `build-network`, `generate-wordclouds`, `render-site`.
6. `uv run scripts/escucha_social_contexto.py exportar`: contexto de la base de Escucha-Social (solo lectura).
7. `uv run scripts/cruce_personajes.py`: cuentas que reaparecen en AGT (nota del 17-sep) y AGT_USAC.
8. `uv run scripts/difusion.py` → `visuals/diffusion.json` (línea de tiempo por semilla; hora real sacada del ID del tuit).
9. `uv run scripts/prosa_sitio.py`: prosa del sitio y motor JS ajustado de `site_overrides/` (correr siempre después de `render-site`).

Actores de Apify: `patient_discovery/twitter-comments` (JxQa1hxyiV7DNvz8h), `seemuapps/x-quote-tweets-scraper` (1zGIVMa95eYRzncI4), `kaitoeasyapi/premium-x-follower-scraper-following-data` (C2Wk3I6xAqC4Xi63f). `APIFY_TOKEN` y `DATABASE_URL` se leen del `.env` de Escucha-Social.

Para una ronda nueva sobre semillas ya recogidas: mover `Dataset/Comments` y `Dataset/Quotes` a `Dataset/archivo_<fecha>/` y correr `interacciones --forzar` (si no, las aristas se duplican).

`Dataset/`, `reportes/` y `runs.log.csv` no se versionan.
