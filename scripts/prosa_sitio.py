"""Escribe la prosa de cada paso del sitio dentro de los bloques sna:auto:prose de index.html.

    uv run scripts/prosa_sitio.py   # después de render_site.py; sobrescribe solo la prosa

La tabla de personajes recurrentes se arma desde reportes/personajes_recurrentes.csv.
También reaplica site_overrides/ (render_site.py vuelve a copiar el motor JS de la plantilla del plugin).
"""

import csv
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "scrollytelling-site/index.html"
OVERRIDES = ROOT / "site_overrides"
URL_USAC = "https://ramonzamora89.github.io/AGT_USAC/"
URL_NOTA_17SEP = ("https://lahora.gt/investigacion/engelberth-blanco/2026/09/17/"
                  "secretaria-privada-acepta-mecanismo-legal-que-tiene-incidencia-en-ministerios-y-secretarias/")


def personajes() -> str:
    filas = list(csv.DictReader(open(ROOT / "reportes/personajes_recurrentes.csv", encoding="utf-8-sig")))
    part = [f for f in filas if f["rol_miciv"] == "participante" and f["AGT_USAC"] in ("participante", "hub")
            or f["rol_miciv"] == "participante" and f["AGT_x_textos"] != "0"]
    tres = [f for f in part if f["AGT_x_textos"] != "0"]
    total = sum(1 for _ in csv.DictReader(open(ROOT / "Dataset/unique_users.csv", encoding="utf-8-sig")))
    usac = [f for f in part if f["AGT_USAC"] in ("participante", "hub")]
    filas_html = "\n".join(
        f"            <tr><td>@{f['handle']}</td><td>{f['participaciones']}</td>"
        f"<td>{'sí' if f['AGT_x_textos'] != '0' else '–'}</td><td>{f['AGT_USAC'] or '–'}</td></tr>"
        for f in sorted(part, key=lambda f: (f["AGT_x_textos"] == "0", -int(f["participaciones"]))))
    return f"""        <h3>Cuentas que reaparecen</h3>
        <p>Esta conversación puede compararse con otras dos en X en torno a la Secretaría Privada:</p>
        <ul>
            <li>la red sobre la crisis de la USAC, de julio de 2026 (<a href="{URL_USAC}" target="_blank" rel="noopener">ver análisis</a>);</li>
            <li>las reacciones a la nota de La Hora «Secretaría Privada acepta “mecanismo legal” que tiene incidencia en ministerios y secretarías», del 17 de septiembre (<a href="{URL_NOTA_17SEP}" target="_blank" rel="noopener">ver nota</a>).</li>
        </ul>
        <p>De las {total} cuentas que participan aquí, <strong>{len(usac)}</strong> ya habían participado en la conversación sobre la USAC, y <strong>{len(tres)}</strong> comentaron también la nota del 17 de septiembre.</p>
        <table class="mini-table">
            <tr><th>Cuenta</th><th>Mensajes aquí</th><th>Nota 17-sep</th><th>USAC</th></tr>
{filas_html}
        </table>
        <p class="nota">Coincidencia por nombre de usuario. «hub» indica que la cuenta estuvo entre las más centrales de una narrativa en la red de la USAC. Una coincidencia muestra presencia repetida en el debate, no coordinación.</p>
"""


