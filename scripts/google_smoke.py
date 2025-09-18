import argparse
import json

import pandas as pd

from core.google_api import normalize_supplier, place_details, text_search

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help='e.g. "tattoo aftercare supplier"')
    ap.add_argument("--location", default="", help="lat,lng (optional)")
    ap.add_argument("--radius_m", type=int, default=50000)
    ap.add_argument("--max_pages", type=int, default=2)
    args = ap.parse_args()

    rows = []
    hits = text_search(args.query, args.location or None, args.radius_m, args.max_pages)
    for r in hits[:25]:  # cap for demo
        det = place_details(r["place_id"])
        sup = normalize_supplier({**r, **det})
        rows.append(sup)

    print(json.dumps({"count": len(rows), "sample": rows[:2]}, ensure_ascii=False, indent=2))
    pd.DataFrame(rows).to_excel("data/processed/suppliers_google_demo.xlsx", index=False)
    print("Wrote data/processed/suppliers_google_demo.xlsx")
