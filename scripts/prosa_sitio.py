"""Escribe la prosa de cada paso del sitio dentro de los bloques sna:auto:prose de index.html.

    uv run scripts/prosa_sitio.py   # después de render_site.py; sobrescribe solo la prosa

La tabla de personajes recurrentes se arma desde reportes/personajes_recurrentes.csv.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "scrollytelling-site/index.html"


def personajes() -> str:
    filas = list(csv.DictReader(open(ROOT / "reportes/personajes_recurrentes.csv", encoding="utf-8-sig")))
    part = [f for f in filas if f["rol_miciv"] == "participante" and f["AGT_USAC"] in ("participante", "hub")
            or f["rol_miciv"] == "participante" and f["AGT_x_textos"] != "0"]
    tres = [f for f in part if f["AGT_x_textos"] != "0"]
    usac = [f for f in part if f["AGT_USAC"] in ("participante", "hub")]
    filas_html = "\n".join(
        f"            <tr><td>@{f['handle']}</td><td>{f['participaciones']}</td>"
        f"<td>{'sí' if f['AGT_x_textos'] != '0' else '–'}</td><td>{f['AGT_USAC'] or '–'}</td></tr>"
        for f in sorted(part, key=lambda f: (f["AGT_x_textos"] == "0", -int(f["participaciones"]))))
    return f"""        <h3>Cuentas que reaparecen</h3>
        <p>De las cuentas que escribieron en esta conversación, <strong>{len(usac)}</strong> ya habían participado en la conversación sobre la USAC (julio de 2026) y <strong>{len(tres)}</strong> también comentaron la nota de La Hora sobre la Secretaría Privada (17 de septiembre). Ninguna coincide con las cuentas citadas por @JLFont001 en sus menciones de Tager.</p>
        <table class="mini-table">
            <tr><th>Cuenta</th><th>Mensajes aquí</th><th>Nota 17-sep</th><th>USAC</th></tr>
{filas_html}
        </table>
        <p class="nota">Coincidencia por nombre de usuario. «hub» indica que la cuenta estuvo entre las más centrales de una narrativa en la red de la USAC. Una coincidencia muestra presencia repetida en el debate, no coordinación.</p>
"""


PROSA = {
    "__intro__": """        <p>El 3 de octubre, La Hora publicó «Puentes de Primavera sobrevalorados: así se aumentaron los costos y se cambiaron las bases de la licitación». La nota señala sobrecostos en puentes de la DGC y sitúa los cambios en la cúpula del MICIVI, con mención de Gilberto Guerra, principal asesor de la ministra Norma Zea.</p>
        <p>Este análisis sigue seis publicaciones en X: dos de @lahoragt y cuatro de cuentas que la citaron o la ampliaron (@DarwinHK, @mmendoza_GT, @RMendezRuiz y @VicenteCarrera_). Se recogieron 35 respuestas y 21 citas de 45 cuentas, y la red de seguidores de cada una. La conversación es pequeña: la red refleja quiénes rodean a esas 45 cuentas, no el alcance total de la nota.</p>
""",
    "__bot_intro__": """        <p>Una cuenta se marca como inorgánica si sigue a muchas más cuentas de las que la siguen (más de 500 seguidos y diez veces más seguidos que seguidores) o si interactúa mucho sin recibir interacción. Es un criterio de comportamiento, no una prueba de automatización, y se aplicó igual que en el análisis de la USAC.</p>
        <p>Casi todas las cuentas marcadas están en la periferia: son seguidores de los participantes, no autores de mensajes. Solo 1 de las 45 cuentas que escribieron cumple el criterio.</p>
""",
    "Medios": """        <p>@lahoragt es el único medio que publicó en el núcleo de esta conversación. Su tuit principal recibió 4 respuestas y 10 citas en X. El tuit de seguimiento (#LHPuentesdePrimavera, sobre los Q89 millones de diferencia calculados por técnicos de la DGC) recibió 2 respuestas y ninguna cita.</p>
        <p>La conversación creció en las citas más que en las respuestas al medio. Las citas con más alcance fueron las de @DarwinHK (383 me gusta, 12,530 vistas), @mmendoza_GT (189 me gusta, 7,874 vistas) y @pchicola (151 me gusta, 3,215 vistas), contadas al momento de la recolección (4 de octubre).</p>
""",
    "Responsabilidad_Arevalo": """        <p>Es la narrativa más extendida: aparece en 26 de los 56 mensajes, de 19 cuentas. Su eje es quién responde por el caso. Una parte de la conversación rechaza que la responsabilidad recaiga en Tager y la atribuye al presidente: «La responsabilidad no se delega. El responsable es el señor a quien el pueblo le otorgó el poder de tomar las decisiones» (@HaniaSieraDavid).</p>
        <p>La cuenta @JJMONDAL publicó el mismo texto tres veces, en respuestas y citas a distintas semillas: «Bernardo Arévalo es el Presidente y el responsable de su Gobierno».</p>
""",
    "Poder_Tager": """        <p>Aparece en 15 mensajes de 13 cuentas. Sostiene que la secretaria privada Ana Glenda Tager ejerce el control real del MICIVI. La formulan sobre todo las dos citas con más alcance: «La principal responsable tiene nombre: Ana Glenda Tager» (@DarwinHK) y «¿Y adivinen quién habría abogado y buscado financiamiento para que Guerra siga al frente del MICIVI? Ana Glenda Tager» (@mmendoza_GT).</p>
        <p>Otras cuentas la convierten en una pregunta al presidente: «¿O la Tager tiene más autoridad que él?» (@PattyPe99872402).</p>
""",
    "Guerra_MICIVI": """        <p>Aparece en 15 mensajes de 13 cuentas. Se centra en la permanencia de Gilberto Guerra en el ministerio y en su relación con el exministro Félix Alvarado, quien lo había denunciado. Es la narrativa más cercana al contenido de la nota y la que menciona más instituciones: @CNCguatemala, @Contraloria_gt, @MPguatemala y @CIV_Guatemala.</p>
        <p>«La @CNCguatemala debería denunciar a Guerra y a Ana Glenda y pronunciarse sobre el caso» (@pchicola).</p>
""",
    "Corrupcion_Gobierno": """        <p>Aparece en 22 mensajes de 16 cuentas. Lee el caso como muestra de corrupción del gobierno en conjunto, con referencias irónicas a la «primavera», Semilla y Raíces. Predomina en las citas al tuit de @lahoragt: «Estela de corrupción desde el centro de gobierno» (@B_ehel).</p>
        <p>Es la narrativa con más lenguaje descalificador y la que menos se refiere a los datos de la licitación.</p>
""",
    "__bot_detail__": """        <p>Las cuentas inorgánicas se concentran entre los seguidores de unos pocos participantes (@Corleone_62, @ASolaresM, @MariaBonita9697). Eso indica que en su entorno abundan perfiles de seguimiento masivo, pero no que esos perfiles hayan amplificado los mensajes de esta conversación.</p>
""",
    "__hubs__": """        <p>Aquí la centralidad debe leerse con cautela: de cada participante se recogieron hasta 200 seguidores, así que casi todos quedan con un grado parecido (entre 200 y 226). El peso real se ve mejor en el alcance de los mensajes: las citas de @DarwinHK, @mmendoza_GT y @pchicola, cuentas con entre 47,000 y 174,000 seguidores, fijaron el marco que retomó el resto.</p>
""",
}


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
    HTML.write_text(html, encoding="utf-8")
    print(f"Prosa escrita en {len(prosa)} pasos → {HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
