# SNA MICIV: estado del proyecto

Sitio: https://ramonzamora89.github.io/SNA_MICIV/ (repo público `ramonzamora89/SNA_MICIV`). Datos recogidos el 4-oct-2026. Gasto en Apify: unos $2.23.

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

Después de migrar: borrar `site_overrides/` y la copia en `prosa_sitio.py`, correr `render_site.py` y verificar que el sitio se vea igual.
