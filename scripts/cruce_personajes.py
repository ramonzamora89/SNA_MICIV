"""Cruza las cuentas de la conversación MICIV con las de AGT (nota del 17-sep) y AGT_USAC.

    uv run scripts/cruce_personajes.py   # → reportes/personajes_recurrentes.csv

Rol en MICIV:
- participante: escribió una respuesta o un quote (o es autor de una semilla)
- mencionado: aparece con @ en esos textos
- red: está en la red de seguidores del sitio (executive_network.json)
Se cruza por handle normalizado (minúsculas, sin @).
"""

import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PIKA = Path("/Volumes/Pikachu")
MENCION = re.compile(r"@([A-Za-z0-9_]{1,15})")
HANDLE_URL = re.compile(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status")


def h(s) -> str:
    return str(s).strip().lstrip("@").lower()


def leer(path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str, **kw).fillna("")


def miciv():
    """Handle → datos de su papel en la conversación MICIV."""
    p = defaultdict(lambda: {"handle": "", "participaciones": 0, "menciones_recibidas": 0, "narrativas": set()})
    cfg = json.loads((ROOT / "sna.config.json").read_text(encoding="utf-8"))
    narr = [(n["key"], [k.lower() for k in n["keywords"]]) for n in cfg["narratives"]]
    textos = []
    for f in glob.glob(str(ROOT / "Dataset/Comments/**/*.csv"), recursive=True):
        d = leer(f)
        textos += list(zip(d["author/screen_name"], d["display_text"].where(d["display_text"] != "", d["text"])))
    for f in glob.glob(str(ROOT / "Dataset/Quotes/**/*.csv"), recursive=True):
        d = leer(f)
        textos += list(zip(d["authorUsername"], d["text"]))
    for autor, texto in textos:
        r = p[h(autor)]
        r["handle"] = r["handle"] or autor
        r["participaciones"] += 1
        low = texto.lower()
        r["narrativas"].update(k for k, kws in narr if any(kw in low for kw in kws))
        for m in set(MENCION.findall(texto)):
            q = p[h(m)]
            q["handle"] = q["handle"] or m
            q["menciones_recibidas"] += 1
    for u in leer(ROOT / "Dataset/unique_users.csv").itertuples():
        p[h(u.screen_name)]["handle"] = p[h(u.screen_name)]["handle"] or u.screen_name
    red = json.loads((ROOT / "scrollytelling-site/visuals/executive_network.json").read_text(encoding="utf-8"))
    nodos = {h(n["id"]): n for n in red["nodes"]}
    return p, nodos


def agt_usac():
    """Participantes de la conversación USAC (comentarios y quotes) y nodos de su red recortada."""
    part = {h(r.screen_name): int(r.apariciones or 0) for r in leer(PIKA / "AGT_USAC/Dataset/unique_users.csv").itertuples()}
    red = json.loads((PIKA / "AGT_USAC/scrollytelling-site/visuals/executive_network.json").read_text(encoding="utf-8"))
    hubs = set()
    for n in red["narratives"].values():
        hubs.update(h(a["id"]) for a in n.get("top_actors", []))
    nodos = {h(n["id"]) for n in red["nodes"]}
    return part, hubs, nodos


def agt():
    """Autores en X de la conversación sobre la nota de La Hora del 17-sep."""
    c = Counter(h(a) for a in leer(PIKA / "AGT/analisis/x_respuestas_nota.csv")["autor_handle"] if a)
    corpus = leer(PIKA / "AGT/analisis/corpus_consolidado.csv")
    corpus = corpus[corpus["plataforma"].str.lower() == "x"]
    for a, url in zip(corpus["autor_handle"], corpus["url"]):
        k = h(a) if a else (h(HANDLE_URL.search(url).group(1)) if HANDLE_URL.search(url) else "")
        if k:
            c[k] += 0 if k in c else 1
    return c


def main():
    p, nodos = miciv()
    usac_part, usac_hubs, usac_nodos = agt_usac()
    agt_c = agt()
    filas = []
    for k in sorted(set(p) | set(nodos)):
        r = p[k] if k in p else {"handle": nodos[k]["id"], "participaciones": 0, "menciones_recibidas": 0, "narrativas": set()}
        n = nodos.get(k, {})
        en = {"en_AGT": agt_c.get(k, 0),
              "en_AGT_USAC": "hub" if k in usac_hubs else ("participante" if k in usac_part else ("red" if k in usac_nodos else ""))}
        if not (en["en_AGT"] or en["en_AGT_USAC"]):
            continue
        rol = "participante" if r["participaciones"] else ("mencionado" if r["menciones_recibidas"] else "red")
        filas.append({"handle": r["handle"] or k, "rol_miciv": rol, "participaciones": r["participaciones"],
                      "menciones_recibidas": r["menciones_recibidas"], "narrativas": ";".join(sorted(r["narrativas"])),
                      "grado_in_red": n.get("val", ""), "comunidad": n.get("group", ""), "es_medio": n.get("es_medio", ""),
                      "inorganico": n.get("type") == "inorganic" if n else "",
                      "AGT_x_textos": en["en_AGT"], "AGT_USAC": en["en_AGT_USAC"],
                      "n_proyectos": sum(bool(v) for v in en.values())})
    orden = {"participante": 0, "mencionado": 1, "red": 2}
    filas.sort(key=lambda f: (-f["n_proyectos"], orden[f["rol_miciv"]], -f["participaciones"] - f["menciones_recibidas"]))
    out = ROOT / "reportes/personajes_recurrentes.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    roles = Counter(f["rol_miciv"] for f in filas)
    print(f"{len(filas)} cuentas de MICIV aparecen en proyectos previos {dict(roles)} → {out.relative_to(ROOT)}\n")
    for f in [f for f in filas if f["rol_miciv"] != "red"][:40]:
        print(f"  @{f['handle']:<18} {f['rol_miciv']:<12} part={f['participaciones']} menc={f['menciones_recibidas']} "
              f"AGT={f['AGT_x_textos']} USAC={f['AGT_USAC'] or '-'}  {f['narrativas']}")


if __name__ == "__main__":
    main()
