/**
 * Network Visualization Engine (D3.js + Canvas 2D)
 * Generic engine: reads step structure, colors and physics from
 * window.SNA_CONFIG (injected by render-site into index.html) instead of
 * hardcoded per-project constants, so any number of narratives works
 * without editing this file.
 *
 * window.SNA_CONFIG shape:
 * {
 *   steps: [{index, type: "intro"|"bot_intro"|"narrative"|"bot_detail"|"hubs", key}],
 *   theme: {organicColor, inorganicColor, medioColor},
 *   physics: {linkDistance, chargeStrength, ticks}
 * }
 */

const canvas = document.querySelector("#network-canvas");
const ctx = canvas.getContext("2d");
const tooltip = document.querySelector("#tooltip");

const SNA_CONFIG = window.SNA_CONFIG || { steps: [], theme: {}, physics: {} };
const STEPS_BY_INDEX = new Map(SNA_CONFIG.steps.map(s => [s.index, s]));

let width, height;
let networkData = null;
let filteredNodes = [];
let filteredLinks = [];
let currentTransform = d3.zoomIdentity;
let activeStep = 0;
let activeClusterKey = null;

let nodesById = new Map();
let baseScale = 1;              // escala de la vista general (resetZoom)
let focus = { key: null, actors: new Set(), neighbors: new Set(), color: "#4285F4" };

const COLORS = {
    organic: SNA_CONFIG.theme.organicColor || "#4285F4",
    inorganic: SNA_CONFIG.theme.inorganicColor || "#e74c3c",
    medio: SNA_CONFIG.theme.medioColor || "#eda100",
    mutedLink: "rgba(0, 0, 0, 0.03)",
    activeLink: "rgba(15, 23, 42, 0.14)",
    highlightLink: "rgba(66, 133, 244, 0.3)"
};

const PHYSICS = {
    linkDistance: SNA_CONFIG.physics.linkDistance ?? 40,
    chargeStrength: SNA_CONFIG.physics.chargeStrength ?? -80,
    ticks: SNA_CONFIG.physics.ticks ?? 300
};

function stepTypeAt(index) {
    const step = STEPS_BY_INDEX.get(index);
    return step ? step.type : null;
}

function clusterKeyAt(index) {
    const step = STEPS_BY_INDEX.get(index);
    return step ? step.key : null;
}

