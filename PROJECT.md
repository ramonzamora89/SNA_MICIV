# SNA MICIV: estado del proyecto

Sitio: https://ramonzamora89.github.io/SNA_MICIV/ (repo público `ramonzamora89/SNA_MICIV`). Última publicación: ronda 2, commit `647e220` (5-oct-2026), desplegada por el workflow de Pages.

## Rondas
- **4-oct-2026:** 6 semillas (nota de La Hora y sus citas). 35 respuestas, 21 quotes, 45 cuentas, red de 10,413 nodos. Archivo en `Dataset/archivo_2026-10-04/`.
- **5-oct-2026:** se recogen de nuevo las 6 semillas (había respuestas tardías) y se suman 5 que tocan el tema de forma indirecta: 3 de @vozdeltuit, @__VaderGT y @5toPoderSM. 89 respuestas, 35 quotes, 104 cuentas, red de 20,072 nodos (59 cuentas nuevas en followers).
  - Nueva narrativa, `Culpas_Trasladadas` («El oficialismo siempre culpa a otro», #ad1457). Se sumaron `responsab` y `alcahuete` a `Responsabilidad_Arevalo`. «excusa» quedó fuera porque coincidía con @FelixSinExcusas.
  - Nuevo paso «Cómo se movió la conversación» (`scripts/difusion.py`, `site_overrides/js/diffusion.js` y `css/diffusion.css`). En escritorio se dibuja sobre el panel del grafo y en móvil, dentro de la tarjeta. `prosa_sitio.py` lo inserta antes del paso de cuentas inorgánicas con `data-step="99"`.
  - El tercer tuit de @vozdeltuit (2106820856714252297) no estaba en la base de monitoreo. El texto se sacó del endpoint público de syndication de X, cacheado en `Dataset/semillas.json`.
  - La nota de La Hora del 5-oct («Grupo de empresas en el CIV») queda como hito en la línea de tiempo, no como semilla, porque falta su tuit.
  - Hallazgos que el sitio cuenta en el paso de difusión: hasta el 4-oct a las 12:34 (hora de Guatemala), 13 de 61 reacciones hablaban de Guerra, la licitación o el ministerio; después, 3 de 63. Solo 5 cuentas participan en los dos momentos. La mitad de las reacciones llega en las primeras 9 h tras cada publicación y el 90 %, en las primeras 24 h. Cruce: 28 de las 104 cuentas estuvieron en AGT_USAC y 4 en AGT (17-sep). 4 participantes cumplen el criterio de inorgánicos.
  - `apify_collect.py`: se bajó el tope por corrida de comentarios y quotes para que el control de presupuesto no bloquee la fase.
  - Se revisó con Playwright y Chrome headless sobre una copia sin contraseña, a 1440 px y 390 px. Sin errores de consola, salvo el favicon, que no existe.

## Próxima ronda (si sigue la conversación)
1. Buscar semillas y respuestas tardías en la base de monitoreo: `uv run scripts/escucha_social_contexto.py candidatos` (ajustar `DESDE`/`HASTA`). La base no siempre tiene todos los tuits; el endpoint de syndication sirve para ver uno suelto.
2. Mover `Dataset/Comments` y `Dataset/Quotes` a `Dataset/archivo_<fecha>/`, sumar las semillas a `seeds.yaml` y correr `apify_collect.py interacciones --forzar`.
3. `extract-users` → `filtrar_participantes.py` → `apify_collect.py followers --dry-run`. Confirmar el costo con Moncho antes de correrlo sin `--dry-run`.
4. `classify-media`, `build-network`, `generate-wordclouds`, `render-site`, `cruce_personajes.py`, `difusion.py` y `prosa_sitio.py`. Las cifras de la prosa están escritas a mano en `prosa_sitio.py` (`PROSA` y `DIFUSION`), así que hay que recalcularlas.
5. Candidato pendiente: el tuit de La Hora de la nota del 5-oct, si Moncho quiere sumarlo como semilla.

## Tareas pendientes

### Llevar la vista de narrativas mejorada a la plantilla del plugin
Hoy la mejora vive solo en este proyecto, en `site_overrides/js/network.js`. `render_site.py` copia `network.js` desde la plantilla del plugin en cada corrida y `scripts/prosa_sitio.py` la vuelve a aplicar. Pasarla a `/Volumes/Pikachu/sna-scrollytelling-plugin/plugins/sna-pipeline/site-template/js/network.js` para que los próximos SNA la traigan de origen.

Cambios respecto a la plantilla (ver `diff` entre ambos archivos):
- **Zoom de narrativa relativo a la vista general.** La plantilla fuerza `Math.max(1.5, …)` en escala absoluta, que en una red de unos 1,800 nodos acercaba seis veces y dejaba fuera de pantalla a casi todas las cuentas. Ahora encuadra la caja de todas las cuentas de la narrativa, entre `baseScale` y `baseScale × 2.5`, con un corrimiento a la derecha para que quepan las etiquetas.
- **Color de la narrativa.** Nodos y conexiones de las cuentas de la narrativa usan `narrative.color` (antes, el azul orgánico). Sus vecinos quedan con opacidad 0.45 y el resto con 0.05.
- **Etiquetas.** Todas las cuentas de la narrativa llevan `@handle` con halo blanco, no solo las que tienen `label` de hub.
- **Foco precalculado.** `computeFocus()` arma los conjuntos de cuentas y vecinos al entrar al paso, en vez de rehacer el `Set` en cada nodo de cada cuadro.

También conviene revisar en el plugin:
- `graph_trim.top_actors_per_narrative` vale 8 por defecto. Aquí se subió a 25 para resaltar todas las cuentas de cada narrativa. Evaluar si conviene otro valor por defecto.
- **La paleta por defecto de las narrativas no debe usar los colores de la leyenda** (rojo inorgánico, azul orgánico, ámbar medios). Se puede añadir una advertencia en `add_narrative.py`.
- **`docs/manual.html` tiene intercambiados los IDs de Apify de comentarios y quotes.** Lo correcto: comentarios = `JxQa1hxyiV7DNvz8h` (`patient_discovery/twitter-comments`); quotes = `1zGIVMa95eYRzncI4` (`seemuapps/x-quote-tweets-scraper`).
- **El actor de followers exige `maxFollowings` ≥ 200.** Documentarlo en el manual.
- Agregar al plugin un paso de recolección por API, sobre la base de `scripts/apify_collect.py`.
- **`extract-users` mezcla a los seguidores de `Redes/` con los participantes** cuando ya hay datos de red (10,444 cuentas en vez de 104). Aquí se corrige con `scripts/filtrar_participantes.py`; en el plugin, filtrar `fuentes` a comments, quotes y autor_original.
- Llevar la vista de difusión (`diffusion.js`) a la plantilla, como paso opcional.

Después de migrar: borrar `site_overrides/` y la copia en `prosa_sitio.py`, correr `render_site.py` y verificar que el sitio se vea igual.
