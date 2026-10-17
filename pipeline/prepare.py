"""Decide who is on the map.

Reads data/config.json, data/interactions.json, data/profiles.json and, if
present, data/seeds.json. Writes data/nodes.json.

Everyone in profiles.json who has at least one interaction with someone else
in profiles.json is placed. The center handle is always placed. Accounts that
only appear in interactions.json, with no profile, are left off, and their
interactions are ignored: the map never invents a person from a handle alone.

Usage: python3 pipeline/prepare.py data
"""
import json, os, sys
from collections import defaultdict

data = sys.argv[1]
cfg = json.load(open(os.path.join(data, "config.json")))
inter = json.load(open(os.path.join(data, "interactions.json")))
profiles = json.load(open(os.path.join(data, "profiles.json")))
seeds_path = os.path.join(data, "seeds.json")
seeds = json.load(open(seeds_path)) if os.path.exists(seeds_path) else []

# one spelling per handle: the profile key wins, then the config/seed spelling
canon = {}
for h in list(profiles) + [cfg["handle"]] + seeds:
    canon.setdefault(h.lower(), h)
C = lambda h: canon.get(h.lower())
me = C(cfg["handle"])
seed_set = {C(s) for s in seeds} - {None}
prof = {C(h): p for h, p in profiles.items()}
if me not in prof:
    prof[me] = {"name": me, "bio": "", "followers": None, "img": ""}

partners = defaultdict(set)
dropped_rows = 0
for r in inter:
    a, b = C(r["from"]), C(r["to"])
    if a is None or b is None or a not in prof or b not in prof:
        dropped_rows += 1
        continue
    if a != b:
        partners[a].add(b); partners[b].add(a)

nodes = [{
    "id": h,
    "name": p.get("name") or h,
    "bio": p.get("bio") or "",
    "followers": p.get("followers"),
    "img": p.get("img") or "",
    "seed": h in seed_set,
} for h, p in sorted(prof.items()) if h == me or partners[h]]

json.dump(nodes, open(os.path.join(data, "nodes.json"), "w"), indent=0)
isolated = len(prof) - len(nodes)
print(f"nodes {len(nodes)} of {len(prof)} profiles ({isolated} with no interaction among map accounts left off); "
      f"{dropped_rows} of {len(inter)} interaction rows involve accounts without a profile; center {me}; seeds {len(seed_set)}")
