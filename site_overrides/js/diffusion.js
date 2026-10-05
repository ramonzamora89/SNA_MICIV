/**
 * Vista de difusión: cómo se mueve la conversación en el tiempo.
 *
 * Una fila por tuit semilla, ordenadas por hora de publicación (real, sacada del ID del tuit).
 * Cada punto es una respuesta o un quote. Las líneas punteadas unen una semilla con la semilla
 * que cita (cascada). Arriba, reacciones por bloque de 3 horas. Hora de Guatemala (UTC-6).
 *
 * En escritorio el gráfico cubre el panel del grafo mientras el paso de difusión está activo;
 * en pantallas angostas se dibuja dentro de la tarjeta.
 */
(function () {
    const GT_OFFSET_H = -6;
    const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
    const TIPO = {
        medio: { color: "#eda100", label: "Medio de comunicación" },
        comment: { color: "#4285F4", label: "Respuesta" },
        quote: { color: "#8b5cf6", label: "Quote" }
    };
    const SIN_NARRATIVA = "#b8c2cf";
    const NARROW = window.matchMedia("(max-width: 900px)");

    let data = null;
    let modo = "tipo";

    const gt = iso => new Date(new Date(iso).getTime() + GT_OFFSET_H * 3600e3);
    const hhmm = d => `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
    const fecha = d => `${d.getUTCDate()} ${MESES[d.getUTCMonth()]} ${hhmm(d)}`;
    const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

    function colorEvento(e) {
        if (modo === "tipo") return e.es_medio ? TIPO.medio.color : TIPO[e.kind].color;
        const n = data.narrativas.find(n => n.key === e.narrativa);
        return n ? n.color : SIN_NARRATIVA;
    }

    function categorias() {
        if (modo === "tipo") return Object.entries(TIPO).map(([k, v]) => ({ key: k, color: v.color, label: v.label }));
        return data.narrativas.map(n => ({ key: n.key, color: n.color, label: n.title }))
            .concat([{ key: null, color: SIN_NARRATIVA, label: "Sin narrativa" }]);
    }

    function catDe(e) {
        if (modo === "tipo") return e.es_medio ? "medio" : e.kind;
        return e.narrativa;
    }

    function montar() {
        const panel = document.getElementById("diffusion-panel");
        const slot = document.getElementById("diffusion-card-slot");
        if (!panel || !slot || !data) return;
        const destino = NARROW.matches ? slot : panel.querySelector(".diffusion-body");
        panel.querySelector(".diffusion-body").innerHTML = "";
        slot.innerHTML = "";
        destino.appendChild(controles());
        dibujar(destino, NARROW.matches ? 0 : panel.clientHeight - destino.offsetTop - 24);
    }

    function controles() {
        const wrap = document.createElement("div");
        wrap.className = "diffusion-controls";
        wrap.innerHTML = `<span>Color por</span>
            <button type="button" data-modo="tipo" class="${modo === "tipo" ? "on" : ""}">tipo de reacción</button>
            <button type="button" data-modo="narrativa" class="${modo === "narrativa" ? "on" : ""}">narrativa</button>`;
        wrap.querySelectorAll("button").forEach(b => b.addEventListener("click", () => { modo = b.dataset.modo; montar(); }));
        const leyenda = document.createElement("div");
        leyenda.className = "diffusion-legend";
        leyenda.innerHTML = categorias().map(c => `<span><i style="background:${c.color}"></i>${esc(c.label)}</span>`).join("")
            + `<span><i class="seed-mark"></i>Tuit semilla</span><span><i class="cascade-mark"></i>Cita a otra semilla</span>`;
        const frag = document.createElement("div");
        frag.append(wrap, leyenda);
        return frag;
    }

    function dibujar(contenedor, altoDisponible) {
        const seeds = data.seeds;
        const events = data.events.map(e => ({ ...e, d: gt(e.t) }));
        const seedIdx = new Map(seeds.map((s, i) => [s.id, i]));
        const corte = gt(data.corte);
        const t0 = d3.utcHour.floor(gt(seeds[0].t));
        const t1 = d3.max([corte, d3.max(events, e => e.d)]);

        const ancho = Math.max(contenedor.clientWidth || 600, 320);
        const angosto = ancho < 560;
        const m = { top: 8, right: 16, bottom: 34, left: angosto ? 96 : 128 };
        const histH = angosto ? 50 : 70;
        const lanesTop = histH + 34;
        // En el panel de escritorio las filas se estiran para usar el alto disponible
        const laneH = angosto ? 26 : Math.max(32, Math.min(46, ((altoDisponible || 0) - 140 - lanesTop - m.bottom) / seeds.length));
        const alto = lanesTop + seeds.length * laneH + m.bottom;
        const w = ancho - m.left - m.right;

        const x = d3.scaleUtc().domain([t0, t1]).range([0, w]);
        const yLane = i => lanesTop + i * laneH + laneH / 2;

        const svg = d3.select(contenedor).append("svg")
            .attr("class", "diffusion-svg").attr("viewBox", `0 0 ${ancho} ${alto + m.top}`).attr("width", "100%");
        const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

        // Bandas de día (fondo alterno) y eje
        const dias = d3.utcDay.range(d3.utcDay.floor(t0), d3.utcDay.offset(t1, 1));
        dias.forEach((d, i) => {
            const a = Math.max(0, x(d)), b = Math.min(w, x(d3.utcDay.offset(d, 1)));
            if (b <= a) return;
            g.append("rect").attr("x", a).attr("y", 0).attr("width", b - a).attr("height", alto - m.bottom)
                .attr("class", i % 2 ? "day-band odd" : "day-band");
            g.append("text").attr("class", "day-label").attr("x", a + 4).attr("y", 10)
                .text(`${d.getUTCDate()} ${MESES[d.getUTCMonth()]}`);
        });
        g.append("g").attr("class", "diffusion-axis").attr("transform", `translate(0,${alto - m.bottom})`)
            .call(d3.axisBottom(x).ticks(d3.utcHour.every(angosto ? 12 : 6)).tickFormat(d => `${hhmm(d).slice(0, 2)}h`));

        // Histograma apilado por bloques de 3 h
        const cats = categorias();
        const bins = d3.utcHours(d3.utcHour.every(3).floor(t0), t1, 3);
        const filas = bins.map(b => {
            const fin = d3.utcHour.offset(b, 3);
            const fila = { b, fin };
            cats.forEach(c => { fila[c.key] = events.filter(e => e.d >= b && e.d < fin && catDe(e) === c.key).length; });
            return fila;
        });
        const stack = d3.stack().keys(cats.map(c => c.key))(filas);
        const yH = d3.scaleLinear().domain([0, d3.max(filas, f => d3.sum(cats, c => f[c.key])) || 1]).nice().range([histH, 16]);
        stack.forEach((serie, k) => {
            g.append("g").selectAll("rect").data(serie).join("rect")
                .attr("x", d => x(d.data.b) + 0.5).attr("width", d => Math.max(0, x(d.data.fin) - x(d.data.b) - 1))
                .attr("y", d => yH(d[1])).attr("height", d => yH(d[0]) - yH(d[1]))
                .attr("fill", cats[k].color);
        });
        g.append("text").attr("class", "hist-label").attr("x", -28).attr("y", (histH + 16) / 2 + 3)
            .attr("text-anchor", "end").text(angosto ? "reac. / 3 h" : "reacciones / 3 h");
        g.append("g").attr("class", "diffusion-axis hist-axis").call(d3.axisLeft(yH).ticks(2).tickSize(3));

        // Hitos y corte de recolección
        const marcas = (data.hitos || []).map(h => ({ d: gt(h.t), texto: h.texto, cls: "hito" }))
            .concat([{ d: corte, texto: "Corte de recolección", cls: "corte" }]);
        // etiquetas escalonadas para que no se encimen cuando dos marcas quedan cerca
        marcas.forEach((mk, k) => {
            if (mk.d < t0 || mk.d > t1) return;
            const yLabel = lanesTop - 20 + (k % 2) * 11;
            g.append("line").attr("class", `marca ${mk.cls}`).attr("x1", x(mk.d)).attr("x2", x(mk.d))
                .attr("y1", yLabel + 3).attr("y2", alto - m.bottom);
            g.append("text").attr("class", `marca-label ${mk.cls}`).attr("x", x(mk.d) - 4).attr("y", yLabel)
                .attr("text-anchor", "end").text(angosto ? "" : mk.texto);
        });

        // Filas por semilla
        seeds.forEach((s, i) => {
            const y = yLane(i), xs = x(gt(s.t));
            g.append("line").attr("class", "lane").attr("x1", xs).attr("x2", w).attr("y1", y).attr("y2", y);
            const lab = g.append("text").attr("class", angosto ? "lane-label small" : "lane-label").attr("x", -8).attr("y", y - 1).attr("text-anchor", "end");
            lab.append("tspan").text(`@${s.autor}`);
            lab.append("tspan").attr("class", "lane-sub").attr("x", -8).attr("dy", angosto ? 10 : 12)
                .text(angosto ? fecha(gt(s.t)) : `${fecha(gt(s.t))} · ${s.n_comment + s.n_quote} reac.`);
        });

        // Cascadas: semilla que cita a otra semilla
        seeds.forEach((s, i) => {
            if (!s.cita_a || !seedIdx.has(s.cita_a)) return;
            const xs = x(gt(s.t)), ya = yLane(seedIdx.get(s.cita_a)), yb = yLane(i);
            g.append("path").attr("class", "cascade")
                .attr("d", `M${xs},${ya} C${xs + 18},${ya} ${xs + 18},${yb} ${xs},${yb}`);
        });

        // Reacciones (con un leve desplazamiento vertical para separar las simultáneas)
        const tip = d3.select(contenedor).append("div").attr("class", "diffusion-tip");
        const jitter = (str) => { let h = 0; for (const c of str) h = (h * 31 + c.charCodeAt(0)) | 0; return ((h % 7) - 3) * (laneH / 14); };
        g.append("g").selectAll("circle").data(events).join("circle")
            .attr("class", "ev")
            .attr("cx", e => x(e.d)).attr("cy", e => yLane(seedIdx.get(e.seed)) + jitter(e.autor + e.t))
            .attr("r", angosto ? 3 : 3.8).attr("fill", colorEvento)
            .on("mouseenter", (ev, e) => mostrar(ev, `<b>@${esc(e.autor)}</b> · ${e.kind === "quote" ? "quote" : "respuesta"} · ${fecha(e.d)}`
                + `${e.narrativa ? `<br><em>${esc((data.narrativas.find(n => n.key === e.narrativa) || {}).title)}</em>` : ""}`
                + `<br>${esc(e.texto)}`))
            .on("mouseleave", ocultar);

        // Marcador de la semilla (tamaño según likes al momento de la consulta)
        const r = d3.scaleSqrt().domain([0, d3.max(seeds, s => s.likes || 0) || 1]).range([4.5, angosto ? 9 : 12]);
        g.append("g").selectAll("path").data(seeds).join("path")
            .attr("class", "seed")
            .attr("transform", (s, i) => `translate(${x(gt(s.t))},${yLane(i)})`)
            .attr("d", s => d3.symbol(d3.symbolDiamond, Math.PI * r(s.likes || 0) ** 2)())
            .attr("fill", s => s.es_medio ? TIPO.medio.color : "#334155")
            .on("mouseenter", (ev, s) => mostrar(ev, `<b>@${esc(s.autor)}</b> · tuit semilla · ${fecha(gt(s.t))}`
                + `${s.likes != null ? ` · ${s.likes} me gusta` : ""}<br>${esc(s.texto)}`))
            .on("mouseleave", ocultar);

        function mostrar(ev, html) {
            const box = contenedor.getBoundingClientRect();
            tip.html(html).style("display", "block");
            const tw = tip.node().offsetWidth;
            let left = ev.clientX - box.left + 12;
            if (left + tw > box.width) left = ev.clientX - box.left - tw - 12;
            tip.style("left", `${Math.max(0, left)}px`).style("top", `${ev.clientY - box.top + 12}px`);
        }
        function ocultar() { tip.style("display", "none"); }
    }

    function observarPaso() {
        const paso = document.querySelector('.step[data-step-type="diffusion"]');
        const panel = document.getElementById("diffusion-panel");
        if (!paso || !panel) return;
        const sync = () => panel.classList.toggle("visible", paso.classList.contains("active") && !NARROW.matches);
        new MutationObserver(sync).observe(paso, { attributes: true, attributeFilter: ["class"] });
        sync();
    }

    document.addEventListener("DOMContentLoaded", () => {
        const graphic = document.getElementById("graphic");
        if (graphic && !document.getElementById("diffusion-panel")) {
            const panel = document.createElement("div");
            panel.id = "diffusion-panel";
            panel.innerHTML = `<div class="diffusion-head">Cómo se movió la conversación · hora de Guatemala</div><div class="diffusion-body"></div>`;
            graphic.appendChild(panel);
        }
        observarPaso();
        d3.json("visuals/diffusion.json").then(d => {
            data = d;
            montar();
            let t;
            window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(montar, 200); });
            NARROW.addEventListener("change", () => { montar(); observarPaso(); });
        }).catch(err => console.error("Error al cargar diffusion.json:", err));
    });
})();
