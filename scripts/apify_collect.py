"""Recolección de X por la API de Apify, con tope de gasto por corrida.

    uv run scripts/apify_collect.py interacciones [--dry-run] [--forzar]  # comentarios + quotes de cada semilla de seeds.yaml
    uv run scripts/apify_collect.py followers [--dry-run]       # seguidores/seguidos de Dataset/apify_users_list.txt

--forzar vuelve a recolectar semillas que ya figuran en runs.log.csv (para traer respuestas tardías);
antes hay que mover los CSV viejos fuera de Dataset/Comments y Dataset/Quotes para no duplicar aristas.
followers pide solo las cuentas que todavía no están como target_username en Dataset/Redes/.

Reutiliza run_actor() de Escucha-Social (APIFY_TOKEN de su .env). Los CSV se bajan con el export de
Apify (format=csv), así quedan las mismas columnas aplanadas que leen los scripts del plugin.
Cada corrida queda en runs.log.csv con su gasto real.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

sys.path.insert(0, "/Volumes/Pikachu/Escucha-Social")
from monitor.apify import API, _headers, account_month_usage_usd, run_actor  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "Dataset"
LOG = ROOT / "runs.log.csv"

# IDs verificados en la API de Apify (el manual del plugin los tiene intercambiados)
COMMENTS = {"actor": "patient_discovery/twitter-comments", "slug": "twitter-comments", "max_usd": 0.30}
QUOTES = {"actor": "seemuapps/x-quote-tweets-scraper", "slug": "x-quote-tweets-scraper", "max_usd": 0.30}
FOLLOWERS = {"actor": "kaitoeasyapi/premium-x-follower-scraper-following-data",
             "slug": "premium-x-follower-scraper-following-data"}
MAX_FOLLOWERS, MAX_FOLLOWINGS, LOTE = 200, 200, 100  # el actor exige maxFollowings >= 200
MAX_QUOTES = 400  # tope explícito; 0 = sin límite según el actor
USD_POR_FILA = 0.00015
MARGEN = 1.3  # un tope justo aborta la corrida a medias (lección de Escucha-Social)
PRESUPUESTO_MES = 45.0


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]


def log(fila: dict):
    nuevo = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "actor", "objetivo", "status", "items", "usd", "run_id", "archivo"])
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def guardar(res, slug: str, destino: Path, objetivo: str) -> Path:
    """Baja el dataset como CSV (columnas aplanadas de Apify) y guarda el JSON crudo."""
    if not res.items:  # Apify no exporta CSV de un dataset vacío
        log({"fecha": stamp(), "actor": res.actor, "objetivo": objetivo, "status": res.status, "items": 0,
             "usd": f"{res.usd:.4f}", "run_id": res.run_id, "archivo": ""})
        print(f"  {res.status}: 0 ítems, ${res.usd:.4f}")
        return None
    run = requests.get(f"{API}/actor-runs/{res.run_id}", headers=_headers(), timeout=30).json()["data"]
    r = requests.get(f"{API}/datasets/{run['defaultDatasetId']}/items", headers=_headers(),
                     params={"clean": "true", "format": "csv", "bom": "true"}, timeout=300)
    r.raise_for_status()
    ts = stamp()
    destino.mkdir(parents=True, exist_ok=True)
    path = destino / f"dataset_{slug}_{ts}.csv"
    path.write_bytes(r.content)
    raw = DATASET / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{slug}_{objetivo}_{ts}.json").write_text(json.dumps(res.items, ensure_ascii=False), encoding="utf-8")
    log({"fecha": ts, "actor": res.actor, "objetivo": objetivo, "status": res.status, "items": len(res.items),
         "usd": f"{res.usd:.4f}", "run_id": res.run_id, "archivo": str(path.relative_to(ROOT))})
    print(f"  {res.status}: {len(res.items)} ítems, ${res.usd:.4f} → {path.relative_to(ROOT)}")
    return path


def revisar_presupuesto(tope_fase: float):
    usado = account_month_usage_usd()
    print(f"Gasto del mes en la cuenta Apify: ${usado:.2f} de ${PRESUPUESTO_MES:.2f}; tope de esta fase ${tope_fase:.2f}")
    if usado + tope_fase > PRESUPUESTO_MES:
        raise SystemExit("La fase podría pasar el presupuesto mensual; ajústalo a propósito antes de seguir.")


def interacciones(dry: bool, forzar: bool = False):
    seeds = yaml.safe_load((ROOT / "seeds.yaml").read_text(encoding="utf-8"))
    tope = len(seeds) * (COMMENTS["max_usd"] + QUOTES["max_usd"])
    print(f"{len(seeds)} semillas × 2 actores, tope máximo ${tope:.2f}")
    if dry:
        return
    revisar_presupuesto(tope)
    hechos = {(r["actor"], r["objetivo"]) for r in csv.DictReader(open(LOG, encoding="utf-8"))
              if r["status"] == "SUCCEEDED"} if LOG.exists() and not forzar else set()
    for s in seeds:
        print(f"@{s['autor']} {s['id']} ({s['carpeta']})")
        if (COMMENTS["actor"], s["id"]) not in hechos:
            res = run_actor(COMMENTS["actor"], {"tweetId": s["id"], "maxPages": 50}, COMMENTS["max_usd"])
            guardar(res, COMMENTS["slug"], DATASET / "Comments" / s["carpeta"], s["id"])
        if (QUOTES["actor"], s["id"]) not in hechos:
            res = run_actor(QUOTES["actor"], {"tweetId": s["id"], "maxItems": MAX_QUOTES}, QUOTES["max_usd"])
            guardar(res, QUOTES["slug"], DATASET / "Quotes" / s["carpeta"], s["id"])


def ya_en_redes() -> set[str]:
    csv.field_size_limit(sys.maxsize)
    vistos = set()
    for f in (DATASET / "Redes").glob("*.csv"):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            vistos |= {(r.get("target_username") or "").lower() for r in csv.DictReader(fh)}
    return vistos


def followers(dry: bool, forzar: bool = False):
    usuarios = [u.strip().lstrip("@") for u in (DATASET / "apify_users_list.txt").read_text().splitlines() if u.strip()]
    vistos = ya_en_redes()
    nuevos = [u for u in usuarios if u.lower() not in vistos]
    print(f"{len(usuarios) - len(nuevos)} cuentas ya están en Dataset/Redes/")
    ronda = datetime.now(timezone.utc).strftime("%Y%m%d")
    lotes = [nuevos[i:i + LOTE] for i in range(0, len(nuevos), LOTE)]
    pendientes = [(f"lote_{ronda}_{i:03d}", l) for i, l in enumerate(lotes)]
    usuarios = nuevos
    por_lote = lambda l: len(l) * (MAX_FOLLOWERS + MAX_FOLLOWINGS) * USD_POR_FILA * MARGEN
    tope = sum(por_lote(l) for _, l in pendientes)
    esperado = sum(len(l) for _, l in pendientes) * (MAX_FOLLOWERS + MAX_FOLLOWINGS) * USD_POR_FILA
    print(f"{len(usuarios)} usuarios, {len(pendientes)}/{len(lotes)} lotes pendientes; "
          f"costo esperado ≤ ${esperado:.2f} (tope con margen ${tope:.2f})")
    if dry:
        return
    revisar_presupuesto(esperado)
    for nombre, l in pendientes:
        print(f"{nombre}: {len(l)} usuarios")
        run_input = {"user_names": l, "maxFollowers": MAX_FOLLOWERS, "maxFollowings": MAX_FOLLOWINGS,
                     "getFollowers": True, "getFollowing": True}
        res = run_actor(FOLLOWERS["actor"], run_input, round(por_lote(l), 2), timeout_s=3600)
        guardar(res, FOLLOWERS["slug"], DATASET / "Redes", nombre)
        time.sleep(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fase", choices=["interacciones", "followers"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--forzar", action="store_true", help="ignorar runs.log.csv y volver a recolectar")
    a = ap.parse_args()
    {"interacciones": interacciones, "followers": followers}[a.fase](a.dry_run, a.forzar)
