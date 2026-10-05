"""Datos para la vista de difusión: cómo se mueve la conversación en el tiempo.

    uv run scripts/difusion.py            # → scrollytelling-site/visuals/diffusion.json

Por cada semilla de seeds.yaml: hora real de publicación (va codificada en el ID del tuit, así que el
tiempo cero no es la primera reacción como en AGT_USAC_v2), y sus respuestas y quotes de Dataset/Comments y
Dataset/Quotes con hora, autor, tipo y narrativa. Si una semilla cita a otra, se registra como cascada.

El texto y las métricas de cada semilla se piden una vez al endpoint público de syndication de X y quedan en
Dataset/semillas.json (las métricas son las del momento de esa consulta).
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "Dataset"
OUT = ROOT / "scrollytelling-site" / "visuals" / "diffusion.json"
CACHE = DATASET / "semillas.json"
SYNDICATION = "https://cdn.syndication.twimg.com/tweet-result"
# Nota de seguimiento de La Hora (5-oct); su tuit no está entre las semillas, se marca como referencia
HITOS = [{"t": "2026-10-05T09:00:13+00:00", "texto": "La Hora publica «Grupo de empresas en el CIV»"}]
TIME_FORMAT = "%a %b %d %H:%M:%S %z %Y"


def hora_de_id(tweet_id: str) -> datetime:
    """Los IDs de X (snowflake) llevan el milisegundo de publicación en los bits altos."""
    return datetime.fromtimestamp(((int(tweet_id) >> 22) + 1288834974657) / 1000, tz=timezone.utc)


def semillas_info(seeds: list[dict]) -> dict:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    for s in seeds:
        if s["id"] in cache:
            continue
        r = requests.get(SYNDICATION, params={"id": s["id"], "lang": "es", "token": "4"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        d = r.json() if r.ok and r.text.strip() else {}
        q = d.get("quoted_tweet") or {}
        cache[s["id"]] = {"texto": d.get("text"), "likes": d.get("favorite_count"),
                          "respuestas": d.get("conversation_count"), "cita_a": q.get("id_str"),
                          "consultado": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        print(f"  syndication @{s['autor']} {s['id']}: {'ok' if d else 'sin datos'}")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache


def narrativa(texto: str, narrativas: list[dict]) -> str | None:
    """La de más palabras clave presentes (mismo criterio de coincidencia que tag_narratives del plugin)."""
    t = (texto or "").lower()
    hits = [(sum(kw.lower() in t for kw in n["keywords"]), -i, n["key"]) for i, n in enumerate(narrativas)]
    mejor = max(hits)
    return mejor[2] if mejor[0] else None


def leer(subdir: str):
    for f in sorted((DATASET / subdir).rglob("*.csv")):
        yield pd.read_csv(f, encoding="utf-8-sig", dtype=str)


def eventos(seed_ids: set[str]) -> list[dict]:
    out, vistos = [], set()
    for df in leer("Comments"):
        for _, r in df.iterrows():
            sid, tid = r.get("conversation_id"), r.get("id")
            if sid not in seed_ids or tid in vistos or pd.isna(r.get("created_at")):
                continue
            vistos.add(tid)
            texto = r.get("display_text") if pd.notna(r.get("display_text")) else r.get("text")
            out.append({"seed": sid, "id": tid, "kind": "comment", "autor": r.get("author/screen_name"),
                        "t": datetime.strptime(r["created_at"], TIME_FORMAT), "texto": texto})
    for df in leer("Quotes"):
        for _, r in df.iterrows():
            sid, tid = r.get("parentTweetId"), r.get("tweetId")
            if sid not in seed_ids or tid in vistos or pd.isna(r.get("createdAt")):
                continue
            vistos.add(tid)
            out.append({"seed": sid, "id": tid, "kind": "quote", "autor": r.get("authorUsername"),
                        "t": datetime.strptime(r["createdAt"], TIME_FORMAT), "texto": r.get("text")})
    return out


def main():
    config = json.loads((ROOT / "sna.config.json").read_text(encoding="utf-8"))
    narrativas = config["narratives"]
    medios = {m.lower() for m in config["media_accounts"]["confirmed"]}
    seeds = yaml.safe_load((ROOT / "seeds.yaml").read_text(encoding="utf-8"))
    info = semillas_info(seeds)
    ids = {s["id"] for s in seeds}

    evs = eventos(ids)
    corte = max(datetime.strptime(r["fecha"][:19], "%Y-%m-%d_%H-%M-%S").replace(tzinfo=timezone.utc)
                for r in csv.DictReader(open(ROOT / "runs.log.csv", encoding="utf-8"))
                if "follower" not in r["actor"])

    seeds_out = []
    for s in seeds:
        i = info.get(s["id"], {})
        texto = i.get("texto") or ""
        seeds_out.append({
            "id": s["id"], "autor": s["autor"], "es_medio": s["autor"].lower() in medios or s["carpeta"] == "Medios",
            "t": hora_de_id(s["id"]).isoformat(), "texto": texto, "likes": i.get("likes"),
            "cita_a": i.get("cita_a") if i.get("cita_a") in ids else None,
            "narrativa": narrativa(texto + " " + s.get("nota", ""), narrativas),
            "n_comment": sum(e["seed"] == s["id"] and e["kind"] == "comment" for e in evs),
            "n_quote": sum(e["seed"] == s["id"] and e["kind"] == "quote" for e in evs),
        })
    seeds_out.sort(key=lambda s: s["t"])

    eventos_out = [{
        "seed": e["seed"], "t": e["t"].isoformat(), "kind": e["kind"], "autor": e["autor"],
        "es_medio": str(e["autor"]).lower() in medios, "narrativa": narrativa(e["texto"], narrativas),
        "texto": " ".join(str(e["texto"] or "").split())[:180], "es_semilla": e["id"] in ids,
    } for e in sorted(evs, key=lambda e: e["t"])]

    data = {"zona": "America/Guatemala", "corte": corte.isoformat(), "hitos": HITOS,
            "narrativas": [{"key": n["key"], "title": n["title"], "color": n["color"]} for n in narrativas],
            "seeds": seeds_out, "events": eventos_out}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    sin = sum(e["narrativa"] is None for e in eventos_out)
    print(f"{len(seeds_out)} semillas, {len(eventos_out)} reacciones ({sin} sin narrativa) → {OUT.relative_to(ROOT)}")
    for s in seeds_out:
        print(f"  {s['t'][:16]} @{s['autor']:<16} 💬{s['n_comment']:>3} ❝{s['n_quote']:>3}  cita_a={s['cita_a']}  {s['narrativa']}")
    from collections import Counter
    print(Counter(e["narrativa"] for e in eventos_out))


if __name__ == "__main__":
    sys.exit(main())