// Same slugging rule as sna_common.slugify() on the Python side -- keep in sync.
function slug(key) {
    return (key || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "narrativa";
}

function resize() {
    width = canvas.parentElement.clientWidth;
    height = canvas.parentElement.clientHeight;
    canvas.width = width;
    canvas.height = height;
    if (networkData) draw();
}
window.addEventListener("resize", resize);
resize();

const clusterCenters = {};

d3.json("visuals/executive_network.json").then(data => {
    networkData = data;

    // El JSON ya viene recortado a los nodos relevantes por build-network --
    // no se vuelve a filtrar acá, para no descartar la muestra de cuentas
    // inorgánicas (que suelen tener in-degree bajo).
    filteredNodes = data.nodes;

    const nodeIds = new Set(filteredNodes.map(d => d.id));
    filteredNodes.forEach(node => nodesById.set(node.id, node));

    filteredLinks = data.links.filter(l =>
        (typeof l.source === 'string' ? nodeIds.has(l.source) : nodeIds.has(l.source.id)) &&
        (typeof l.target === 'string' ? nodeIds.has(l.target) : nodeIds.has(l.target.id))
    );

    const simulation = d3.forceSimulation(filteredNodes)
        .force("link", d3.forceLink(filteredLinks).id(d => d.id).distance(PHYSICS.linkDistance))
        .force("charge", d3.forceManyBody().strength(PHYSICS.chargeStrength))
        .force("center", d3.forceCenter(width / 2, height / 2));

    for (let i = 0; i < PHYSICS.ticks; i++) simulation.tick();
    simulation.stop();

    calculateClusterCenters();
    populateUI();
    resetZoom();
    setupInteractions();
    draw();
}).catch(err => {
    console.error("Error cargando datos de red:", err);
});

function calculateClusterCenters() {
    if (!networkData) return;
    Object.keys(networkData.narratives).forEach(key => {
        const narrative = networkData.narratives[key];
        const actorIds = new Set(narrative.top_actors.map(a => a.id));
        const matchingNodes = filteredNodes.filter(n => actorIds.has(n.id));

        if (matchingNodes.length > 0) {
            const xs = matchingNodes.map(n => n.x);
            const ys = matchingNodes.map(n => n.y);
            clusterCenters[key] = {
                x: d3.mean(matchingNodes, n => n.x),
                y: d3.mean(matchingNodes, n => n.y),
                spanX: Math.max(...xs) - Math.min(...xs),
                spanY: Math.max(...ys) - Math.min(...ys),
                midX: (Math.max(...xs) + Math.min(...xs)) / 2,
                midY: (Math.max(...ys) + Math.min(...ys)) / 2
            };
        } else {
            clusterCenters[key] = { x: width / 2, y: height / 2, spanX: 200, spanY: 200 };
        }
    });
}

function populateUI() {
    if (!networkData) return;

    const botGrid = document.querySelector("#bot-grid");
    if (botGrid) {
        botGrid.innerHTML = "";
        networkData.stats.all_bots.slice(0, 32).forEach(bot => {
            const badge = document.createElement("span");
            badge.className = "actor-badge inorganic";
            badge.innerText = `@${bot}`;
            botGrid.appendChild(badge);
        });
    }

    Object.keys(networkData.narratives).forEach(key => {
        const container = document.querySelector(`#actors-${slug(key)}`);
        const narrative = networkData.narratives[key];
        if (container) {
            container.innerHTML = "";
            narrative.top_actors.forEach(actor => {
                const badge = document.createElement("span");
                const cls = actor.es_medio ? "medio" : actor.type;
                badge.className = `actor-badge ${cls}`;
                badge.innerText = `@${actor.id}`;
                container.appendChild(badge);
            });
        }
    });
}

function draw() {
    if (!networkData) return;

    ctx.save();
    ctx.clearRect(0, 0, width, height);
    ctx.translate(currentTransform.x, currentTransform.y);
    ctx.scale(currentTransform.k, currentTransform.k);

    const stepType = stepTypeAt(activeStep);

    filteredLinks.forEach(link => {
        const source = nodesById.get(link.source.id || link.source);
        const target = nodesById.get(link.target.id || link.target);
        if (!source || !target) return;

        ctx.beginPath();

        if (stepType === "intro" || stepType === "bot_intro" || stepType === "diffusion") {
            ctx.strokeStyle = COLORS.activeLink;
            ctx.lineWidth = 0.6 / Math.sqrt(currentTransform.k);
        } else if (stepType === "narrative") {
            if (focus.actors.has(source.id) || focus.actors.has(target.id)) {
                ctx.strokeStyle = hexToRgba(focus.color, 0.28);
                ctx.lineWidth = 0.9 / currentTransform.k;
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        } else if (stepType === "bot_detail") {
            if (source.type === 'inorganic' && target.type === 'inorganic') {
                ctx.strokeStyle = "rgba(231, 76, 60, 0.25)";
                ctx.lineWidth = 0.8 / Math.sqrt(currentTransform.k);
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        } else if (stepType === "hubs") {
            if (source.label || target.label) {
                ctx.strokeStyle = "rgba(66, 133, 244, 0.35)";
                ctx.lineWidth = 0.8 / Math.sqrt(currentTransform.k);
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        }

        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
    });

    filteredNodes.forEach(node => {
        ctx.beginPath();
        const radius = Math.sqrt(node.val) * 0.65;
        let opacity = 1.0;
        let color = node.es_medio ? COLORS.medio : (node.type === 'inorganic' ? COLORS.inorganic : COLORS.organic);

        if (stepType === "intro" || stepType === "bot_intro" || stepType === "diffusion") {
            opacity = 1.0;
        } else if (stepType === "narrative") {
            if (focus.actors.has(node.id)) {
                const r = Math.max(radius * 1.4, 7 / currentTransform.k);
                ctx.arc(node.x, node.y, r * 1.9, 0, 2 * Math.PI);
                ctx.fillStyle = hexToRgba(focus.color, 0.18);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                ctx.fillStyle = focus.color;
                ctx.fill();
                ctx.lineWidth = 1.5 / currentTransform.k;
                ctx.strokeStyle = "#ffffff";
                ctx.stroke();
                return;
            } else if (focus.neighbors.has(node.id)) {
                opacity = 0.45;
            } else {
                opacity = 0.05;
            }
        } else if (stepType === "bot_detail") {
            if (node.type === 'inorganic') {
                opacity = 1.0;
                color = COLORS.inorganic;
                ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(231, 76, 60, 0.15)";
                ctx.fill();
                ctx.beginPath();
            } else {
                opacity = 0.08;
            }
        } else if (stepType === "hubs") {
            if (node.label) {
                opacity = 1.0;
                ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(0, 0, 0, 0.03)";
                ctx.fill();
                ctx.beginPath();
            } else {
                opacity = 0.08;
            }
        }

        ctx.fillStyle = hexToRgba(color, opacity);
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fill();
    });

    if (stepType === "narrative") {
        const fontPx = 13 / currentTransform.k;
        ctx.font = `600 ${fontPx}px 'Poppins', sans-serif`;
        ctx.lineJoin = "round";
        filteredNodes.forEach(node => {
            if (!focus.actors.has(node.id)) return;
            const r = Math.max(Math.sqrt(node.val) * 0.65 * 1.4, 7 / currentTransform.k);
            const x = node.x + r + 4 / currentTransform.k, y = node.y + fontPx * 0.35;
            ctx.lineWidth = 3.5 / currentTransform.k;
            ctx.strokeStyle = "rgba(255,255,255,0.92)";
            ctx.strokeText("@" + node.id, x, y);
            ctx.fillStyle = "#1f2937";
            ctx.fillText("@" + node.id, x, y);
        });
        ctx.restore();
        return;
    }

    filteredNodes.forEach(node => {
        if (!node.label) return;
        let showLabel = false;
        let labelColor = "#2c3e50";
        let opacity = 1.0;

        if (stepType === "intro" || stepType === "bot_intro" || stepType === "diffusion") {
            showLabel = true;
            opacity = 0.75;
        } else if (stepType === "narrative") {
            const narrative = networkData.narratives[activeClusterKey];
            const actorIds = narrative ? new Set(narrative.top_actors.map(a => a.id)) : null;
            showLabel = !!(actorIds && actorIds.has(node.id));
            labelColor = node.es_medio ? "#92620a" : "#1e40af";
        } else if (stepType === "bot_detail") {
            showLabel = node.type === 'inorganic' && node.val > 3;
            labelColor = "#991b1b";
        } else if (stepType === "hubs") {
            showLabel = true;
            labelColor = node.type === 'inorganic' ? "#991b1b" : "#1e40af";
        }

        if (showLabel) {
            const radius = Math.sqrt(node.val) * 0.65;
            ctx.font = `bold ${10 / Math.sqrt(currentTransform.k) + 8}px 'Poppins', sans-serif`;
            ctx.fillStyle = hexToRgba(labelColor, opacity);
            ctx.fillText(node.label, node.x + radius + 3, node.y + 3);
        }
    });

    ctx.restore();
}

function hexToRgba(hex, alpha) {
    let r = 0, g = 0, b = 0;
    if (hex.startsWith("#")) {
        if (hex.length === 4) {
            r = parseInt(hex[1] + hex[1], 16);
            g = parseInt(hex[2] + hex[2], 16);
            b = parseInt(hex[3] + hex[3], 16);
        } else if (hex.length === 7) {
            r = parseInt(hex.substring(1, 3), 16);
            g = parseInt(hex.substring(3, 5), 16);
            b = parseInt(hex.substring(5, 7), 16);
        }
    } else if (hex.startsWith("rgba")) {
        return hex;
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function transitionTo(targetX, targetY, targetScale) {
    const x = width / 2 - targetX * targetScale;
    const y = height / 2 - targetY * targetScale;

    const interpolator = d3.interpolate(
        { x: currentTransform.x, y: currentTransform.y, k: currentTransform.k },
        { x, y, k: targetScale }
    );

    d3.transition()
        .duration(1100)
        .ease(d3.easeCubicInOut)
        .tween("zoom", () => (t) => {
            const current = interpolator(t);
            currentTransform = d3.zoomIdentity.translate(current.x, current.y).scale(current.k);
            draw();
        });
}

function resetZoom() {
    if (filteredNodes.length === 0) return;
    const minX = d3.min(filteredNodes, d => d.x);
    const maxX = d3.max(filteredNodes, d => d.x);
    const minY = d3.min(filteredNodes, d => d.y);
    const maxY = d3.max(filteredNodes, d => d.y);
    const centerX = d3.mean(filteredNodes, d => d.x);
    const centerY = d3.mean(filteredNodes, d => d.y);

    // Sin tope artificial: la red llena el 90% del canvas según su distribución real
    const scaleX = (width * 0.90) / (maxX - minX);
    const scaleY = (height * 0.90) / (maxY - minY);
    const targetScale = Math.min(scaleX, scaleY);
    baseScale = targetScale;

    currentTransform = d3.zoomIdentity
        .translate(width / 2 - centerX * targetScale, height / 2 - centerY * targetScale)
        .scale(targetScale);
}

function computeFocus(key) {
    const narrative = networkData && networkData.narratives[key];
    focus = { key, actors: new Set(), neighbors: new Set(), color: COLORS.organic };
    if (!narrative) return;
    focus.actors = new Set(narrative.top_actors.map(a => a.id));
    focus.color = narrative.color || (key === "Medios" ? COLORS.medio : COLORS.organic);
    filteredLinks.forEach(l => {
        const s = l.source.id || l.source, t = l.target.id || l.target;
        if (focus.actors.has(s)) focus.neighbors.add(t);
        if (focus.actors.has(t)) focus.neighbors.add(s);
    });
}

function setVisualState(stepIndex) {
    activeStep = stepIndex;
    activeClusterKey = clusterKeyAt(stepIndex);
    if (!networkData) return;
    if (stepTypeAt(stepIndex) === "narrative") computeFocus(activeClusterKey);

    const stepType = stepTypeAt(stepIndex);

    if (stepType === "intro" || stepType === "bot_intro" || stepType === "diffusion") {
        resetZoom();
        draw();
    } else if (stepType === "narrative") {
        const center = clusterCenters[activeClusterKey];
        if (center) {
            // Encuadrar todas las cuentas de la narrativa (más un margen para etiquetas),
            // sin alejarse más que la vista general ni acercarse más de 2.5x
            const pad = 0.18;
            const fitX = (width * 0.70) / (center.spanX * (1 + pad) || 1);
            const fitY = (height * 0.78) / (center.spanY * (1 + pad) || 1);
            const targetScale = Math.max(baseScale, Math.min(fitX, fitY, baseScale * 2.5));
            // las etiquetas van a la derecha de cada nodo: correr el encuadre un poco hacia ellas
            transitionTo((center.midX ?? center.x) + center.spanX * 0.08, center.midY ?? center.y, targetScale);
        }
    } else if (stepType === "bot_detail") {
        const inorganicNodes = filteredNodes.filter(n => n.type === 'inorganic');
        if (inorganicNodes.length > 0) {
            const avgX = d3.mean(inorganicNodes, n => n.x);
            const avgY = d3.mean(inorganicNodes, n => n.y);
            transitionTo(avgX, avgY, 0.52);
        } else {
            resetZoom();
            draw();
        }
    } else if (stepType === "hubs") {
        const hubs = filteredNodes.filter(n => n.label !== "");
        if (hubs.length > 0) {
            const avgX = d3.mean(hubs, n => n.x);
            const avgY = d3.mean(hubs, n => n.y);
            transitionTo(avgX, avgY, 0.72);
        } else {
            resetZoom();
            draw();
        }
    }
}

function setupInteractions() {
    canvas.addEventListener("mousemove", (event) => {
        if (!networkData || filteredNodes.length === 0) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = (event.clientX - rect.left - currentTransform.x) / currentTransform.k;
        const mouseY = (event.clientY - rect.top - currentTransform.y) / currentTransform.k;

        let hoveredNode = null;
        let minDistance = 15 / currentTransform.k;

        filteredNodes.forEach(node => {
            const dx = node.x - mouseX;
            const dy = node.y - mouseY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < minDistance) {
                minDistance = distance;
                hoveredNode = node;
            }
        });

        if (hoveredNode) {
            const isBot = hoveredNode.type === 'inorganic';
            let roleText = hoveredNode.es_medio
                ? '<span class="medio-text">Medio de comunicación</span>'
                : (isBot ? '<span class="inorganic-text">Inorgánico</span>' : '<span class="organic-text">Orgánico</span>');

            tooltip.innerHTML = `
                <strong>@${hoveredNode.id}</strong>
                Rol: ${roleText}<br>
                Centralidad: ${hoveredNode.val.toFixed(1)}<br>
                Comunidad: Clúster #${hoveredNode.group}
            `;

            tooltip.style.opacity = 1;
            const tooltipWidth = tooltip.offsetWidth || 200;
            const tooltipHeight = tooltip.offsetHeight || 90;

            let posX = event.clientX + 15;
            let posY = event.clientY + 15;
            if (posX + tooltipWidth > window.innerWidth) posX = event.clientX - tooltipWidth - 15;
            if (posY + tooltipHeight > window.innerHeight) posY = event.clientY - tooltipHeight - 15;

            tooltip.style.left = `${posX}px`;
            tooltip.style.top = `${posY}px`;
            canvas.style.cursor = "pointer";
        } else {
            tooltip.style.opacity = 0;
            canvas.style.cursor = "default";
        }
    });
}