PROSA = {
    "__intro__": """        <p>El 3 de octubre, La Hora publicó «Puentes de Primavera sobrevalorados: así se aumentaron los costos y se cambiaron las bases de la licitación». La nota señala sobrecostos en puentes de la DGC y sitúa los cambios en la cúpula del MICIVI, con mención de Gilberto Guerra, principal asesor de la ministra Norma Zea.</p>
        <p>Este análisis sigue once publicaciones en X. Seis giran en torno a la nota: dos de @lahoragt y cuatro de cuentas que la citaron o la ampliaron (@DarwinHK, @mmendoza_GT, @RMendezRuiz y @VicenteCarrera_). Las otras cinco tocan el tema de forma indirecta y se publicaron entre la tarde del 4 y la madrugada del 5 de octubre: tres de @vozdeltuit, una de @__VaderGT y una de @5toPoderSM.</p>
        <p>Se recogieron 89 respuestas y 35 citas de 100 cuentas, más la red de seguidores de cada una y de los autores de las semillas (104 cuentas). La conversación es pequeña: la red refleja quiénes rodean a esas cuentas, no el alcance total de la nota.</p>
""",
    "__bot_intro__": """        <p>Una cuenta se marca como inorgánica si sigue a muchas más cuentas de las que la siguen (más de 500 seguidos y diez veces más seguidos que seguidores) o si interactúa mucho sin recibir interacción. Es un criterio de comportamiento, no una prueba de automatización.</p>
        <p>Casi todas las cuentas marcadas están en la periferia: son seguidores de los participantes, no autores de mensajes. Solo 4 de las 104 cuentas que escribieron cumplen el criterio.</p>
""",
    "Medios": """        <p>@lahoragt es el único medio que publicó en el núcleo de esta conversación, y ningún otro medio respondió ni citó. Su tuit principal recibió 8 respuestas y 10 citas. El de seguimiento (#LHPuentesdePrimavera, sobre los Q89 millones de diferencia calculados por técnicos de la DGC) recibió 2 respuestas y ninguna cita. La continuación del 5 de octubre («Grupo de empresas en el CIV») quedó fuera de este análisis.</p>
        <p>La conversación creció en las citas más que en las respuestas al medio. Las de más alcance fueron las de @DarwinHK (607 me gusta, 23,475 vistas), @pchicola (301 me gusta, 6,891 vistas) y @mmendoza_GT (299 me gusta, 12,458 vistas), contadas el 5 de octubre.</p>
""",
    "Responsabilidad_Arevalo": """        <p>Es la narrativa más extendida: aparece en 62 de los 124 mensajes, de 51 cuentas. Su eje es quién responde por el caso. Una parte de la conversación rechaza que la responsabilidad recaiga en Tager y la atribuye al presidente: «La responsabilidad no se delega. El responsable es el señor a quien el pueblo le otorgó el poder de tomar las decisiones» (@HaniaSieraDavid).</p>
        <p>Los tuits de @vozdeltuit del 4 de octubre ampliaron este encuadre: «A Ana Glenda Tager le quieren echar todas las culpas, de lo que el Presidente […] no pudo hacer». Entre las respuestas: «Pedir la renuncia de Ana Glenda es pedir la renuncia de Arévalo» (@Reyes16Fernando). La cuenta @JJMONDAL publicó tres veces el mismo texto en distintas semillas: «Bernardo Arévalo es el Presidente y el responsable de su Gobierno».</p>
""",
    "Poder_Tager": """        <p>Aparece en 21 mensajes de 18 cuentas. Sostiene que la secretaria privada Ana Glenda Tager ejerce el control real del MICIVI. La formulan sobre todo las dos citas con más alcance: «La principal responsable tiene nombre: Ana Glenda Tager» (@DarwinHK) y «¿Y adivinen quién habría abogado y buscado financiamiento para que Guerra siga al frente del MICIVI? Ana Glenda Tager» (@mmendoza_GT).</p>
        <p>Otras cuentas la convierten en una pregunta sobre su legitimidad: «Quien es esa y que poder tiene? Ana Glenda Tager? Yo no voté por ella!!!» (@ByronPa93998161).</p>
""",
    "Guerra_MICIVI": """        <p>Aparece en 18 mensajes de 16 cuentas. Se centra en la permanencia de Gilberto Guerra en el ministerio y en su relación con el exministro Félix Alvarado, quien lo había denunciado. Es la narrativa más cercana al contenido de la nota y la que menciona más instituciones: @CNCguatemala, @Contraloria_gt, @MPguatemala y @CIV_Guatemala.</p>
        <p>«La @CNCguatemala debería denunciar a Guerra y a Ana Glenda y pronunciarse sobre el caso» (@pchicola). Es también la que más rápido se apaga: casi no aparece después de la tarde del 4 de octubre (ver «Cómo se movió la conversación»).</p>
""",
    "Corrupcion_Gobierno": """        <p>Aparece en 30 mensajes de 24 cuentas. Lee el caso como muestra de corrupción del gobierno en conjunto, con referencias irónicas a la «primavera», Semilla y Raíces. Predomina en las citas al tuit de @lahoragt: «Estela de corrupción desde el centro de gobierno» (@B_ehel).</p>
        <p>Es la narrativa con más lenguaje descalificador y la que menos se refiere a los datos de la licitación.</p>
""",
    "Culpas_Trasladadas": """        <p>Aparece en 15 mensajes de 11 cuentas; 10 de ellos responden a @vozdeltuit y @__VaderGT. No discute el caso de los puentes: sostiene que el oficialismo siempre encuentra a quién culpar y que Tager es la culpable más reciente. El tuit con más me gusta de la serie de @vozdeltuit lo resume así: «Matrices de opinión del oficialismo: 2024 : Consuelo Porras no nos deja Gobernar. […] 2027: La Primavera no despegó por Ana Glenda 🙄» (@vozdeltuit, 236 me gusta).</p>
        <p>Las respuestas siguen la broma: «2028: “Es que el anterior gobierno”» (@Rxbito), «+ los net centers no nos dejan trabajar» (@Cobr41986). También hay quien la discute: «O sea, culpar a miguel martinez, a baldetti y sandra torres es prohibido» (@ManALaTortrix).</p>
""",
    "__bot_detail__": """        <p>Las cuentas inorgánicas se concentran entre los seguidores de unos pocos participantes (@Corleone_62, @Zacapaneco5, @ASolaresM, @MariaBonita9697). Eso indica que en su entorno abundan perfiles de seguimiento masivo, pero no que esos perfiles hayan amplificado los mensajes de esta conversación.</p>
""",
    "__hubs__": """        <p>Aquí la centralidad debe leerse con cautela: de cada participante se recogieron hasta 200 seguidores, así que las cuentas más centrales quedan con un grado parecido (entre 203 y 248). El peso real se ve mejor en el alcance de los mensajes: las citas de @DarwinHK, @mmendoza_GT y @pchicola fijaron el marco del primer momento, y los tuits de @vozdeltuit y @__VaderGT, el del segundo.</p>
""",
}


