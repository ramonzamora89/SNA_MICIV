"""Deja en Dataset/unique_users.csv y apify_users_list.txt solo a quienes participan (semillas, respuestas, quotes).

    uv run scripts/filtrar_participantes.py   # correr siempre después de extract-users

extract-users del plugin también lee Dataset/Redes/, así que en una segunda ronda mete a los ~10,000
seguidores en la lista y el paso de followers los pediría a todos.
"""

from pathlib import Path

import pandas as pd

DATASET = Path(__file__).resolve().parent.parent / "Dataset"

df = pd.read_csv(DATASET / "unique_users.csv", encoding="utf-8-sig", dtype=str)
part = df[df["fuentes"].str.contains("comments|quotes|autor_original", na=False)]
part.to_csv(DATASET / "unique_users.csv", index=False, encoding="utf-8-sig")
(DATASET / "apify_users_list.txt").write_text("\n".join(part["screen_name"]) + "\n", encoding="utf-8")
print(f"{len(part)} participantes de {len(df)} cuentas → Dataset/unique_users.csv, apify_users_list.txt")
