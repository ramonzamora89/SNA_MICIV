"""Contexto desde la base de Escucha-Social (Supabase), en modo solo lectura.

    uv run scripts/escucha_social_contexto.py candidatos   # tuits del 3-5 oct sobre la nota, para elegir semillas
    uv run scripts/escucha_social_contexto.py exportar     # nota, ítems vinculados, análisis y comentarios → Dataset/escucha_social/

DATABASE_URL se lee de /Volumes/Pikachu/Escucha-Social/.env y nunca se imprime.
"""

import argparse
import csv
import json
from pathlib import Path

import psycopg

ES_ENV = Path("/Volumes/Pikachu/Escucha-Social/.env")
OUT = Path(__file__).resolve().parent.parent / "Dataset" / "escucha_social"
DESDE, HASTA = "2026-10-03", "2026-10-06"
NOTA = "lahora:1026613"
# Términos de la nota: puentes sobrevalorados, licitación DGC, Gilberto Guerra
PATRONES = ["%puente%", "%primavera%", "%gilberto guerra%", "%sobrevalora%", "%dgc%", "%89 millones%", "%q89%",
            "%148 millones%", "%lahora.gt/investigacion/smorales/2026/10/03%"]


def database_url() -> str:
    for line in ES_ENV.read_text().splitlines():
        k, sep, v = line.partition("=")
        if sep and k.strip() == "DATABASE_URL":
            return v.strip().strip("\"'")
    raise SystemExit("DATABASE_URL no está en el .env de Escucha-Social")


def conectar():
    return psycopg.connect(database_url(), options="-c default_transaction_read_only=on")


def filtro(alias: str = "i") -> str:
    campos = f"lower(coalesce({alias}.title,'') || ' ' || coalesce({alias}.body,'') || ' ' || coalesce({alias}.url,''))"
    return "(" + " OR ".join(f"{campos} LIKE %s" for _ in PATRONES) + ")"


def candidatos():
    sql = f"""SELECT i.id, i.author, i.published_at, i.url, i.metrics, left(i.body, 160)
              FROM items i WHERE i.source = 'x' AND i.published_at >= %s AND i.published_at < %s AND {filtro()}
              ORDER BY coalesce((i.metrics->>'reacciones')::int, 0) + coalesce((i.metrics->>'compartidos')::int, 0) DESC"""
    with conectar() as c:
        rows = c.execute(sql, [DESDE, HASTA, *PATRONES]).fetchall()
    print(f"{len(rows)} tuits en la base sobre la nota ({DESDE} a {HASTA})\n")
    for id_, autor, fecha, url, m, texto in rows:
        m = m or {}
        print(f"{id_}  @{autor}  {fecha:%d-%m %H:%M}  ♥{m.get('reacciones')} 💬{m.get('comentarios')} "
              f"↻{m.get('compartidos')} seg={m.get('seguidores')}\n   {url}\n   {' '.join((texto or '').split())}\n")


def _csv(path: Path, header: list[str], rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in r])


def exportar():
    OUT.mkdir(parents=True, exist_ok=True)
    with conectar() as c:
        items = c.execute(
            f"""SELECT i.id, i.source, i.outlet, i.author, i.published_at, i.url, i.title, i.body, i.entities, i.metrics,
                       a.tone, a.risk, a.frame, a.summary
                FROM items i LEFT JOIN analyses a ON a.item_id = i.id
                WHERE i.id = %s OR (i.published_at >= %s AND i.published_at < %s AND {filtro()})
                ORDER BY i.published_at""", [NOTA, DESDE, HASTA, *PATRONES]).fetchall()
        ids = [r[0] for r in items]
        comentarios = c.execute(
            "SELECT id, item_id, text, author_hash, likes, published_at, parent_id FROM comments WHERE item_id = ANY(%s) "
            "ORDER BY published_at", [ids]).fetchall()
    _csv(OUT / "items_nota.csv", ["id", "source", "outlet", "author", "published_at", "url", "title", "body", "entities",
                                  "metrics", "tone", "risk", "frame", "summary"], items)
    _csv(OUT / "comentarios_nota.csv", ["id", "item_id", "text", "author_hash", "likes", "published_at", "parent_id"],
         comentarios)
    por_fuente = {}
    for r in items:
        por_fuente[r[1]] = por_fuente.get(r[1], 0) + 1
    print(f"{len(items)} ítems {por_fuente} y {len(comentarios)} comentarios → {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["candidatos", "exportar"])
    {"candidatos": candidatos, "exportar": exportar}[ap.parse_args().accion]()