DIFUSION = """        <p>Cada fila es una de las once publicaciones, ordenadas por hora de publicación (hora de Guatemala), y cada punto es una respuesta o una cita. Las líneas punteadas unen una publicación con la que cita.</p>
        <p>La conversación tuvo dos momentos. El primero gira en torno a la nota: el tuit de La Hora sale el 3 de octubre a las 03:01, y las citas de @DarwinHK y @mmendoza_GT, esa noche a las 20:39 y 20:45, concentran la mayor parte de las reacciones. El segundo empieza el 4 de octubre a las 12:34, cuando @vozdeltuit publica tres tuits en 22 minutos que ya no hablan de los puentes sino de a quién se culpa. @__VaderGT sigue a las 14:25 con el mismo encuadre.</p>
        <p>El cambio de tema es claro. Antes de las 12:34 del 4 de octubre, 13 de 61 reacciones mencionaban a Guerra, la licitación o el ministerio; después, solo 3 de 63. Además, el segundo momento llegó a otro público: solo 5 cuentas participaron en ambos.</p>
        <p>Las reacciones llegan rápido: la mitad, en las primeras 9 horas tras cada publicación, y el 90 %, dentro de las primeras 24.</p>
        <p class="nota">La hora de publicación sale del identificador de cada tuit. Las reacciones se cuentan hasta el corte de recolección (5 de octubre, 07:55), y X no siempre entrega todas las respuestas. El tamaño de cada rombo indica los me gusta de la publicación al 5 de octubre. Con «Color por narrativa», cada punto toma la narrativa con más palabras clave presentes.</p>
"""


def difusion(html: str) -> str:
    """Inserta el paso de difusión antes del de cuentas inorgánicas, con su CSS, su JS y su entrada en SNA_CONFIG."""
    seccion = f"""<section class="step" data-step="99" data-step-type="diffusion" data-hint="Difusión en el tiempo">
    <div class="step-card">
        <div class="meta-tag">Difusión</div>
        <h2>Cómo se movió la conversación</h2>
{DIFUSION}        <div id="diffusion-card-slot"></div>
    </div>
</section>

"""
    html = re.sub(r'<section class="step" data-step="99" data-step-type="diffusion".*?</section>\n\n', "", html, flags=re.DOTALL)
    html, n = re.subn(r'(<section class="step" data-step="\d+" data-step-type="bot_detail")', lambda m: seccion + m.group(1), html)
    if not n:
        raise SystemExit("No está el paso bot_detail en index.html para insertar la difusión antes")
    if "css/diffusion.css" not in html:
        html = html.replace('<link rel="stylesheet" href="css/style.css">',
                            '<link rel="stylesheet" href="css/style.css">\n    <link rel="stylesheet" href="css/diffusion.css">', 1)
    if "js/diffusion.js" not in html:
        html = html.replace('<script src="js/network.js"></script>',
                            '<script src="js/network.js"></script>\n    <script src="js/diffusion.js"></script>', 1)
    if '"type": "diffusion"' not in html:
        html = html.replace("window.SNA_CONFIG = {steps: [",
                            'window.SNA_CONFIG = {steps: [{"index": 99, "type": "diffusion", "key": "__diffusion__"}, ', 1)
    return html


def main():
    html = HTML.read_text(encoding="utf-8")
    prosa = dict(PROSA)
    prosa["__hubs__"] += personajes()
    for key, texto in prosa.items():
        patron = rf"(<!-- sna:auto:prose key={re.escape(key)} start -->\n)(.*?)(        <!-- sna:auto:prose key={re.escape(key)} end -->)"
        html, n = re.subn(patron, lambda m: m.group(1) + texto + m.group(3), html, flags=re.DOTALL)
        if not n:
            raise SystemExit(f"No está el bloque de prosa '{key}' en index.html")
    if ".mini-table" not in html:
        html = html.replace("</head>", """<style>
.mini-table{width:100%;border-collapse:collapse;font-size:.8rem;margin:.6rem 0}
.mini-table th,.mini-table td{text-align:left;padding:.2rem .4rem;border-bottom:1px solid rgba(127,127,127,.25)}
.step-card .nota{font-size:.75rem;opacity:.75}
</style>
</head>""", 1)
    html = difusion(html)
    HTML.write_text(html, encoding="utf-8")
    for f in OVERRIDES.rglob("*"):
        if f.is_file():
            shutil.copyfile(f, ROOT / "scrollytelling-site" / f.relative_to(OVERRIDES))
    print(f"Prosa escrita en {len(prosa)} pasos → {HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
